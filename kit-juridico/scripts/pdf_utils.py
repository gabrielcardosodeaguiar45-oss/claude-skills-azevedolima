"""
Utilitários PDF baseados em PyMuPDF (fitz).

Substitui a versão legacy em PyPDF2 — PyMuPDF é muito mais rápido,
suporta text-layer com bbox, highlight nativo e otimização (garbage=4).

Uso CLI:
    python pdf_utils.py count <input.pdf>
    python pdf_utils.py split <input.pdf> <output_dir> [--per-page]
    python pdf_utils.py extract <input.pdf> <output.pdf> <start_page> <end_page>
    python pdf_utils.py merge <output.pdf> <file1.pdf> <file2.pdf> ...
"""
import sys
import os
from pathlib import Path

try:
    import fitz
except ImportError as e:
    raise ImportError(
        f"Dependência ausente: {e}. "
        f"Instale via: pip install -r requirements.txt"
    ) from e


def open_pdf(path: str):
    """
    Abre PDF tolerando caracteres Unicode no path. PyMuPDF no Windows
    eventualmente falha em paths com em-dash (—), graus (°) e outros
    chars. Este wrapper carrega bytes via Python e passa via stream.
    """
    try:
        return fitz.open(path)
    except Exception:
        # Fallback: ler bytes manualmente
        with open(path, "rb") as f:
            data = f.read()
        return fitz.open(stream=data, filetype="pdf")


def count_pages(input_path: str) -> int:
    """Retorna o número de páginas de um PDF."""
    with open_pdf(input_path) as doc:
        return len(doc)


def split_per_page(input_path: str, output_dir: str) -> list[str]:
    """Separa um PDF em N PDFs (um por página)."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out = []
    with open_pdf(input_path) as doc:
        for i in range(len(doc)):
            new = fitz.open()
            new.insert_pdf(doc, from_page=i, to_page=i)
            outpath = os.path.join(output_dir, f"pagina_{i+1:03d}.pdf")
            new.save(outpath, garbage=4, deflate=True)
            new.close()
            out.append(outpath)
    return out


def extract_pages(input_path: str, output_path: str, pages: list[int]) -> str:
    """Extrai páginas específicas (1-indexed) e salva em output_path."""
    with open_pdf(input_path) as doc:
        new = fitz.open()
        for p in pages:
            new.insert_pdf(doc, from_page=p-1, to_page=p-1)
        new.save(output_path, garbage=4, deflate=True)
        new.close()
    return output_path


def extract_page_range(input_path: str, output_path: str, start: int, end: int) -> str:
    """Extrai intervalo de páginas (1-indexed, inclusivo)."""
    return extract_pages(input_path, output_path, list(range(start, end+1)))


def merge_pdfs(output_path: str, input_paths: list[str]) -> str:
    """Junta múltiplos PDFs em um único arquivo."""
    new = fitz.open()
    for p in input_paths:
        with open_pdf(p) as doc:
            new.insert_pdf(doc)
    new.save(output_path, garbage=4, deflate=True)
    new.close()
    return output_path


def has_text_layer(input_path: str, threshold: int = 50) -> bool:
    """
    Verifica se o PDF tem text-layer útil. Retorna True se a soma de
    caracteres extraídos superar o threshold.
    """
    total = 0
    with open_pdf(input_path) as doc:
        for page in doc:
            total += len(page.get_text().strip())
            if total >= threshold:
                return True
    return False


def render_page(input_path: str, page_num: int, output_path: str,
                zoom: float = 2.0, rotation: int = 0) -> str:
    """Renderiza uma página como PNG. page_num é 1-indexed."""
    with open_pdf(input_path) as doc:
        page = doc[page_num - 1]
        mat = fitz.Matrix(zoom, zoom).prerotate(rotation)
        pix = page.get_pixmap(matrix=mat)
        pix.save(output_path)
    return output_path


def detect_orientation(input_path: str, page_num: int = 1) -> int:
    """
    Detecta orientação correta da página (0/90/180/270).
    Heurística: se mediabox é landscape (largura > altura), provavelmente
    foi escaneado em paisagem e o texto está rotacionado 90 ou 270.

    Retorna o ângulo prerotate sugerido para deixar o texto de pé.
    """
    with open_pdf(input_path) as doc:
        page = doc[page_num - 1]
        rect = page.mediabox
        if rect.width > rect.height * 1.2:
            # Paisagem; default 270 (depende do scanner — pode precisar de override).
            return 270
    return 0


# === CLI ===

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "count":
        print(count_pages(sys.argv[2]))
    elif cmd == "split":
        out = split_per_page(sys.argv[2], sys.argv[3])
        print(f"OK: {len(out)} páginas em {sys.argv[3]}")
    elif cmd == "extract":
        extract_page_range(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
        print(f"OK: {sys.argv[3]}")
    elif cmd == "merge":
        merge_pdfs(sys.argv[2], sys.argv[3:])
        print(f"OK: {sys.argv[2]}")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
