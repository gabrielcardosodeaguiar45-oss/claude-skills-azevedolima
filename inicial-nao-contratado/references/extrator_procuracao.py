"""Extrator de números de contrato a partir do CONTEÚDO da procuração (PDF).

REGRA OPERACIONAL OBRIGATÓRIA (gravada na SKILL.md §9-quater):
A procuração é a ÚNICA fonte autoritativa do que o cliente nos autorizou
a impugnar. NUNCA assumir contratos sem confirmação na procuração:

  - Se o nome do arquivo da procuração tem o número (ex.:
    '2 - PROCURAÇÃO BANCO 0123506012709.pdf'), usar esse número.
  - Senão, ler o CONTEÚDO da procuração (text-layer ou OCR via easyocr)
    e extrair os números via regex.
  - Se mesmo assim ficar vazio, ABORTAR com alerta CRÍTICO (não cair em
    "pegar todos os contratos do banco").

Estratégia de leitura (em ordem de tentativa):
  1. text-layer via pymupdf (rápido — funciona em procurações digitais)
  2. EasyOCR renderizando a página em PNG (procurações escaneadas)

Padrão para extrair número de contrato consignado:
  - 12 a 15 dígitos seguidos
  - normalmente precedido por 'Contrato n°', 'Contrato nº', 'sob o nº', etc.
"""
import os, re, sys
from typing import List, Tuple, Optional
import fitz  # pymupdf

# Padrão dos números de contrato consignado (entre 10 e 16 dígitos seguidos)
PADRAO_CONTRATO_CONSIGNADO = re.compile(r'\b(\d{10,16})\b')

# Padrões mais específicos com "contrato" próximo (alta confiança)
PADRAO_CONTRATO_CONTEXTUAL = re.compile(
    r'(?:[Cc]ontrato\s*(?:n[°ºo]?|sob\s+(?:o\s+)?n[°ºo]?)?[:\s]*)([\d\.\-\s]{10,25})',
    re.MULTILINE
)


def _normalizar_numero(s: str) -> str:
    """Remove espaços, pontos, traços. '0123-506-012-709' → '0123506012709'."""
    return re.sub(r'[^\d]', '', s or '')


def _extrair_de_texto(texto: str) -> List[str]:
    """Aplica regex no texto e retorna lista de números (12-15 dígitos)."""
    candidatos = set()

    # 1. Padrão contextual (alta confiança)
    for m in PADRAO_CONTRATO_CONTEXTUAL.finditer(texto):
        n = _normalizar_numero(m.group(1))
        if 10 <= len(n) <= 16:
            candidatos.add(n)

    # 2. Padrão genérico (fallback) — só se nada veio do contextual
    if not candidatos:
        for m in PADRAO_CONTRATO_CONSIGNADO.finditer(texto):
            n = _normalizar_numero(m.group(1))
            # Filtrar CPFs (11 dígitos) e CNPJs (14 dígitos com formato típico)
            # Heurística: contratos consignados tipicamente têm 12-15 dígitos
            # e NÃO seguem o padrão de CPF/CNPJ formatados.
            if 12 <= len(n) <= 15:
                candidatos.add(n)

    return sorted(candidatos)


def _extrair_via_text_layer(pdf_path: str) -> Tuple[str, List[str]]:
    """Tenta extrair texto da camada do PDF (sem OCR).
    Retorna (texto_completo, numeros_encontrados).
    """
    doc = fitz.open(pdf_path)
    texto = '\n'.join(doc[i].get_text() for i in range(len(doc)))
    doc.close()
    if not texto.strip():
        return '', []
    return texto, _extrair_de_texto(texto)


def _extrair_via_easyocr(pdf_path: str, max_dim: int = 2400) -> Tuple[str, List[str]]:
    """Renderiza páginas do PDF em PNG e roda EasyOCR (pt). Retorna texto + nums.
    Resolução padrão = 2400px (melhor que 1800 para procurações escaneadas
    de baixa qualidade).
    """
    try:
        import easyocr
    except ImportError:
        return '', []

    reader = easyocr.Reader(['pt'], gpu=False, verbose=False)
    doc = fitz.open(pdf_path)
    textos = []
    for ip in range(len(doc)):
        page = doc[ip]
        w_pts, h_pts = page.rect.width, page.rect.height
        # Resolução agressiva: até 2400px
        zoom = min(300 / 72, max_dim / max(w_pts, h_pts))
        m = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=m)
        import tempfile
        fd, tmp_path = tempfile.mkstemp(suffix='.png', prefix='procuracao_')
        os.close(fd)
        pix.save(tmp_path)
        try:
            # Parâmetros otimizados para texto manuscrito/escaneado:
            # - text_threshold=0.5 (menor = pega texto fraco)
            # - low_text=0.3 (menor = pega caracteres pequenos)
            # - paragraph=False para preservar linhas separadas (números aparecem em linhas isoladas)
            blocos = reader.readtext(tmp_path, detail=0, paragraph=False,
                                       text_threshold=0.5, low_text=0.3)
            textos.append('\n'.join(blocos))
        finally:
            try: os.unlink(tmp_path)
            except OSError: pass
    doc.close()
    texto_completo = '\n'.join(textos)
    return texto_completo, _extrair_de_texto(texto_completo)


def extrair_numeros_contrato_da_procuracao(pdf_path: str,
                                              usar_easyocr: bool = True
                                              ) -> dict:
    """Extrai números de contrato a partir do conteúdo da procuração.

    Args:
        pdf_path: caminho do PDF da procuração.
        usar_easyocr: True para ativar fallback OCR quando text-layer está vazio.

    Returns:
        {
            'fonte': 'text-layer' | 'easyocr' | 'nome-do-arquivo' | 'vazio',
            'texto_amostra': str (primeiros 500 chars do que conseguiu ler),
            'numeros': [str] (lista única de números 12-15 dígitos),
            'arquivo': str (caminho)
        }
    """
    if not os.path.exists(pdf_path):
        return {'fonte': 'erro', 'texto_amostra': f'arquivo não existe: {pdf_path}',
                'numeros': [], 'arquivo': pdf_path}

    # Tentativa 1: text-layer
    try:
        texto, nums = _extrair_via_text_layer(pdf_path)
    except Exception as e:
        texto, nums = '', []
    if nums:
        return {'fonte': 'text-layer', 'texto_amostra': texto[:500],
                'numeros': nums, 'arquivo': pdf_path}

    # Tentativa 2: easyocr
    if usar_easyocr:
        try:
            texto, nums = _extrair_via_easyocr(pdf_path)
        except Exception as e:
            texto, nums = f'easyocr falhou: {e}', []
        if nums:
            return {'fonte': 'easyocr', 'texto_amostra': texto[:500],
                    'numeros': nums, 'arquivo': pdf_path}

    # Tentativa 3: nome do arquivo
    nome = os.path.basename(pdf_path)
    nums_nome = re.findall(r'\b(\d{10,16})\b', nome)
    nums_nome = [_normalizar_numero(n) for n in nums_nome
                  if 10 <= len(_normalizar_numero(n)) <= 16]
    if nums_nome:
        return {'fonte': 'nome-do-arquivo', 'texto_amostra': nome,
                'numeros': sorted(set(nums_nome)), 'arquivo': pdf_path}

    return {'fonte': 'vazio', 'texto_amostra': (texto or '')[:500],
            'numeros': [], 'arquivo': pdf_path}


def extrair_numeros_contrato_de_pasta(pasta_cliente: str,
                                         usar_easyocr: bool = True
                                         ) -> dict:
    """Para cada procuração da pasta, tenta extrair números de contrato.

    Returns:
        {
            'procuracoes': [{ 'arquivo': ..., 'fonte': ..., 'numeros': [...] }],
            'numeros_unicos': [str],
            'alertas': [str],
        }
    """
    procs = []
    for arq in sorted(os.listdir(pasta_cliente)):
        if 'procura' in arq.lower() and arq.lower().endswith('.pdf'):
            full = os.path.join(pasta_cliente, arq)
            res = extrair_numeros_contrato_da_procuracao(full, usar_easyocr=usar_easyocr)
            procs.append(res)

    todos = sorted({n for p in procs for n in p['numeros']})
    alertas = []
    for p in procs:
        if not p['numeros']:
            alertas.append(
                f'🚨 Procuração SEM número de contrato extraível: '
                f'{os.path.basename(p["arquivo"])} (fonte tentada: {p["fonte"]}). '
                f'Ler o PDF MANUALMENTE e passar `numeros_contrato_explicitos=[...]`.'
            )
        elif p['fonte'] == 'easyocr':
            alertas.append(
                f'ℹ️ Procuração {os.path.basename(p["arquivo"])} foi lida via OCR '
                f'(easyocr). Confirmar manualmente os números extraídos: {p["numeros"]}.'
            )

    return {'procuracoes': procs, 'numeros_unicos': todos, 'alertas': alertas}


if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    # Teste: Edmunda (procuração escaneada com 1 contrato no conteúdo)
    pasta = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\EDMUNDA LIMA DOS SANTOS'
    res = extrair_numeros_contrato_de_pasta(pasta)
    print('\n=== EDMUNDA ===')
    for p in res['procuracoes']:
        print(f'  {os.path.basename(p["arquivo"])}: fonte={p["fonte"]}, numeros={p["numeros"]}')
        print(f'    amostra: {p["texto_amostra"][:200]!r}')
    print(f'\nÚnicos: {res["numeros_unicos"]}')
    for a in res['alertas']:
        print(f'  {a}')
