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
        # 2026-05-16 — alertas de qualidade do parse (caso paradigma VILSON)
        # Preenchidos no fim de parse_hiscre() depois de detectar a competência.
        # Se não-vazio, o pipeline deve propagar como ALERTA na inicial.
        'alertas_qualidade': [],
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
    # Padrão típico de cada bloco de competência:
    #   Valor                          ← cabeçalho de tabela
    #   Líquido
    #   ... (outras colunas: Meio de Pagamento, Status, ...)
    #   09/2025                        ← competência
    #   R$ 2.530,87 CCF - CONTA-CORRENTE
    #
    # CORREÇÃO 2026-05-16 (caso VILSON): o parser anterior só lia a página 1
    # do PDF, pegando a PRIMEIRA competência (mais antiga) quando o HISCRE
    # está em ordem cronológica crescente (ex.: Vilson tem 55 páginas
    # 01/2020 → 02/2026; o valor de 01/2020 era R$ 689,92, mas em 02/2026
    # ele recebe R$ 988,43). Agora varremos TODAS as páginas e procuramos a
    # ÚLTIMA competência com status "Pago" + Valor Líquido.
    todas_linhas = []
    for pagina in range(len(doc)):
        txt_pag = doc[pagina].get_text()
        todas_linhas.extend(l.strip() for l in txt_pag.split('\n') if l.strip())

    # Estratégia robusta (tolerante à quebra de linhas do fitz):
    #   1. Caça toda ocorrência de "MM/AAAA" como linha isolada (= competência).
    #   2. Olha nas 30 linhas seguintes:
    #      - precisa achar "Pago" (confirma competência paga)
    #      - precisa achar "Origem: Maciça" (filtra fora pagamentos PAB
    #        suplementares avulsos, ex.: complementações)
    #      - precisa achar UM "R$ XXX,XX" (valor líquido — o PRIMEIRO)
    #   3. Mantém a competência (ano, mês, valor) MAIS RECENTE, ignorando
    #      meses 04 e 05 (antecipação de 13º distorce o valor mensal).
    #
    # Caso paradigma VILSON (2026-05-16): HISCRE tem 55 páginas.
    # - Página 53: 01/2026 R$ 154,07 Origem PAB (complementação avulsa).
    # - Página 54: 01/2026 R$ 988,43 Origem Maciça (pagamento mensal real).
    # Sem o filtro Maciça, o parser pegava 154,07.
    competencia_atual = None
    melhor_comp = None  # tupla (ano, mes, valor)
    melhor_comp_fallback = None  # idem, mas aceita meses 04/05 com 13º
    for idx, lin in enumerate(todas_linhas):
        m_comp = re.match(r'^(\d{2})/(\d{4})$', lin)
        if not m_comp:
            continue
        try:
            mes = int(m_comp.group(1))
            ano = int(m_comp.group(2))
        except ValueError:
            continue
        if not (1 <= mes <= 12 and 2000 <= ano <= 2100):
            continue
        # Filtra competências do CABEÇALHO ("Compet. Inicial: 01/2020" /
        # "Compet. Final: 02/2026"), que se repetem em cada página do HISCRE.
        # O fitz extrai essas linhas perto de "Compet. Inicial:" ou
        # "Compet. Final:" (até 3 linhas antes ou depois).
        vizinhanca = todas_linhas[max(0, idx - 3): idx] + todas_linhas[idx + 1: idx + 4]
        if any('Compet. Inicial' in v or 'Compet. Final' in v for v in vizinhanca):
            continue
        janela = todas_linhas[idx + 1: idx + 31]
        if not any('Pago' in c for c in janela):
            continue
        if not any('Maci' in c for c in janela):
            # 'Maci' cobre tanto "Maciça" quanto possíveis grafias sem cedilha
            continue
        valor_liq = None
        for cand in janela:
            m = re.match(r'^R\$\s*([\d.,]+)$', cand)
            if not m:
                m = re.match(r'^R\$\s*([\d.,]+)\s+\S', cand)
            if m:
                v = _to_float('R$ ' + m.group(1))
                if v and v > 50:
                    valor_liq = v
                    break
        if valor_liq is None:
            continue
        cand_tup = (ano, mes, valor_liq)
        # Sempre atualiza o fallback (aceita 04/05)
        if melhor_comp_fallback is None or cand_tup[:2] > melhor_comp_fallback[:2]:
            melhor_comp_fallback = cand_tup
        # 04 (1ª parcela 13º) e 05 (2ª parcela 13º + folha): valor distorcido,
        # só usa se não houver outro mês.
        if mes in (4, 5):
            continue
        if melhor_comp is None or cand_tup[:2] > melhor_comp[:2]:
            melhor_comp = cand_tup

    # Se SÓ existem meses 04/05, usa o fallback
    if melhor_comp is None:
        melhor_comp = melhor_comp_fallback

    if melhor_comp:
        out['valor_liquido'] = melhor_comp[2]
        out['competencia_referencia'] = f'{melhor_comp[1]:02d}/{melhor_comp[0]}'
    else:
        # Fallback: comportamento antigo (página 1) caso a varredura nova falhe
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
                    if v and v > 100:
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

    # === Patch — alertas de qualidade do parse (2026-05-16) ===
    # Caso paradigma VILSON: parser pegou competência 01/2020 (2 anos atrás)
    # quando o HISCRE tinha 55 páginas até 02/2026. Esses alertas detectam
    # o sintoma e forçam o pipeline a propagar para o operador.
    from datetime import datetime as _dt
    hoje = _dt.today()
    if not out.get('valor_liquido'):
        out['alertas_qualidade'].append(
            '🚨 VALOR LÍQUIDO do HISCRE não foi extraído. A inicial NÃO pode '
            'mencionar renda real do autor sem este dado. Verificar o PDF do '
            'HISCRE manualmente ou rejeitar a geração.'
        )
    if out.get('competencia_referencia'):
        try:
            mes_s, ano_s = out['competencia_referencia'].split('/')
            comp_ref_dt = _dt(int(ano_s), int(mes_s), 1)
            meses_atraso = (hoje.year - comp_ref_dt.year) * 12 + (hoje.month - comp_ref_dt.month)
            if meses_atraso > 12:
                out['alertas_qualidade'].append(
                    f'🚨 HISCRE com competência muito ANTIGA: '
                    f'{out["competencia_referencia"]} ({meses_atraso} meses '
                    f'atrás). Provável bug de parse — pegou competência '
                    f'inicial do extrato em vez da mais recente. CONFERIR '
                    f'antes do protocolo ou puxar HISCRE novo.'
                )
            elif meses_atraso > 6:
                out['alertas_qualidade'].append(
                    f'⚠ HISCRE com competência {out["competencia_referencia"]} '
                    f'({meses_atraso} meses atrás). Considere puxar HISCRE '
                    f'atualizado se o caso ainda está em fase de protocolo.'
                )
        except (ValueError, AttributeError):
            pass

    # Sanity check do valor líquido vs MR (salário bruto)
    if out.get('valor_liquido') and out.get('mr'):
        if out['valor_liquido'] > out['mr'] * 1.5:
            out['alertas_qualidade'].append(
                f'⚠ Valor líquido (R$ {out["valor_liquido"]:.2f}) muito acima '
                f'do MR/bruto (R$ {out["mr"]:.2f}). Provável captura indevida '
                f'de competência com 13º antecipado ou outro pagamento atípico. '
                f'CONFERIR.'
            )

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
