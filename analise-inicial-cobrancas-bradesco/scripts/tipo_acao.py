# -*- coding: utf-8 -*-
"""
Detecção do tipo de ação (1 dos 6 ou combinada) por subpasta + rubrica + IRDR.

Uso:

    from tipo_acao import detectar_tipo

    info = detectar_tipo(pasta_cliente, texto_inicial)
    # -> {
    #   'tipos_detectados': ['MORA_CRED_PESS'],
    #   'fonte_subpasta': 'MORA CRED PESS',
    #   'rubrica_no_texto': 'Mora Cred Pess',
    #   'irdr_no_texto': '0004464-79.2023.8.04.0000',
    #   'irdr_esperado': '0004464-79.2023.8.04.0000',
    #   'tese_pretty': 'IRDR n.º 0004464-79.2023.8.04.0000 (TJ-AM)',
    #   'combinada': False,
    #   'objeto_procuracao_esperado': ['mora credito pessoal', ...],
    #   'tipo_notificacao_esperado': 'AM - Encargos',
    #   'n_reus': 1,
    #   'consistencia': 'OK' | 'ALERTA' | 'INCONSISTENTE'
    # }
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Dict, List, Optional


_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "teses.json")


def _norm(s: str) -> str:
    if not s:
        return ""
    n = unicodedata.normalize("NFKD", s)
    n = "".join(c for c in n if not unicodedata.combining(c))
    return n.upper().strip()


def carregar_teses(caminho: str = _DEFAULT_PATH) -> Dict:
    caminho = os.path.abspath(caminho)
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


# Pistas de subpasta para mapear nome → tipo
SUBPASTA_PISTAS = {
    "MORA_CRED_PESS": ["MORA CRED PESS", "MORA CREDITO PESSOAL", "MORA CRED. PESS"],
    "MORA_ENCARGOS": ["MORA ENCARG", "ENCARGO LIM", "ENC LIM CRED", "MORA + ENCARGO"],
    "TARIFAS": ["TARIFA", "TARIFAS"],
    "TITULO_CAPITALIZACAO": ["TITULO CAP", "TÍTULO CAP", "TITULO DE CAPITALIZACAO", "TITULO DE CAPITALIZAÇÃO"],
    "APLIC_INVEST": ["APLIC INVEST", "INVEST FACIL", "APLICACAO INVEST", "APLICAÇÃO INVEST"],
    "PG_ELETRON": ["PG ELETRON", "PGTO ELETRONICO", "PAGAMENTO ELETRONICO", "PAGAMENTO ELETRÔNICO"],
}


def _tipo_por_subpasta(nome_pasta: str) -> List[str]:
    """Retorna lista de tipos detectados pelo nome da subpasta. Pode ser vazia."""
    if not nome_pasta:
        return []
    n = _norm(nome_pasta)
    detectados = []
    for tipo, pistas in SUBPASTA_PISTAS.items():
        for p in pistas:
            if _norm(p) in n:
                detectados.append(tipo)
                break
    return detectados


def _tipo_por_rubrica(texto_inicial: str, teses: Dict) -> List[str]:
    """Detecta tipos pela rubrica citada no texto da inicial."""
    if not texto_inicial:
        return []
    detectados = []
    for tipo, info in teses["tipos"].items():
        regex = info.get("rubrica_inicial_regex")
        if regex and re.search(regex, texto_inicial, re.IGNORECASE | re.UNICODE):
            detectados.append(tipo)
    return detectados


def _irdr_no_texto(texto_inicial: str) -> Optional[str]:
    """Extrai número de IRDR citado na inicial, se houver."""
    if not texto_inicial:
        return None
    # Padrão: "0000000-00.0000.0.00.0000"
    m = re.search(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b", texto_inicial)
    return m.group(0) if m else None


def _rubrica_extraida(texto_inicial: str, teses: Dict) -> Optional[str]:
    """Tenta identificar qual rubrica foi citada na inicial."""
    for tipo, info in teses["tipos"].items():
        regex = info.get("rubrica_inicial_regex")
        if regex:
            m = re.search(regex, texto_inicial, re.IGNORECASE | re.UNICODE)
            if m:
                return m.group(0)
    return None


def detectar_tipo(
    pasta_subdir_nome: Optional[str],
    texto_inicial: str,
    teses: Optional[Dict] = None,
) -> Dict:
    """Detecta o tipo da ação cruzando subpasta + texto da inicial.

    Args:
        pasta_subdir_nome: nome da subpasta (ex.: "MORA CRED PESS"). Pode ser None.
        texto_inicial: texto completo da inicial.
        teses: dict carregado de teses.json (opcional).

    Returns:
        Dicionário com tipos detectados, consistência, IRDR esperado etc.
    """
    if teses is None:
        teses = carregar_teses()

    tipos_subpasta = _tipo_por_subpasta(pasta_subdir_nome or "")
    tipos_rubrica = _tipo_por_rubrica(texto_inicial, teses)

    # União dos dois conjuntos
    todos = list(dict.fromkeys(tipos_subpasta + tipos_rubrica))

    if not todos:
        return {
            "tipos_detectados": [],
            "fonte_subpasta": pasta_subdir_nome,
            "tipos_subpasta": [],
            "tipos_rubrica": [],
            "rubrica_no_texto": None,
            "irdr_no_texto": _irdr_no_texto(texto_inicial),
            "combinada": False,
            "consistencia": "INCONSISTENTE",
            "mensagem": "Nenhum tipo de ação reconhecido na subpasta nem no texto da inicial.",
        }

    combinada = len(todos) > 1
    irdr_no_texto = _irdr_no_texto(texto_inicial)
    rubrica_extraida = _rubrica_extraida(texto_inicial, teses)

    # IRDR esperado: pega o do primeiro tipo (ou todos quando combinada)
    irdrs_esperados = []
    teses_pretty = []
    objetos_proc = []
    tipos_notificacao = []
    n_reus_max = 1
    for t in todos:
        info = teses["tipos"].get(t, {})
        if info.get("irdr"):
            irdrs_esperados.append(info["irdr"])
        if info.get("irdr_pretty"):
            teses_pretty.append(info["irdr_pretty"])
        objetos_proc.extend(info.get("objeto_procuracao", []))
        if info.get("tipo_notificacao"):
            tipos_notificacao.append(info["tipo_notificacao"])
        n_reus_max = max(n_reus_max, info.get("n_reus", 1))

    # Avaliar consistência
    consistencia = "OK"
    msgs = []
    if tipos_subpasta and tipos_rubrica:
        # Existe interseção?
        comum = set(tipos_subpasta) & set(tipos_rubrica)
        if not comum:
            consistencia = "ALERTA"
            msgs.append(
                f"Subpasta indica {tipos_subpasta} mas rubrica do texto indica {tipos_rubrica}."
            )
    if irdr_no_texto and irdrs_esperados and irdr_no_texto not in irdrs_esperados:
        consistencia = "ALERTA"
        msgs.append(
            f"IRDR no texto ({irdr_no_texto}) não corresponde ao(s) esperado(s) {irdrs_esperados}."
        )

    return {
        "tipos_detectados": todos,
        "fonte_subpasta": pasta_subdir_nome,
        "tipos_subpasta": tipos_subpasta,
        "tipos_rubrica": tipos_rubrica,
        "rubrica_no_texto": rubrica_extraida,
        "irdr_no_texto": irdr_no_texto,
        "irdr_esperado": irdrs_esperados,
        "tese_pretty": teses_pretty,
        "combinada": combinada,
        "objeto_procuracao_esperado": objetos_proc,
        "tipo_notificacao_esperado": tipos_notificacao,
        "n_reus": n_reus_max,
        "consistencia": consistencia,
        "mensagens": msgs,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python tipo_acao.py <texto.txt> [nome_subpasta]")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        texto = f.read()
    sub = sys.argv[2] if len(sys.argv) > 2 else None
    info = detectar_tipo(sub, texto)
    print(json.dumps(info, indent=2, ensure_ascii=False))
