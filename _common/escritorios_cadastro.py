# -*- coding: utf-8 -*-
"""Cadastro CANÔNICO de endereços dos escritórios do De Azevedo Lima & Rebonatto.

Fonte única de verdade para o placeholder `{{ESCRITORIO_ENDERECO_COMPOSTO}}`
em todas as skills.

Importação:
    sys.path.insert(0, str(Path(__file__).parent.parent / '_common'))
    from escritorios_cadastro import montar_endereco_escritorio_completo

Regra:
    Toda peça menciona MATRIZ (Joaçaba/SC) + UNIDADE DE APOIO na UF onde a ação
    é protocolada. A unidade de apoio varia conforme a UF.

Cobertura atual:
    AL / SE  → unidade de apoio em Arapiraca/AL
    AM       → unidade de apoio em Maués/AM
    BA / ES  → unidade de apoio em Salvador/BA  (endereço a confirmar)
    MG       → unidade de apoio em Uberlândia/MG  (endereço a confirmar)
    SC       → sem unidade de apoio (peça assinada na própria matriz)

Sincronizado com `procuradores.py::CIDADE_POR_UF`.
"""

# ============================================================
# MATRIZ — sempre a mesma em qualquer peça
# ============================================================
ENDERECO_MATRIZ = {
    'logradouro': 'Rua Frei Rogério',
    'numero': '541',
    'bairro': 'Centro',
    'cidade': 'Joaçaba',
    'uf': 'SC',
    'cep': '89600-000',
}

ENDERECO_MATRIZ_STR = (
    f"{ENDERECO_MATRIZ['logradouro']}, "
    f"{ENDERECO_MATRIZ['numero']}, "
    f"{ENDERECO_MATRIZ['bairro']}, "
    f"{ENDERECO_MATRIZ['cidade']}/{ENDERECO_MATRIZ['uf']}, "
    f"CEP {ENDERECO_MATRIZ['cep']}"
)


# ============================================================
# UNIDADES DE APOIO por UF (cidade onde o procurador está)
# ============================================================
UNIDADES_DE_APOIO = {
    'AL': {
        'logradouro': 'Rua Nossa Senhora da Salete',
        'numero': '597',
        'complemento': 'Sala 04',
        'bairro': 'Itapuã',
        'cidade': 'Arapiraca',
        'uf': 'AL',
        'cep': '57314-175',
    },
    'SE': {
        # SE compartilha a filial AL (Tiago/Alexandre cobrem ambos)
        'logradouro': 'Rua Nossa Senhora da Salete',
        'numero': '597',
        'complemento': 'Sala 04',
        'bairro': 'Itapuã',
        'cidade': 'Arapiraca',
        'uf': 'AL',
        'cep': '57314-175',
    },
    'AM': {
        'logradouro': 'Travessa Michiles',
        'numero': 's/n',
        'complemento': '',
        'bairro': 'Centro',
        'cidade': 'Maués',
        'uf': 'AM',
        'cep': '69195-000',
    },
    'BA': {
        # BA/ES compartilham a unidade de Salvador (Gabriel cobre ambos)
        'logradouro': '[A CONFIRMAR]',
        'numero': '[A CONFIRMAR]',
        'complemento': '',
        'bairro': '[A CONFIRMAR]',
        'cidade': 'Salvador',
        'uf': 'BA',
        'cep': '[A CONFIRMAR]',
    },
    'ES': {
        'logradouro': '[A CONFIRMAR]',
        'numero': '[A CONFIRMAR]',
        'complemento': '',
        'bairro': '[A CONFIRMAR]',
        'cidade': 'Salvador',
        'uf': 'BA',
        'cep': '[A CONFIRMAR]',
    },
    'MG': {
        'logradouro': '[A CONFIRMAR]',
        'numero': '[A CONFIRMAR]',
        'complemento': '',
        'bairro': '[A CONFIRMAR]',
        'cidade': 'Uberlândia',
        'uf': 'MG',
        'cep': '[A CONFIRMAR]',
    },
    # SC: sem unidade de apoio — peça é assinada na própria matriz.
    'SC': None,
}


def _formatar_endereco(d: dict) -> str:
    """Formata um dict de endereço como string canônica."""
    partes = [d['logradouro'], d['numero']]
    if d.get('complemento'):
        partes.append(d['complemento'])
    partes.append(d['bairro'])
    base = ', '.join(p for p in partes if p)
    return f"{base}, {d['cidade']}/{d['uf']}, CEP {d['cep']}"


def montar_endereco_escritorio_completo(uf: str) -> str:
    """Retorna a string composta: matriz + 'e unidade de apoio em' + filial.

    Quando a UF não tem unidade de apoio (caso SC ou UF desconhecida),
    retorna só a matriz.

    Args:
        uf: sigla da UF onde a peça será protocolada (ex: 'AM', 'AL', 'BA')

    Returns:
        String pronta para o placeholder `{{ESCRITORIO_ENDERECO_COMPOSTO}}`.

    Exemplos:
        >>> montar_endereco_escritorio_completo('AM')
        'Rua Frei Rogério, 541, Centro, Joaçaba/SC, CEP 89600-000, e unidade de apoio em Travessa Michiles, s/n, Centro, Maués/AM, CEP 69195-000'

        >>> montar_endereco_escritorio_completo('SC')
        'Rua Frei Rogério, 541, Centro, Joaçaba/SC, CEP 89600-000'
    """
    uf = (uf or '').upper().strip()
    apoio = UNIDADES_DE_APOIO.get(uf)
    if not apoio:
        return ENDERECO_MATRIZ_STR
    return f"{ENDERECO_MATRIZ_STR}, e unidade de apoio em {_formatar_endereco(apoio)}"


def obter_endereco_matriz() -> str:
    """Retorna apenas o endereço da matriz (Joaçaba/SC)."""
    return ENDERECO_MATRIZ_STR


def obter_endereco_apoio(uf: str) -> str | None:
    """Retorna apenas o endereço da unidade de apoio na UF, ou None se não houver."""
    uf = (uf or '').upper().strip()
    apoio = UNIDADES_DE_APOIO.get(uf)
    return _formatar_endereco(apoio) if apoio else None


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print('=== ESCRITORIO_ENDERECO_COMPOSTO por UF ===\n')
    for uf in ['AL', 'AM', 'BA', 'ES', 'MG', 'SC', 'SE']:
        end = montar_endereco_escritorio_completo(uf)
        print(f'[{uf}]')
        print(f'  {end}\n')
