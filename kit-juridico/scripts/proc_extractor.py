"""
Extrator de procurações: detecta rotação, recorta o bloco "PODERES ESPECIAIS"
e prepara crops para o Claude (via Read) extrair banco + tipo + contrato.

Uso:
    python proc_extractor.py <pdf_procuracoes> <output_dir>

Saída em <output_dir>:
    - crops_pag_NN.png  (1 crop por página, com a região PODERES ESPECIAIS)
    - manifesto.json    (lista de páginas com path, tamanho)

Como a extração final do banco/contrato exige inteligência de leitura
(formatos variados), este script só prepara os crops. O orquestrador
(pipeline.py) usa esses crops via Read tool para pedir ao modelo a
extração estruturada.
"""
import sys
import os
import json
from pathlib import Path

try:
    import fitz
    from PIL import Image
except ImportError as e:
    raise ImportError(
        f"Dependência ausente: {e}. "
        f"Instale via: pip install -r requirements.txt"
    ) from e


def _open_pdf(path):
    """Abre PDF tolerando paths com chars Unicode problemáticos no Windows."""
    try:
        return fitz.open(path)
    except Exception:
        with open(path, "rb") as f:
            return fitz.open(stream=f.read(), filetype="pdf")


def render_pagina_rotacionada(pdf_path: str, pag_num: int, output_path: str,
                               zoom: float = 2.5, rotation: int = 270) -> str:
    """Renderiza página em PNG já rotacionada."""
    with _open_pdf(pdf_path) as doc:
        page = doc[pag_num - 1]
        mat = fitz.Matrix(zoom, zoom).prerotate(rotation)
        pix = page.get_pixmap(matrix=mat)
        pix.save(output_path)
    return output_path


def crop_bloco_poderes(png_path: str, output_path: str,
                       y_inicio: float = 0.30, y_fim: float = 0.80,
                       max_dim: int = 1700) -> tuple:
    """
    Recorta a região central onde costuma estar o bloco PODERES ESPECIAIS
    da procuração (texto que diz 'em face do BANCO X, referente ao Contrato nº NNN').

    Faixa ampla 0.30-0.80 cobre layouts variados:
        - Procurações compactas com 2 outorgantes (PODERES ESPECIAIS em y~0.40)
        - Procurações simples (PODERES ESPECIAIS em y~0.60)

    Reduz para max_dim no maior lado para caber no limite do Read tool (~1800px).
    Retorna (width, height) do crop final.
    """
    img = Image.open(png_path)
    w, h = img.size
    cropped = img.crop((0, int(y_inicio * h), w, int(y_fim * h)))
    cw, ch = cropped.size
    if max(cw, ch) > max_dim:
        s = max_dim / max(cw, ch)
        cropped = cropped.resize((int(cw * s), int(ch * s)), Image.LANCZOS)
    cropped.save(output_path, "PNG", optimize=True)
    return cropped.size


def detectar_rotacao_correta(pdf_path: str, pag_num: int = 1) -> int:
    """
    Detecta automaticamente qual rotação deixa o texto de pé.
    Para procurações escaneadas em paisagem, geralmente é 270.
    """
    with _open_pdf(pdf_path) as doc:
        page = doc[pag_num - 1]
        rect = page.mediabox
        # mediabox em paisagem = texto provavelmente rotacionado
        if rect.width > rect.height * 1.2:
            return 270
        return 0


def preparar_crops(pdf_path: str, output_dir: str) -> dict:
    """
    Para cada página do PDF, gera um crop do bloco PODERES ESPECIAIS.
    Salva manifesto.json com lista de paths.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    rotacao = detectar_rotacao_correta(pdf_path)
    manifesto = {
        "pdf_origem": pdf_path,
        "rotacao_aplicada": rotacao,
        "paginas": []
    }
    with _open_pdf(pdf_path) as doc:
        total = len(doc)

    for i in range(1, total + 1):
        png_full = os.path.join(output_dir, f"_full_{i:02d}.png")
        png_crop = os.path.join(output_dir, f"crop_pag_{i:02d}.png")
        render_pagina_rotacionada(pdf_path, i, png_full, rotation=rotacao)
        size = crop_bloco_poderes(png_full, png_crop)
        os.remove(png_full)
        manifesto["paginas"].append({
            "pagina": i,
            "crop_path": png_crop,
            "crop_size": size,
        })

    with open(os.path.join(output_dir, "manifesto.json"), "w", encoding="utf-8") as f:
        json.dump(manifesto, f, indent=2, ensure_ascii=False)
    return manifesto


def crop_linha_contrato(pdf_path: str, pag_num: int, output_path: str,
                        zoom: float = 4.0, rotation: int = 270,
                        y_ini: float = 0.46, y_fim: float = 0.55) -> str:
    """
    Crop super-zoom da linha que contém 'em face do BANCO X, Contrato nº NNN'.
    Usado para revalidação de números duvidosos.
    """
    full = output_path.replace(".png", "_full.png")
    render_pagina_rotacionada(pdf_path, pag_num, full, zoom=zoom, rotation=rotation)
    img = Image.open(full)
    w, h = img.size
    cropped = img.crop((int(0.05 * w), int(y_ini * h), int(0.95 * w), int(y_fim * h)))
    target = 1500
    cw, ch = cropped.size
    if max(cw, ch) > target:
        s = target / max(cw, ch)
        cropped = cropped.resize((int(cw * s), int(ch * s)), Image.LANCZOS)
    cropped.save(output_path, "PNG", optimize=True)
    os.remove(full)
    return output_path


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    pdf = sys.argv[1]
    out = sys.argv[2]
    manifesto = preparar_crops(pdf, out)
    print(f"OK: {len(manifesto['paginas'])} crops em {out}/")
    print(f"Rotação: {manifesto['rotacao_aplicada']}°")


if __name__ == "__main__":
    main()
