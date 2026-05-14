# -*- coding: utf-8 -*-
"""
Cruzamento automático entre CCB (Cédula de Crédito Bancário), TED e petição
inicial — acusa divergência entre Valor Liberado e valor efetivamente
transferido à conta do consumidor.

Lê texto extraído de PDFs de processo (via pymupdf ou pdfplumber) e
identifica os campos relevantes por regex. Trabalha com padrões
padronizados dos principais bancos consignados (C6, Bradesco, Pan,
Daycoval, Itaú, BMG, Safra, Parati).

Uso:

    from ccb_ted_diff import extrair_valores_ccb, extrair_valor_ted, acusar_diferenca

    ccb_data = extrair_valores_ccb(texto_ccb)
    ted_valor = extrair_valor_ted(texto_ted)
    alerta = acusar_diferenca(ccb_data, ted_valor, valor_inicial)
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional


# --------------------------------------------------------------------- #
# Conversão de valores em pt-BR
# --------------------------------------------------------------------- #
def parse_br(valor_str: str) -> Optional[Decimal]:
    """Converte '1.428,03' → Decimal('1428.03')."""
    if valor_str is None:
        return None
    s = valor_str.strip().replace("R$", "").replace("\u00a0", "").strip()
    # Remove separador de milhar e troca vírgula por ponto
    s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def fmt_br(valor: Decimal) -> str:
    """Formata Decimal(1428.03) → 'R$ 1.428,03'."""
    if valor is None:
        return "—"
    s = f"{valor:,.2f}"
    # Troca vírgulas por pontos e vice-versa (pt-BR)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


# --------------------------------------------------------------------- #
# Extração
# --------------------------------------------------------------------- #
RE_VALOR = r"R?\$?\s*([\d\.]+,\d{2})"

PADROES_CCB = {
    "valor_liberado": [
        r"Valor\s+Liberado\s*\n?\s*" + RE_VALOR,
        r"Valor\s+Liberado[:\s]+" + RE_VALOR,
    ],
    "valor_total_financiado": [
        r"Valor\s+Total\s+Financiado\s*\n?\s*" + RE_VALOR,
        r"Valor\s+Total\s+Financiado[:\s]+" + RE_VALOR,
    ],
    "iof": [
        r"IOF\s*\(Financiado\)\s*\n?\s*" + RE_VALOR,
        r"IOF[:\s]+" + RE_VALOR,
    ],
    "tarifa_cadastro": [
        r"Tarifa\s+de\s+Cadastro\s*\n?\s*" + RE_VALOR,
    ],
    "premio_seguro": [
        r"Pr[eê]mio\s+de\s+Seguro[^\n]*\n?\s*" + RE_VALOR,
    ],
    "nr_parcelas": [
        r"N[º°]?\s*de\s+Parcelas[^\n]*\n?\s*(\d+)",
    ],
    "valor_parcela": [
        r"Valor\s+Parcela\s*\n?\s*" + RE_VALOR,
    ],
    "contrato": [
        r"CCB[^\d]*(?:N[º°])?\s*(\d{10,})",
        r"Contrato\s+N?º?\s*(\d{10,})",
    ],
    "data_contratacao": [
        r"DATA\s+DE\s+EMISS[ÃA]O[:\s]+[^\d]*(\d{2}/\d{2}/\d{4})",
        r"Local\s+e\s+Data[^\d]*(\d{2}/\d{2}/\d{4})",
    ],
}

PADROES_TED = [
    r"VALOR\s*\n?\s*" + RE_VALOR,
    r"TED[^\n]*?\s*" + RE_VALOR,
    r"Valor\s+por\s+extenso[^\n]*?([\d\.]+,\d{2})",
]


def _extrair_primeiro(texto: str, padroes) -> Optional[str]:
    for p in padroes:
        m = re.search(p, texto, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def extrair_valores_ccb(texto_ccb: str) -> Dict:
    """Extrai campos da CCB. Retorna dict com strings originais e Decimals."""
    out = {}
    for campo, padroes in PADROES_CCB.items():
        raw = _extrair_primeiro(texto_ccb, padroes)
        out[campo + "_str"] = raw
        if campo in ("nr_parcelas",):
            out[campo] = int(raw) if raw and raw.isdigit() else None
        elif campo in ("contrato", "data_contratacao"):
            out[campo] = raw
        else:
            out[campo] = parse_br(raw) if raw else None
    return out


def extrair_valor_ted(texto_ted: str) -> Optional[Decimal]:
    raw = _extrair_primeiro(texto_ted, PADROES_TED)
    return parse_br(raw) if raw else None


# --------------------------------------------------------------------- #
# Análise
# --------------------------------------------------------------------- #
def acusar_diferenca(
    ccb: Dict,
    ted: Optional[Decimal],
    inicial_valor: Optional[Decimal] = None,
    tolerancia: Decimal = Decimal("0.01"),
) -> Dict:
    """Compara os valores e retorna diagnóstico estruturado.

    Retorna dict com:
      alertas: lista de strings (cada uma é um ALERTA pronto para relatório)
      comparacao: tabela estruturada
    """
    alertas = []
    comp = {
        "valor_liberado_ccb": ccb.get("valor_liberado"),
        "valor_total_financiado_ccb": ccb.get("valor_total_financiado"),
        "iof_ccb": ccb.get("iof"),
        "tarifa_cadastro_ccb": ccb.get("tarifa_cadastro"),
        "premio_seguro_ccb": ccb.get("premio_seguro"),
        "ted_transferido": ted,
        "valor_alegado_inicial": inicial_valor,
    }

    vl = ccb.get("valor_liberado")
    vtf = ccb.get("valor_total_financiado")
    iof = ccb.get("iof")
    tarifa = ccb.get("tarifa_cadastro") or Decimal("0")
    seguro = ccb.get("premio_seguro") or Decimal("0")

    # 1. Valor Total Financiado = Valor Liberado + IOF + Tarifa + Seguro ?
    if vl and vtf and iof is not None:
        esperado = vl + iof + tarifa + seguro
        if abs(vtf - esperado) > tolerancia:
            alertas.append(
                f"[INCONSISTÊNCIA INTERNA DA CCB] Valor Total Financiado ({fmt_br(vtf)}) "
                f"difere da soma Valor Liberado + IOF + Tarifas + Seguro ({fmt_br(esperado)}) "
                f"por {fmt_br(abs(vtf - esperado))}."
            )

    # 2. TED < Valor Liberado? (R$ X "somem" no caminho)
    if vl and ted:
        if abs(vl - ted) > tolerancia:
            diff = vl - ted
            if diff > 0:
                alertas.append(
                    f"[INCONSISTÊNCIA CCB × TED] A CCB indica Valor Liberado de "
                    f"{fmt_br(vl)}, mas o TED transferiu apenas {fmt_br(ted)} à "
                    f"conta do consumidor — diferença de {fmt_br(diff)} sem destinação "
                    f"explicada (possível comissão oculta a correspondente bancário, "
                    f"operação-ponte ou tarifa indevida). Argumento autônomo de fraude; "
                    f"não depende de perícia."
                )
            else:
                alertas.append(
                    f"[ATENÇÃO] TED ({fmt_br(ted)}) é SUPERIOR ao Valor Liberado "
                    f"({fmt_br(vl)}) — situação atípica."
                )

    # 3. Valor alegado na inicial bate com TED?
    if ted and inicial_valor and abs(ted - inicial_valor) > tolerancia:
        alertas.append(
            f"[DIVERGÊNCIA INICIAL × TED] Inicial afirma valor de "
            f"{fmt_br(inicial_valor)}, TED registra {fmt_br(ted)}."
        )

    return {
        "alertas": alertas,
        "comparacao": comp,
    }


def relatorio_texto(ccb: Dict, ted: Optional[Decimal],
                    inicial_valor: Optional[Decimal] = None) -> str:
    """Gera bloco de texto pronto para o relatório de conferência."""
    linhas = ["Cruzamento CCB × TED × Inicial:"]
    linhas.append(f"  Valor Liberado (CCB):            {fmt_br(ccb.get('valor_liberado'))}")
    linhas.append(f"  Valor Total Financiado (CCB):    {fmt_br(ccb.get('valor_total_financiado'))}")
    linhas.append(f"  IOF Financiado (CCB):            {fmt_br(ccb.get('iof'))}")
    linhas.append(f"  Tarifa de Cadastro (CCB):        {fmt_br(ccb.get('tarifa_cadastro'))}")
    linhas.append(f"  Prêmio de Seguro (CCB):          {fmt_br(ccb.get('premio_seguro'))}")
    linhas.append(f"  TED transferido à conta:         {fmt_br(ted)}")
    if inicial_valor is not None:
        linhas.append(f"  Valor alegado na inicial:        {fmt_br(inicial_valor)}")

    resultado = acusar_diferenca(ccb, ted, inicial_valor)
    if resultado["alertas"]:
        linhas.append("")
        linhas.append("Alertas:")
        for a in resultado["alertas"]:
            linhas.append(f"  - {a}")
    else:
        linhas.append("")
        linhas.append("Nenhuma divergência detectada.")

    return "\n".join(linhas)


if __name__ == "__main__":
    # Teste rápido com dados do caso Emilia
    texto_ccb_fake = """
    CÉDULA DE CRÉDITO BANCÁRIO (CCB) Nº 010120325224
    EMPRÉSTIMO CONSIGNADO
    Valor Liberado
    R$ 1.384,69
    Valor Total Financiado
    R$ 1.428,03
    IOF (Financiado)
    R$ 43,34
    Tarifa de Cadastro
    R$ 0,00
    Nº de Parcelas (mensais)
    84
    Valor Parcela
    37,80
    """
    dados = extrair_valores_ccb(texto_ccb_fake)
    ted = Decimal("1154.74")
    print(relatorio_texto(dados, ted, Decimal("1154.74")))
