# -*- coding: utf-8 -*-
"""
Cruzamento da Tabela (PDF ou XLSX) com a inicial e o extrato.

A Tabela é o cálculo do total dos descontos sob a rubrica. Tipicamente
tem colunas: Data | Descrição | Valor | (corrigido).

Usa pdfplumber/openpyxl. Compara qtd de linhas e total da tabela com:
- O total declarado na inicial.
- A contagem feita no extrato (cruzamento_extrato).
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Tuple


def _ler_pdf_tabela(caminho: str) -> Tuple[List[List[str]], str]:
    """Lê tabela em PDF e retorna lista de linhas + texto bruto."""
    if not os.path.exists(caminho):
        return [], ""
    try:
        import pdfplumber
        rows: List[List[str]] = []
        texto = ""
        with pdfplumber.open(caminho) as pdf:
            for pg in pdf.pages:
                t = pg.extract_text() or ""
                texto += t + "\n"
                tabs = pg.extract_tables() or []
                for tab in tabs:
                    for linha in tab:
                        if linha and any((c or "").strip() for c in linha):
                            rows.append([(c or "").strip() for c in linha])
        return rows, texto
    except Exception:
        pass
    # Fallback pymupdf - sem extração de tabela, só texto
    try:
        import fitz
        doc = fitz.open(caminho)
        texto = ""
        for pg in doc:
            texto += pg.get_text() + "\n"
        doc.close()
        return [], texto
    except Exception:
        return [], ""


def _ler_xlsx_tabela(caminho: str) -> List[List[str]]:
    if not os.path.exists(caminho):
        return []
    try:
        import openpyxl
        wb = openpyxl.load_workbook(caminho, data_only=True)
        rows: List[List[str]] = []
        for ws in wb.worksheets:
            for linha in ws.iter_rows(values_only=True):
                vals = [str(c) if c is not None else "" for c in linha]
                if any(v.strip() for v in vals):
                    rows.append(vals)
        return rows
    except Exception:
        return []


def _parse_valor(s: str) -> Optional[float]:
    if not s:
        return None
    s = s.replace("R$", "").strip()
    # Remove parênteses (negativos)
    s = s.replace("(", "-").replace(")", "")
    s = s.replace(".", "").replace(",", ".")
    s = re.sub(r"[^\d\.\-]", "", s)
    try:
        return float(s)
    except ValueError:
        return None


def _somar_coluna_valor(rows: List[List[str]]) -> Tuple[int, float]:
    """Tenta identificar coluna de valor e somar.

    Heurística: pega a coluna com mais células parseáveis como número.
    """
    if not rows:
        return 0, 0.0

    n_cols = max(len(r) for r in rows)
    melhor_col = -1
    melhor_n = 0
    melhor_valores: List[float] = []
    for col in range(n_cols):
        vals = []
        for r in rows:
            if col < len(r):
                v = _parse_valor(r[col])
                if v is not None:
                    vals.append(v)
        if len(vals) > melhor_n:
            melhor_n = len(vals)
            melhor_col = col
            melhor_valores = vals

    qtd = len(melhor_valores)
    total = sum(abs(v) for v in melhor_valores)
    return qtd, round(total, 2)


def cruzar_tabela(
    caminho_tabela: str, total_inicial: Optional[float], qtd_inicial: Optional[int]
) -> Dict:
    """Cruza Tabela.pdf/.xlsx com inicial.

    Retorna {tem_tabela, qtd_tabela, total_tabela, divergencias, status}.
    """
    if not caminho_tabela or not os.path.exists(caminho_tabela):
        return {
            "tem_tabela": False,
            "divergencias": [{
                "campo": "tabela_ausente",
                "observacao": "Tabela.pdf/.xlsx não encontrada na pasta.",
                "severidade": "MEDIA",
            }],
            "status": "ALERTA",
        }

    ext = os.path.splitext(caminho_tabela)[1].lower()
    if ext == ".xlsx":
        rows = _ler_xlsx_tabela(caminho_tabela)
        texto_bruto = ""
    else:
        rows, texto_bruto = _ler_pdf_tabela(caminho_tabela)

    qtd_tab, total_tab = _somar_coluna_valor(rows)

    divergencias: List[Dict] = []

    if qtd_tab == 0:
        divergencias.append({
            "campo": "tabela_ilegivel",
            "observacao": "Não foi possível extrair valores numéricos da tabela. Verificar se o PDF é escaneado ou se a estrutura é incomum.",
            "severidade": "MEDIA",
        })

    if total_inicial is not None and total_tab > 0:
        if abs(total_inicial - total_tab) > max(1.0, total_inicial * 0.02):
            divergencias.append({
                "campo": "total_inicial_vs_tabela",
                "inicial": total_inicial,
                "tabela": total_tab,
                "observacao": f"Total declarado na inicial (R$ {total_inicial:.2f}) difere do total da tabela (R$ {total_tab:.2f}).",
                "severidade": "MEDIA",
            })

    if qtd_inicial is not None and qtd_tab > 0:
        if abs(qtd_inicial - qtd_tab) > max(1, qtd_inicial * 0.05):
            divergencias.append({
                "campo": "qtd_inicial_vs_tabela",
                "inicial": qtd_inicial,
                "tabela": qtd_tab,
                "observacao": f"Quantidade de descontos na inicial ({qtd_inicial}) difere da quantidade de linhas-valor na tabela ({qtd_tab}).",
                "severidade": "MEDIA",
            })

    status = "INCONSISTENTE" if any(d.get("severidade") == "ALTA" for d in divergencias) else (
        "ALERTA" if divergencias else "OK"
    )

    return {
        "tem_tabela": True,
        "caminho": caminho_tabela,
        "extensao": ext,
        "qtd_tabela": qtd_tab,
        "total_tabela": total_tab,
        "divergencias": divergencias,
        "status": status,
    }


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Uso: python cruzamento_tabela.py <tabela.pdf|.xlsx> [total_inicial] [qtd_inicial]")
        sys.exit(1)
    total = float(sys.argv[2]) if len(sys.argv) > 2 else None
    qtd = int(sys.argv[3]) if len(sys.argv) > 3 else None
    print(json.dumps(cruzar_tabela(sys.argv[1], total, qtd), indent=2, ensure_ascii=False))
