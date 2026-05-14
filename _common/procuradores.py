# -*- coding: utf-8 -*-
"""Cadastro CANÔNICO de procuradores do escritório De Azevedo Lima & Rebonatto.

Fonte única de verdade para:
- skills/inicial-nao-contratado/references/escritorios.py
- skills/notificacao-extrajudicial/_run_notificacoes.py
- (futuras skills que precisarem)

Importação:
    sys.path.insert(0, str(Path(__file__).parent.parent / '_common'))
    from procuradores import ADVOGADOS_POR_UF, PROCURADORES, SOCIOS_ADMIN

Regras de negócio:
- Sócios administradores podem usar peças COM logo do escritório
- Demais procuradores devem usar versões SEM logo
- Em AM, mesmo que outros constem na procuração, é Patrick que protocola
- Endereço default por UF segue regra: matriz Joaçaba/SC + filial de apoio
"""

# Sócios administradores — autorizados a usar peças COM logo
SOCIOS_ADMIN = {'tiago', 'eduardo'}


# Procuradores em formato canônico
PROCURADORES = {
    'tiago': {
        'nome': 'Tiago de Azevedo Lima',
        'nome_maiusculo': 'TIAGO DE AZEVEDO LIMA',
        'genero': 'M',
        'oab_principal': 'OAB/SC 36672',
        'oabs_por_uf': {
            'SC': 'OAB/SC 36672',
            'AL': 'OAB/AL 20906A',
            'BA': 'OAB/BA 80006',
            'MG': 'OAB/MG 228433',
            'RS': 'OAB/RS 139330A',
            'SE': 'OAB/SE 1850A',
        },
        'jurisdicoes': ['AL', 'SE'],
        'eh_socio_admin': True,
    },
    'eduardo': {
        'nome': 'Eduardo Fernando Rebonatto',
        'nome_maiusculo': 'EDUARDO FERNANDO REBONATTO',
        'genero': 'M',
        'oab_principal': 'OAB/SC 36592',
        'oabs_por_uf': {
            'SC': 'OAB/SC 36592',
            'AM': 'OAB/AM A2118',
            'BA': 'OAB/BA 77088',
            'PR': 'OAB/PR 132523',
        },
        'jurisdicoes': ['AM'],
        'eh_socio_admin': True,
    },
    'patrick': {
        'nome': 'Patrick Willian da Silva',
        'nome_maiusculo': 'PATRICK WILLIAN DA SILVA',
        'genero': 'M',
        'oab_principal': 'OAB/SC 53969',
        'oabs_por_uf': {
            'SC': 'OAB/SC 53969',
            'AM': 'OAB/AM A2638',
        },
        'jurisdicoes': ['AM'],
        'eh_socio_admin': False,
    },
    'gabriel': {
        'nome': 'Gabriel Cardoso de Aguiar',
        'nome_maiusculo': 'GABRIEL CARDOSO DE AGUIAR',
        'genero': 'M',
        'oab_principal': 'OAB/SC 76040',
        'oabs_por_uf': {
            'SC': 'OAB/SC 76040',
            'BA': 'OAB/BA 88973',
            'ES': 'OAB/ES 43987',
        },
        'jurisdicoes': ['BA', 'SC', 'ES'],
        'eh_socio_admin': False,
    },
    'alexandre': {
        'nome': 'Alexandre Raizel de Meira',
        'nome_maiusculo': 'ALEXANDRE RAIZEL DE MEIRA',
        'genero': 'M',
        'oab_principal': 'OAB/SC 68186',
        'oabs_por_uf': {
            'SC': 'OAB/SC 68186',
            'MG': 'OAB/MG 230436',
            'SE': 'OAB/SE 1901A',
        },
        'jurisdicoes': ['MG', 'AL', 'SE'],
        'eh_socio_admin': False,
    },
}


# Quem PROTOCOLA por UF (regra de negócio fixa do escritório)
PROTOCOLA_POR_UF = {
    'AM': 'patrick',     # SEMPRE Patrick (PJe local)
    'AL': 'tiago',       # transição → 'alexandre'
    'SE': 'alexandre',
    'BA': 'gabriel',
    'SC': 'gabriel',
    'ES': 'gabriel',
    'MG': 'alexandre',
}


# Cidade de assinatura (cidade onde o procurador está localizado)
CIDADE_POR_UF = {
    'AL': 'Arapiraca',
    'AM': 'Maués',
    'BA': 'Salvador',
    'SC': 'Joaçaba',
    'ES': 'Vitória',
    'MG': 'Uberlândia',
    'SE': 'Aracaju',
}


def selecionar_advogado_para_uf(uf: str, override: str = None) -> dict:
    """Retorna dict do advogado que ASSINA peças na UF informada.

    Inclui:
    - dados pessoais (nome, OAB da UF, gênero)
    - versao = 'COM' (sócio admin) ou 'SEM' (demais)
    - cidade da assinatura
    """
    chave = override or PROTOCOLA_POR_UF.get(uf)
    if not chave:
        return None
    p = PROCURADORES.get(chave)
    if not p:
        return None
    return {
        'chave': chave,
        'nome': p['nome'],
        'nome_maiusculo': p['nome_maiusculo'],
        'oab_uf': p['oabs_por_uf'].get(uf, p['oab_principal']),
        'genero': p['genero'],
        'versao': 'COM' if p['eh_socio_admin'] else 'SEM',
        'cidade': CIDADE_POR_UF.get(uf, ''),
        'uf': uf,
    }


def montar_advogado_por_uf() -> dict:
    """Monta o dict ADVOGADO_POR_UF compatível com notificacao-extrajudicial.
    Usado para evitar duplicação de cadastro entre skills."""
    return {uf: selecionar_advogado_para_uf(uf) for uf in PROTOCOLA_POR_UF}


# Pré-computado para importação direta
ADVOGADO_POR_UF = montar_advogado_por_uf()


if __name__ == '__main__':
    import sys, io, json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print('=== ADVOGADO_POR_UF (computado) ===')
    for uf, adv in ADVOGADO_POR_UF.items():
        print(f"  {uf}: {adv['nome']} | {adv['oab_uf']} | {adv['versao']}-escritorio | {adv['cidade']}")
