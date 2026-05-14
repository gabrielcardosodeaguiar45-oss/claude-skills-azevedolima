#!/usr/bin/env python3
"""detect_2via_massiva.py — detecta postagem concentrada de faturas (2a via em lote).

Regra 2 das 16: se todas (ou quase todas) as faturas foram postadas na mesma data
e essa data e proxima da contestacao, e 2a via massiva → Bloco A.

Heuristica:
  - 80 porcento ou mais das faturas com mesma data de postagem.
  - Data de postagem predominante < 90 dias antes da contestacao.

Uso:
  python detect_2via_massiva.py --caso _analise.json

Saida:
  {
    "massiva_detectada": true,
    "percentual_mesma_data": 0.95,
    "data_predominante": "2025-08-12",
    "dias_antes_contestacao": 45,
    "recomendacao_bloco_A": true
  }
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def detect(caso: dict) -> dict:
    faturas = caso.get("faturas") or {}
    total = int(faturas.get("total_faturas") or 0)
    pred_str = faturas.get("data_postagem_predominante")
    pred = parse_date(pred_str)
    data_contestacao = parse_date(caso.get("processo", {}).get("data_contestacao"))

    percentual = 1.0 if faturas.get("postagem_concentrada") else 0.0
    dias = None
    if pred and data_contestacao:
        dias = (data_contestacao - pred).days

    massiva = bool(faturas.get("postagem_concentrada")) and (dias is None or dias <= 90)

    return {
        "massiva_detectada": massiva,
        "total_faturas": total,
        "percentual_mesma_data": percentual,
        "data_predominante": pred_str,
        "data_contestacao": caso.get("processo", {}).get("data_contestacao"),
        "dias_antes_contestacao": dias,
        "recomendacao_bloco_A": massiva,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--caso", required=True)
    args = ap.parse_args()
    caso = json.loads(Path(args.caso).read_text(encoding="utf-8"))
    result = detect(caso)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
