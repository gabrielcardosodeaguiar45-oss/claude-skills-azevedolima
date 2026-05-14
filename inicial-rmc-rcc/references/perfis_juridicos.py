"""Configuracao por UF para a skill `inicial-rmc-rcc`.

Cada perfil de UF define:
  - templates: pasta de templates DOCX (origem)
  - destino: pasta de templates padronizados (apos gerador)
  - procurador: chave do procurador (de escritorios.py do NC) que protocola
  - endereco_escritorio: matriz + unidade de apoio (de escritorios.py)
  - arquivos: lista de (label, origem_basename, destino_basename, is_rcc, is_demais)

Para adicionar uma UF nova (AL/BA/MG), basta replicar a estrutura de AM com
os caminhos dos templates do procurador local.
"""
import sys
import os

# Reaproveita escritorios.py do NC (nao duplica)
_NC_REFS = r"C:/Users/gabri/.claude/skills/inicial-nao-contratado/references"
if _NC_REFS not in sys.path:
    sys.path.insert(0, _NC_REFS)
try:
    from escritorios import montar_endereco_escritorio_completo, selecionar_procurador
except ImportError:
    # Fallback minimo (se NC nao disponivel)
    def montar_endereco_escritorio_completo(uf):
        return f"[ENDERECO ESCRITORIO {uf}]"
    def selecionar_procurador(uf, override_chave=None):
        return None


# ============================================================
#   CAMINHOS BASE
# ============================================================

ORIG_BASE = r"C:/Users/gabri/OneDrive/Área de Trabalho/APP - RMC-RCC"
DEST_BASE = r"C:/Users/gabri/OneDrive/Área de Trabalho/APP - RMC-RCC/Templates Padronizados"


# ============================================================
#   PERFIS POR UF
# ============================================================

PERFIS = {
    # ----------------------------------------------------------------
    #   AM — Patrick Willian da Silva (sempre, regra fixa PJe TJAM)
    # ----------------------------------------------------------------
    "AM": {
        "uf": "AM",
        "procurador_chave": "patrick",
        "comarca_default": "Maués",
        "endereco_escritorio": montar_endereco_escritorio_completo("AM"),
        "arquivos": [
            {
                "label": "RMC-BMG",
                "origem": f"{ORIG_BASE}/Tese RMC/1. Petição Inicial- RMC- AM Dr. Patrick - BMG.docx",
                "destino": f"{DEST_BASE}/AM/1. Inicial RMC - AM Dr. Patrick - BMG.docx",
                "is_rcc": False,
                "is_demais": False,
            },
            {
                "label": "RMC-Demais",
                "origem": f"{ORIG_BASE}/Tese RMC/1. Petição Inicial- RMC- AM Dr. Patrick - Demais bancos.docx",
                "destino": f"{DEST_BASE}/AM/1. Inicial RMC - AM Dr. Patrick - Demais bancos.docx",
                "is_rcc": False,
                "is_demais": True,
            },
            {
                "label": "RCC-BMG",
                "origem": f"{ORIG_BASE}/Tese RCC/1. Petição Inicial- RCC- AM Dr. Patrick - BMG.docx",
                "destino": f"{DEST_BASE}/AM/1. Inicial RCC - AM Dr. Patrick - BMG.docx",
                "is_rcc": True,
                "is_demais": False,
            },
            {
                "label": "RCC-Demais",
                "origem": f"{ORIG_BASE}/Tese RCC/1. Petição Inicial- RCC- AM Dr. Patrick - Demais bancos.docx",
                "destino": f"{DEST_BASE}/AM/1. Inicial RCC - AM Dr. Patrick - Demais bancos.docx",
                "is_rcc": True,
                "is_demais": True,
            },
        ],
    },

    # ----------------------------------------------------------------
    #   AL — Tiago de Azevedo Lima (transicao -> Alexandre)
    #   (PENDENTE — adicionar quando os templates AL chegarem)
    # ----------------------------------------------------------------
    "AL": {
        "uf": "AL",
        "procurador_chave": "tiago",
        "comarca_default": "Arapiraca",
        "endereco_escritorio": montar_endereco_escritorio_completo("AL"),
        "arquivos": [
            {
                "label": "RMC-AL",
                "origem": f"{ORIG_BASE}/Tese RMC/1. Petição Inicial -RMC-AL Dr. Tiago - Ajustado Gabriel.docx",
                "destino": f"{DEST_BASE}/AL/1. Inicial RMC - AL Dr. Tiago.docx",
                "is_rcc": False,
                "is_demais": False,
            },
            {
                "label": "RCC-AL",
                "origem": f"{ORIG_BASE}/Tese RCC/1. Petição Inicial -RCC-AL Dr. Tiago  - Ajustado Gabriel.docx",
                "destino": f"{DEST_BASE}/AL/1. Inicial RCC - AL Dr. Tiago.docx",
                "is_rcc": True,
                "is_demais": False,
            },
        ],
    },

    # ----------------------------------------------------------------
    #   BA — Gabriel Cardoso de Aguiar / Dr. Edu (revisar)
    # ----------------------------------------------------------------
    "BA": {
        "uf": "BA",
        "procurador_chave": "gabriel",
        "comarca_default": "Salvador",
        "endereco_escritorio": montar_endereco_escritorio_completo("BA"),
        "arquivos": [
            {
                "label": "RMC-BA",
                "origem": f"{ORIG_BASE}/Tese RMC/1. Petição Inicial- RMC- BA Dr  Edu.docx",
                "destino": f"{DEST_BASE}/BA/1. Inicial RMC - BA Dr. Edu.docx",
                "is_rcc": False,
                "is_demais": False,
            },
            {
                "label": "RCC-BA",
                "origem": f"{ORIG_BASE}/Tese RCC/1. Petição Inicial- RCC BA Dr. Edu.docx",
                "destino": f"{DEST_BASE}/BA/1. Inicial RCC - BA Dr. Edu.docx",
                "is_rcc": True,
                "is_demais": False,
            },
        ],
    },

    # ----------------------------------------------------------------
    #   MG — Alexandre Raizel de Meira (Dr. Xande)
    # ----------------------------------------------------------------
    "MG": {
        "uf": "MG",
        "procurador_chave": "alexandre",
        "comarca_default": "Uberlândia",
        "endereco_escritorio": montar_endereco_escritorio_completo("MG"),
        "arquivos": [
            {
                "label": "RMC-MG",
                "origem": f"{ORIG_BASE}/Tese RMC/1. Petição Inicial- RMC- MG Dr. Xande.docx",
                "destino": f"{DEST_BASE}/MG/1. Inicial RMC - MG Dr. Alexandre.docx",
                "is_rcc": False,
                "is_demais": False,
            },
            {
                "label": "RCC-MG",
                "origem": f"{ORIG_BASE}/Tese RCC/1. Petição Inicial- RCC-MG Dr. Xande.docx",
                "destino": f"{DEST_BASE}/MG/1. Inicial RCC - MG Dr. Alexandre.docx",
                "is_rcc": True,
                "is_demais": False,
            },
        ],
    },
}


def perfil(uf):
    """Retorna o perfil da UF."""
    return PERFIS.get(uf.upper())


def listar_ufs_ativas():
    """Retorna as UFs com templates de origem que EXISTEM em disco."""
    ativas = []
    for uf, p in PERFIS.items():
        for arq in p["arquivos"]:
            if os.path.exists(arq["origem"]):
                ativas.append(uf)
                break
    return ativas
