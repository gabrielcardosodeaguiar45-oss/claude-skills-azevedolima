"""Perfis de jurisdição da skill `inicial-nao-contratado`.

Cada perfil define TUDO que difere uma UF/foro de outra:
  - polo passivo inclui INSS ou só banco
  - procurador default
  - templates do vault por cenário (1contrato / multiplos / refin)
  - convenção de placeholders (BA / AM)
  - endereço do INSS no polo passivo (Federal)
  - cabeçalho-modelo
  - se decide foro automaticamente por valor da causa (AL → ≤60 SM JEF / >60 SM TJAL)

Para ADICIONAR uma nova UF (ex.: PE Federal):
  1. Cole um perfil similar abaixo (ex.: copie BA_FEDERAL → PE_FEDERAL)
  2. Ajuste UF, comarcas, templates, end_inss, cabecalho
  3. Coloque o template novo em
     `Obsidian Vault/Modelos/IniciaisNaoContratado/_templates/inicial-jfpe-base.docx`
  4. Rode `python validar_template.py inicial-jfpe-base.docx` para checar
  5. Use o pipeline genérico: `gerar_inicial('PE_FEDERAL', ...)`

NÃO precisa criar pipeline novo nem helper novo.
"""
from typing import Dict, List, Optional


PERFIS: Dict[str, Dict] = {
    # ========================================================
    #  BA — Federal (JEF Salvador) — Gabriel
    # ========================================================
    'BA_FEDERAL': {
        'uf': 'BA',
        'foro': 'federal',
        'inclui_inss': True,
        'procurador_chave_default': 'gabriel',
        'comarcas_validas': [
            'Salvador', 'Camaçari', 'Mata de São João', 'Lauro de Freitas',
            'Simões Filho', 'Dias d\'Ávila', 'Vera Cruz', 'Itaparica',
            # Adicionar conforme necessário
        ],
        'templates_por_cenario': {
            '1contrato':   'inicial-jfba-base.docx',
            'multiplos':   'inicial-jfba-multiplos-avn-inativo.docx',
            'refin':       'inicial-jfba-refin-ativo.docx',
        },
        'end_inss_polo_passivo': 'Av. Sete de Setembro, 1078 - Mercês, Salvador/BA',
        'cabecalho_template': 'Ao Juízo da {N}ª Vara Federal — JEF Cível Subseção Judiciária de {comarca}/BA',
        'convencao_placeholders': 'BA',  # {{nome_autor}}, {{cpf_autor}}, ...
        'tipo_template_default': 'auto',  # decide entre base/multiplos/refin pelo HISCON
        'pipeline_modulo': '_pipeline_caso',
        'pipeline_func_montar': 'montar_dados_inicial',
        'pipeline_func_gerar': 'gerar_inicial',
        # Argumentos específicos do BA
        'pipeline_kwargs_extra': {'subsecao': 'Salvador', 'banco_jurisdicao': 'matriz'},
    },

    # ========================================================
    #  AM — Estadual rito comum (TJAM) — Patrick
    # ========================================================
    # REGRA AM (gravada 2026-05-14, Gabriel): no Amazonas o entendimento atual
    # é AJUIZAR UMA AÇÃO POR CONTRATO. Mesmo banco/benefício com 2+ contratos
    # NC → 2+ INICIAIS separadas (não consolidar). A NOTIFICAÇÃO extrajudicial,
    # ao contrário, agrega todos os contratos do banco em uma única notificação.
    # Esse entendimento é específico do AM e pode mudar.
    # Estrutura no kit-juridico: usar subpasta `Contrato XXX/` dentro de
    # `Não contratado/BANCO X/` mesmo quando há 1 banco com 2+ contratos no AM.
    # Procurador (Patrick) e perfil seguem iguais.
    'AM_ESTADUAL': {
        'uf': 'AM',
        'foro': 'estadual',
        'inclui_inss': False,  # Estadual, sem INSS (mesmo se procuração menciona INSS)
        'uma_inicial_por_contrato': True,  # AM-only — vide regra acima
        'procurador_chave_default': 'patrick',  # FIXO — só Patrick protocola PJe AM
        'comarcas_validas': [
            'Maués', 'Manaus', 'Boa Vista do Ramos', 'Caapiranga',
            'Presidente Figueiredo', 'Manacapuru', 'Anamã', 'Codajás',
        ],
        'templates_por_cenario': {
            '1contrato':   'inicial-jeam-base.docx',
            'multiplos':   'inicial-jeam-base.docx',  # AM nunca usa "multiplos"
                                                       # por regra (1 inicial/contrato)
            'refin':       'inicial-jeam-refin.docx',
        },
        'end_inss_polo_passivo': None,  # N/A
        'cabecalho_template': 'Ao Juízo da ___ Vara Cível da Comarca de {comarca}/AM',
        'convencao_placeholders': 'AM',  # {{nome_completo}}, {{cpf}}, {{quali_banco}}
        'tipo_template_default': 'auto',
        'pipeline_modulo': '_pipeline_caso_am',
        'pipeline_func_montar': 'montar_dados_inicial_am',
        'pipeline_func_gerar': 'gerar_inicial_am',
        'pipeline_kwargs_extra': {},
    },

    # ========================================================
    #  AL — Federal (JEF AL ≤ 60 SM) — Tiago (transição → Alexandre)
    # ========================================================
    'AL_FEDERAL': {
        'uf': 'AL',
        'foro': 'federal',
        'inclui_inss': True,
        'procurador_chave_default': 'tiago',
        'comarcas_validas': [
            'Arapiraca', 'Maceió', 'Jaramataia', 'Lagoa da Canoa',
            'Major Izidoro', 'São Sebastião', 'Campo Alegre',
        ],
        'templates_por_cenario': {
            '1banco':      'inicial-jfal-1banco.docx',
            '2bancos':     'inicial-jfal-2bancos.docx',
            # 'refin' usa '1banco' por enquanto
        },
        'end_inss_polo_passivo': 'Av. Sete de Setembro, 1078 - Mercês, Salvador/BA',
        'cabecalho_template': 'Ao Juízo do Juizado Especial Federal Subseção de {comarca}/AL',
        'convencao_placeholders': 'AL',  # via helpers_redacao
        'tipo_template_default': 'auto',
        'pipeline_modulo': '_pipeline_caso_al',
        'pipeline_func_montar': 'montar_dados_inicial_al',
        'pipeline_func_gerar': 'gerar_inicial_al',
        'pipeline_kwargs_extra': {},  # forcar_foro='federal' será injetado
        'forcar_foro': 'federal',
        'limite_jec_60sm': True,  # acima disso vai pra estadual
    },

    # ========================================================
    #  AL — Estadual rito comum (TJAL > 60 SM ou sorteio)
    # ========================================================
    'AL_ESTADUAL': {
        'uf': 'AL',
        'foro': 'estadual',
        'inclui_inss': False,
        'procurador_chave_default': 'tiago',
        'comarcas_validas': [
            'Arapiraca', 'Maceió', 'Jaramataia', 'Lagoa da Canoa',
            'Major Izidoro', 'São Sebastião', 'Campo Alegre',
        ],
        'templates_por_cenario': {
            '1banco':      'inicial-jeal-1banco.docx',
            '2bancos':     'inicial-jeal-2bancos.docx',
        },
        'end_inss_polo_passivo': None,
        'cabecalho_template': 'Ao Juízo da ___ Vara Cível da Comarca de {comarca}/AL',
        'convencao_placeholders': 'AL',
        'tipo_template_default': 'auto',
        'pipeline_modulo': '_pipeline_caso_al',
        'pipeline_func_montar': 'montar_dados_inicial_al',
        'pipeline_func_gerar': 'gerar_inicial_al',
        'pipeline_kwargs_extra': {},
        'forcar_foro': 'estadual',
    },

    # ========================================================
    #  MG — Estadual rito comum (TJMG) — Alexandre Raizel de Meira
    # ========================================================
    'MG_ESTADUAL': {
        'uf': 'MG',
        'foro': 'estadual',
        'inclui_inss': False,
        'procurador_chave_default': 'alexandre',
        'comarcas_validas': [
            'Ipatinga', 'Uberlândia', 'Belo Horizonte', 'Coronel Fabriciano',
            'Timóteo', 'Governador Valadares',
        ],
        'templates_por_cenario': {
            '1banco':  'inicial-jemg-1banco.docx',
            # '2bancos': pendente — criar quando aparecer caso com 2 bancos réus
        },
        'end_inss_polo_passivo': None,
        'cabecalho_template': 'Ao Juízo da ___ Vara Cível da Comarca de {comarca}/MG',
        'convencao_placeholders': 'AL',  # mesmo padrão genérico do AL
        'tipo_template_default': 'auto',
        'pipeline_modulo': '_pipeline_caso_al',  # reaproveita o pipeline AL
        'pipeline_func_montar': 'montar_dados_inicial_al',
        'pipeline_func_gerar': 'gerar_inicial_al',
        'pipeline_kwargs_extra': {},
        'forcar_foro': 'estadual',  # MG = Estadual fixo
    },

    # ========================================================
    #  Adicionar aqui PE_FEDERAL, ES_FEDERAL, SE_FEDERAL, etc.
    # ========================================================
    # 'PE_FEDERAL': {
    #     'uf': 'PE', 'foro': 'federal', 'inclui_inss': True,
    #     'procurador_chave_default': 'novo_procurador_pe',
    #     'comarcas_validas': ['Recife', 'Olinda', ...],
    #     'templates_por_cenario': {'1contrato': 'inicial-jfpe-base.docx', ...},
    #     'end_inss_polo_passivo': 'Av. ... Recife/PE',
    #     'cabecalho_template': 'Ao Juízo do Juizado Especial Federal Subseção de {comarca}/PE',
    #     'convencao_placeholders': 'BA',   # ou 'AM' ou criar 'PE'
    #     'pipeline_modulo': '_pipeline_caso',  # se reaproveitar BA
    #     ...
    # },
}


def get_perfil(chave: str) -> Dict:
    """Retorna o perfil pela chave. Lança KeyError com lista de chaves válidas."""
    if chave not in PERFIS:
        raise KeyError(
            f'Perfil {chave!r} não cadastrado. Perfis disponíveis: '
            f'{sorted(PERFIS.keys())}. Para adicionar uma nova UF, '
            f'consulte GUIA_NOVA_UF.md.'
        )
    return PERFIS[chave]


def listar_perfis() -> List[str]:
    """Lista as chaves de perfis cadastrados."""
    return sorted(PERFIS.keys())


def perfil_por_uf(uf: str, foro: str = None) -> Optional[str]:
    """Resolve a chave do perfil pela UF (e opcionalmente foro).
    Ex.: ('AL', 'federal') → 'AL_FEDERAL'
    """
    foro_norm = (foro or '').upper()
    for chave, p in PERFIS.items():
        if p['uf'].upper() == uf.upper():
            if foro_norm and chave.endswith(f'_{foro_norm}'):
                return chave
            if not foro_norm:
                return chave
    return None


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print('=== PERFIS CADASTRADOS ===')
    for chave in listar_perfis():
        p = PERFIS[chave]
        print(f'\n{chave}:')
        print(f'  UF/foro: {p["uf"]}/{p["foro"]}')
        print(f'  Inclui INSS: {p["inclui_inss"]}')
        print(f'  Procurador default: {p["procurador_chave_default"]}')
        print(f'  Templates: {list(p["templates_por_cenario"].values())}')
        print(f'  Pipeline: {p["pipeline_modulo"]}.{p["pipeline_func_gerar"]}')
