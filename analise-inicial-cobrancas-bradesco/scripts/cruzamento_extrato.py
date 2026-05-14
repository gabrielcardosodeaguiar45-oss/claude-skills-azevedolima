# -*- coding: utf-8 -*-
"""
Cruzamento de período / quantidade / total declarados na inicial com extrato bancário.

Lê o PDF do extrato (com pdfplumber ou pymupdf), conta lançamentos da rubrica
e soma os valores. Compara com o que a inicial alega.

Saída:
{
  'inicial': {'data_inicio': '07/01/2026', 'data_fim': '07/11/2025', 'qtd': 121, 'total': 13607.22},
  'extrato': {'data_inicio': '...', 'data_fim': '...', 'qtd_rubrica': 110, 'total_rubrica': 12045.50},
  'divergencias': [
      {'campo': 'periodo', 'inicial': '07/01/2026 a 07/11/2025', 'observacao': 'data inicial > data final', 'severidade': 'ALTA'},
      ...
  ],
  'status': 'OK' | 'ALERTA' | 'INCONSISTENTE'
}
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def _ler_pdf(caminho: str) -> str:
    """Tenta ler com pdfplumber, depois pymupdf."""
    if not caminho or not os.path.exists(caminho):
        return ""
    texto = ""
    try:
        import pdfplumber
        with pdfplumber.open(caminho) as pdf:
            for pg in pdf.pages:
                t = pg.extract_text()
                if t:
                    texto += t + "\n"
        if texto.strip():
            return texto
    except Exception:
        pass
    try:
        import fitz  # pymupdf
        doc = fitz.open(caminho)
        for pg in doc:
            texto += pg.get_text() + "\n"
        doc.close()
    except Exception:
        pass
    return texto


def _parse_data(s: str) -> Optional[datetime]:
    """Parse de data em formato dd/mm/aaaa."""
    if not s:
        return None
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s.strip())
    if not m:
        return None
    try:
        d, mo, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return datetime(a, mo, d)
    except ValueError:
        return None


def _parse_valor(s: str) -> Optional[float]:
    """Converte 'R$ 13.607,22' ou '13.607,22' para float."""
    if not s:
        return None
    s = s.replace("R$", "").strip()
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def extrair_alegacoes_inicial(texto_inicial: str) -> Dict:
    """Extrai período, qtd e total da inicial.

    Procura por padrões como:
        "desde a data de [DD/MM/AAAA] a [DD/MM/AAAA]"
        "[N] (extenso) descontos"
        "totalizando um montante de R$ [VALOR]"
    """
    out: Dict = {
        "data_inicio": None, "data_fim": None,
        "qtd": None, "qtd_extenso": None,
        "total": None, "total_extenso": None,
    }

    # Período
    m = re.search(
        r"desde\s+a?\s*data\s+de\s+(\d{1,2}/\d{1,2}/\d{4})\s+a\s+(\d{1,2}/\d{1,2}/\d{4})",
        texto_inicial, re.IGNORECASE,
    )
    if m:
        out["data_inicio"] = m.group(1)
        out["data_fim"] = m.group(2)

    # Quantidade de descontos
    m = re.search(
        r"\b(?:foram\s+realizados\s+|realizaram-se\s+|j[áa]\s+foram?\s+realizad[oa]s?\s+)?"
        r"(\d{1,4})\s*\(([^)]+)\)\s+descontos?",
        texto_inicial, re.IGNORECASE,
    )
    if m:
        try:
            out["qtd"] = int(m.group(1))
            out["qtd_extenso"] = m.group(2).strip()
        except ValueError:
            pass

    # Total descontado
    m = re.search(
        r"totalizando\s+um\s+montante\s+de\s+R?\$?\s*([\d\.\,]+)\s*\(([^)]+)\)",
        texto_inicial, re.IGNORECASE,
    )
    if m:
        out["total"] = _parse_valor(m.group(1))
        out["total_extenso"] = m.group(2).strip()

    return out


def contar_rubrica_no_extrato(
    texto_extrato: str, rubricas: List[str]
) -> Tuple[int, float, Optional[datetime], Optional[datetime]]:
    """Conta linhas com a rubrica no extrato e soma valores.

    Cada linha tipicamente tem: 'DD/MM/AAAA  DESCRICAO  VALOR'.
    Como o parsing exato varia muito por banco, fazemos uma estimativa
    contando ocorrências da rubrica e somando o primeiro valor numérico
    presente na mesma linha.
    """
    if not texto_extrato:
        return 0, 0.0, None, None

    qtd = 0
    total = 0.0
    datas: List[datetime] = []

    linhas = texto_extrato.split("\n")
    for linha in linhas:
        # Verifica se a rubrica está presente
        achou = False
        for r in rubricas:
            if r.lower() in linha.lower():
                achou = True
                break
        if not achou:
            continue

        qtd += 1

        # Extrai data
        m_data = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", linha)
        if m_data:
            d = _parse_data(m_data.group(1))
            if d:
                datas.append(d)

        # Extrai valor (último número com vírgula da linha)
        valores = re.findall(r"-?\s*\d{1,3}(?:\.\d{3})*,\d{2}\b", linha)
        if valores:
            v = _parse_valor(valores[-1])
            if v is not None:
                total += abs(v)

    data_inicio = min(datas) if datas else None
    data_fim = max(datas) if datas else None
    return qtd, total, data_inicio, data_fim


def cruzar_extrato(
    texto_inicial: str, caminho_extrato: str, rubricas_alvo: List[str]
) -> Dict:
    """Função principal. Cruza o que a inicial diz com o extrato."""
    aleg = extrair_alegacoes_inicial(texto_inicial)
    texto_extrato = _ler_pdf(caminho_extrato)

    extrato_info = {
        "tem_texto": bool(texto_extrato.strip()),
        "qtd_rubrica": None,
        "total_rubrica": None,
        "data_inicio": None,
        "data_fim": None,
        "rubricas_buscadas": rubricas_alvo,
    }

    if texto_extrato.strip():
        qtd, total, di, df = contar_rubrica_no_extrato(texto_extrato, rubricas_alvo)
        extrato_info["qtd_rubrica"] = qtd
        extrato_info["total_rubrica"] = round(total, 2)
        extrato_info["data_inicio"] = di.strftime("%d/%m/%Y") if di else None
        extrato_info["data_fim"] = df.strftime("%d/%m/%Y") if df else None

    divergencias: List[Dict] = []

    # Datas invertidas na inicial
    di_aleg = _parse_data(aleg.get("data_inicio") or "")
    df_aleg = _parse_data(aleg.get("data_fim") or "")
    if di_aleg and df_aleg and di_aleg > df_aleg:
        divergencias.append({
            "campo": "periodo_invertido",
            "inicial": f"{aleg['data_inicio']} a {aleg['data_fim']}",
            "observacao": "Data inicial é POSTERIOR à data final - período invertido.",
            "severidade": "ALTA",
        })

    # Comparar período inicial x extrato
    di_ext = _parse_data(extrato_info.get("data_inicio") or "")
    df_ext = _parse_data(extrato_info.get("data_fim") or "")
    if di_aleg and di_ext and abs((di_aleg - di_ext).days) > 30:
        divergencias.append({
            "campo": "data_inicio_divergente",
            "inicial": aleg.get("data_inicio"),
            "extrato": extrato_info.get("data_inicio"),
            "observacao": "Data inicial declarada na inicial difere em mais de 30 dias da primeira ocorrência da rubrica no extrato.",
            "severidade": "MEDIA",
        })
    if df_aleg and df_ext and abs((df_aleg - df_ext).days) > 30:
        divergencias.append({
            "campo": "data_fim_divergente",
            "inicial": aleg.get("data_fim"),
            "extrato": extrato_info.get("data_fim"),
            "observacao": "Data final declarada na inicial difere em mais de 30 dias da última ocorrência da rubrica no extrato.",
            "severidade": "MEDIA",
        })

    # Quantidade
    qtd_aleg = aleg.get("qtd")
    qtd_ext = extrato_info.get("qtd_rubrica")
    if qtd_aleg is not None and qtd_ext is not None:
        if qtd_ext == 0 and qtd_aleg > 0:
            divergencias.append({
                "campo": "quantidade_zero",
                "inicial": qtd_aleg,
                "extrato": qtd_ext,
                "observacao": "A inicial alega N descontos, mas a busca pela rubrica no extrato não retornou nenhum lançamento. Pode ser falha de parsing do PDF (extrato escaneado) ou rubrica diferente.",
                "severidade": "MEDIA",
            })
        elif abs(qtd_aleg - qtd_ext) > max(2, qtd_aleg * 0.05):
            divergencias.append({
                "campo": "quantidade_divergente",
                "inicial": qtd_aleg,
                "extrato": qtd_ext,
                "observacao": f"Quantidade de descontos declarada ({qtd_aleg}) difere da contagem no extrato ({qtd_ext}).",
                "severidade": "MEDIA",
            })

    # Total
    tot_aleg = aleg.get("total")
    tot_ext = extrato_info.get("total_rubrica")
    if tot_aleg is not None and tot_ext is not None and tot_ext > 0:
        if abs(tot_aleg - tot_ext) > max(1.0, tot_aleg * 0.02):
            divergencias.append({
                "campo": "total_divergente",
                "inicial": tot_aleg,
                "extrato": tot_ext,
                "observacao": f"Total declarado (R$ {tot_aleg:.2f}) difere da soma dos lançamentos da rubrica no extrato (R$ {tot_ext:.2f}).",
                "severidade": "MEDIA",
            })

    if not extrato_info["tem_texto"]:
        divergencias.append({
            "campo": "extrato_ilegivel",
            "observacao": "Não foi possível extrair texto do extrato. Verificar se o PDF é escaneado (precisaria de OCR) ou se está corrompido. Conferência de período/qtd/total não pôde ser feita programaticamente.",
            "severidade": "MEDIA",
        })

    if any(d["severidade"] == "ALTA" for d in divergencias):
        status = "INCONSISTENTE"
    elif divergencias:
        status = "ALERTA"
    else:
        status = "OK"

    return {
        "inicial": aleg,
        "extrato": extrato_info,
        "divergencias": divergencias,
        "status": status,
    }


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 3:
        print("Uso: python cruzamento_extrato.py <inicial.txt> <extrato.pdf> [rubrica1,rubrica2,...]")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        texto = f.read()
    rubricas = sys.argv[3].split(",") if len(sys.argv) > 3 else ["Mora Cred Pess"]
    print(json.dumps(cruzar_extrato(texto, sys.argv[2], rubricas), indent=2, ensure_ascii=False))
