# -*- coding: utf-8 -*-
"""
Detecção de "peça não adaptada" — padrões mecânicos que indicam que a peça
foi montada a partir de modelo genérico sem adaptação ao caso concreto.

Lista curta de padrões de alta precisão, baseada em erros reais observados
em conferências passadas:

    - Plural "os Réus"/"as Rés"/"os Requeridos" em processo com UM réu
    - Pronomes do gênero oposto ao do cliente ("o Recorrente" para mulher)
    - Menções a "INSS"/"autarquia previdenciária" em ação puramente bancária
    - Menções a "empréstimo consignado" em ação puramente de cartão RMC/RCC
    - Menções a "cartão de crédito consignado" em ação puramente de empréstimo
    - "Apelante" usado em réplica (peça de primeiro grau)
    - "Contestação" sendo rebatida em apelação (revela que é modelo de réplica)

Uso:

    from peca_nao_adaptada import analisar

    alertas = analisar(
        texto_peca=texto,
        genero_cliente="F",
        n_reus=1,
        tipo_acao="emprestimo_consignado_nao_contratado",
        tipo_peca="apelacao",
    )
    # -> lista de dicts [{paragrafo, trecho, tipo, severidade, mensagem}, ...]
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional


SEVERIDADES = ("ALTA", "MEDIA", "BAIXA")


# Padrões de plural indevido (quando n_reus == 1)
PADROES_PLURAL = [
    r"\bos\s+R[ée]us\b",
    r"\bas\s+R[ée]s\b",
    r"\bos\s+Requeridos\b",
    r"\bas\s+Requeridas\b",
    r"\bR[ée]us\b",
    r"\bR[ée]s\b",
]

# Padrões de gênero (para cliente mulher)
PADROES_MASC = [
    r"\bo\s+Recorrente\b",
    r"\bo\s+Apelante\b",
    r"\bo\s+Autor\b",
    r"\bo\s+Requerente\b",
    r"\bo\s+Consumidor\b",
    r"\bao\s+Recorrente\b",
    r"\bdo\s+Recorrente\b",
]

PADROES_FEM = [
    r"\ba\s+Recorrente\b",
    r"\ba\s+Apelante\b",
    r"\ba\s+Autora\b",
    r"\ba\s+Requerente\b",
    r"\ba\s+Consumidora\b",
]


TIPO_ACAO_PADROES_SUSPEITOS = {
    "emprestimo_nao_contratado": [
        (r"\bcart[ãa]o\s+de\s+cr[ée]dito\s+consignado\b", "MEDIA",
         "Menção a 'cartão de crédito consignado' em ação de empréstimo — verificar se é apenas rebate da sentença ou deslize de modelo."),
        (r"\bRMC\b|\bRCC\b|\breserva\s+de\s+margem\b", "MEDIA",
         "Menção a 'RMC/RCC' em ação de empréstimo — verificar se é pertinente."),
    ],
    "rmc_rcc": [
        (r"\bempr[ée]stimo\s+consignado\b", "MEDIA",
         "Menção a 'empréstimo consignado' em ação de RMC/RCC — verificar se é pertinente."),
    ],
    "bancario": [
        (r"\bINSS\b", "MEDIA",
         "Menção a 'INSS' em ação bancária pura — verificar se é pertinente (ex.: apenas para descrever origem do benefício) ou se indica modelo previdenciário."),
        (r"\bautarquia\s+previdenci[áa]ria\b", "MEDIA",
         "Menção a 'autarquia previdenciária' em ação bancária — possível modelo previdenciário não adaptado."),
    ],
}


PADROES_PECA_CRUZADA = {
    "apelacao": [
        (r"\ba\s+presente\s+r[ée]plica\b", "ALTA",
         "Palavra 'réplica' em apelação — modelo de réplica não adaptado."),
        (r"\bem\s+impugna[çc][ãa]o\b", "ALTA",
         "Menção a 'impugnação' em apelação — modelo de réplica/impugnação não adaptado."),
    ],
    "replica": [
        (r"\bApelante\b", "ALTA",
         "Termo 'Apelante' em réplica — modelo de apelação não adaptado."),
        (r"\bapela[çc][ãa]o\b", "MEDIA",
         "Menção a 'apelação' em réplica — verificar pertinência."),
    ],
    "contestacao": [
        (r"\bAutora?\b", "BAIXA",
         "Pode indicar referência à parte autora — apenas verificar."),
    ],
}


def _encontrar_no_texto(paragrafos: List[str], padrao: str) -> List[Dict]:
    """Retorna lista de (num_paragrafo, trecho_com_match)."""
    achados = []
    regex = re.compile(padrao, re.IGNORECASE)
    for i, texto in enumerate(paragrafos, start=1):
        for m in regex.finditer(texto):
            inicio = max(0, m.start() - 30)
            fim = min(len(texto), m.end() + 30)
            trecho = texto[inicio:fim].strip()
            achados.append({
                "paragrafo": i,
                "match": m.group(0),
                "trecho": trecho,
            })
    return achados


def analisar(
    paragrafos: List[str],
    genero_cliente: Optional[str] = None,
    n_reus: int = 1,
    tipo_acao: Optional[str] = None,
    tipo_peca: Optional[str] = None,
) -> List[Dict]:
    """Executa todas as verificações de peça não adaptada.

    Args:
        paragrafos: lista de parágrafos da peça (em ordem).
        genero_cliente: 'M', 'F' ou None. Se None, não checa gênero.
        n_reus: número de partes no polo passivo.
        tipo_acao: chave em TIPO_ACAO_PADROES_SUSPEITOS.
        tipo_peca: 'apelacao', 'replica', 'contestacao'.

    Retorna lista de dicts com alertas.
    """
    alertas: List[Dict] = []

    # Plural indevido
    if n_reus == 1:
        for padrao in PADROES_PLURAL:
            for r in _encontrar_no_texto(paragrafos, padrao):
                alertas.append({
                    "paragrafo": r["paragrafo"],
                    "trecho": r["trecho"],
                    "tipo": "plural_indevido",
                    "severidade": "MEDIA",
                    "mensagem": (
                        f"§{r['paragrafo']}: uso de '{r['match']}' "
                        f"com apenas 1 réu — modelo não adaptado."
                    ),
                })

    # Gênero
    if genero_cliente == "F":
        for padrao in PADROES_MASC:
            for r in _encontrar_no_texto(paragrafos, padrao):
                alertas.append({
                    "paragrafo": r["paragrafo"],
                    "trecho": r["trecho"],
                    "tipo": "genero_incorreto",
                    "severidade": "MEDIA",
                    "mensagem": (
                        f"§{r['paragrafo']}: '{r['match']}' (masculino) "
                        f"para cliente mulher."
                    ),
                })
    elif genero_cliente == "M":
        for padrao in PADROES_FEM:
            for r in _encontrar_no_texto(paragrafos, padrao):
                alertas.append({
                    "paragrafo": r["paragrafo"],
                    "trecho": r["trecho"],
                    "tipo": "genero_incorreto",
                    "severidade": "MEDIA",
                    "mensagem": (
                        f"§{r['paragrafo']}: '{r['match']}' (feminino) "
                        f"para cliente homem."
                    ),
                })

    # Tipo de ação
    if tipo_acao and tipo_acao in TIPO_ACAO_PADROES_SUSPEITOS:
        for padrao, sev, msg in TIPO_ACAO_PADROES_SUSPEITOS[tipo_acao]:
            for r in _encontrar_no_texto(paragrafos, padrao):
                alertas.append({
                    "paragrafo": r["paragrafo"],
                    "trecho": r["trecho"],
                    "tipo": "tipo_acao_dissociado",
                    "severidade": sev,
                    "mensagem": f"§{r['paragrafo']}: {msg}",
                })

    # Tipo de peça cruzada
    if tipo_peca and tipo_peca in PADROES_PECA_CRUZADA:
        for padrao, sev, msg in PADROES_PECA_CRUZADA[tipo_peca]:
            for r in _encontrar_no_texto(paragrafos, padrao):
                alertas.append({
                    "paragrafo": r["paragrafo"],
                    "trecho": r["trecho"],
                    "tipo": "peca_cruzada",
                    "severidade": sev,
                    "mensagem": f"§{r['paragrafo']}: {msg}",
                })

    return alertas


if __name__ == "__main__":
    teste = [
        "Condenar os Réus ao pagamento de danos morais.",
        "A parte autora, ora Apelante, foi vítima de fraude.",
        "O Recorrente teve seu benefício descontado.",
        "Trata-se de réplica à contestação apresentada pelo banco.",
    ]
    for a in analisar(teste, genero_cliente="F", n_reus=1,
                      tipo_acao="emprestimo_nao_contratado",
                      tipo_peca="apelacao"):
        print(a)
