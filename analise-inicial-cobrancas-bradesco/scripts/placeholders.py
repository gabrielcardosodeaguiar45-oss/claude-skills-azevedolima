# -*- coding: utf-8 -*-
"""
Detecção de placeholders e texto-template não preenchido na inicial.

Padrões alvo (mais frequentes nesses modelos):

1. {{nome_completo}} / {{cidade}} / {{cpf}} etc. - placeholder Jinja-style.
2. Vírgulas seguidas com vazio entre elas (qualificação não preenchida):
   ", , , , inscrita no CPF sob o nº ,"
3. "Cidade/AM" ou "comarca de Cidade/AM" sem cidade real.
4. "valor de R$ ()" ou "R$ , ( )" - números não preenchidos.
5. "data de a " - datas não preenchidas.
6. "nº ()" ou "nº " seguido de espaço - número/contrato vazio.
7. Referências a "CONFIRMAÇÃO MENSAGEM.png" ou outros prints nominais
   indicando contrato cru.

Uso:

    from placeholders import detectar_placeholders

    alertas = detectar_placeholders(paragrafos)
    # -> [{paragrafo, trecho, padrao, severidade, mensagem}, ...]
"""
from __future__ import annotations

import re
from typing import Dict, List


PADROES = [
    {
        "regex": r"\{\{[^\}]+\}\}",
        "nome": "placeholder_jinja",
        "severidade": "ALTA",
        "msg_fmt": "Placeholder não preenchido: {match!r}.",
    },
    {
        "regex": r"(?<!\d),\s*,\s*,",
        "nome": "qualificacao_vazia",
        "severidade": "ALTA",
        "msg_fmt": "Sequência de vírgulas vazias indica qualificação não preenchida.",
    },
    {
        "regex": r"\bComarca\s+de\s+Cidade\b",
        "nome": "cidade_generica",
        "severidade": "ALTA",
        "msg_fmt": "Comarca genérica 'Cidade' não substituída pelo nome real.",
    },
    {
        "regex": r"\bComarca\s+de\s+_+\b",
        "nome": "cidade_placeholder_underline",
        "severidade": "ALTA",
        "msg_fmt": "Comarca com underlines/placeholder visíveis.",
    },
    {
        "regex": r"R\$\s*\(\s*\)",
        "nome": "valor_vazio",
        "severidade": "ALTA",
        "msg_fmt": "Valor monetário com parênteses vazios (extenso não preenchido).",
    },
    {
        "regex": r"R\$\s*,\s*\(",
        "nome": "valor_so_virgula",
        "severidade": "ALTA",
        "msg_fmt": "Valor monetário começa com 'R$ ,' - número faltando.",
    },
    {
        "regex": r"\bdesde\s+a\s+data\s+de\s+a\b",
        "nome": "data_vazia_periodo",
        "severidade": "ALTA",
        "msg_fmt": "Período 'desde a data de [VAZIO] a [VAZIO]' não preenchido.",
    },
    {
        "regex": r"\bn[ºo°]\s*\(\s*\)",
        "nome": "numero_vazio",
        "severidade": "MEDIA",
        "msg_fmt": "Número (contrato/conta/agência) com parênteses vazios.",
    },
    {
        "regex": r"\b__+\b",
        "nome": "underline_placeholder",
        "severidade": "MEDIA",
        "msg_fmt": "Underlines no texto - provável placeholder não preenchido.",
    },
    {
        "regex": r"\[\s*INSERIR\s*[^\]]*\]",
        "nome": "instrucao_modelo",
        "severidade": "ALTA",
        "msg_fmt": "Instrução de modelo '[INSERIR ...]' não removida.",
        "flags": re.IGNORECASE,
    },
    {
        "regex": r"\[\s*PREENCHER\s*[^\]]*\]",
        "nome": "instrucao_modelo",
        "severidade": "ALTA",
        "msg_fmt": "Instrução de modelo '[PREENCHER ...]' não removida.",
        "flags": re.IGNORECASE,
    },
    {
        "regex": r"\bXXX+\b",
        "nome": "xxx_placeholder",
        "severidade": "ALTA",
        "msg_fmt": "Sequência de 'X' indica placeholder não preenchido.",
    },
    {
        "regex": r"\bnome[_\s]?completo\b|\bcpf\b\s*:|\brg\b\s*:|\bcidade\b\s*:",
        "nome": "rotulo_modelo_visivel",
        "severidade": "MEDIA",
        "msg_fmt": "Rótulo de campo de modelo visível no corpo do texto.",
        "flags": re.IGNORECASE,
        "extra_check": True,
    },
]


def detectar_placeholders(paragrafos: List[str]) -> List[Dict]:
    """Roda todos os padrões sobre a lista de parágrafos.

    Args:
        paragrafos: lista de parágrafos da inicial.

    Returns:
        Lista de alertas (dicts).
    """
    alertas: List[Dict] = []
    for i, texto in enumerate(paragrafos, start=1):
        if not texto or not texto.strip():
            continue
        for padrao in PADROES:
            flags = padrao.get("flags", 0)
            regex = re.compile(padrao["regex"], flags)
            for m in regex.finditer(texto):
                inicio = max(0, m.start() - 30)
                fim = min(len(texto), m.end() + 30)
                trecho = texto[inicio:fim].strip()
                msg = padrao["msg_fmt"].format(match=m.group(0))
                # Filtros para reduzir falso-positivo
                if padrao["nome"] == "qualificacao_vazia":
                    # Só sinaliza se estiver em parágrafo de qualificação (autor ou réu)
                    if not re.search(
                        r"\binscrit[ao]\b|\bCPF\b|\bC[ée]dula\b|\bRG\b|\bresidente\b",
                        texto, re.IGNORECASE,
                    ):
                        continue
                if padrao["nome"] == "cidade_generica":
                    # Confirmar que está em endereçamento ou qualificação
                    if "Juízo" not in texto and "Juizado" not in texto and "Comarca" not in texto:
                        continue
                alertas.append({
                    "paragrafo": i,
                    "trecho": trecho,
                    "padrao": padrao["nome"],
                    "severidade": padrao["severidade"],
                    "mensagem": f"§{i}: {msg}",
                })
    return alertas


if __name__ == "__main__":
    teste = [
        "Ao Juízo do Juizado Especial Cível da Comarca de Cidade/AM",
        "MARIA DA SILVA, brasileira, casada, aposentada, inscrita no CPF sob o nº 123.456.789-00",
        ", , , , inscrita no CPF sob o nº , Cédula de Identidade nº , residente",
        "valor de R$ () (vinte mil reais)",
        "{{nome_completo}}, brasileiro, [PREENCHER profissão]",
        "no período de 07/01/2026 a 07/11/2025",  # datas invertidas (outro script)
    ]
    for a in detectar_placeholders(teste):
        print(a)
