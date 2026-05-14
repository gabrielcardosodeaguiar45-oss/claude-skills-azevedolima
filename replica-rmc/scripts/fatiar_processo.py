#!/usr/bin/env python3
"""fatiar_processo.py — fatia PDF consolidado em arquivos por peca.

Wrapper simplificado para casos em que a skill `fatiar-processo` nao esteja
disponivel no ambiente. Usa heuristica de palavras-chave no inicio de cada
pagina. Para casos complexos, prefira a skill oficial.

Uso:
  python fatiar_processo.py --pdf <consolidado.pdf> --out <pasta-saida>

Saida:
  {
    "consolidado": "...",
    "pasta_saida": "...",
    "arquivos": [{"tipo":"inicial","path":"001-inicial.pdf","pagina_inicial":1,"pagina_final":18}, ...]
  }
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import fitz
except ImportError:
    print(json.dumps({"erro": "PyMuPDF nao instalado. Rodar: pip install pymupdf"}))
    sys.exit(2)


MARCADORES = [
    ("inicial", ["peticao inicial", "pet. inicial", "exmo. sr.", "exma. sra."]),
    ("procuracao", ["procuracao"]),
    ("hiscon", ["historico de emprestimo consignado", "consignacoes em benef"]),
    ("contestacao", ["contestacao", "preliminarmente"]),
    ("ccb", ["cedula de credito bancario", "ccb n"]),
    ("laudo_digital", ["formalizacao", "assinatura eletronica"]),
    ("ted", ["comprovante de transferencia", "transferencia eletronica"]),
    ("fatura", ["fatura do cartao", "data de postagem"]),
    ("decisao", ["defiro", "despacho"]),
]


def classifica(texto: str) -> str | None:
    low = texto.lower()
    for tipo, palavras in MARCADORES:
        for p in palavras:
            if p in low[:1500]:
                return tipo
    return None


def fatiar(pdf_path: Path, pasta_saida: Path) -> dict:
    pasta_saida.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    segmentos: list[dict] = []
    atual: dict | None = None
    for i, page in enumerate(doc, start=1):
        txt = page.get_text("text")
        tipo = classifica(txt)
        if tipo and (atual is None or tipo != atual["tipo"]):
            if atual is not None:
                atual["pagina_final"] = i - 1
                segmentos.append(atual)
            atual = {"tipo": tipo, "pagina_inicial": i}
    if atual is not None:
        atual["pagina_final"] = len(doc)
        segmentos.append(atual)

    arquivos = []
    for idx, seg in enumerate(segmentos, start=1):
        nome = f"{idx:03d}-{seg['tipo']}.pdf"
        caminho = pasta_saida / nome
        new = fitz.open()
        new.insert_pdf(doc, from_page=seg["pagina_inicial"] - 1, to_page=seg["pagina_final"] - 1)
        new.save(caminho, garbage=4, deflate=True)
        new.close()
        arquivos.append({
            "tipo": seg["tipo"],
            "path": str(caminho),
            "pagina_inicial": seg["pagina_inicial"],
            "pagina_final": seg["pagina_final"],
        })
    doc.close()
    return {
        "consolidado": str(pdf_path),
        "pasta_saida": str(pasta_saida),
        "total_segmentos": len(arquivos),
        "arquivos": arquivos,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = fatiar(args.pdf, args.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
