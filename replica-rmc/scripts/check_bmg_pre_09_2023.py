#!/usr/bin/env python3
"""check_bmg_pre_09_2023.py — flag para BMG com averbacao anterior a 01/09/2023.

Regra 7 das 16: o proprio BMG admitiu em contestacoes posteriores que passou a
exigir videochamada biometrica apenas a partir de 09/2023 (IN PRES/INSS 138/2022).
Logo, para averbacoes anteriores, nao ha meio biometrico forte — Bloco C.

Uso:
  python check_bmg_pre_09_2023.py --caso _analise.json

Saida:
  {
    "aplicavel": true,
    "banco_eh_bmg": true,
    "data_averbacao": "2022-04-15",
    "anterior_a_01_09_2023": true,
    "recomendacao_bloco_C": true
  }
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


CUTOFF = date(2023, 9, 1)


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def check(caso: dict) -> dict:
    banco = (caso.get("banco") or {}).get("razao_social") or ""
    contrato = caso.get("contrato_principal") or {}
    data_str = contrato.get("data_averbacao")
    dt = parse_date(data_str)
    eh_bmg = "bmg" in banco.lower()
    anterior = bool(dt and dt < CUTOFF)
    return {
        "aplicavel": eh_bmg and anterior,
        "banco_eh_bmg": eh_bmg,
        "banco_razao_social": banco,
        "data_averbacao": data_str,
        "cutoff": CUTOFF.isoformat(),
        "anterior_a_01_09_2023": anterior,
        "recomendacao_bloco_C": eh_bmg and anterior,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--caso", required=True)
    args = ap.parse_args()
    caso = json.loads(Path(args.caso).read_text(encoding="utf-8"))
    result = check(caso)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
