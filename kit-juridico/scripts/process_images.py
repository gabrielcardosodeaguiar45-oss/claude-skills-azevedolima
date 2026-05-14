"""
Processamento de imagens de documentos: detecta bordas do documento, recorta
fundo, converte para PDF.

Versão modernizada com OpenCV (mais robusto que a versão legacy baseada
apenas em PIL.FIND_EDGES). Cai para PIL se OpenCV não estiver instalado.

Uso:
    python process_images.py <input_image> <output_pdf>
    python process_images.py <input_dir> <output_dir> --batch
"""
import sys
import os
from pathlib import Path

try:
    from PIL import Image, ImageOps, ImageFilter
    import img2pdf
except ImportError as e:
    raise ImportError(
        f"Dependência ausente: {e}. "
        f"Instale via: pip install -r requirements.txt"
    ) from e

try:
    import cv2
    import numpy as np
    OPENCV = True
except ImportError:
    OPENCV = False


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".img", ".bmp", ".tiff", ".tif", ".webp"}


def detect_bounds_opencv(img_pil):
    """
    Detecta bordas do documento usando OpenCV: blur + canny + contorno.
    Retorna (left, top, right, bottom).
    """
    np_img = np.array(img_pil.convert("RGB"))
    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Dilatar pra unir bordas pontilhadas
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return _bounds_full_image(img_pil)

    # Maior contorno por área
    biggest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(biggest)

    img_w, img_h = img_pil.size
    # Sanity check: contorno deve cobrir pelo menos 30% da imagem
    if w * h < img_w * img_h * 0.3:
        return _bounds_full_image(img_pil)

    margin = int(min(img_w, img_h) * 0.01)
    left = max(0, x - margin)
    top = max(0, y - margin)
    right = min(img_w, x + w + margin)
    bottom = min(img_h, y + h + margin)
    return (left, top, right, bottom)


def detect_bounds_pil(img_pil):
    """Fallback PIL (heurística antiga)."""
    gray = img_pil.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    width, height = gray.size

    pixels = edges.load()
    threshold = 30
    margin_x = int(width * 0.02)
    margin_y = int(height * 0.02)

    top = 0
    for y in range(height):
        for x in range(0, width, 3):
            if pixels[x, y] > threshold:
                top = max(0, y - margin_y)
                break
        else:
            continue
        break

    bottom = height - 1
    for y in range(height - 1, -1, -1):
        for x in range(0, width, 3):
            if pixels[x, y] > threshold:
                bottom = min(height - 1, y + margin_y)
                break
        else:
            continue
        break

    left = 0
    for x in range(width):
        for y in range(0, height, 3):
            if pixels[x, y] > threshold:
                left = max(0, x - margin_x)
                break
        else:
            continue
        break

    right = width - 1
    for x in range(width - 1, -1, -1):
        for y in range(0, height, 3):
            if pixels[x, y] > threshold:
                right = min(width - 1, x + margin_x)
                break
        else:
            continue
        break

    # Sanity: se recorte muito agressivo, voltar pra imagem completa
    if right - left < width * 0.2 or bottom - top < height * 0.2:
        return _bounds_full_image(img_pil)
    return (left, top, right, bottom)


def _bounds_full_image(img_pil):
    w, h = img_pil.size
    margin = int(min(w, h) * 0.02)
    return (margin, margin, w - margin, h - margin)


def crop_and_save_as_pdf(input_path: str, output_pdf_path: str) -> str:
    img = Image.open(input_path)
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    if OPENCV:
        bounds = detect_bounds_opencv(img)
    else:
        bounds = detect_bounds_pil(img)

    cropped = img.crop(bounds)
    temp = output_pdf_path + ".tmp.jpg"
    cropped.save(temp, "JPEG", quality=95)
    with open(output_pdf_path, "wb") as f:
        f.write(img2pdf.convert(temp))
    os.remove(temp)
    return output_pdf_path


def process_batch(input_dir: str, output_dir: str) -> list[str]:
    indir = Path(input_dir)
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_files = []
    for f in sorted(indir.iterdir()):
        if f.suffix.lower() in IMAGE_EXTS:
            outp = outdir / (f.stem + ".pdf")
            try:
                crop_and_save_as_pdf(str(f), str(outp))
                out_files.append(str(outp))
                print(f"OK: {f.name} -> {outp.name}")
            except Exception as e:
                print(f"ERRO: {f.name} -> {e}")
    return out_files


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    inp, outp = sys.argv[1], sys.argv[2]
    if "--batch" in sys.argv:
        results = process_batch(inp, outp)
        print(f"Total processadas: {len(results)}")
    else:
        crop_and_save_as_pdf(inp, outp)
        print(f"OK: {outp}")


if __name__ == "__main__":
    main()
