#!/usr/bin/env python3
"""check_ip_rfc1918.py — classifica IP em publico/privado segundo RFC 1918.

Faixas privadas RFC 1918:
  10.0.0.0/8
  172.16.0.0 — 172.31.255.255  (NOTA: 172.15.x.x e 172.32.x.x são PUBLICOS)
  192.168.0.0/16

Uso:
  python check_ip_rfc1918.py <IP>
  python check_ip_rfc1918.py --json '{"ip":"187.90.23.45"}'

Saida:
  {
    "ip": "187.90.23.45",
    "classe": "publico",
    "faixa_rfc1918": null
  }
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import sys


RFC1918_BLOCKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def classify(ip_str: str) -> dict:
    try:
        ip = ipaddress.ip_address(ip_str.strip())
    except ValueError as exc:
        return {"ip": ip_str, "classe": "invalido", "erro": str(exc)}
    for block in RFC1918_BLOCKS:
        if ip in block:
            return {"ip": str(ip), "classe": "privado", "faixa_rfc1918": str(block)}
    return {"ip": str(ip), "classe": "publico", "faixa_rfc1918": None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip", nargs="?")
    ap.add_argument("--json", help="JSON com chave 'ip'")
    args = ap.parse_args()
    if args.json:
        data = json.loads(args.json)
        ip = data.get("ip")
    else:
        ip = args.ip
    if not ip:
        print(json.dumps({"erro": "IP ausente"}, ensure_ascii=False))
        return 2
    result = classify(ip)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["classe"] in {"publico", "privado"} else 1


if __name__ == "__main__":
    sys.exit(main())
