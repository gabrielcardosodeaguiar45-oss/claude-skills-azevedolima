"""
Classificador: detecta teses ativas a partir dos arquivos da pasta do cliente.
Mapeia tabelas (7 - TABELA *.pdf) e procurações (2 - PROCURAÇÃO *.pdf) para teses.
"""
import os, re

# Mapa: padrão de nome do arquivo → tese
ARQUIVO_PARA_TESE = [
    (r'7\s*[-–]\s*TABELA\s+CESTA',                       'TARIFAS'),
    (r'7\s*[-–]\s*TABELA\s+CART[ÃA]O\s+CR[ÉE]DITO\s+ANUIDADE', 'TARIFAS'),
    (r'7\s*[-–]\s*TABELA\s+TARIFA',                      'TARIFAS'),
    (r'7\s*[-–]\s*TABELA\s+MORA',                        'MORA'),
    (r'7\s*[-–]\s*TABELA\s+ENCARGO',                     'MORA'),  # encargo conta como mora
    (r'7\s*[-–]\s*TABELA\s+APLIC',                       'APLIC'),
    (r'7\s*[-–]\s*TABELA\s+T[ÍI]TULO\s+DE\s+CAPITALIZA', 'TITULO'),
    (r'7\s*[-–]\s*TABELA\s+PG\s*ELETRON|PAGAMENTO',      'PG_ELETRON'),
    (r'7\s*[-–]\s*TABELA(?!\s+\w)',                      None),  # tabela genérica - depende do conteúdo
]

# Mapa: rubrica do extrato → tese
RUBRICA_PARA_TESE = [
    (r'TARIFA BANCARIA',                                 'TARIFAS'),
    (r'CESTA\s*(B\.)?EXPRESSO',                          'TARIFAS'),
    (r'CARTAO CREDITO ANUIDADE',                         'TARIFAS'),
    (r'(MORA CRED PESS|CRED MORA PESS|MORA CREDITO PESSOAL)', 'MORA'),
    (r'(ENC LIM CRED|ENCARGOS LIMITE DE CRED|ENCARGO)',  'MORA'),
    (r'APLIC\.?\s*INVEST FACIL',                         'APLIC'),
    (r'TITULO DE CAPITALIZACAO',                         'TITULO'),
    (r'PAGTO ELETRON COBRANCA',                          'PG_ELETRON'),
]

# Pastas a IGNORAR (regra crítica)
PASTAS_IGNORAR = {'KIT', '0. KIT', '0_KIT', 'kit', '0. Kit'}


def listar_documentos(pasta_cliente):
    """Lista PDFs/DOCX da pasta principal, EXCLUINDO subpasta KIT/.

    Args:
        pasta_cliente: pasta raiz do cliente

    Returns: list de paths de arquivos (apenas raiz, não recursivo na KIT)
    """
    arquivos = []
    if not os.path.isdir(pasta_cliente):
        return arquivos
    for item in os.listdir(pasta_cliente):
        full = os.path.join(pasta_cliente, item)
        # ignora subpasta KIT
        if os.path.isdir(full):
            continue
        if item.startswith('Thumbs.db') or item.startswith('~$'):
            continue
        if item.lower().endswith(('.pdf', '.docx', '.jpg', '.jpeg', '.png')):
            arquivos.append(full)
    return arquivos


def detectar_teses_ativas(pasta_cliente):
    """Detecta teses ativas pelas tabelas presentes na pasta principal.

    Args:
        pasta_cliente: caminho da pasta do cliente

    Returns: dict {tese: list of arquivos de tabela} — tese pode ser
        TARIFAS, MORA, APLIC, TITULO, PG_ELETRON
    """
    teses = {}
    arquivos = listar_documentos(pasta_cliente)
    for arq in arquivos:
        nome = os.path.basename(arq)
        for padrao, tese in ARQUIVO_PARA_TESE:
            if not tese:
                continue
            if re.search(padrao, nome, re.IGNORECASE):
                teses.setdefault(tese, []).append(arq)
                break
    return teses


def identificar_tese_pela_rubrica(descricao):
    """Dada a descrição de uma rubrica do extrato, identifica qual tese."""
    descricao_upper = descricao.upper()
    for padrao, tese in RUBRICA_PARA_TESE:
        if re.search(padrao, descricao_upper):
            return tese
    return None


def deve_combinar(teses_ativas_dict, comarca, valores_dobros):
    """Decide se deve usar template combinada ou separar.

    Args:
        teses_ativas_dict: {tese: [arquivos]}
        comarca: nome da comarca do autor
        valores_dobros: dict {tese: valor_dobro}

    Returns: bool (True se deve combinar)
    """
    if len(teses_ativas_dict) < 2:
        return False  # 1 só tese não combina

    COMARCAS_QUE_JUNTAM = {'Caapiranga', 'Presidente Figueiredo', 'Manacapuru'}
    LIMITE_VALOR_BAIXO = 400.00

    if comarca in COMARCAS_QUE_JUNTAM:
        return True
    if any(v <= LIMITE_VALOR_BAIXO for v in valores_dobros.values()):
        return True
    if sum(valores_dobros.values()) <= LIMITE_VALOR_BAIXO:
        return True
    return False


def selecionar_template(teses_ativas, eh_pg_eletron=False, comarca=None,
                         valores_dobros=None, mora_tem_so_mora=False,
                         mora_tem_so_encargo=False):
    """Seleciona o template apropriado conforme as teses ativas.

    Args:
        teses_ativas: list de strings com códigos de tese
        eh_pg_eletron: True se é caso de PG ELETRON (sempre 1 inicial por terceiro)
        comarca: nome da comarca
        valores_dobros: dict {tese: dobro}
        mora_tem_so_mora: True se tese MORA tem só 'MORA CRED PESS'
        mora_tem_so_encargo: True se tese MORA tem só 'ENC LIM CRED'

    Returns: str com nome do template OU list[str] se for caso de gerar múltiplas
    """
    if eh_pg_eletron:
        return 'inicial-pg-eletron.docx'

    if len(teses_ativas) == 1:
        tese = teses_ativas[0]
        mapa = {
            'TARIFAS': 'inicial-tarifas.docx',
            'APLIC': 'inicial-aplic-invest.docx',
            'TITULO': 'inicial-combinada.docx',  # template próprio pendente
            'MORA': 'inicial-mora.docx' if (mora_tem_so_mora or mora_tem_so_encargo) else 'inicial-mora-encargo.docx',
        }
        return mapa.get(tese, 'inicial-combinada.docx')

    # 2+ teses
    if valores_dobros and deve_combinar({t: [] for t in teses_ativas}, comarca, valores_dobros):
        return 'inicial-combinada.docx'

    # 2+ teses sem critério para combinar → 1 inicial por tese
    return [selecionar_template([t], False, comarca,
                                  {t: valores_dobros.get(t)} if valores_dobros else None,
                                  mora_tem_so_mora, mora_tem_so_encargo)
            for t in teses_ativas]


# ============================================================
# Normalização de rubricas
# ============================================================
NORMALIZACOES_RUBRICAS = {
    'TARIFA BANCARIA':         'TARIFA BANCÁRIA',
    'TITULO DE CAPITALIZACAO': 'TÍTULO DE CAPITALIZAÇÃO',
    'MORA CREDITO PESSOAL':    'MORA CRÉDITO PESSOAL',
    'ENCARGOS LIMITE DE CRED': 'ENCARGOS LIMITE DE CRÉDITO',
    'CARTAO CREDITO ANUIDADE': 'CARTÃO CRÉDITO ANUIDADE',
    'APLIC INVEST FACIL':      'APLIC.INVEST FÁCIL',
}


def normalizar_rubrica(texto):
    """Aplica acentuação padrão em rubricas extraídas dos extratos."""
    s = re.sub(r'\s+', ' ', texto).strip()
    for k, v in NORMALIZACOES_RUBRICAS.items():
        s = s.replace(k, v)
    return s


# ============================================================
# Rótulos humanizados (para ementa combinada)
# ============================================================
ROTULOS_HUMANIZADOS = {
    'TARIFAS': ['Tarifa Bancária'],
    'MORA':    ['Mora Cred Pess', 'Enc. Lim. Crédito'],
    'APLIC':   ['Aplic.Invest Fácil'],
    'TITULO':  ['Título de Capitalização'],
}


# ============================================================
# Rótulos para o pedido (CAPS)
# ============================================================
ROTULOS_PEDIDO = {
    'TARIFAS': 'TARIFA BANCÁRIA',
    'MORA':    'MORA CRÉDITO PESSOAL / ENCARGOS LIMITE DE CRÉDITO',
    'APLIC':   'APLIC.INVEST FÁCIL',
    'TITULO':  'TÍTULO DE CAPITALIZAÇÃO',
}
