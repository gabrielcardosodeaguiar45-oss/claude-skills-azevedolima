"""
Wrappers de num2words pt_BR para garantir uniformidade dos extensos
em todas as iniciais Bradesco.

REGRA: usar SEMPRE estas funções; nunca chamar num2words diretamente
de scripts ad hoc. Mantém formatação consistente (R$, "reais", "centavos",
"e" entre milhar e centena, etc.).
"""
from num2words import num2words


def fmt_moeda(valor):
    """Formata float como '1.212,17' (estilo brasileiro). Sem 'R$'."""
    s = f'{float(valor):,.2f}'
    return s.replace(',', '#').replace('.', ',').replace('#', '.')


def fmt_moeda_completa(valor):
    """Formata float como 'R$ 1.212,17'."""
    return f'R$ {fmt_moeda(valor)}'


def extenso_moeda(valor):
    """num2words em currency pt_BR. Devolve string como
    'um mil, duzentos e doze reais e dezessete centavos'."""
    return num2words(float(valor), lang='pt_BR', to='currency')


def extenso_cardinal(n):
    """num2words cardinal pt_BR. Devolve 'doze', 'cinquenta e um', etc."""
    return num2words(int(n), lang='pt_BR')


def extenso_ordinal(n):
    """num2words ordinal pt_BR. Devolve 'primeiro', 'décimo segundo', etc."""
    return num2words(int(n), lang='pt_BR', to='ordinal')


# ============================================================
# HELPER: monta dict de placeholders monetários a partir de descontos
# ============================================================
def montar_placeholders_monetarios(descontos, dano_moral=15000.0):
    """A partir da lista de descontos (parsear_tabela_descontos),
    devolve dict com TODOS os placeholders monetários da inicial.

    Args:
        descontos: list de dicts {data, descricao, valor} ou tuplas (data, valor)
        dano_moral: valor do dano moral em float (15000 isolada / N*5000 combinada)

    Returns:
        dict com keys:
            numero_desconto, desconto_extenso,
            inicio_desconto, fim_desconto,
            total_descontos, total_descontos_extenso,
            dobro_descontos, dobro_descontos_extenso,
            dano_moral_total, dano_moral_total_extenso,
            valor_causa, valor_causa_extenso
    """
    if not descontos:
        return {}

    # Normaliza tuplas → dicts
    if isinstance(descontos[0], tuple):
        descontos = [{'data': d, 'valor': v} for d, v in descontos]

    descontos_ord = sorted(descontos, key=lambda x: x['data'].split('/')[::-1])
    n = len(descontos_ord)
    total = sum(d['valor'] for d in descontos_ord)
    dobro = total * 2
    valor_causa = dobro + dano_moral

    return {
        'numero_desconto':           str(n),
        'desconto_extenso':          extenso_cardinal(n),
        'inicio_desconto':           descontos_ord[0]['data'],
        'fim_desconto':              descontos_ord[-1]['data'],
        'total_descontos':           fmt_moeda(total),
        'total_descontos_extenso':   extenso_moeda(total),
        'dobro_descontos':           fmt_moeda(dobro),
        'dobro_descontos_extenso':   extenso_moeda(dobro),
        'dano_moral_total':          fmt_moeda(dano_moral),
        'dano_moral_total_extenso':  extenso_moeda(dano_moral),
        'valor_causa':               fmt_moeda(valor_causa),
        'valor_causa_extenso':       extenso_moeda(valor_causa),
    }


# ============================================================
# HELPER: para teses combinadas, soma de DOBROS de cada tese
# ============================================================
def montar_placeholders_combinados(dobros_por_tese, dano_moral_total):
    """Para template combinada com 2+ teses.

    Args:
        dobros_por_tese: dict {tese: valor_dobro} (ex.: {'TARIFAS': 1234.56,
                          'MORA': 567.89})
        dano_moral_total: dano moral total agregado (ex.: N*5000)

    Returns:
        dict com totais agregados.
    """
    soma_dobros = sum(dobros_por_tese.values())
    valor_causa = soma_dobros + dano_moral_total

    return {
        'soma_dobros':              fmt_moeda(soma_dobros),
        'soma_dobros_extenso':      extenso_moeda(soma_dobros),
        'dano_moral_total':         fmt_moeda(dano_moral_total),
        'dano_moral_total_extenso': extenso_moeda(dano_moral_total),
        'valor_causa':              fmt_moeda(valor_causa),
        'valor_causa_extenso':      extenso_moeda(valor_causa),
    }
