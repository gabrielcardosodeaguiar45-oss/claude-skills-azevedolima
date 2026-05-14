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


def score_kit_assinado(input_path: str) -> dict:
    """Calcula score 0-100 de probabilidade de ser KIT ASSINADO (escaneado
    via app de scanner) vs KIT MODELO (template em branco gerado em editor).

    Sinais positivos (kit assinado):
      - producer/creator de app de scanner (CamScanner, Adobe Scan, etc.)
      - text-layer ausente ou muito pequeno
      - imagens raster presentes na primeira página
      - tamanho > 3 MB
      - nome do arquivo começa com "processo"

    Sinais negativos (kit modelo/template em branco):
      - producer/creator de editor (Word, LibreOffice, OpenOffice)
      - text-layer abundante + zero imagens raster
      - tamanho < 1 MB
      - nome começa só com "KIT" sem indicador de assinatura

    Caso paradigma: Guilherme de Oliveira Lacerda (2026-05-14) — havia
    "KIT GUILHERME DE OLIVEIRA LACERDA.pdf" (Word, 0.33MB, text-layer)
    e "Processo Guilherme de Oliveira Lacerda.pdf" (CamScanner, 12.69MB,
    escaneado). A skill estava pegando o KIT em branco em vez do Processo.

    Retorna:
      {
        'score': int (-100 a 100; >=50 = ASSINADO, <=-30 = MODELO, entre = AMBIGUO),
        'classificacao': 'ASSINADO' | 'MODELO' | 'AMBIGUO',
        'sinais': dict com os sinais individuais detectados (para debug),
      }
    """
    from pathlib import Path
    nome = Path(input_path).name
    nome_lower = nome.lower()
    sinais = {}
    score = 0

    try:
        tamanho_bytes = os.path.getsize(input_path)
    except OSError:
        tamanho_bytes = 0
    tamanho_mb = tamanho_bytes / 1024 / 1024
    sinais['tamanho_mb'] = round(tamanho_mb, 2)

    # Sinal 1 — producer/creator do PDF (mais forte)
    producer = ''
    creator = ''
    n_imagens_p1 = 0
    text_chars_p1 = 0
    paginas = 0
    try:
        with open_pdf(input_path) as doc:
            paginas = len(doc)
            meta = doc.metadata or {}
            producer = (meta.get('producer') or '').lower()
            creator = (meta.get('creator') or '').lower()
            if paginas > 0:
                p1 = doc[0]
                text_chars_p1 = len((p1.get_text() or '').strip())
                n_imagens_p1 = len(p1.get_images())
    except Exception as e:
        sinais['erro'] = str(e)

    sinais['producer'] = producer
    sinais['creator'] = creator
    sinais['paginas'] = paginas
    sinais['text_chars_p1'] = text_chars_p1
    sinais['n_imagens_p1'] = n_imagens_p1

    SCANNERS = ('intsig', 'camscanner', 'adobe scan', 'scannerpro',
                'tinyscanner', 'genius scan', 'office lens', 'simple scan',
                'docscanner', 'tap scanner')
    EDITORES = ('microsoft® word', 'microsoft word', 'libreoffice',
                'openoffice', 'wps writer', 'pages', 'google docs',
                'foxit phantompdf', 'acrobat pro dc')

    if any(s in producer or s in creator for s in SCANNERS):
        score += 50
        sinais['flag_scanner'] = True
    if any(e in producer or e in creator for e in EDITORES):
        score -= 50
        sinais['flag_editor'] = True

    # Sinal 2 — text-layer
    if text_chars_p1 < 100:
        score += 30
        sinais['flag_sem_text_layer'] = True
    elif text_chars_p1 > 500:
        score -= 30
        sinais['flag_text_layer_abundante'] = True

    # Sinal 3 — imagens raster
    if n_imagens_p1 >= 1:
        score += 20
        sinais['flag_tem_raster'] = True
    elif n_imagens_p1 == 0 and text_chars_p1 > 500:
        score -= 20
        sinais['flag_sem_raster_com_texto'] = True

    # Sinal 4 — tamanho
    if tamanho_mb > 3:
        score += 15
        sinais['flag_grande'] = True
    elif tamanho_mb < 1:
        score -= 15
        sinais['flag_pequeno'] = True

    # Sinal 5 — nome (fraco)
    if nome_lower.startswith('processo'):
        score += 10
        sinais['flag_nome_processo'] = True
    elif nome_lower.startswith('kit') and 'assinad' not in nome_lower:
        score -= 10
        sinais['flag_nome_kit_em_branco'] = True

    score = max(-100, min(100, score))

    if score >= 50:
        classificacao = 'ASSINADO'
    elif score <= -30:
        classificacao = 'MODELO'
    else:
        classificacao = 'AMBIGUO'

    return {
        'score': score,
        'classificacao': classificacao,
        'sinais': sinais,
    }


def escolher_kit_assinado(paths: list) -> dict:
    """Recebe múltiplos PDFs candidatos a "kit do cliente" e devolve qual usar.

    Aplica score_kit_assinado em cada um e seleciona o de maior score.
    Em caso de empate, prefere o mais recente por mtime.

    Não exclui nem move nenhum arquivo — apenas decide qual usar.

    Retorna:
      {
        'escolhido': str (path do kit assinado) | None,
        'descartados': list[str] (paths dos templates / outros),
        'detalhes': list[dict] com score+sinais de cada candidato (ordenado),
      }
    """
    if not paths:
        return {'escolhido': None, 'descartados': [], 'detalhes': []}

    detalhes = []
    for p in paths:
        info = score_kit_assinado(p)
        info['path'] = p
        try:
            info['mtime'] = os.path.getmtime(p)
        except OSError:
            info['mtime'] = 0
        detalhes.append(info)

    # Ordena por score desc, depois mtime desc (mais recente primeiro)
    detalhes.sort(key=lambda x: (x['score'], x['mtime']), reverse=True)

    escolhido = detalhes[0]['path'] if detalhes[0]['score'] > 0 else None
    descartados = [d['path'] for d in detalhes[1:]]

    return {
        'escolhido': escolhido,
        'descartados': descartados,
        'detalhes': detalhes,
    }


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
