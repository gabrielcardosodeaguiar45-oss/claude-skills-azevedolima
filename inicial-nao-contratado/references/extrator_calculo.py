"""Extrator de dados do PDF de cálculo (formato Cálculo Jurídico).

Extrai:
- Total Geral (valor da causa) — da p.2
- Dano moral pleiteado no cálculo — da p.3+ (linha "DANOS MORAIS")
- Data de nascimento + idade do cliente — da p.1
- Termo final do cálculo (data de referência)

Formato esperado do PDF (ex.: George/ITAÚ):
  Página 1: Dados do cliente, dados do cálculo
  Página 2: "Total geral: R$ XXX" + "Totais" + "Principal/Juros/Multa/..."
  Página 3+: Detalhamento parcela a parcela, incluindo linha DANOS MORAIS
"""
import re
from typing import Dict, Optional
from datetime import datetime

import fitz  # pymupdf


def _to_float(s: str) -> Optional[float]:
    """'R$ 79.322,71' → 79322.71"""
    if not s:
        return None
    s = s.strip().replace('R$', '').strip()
    if not s:
        return None
    try:
        return float(s.replace('.', '').replace(',', '.'))
    except ValueError:
        return None


def _parse_data_br(s: str) -> Optional[datetime]:
    """'11/10/1966' → datetime(1966, 10, 11)"""
    if not s:
        return None
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})', s.strip())
    if not m:
        return None
    try:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def parse_calculo(pdf_path: str) -> Dict:
    """Extrai dados do PDF de cálculo.

    Returns:
        {
            'nome_cliente': str,
            'data_nascimento': datetime ou None,
            'idade': int ou None,
            'sexo': str ('M' / 'F' / '-'),
            'termo_final': datetime ou None,
            'valor_total_geral': float (R$),
            'valor_principal': float (R$),
            'valor_juros': float (R$),
            'dano_moral_pleiteado_pdf': float ou None (extraído da linha DANOS MORAIS),
            'paginas': int,
        }
    """
    out = {
        'nome_cliente': None,
        'data_nascimento': None,
        'idade': None,
        'sexo': None,
        'termo_final': None,
        'valor_total_geral': None,
        'valor_principal': None,
        'valor_juros': None,
        'dano_moral_pleiteado_pdf': None,
        'paginas': 0,
    }

    doc = fitz.open(pdf_path)
    out['paginas'] = len(doc)
    if len(doc) == 0:
        doc.close()
        return out

    # === Página 1: Dados do cliente + Dados do cálculo ===
    p1 = doc[0].get_text()
    linhas = [l.strip() for l in p1.split('\n') if l.strip()]
    for i, l in enumerate(linhas):
        if l == 'Nome' and i + 1 < len(linhas):
            out['nome_cliente'] = linhas[i + 1]
        elif l == 'Data de nascimento' and i + 1 < len(linhas):
            out['data_nascimento'] = _parse_data_br(linhas[i + 1])
        elif l == 'Idade' and i + 1 < len(linhas):
            # '59 anos, 6 meses e 5 dias'
            m = re.match(r'(\d+)\s*anos', linhas[i + 1])
            if m:
                out['idade'] = int(m.group(1))
        elif l == 'Sexo' and i + 1 < len(linhas):
            out['sexo'] = linhas[i + 1]
        elif l == 'Termo final' and i + 1 < len(linhas):
            out['termo_final'] = _parse_data_br(linhas[i + 1])

    # === Página 2: Resultado + Totais ===
    if len(doc) > 1:
        p2 = doc[1].get_text()
        linhas2 = [l.strip() for l in p2.split('\n') if l.strip()]
        for i, l in enumerate(linhas2):
            # 'Total geral' seguido pelo valor na próxima linha
            if l == 'Total geral' and i + 1 < len(linhas2):
                out['valor_total_geral'] = _to_float(linhas2[i + 1])
            elif l == 'Valor Total Geral' and i + 1 < len(linhas2):
                # Variante: prefere este se ambos existirem (é o valor depois de honorários)
                v = _to_float(linhas2[i + 1])
                if v is not None:
                    out['valor_total_geral'] = v
            elif l == 'Principal' and i + 1 < len(linhas2):
                v = _to_float(linhas2[i + 1])
                if v is not None and out['valor_principal'] is None:
                    out['valor_principal'] = v
            elif l == 'Juros' and i + 1 < len(linhas2):
                v = _to_float(linhas2[i + 1])
                if v is not None and out['valor_juros'] is None:
                    out['valor_juros'] = v

    # === Páginas 3+: Procurar linha "DANOS MORAIS" ===
    # ATENÇÃO: o texto pymupdf vem QUEBRADO em pedaços. Padrão típico:
    #   Principal
    #   DANOS         ← linha 1
    #   MORAIS        ← linha 2
    #   01/07/2020    ← data
    #   R$            ← prefixo
    #   25.000,00     ← VALOR PLEITEADO
    #   1,000000
    #   ...
    #
    # Estratégia: detectar 'DANOS' seguido de 'MORAIS' em linhas adjacentes
    # (ou 'DANOS MORAIS' direto), depois pular data + 'R$' e capturar o valor.
    for pg in range(2, len(doc)):
        txt = doc[pg].get_text()
        linhas_pg = [l.strip() for l in txt.split('\n') if l.strip()]
        for i, l in enumerate(linhas_pg):
            # Detectar início do bloco DANOS MORAIS
            tem_danos_morais = (
                l == 'DANOS MORAIS' or
                (l == 'DANOS' and i + 1 < len(linhas_pg) and linhas_pg[i + 1] == 'MORAIS')
            )
            if not tem_danos_morais:
                continue
            # Procurar próximo valor numérico após data e R$
            for j in range(i + 1, min(i + 12, len(linhas_pg))):
                cand = linhas_pg[j]
                if re.fullmatch(r'\d{1,3}(?:\.\d{3})*,\d{2}', cand):
                    v = _to_float(cand)
                    if v and v >= 1000:  # dano moral é sempre ≥ R$ 1.000
                        out['dano_moral_pleiteado_pdf'] = v
                        break
            if out['dano_moral_pleiteado_pdf'] is not None:
                break
        if out['dano_moral_pleiteado_pdf'] is not None:
            break

    doc.close()
    return out


def eh_idoso(dados_calculo: Dict, data_referencia: Optional[datetime] = None) -> Optional[bool]:
    """Retorna True se a parte autora tem 60+ anos na data de referência (ou hoje).
    Retorna None se data de nascimento não foi encontrada."""
    if not dados_calculo.get('data_nascimento'):
        # Tentar usar a idade direta se tiver
        idade = dados_calculo.get('idade')
        if idade is not None:
            return idade >= 60
        return None
    nasc = dados_calculo['data_nascimento']
    ref = data_referencia or datetime.today()
    idade = ref.year - nasc.year - ((ref.month, ref.day) < (nasc.month, nasc.day))
    return idade >= 60


if __name__ == '__main__':
    import sys, io, os
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    base = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\GEORGE DA SILVA SOUZA - Marcio Teixeira'
    casos = [
        ('ITAÚ',    os.path.join(base, r'BANCO ITAÚ\2 AVERBAÇÃO NOVA INATIVO\9- CÁLCULO.pdf')),
        ('FACTA',   os.path.join(base, r'BANCO FACTA\1 AVERBAÇÃO NOVA INATIVO\10- CÁLCULO.pdf')),
        ('AGIBANK', os.path.join(base, r'BANCO AGIBANK\1 REFINANCIAMENTO INATIVO\10- CÁLCULO.pdf')),
        ('PAN',     os.path.join(base, r'BANCO PAN\1 AVERBAÇÃO NOVA INATIVO\10- CÁLCULO.pdf')),
    ]

    for label, p in casos:
        print(f'\n████ CÁLCULO {label} ████')
        if not os.path.exists(p):
            print(f'  NÃO EXISTE: {p}')
            continue
        res = parse_calculo(p)
        for k, v in res.items():
            print(f'  {k}: {v}')
        print(f'  É IDOSO?: {eh_idoso(res)}')
