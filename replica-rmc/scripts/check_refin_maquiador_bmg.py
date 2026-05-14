#!/usr/bin/env python3
"""check_refin_maquiador_bmg.py — detecta "credito de refin" sem queda de saldo.

Regra 9 das 16 (caso ANTONIO MARCOS — BMG Maues, novembro/2023):
o BMG lancou como refinanciamento um valor que nao abateu o saldo devedor
(saldo permanece identico, so muda a amortizacao). E onerosidade quantificada:
nao e hipotese — e evidencia documental.

Uso:
  python check_refin_maquiador_bmg.py --caso _analise.json

Saida:
  {
    "aplicavel": true,
    "banco_eh_bmg": true,
    "refin_maquiador_detectado": true,
    "data_refin": "2023-11-14",
    "valor_refin": 1875.00,
    "recomendacao_secao_onerosidade": true
  }
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def check(caso: dict) -> dict:
    banco = (caso.get("banco") or {}).get("razao_social") or ""
    faturas = caso.get("faturas") or {}
    detectado = bool(faturas.get("refin_maquiador_detectado"))
    eh_bmg = "bmg" in banco.lower()
    return {
        "aplicavel": eh_bmg and detectado,
        "banco_eh_bmg": eh_bmg,
        "refin_maquiador_detectado": detectado,
        "data_refin": faturas.get("data_refin_maquiador"),
        "valor_refin": faturas.get("valor_refin_maquiador"),
        "recomendacao_secao_onerosidade": eh_bmg and detectado,
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
