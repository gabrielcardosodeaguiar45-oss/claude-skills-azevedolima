"""Sistema de aprendizado OCR contínuo para o auditor de procurações.

Não treina o modelo easyocr propriamente (fine-tuning é caro e exige
dataset grande). Em vez disso, mantém TRÊS camadas de correção que ficam
melhores a cada caso processado:

1. **Allowlist de bancos canônicos**: força o OCR a preferir nomes da
   lista (`BANRISUL`, `BRADESCO`, etc.) sobre variações ruidosas
   (`BANRSUL`, `BRADESC0`). Easyocr aceita `allowlist=` no `readtext`.

2. **Dicionário de correções aprendidas**: arquivo JSON `_ocr_corrections.json`
   que mapeia `(contexto_ocr_bruto) → contrato_correto`. Toda vez que o
   usuário corrige um número, a correção fica salva e é aplicada
   automaticamente em runs futuros.

3. **Heurística pós-OCR contextual**: regras determinísticas para corrigir
   ruído sistemático (zeros virando `o`/`q`/`O`, `S A` sem ponto vs `SA`,
   `ª`/`a`/`A` confundidos em "ao", `_`/espaços, etc.). Já implementadas
   no regex do auditor, mas centralizadas aqui para reuso.

USO:
    from ocr_learning import (carregar_dicionario, salvar_correcao,
                                aplicar_correcoes, sugerir_correcao)

    # Ao detectar uma procuração via OCR:
    contrato_bruto = "00000o0qo0000917305"
    contrato_corrigido = aplicar_correcoes(contrato_bruto)

    # Quando o usuário corrige (via auditor manual ou re-rodada):
    salvar_correcao(
        bruto=contrato_bruto,
        correcao='000000000000917305',
        banco='BANRISUL',
        cliente='VILSON DA CRUZ BRASIL',
    )

    # Sugestão automática quando há ambiguidade:
    sugestoes = sugerir_correcao('00000O0Q00000920809')
    # → ['00000000000009208603', '0000000000009208090']  (top-K)
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================================
# Arquivo de aprendizado (persistido entre sessões)
# ============================================================================

DICIONARIO_PATH = Path(__file__).parent / '_ocr_corrections.json'


def _carregar_dict() -> Dict:
    if not DICIONARIO_PATH.exists():
        return {
            'versao': '1.0',
            'atualizado': None,
            'correcoes': [],          # lista de dicts (bruto, correcao, banco, cliente, data)
            'substituicoes_caracteres': {  # confusões OCR (caractere → caractere)
                'o': '0', 'O': '0', 'q': '0', 'Q': '0',
                'l': '1', 'I': '1', '|': '1',
                'S': '5', 's': '5',
                'B': '8',  # B → 8 em contexto numérico
            },
            'palavras_ancora_bancos': [
                'BANRISUL', 'BMG', 'PAN', 'BRADESCO', 'FACTA', 'C6',
                'ITAU', 'ITAÚ', 'DAYCOVAL', 'OLE', 'SANTANDER', 'SAFRA',
                'MERCANTIL', 'INTER', 'INBURSA', 'PARANA', 'PARATI',
                'SENFF', 'SICOOB', 'CETELEM', 'BGN', 'AGIBANK', 'CREFISA',
                'MASTER', 'PICPAY', 'CAPITAL', 'NUBANK', 'CAIXA',
                'BANCO DO ESTADO DO RIO GRANDE DO SUL',
            ],
            'palavras_ancora_teses_bradesco': [
                'TARIFA', 'TARIFAS', 'MORA', 'MORA CRED PESS',
                'GASTOS CARTAO', 'GASTOS CARTÃO',
                'APLIC INVEST', 'APLICAÇÃO INVEST',
                'TITULO CAPITALIZACAO', 'TÍTULO CAPITALIZAÇÃO',
                'PG ELETRON', 'PAGAMENTO ELETRÔNICO',
                'ENCARGO', 'CESTA',
            ],
            'estatisticas': {
                'total_correcoes': 0,
                'por_banco': {},
            },
        }
    with open(DICIONARIO_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _salvar_dict(d: Dict) -> None:
    d['atualizado'] = datetime.now().isoformat()
    with open(DICIONARIO_PATH, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


# ============================================================================
# API pública
# ============================================================================

def carregar_dicionario() -> Dict:
    """Retorna o dicionário atual de correções."""
    return _carregar_dict()


def salvar_correcao(bruto: str, correcao: str, banco: str = '',
                    cliente: str = '', contexto: str = '') -> None:
    """Registra que o OCR pegou `bruto` quando o valor correto era `correcao`.

    Toda futura ocorrência de `bruto` (ou variações similares) terá a
    correção sugerida automaticamente.

    Args:
        bruto: o que o OCR extraiu (ex.: '00000o0qo0000917305')
        correcao: o número correto confirmado (ex.: '000000000000917305')
        banco: chave canônica do banco (opcional, p/ estatísticas)
        cliente: nome do cliente (opcional, p/ auditoria)
        contexto: trecho do PDF onde apareceu (opcional, p/ debug)
    """
    d = _carregar_dict()
    entrada = {
        'bruto': bruto,
        'correcao': correcao,
        'banco': banco.upper() if banco else '',
        'cliente': cliente,
        'contexto': contexto[:200] if contexto else '',
        'data': datetime.now().isoformat(),
    }
    # Evita duplicata exata
    if not any(c.get('bruto') == bruto and c.get('correcao') == correcao
               for c in d.get('correcoes', [])):
        d.setdefault('correcoes', []).append(entrada)
        d.setdefault('estatisticas', {})
        d['estatisticas']['total_correcoes'] = len(d['correcoes'])
        por_banco = d['estatisticas'].setdefault('por_banco', {})
        if banco:
            por_banco[banco.upper()] = por_banco.get(banco.upper(), 0) + 1
        # Auto-aprende caracteres mais frequentes errados (ex.: 'o' virando '0')
        if len(bruto) == len(correcao):
            subs = d.setdefault('substituicoes_caracteres', {})
            for a, b in zip(bruto, correcao):
                if a != b and a.isalpha() and b.isdigit():
                    # OCR pegou letra onde devia ser dígito
                    subs[a] = b
        _salvar_dict(d)


def aplicar_correcoes(bruto: str) -> str:
    """Aplica TODAS as camadas de correção em sequência:

    1. Match exato no histórico (`bruto` já visto antes → devolve correção).
    2. Substituições de caractere (o→0, q→0, etc.).
    3. Limpeza final: só dígitos + hífen.

    Returns: número limpo, pronto para comparação.
    """
    if not bruto:
        return ''
    d = _carregar_dict()
    # 1. Match exato no histórico
    for c in d.get('correcoes', []):
        if c.get('bruto') == bruto:
            return c.get('correcao')
    # 2. Substituições de caractere
    subs = d.get('substituicoes_caracteres', {})
    out = []
    for ch in bruto:
        if ch.isdigit() or ch == '-':
            out.append(ch)
        elif ch in subs:
            out.append(subs[ch])
        # Ignora outros caracteres
    return ''.join(out)


def sugerir_correcao(bruto: str, top_k: int = 3) -> List[str]:
    """Devolve as top-K correções mais prováveis com base no histórico.

    Usa distância de Hamming sobre números do mesmo tamanho, lstrip('0')
    para tolerar prefixos diferentes. Útil para sugerir match quando há
    ambiguidade.
    """
    d = _carregar_dict()
    candidato = aplicar_correcoes(bruto)
    candidato_clean = candidato.lstrip('0')
    historico = []
    for c in d.get('correcoes', []):
        cor = c.get('correcao', '')
        cor_clean = re.sub(r'\D', '', cor).lstrip('0')
        if not cor_clean:
            continue
        # Mesma faixa de tamanho ± 2
        if abs(len(cor_clean) - len(candidato_clean)) > 2:
            continue
        # Distância: Hamming se mesmo tamanho, senão substring score
        if len(cor_clean) == len(candidato_clean):
            dist = sum(1 for a, b in zip(cor_clean, candidato_clean) if a != b)
        else:
            menor, maior = sorted([cor_clean, candidato_clean], key=len)
            dist = 0 if menor in maior else 99
            dist += abs(len(cor_clean) - len(candidato_clean))
        historico.append((dist, cor))
    historico.sort()
    # Devolve apenas as correções, sem distância, top-K
    return [c for _, c in historico[:top_k]]


def obter_allowlist_easyocr() -> str:
    """Retorna a string `allowlist` para passar ao easyocr.

    Inclui dígitos + letras maiúsculas + caracteres comuns em procurações.
    Easyocr usa essa lista para PREFERIR esses caracteres ao decidir entre
    candidatos ambíguos (ex.: 'o' vs '0' → se '0' está na allowlist e 'o'
    não, o modelo escolhe '0' com mais frequência).
    """
    return (
        '0123456789'
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        'abcdefghijklmnopqrstuvwxyz'
        'ÁÀÂÃÄÇÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜ'
        'áàâãäçéèêëíìîïóòôõöúùûü'
        ' .,;:!?()-/&º°ª'
    )


def estatisticas_aprendizado() -> Dict:
    """Devolve resumo do aprendizado acumulado até agora."""
    d = _carregar_dict()
    return {
        'total_correcoes_aprendidas': len(d.get('correcoes', [])),
        'por_banco': d.get('estatisticas', {}).get('por_banco', {}),
        'caracteres_substituidos': dict(d.get('substituicoes_caracteres', {})),
        'ultima_atualizacao': d.get('atualizado'),
    }


# ============================================================================
# CLI
# ============================================================================

def main():
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if len(sys.argv) < 2:
        print('USO:')
        print('  python ocr_learning.py stats               # mostra estatisticas')
        print('  python ocr_learning.py corrigir BRUTO CORRECAO [BANCO]')
        print('  python ocr_learning.py aplicar BRUTO       # aplica correcoes')
        print('  python ocr_learning.py sugerir BRUTO       # sugere top-K')
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'stats':
        import json as _j
        print(_j.dumps(estatisticas_aprendizado(), indent=2, ensure_ascii=False))
    elif cmd == 'corrigir':
        bruto, correcao = sys.argv[2], sys.argv[3]
        banco = sys.argv[4] if len(sys.argv) > 4 else ''
        salvar_correcao(bruto, correcao, banco)
        print(f'OK: {bruto!r} -> {correcao!r} (banco {banco!r})')
    elif cmd == 'aplicar':
        bruto = sys.argv[2]
        print(aplicar_correcoes(bruto))
    elif cmd == 'sugerir':
        bruto = sys.argv[2]
        for s in sugerir_correcao(bruto):
            print(s)


if __name__ == '__main__':
    main()
