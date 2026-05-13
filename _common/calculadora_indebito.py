"""Calculadora de indébito para ações de empréstimo não contratado / RMC / RCC.

Regime de atualização (conforme pedido nas iniciais do escritório):
  - Correção monetária: INPC (responsabilidade civil — STJ)
  - Juros de mora: 1% ao mês SIMPLES (juros legais, art. 406 CC c/c CTN —
    regra anterior à Lei 14.905/2024). Para casos posteriores a 30/08/2024,
    o procurador deve revisar se aplica SELIC-IPCA.
  - Dobro: art. 42, p. único, CDC

Geração de planilha Excel com:
  - 1 aba "RESUMO" com totais por contrato
  - 1 aba por contrato detalhando cada parcela descontada

Não usar para iniciais Bradesco AM (Patrick) — essas têm regime próprio na
skill inicial-bradesco.
"""
import os
import re
from datetime import date
from typing import List, Dict, Optional, Tuple

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Import indices_oficiais — mesmo diretório
import sys
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)
from indices_oficiais import (inpc_acumulado_entre, corrigir_inpc,
                                juros_simples_mes, meses_entre,
                                INPC_ULTIMO_MES)


# ========================================
# Estilos
# ========================================
_BORDA = Border(
    left=Side(style='thin', color='999999'),
    right=Side(style='thin', color='999999'),
    top=Side(style='thin', color='999999'),
    bottom=Side(style='thin', color='999999'),
)
_FILL_TITULO = PatternFill('solid', fgColor='305496')
_FILL_CAB = PatternFill('solid', fgColor='8EA9DB')
_FILL_TOTAL = PatternFill('solid', fgColor='FFE699')
_FILL_DOBRO = PatternFill('solid', fgColor='C6EFCE')
_FONT_TITULO = Font(name='Calibri', size=12, bold=True, color='FFFFFF')
_FONT_CAB = Font(name='Calibri', size=11, bold=True)
_FONT_TOTAL = Font(name='Calibri', size=11, bold=True)
_CENTER = Alignment(horizontal='center', vertical='center', wrap_text=True)
_LEFT = Alignment(horizontal='left', vertical='center', wrap_text=True)
_RIGHT = Alignment(horizontal='right', vertical='center')


# ========================================
# Helpers
# ========================================

def _parse_brl(valor_str: str) -> float:
    """'R$37,10' / '37,10' / '1.234,56' → float."""
    if isinstance(valor_str, (int, float)):
        return float(valor_str)
    if not valor_str:
        return 0.0
    s = str(valor_str).strip()
    s = re.sub(r'[Rr]\$\s*', '', s)
    s = s.replace('.', '').replace(',', '.').strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_competencia(comp_str: str) -> Optional[Tuple[int, int]]:
    """'08/2020' → (2020, 8). Retorna None se não parsear."""
    if not comp_str:
        return None
    m = re.match(r'(\d{1,2})/(\d{4})', str(comp_str).strip())
    if not m:
        return None
    mes, ano = int(m.group(1)), int(m.group(2))
    if 1 <= mes <= 12:
        return (ano, mes)
    return None


def _iter_meses(ini: Tuple[int, int], fim: Tuple[int, int]):
    a, m = ini
    while (a, m) <= fim:
        yield (a, m)
        m += 1
        if m > 12:
            m = 1
            a += 1


# ========================================
# Cálculo por contrato
# ========================================

def calcular_contrato(contrato: Dict, data_apuracao: Optional[date] = None,
                       taxa_juros_mes_pct: float = 1.0) -> Dict:
    """Calcula o indébito de um contrato.

    Args:
        contrato: dict com campos:
            - numero / contrato
            - banco / banco_nome
            - valor_parcela / valor_parcela_str (R$ XX,XX ou float)
            - qtd_parcelas (int)
            - competencia_inicio / competencia_inicio_str (MM/AAAA)
            - competencia_fim / competencia_fim_str (MM/AAAA, opcional)
            - situacao (Ativo / Excluído / Encerrado)
        data_apuracao: data do cálculo. Default = hoje.
        taxa_juros_mes_pct: % ao mês (default 1.0 = juros legais)

    Returns:
        dict {
            'contrato': str,
            'banco': str,
            'qtd_parcelas': int,
            'valor_parcela': float,
            'meses_pagos': int,
            'parcelas': [list de dicts mensais],
            'soma_pagos': float (sem correção),
            'soma_corrigida': float (INPC),
            'soma_juros': float,
            'total_simples': float (corrigido + juros),
            'total_dobrado': float (art. 42 CDC)
        }
    """
    if data_apuracao is None:
        data_apuracao = date.today()
    # Coerções
    numero = str(contrato.get('numero') or contrato.get('contrato') or '')
    banco = str(contrato.get('banco_nome') or contrato.get('banco') or '')
    vp = (contrato.get('valor_parcela_str') or contrato.get('valor_parcela')
          or contrato.get('valor_parcela_float') or 0)
    valor_parcela = _parse_brl(vp) if not isinstance(vp, (int, float)) else float(vp)
    qtd_parcelas = int(contrato.get('qtd_parcelas') or 0)
    comp_ini = (_parse_competencia(contrato.get('competencia_inicio_str')) or
                _parse_competencia(contrato.get('competencia_inicio')))
    comp_fim_extra = (_parse_competencia(contrato.get('competencia_fim_str')) or
                     _parse_competencia(contrato.get('competencia_fim')))
    situacao = (contrato.get('situacao') or '').strip()

    parcelas = []
    if not comp_ini or qtd_parcelas <= 0 or valor_parcela <= 0:
        return {
            'contrato': numero,
            'banco': banco,
            'qtd_parcelas': qtd_parcelas,
            'valor_parcela': valor_parcela,
            'meses_pagos': 0,
            'parcelas': [],
            'soma_pagos': 0,
            'soma_corrigida': 0,
            'soma_juros': 0,
            'total_simples': 0,
            'total_dobrado': 0,
            'alerta': 'Dados insuficientes (sem competência início ou qtd_parcelas ou valor_parcela)',
        }

    # Determinar último mês a contar
    # Regra:
    #   - Se há competencia_fim_str (encerrado): vai até ela
    #   - Senão (ativo): conta até qtd_parcelas OU mês de hoje, o que for primeiro
    a_ini, m_ini = comp_ini
    if comp_fim_extra:
        a_fim, m_fim = comp_fim_extra
    else:
        # Mês limite = comp_ini + qtd_parcelas - 1
        m_total = m_ini + qtd_parcelas - 1
        a_fim = a_ini + (m_total - 1) // 12
        m_fim = ((m_total - 1) % 12) + 1
    # Não passa do mês de apuração
    if (a_fim, m_fim) > (data_apuracao.year, data_apuracao.month):
        a_fim, m_fim = data_apuracao.year, data_apuracao.month

    mes_apuracao = (data_apuracao.year, data_apuracao.month)
    for (ano, mes) in _iter_meses((a_ini, m_ini), (a_fim, m_fim)):
        fator_inpc = inpc_acumulado_entre((ano, mes), mes_apuracao)
        n_meses = meses_entre(date(ano, mes, 1), data_apuracao)
        valor_corr = valor_parcela * fator_inpc
        juros = valor_parcela * (taxa_juros_mes_pct / 100.0) * n_meses
        total_simples = valor_corr + juros
        total_dobrado = total_simples * 2
        parcelas.append({
            'competencia': f'{mes:02d}/{ano}',
            'valor_original': valor_parcela,
            'fator_inpc': fator_inpc,
            'valor_corrigido': valor_corr,
            'meses_juros': n_meses,
            'juros': juros,
            'total_simples': total_simples,
            'total_dobrado': total_dobrado,
        })

    soma_pagos = sum(p['valor_original'] for p in parcelas)
    soma_corrigida = sum(p['valor_corrigido'] for p in parcelas)
    soma_juros = sum(p['juros'] for p in parcelas)
    total_simples = sum(p['total_simples'] for p in parcelas)
    total_dobrado = sum(p['total_dobrado'] for p in parcelas)
    return {
        'contrato': numero,
        'banco': banco,
        'qtd_parcelas': qtd_parcelas,
        'valor_parcela': valor_parcela,
        'meses_pagos': len(parcelas),
        'parcelas': parcelas,
        'soma_pagos': soma_pagos,
        'soma_corrigida': soma_corrigida,
        'soma_juros': soma_juros,
        'total_simples': total_simples,
        'total_dobrado': total_dobrado,
        'situacao': situacao,
    }


# ========================================
# Geração de Excel
# ========================================

def _set_brl(cell, valor):
    cell.value = valor
    cell.number_format = 'R$ #,##0.00'
    cell.alignment = _RIGHT


def calcular_dano_moral(n_contratos: int) -> Dict:
    """Calcula o dano moral pleiteado conforme regra fixa do escritório:
      - 1 contrato                → R$ 15.000,00
      - 2+ contratos (cumulativo) → R$ 5.000,00 × N

    Returns: {'valor': float, 'criterio': str}
    """
    if n_contratos <= 0:
        return {'valor': 0.0, 'criterio': 'sem contratos'}
    if n_contratos == 1:
        return {'valor': 15000.0,
                'criterio': 'R$ 15.000,00 (1 contrato isolado)'}
    return {'valor': 5000.0 * n_contratos,
            'criterio': f'R$ 5.000,00 × {n_contratos} contratos'}


def gerar_excel_indebito(
    contratos: List[Dict],
    cliente_nome: str,
    output_path: str,
    data_apuracao: Optional[date] = None,
    taxa_juros_mes_pct: float = 1.0,
) -> str:
    """Gera planilha Excel com cálculo de indébito por contrato.

    Cada contrato vira uma ABA com a tabela mensal de parcelas + uma aba
    "RESUMO" com totais e o total geral.

    Args:
        contratos: lista de dicts (formato extrator_hiscon)
        cliente_nome: nome para exibir no cabeçalho
        output_path: caminho do .xlsx
        data_apuracao: data do cálculo (default hoje)
        taxa_juros_mes_pct: 1.0 default

    Returns:
        output_path
    """
    if data_apuracao is None:
        data_apuracao = date.today()

    # Calcular todos
    calculos = [calcular_contrato(c, data_apuracao, taxa_juros_mes_pct)
                for c in contratos]

    wb = Workbook()
    # Remove aba padrão
    wb.remove(wb.active)

    # === ABA RESUMO ===
    ws = wb.create_sheet('RESUMO', 0)
    ws.merge_cells('A1:H1')
    ws['A1'] = f'CÁLCULO DE INDÉBITO — {cliente_nome.upper()}'
    ws['A1'].font = _FONT_TITULO
    ws['A1'].fill = _FILL_TITULO
    ws['A1'].alignment = _CENTER

    ws['A2'] = f'Data de apuração: {data_apuracao.strftime("%d/%m/%Y")}'
    ws['A2'].font = Font(bold=True, italic=True)
    ws.merge_cells('A2:H2')

    ws['A3'] = (f'Regime: correção INPC + juros {taxa_juros_mes_pct:.1f}% a.m. '
                f'simples + dobro (art. 42 CDC). Último INPC disponível: '
                f'{INPC_ULTIMO_MES[1]:02d}/{INPC_ULTIMO_MES[0]}')
    ws['A3'].font = Font(italic=True, size=10)
    ws.merge_cells('A3:H3')

    # Cabeçalhos
    cabs = ['Contrato', 'Banco', 'Situação', 'Valor parcela', 'Meses descontados',
            'Total descontado', 'Corrigido + juros', 'TOTAL EM DOBRO']
    for i, c in enumerate(cabs, 1):
        cell = ws.cell(row=5, column=i, value=c)
        cell.font = _FONT_CAB
        cell.fill = _FILL_CAB
        cell.alignment = _CENTER
        cell.border = _BORDA

    # Linhas de cada contrato
    row = 6
    for calc in calculos:
        ws.cell(row=row, column=1, value=calc['contrato']).border = _BORDA
        ws.cell(row=row, column=2, value=calc['banco']).border = _BORDA
        ws.cell(row=row, column=3, value=calc.get('situacao', '')).border = _BORDA
        _set_brl(ws.cell(row=row, column=4), calc['valor_parcela'])
        ws.cell(row=row, column=4).border = _BORDA
        ws.cell(row=row, column=5, value=calc['meses_pagos']).alignment = _CENTER
        ws.cell(row=row, column=5).border = _BORDA
        _set_brl(ws.cell(row=row, column=6), calc['soma_pagos'])
        ws.cell(row=row, column=6).border = _BORDA
        _set_brl(ws.cell(row=row, column=7), calc['total_simples'])
        ws.cell(row=row, column=7).border = _BORDA
        _set_brl(ws.cell(row=row, column=8), calc['total_dobrado'])
        ws.cell(row=row, column=8).border = _BORDA
        ws.cell(row=row, column=8).fill = _FILL_DOBRO
        ws.cell(row=row, column=8).font = Font(bold=True)
        row += 1

    # Linha de SUBTOTAL (somatório das colunas dos contratos)
    soma_pagos_total = sum(c['soma_pagos'] for c in calculos)
    soma_simples_total = sum(c['total_simples'] for c in calculos)
    soma_dobrado_total = sum(c['total_dobrado'] for c in calculos)
    ws.cell(row=row, column=1, value='SUBTOTAL (descontos em dobro)').font = _FONT_TOTAL
    ws.cell(row=row, column=1).fill = _FILL_TOTAL
    for col in range(2, 6):
        ws.cell(row=row, column=col).fill = _FILL_TOTAL
    _set_brl(ws.cell(row=row, column=6), soma_pagos_total)
    ws.cell(row=row, column=6).fill = _FILL_TOTAL
    ws.cell(row=row, column=6).font = _FONT_TOTAL
    _set_brl(ws.cell(row=row, column=7), soma_simples_total)
    ws.cell(row=row, column=7).fill = _FILL_TOTAL
    ws.cell(row=row, column=7).font = _FONT_TOTAL
    _set_brl(ws.cell(row=row, column=8), soma_dobrado_total)
    ws.cell(row=row, column=8).fill = _FILL_TOTAL
    ws.cell(row=row, column=8).font = Font(bold=True, color='006100', size=12)
    for col in range(1, 9):
        ws.cell(row=row, column=col).border = _BORDA
    row += 1

    # ===== Dano moral =====
    n_contratos = len(calculos)
    dm = calcular_dano_moral(n_contratos)
    ws.cell(row=row, column=1,
            value='DANO MORAL (regra fixa do escritório)').font = _FONT_TOTAL
    ws.cell(row=row, column=1).fill = _FILL_TOTAL
    for col in range(2, 8):
        ws.cell(row=row, column=col).fill = _FILL_TOTAL
    ws.cell(row=row, column=2, value=dm['criterio']).font = Font(italic=True)
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
    _set_brl(ws.cell(row=row, column=8), dm['valor'])
    ws.cell(row=row, column=8).fill = _FILL_TOTAL
    ws.cell(row=row, column=8).font = Font(bold=True, color='006100', size=12)
    for col in range(1, 9):
        ws.cell(row=row, column=col).border = _BORDA
    row += 1

    # ===== TOTAL GERAL (dobrado + dano moral) =====
    total_geral = soma_dobrado_total + dm['valor']
    ws.cell(row=row, column=1, value='TOTAL GERAL DA AÇÃO').font = Font(
        name='Calibri', size=13, bold=True, color='FFFFFF')
    ws.cell(row=row, column=1).fill = _FILL_TITULO
    for col in range(2, 8):
        ws.cell(row=row, column=col).fill = _FILL_TITULO
    ws.cell(row=row, column=2,
            value=f'Subtotal em dobro + Dano moral').font = Font(
        italic=True, color='FFFFFF')
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
    _set_brl(ws.cell(row=row, column=8), total_geral)
    ws.cell(row=row, column=8).fill = _FILL_TITULO
    ws.cell(row=row, column=8).font = Font(
        name='Calibri', size=14, bold=True, color='FFFF00')
    ws.row_dimensions[row].height = 28
    for col in range(1, 9):
        ws.cell(row=row, column=col).border = _BORDA
    row += 1

    # Larguras
    for col, w in zip('ABCDEFGH', [22, 32, 12, 14, 12, 16, 18, 22]):
        ws.column_dimensions[col].width = w
    ws.row_dimensions[1].height = 24
    ws.row_dimensions[5].height = 30

    # === UMA ABA POR CONTRATO ===
    for idx, calc in enumerate(calculos):
        # Nome da aba: número do contrato (máx 31 chars)
        nome_aba = f"{idx+1:02d}_{calc['contrato']}"[:31]
        ws_c = wb.create_sheet(nome_aba)

        ws_c.merge_cells('A1:H1')
        ws_c['A1'] = (f'CONTRATO Nº {calc["contrato"]} — {calc["banco"]}')
        ws_c['A1'].font = _FONT_TITULO
        ws_c['A1'].fill = _FILL_TITULO
        ws_c['A1'].alignment = _CENTER

        info_row = 2
        ws_c[f'A{info_row}'] = (f'Situação: {calc.get("situacao", "")}  •  '
                                 f'Valor parcela: R$ {calc["valor_parcela"]:,.2f}  •  '
                                 f'Meses descontados: {calc["meses_pagos"]}  •  '
                                 f'Apuração: {data_apuracao.strftime("%d/%m/%Y")}')
        ws_c[f'A{info_row}'].font = Font(italic=True, size=10)
        ws_c.merge_cells(f'A{info_row}:H{info_row}')

        # Cabeçalho tabela
        cabs2 = ['Competência', 'Valor original', 'Fator INPC',
                  'Valor corrigido', 'Meses (juros)', 'Juros 1% a.m.',
                  'Total simples', 'Total em dobro (art. 42 CDC)']
        for i, c in enumerate(cabs2, 1):
            cell = ws_c.cell(row=4, column=i, value=c)
            cell.font = _FONT_CAB
            cell.fill = _FILL_CAB
            cell.alignment = _CENTER
            cell.border = _BORDA
        ws_c.row_dimensions[4].height = 30

        # Linhas das parcelas
        r2 = 5
        for p in calc['parcelas']:
            ws_c.cell(row=r2, column=1, value=p['competencia']).alignment = _CENTER
            _set_brl(ws_c.cell(row=r2, column=2), p['valor_original'])
            cell_fator = ws_c.cell(row=r2, column=3, value=p['fator_inpc'])
            cell_fator.number_format = '0.000000'
            cell_fator.alignment = _CENTER
            _set_brl(ws_c.cell(row=r2, column=4), p['valor_corrigido'])
            ws_c.cell(row=r2, column=5, value=p['meses_juros']).alignment = _CENTER
            _set_brl(ws_c.cell(row=r2, column=6), p['juros'])
            _set_brl(ws_c.cell(row=r2, column=7), p['total_simples'])
            _set_brl(ws_c.cell(row=r2, column=8), p['total_dobrado'])
            ws_c.cell(row=r2, column=8).fill = _FILL_DOBRO
            ws_c.cell(row=r2, column=8).font = Font(bold=True)
            for col in range(1, 9):
                ws_c.cell(row=r2, column=col).border = _BORDA
            r2 += 1

        # Linha total
        ws_c.cell(row=r2, column=1, value='TOTAL').font = _FONT_TOTAL
        for col in range(1, 6):
            ws_c.cell(row=r2, column=col).fill = _FILL_TOTAL
        _set_brl(ws_c.cell(row=r2, column=2), calc['soma_pagos'])
        ws_c.cell(row=r2, column=2).fill = _FILL_TOTAL
        ws_c.cell(row=r2, column=2).font = _FONT_TOTAL
        _set_brl(ws_c.cell(row=r2, column=4), calc['soma_corrigida'])
        ws_c.cell(row=r2, column=4).fill = _FILL_TOTAL
        ws_c.cell(row=r2, column=4).font = _FONT_TOTAL
        _set_brl(ws_c.cell(row=r2, column=6), calc['soma_juros'])
        ws_c.cell(row=r2, column=6).fill = _FILL_TOTAL
        ws_c.cell(row=r2, column=6).font = _FONT_TOTAL
        _set_brl(ws_c.cell(row=r2, column=7), calc['total_simples'])
        ws_c.cell(row=r2, column=7).fill = _FILL_TOTAL
        ws_c.cell(row=r2, column=7).font = _FONT_TOTAL
        _set_brl(ws_c.cell(row=r2, column=8), calc['total_dobrado'])
        ws_c.cell(row=r2, column=8).fill = _FILL_TOTAL
        ws_c.cell(row=r2, column=8).font = Font(bold=True, color='006100', size=12)
        for col in range(1, 9):
            ws_c.cell(row=r2, column=col).border = _BORDA

        # Larguras
        for col, w in zip('ABCDEFGH', [12, 14, 11, 16, 11, 14, 16, 20]):
            ws_c.column_dimensions[col].width = w
        ws_c.row_dimensions[1].height = 24

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    wb.save(output_path)
    return output_path


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    # Teste rápido
    contratos_teste = [
        {
            'numero': '622902175',
            'banco_nome': 'BANCO ITAU CONSIGNADO SA',
            'valor_parcela': 'R$49,50',
            'qtd_parcelas': 84,
            'competencia_inicio_str': '08/2020',
            'competencia_fim_str': '07/2027',
            'situacao': 'Ativo',
        },
    ]
    out = gerar_excel_indebito(contratos_teste, 'TESTE FULANO',
                                 r'C:\Users\gabri\OneDrive\Área de Trabalho\CLAUDE\_teste_calculo.xlsx')
    print(f'Excel gerado: {out}')
