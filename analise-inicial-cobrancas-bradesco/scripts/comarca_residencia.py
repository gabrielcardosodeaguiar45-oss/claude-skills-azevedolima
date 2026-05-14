# -*- coding: utf-8 -*-
"""
Verifica se a comarca declarada na inicial corresponde ao domicílio do
cliente (comprovante de residência + qualificação na inicial).
"""
from __future__ import annotations

import os
import re
import unicodedata
from typing import Dict, List, Optional


def _norm(s: str) -> str:
    if not s:
        return ""
    n = unicodedata.normalize("NFKD", s)
    n = "".join(c for c in n if not unicodedata.combining(c))
    return n.upper().strip()


def _ler_pdf(caminho: str) -> str:
    if not caminho or not os.path.exists(caminho):
        return ""
    try:
        import pdfplumber
        texto = ""
        with pdfplumber.open(caminho) as pdf:
            for pg in pdf.pages:
                t = pg.extract_text() or ""
                texto += t + "\n"
        if texto.strip():
            return texto
    except Exception:
        pass
    try:
        import fitz
        doc = fitz.open(caminho)
        texto = ""
        for pg in doc:
            texto += pg.get_text() + "\n"
        doc.close()
        return texto
    except Exception:
        return ""


def extrair_comarca_inicial(texto_inicial: str) -> Optional[str]:
    """Extrai a cidade/comarca do endereçamento da inicial."""
    if not texto_inicial:
        return None
    # Padrões comuns
    padroes = [
        r"Comarca\s+d[eo]\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^/]+?)\s*/\s*AM",
        r"Juizado\s+Especial[^,]*?d[eo]\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^/]+?)\s*/\s*AM",
    ]
    for p in padroes:
        m = re.search(p, texto_inicial, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def extrair_cidade_qualificacao(texto_inicial: str) -> Optional[str]:
    """Extrai cidade do endereço do autor na qualificação."""
    if not texto_inicial:
        return None
    padroes = [
        r"Munic[íi]pio\s+d[eo]\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^/,\.]+?)\s*/\s*AM",
        r"em\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^,]+?)\s*/\s*AM",
    ]
    for p in padroes:
        m = re.search(p, texto_inicial)
        if m:
            return m.group(1).strip()
    return None


def extrair_cidade_comprovante(texto_comprovante: str) -> Optional[str]:
    """Extrai cidade do comprovante de residência (heurística)."""
    if not texto_comprovante:
        return None
    # Busca CEP + cidade
    m = re.search(
        r"\b\d{5}[-\s]?\d{3}\b[^,\n]*?([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ſ\s]+?)\s*[-/]?\s*AM\b",
        texto_comprovante,
    )
    if m:
        return m.group(1).strip()
    # Busca direto "Cidade/AM"
    m = re.search(r"([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ſ\s]+?)\s*[-/]\s*AM\b", texto_comprovante)
    if m:
        return m.group(1).strip()
    return None


def verificar_comarca(
    texto_inicial: str, caminho_comprovante: Optional[str]
) -> Dict:
    """Cruza comarca da inicial com cidade do comprovante de residência."""
    out: Dict = {
        "comarca_inicial": None,
        "cidade_qualificacao": None,
        "cidade_comprovante": None,
        "tem_comprovante": bool(caminho_comprovante and os.path.exists(caminho_comprovante)),
        "divergencias": [],
        "status": "OK",
    }

    out["comarca_inicial"] = extrair_comarca_inicial(texto_inicial)
    out["cidade_qualificacao"] = extrair_cidade_qualificacao(texto_inicial)

    if not out["comarca_inicial"]:
        out["divergencias"].append({
            "campo": "comarca_nao_extraida",
            "observacao": "Não foi possível extrair a comarca do endereçamento da inicial. Confirmar manualmente.",
            "severidade": "BAIXA",
        })

    if out["tem_comprovante"]:
        texto_comp = _ler_pdf(caminho_comprovante)
        out["cidade_comprovante"] = extrair_cidade_comprovante(texto_comp)
        if not out["cidade_comprovante"]:
            out["divergencias"].append({
                "campo": "comprovante_ilegivel",
                "observacao": "Comprovante de residência ilegível ou cidade não identificada (provavelmente escaneado). Validar manualmente.",
                "severidade": "BAIXA",
            })
    else:
        out["divergencias"].append({
            "campo": "comprovante_ausente",
            "observacao": "Comprovante de residência ausente da pasta.",
            "severidade": "ALTA",
        })

    # Comparar comarca inicial com cidade qualificação
    if out["comarca_inicial"] and out["cidade_qualificacao"]:
        if _norm(out["comarca_inicial"]) != _norm(out["cidade_qualificacao"]):
            out["divergencias"].append({
                "campo": "comarca_x_qualificacao",
                "comarca_inicial": out["comarca_inicial"],
                "cidade_qualificacao": out["cidade_qualificacao"],
                "observacao": (
                    f"Comarca declarada na inicial ({out['comarca_inicial']}) difere "
                    f"da cidade na qualificação do autor ({out['cidade_qualificacao']})."
                ),
                "severidade": "ALTA",
            })

    # Comparar comarca inicial com cidade do comprovante
    if out["comarca_inicial"] and out["cidade_comprovante"]:
        if _norm(out["comarca_inicial"]) != _norm(out["cidade_comprovante"]):
            out["divergencias"].append({
                "campo": "comarca_x_comprovante",
                "comarca_inicial": out["comarca_inicial"],
                "cidade_comprovante": out["cidade_comprovante"],
                "observacao": (
                    f"Comarca da inicial ({out['comarca_inicial']}) difere da cidade "
                    f"do comprovante de residência ({out['cidade_comprovante']}). "
                    f"Risco de incompetência territorial."
                ),
                "severidade": "ALTA",
            })

    if any(d["severidade"] == "ALTA" for d in out["divergencias"]):
        out["status"] = "INCONSISTENTE"
    elif out["divergencias"]:
        out["status"] = "ALERTA"

    return out


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 3:
        print("Uso: python comarca_residencia.py <inicial.txt> <comprovante.pdf>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        texto = f.read()
    print(json.dumps(verificar_comarca(texto, sys.argv[2]), indent=2, ensure_ascii=False))
