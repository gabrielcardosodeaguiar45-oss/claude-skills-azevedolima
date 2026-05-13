"""Procuradores e dados do escritório por jurisdição.

Escritório: De Azevedo Lima & Rebonatto

QUEM PROTOCOLA POR UF (atualizado 07/05/2026 — Gabriel):

| UF | Procurador atual | Próximo (transição) | Comarcas conhecidas |
|---|---|---|---|
| AM | Patrick Willian da Silva (OAB/AM A2638) | — | Maués, Manaus, Boa Vista do Ramos, Caapiranga, Presidente Figueiredo, Manacapuru, Anamã, Codajás |
| AL | Tiago de Azevedo Lima (OAB/AL 20906A)   | Alexandre (em transição) | Arapiraca |
| SE | Tiago de Azevedo Lima (OAB/SE — pendente) | Alexandre (em transição) | (pendente) |
| MG | Alexandre (pendente)                    | — | Uberlândia |
| BA | Gabriel Cardoso de Aguiar (OAB/BA 88973) | — | Salvador |
| SC | Gabriel Cardoso de Aguiar (OAB/SC 76040) | — | Joaçaba, Concórdia |
| ES | Gabriel Cardoso de Aguiar (OAB/ES — pendente) | — | (pendente) |

ENDEREÇOS DOS ESCRITÓRIOS (oficial, conforme imagem 07/05/2026 — CEPs pendentes):
- Joaçaba/SC:    Rua Frei Rogério, 541, Centro
- Concórdia/SC:  Rua Getúlio Vargas, 400, Ed. Palladium Offices, Sala 404, Centro
- Salvador/BA:   Rua Portugal, 5, Ed. Status, Comércio
- Arapiraca/AL:  Rua Nossa Senhora da Salete, 597, Sala 04, Itapuã
- Uberlândia/MG: Av. Floriano Peixoto, 615, Ed. Floriano Center, Loja 07, Térreo, Centro
- Maués/AM:      Travessa Michiles, S/N, Centro
- Caapiranga/AM: Rua Antônio Moraes Filho, S/N, Santa Luzia

Para descobrir OABs faltantes: https://cna.oab.org.br/

REGRAS OPERACIONAIS:

1. AM: mesmo quando a notificação extrajudicial é assinada por Eduardo,
   Gabriel ou Tiago (que constam todos na procuração do cliente), a INICIAL
   AM é sempre protocolada pelo Dr. Patrick — porque o sistema PJe/Projudi
   do TJAM é acessado por ele localmente. Os outros procuradores ficam apenas
   no instrumento de procuração. Para casos AM, sempre `procurador_chave='patrick'`.

2. AL/SE: a transição entre Tiago e Alexandre é manual. Por enquanto,
   `procurador_chave='tiago'` por padrão; passar `'alexandre'` quando
   Alexandre assumir.

3. AL Federal vs Estadual: o foro depende do valor da causa.
   - JEF AL (Federal) — até 60 SM (R$ 91.080,00 em 2026 com SM = R$ 1.518)
   - TJAL Juízo Comum (Estadual) — acima de 60 SM, ou por sorteio/escolha
     estratégica.

Pendências de cadastro:
- Tiago: OAB/SE (número)
- Alexandre: nome completo + OAB/AL + OAB/SE + OAB/MG
- Gabriel: OAB/ES (se houver) + endereço escritório ES
- Endereços do escritório em Arapiraca/AL e Uberlândia/MG (extrair dos
  modelos quando chegarem na pasta).
"""

# Catálogo único de endereços do escritório por cidade.
# CEPs pesquisados via ViaCEP em 07/05/2026:
#   - Joaçaba/SC, Maués/AM, Caapiranga/AM: cidades de CEP único (genérico)
#   - Concórdia/SC, Arapiraca/AL, Uberlândia/MG: CEP por faixa de número
#   - Salvador/BA: Edifício Status tem CEP corporativo 40015-903 (40015-000
#     é a faixa par; o nº 5 é ímpar — confirmar com o procurador)
ENDERECOS_FILIAIS = {
    'Joaçaba/SC':    {'logradouro': 'Rua Frei Rogério, 541',                                          'bairro': 'Centro',     'cep': '89600-000'},
    'Concórdia/SC':  {'logradouro': 'Rua Getúlio Vargas, 400, Ed. Palladium Offices, Sala 404',       'bairro': 'Centro',     'cep': '89700-017'},
    'Salvador/BA':   {'logradouro': 'Rua Portugal, 5, Ed. Status',                                    'bairro': 'Comércio',   'cep': '40015-903'},
    'Arapiraca/AL':  {'logradouro': 'Rua Nossa Senhora da Salete, 597, Sala 04',                      'bairro': 'Itapuã',     'cep': '57314-175'},
    'Uberlândia/MG': {'logradouro': 'Av. Floriano Peixoto, 615, Ed. Floriano Center, Loja 07, Térreo','bairro': 'Centro',     'cep': '38400-102'},
    'Maués/AM':      {'logradouro': 'Travessa Michiles, S/N',                                         'bairro': 'Centro',     'cep': '69190-000'},
    'Caapiranga/AM': {'logradouro': 'Rua Antônio Moraes Filho, S/N',                                  'bairro': 'Santa Luzia','cep': '69425-000'},
}


def _e(cidade: str) -> str:
    """Helper: monta string completa do endereço da filial."""
    d = ENDERECOS_FILIAIS[cidade]
    cep_str = f', CEP {d["cep"]}' if d['cep'] else ' (CEP pendente)'
    return f'{d["logradouro"]}, {d["bairro"]}, {cidade}{cep_str}'


# Filial principal (matriz do escritório) — sempre Joaçaba/SC
FILIAL_MATRIZ = 'Joaçaba/SC'

# Filial de apoio por UF (regra: SEMPRE matriz SC PRIMEIRO + unidade de apoio
# na UF do cliente). Para SC, não tem unidade de apoio (a matriz é SC).
FILIAL_APOIO_POR_UF = {
    'BA': 'Salvador/BA',
    'AM': 'Maués/AM',
    'AL': 'Arapiraca/AL',
    'SE': 'Arapiraca/AL',  # default temporário até abrir filial em SE
    'MG': 'Uberlândia/MG',
    'ES': 'Salvador/BA',   # default temporário até abrir filial em ES
    'SC': None,            # já é a matriz
}


def montar_endereco_escritorio_completo(uf: str) -> str:
    """Retorna a string composta de endereço para a qualificação:
        "Rua Frei Rogério, 541, Centro, Joaçaba/SC, CEP 89600-000, e
         unidade de apoio em [endereço da filial da UF]"

    Para SC: retorna apenas a matriz (não tem unidade de apoio).
    Regra fixa do escritório (07/05/2026, Gabriel): MATRIZ SC SEMPRE
    PRIMEIRO + unidade de apoio na UF do cliente.
    """
    matriz = _e(FILIAL_MATRIZ)
    cidade_apoio = FILIAL_APOIO_POR_UF.get((uf or '').upper())
    if cidade_apoio is None or cidade_apoio == FILIAL_MATRIZ:
        return matriz
    apoio = _e(cidade_apoio)
    return f'{matriz}, e unidade de apoio em {apoio}'


PROCURADORES = {
    'gabriel': {
        'nome': 'Gabriel Cardoso de Aguiar',
        'oab': 'OAB/SC 76040',  # principal (advogado pleno em SC)
        'oabs_por_uf': {
            'SC': 'OAB/SC 76040',   # principal (ADVOGADO)
            'BA': 'OAB/BA 88973',   # SUPLEMENTAR
            'ES': 'OAB/ES 43987',   # SUPLEMENTAR
        },
        'jurisdicoes': ['BA', 'SC', 'ES'],
        'tribunais': ['JEF Salvador/BA', 'TRF1', 'JEF/TJSC', 'JEF/TJES'],
        'enderecos_escritorio': [_e('Joaçaba/SC'), _e('Concórdia/SC'), _e('Salvador/BA')],
        # Endereço default por UF para usar no rodapé/qualificação
        'endereco_por_uf': {
            'BA': _e('Salvador/BA'),
            'SC': _e('Joaçaba/SC'),   # ou Concórdia conforme o caso
            'ES': _e('Salvador/BA'),  # default temporário até definir filial ES
        },
    },
    'patrick': {
        'nome': 'Patrick Willian da Silva',
        'oab': 'OAB/SC 53969',  # principal (ADVOGADO em SC)
        'oabs_por_uf': {
            'SC': 'OAB/SC 53969',   # principal (ADVOGADO)
            'AM': 'OAB/AM A2638',   # SUPLEMENTAR — usado nas iniciais AM
        },
        'jurisdicoes': ['AM'],  # protocola apenas em AM
        'tribunais': ['TJAM (Justiça Estadual rito comum)',
                      'Comarcas: Maués, Manaus, Boa Vista do Ramos, Caapiranga, '
                      'Presidente Figueiredo, Manacapuru, Anamã, Codajás'],
        'enderecos_escritorio': [_e('Maués/AM'), _e('Caapiranga/AM'), _e('Joaçaba/SC')],
        'endereco_por_uf': {'AM': _e('Maués/AM')},  # default Maués
    },
    'eduardo': {
        'nome': 'Eduardo Fernando Rebonatto',
        'oab': 'OAB/SC 36592',  # principal (ADVOGADO em SC)
        'oabs_por_uf': {
            'SC': 'OAB/SC 36592',   # principal (ADVOGADO)
            'AM': 'OAB/AM A2118',   # SUPLEMENTAR
            'BA': 'OAB/BA 77088',   # SUPLEMENTAR
            'PR': 'OAB/PR 132523',  # SUPLEMENTAR
        },
        'jurisdicoes': ['AM'],  # consta na procuração mas Patrick que protocola
        'tribunais': ['TJAM (Justiça Estadual rito comum)'],
        'enderecos_escritorio': [_e('Maués/AM'), _e('Joaçaba/SC')],
        'endereco_por_uf': {'AM': _e('Maués/AM')},
    },
    'tiago': {
        'nome': 'Tiago de Azevedo Lima',
        'oab': 'OAB/SC 36672',  # principal (ADVOGADO em SC)
        'oabs_por_uf': {
            'SC': 'OAB/SC 36672',     # principal (ADVOGADO)
            'AL': 'OAB/AL 20906A',    # SUPLEMENTAR — Arapiraca
            'BA': 'OAB/BA 80006',     # SUPLEMENTAR
            'MG': 'OAB/MG 228433',    # SUPLEMENTAR
            'RS': 'OAB/RS 139330A',   # SUPLEMENTAR
            'SE': 'OAB/SE 1850A',     # SUPLEMENTAR
        },
        'jurisdicoes': ['AL', 'SE'],
        'tribunais': ['JEF AL (até 60 SM)', 'TJAL Juízo Comum (>60 SM ou sorteio)',
                      'JEF SE', 'TJSE'],
        'enderecos_escritorio': [_e('Arapiraca/AL'), _e('Joaçaba/SC')],
        'endereco_por_uf': {
            'AL': _e('Arapiraca/AL'),
            'SE': _e('Arapiraca/AL'),  # default temporário até confirmar filial em SE
        },
    },
    'alexandre': {
        # ALEXANDRE RAIZEL DE MEIRA — confirmado pelo Gabriel em 07/05/2026.
        # Em transição com Tiago (AL/SE); procurador único em MG (Uberlândia).
        # OAB/AL e OAB/SE: ainda não emitidas (ele "vai começar" lá).
        'nome': 'Alexandre Raizel de Meira',
        'oab': 'OAB/SC 68186',  # principal (ADVOGADO em SC)
        'oabs_por_uf': {
            'SC': 'OAB/SC 68186',     # principal (ADVOGADO)
            'MG': 'OAB/MG 230436',    # SUPLEMENTAR
            # 'AL': pendente (vai tirar)
            # 'SE': pendente (vai tirar)
        },
        'jurisdicoes': ['AL', 'SE', 'MG'],
        'tribunais': ['JEF AL', 'TJAL', 'JEF SE', 'TJSE', 'JEF MG', 'TJMG'],
        'enderecos_escritorio': [_e('Arapiraca/AL'), _e('Uberlândia/MG'), _e('Joaçaba/SC')],
        'endereco_por_uf': {
            'AL': _e('Arapiraca/AL'),
            'SE': _e('Arapiraca/AL'),
            'MG': _e('Uberlândia/MG'),
        },
        'status': 'em transição (vai assumir AL/SE; MG é exclusivo); pendente OAB/AL e OAB/SE',
    },
}


# Mapa fixo de quem protocola por UF (a regra de negócio do escritório)
PROTOCOLA_POR_UF = {
    'AM': 'patrick',     # SEMPRE Patrick (regra fixa do PJe local)
    'AL': 'tiago',       # transição → 'alexandre' (override manual)
    'SE': 'tiago',       # transição → 'alexandre' (override manual)
    'BA': 'gabriel',
    'SC': 'gabriel',
    'ES': 'gabriel',
    'MG': 'alexandre',   # quando Alexandre estiver cadastrado
}


def detectar_procurador_por_oab(oab: str) -> dict:
    """Encontra o procurador pela OAB (formato 'OAB/AM A2638' ou 'OAB/AL 20906A').
    Procura tanto na OAB principal quanto em `oabs_por_uf`.
    """
    oab_norm = oab.replace(' ', '').upper()
    for chave, dados in PROCURADORES.items():
        if dados['oab'].replace(' ', '').upper() == oab_norm:
            return dict(dados, chave=chave)
        for o in dados.get('oabs_por_uf', {}).values():
            if o and o.replace(' ', '').upper() == oab_norm:
                return dict(dados, chave=chave)
    return None


def selecionar_procurador(uf: str, override_chave: str = None) -> dict:
    """Retorna o procurador que deve PROTOCOLAR a inicial na UF informada.

    Args:
        uf: 'BA' / 'AM' / 'AL' / 'SE' / 'SC' / 'ES' / 'MG'
        override_chave: se passado, força o procurador (ex.: 'alexandre' para
                        casos onde já transicionou em AL).

    Returns:
        dict do procurador (com 'chave', 'oab' apropriada para a UF) ou None.
    """
    chave = override_chave or PROTOCOLA_POR_UF.get(uf)
    if not chave:
        return None
    dados = PROCURADORES.get(chave)
    if not dados:
        return None
    out = dict(dados, chave=chave)
    # Se houver OAB específica da UF, expor como `oab_uf`
    out['oab_uf'] = dados.get('oabs_por_uf', {}).get(uf, dados['oab'])
    # Endereço default do escritório para essa UF (vai pro rodapé/qualificação)
    out['endereco_uf'] = dados.get('endereco_por_uf', {}).get(uf)
    return out


def selecionar_template_por_uf(uf: str, cenario: str, foro: str = 'auto',
                                 n_bancos: int = 1) -> str:
    """Seleciona o nome do template baseado em UF + cenário (+ foro para AL +
    quantidade de bancos réus para AL).

    Args:
        uf: 'BA' / 'AM' / 'AL' (próximos: 'SE', 'MG', 'SC', 'ES')
        cenario: '1contrato' / 'multiplos' / 'refin'
        foro: 'auto' / 'federal' / 'estadual' (AL — JEF até 60 SM, TJAL >60 SM ou sorteio)
        n_bancos: número de instituições financeiras réus (AL — 1 ou 2; >=3
                  cai no template '2bancos' com alerta de adaptação manual)

    Returns:
        nome do arquivo .docx
    """
    if uf == 'BA':
        return {
            '1contrato': 'inicial-jfba-base.docx',
            'multiplos': 'inicial-jfba-multiplos-avn-inativo.docx',
            'refin':     'inicial-jfba-refin-ativo.docx',
        }.get(cenario, 'inicial-jfba-base.docx')

    if uf == 'AM':
        return {
            '1contrato': 'inicial-jeam-base.docx',
            'multiplos': 'inicial-jeam-base.docx',  # AM ainda não tem MULT
            'refin':     'inicial-jeam-refin.docx',
        }.get(cenario, 'inicial-jeam-base.docx')

    if uf == 'AL':
        # AL tem 4 templates: Federal × Estadual × 1banco × 2bancos.
        # A divisão NÃO é por número de contratos — é por número de BANCOS RÉUS:
        #   - 5 contratos do BANCO PAN → '1banco' (replicar bloco fático N vezes)
        #   - 2 PAN + 1 C6                → '2bancos'
        #   - 3+ bancos                   → '2bancos' + alerta de adaptação manual
        # O foro decide entre JFAL (Federal — com INSS) e JEAL (Estadual — sem INSS).
        if foro not in ('federal', 'estadual'):
            raise ValueError(
                'AL: o foro deve ser informado explicitamente ("federal" ou "estadual"). '
                'Para resolver pelo valor da causa, use decidir_foro_al(valor_causa).'
            )
        sufixo = '2bancos' if n_bancos >= 2 else '1banco'
        if foro == 'federal':
            return f'inicial-jfal-{sufixo}.docx'
        return f'inicial-jeal-{sufixo}.docx'

    if uf == 'MG':
        # MG — Estadual rito comum (TJMG) — Alexandre.
        # Atualmente só temos o template `inicial-jemg-1banco.docx` (1 banco
        # réu, sem INSS). Para 2+ bancos, vamos precisar criar `inicial-jemg-2bancos.docx`.
        sufixo = '2bancos' if n_bancos >= 2 else '1banco'
        return f'inicial-jemg-{sufixo}.docx'

    raise ValueError(f'UF não suportada (ainda): {uf}')


# Salário mínimo nacional vigente (atualizar anualmente)
SALARIO_MINIMO_2026 = 1518.00
TETO_JEF_60SM_2026 = 60 * SALARIO_MINIMO_2026  # R$ 91.080,00


# Cidades AL com regra fixa: SEMPRE Federal (independente do valor da causa,
# por renúncia ao excedente — decisão operacional do escritório, gravada 13/05/2026).
# A cidade do AUTOR é usada para essa decisão; não a cidade do banco-réu.
CIDADES_AL_SEMPRE_FEDERAL = {
    'vicosa',          # Viçosa/AL
    'sao sebastiao',   # São Sebastião/AL
    'traipu',          # Traipu/AL
}


def cidade_forca_foro_federal(cidade: str) -> bool:
    """Retorna True se a cidade do autor está na lista de cidades AL que
    SEMPRE ajuízam no JEF Federal (independente do valor da causa, com
    renúncia ao excedente quando ultrapassar 60 SM)."""
    import unicodedata
    if not cidade:
        return False
    norm = unicodedata.normalize('NFD', str(cidade).strip().lower())
    norm = ''.join(c for c in norm if unicodedata.category(c) != 'Mn')
    return norm in CIDADES_AL_SEMPRE_FEDERAL


def decidir_foro_al(valor_causa: float, forcar: str = None,
                       cidade_autor: str = None) -> dict:
    """Decide o foro AL (federal ou estadual).

    Hierarquia (precedência):
    1. `forcar` (override manual) — sempre vence
    2. `cidade_autor` em CIDADES_AL_SEMPRE_FEDERAL (Viçosa/São Sebastião/
       Traipu) — JEF Federal com renúncia ao excedente se > 60 SM
    3. Valor da causa ≤ 60 SM → Federal; > 60 SM → Estadual

    Args:
        valor_causa: float em reais
        forcar: 'federal' / 'estadual' / None — override manual (sorteio ou
                escolha estratégica)
        cidade_autor: cidade da parte autora — usada para regra de cidade
                fixa (Viçosa/São Sebastião/Traipu sempre Federal)

    Returns:
        {
            'foro': 'federal' / 'estadual',
            'motivo': str explicando a decisão,
            'teto_jef': float,
            'renuncia_ao_excedente': bool — True se foro Federal foi imposto
                por cidade fixa mas o valor excede 60 SM (cliente renuncia
                ao excedente)
        }
    """
    if forcar in ('federal', 'estadual'):
        return {
            'foro': forcar,
            'motivo': f'override manual (forcar={forcar!r}) — sorteio ou escolha estratégica',
            'teto_jef': TETO_JEF_60SM_2026,
            'renuncia_ao_excedente': False,
        }
    # Regra de cidade fixa (precede o teto de valor)
    if cidade_autor and cidade_forca_foro_federal(cidade_autor):
        excede_teto = valor_causa > TETO_JEF_60SM_2026
        motivo = (
            f'cidade do autor ({cidade_autor!r}) está na lista AL com regra '
            f'fixa de JEF Federal'
            + (f' — valor R$ {valor_causa:,.2f} excede 60 SM, RENÚNCIA AO '
               f'EXCEDENTE'
               if excede_teto else '')
        )
        return {
            'foro': 'federal',
            'motivo': motivo,
            'teto_jef': TETO_JEF_60SM_2026,
            'renuncia_ao_excedente': excede_teto,
        }
    if valor_causa <= TETO_JEF_60SM_2026:
        return {
            'foro': 'federal',
            'motivo': f'valor da causa R$ {valor_causa:,.2f} ≤ 60 SM (R$ {TETO_JEF_60SM_2026:,.2f}) — JEF AL',
            'teto_jef': TETO_JEF_60SM_2026,
            'renuncia_ao_excedente': False,
        }
    return {
        'foro': 'estadual',
        'motivo': f'valor da causa R$ {valor_causa:,.2f} > 60 SM (R$ {TETO_JEF_60SM_2026:,.2f}) — TJAL Juízo Comum',
        'teto_jef': TETO_JEF_60SM_2026,
        'renuncia_ao_excedente': False,
    }


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print('=== PROCURADORES ===')
    for k, v in PROCURADORES.items():
        print(f'\n{k}: {v["nome"]} ({v["oab"]})')
        print(f'  Jurisdições: {v["jurisdicoes"]}')
        print(f'  OABs por UF: {v.get("oabs_por_uf", {})}')

    print('\n=== PROTOCOLA POR UF ===')
    for uf, chave in PROTOCOLA_POR_UF.items():
        print(f'  {uf}: {chave}')

    print('\n=== SELEÇÃO DE PROCURADOR + ENDEREÇO ===')
    for uf in ['BA', 'AM', 'AL', 'SE', 'SC', 'ES', 'MG']:
        p = selecionar_procurador(uf)
        if p:
            print(f'  {uf}: {p["chave"]} = {p["nome"]} ({p["oab_uf"]})')
            print(f'        endereço: {p.get("endereco_uf")}')
        else:
            print(f'  {uf}: (não cadastrado)')

    print('\n=== TEMPLATES ===')
    for uf, cen in [('BA', '1contrato'), ('BA', 'multiplos'), ('BA', 'refin'),
                     ('AM', '1contrato'), ('AM', 'refin')]:
        print(f'  {uf} + {cen}: {selecionar_template_por_uf(uf, cen)}')
    for foro in ['federal', 'estadual']:
        for nb in [1, 2, 3]:
            print(f'  AL ({foro}, {nb} banco(s)): {selecionar_template_por_uf("AL", "1contrato", foro=foro, n_bancos=nb)}')

    print('\n=== DECIDIR FORO AL ===')
    for vc in [10000.00, 50000.00, 91000.00, 91080.00, 91100.00, 200000.00]:
        d = decidir_foro_al(vc)
        print(f'  R$ {vc:>12,.2f} → {d["foro"]:8} | {d["motivo"]}')
    d = decidir_foro_al(50000.00, forcar='estadual')
    print(f'  R$  50.000,00 (forçado) → {d["foro"]:8} | {d["motivo"]}')
