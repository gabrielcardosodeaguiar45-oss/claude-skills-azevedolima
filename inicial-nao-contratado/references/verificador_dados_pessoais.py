"""Verificador de coerência entre dados pessoais do KIT (doc físico) e HISCRE.

Regra crítica da skill (ver SKILL.md §9-bis):
- Doc pessoal é fonte PRIMÁRIA
- HISCRE é fonte SUBSIDIÁRIA
- SEMPRE comparar para detectar:
  - Documento de OUTRA pessoa na pasta
  - OCR errado do KIT
  - Homônimos / mudança de nome

Severidade das divergências:
- CRÍTICA: CPF, nome → "REVISAR ANTES DE PROTOCOLAR"
- ATENÇÃO: data_nascimento, nome_mae → "CONFERIR"
"""
import re, unicodedata
from typing import Dict, List, Optional


def _normalizar_str(s: Optional[str]) -> str:
    """Normaliza string para comparação: caixa baixa, sem acentos, sem
    pontuação extra."""
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^\w\s]', '', s.upper()).strip()


def _normalizar_cpf(s: Optional[str]) -> str:
    """CPF: só dígitos."""
    if not s:
        return ''
    return re.sub(r'\D', '', s)


def comparar_doc_vs_hiscre(autora_do_doc: Dict, hiscre: Dict) -> List[Dict]:
    """Compara dados pessoais entre documento físico e HISCRE.

    Args:
        autora_do_doc: dict com chaves: nome, cpf, rg, data_nascimento, nome_mae
                       (qualquer chave pode ser None ou ausente)
        hiscre: dict do parse_hiscre com chaves: nome_autor, cpf, data_nascimento,
                nome_mae, nb_beneficio

    Returns:
        Lista de divergências: [{'campo', 'doc', 'hiscre', 'severidade', 'msg'}]
    """
    divergencias = []

    # === CPF (CRÍTICO — deve bater 100%) ===
    cpf_doc = _normalizar_cpf(autora_do_doc.get('cpf'))
    cpf_hiscre = _normalizar_cpf(hiscre.get('cpf'))
    if cpf_doc and cpf_hiscre and cpf_doc != cpf_hiscre:
        divergencias.append({
            'campo': 'CPF',
            'doc': autora_do_doc.get('cpf'),
            'hiscre': hiscre.get('cpf'),
            'severidade': 'CRÍTICA',
            'msg': 'CPF do documento NÃO bate com o do HISCRE. Pode ser '
                   'documento de OUTRA pessoa na pasta ou OCR errado. '
                   'REVISAR antes de protocolar.',
        })

    # === Nome (CRÍTICO) ===
    nome_doc = _normalizar_str(autora_do_doc.get('nome'))
    nome_hiscre = _normalizar_str(hiscre.get('nome_autor'))
    if nome_doc and nome_hiscre and nome_doc != nome_hiscre:
        # Tentar match parcial (por exemplo, nome do casamento que mudou)
        # Se 80% das palavras são iguais, é "ATENÇÃO"; senão CRÍTICA
        words_doc = set(nome_doc.split())
        words_hiscre = set(nome_hiscre.split())
        if words_doc and words_hiscre:
            sobreposicao = len(words_doc & words_hiscre) / max(len(words_doc), len(words_hiscre))
        else:
            sobreposicao = 0
        if sobreposicao < 0.5:
            divergencias.append({
                'campo': 'Nome',
                'doc': autora_do_doc.get('nome'),
                'hiscre': hiscre.get('nome_autor'),
                'severidade': 'CRÍTICA',
                'msg': 'Nome do documento totalmente diferente do HISCRE. '
                       'PROVÁVEL documento de OUTRA pessoa. REVISAR.',
            })
        else:
            divergencias.append({
                'campo': 'Nome',
                'doc': autora_do_doc.get('nome'),
                'hiscre': hiscre.get('nome_autor'),
                'severidade': 'ATENÇÃO',
                'msg': f'Nome do documento ligeiramente diferente do HISCRE '
                       f'({sobreposicao:.0%} de palavras em comum). Pode ser '
                       'mudança por casamento, abreviação ou erro de OCR.',
            })

    # === Data de nascimento (ATENÇÃO) ===
    dn_doc = autora_do_doc.get('data_nascimento')
    dn_hiscre = hiscre.get('data_nascimento')
    if dn_doc and dn_hiscre:
        # normalizar para data — aceitar string ou datetime
        from datetime import datetime
        if isinstance(dn_doc, str):
            try:
                dn_doc = datetime.fromisoformat(dn_doc)
            except ValueError:
                # tentar dd/mm/aaaa
                try:
                    dn_doc = datetime.strptime(dn_doc, '%d/%m/%Y')
                except ValueError:
                    dn_doc = None
        if isinstance(dn_hiscre, str):
            try:
                dn_hiscre = datetime.fromisoformat(dn_hiscre)
            except ValueError:
                dn_hiscre = None
        if dn_doc and dn_hiscre and dn_doc.date() != dn_hiscre.date():
            divergencias.append({
                'campo': 'Data nascimento',
                'doc': dn_doc.strftime('%d/%m/%Y') if hasattr(dn_doc, 'strftime') else str(dn_doc),
                'hiscre': dn_hiscre.strftime('%d/%m/%Y') if hasattr(dn_hiscre, 'strftime') else str(dn_hiscre),
                'severidade': 'CRÍTICA',
                'msg': 'Data de nascimento do documento NÃO bate com o HISCRE. '
                       'PROVÁVEL documento de OUTRA pessoa.',
            })

    # === Nome da mãe (ATENÇÃO) ===
    mae_doc = _normalizar_str(autora_do_doc.get('nome_mae'))
    mae_hiscre = _normalizar_str(hiscre.get('nome_mae'))
    if mae_doc and mae_hiscre and mae_doc != mae_hiscre:
        divergencias.append({
            'campo': 'Nome da mãe',
            'doc': autora_do_doc.get('nome_mae'),
            'hiscre': hiscre.get('nome_mae'),
            'severidade': 'ATENÇÃO',
            'msg': 'Nome da mãe diverge entre documento e HISCRE. CONFERIR.',
        })

    return divergencias


def consolidar_dados_autora(autora_do_doc: Dict, hiscre: Dict) -> Dict:
    """Consolida AUTORA usando hierarquia: doc > HISCRE.

    Returns:
        dict com campos preenchidos + flag '_fontes' indicando origem de cada campo
    """
    out = dict(autora_do_doc)  # base = doc
    fontes = {}

    # CPF
    if not out.get('cpf') and hiscre.get('cpf'):
        out['cpf'] = hiscre['cpf']
        fontes['cpf'] = 'HISCRE (subsidiário)'
    elif out.get('cpf'):
        fontes['cpf'] = 'documento físico (primário)'

    # Nome
    if not out.get('nome') and hiscre.get('nome_autor'):
        out['nome'] = hiscre['nome_autor']
        fontes['nome'] = 'HISCRE (subsidiário)'
    elif out.get('nome'):
        fontes['nome'] = 'documento físico (primário)'

    # Data nascimento
    if not out.get('data_nascimento') and hiscre.get('data_nascimento'):
        out['data_nascimento'] = hiscre['data_nascimento']
        fontes['data_nascimento'] = 'HISCRE (subsidiário)'
    elif out.get('data_nascimento'):
        fontes['data_nascimento'] = 'documento físico (primário)'

    # Nome mãe
    if not out.get('nome_mae') and hiscre.get('nome_mae'):
        out['nome_mae'] = hiscre['nome_mae']
        fontes['nome_mae'] = 'HISCRE (subsidiário)'
    elif out.get('nome_mae'):
        fontes['nome_mae'] = 'documento físico (primário)'

    out['_fontes'] = fontes
    return out


if __name__ == '__main__':
    # Testes
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Caso 1: BATEM (esperado: 0 divergências)
    doc1 = {'nome': 'GEORGE DA SILVA SOUZA', 'cpf': '387.047.905-10',
            'nome_mae': 'ELIETA DA SILVA SOUZA'}
    his1 = {'nome_autor': 'GEORGE DA SILVA SOUZA', 'cpf': '387.047.905-10',
            'nome_mae': 'ELIETA DA SILVA SOUZA'}
    print('CASO 1 (BATEM):', comparar_doc_vs_hiscre(doc1, his1))

    # Caso 2: CPF errado (CRÍTICA)
    doc2 = {'nome': 'GEORGE DA SILVA SOUZA', 'cpf': '382.099.905-10'}
    his2 = {'nome_autor': 'GEORGE DA SILVA SOUZA', 'cpf': '387.047.905-10'}
    print('\nCASO 2 (CPF divergente):')
    for d in comparar_doc_vs_hiscre(doc2, his2):
        print(f'  [{d["severidade"]}] {d["campo"]}: doc={d["doc"]} vs hiscre={d["hiscre"]}')

    # Caso 3: nome diferente (CRÍTICA)
    doc3 = {'nome': 'JOÃO DA SILVA SAUSER', 'cpf': '387.047.905-10'}
    his3 = {'nome_autor': 'GEORGE DA SILVA SOUZA', 'cpf': '387.047.905-10'}
    print('\nCASO 3 (nome diferente):')
    for d in comparar_doc_vs_hiscre(doc3, his3):
        print(f'  [{d["severidade"]}] {d["campo"]}: doc={d["doc"]!r} vs hiscre={d["hiscre"]!r}')
