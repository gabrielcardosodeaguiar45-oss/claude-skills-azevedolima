#!/usr/bin/env python3
"""check_cartao_gemeo.py — detecta cartao gemeo (Santander e correlatos).

Regra 10 das 16: se a terminacao do cartao que aparece nas faturas difere da
terminacao do cartao constante do contrato/pedido, ha dois cartoes — o banco
misturou dois contratos. Levantar impugnacao especifica.

Uso:
  python check_cartao_gemeo.py --caso _analise.json

Saida:
  {
    "gemeo_detectado": true,
    "terminacao_contrato": "1234",
    "terminacao_faturas": "5678",
    "banco": "Banco Santander ...",
    "recomendacao_paragrafo_gemeo": true
  }
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def last4(s: str | None) -> str:
    if not s:
        return ""
    digits = re.sub(r"[^0-9]", "", s)
    return digits[-4:] if len(digits) >= 4 else digits


def check(caso: dict) -> dict:
    contrato = caso.get("contrato_principal") or {}
    faturas = caso.get("faturas") or {}
    banco = (caso.get("banco") or {}).get("razao_social") or ""
    t_contrato = last4(contrato.get("terminacao_cartao"))
    t_faturas = last4(faturas.get("terminacao_cartao_faturas"))
    gemeo = bool(t_contrato and t_faturas and t_contrato != t_faturas)
    return {
        "gemeo_detectado": gemeo,
        "terminacao_contrato": t_contrato or None,
        "terminacao_faturas": t_faturas or None,
        "banco": banco,
        "santander": "santander" in banco.lower(),
        "recomendacao_paragrafo_gemeo": gemeo,
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
