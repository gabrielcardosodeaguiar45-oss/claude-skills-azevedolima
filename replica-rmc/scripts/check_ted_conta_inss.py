#!/usr/bin/env python3
"""check_ted_conta_inss.py — cruza conta de destino da TED contra conta INSS.

Regra 4 das 16: se a TED foi enviada para conta em banco distinto daquele em que o
autor recebe o beneficio, o argumento de que "o credito foi recebido" cai. Bloco B
de regras-de-adaptacao.md deve ser invocado.

Uso:
  python check_ted_conta_inss.py --caso _analise.json

Saida:
  {
    "divergencia_detectada": true,
    "teds_divergentes": [
      {"data": "...", "valor": ..., "conta_destino": "...", "conta_inss": "..."},
    ],
    "recomendacao_bloco_B": true
  }
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def normalize_conta(conta: str | None) -> str:
    if not conta:
        return ""
    return re.sub(r"[^0-9]", "", conta)


def check(caso: dict) -> dict:
    teds = caso.get("teds") or []
    conta_inss = normalize_conta(teds[0].get("conta_inss_do_autor") if teds else None)
    if not conta_inss:
        return {
            "divergencia_detectada": False,
            "motivo": "conta_inss ausente em _analise.json",
            "recomendacao_bloco_B": False,
        }
    divergentes = []
    for i, ted in enumerate(teds):
        conta_dest = normalize_conta(ted.get("conta_destino"))
        if conta_dest and conta_dest != conta_inss:
            divergentes.append(
                {
                    "indice": i,
                    "data": ted.get("data"),
                    "valor": ted.get("valor"),
                    "banco_destino": ted.get("banco_destino"),
                    "agencia_destino": ted.get("agencia_destino"),
                    "conta_destino": ted.get("conta_destino"),
                    "conta_inss": conta_inss,
                }
            )
    return {
        "divergencia_detectada": bool(divergentes),
        "total_teds": len(teds),
        "total_divergentes": len(divergentes),
        "teds_divergentes": divergentes,
        "recomendacao_bloco_B": bool(divergentes),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--caso", required=True, help="Caminho do _analise.json")
    args = ap.parse_args()
    caso = json.loads(Path(args.caso).read_text(encoding="utf-8"))
    result = check(caso)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
