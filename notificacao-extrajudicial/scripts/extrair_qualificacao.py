"""
Extrator de qualificação do cliente a partir de PDF da procuração.

Estratégia:
1. Tentar text-layer com pymupdf (fitz)
2. Se vazio, fazer OCR com easyOCR
3. Parsear via regex: nome, CPF, RG, RG_orgao, endereço, profissão,
   estado_civil, nacionalidade, gênero

Atenção: nem todas as procurações têm todos os campos. Os ausentes ficam
como string vazia para o usuário preencher manualmente.
"""
import re
import io
import os
from typing import Optional

import fitz  # pymupdf

# Lazy load do easyOCR (carrega só quando necessário)
_OCR_READER = None


def _get_ocr_reader():
    global _OCR_READER
    if _OCR_READER is None:
        import easyocr
        _OCR_READER = easyocr.Reader(['pt'], gpu=False, verbose=False)
    return _OCR_READER


def _extrair_texto_imagem(img_path: str) -> str:
    """OCR de uma imagem PNG/JPG já rotacionada/recortada."""
    if not os.path.exists(img_path):
        return ''
    reader = _get_ocr_reader()
    print(f'    [OCR] Lendo imagem {img_path}...')
    with open(img_path, 'rb') as f:
        img_bytes = f.read()
    result = reader.readtext(img_bytes, detail=0, paragraph=True)
    return '\n'.join(result).strip()


def _extrair_texto_pdf(pdf_path: str, max_pages: int = 5) -> str:
    """Extrai texto de PDF. Tenta text-layer; se vazio, OCR."""
    # Suporte a PNG/JPG (caso seja imagem direta)
    if pdf_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        return _extrair_texto_imagem(pdf_path)
    # 1. Text-layer
    try:
        with open(pdf_path, 'rb') as f:
            data = f.read()
        doc = fitz.open(stream=data, filetype='pdf')
    except Exception:
        return ''

    textos = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        textos.append(page.get_text())
    text_layer = '\n'.join(textos).strip()
    doc.close()

    if len(text_layer) > 100:
        return text_layer

    # 2. OCR fallback
    print(f'    [OCR] Text-layer vazio, ocrizando {pdf_path}...')
    reader = _get_ocr_reader()
    doc = fitz.open(stream=data, filetype='pdf')
    textos = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        # Detecta se a página está em landscape (procurações geralmente
        # vêm escaneadas viradas) — se sim, aplica rotação 270°.
        rect = page.rect
        rotacao = 0
        if rect.width > rect.height * 1.2:
            rotacao = 270  # gira anti-horário
            page.set_rotation(rotacao)
        # Renderiza página em imagem PNG (DPI maior melhora OCR)
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes('png')
        # OCR
        result = reader.readtext(img_bytes, detail=0, paragraph=True)
        textos.append('\n'.join(result))
        # Volta rotação para próxima iteração não acumular
        if rotacao:
            page.set_rotation(0)
    doc.close()
    return '\n'.join(textos).strip()


def parsear_qualificacao(texto: str) -> dict:
    """
    Aplica regex para extrair campos da procuração. Retorna dict com:
        nome, cpf, rg, rg_orgao, profissao, estado_civil, nacionalidade,
        logradouro, bairro, municipio, uf, cep, genero

    Restringe busca ao BLOCO OUTORGANTE (antes de OUTORGADO/OUTORGADOS)
    para evitar pegar dados dos advogados.
    """
    qual = {
        'nome': '',
        'cpf': '',
        'rg': '',
        'rg_orgao': '',
        'profissao': '',
        'estado_civil': '',
        'nacionalidade': '',
        'logradouro': '',
        'bairro': '',
        'municipio': '',
        'uf': '',
        'cep': '',
        'genero': '',  # 'M' ou 'F'
    }

    # Normalizar texto (remover múltiplos espaços/quebras)
    txt_full = re.sub(r'\s+', ' ', texto)

    # Isolar bloco OUTORGANTE (antes do primeiro OUTORGADO/OUTORGADOS)
    m_outorgado = re.search(r'OUTORGAD[OA]S?\s*[:.]', txt_full, re.IGNORECASE)
    if m_outorgado:
        bloco = txt_full[:m_outorgado.start()]
    else:
        bloco = txt_full[:2000]  # fallback: primeiros 2000 chars
    txt = bloco

    # CPF — padrão XXX.XXX.XXX-XX (com ou sem pontuação)
    m = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', txt)
    if m:
        qual['cpf'] = m.group(1)

    # RG — busca específica antes do CPF (evita confundir com CPF que vem
    # com "RG/CPF" no OCR). Tenta padrões clássicos.
    # Padrão 1: "RG nº 12.345.678" (com pontuação)
    m = re.search(r'RG[/\s]*(?:n[º°]?\s*)?[:\s]*(\d{1,3}\.\d{3}\.\d{3}[-\.]?\d?)', txt, re.IGNORECASE)
    if m and m.group(1) != qual['cpf']:
        qual['rg'] = m.group(1)

    # Órgão expedidor — SSP/UF, SESP/UF, etc.
    m = re.search(r'((?:SSP|SESP|DETRAN|IFP|PC|IGP|SDS|PMRJ|MAER|PMERJ|DGPC|IIRGD|GEJSPC|SJTC)[/\-\s]?[A-Z]{2})', txt)
    if m:
        qual['rg_orgao'] = m.group(1).replace(' ', '/').replace('-', '/')

    # CEP
    m = re.search(r'CEP[:\s]*(\d{2}\.?\d{3}[-\s]?\d{3})', txt, re.IGNORECASE)
    if m:
        qual['cep'] = m.group(1).replace(' ', '').replace('.', '')
        # Reformata para XXXXX-XXX
        cep = qual['cep'].replace('-', '')
        if len(cep) == 8:
            qual['cep'] = cep[:5] + '-' + cep[5:]

    # Estado civil — tolerante a OCR errors típicos (vlúva, viuva, casadc, etc.)
    estado_civil_patterns = [
        ('viúva', r'\bv[il][úu]va\b'),
        ('viúvo', r'\bv[il][úu]vo\b'),
        ('casada', r'\bcasada\b'),
        ('casado', r'\bcasado\b'),
        ('solteira', r'\bsolteira\b'),
        ('solteiro', r'\bsolteiro\b'),
        ('divorciada', r'\bdivorciada\b'),
        ('divorciado', r'\bdivorciado\b'),
        ('separada', r'\bseparada\b'),
        ('separado', r'\bseparado\b'),
    ]
    for ec_canon, ec_pat in estado_civil_patterns:
        if re.search(ec_pat, txt, re.IGNORECASE):
            qual['estado_civil'] = ec_canon
            break

    # Nacionalidade
    if re.search(r'\bbrasileira\b', txt, re.IGNORECASE):
        qual['nacionalidade'] = 'brasileira'
        qual['genero'] = 'F'
    elif re.search(r'\bbrasileiro\b', txt, re.IGNORECASE):
        qual['nacionalidade'] = 'brasileiro'
        qual['genero'] = 'M'

    # Profissão (heurística — palavras comuns)
    for prof in [
        'aposentada', 'aposentado',
        'pensionista',
        'do lar',
        'lavradora', 'lavrador',
        'agricultora', 'agricultor',
        'pescadora', 'pescador',
        'doméstica', 'doméstico',
        'beneficiária', 'beneficiário',
        'autônoma', 'autônomo',
    ]:
        if re.search(r'\b' + re.escape(prof) + r'\b', txt, re.IGNORECASE):
            qual['profissao'] = prof.lower()
            break

    # Endereço — várias formas possíveis após "residente e domiciliad[ao]"
    m = re.search(
        r'residente e domiciliad[oa]\s+(?:[àaeon]+|\s)+\s*(.+?)(?:CEP|$)',
        txt, re.IGNORECASE)
    if m:
        end_str = m.group(1).strip().rstrip(',').strip()
        # Tenta extrair "<logradouro>, <bairro>?, <municipio>[-/]<UF>"
        # Pattern: divide por vírgulas, último elemento provável é "municipio-UF" ou "municipio/UF"
        partes = [p.strip() for p in end_str.split(',') if p.strip()]
        if partes:
            # Última parte: municipio-UF
            ultima = partes[-1]
            m_uf = re.search(r'(.+?)[-/](AL|AM|BA|CE|DF|ES|GO|MA|MG|MS|MT|PA|PB|PE|PI|PR|RJ|RN|RO|RR|RS|SC|SE|SP|TO)\b', ultima)
            if m_uf:
                # Capitalize: "maribondo" → "Maribondo"
                mun = m_uf.group(1).strip().rstrip(',').strip()
                qual['municipio'] = ' '.join(w.capitalize() for w in mun.split())
                qual['uf'] = m_uf.group(2)
                partes = partes[:-1]
            # Filtra partes que são apenas número (S/Nº, 123, etc.) — esses vão pro logradouro
            def _eh_num(s):
                s_clean = s.replace('.', '').replace('º', '').replace('ª', '').strip().lower()
                return s_clean in ('s/n', 'sn') or s_clean.startswith('n') and s_clean[1:].strip().isdigit() or s_clean.replace('-', '').isdigit()

            partes_nao_num = [p for p in partes if not _eh_num(p)]
            partes_num = [p for p in partes if _eh_num(p)]
            # Bairro = última parte não-numérica (se houver mais de uma)
            if len(partes_nao_num) >= 2:
                qual['bairro'] = partes_nao_num[-1].strip()
                logr_partes = partes_nao_num[:-1] + partes_num
                qual['logradouro'] = ', '.join(logr_partes).strip()
            elif partes_nao_num:
                qual['logradouro'] = ', '.join(partes_nao_num + partes_num).strip()

    # Inferir gênero do estado civil/profissão se não pegou da nacionalidade
    if not qual['genero']:
        if qual['estado_civil'].endswith('a') or qual['profissao'].endswith('a'):
            qual['genero'] = 'F'
        elif qual['estado_civil'].endswith('o') or qual['profissao'].endswith('o'):
            qual['genero'] = 'M'

    return qual


def extrair_qualificacao(pdf_path: str, max_pages: int = 5) -> dict:
    """Lê PDF da procuração e extrai qualificação. Retorna dict."""
    if not os.path.exists(pdf_path):
        return {}
    texto = _extrair_texto_pdf(pdf_path, max_pages=max_pages)
    if not texto:
        return {}
    qual = parsear_qualificacao(texto)
    qual['_texto_extraido'] = texto[:1000]  # Primeiras 1000 chars para debug
    return qual


if __name__ == '__main__':
    import sys, json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if len(sys.argv) < 2:
        print('Uso: python extrair_qualificacao.py <path_procuracao.pdf>')
        sys.exit(1)
    qual = extrair_qualificacao(sys.argv[1])
    print(json.dumps(qual, indent=2, ensure_ascii=False))
