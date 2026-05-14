#!/usr/bin/env python3
"""extract_processo.py — extracao estruturada de PDFs de processo RMC/RCC.

Usa PyMuPDF (fitz) para extrair texto pagina-a-pagina. Para PDFs grandes
(>80 paginas), salva em arquivo temp e devolve o caminho para que o agente
leia por offset/limit. Inclui detectores regex para CNJ, CPF, OAB, IP, hash.

Uso:
  python extract_processo.py --pdf <caminho.pdf> [--out <saida.txt>]
  python extract_processo.py --pasta <pasta-fatiada> [--tmpdir <dir>]

Saida:
  Quando --pdf:
    {"arquivo": "...", "paginas": N, "txt_path": "...", "metadados_basicos": {...}}
  Quando --pasta:
    {"arquivos": [{"tipo":"inicial","path":"...","txt_path":"...","pagiinas":N}, ...]}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print(json.dumps({"erro": "PyMuPDF nao instalado. Rodar: pip install pymupdf"}))
    sys.exit(2)


REGEX_CNJ = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
REGEX_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
REGEX_OAB = re.compile(r"OAB[/\s]?(AM|AL|BA|MG|SC|SP|RJ|PE|CE|PR|GO|MT|MS|RO|AC|RR|AP|PA|MA|PI|RN|PB|TO|ES|DF)\s*\d+[A-Z]?")
REGEX_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
REGEX_HASH256 = re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE)
REGEX_MONEY = re.compile(r"R\$\s?[\d.]+,\d{2}")


CLASSIFIER_KEYWORDS = {
    "inicial": ["pet. inicial", "peticao inicial", "exmo.", "exma.", "causa de pedir"],
    "contestacao": ["contestacao", "contesta cao", "preliminarmente"],
    "hiscon": ["historico de emprestimo", "hiscon", "hiscre", "consignacoes em benef"],
    "ccb": ["cedula de credito bancario", "ccb n", "ccb nº"],
    "laudo_digital": ["formalizacao", "assinatura eletronica", "icp-brasil", "clicksign", "docusign"],
    "ted": ["transferencia eletronica", "comprovante de transferencia"],
    "fatura": ["fatura do cartao", "data de postagem"],
    "procuracao": ["procuracao"],
    "decisao": ["decisao", "defiro", "despacho"],
}


def classify(nome_arquivo: str, texto_amostra: str) -> str:
    low = (nome_arquivo + " " + texto_amostra[:2000]).lower()
    for tipo, palavras in CLASSIFIER_KEYWORDS.items():
        for p in palavras:
            if p in low:
                return tipo
    return "indefinido"


def extract_pdf(pdf_path: Path, out_path: Path | None = None) -> dict:
    doc = fitz.open(pdf_path)
    paginas = len(doc)
    chunks = []
    for i, page in enumerate(doc, start=1):
        texto = page.get_text("text")
        chunks.append(f"\n===== PAG {i}/{paginas} — {pdf_path.name} =====\n")
        chunks.append(texto)
    full = "".join(chunks)
    doc.close()

    if out_path is None:
        tmpdir = Path(tempfile.gettempdir())
        out_path = tmpdir / f"extract-{pdf_path.stem}.txt"
    out_path.write_text(full, encoding="utf-8")

    cnj = REGEX_CNJ.search(full)
    cpf_primeiro = REGEX_CPF.search(full)
    oab_primeiro = REGEX_OAB.search(full)

    return {
        "arquivo": str(pdf_path),
        "paginas": paginas,
        "txt_path": str(out_path),
        "tipo_heuristico": classify(pdf_path.name, full),
        "metadados_basicos": {
            "cnj_primeiro_match": cnj.group(0) if cnj else None,
            "cpf_primeiro_match": cpf_primeiro.group(0) if cpf_primeiro else None,
            "oab_primeiro_match": oab_primeiro.group(0) if oab_primeiro else None,
            "total_ips": len(REGEX_IP.findall(full)),
            "total_hashes_sha256": len(REGEX_HASH256.findall(full)),
        },
    }


def extract_folder(pasta: Path, tmpdir: Path | None = None) -> dict:
    tmpdir = tmpdir or Path(tempfile.gettempdir())
    pdfs = sorted(pasta.glob("*.pdf"))
    arquivos = []
    for pdf in pdfs:
        out = tmpdir / f"extract-{pdf.stem}.txt"
        arquivos.append(extract_pdf(pdf, out))
    return {
        "pasta": str(pasta),
        "total_pdfs": len(pdfs),
        "arquivos": arquivos,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--pdf", type=Path)
    grp.add_argument("--pasta", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--tmpdir", type=Path)
    args = ap.parse_args()

    if args.pdf:
        result = extract_pdf(args.pdf, args.out)
    else:
        result = extract_folder(args.pasta, args.tmpdir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
