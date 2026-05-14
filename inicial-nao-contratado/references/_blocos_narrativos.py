# -*- coding: utf-8 -*-
"""Geradores de blocos narrativos concatenados (Opção 4) para
templates AL/MG (`inicial-jeal-*`, `inicial-jemg-*`, `inicial-jfal-*`).

Substitui os marcadores únicos:
- {{BLOCO_CONTRATOS_FRAUDULENTOS}} no par "No que diz respeito ..."
- {{BLOCO_PEDIDO_DECLARACAO}} no par "Declarar a inexistência ..."

Para 1 contrato → texto natural sem enumeração.
Para N contratos → texto enumerado com (i)/(ii)/(iii) e conector "; e por fim".

Helpers públicos:
    gerar_bloco_contratos_fraudulentos(contratos)
    gerar_bloco_pedido_declaracao(contratos, nb_beneficio)
    normalizar_banco_reu(nome) -> str
"""
from typing import List, Dict
import re

# Romanos minúsculos para enumeração inline (i, ii, iii, ...)
_ROMANO = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x',
           'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx']


def normalizar_banco_reu(nome: str) -> str:
    """Padroniza o nome do banco em CAIXA ALTA, sem espaço duplicado.
    Ex.: 'Banco Pan S.A.' → 'BANCO PAN S.A.'"""
    if not nome:
        return ''
    s = re.sub(r'\s+', ' ', nome).strip().upper()
    return s


def _fmt_brl(v) -> str:
    if v is None or v == '':
        return ''
    try:
        f = float(v)
    except (ValueError, TypeError):
        return str(v)
    return f'{f:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.')


def _extenso_brl(v) -> str:
    """Wrapper opcional. Se num2words não disponível, devolve vazio."""
    if v is None or v == '':
        return ''
    try:
        from num2words import num2words
        return num2words(float(v), lang='pt_BR', to='currency')
    except Exception:
        return ''


def _segmento_contrato(c: Dict, banco_reu_nome: str = '') -> str:
    """Compõe a sentença descritiva de UM contrato.
    Espera dict com chaves: numero, valor_emprestado, valor_parcela,
    qtd_parcelas, competencia_inicio, competencia_fim (opcional)."""
    numero = c.get('numero') or c.get('contrato_numero') or '___'
    v_empr = _fmt_brl(c.get('valor_emprestado'))
    v_par = _fmt_brl(c.get('valor_parcela'))
    qtd = c.get('qtd_parcelas') or c.get('contrato_qtd_parcelas') or '___'
    inicio = c.get('competencia_inicio') or c.get('contrato_competencia_inicio') or '___'
    ext_empr = _extenso_brl(c.get('valor_emprestado'))
    ext_par = _extenso_brl(c.get('valor_parcela'))

    sentenca = (
        f'a primeira parcela descontada do benefício da parte autora foi na '
        f'competência {inicio}, de um total de {qtd} parcelas, no valor de '
        f'R$ {v_par}'
    )
    if ext_par:
        sentenca += f' ({ext_par})'
    sentenca += f', relativas a um empréstimo consignado no valor de R$ {v_empr}'
    if ext_empr:
        sentenca += f' ({ext_empr})'
    sentenca += f', contrato nº {numero}'
    if banco_reu_nome:
        sentenca += f', cuja operação foi realizada pelo {banco_reu_nome}, ora requerido'
    sentenca += '.'
    return sentenca


def gerar_bloco_contratos_fraudulentos(contratos: List[Dict],
                                         banco_reu_nome: str = '') -> str:
    """Gera o conteúdo do parágrafo 'No que diz respeito...' em prosa natural.

    1 contrato → 'No que diz respeito ao referido empréstimo, cumpre informar
                  que: a primeira parcela ...'
    N contratos → 'No que diz respeito aos referidos empréstimos, cumpre
                   informar que: (i) quanto ao contrato nº X, ... ; (ii)
                   quanto ao contrato nº Y, ... ; e por fim, (iii) quanto
                   ao contrato nº Z, ...'
    """
    if not contratos:
        return ''
    n = len(contratos)
    if n == 1:
        return ('No que diz respeito ao referido empréstimo, cumpre informar '
                'que: ' + _segmento_contrato(contratos[0], banco_reu_nome))

    # N >= 2
    partes = []
    for idx, c in enumerate(contratos):
        rom = _ROMANO[idx] if idx < len(_ROMANO) else str(idx + 1)
        numero = c.get('numero') or c.get('contrato_numero') or '___'
        seg = _segmento_contrato(c, banco_reu_nome)
        # Reescreve para inserir "(rom) quanto ao contrato nº X," no início.
        # Pega o segmento completo e tira o trecho ", contrato nº ..., cuja
        # operação..., ora requerido." pra evitar repetição (já citado no
        # prefixo). Mantém a parte da primeira parcela / valor.
        # seg = "a primeira parcela ... R$ X,XX (...), relativas ... R$ Y,YY (...), contrato nº NNN, cuja operação foi realizada pelo BANCO X, ora requerido."
        antes_contrato = seg.split(', contrato nº ', 1)[0]  # tudo antes de ", contrato nº"
        seg_reescrito = f'({rom}) quanto ao contrato nº {numero}, {antes_contrato}'
        if seg_reescrito.endswith('.'):
            seg_reescrito = seg_reescrito[:-1]
        partes.append(seg_reescrito)

    # Conector entre o penúltimo e o último: "; e por fim, "
    miolo = '; '.join(partes[:-1])
    return (f'No que diz respeito aos referidos empréstimos, cumpre '
            f'informar que: {miolo}; e por fim, {partes[-1]}.')


def gerar_bloco_pedido_declaracao(contratos: List[Dict],
                                    nb_beneficio: str = '') -> str:
    """Gera o conteúdo do pedido 'Declarar a inexistência ...' em prosa natural.

    1 contrato → 'do empréstimo consignado no valor de R$ X, contrato nº Y -
                  com descontos de R$ Z mensais, com inclusão em DD/MM/AAAA,
                  início de desconto em DD/MM/AAAA, no benefício
                  previdenciário NB'
    N contratos → '(i) do empréstimo consignado ... ; (ii) do empréstimo ... ;
                   e (iii) do empréstimo ...'

    Nota: o template já tem 'Declarar a inexistência ' antes do marcador,
    então este helper retorna SEM esse prefixo.
    """
    if not contratos:
        return ''

    def _seg_pedido(c, prefixo=''):
        numero = c.get('numero') or c.get('contrato_numero') or '___'
        v_empr = _fmt_brl(c.get('valor_emprestado'))
        v_par = _fmt_brl(c.get('valor_parcela'))
        ext_empr = _extenso_brl(c.get('valor_emprestado'))
        ext_par = _extenso_brl(c.get('valor_parcela'))
        data_inc = c.get('data_inclusao') or c.get('contrato_data_inclusao') or '___'
        comp_ini = c.get('competencia_inicio') or c.get('contrato_competencia_inicio') or '___'

        s = f'{prefixo}do empréstimo consignado no valor de R$ {v_empr}'
        if ext_empr:
            s += f' ({ext_empr})'
        s += f', contrato nº {numero} - com descontos de R$ {v_par}'
        if ext_par:
            s += f' ({ext_par})'
        s += (f' mensais, com inclusão em {data_inc}, início de desconto em '
              f'{comp_ini}, no benefício previdenciário {nb_beneficio}')
        return s

    n = len(contratos)
    if n == 1:
        return _seg_pedido(contratos[0])

    partes = []
    for idx, c in enumerate(contratos):
        rom = _ROMANO[idx] if idx < len(_ROMANO) else str(idx + 1)
        partes.append(_seg_pedido(c, prefixo=f'({rom}) '))
    miolo = '; '.join(partes[:-1])
    return f'{miolo}; e {partes[-1]}'


# ============================================================
# Demo / smoke test
# ============================================================
if __name__ == '__main__':
    contratos_demo = [
        {'numero': '3880089838', 'valor_emprestado': 2171.24,
         'valor_parcela': 49.00, 'qtd_parcelas': 84,
         'competencia_inicio': '01/06/2024',
         'data_inclusao': '31/05/2024'},
        {'numero': '3880089839', 'valor_emprestado': 1500.00,
         'valor_parcela': 35.00, 'qtd_parcelas': 60,
         'competencia_inicio': '01/07/2024',
         'data_inclusao': '30/06/2024'},
    ]
    print('=== 1 contrato ===')
    print(gerar_bloco_contratos_fraudulentos(contratos_demo[:1], 'BANCO PAN S.A.'))
    print()
    print(gerar_bloco_pedido_declaracao(contratos_demo[:1], '149.139.433-9'))
    print()
    print('=== 2 contratos ===')
    print(gerar_bloco_contratos_fraudulentos(contratos_demo, 'BANCO PAN S.A.'))
    print()
    print(gerar_bloco_pedido_declaracao(contratos_demo, '149.139.433-9'))
    print()
    print('=== Normalização ===')
    print(normalizar_banco_reu('Banco Pan S.A.'))
    print(normalizar_banco_reu('  banco  itaú  consignado   '))
