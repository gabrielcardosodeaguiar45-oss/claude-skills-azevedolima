"""Parser do HISCRE (Histórico de Créditos do INSS).

O HISCRE é a fonte MAIS CONFIÁVEL de:
- CPF do beneficiário (campo formal do INSS)
- Data de nascimento
- NIT, NB, espécie do benefício
- DIB (Data Início Benefício)
- MR (mensalidade reajustada — renda BRUTA)
- Valor LÍQUIDO da última competência (renda real depositada na conta)

Para a inicial, usar:
- {{valor_renda_liquida}} = "Valor Líquido" do HISCRE (NÃO usar BASE DE CÁLCULO do HISCON,
  que é a renda BRUTA)
- {{cpf_autor}} = CPF do HISCRE (mais confiável que o KIT manuscrito)
"""
import re
from typing import Dict, Optional
from datetime import datetime

import fitz


def _to_float(s: str) -> Optional[float]:
    if not s:
        return None
    s = s.strip().replace('R$', '').strip()
    if not s:
        return None
    try:
        return float(s.replace('.', '').replace(',', '.'))
    except ValueError:
        return None


def _to_data(s: str) -> Optional[datetime]:
    if not s:
        return None
    m = re.search(r'(\d{2})/(\d{2})/(\d{4})', s)
    if not m:
        return None
    try:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def parse_hiscre(pdf_path: str) -> Dict:
    """Extrai dados do PDF de HISCRE.

    Returns:
        {
            'nome_autor': str,
            'cpf': str ('xxx.xxx.xxx-xx'),
            'nit': str,
            'data_nascimento': datetime,
            'nome_mae': str,
            'nb_beneficio': str,
            'especie_codigo': int,
            'especie_descricao': str ('APOSENTADORIA POR INCAPACIDADE...'),
            'aps': str (agência da previdência social),
            'dib': datetime (data início benefício),
            'dip': datetime (data início pagamento),
            'mr': float (mensalidade reajustada — RENDA BRUTA),
            'banco_pagador': str (ex.: '756 - BANCO SICOOB'),
            'op_banco_pagador': str (ex.: '843992 - PA98 LOJA AGIBANK CAMACARI - BA'),
            'competencia_referencia': str (ex.: '09/2025'),
            'valor_liquido': float (RENDA LÍQUIDA — usar como {{valor_renda_liquida}}),
            'data_pagamento': datetime,
        }
    """
    out = {
        'nome_autor': None,
        'cpf': None,
        'nit': None,
        'data_nascimento': None,
        'nome_mae': None,
        'nb_beneficio': None,
        'especie_codigo': None,
        'especie_descricao': None,
        'aps': None,
        'dib': None,
        'dip': None,
        'mr': None,
        'banco_pagador': None,
        'op_banco_pagador': None,
        'competencia_referencia': None,
        'valor_liquido': None,
        'data_pagamento': None,
    }

    doc = fitz.open(pdf_path)
    if len(doc) == 0:
        doc.close()
        return out

    p1 = doc[0].get_text()
    linhas = [l.strip() for l in p1.split('\n') if l.strip()]

    for i, l in enumerate(linhas):
        # CPF: "CPF: xxx.xxx.xxx-xx"
        m = re.match(r'CPF:\s*([\d.\-]+)', l)
        if m:
            out['cpf'] = m.group(1).strip()
            continue
        # NIT: "NIT: xxx.xxxxx.xx-x"
        m = re.match(r'NIT:\s*(.+)', l)
        if m:
            out['nit'] = m.group(1).strip()
            continue
        # Data nascimento
        m = re.match(r'Data de Nascimento:\s*(.+)', l)
        if m:
            out['data_nascimento'] = _to_data(m.group(1))
            continue
        # Nome
        m = re.match(r'Nome:\s*(.+)', l)
        if m:
            out['nome_autor'] = m.group(1).strip()
            continue
        # Nome da mãe (na linha SEGUINTE ao label "Nome da mãe:")
        if l == 'Nome da mãe:' and i > 0:
            # O parser do INSS lança o nome da mãe ANTES do label
            out['nome_mae'] = linhas[i - 1].strip()
        # NB
        m = re.match(r'NB:\s*(.+)', l)
        if m:
            out['nb_beneficio'] = m.group(1).strip()
            continue
        # Espécie
        m = re.match(r'Espécie:\s*(\d+)\s*-\s*(.+)', l)
        if m:
            out['especie_codigo'] = int(m.group(1))
            out['especie_descricao'] = m.group(2).strip()
            continue
        # APS
        m = re.match(r'APS:\s*(.+)', l)
        if m:
            out['aps'] = m.group(1).strip()
        # APS pode estar em formato "04001010 - AGÊNCIA DA PREVIDÊNCIA..."
        if re.match(r'^\d{8}\s*-\s*AG[ÊE]NCIA', l):
            out['aps'] = l
            continue
        # DIB: linha "Data de Início do Benefício (DIB):" + valor antes
        if l.startswith('Data de Início do Benefício'):
            # valor está NA LINHA ANTERIOR
            if i > 0:
                out['dib'] = _to_data(linhas[i - 1])
            continue
        if l.startswith('Data de Início do Pagamento'):
            if i > 0:
                out['dip'] = _to_data(linhas[i - 1])
            continue
        # MR (mensalidade reajustada)
        if l == 'MR:' and i > 0:
            out['mr'] = _to_float(linhas[i - 1])
            continue
        # Competência início (na linha seguinte ao label "Compet. Inicial:")
        if l == 'Compet. Inicial:' and i > 0:
            out['competencia_referencia'] = linhas[i - 1].strip()
            continue

    # === Procurar "Valor Líquido" e o valor R$ associado ===
    # Padrão típico:
    #   Valor
    #   Líquido          ← linha
    #   ... (outras colunas: Meio de Pagamento, Status, ...)
    #   09/2025          ← competência
    #   R$ 2.530,87 CCF - CONTA-CORRENTE     ← linha com valor + meio
    #
    # Estratégia: depois de achar 'Valor\nLíquido', a primeira linha que casa
    # 'R$ XXX,XX ALGUMA_COISA' tem o valor líquido.
    pos_val_liquido = -1
    for i, l in enumerate(linhas):
        if l == 'Valor' and i + 1 < len(linhas) and linhas[i + 1] == 'Líquido':
            pos_val_liquido = i
            break
    if pos_val_liquido >= 0:
        for j in range(pos_val_liquido + 2, min(pos_val_liquido + 25, len(linhas))):
            cand = linhas[j]
            m = re.match(r'^R\$\s*([\d.,]+)\s*(\w.*)?$', cand)
            if m:
                v = _to_float('R$ ' + m.group(1))
                if v and v > 100:  # sanity check
                    out['valor_liquido'] = v
                    break

    # === Banco pagador ===
    for l in linhas:
        m = re.match(r'^Banco:\s*(\d+)\s*-\s*([A-Z][A-Z\s]+?)(?:\s+OP:\s*(.+))?$', l)
        if m:
            out['banco_pagador'] = f'{m.group(1)} - {m.group(2).strip()}'
            if m.group(3):
                out['op_banco_pagador'] = m.group(3).strip()
            break

    # === Data pagamento ===
    for i, l in enumerate(linhas):
        if l == 'Data do' and i + 1 < len(linhas) and linhas[i + 1] == 'Pagamento':
            # Próximas linhas têm a data
            for j in range(i + 2, min(i + 8, len(linhas))):
                d = _to_data(linhas[j])
                if d:
                    out['data_pagamento'] = d
                    break
            break

    doc.close()
    return out


if __name__ == '__main__':
    import sys, io, os
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    base = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\GEORGE DA SILVA SOUZA - Marcio Teixeira'
    p = os.path.join(base, r'BANCO ITAÚ\2 AVERBAÇÃO NOVA INATIVO\9 - HISTÓRICO DE CRÉDITO.pdf')
    res = parse_hiscre(p)
    print('=== HISCRE — George da Silva Souza ===')
    for k, v in res.items():
        print(f'  {k}: {v}')
