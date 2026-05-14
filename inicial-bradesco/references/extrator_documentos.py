"""
Extrator de documentos PDF para a skill inicial-bradesco.

REGRA CRÍTICA: a renda mensal usada na inicial vem SEMPRE do extrato bancário real
(função `extrair_renda_real`). NUNCA hardcode. Se não houver crédito identificável,
retornar None e a skill alerta como pendência.
"""
import os, re, fitz
from datetime import datetime


# ============================================================
# Regex compartilhados
# ============================================================
RE_DATA = re.compile(r'^\d{2}/\d{2}/\d{4}$')
RE_VALOR = re.compile(r'^\d{1,3}(?:\.\d{3})*,\d{2}$')


# ============================================================
# Leitor robusto de PDF (text-layer com fallback OCR)
# ============================================================
# Cache do texto por PDF (path → texto). Evita OCR múltiplo no mesmo arquivo
# quando várias funções (renda + tabela + lançamentos) leem o mesmo extrato.
_CACHE_TEXTO_PDF: dict[str, str] = {}
_OCR_READER = None


def _get_ocr_reader():
    """Lazy load do easyOCR. Carregamento custa ~3s; vale a pena ser preguiçoso."""
    global _OCR_READER
    if _OCR_READER is None:
        try:
            import easyocr
        except ImportError:
            os.system('pip install easyocr --break-system-packages -q')
            import easyocr
        _OCR_READER = easyocr.Reader(['pt'], gpu=False, verbose=False)
    return _OCR_READER


def _pagina_tem_texto(page, threshold: int = 50) -> bool:
    """Heurística: página tem text-layer útil se get_text() retorna >threshold chars."""
    return len(page.get_text().strip()) > threshold


def _ler_texto_pdf(pdf_path: str, force_ocr: bool = False,
                   max_pages: int | None = None) -> str:
    """Lê texto de um PDF de forma robusta:
    1. Tenta text-layer (rápido)
    2. Se a maioria das páginas não tem texto, faz OCR com easyOCR
    3. Aplica rotação automática quando página está em landscape

    Cache em memória para evitar reprocessamento do mesmo arquivo.

    Args:
        pdf_path: caminho do PDF
        force_ocr: força OCR mesmo se houver text-layer (para auditoria)
        max_pages: limita N primeiras páginas (None = todas)

    Returns: texto concatenado de todas as páginas (separado por '\n').
    """
    if not os.path.exists(pdf_path):
        return ''
    cache_key = f'{pdf_path}::ocr={force_ocr}::max={max_pages}'
    if cache_key in _CACHE_TEXTO_PDF:
        return _CACHE_TEXTO_PDF[cache_key]

    try:
        with open(pdf_path, 'rb') as f:
            data = f.read()
        doc = fitz.open(stream=data, filetype='pdf')
    except Exception:
        return ''

    paginas_texto: list[str] = []
    paginas_processadas = 0
    paginas_com_texto = 0

    for i, page in enumerate(doc):
        if max_pages and i >= max_pages:
            break
        paginas_processadas += 1

        # Tentativa 1: text-layer
        if not force_ocr and _pagina_tem_texto(page):
            paginas_com_texto += 1
            paginas_texto.append(page.get_text())
            continue

        # Tentativa 2: OCR
        # Aplica rotação se a página vem em landscape (largura > altura * 1.2)
        rect = page.rect
        rotacao = 0
        if rect.width > rect.height * 1.2:
            rotacao = 270
            page.set_rotation(rotacao)
        try:
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes('png')
            reader = _get_ocr_reader()
            # paragraph=True agrupa linhas próximas (melhora extração de tabelas)
            result = reader.readtext(img_bytes, detail=0, paragraph=True)
            paginas_texto.append('\n'.join(result))
        except Exception as e:
            paginas_texto.append(f'[OCR_FALHOU: {e}]')
        finally:
            if rotacao:
                page.set_rotation(0)

    doc.close()
    texto = '\n'.join(paginas_texto)
    _CACHE_TEXTO_PDF[cache_key] = texto
    return texto


def detectar_pdf_imagem(pdf_path: str, threshold_paginas_pct: float = 0.5) -> bool:
    """Retorna True se a maioria das páginas do PDF não tem text-layer
    (ou seja, o PDF é provavelmente um scan/imagem).

    Útil para alertar quando o extrato vai precisar de OCR (mais lento).
    """
    if not os.path.exists(pdf_path):
        return False
    try:
        with open(pdf_path, 'rb') as f:
            data = f.read()
        doc = fitz.open(stream=data, filetype='pdf')
    except Exception:
        return False
    n_total = doc.page_count
    if n_total == 0:
        doc.close()
        return False
    n_imagem = sum(1 for p in doc if not _pagina_tem_texto(p))
    doc.close()
    return (n_imagem / n_total) >= threshold_paginas_pct


# ============================================================
# Rubricas do extrato Bradesco
# ============================================================
RUBRICAS_RENDA = [
    'INSS',
    'CREDITO DE SALARIO',
    'TRANSF SALDO C/SAL',           # típico de servidor (conta-salário)
    'BENEFICIO PREVIDENCIARIO',
    'PAGTO BENEFICIO INSS',
    'APOSENTADORIA',
    'PENSAO',
    'PREFEITURA MUNICIPAL',          # alguns servidores recebem direto
    'GOVERNO',
]


# ============================================================
# 1. EXTRAÇÃO DE RENDA REAL DO EXTRATO (regra crítica)
# ============================================================
def extrair_renda_real(extrato_path, valor_minimo=500.0):
    """REGRA CRÍTICA: extrai a renda mensal mais recente do extrato Bradesco.

    Procura créditos com rubricas conhecidas (INSS, salário, etc.) e devolve
    o lançamento mais recente. NUNCA usar fallback hardcoded — se não achar,
    retorna None e a skill marca como pendência manual.

    Args:
        extrato_path: caminho do PDF do extrato
        valor_minimo: filtra créditos abaixo desse valor (R$)

    Returns:
        dict com keys {'data_str', 'data_dt', 'rubrica', 'valor'} ou None
    """
    texto = _ler_texto_pdf(extrato_path)
    if not texto:
        return None
    linhas = [ln.rstrip() for ln in texto.split('\n')]

    eventos = []
    for i, ln in enumerate(linhas):
        upper = ln.upper().strip()
        for rubrica in RUBRICAS_RENDA:
            if upper == rubrica or upper.startswith(rubrica):
                data = None
                for j in range(i-1, max(-1, i-15), -1):
                    if RE_DATA.match(linhas[j].strip()):
                        data = linhas[j].strip()
                        break
                valor = None
                for j in range(i+1, min(len(linhas), i+10)):
                    if RE_VALOR.match(linhas[j].strip()):
                        valor = linhas[j].strip()
                        break
                if data and valor:
                    try:
                        d_dt = datetime.strptime(data, '%d/%m/%Y')
                        v = float(valor.replace('.', '').replace(',', '.'))
                        if v >= valor_minimo:
                            eventos.append({
                                'data_str': data,
                                'data_dt': d_dt,
                                'rubrica': upper,
                                'valor': v,
                            })
                    except ValueError:
                        pass
                break

    if not eventos:
        return None
    eventos.sort(key=lambda e: e['data_dt'])
    return eventos[-1]  # mais recente


# ============================================================
# 2. EXTRAIR CONTA + AGÊNCIA DA 1ª PÁGINA DO EXTRATO
# ============================================================
def extrair_conta_agencia(extrato_path):
    """Lê 1ª página do extrato Bradesco e extrai conta/agência.

    Returns: {'conta': str, 'agencia': str} ou {} se não encontrar.
    """
    # Usa leitor robusto (text-layer + OCR) com cache; lê só primeiras páginas
    texto = _ler_texto_pdf(extrato_path, max_pages=5)
    if not texto:
        return {}

    m_a = re.search(r'Ag[êe]ncia[:\s]*(\d{4})', texto, re.IGNORECASE)
    m_c = re.search(r'Conta[:\s]*([\d-]+)', texto, re.IGNORECASE)
    out = {}
    if m_a:
        out['agencia'] = m_a.group(1)
    if m_c:
        out['conta'] = m_c.group(1)
    return out


# ============================================================
# 3. EXTRAIR LANÇAMENTOS DA TABELA (PDF 7)
# ============================================================
def parsear_tabela_descontos(tabela_path, filtro_rubrica=None):
    """Parseia tabela 7 - TABELA *.pdf em lista de descontos.

    Args:
        tabela_path: caminho do PDF
        filtro_rubrica: se fornecido, filtra apenas linhas que contêm essa string
                        (case-insensitive). Útil para isolar uma tese
                        quando a tabela tem múltiplas (ex.: ASPECIR vs MBM).

    Returns: list de dicts com {data, descricao, valor (float)}

    Robusto: detecta PDF imagem e aplica OCR automaticamente.
    """
    texto = _ler_texto_pdf(tabela_path)
    if not texto:
        return []
    linhas = [ln.strip() for ln in texto.split('\n') if ln.strip()]

    descontos = []
    i = 0
    while i < len(linhas):
        m = re.match(r'^(\d{2}/\d{2}/\d{4})\s+(.+)', linhas[i])
        if m:
            data = m.group(1)
            descricao = m.group(2).strip()
            if i + 1 < len(linhas):
                v = linhas[i+1].replace('R$', '').replace(',', '.').strip()
                try:
                    valor = float(v)
                    if filtro_rubrica is None or filtro_rubrica.lower() in descricao.lower():
                        descontos.append({
                            'data': data,
                            'descricao': descricao,
                            'valor': valor,
                        })
                    i += 2
                    continue
                except ValueError:
                    pass
        i += 1
    return descontos


def parsear_lancamentos_extrato(extrato_path, filtro_rubrica):
    """Parseia o EXTRATO bancário direto procurando por uma rubrica específica.
    Útil quando a tabela não foi feita ou faltam lançamentos.

    Args:
        extrato_path: caminho do PDF do extrato
        filtro_rubrica: string a procurar (ex.: 'APLIC.INVEST FACIL')

    Returns: list de dicts {data, valor (float)}

    Robusto: detecta PDF imagem e aplica OCR automaticamente.
    """
    texto = _ler_texto_pdf(extrato_path)
    if not texto:
        return []
    linhas = [ln.rstrip() for ln in texto.split('\n')]

    eventos = []
    filtro_upper = filtro_rubrica.upper()
    for i, ln in enumerate(linhas):
        if filtro_upper in ln.upper():
            # Confirma que é movimento (proxima linha eh DOCTO)
            nxt = linhas[i+1].strip() if i+1 < len(linhas) else ''
            if not re.match(r'^\d{4,8}$', nxt):
                continue
            data = None
            for j in range(i-1, max(-1, i-15), -1):
                if RE_DATA.match(linhas[j].strip()):
                    data = linhas[j].strip()
                    break
            valor = None
            for j in range(i+1, min(len(linhas), i+10)):
                if RE_VALOR.match(linhas[j].strip()):
                    valor = linhas[j].strip()
                    break
            if data and valor:
                try:
                    v = float(valor.replace('.', '').replace(',', '.'))
                    eventos.append({'data': data, 'valor': v})
                except ValueError:
                    pass
    return eventos


# ============================================================
# 3-bis. AUDITORIA + LANÇAMENTOS DA FONTE RECOMENDADA
# ============================================================
def obter_lancamentos_auditados(tabela_path: str, extrato_path: str,
                                  rubrica: str,
                                  tolerancia_centavos: int = 1) -> dict:
    """Audita tabela vs extrato para uma rubrica e retorna lançamentos da
    fonte mais confiável.

    Use ANTES de montar o `tese['lancamentos']` para a inicial — substitui
    o hardcode manual.

    Returns:
        {
            'lancamentos': [(data_str, valor_float), ...],  # pronto para tese
            'fonte_usada': 'tabela' / 'extrato',
            'severidade': 'OK' / 'ATENCAO' / 'CRITICO',
            'relatorio': str (texto humano com divergências, anexar a alerta),
            'qtd_tabela': int,
            'qtd_extrato': int,
            'soma_tabela': float,
            'soma_extrato': float,
        }

    Política de seleção:
      - paridade → usa tabela (mais legível, NotebookLM já formatou)
      - extrato > tabela em quantidade → usa extrato (tabela está incompleta)
      - tabela > extrato → usa tabela (parser direto pode ter falhado);
        mas alerta crítico para revisão manual
    """
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from auditor import auditar_tabela_vs_extrato, gerar_relatorio_auditoria_tabela

    audit = auditar_tabela_vs_extrato(
        tabela_path, extrato_path, [rubrica], tolerancia_centavos
    )
    if not audit['rubricas']:
        return {
            'lancamentos': [],
            'fonte_usada': 'nenhuma',
            'severidade': 'CRITICO',
            'relatorio': audit.get('recomendacao_global', 'Sem dados para auditar'),
            'qtd_tabela': 0, 'qtd_extrato': 0,
            'soma_tabela': 0.0, 'soma_extrato': 0.0,
        }

    r = audit['rubricas'][0]
    fonte = r['fonte_recomendada']
    if fonte == 'extrato':
        descontos = parsear_lancamentos_extrato(extrato_path, filtro_rubrica=rubrica)
        lancamentos = [(d['data'], d['valor']) for d in descontos]
    elif fonte in ('tabela', 'paridade'):
        descontos = parsear_tabela_descontos(tabela_path, filtro_rubrica=rubrica)
        lancamentos = [(d['data'], d['valor']) for d in descontos]
        fonte = 'tabela' if fonte == 'paridade' else fonte
    else:
        lancamentos = []

    return {
        'lancamentos': lancamentos,
        'fonte_usada': fonte,
        'severidade': audit['severidade'],
        'relatorio': gerar_relatorio_auditoria_tabela(audit),
        'qtd_tabela': r['tabela']['qtd'],
        'qtd_extrato': r['extrato']['qtd'],
        'soma_tabela': r['tabela']['soma'],
        'soma_extrato': r['extrato']['soma'],
    }


# ============================================================
# 4. EXTRAIR QUALIFICAÇÃO DA NOTIFICAÇÃO EXTRAJUDICIAL
# ============================================================
def extrair_qualificacao_da_notificacao(notificacao_path):
    """Lê notificação extrajudicial (texto-camada) e extrai dados do autor.

    Padrão típico: "NOME COMPLETO, brasileira, viúva, aposentada, inscrita
    no CPF sob o nº X, Cédula de Identidade nº Y, órgão expedidor Z, residente..."

    Returns: dict com campos extraídos (chaves vazias se não achou).
    """
    if not os.path.exists(notificacao_path):
        return {}
    doc = fitz.open(notificacao_path)
    txt = '\n'.join(p.get_text() for p in doc)
    doc.close()

    out = {}

    # Nome (linha que começa com NOME EM CAIXA ALTA antes de "brasileir")
    m = re.search(r'\n([A-ZÁÉÍÓÚÂÊÔÃÕÇ ]{8,})\s*,\s*brasileir', txt)
    if m:
        out['nome_completo'] = m.group(1).strip()

    # CPF
    m = re.search(r'CPF\s+sob\s+o\s+n[º\s]+([\d.\-]+)', txt, re.IGNORECASE)
    if m:
        out['cpf'] = m.group(1).strip()

    # RG (Cédula de Identidade)
    m = re.search(r'C[ée]dula\s+de\s+Identidade\s+n[º\s]+([\d.\-]+)', txt, re.IGNORECASE)
    if m:
        out['rg'] = m.group(1).strip()

    # Órgão expedidor
    m = re.search(r'[óo]rg[ãa]o\s+expedidor\s+([A-Z]{2,5}/?[A-Z]{0,3})', txt, re.IGNORECASE)
    if m:
        out['orgao_expedidor'] = m.group(1).strip()

    # Estado civil + profissão (depois de "brasileiro/a,")
    m = re.search(r'brasileir[ao],\s*([\w\s]+?),\s*([\w\s]+?),\s*inscrit[ao]', txt, re.IGNORECASE)
    if m:
        out['estado_civil'] = m.group(1).strip()
        out['profissao'] = m.group(2).strip()

    # Nacionalidade
    m = re.search(r'\b(brasileir[ao])\b', txt, re.IGNORECASE)
    if m:
        out['nacionalidade'] = m.group(1).lower()

    # Endereço completo (logradouro, número, bairro, município, CEP, UF)
    # Padrão tipico: "residente e domiciliada à RUA, nº NUM, bairro BAIRRO, Município de CIDADE, CEP XX, estado de UF"
    m = re.search(
        r'residente\s+e\s+domiciliad[ao]\s+[àa]\s*([^,]+),'
        r'\s*n[º\s]*([^,]+),'
        r'\s*bairro\s+([^,]+),'
        r'\s*Munic[íi]pio\s+de\s+([^,]+),'
        r'\s*CEP\s+([\d.\-]+),'
        r'\s*estado\s+de\s+([A-Z]{2})',
        txt, re.IGNORECASE
    )
    if m:
        out['logradouro'] = m.group(1).strip()
        out['numero'] = m.group(2).strip()
        out['bairro'] = m.group(3).strip()
        out['cidade_de_residencia'] = m.group(4).strip()
        out['cep'] = m.group(5).strip()
        out['uf'] = m.group(6).strip()

    # Para PG ELETRON: dados do TERCEIRO BENEFICIÁRIO
    # Padrão: "À Ouvidoria do <NOME>\nCNPJ: <X>\n<ENDEREÇO>"
    m = re.search(
        r'À\s+Ouvidoria\s+do\s+([^\n]+?)\s*\n\s*CNPJ[:\s]+([\d.\-/]+)\s*\n\s*([^\n]+)',
        txt
    )
    # primeira ocorrência geralmente é Bradesco; segunda é o terceiro
    matches = list(re.finditer(
        r'À\s+Ouvidoria\s+(?:do|da|de)\s+([^\n]+?)\s*\n\s*CNPJ[:\s]+([\d.\-/]+)\s*\n\s*([^\n]+)',
        txt
    ))
    for mm in matches:
        nome = mm.group(1).strip()
        if 'BRADESCO' in nome.upper():
            continue  # primeiro réu é fixo
        out['nome_terceiro'] = nome
        out['cnpj_terceiro'] = mm.group(2).strip()
        # Tenta parsear endereço da próxima linha
        end_lin = mm.group(3).strip()
        # Padrão "Rua X, nº Y, Bairro, Cidade/UF, CEP Z"
        m_end = re.search(
            r'^([^,]+?),\s*n?[º\s]*([^,]+),\s*([^,]+),'
            r'\s*([A-Za-zÀ-ú\s]+)\s*[/\-]\s*([A-Z]{2})\s*,?\s*CEP\s*([\d.\-]+)',
            end_lin
        )
        if m_end:
            out['logradouro_terceiro'] = m_end.group(1).strip()
            out['numero_terceiro'] = m_end.group(2).strip()
            out['bairro_terceiro'] = m_end.group(3).strip()
            out['cidade_terceiro'] = m_end.group(4).strip()
            out['uf_terceiro'] = m_end.group(5).strip()
            out['cep_terceiro'] = m_end.group(6).strip()
        else:
            # endereço completo num campo só (fallback)
            out['endereco_terceiro_raw'] = end_lin
        break  # só pegar 1 terceiro

    return out


# ============================================================
# 5. EXTRAIR ENDEREÇO DA DECLARAÇÃO DE DOMICÍLIO
# ============================================================
def extrair_endereco_declaracao(declaracao_path):
    """Lê declaração de domicílio (5.1) e extrai endereço do autor.
    Esta é a fonte preferencial quando o comprovante de residência está no
    nome de terceiro. Returns dict ou {}."""
    if not os.path.exists(declaracao_path):
        return {}
    doc = fitz.open(declaracao_path)
    txt = '\n'.join(p.get_text() for p in doc)
    doc.close()
    if not txt.strip():
        return {}  # PDF escaneado, sem texto

    out = {}
    m = re.search(
        r'Endereço[:\s]+([^,]+),'
        r'\s*([^,]+),'
        r'\s*Bairro\s+([^,]+),'
        r'\s*Munic[íi]pio\s+de\s+([^,]+),'
        r'\s*CEP\s+([\d.\-]+)',
        txt, re.IGNORECASE
    )
    if m:
        out['logradouro'] = m.group(1).strip()
        out['numero'] = m.group(2).strip()
        out['bairro'] = m.group(3).strip()
        out['cidade_de_residencia'] = m.group(4).strip()
        out['cep'] = m.group(5).strip()
    return out


# ============================================================
# 6. AUDITORIA APLIC.INVEST (separar aplicações vs resgates)
# ============================================================
def auditoria_aplic_invest(extrato_path):
    """Para a tese APLIC.INVEST FACIL, separa APLICAÇÕES (débitos) vs
    RESGATES (créditos) e calcula saldo líquido retido.

    Returns: dict com totais e alerta se saldo for negativo.
    """
    if not os.path.exists(extrato_path):
        return {'erro': 'extrato não encontrado'}
    doc = fitz.open(extrato_path)
    texto = '\n'.join(p.get_text() for p in doc)
    doc.close()
    linhas = [ln.rstrip() for ln in texto.split('\n')]

    aplicacoes = []
    resgates = []
    rendimentos = []

    for i, ln in enumerate(linhas):
        upper = ln.upper()
        if 'APLIC.INVEST FACIL' in upper:
            tipo = 'aplic'
        elif 'RESGATE INVEST FACIL' in upper:
            tipo = 'resgate'
        elif 'RENTAB.INVEST FACIL' in upper or 'RENTAB.INVEST FACILCRED' in upper:
            tipo = 'rendimento'
        else:
            continue
        # Confirma movimento: próxima linha tem DOCTO
        nxt = linhas[i+1].strip() if i+1 < len(linhas) else ''
        if not re.match(r'^\d{4,8}$', nxt):
            continue
        data = None
        for j in range(i-1, max(-1, i-15), -1):
            if RE_DATA.match(linhas[j].strip()):
                data = linhas[j].strip()
                break
        valor = None
        for j in range(i+1, min(len(linhas), i+10)):
            if RE_VALOR.match(linhas[j].strip()):
                valor = linhas[j].strip()
                break
        if data and valor:
            try:
                v = float(valor.replace('.', '').replace(',', '.'))
                ev = {'data': data, 'valor': v}
                if tipo == 'aplic':
                    aplicacoes.append(ev)
                elif tipo == 'resgate':
                    resgates.append(ev)
                else:
                    rendimentos.append(ev)
            except ValueError:
                pass

    t_aplic = sum(x['valor'] for x in aplicacoes)
    t_resg = sum(x['valor'] for x in resgates)
    t_rend = sum(x['valor'] for x in rendimentos)
    saldo_liquido = t_aplic - t_resg

    return {
        'aplicacoes': len(aplicacoes),
        'total_aplicado': t_aplic,
        'resgates': len(resgates),
        'total_resgatado': t_resg,
        'rendimentos': len(rendimentos),
        'total_rendimento': t_rend,
        'saldo_liquido': saldo_liquido,
        'alerta': saldo_liquido < 0,
        'mensagem_alerta': (
            'CLIENTE RECEBEU MAIS DO QUE APLICOU. Saldo líquido negativo. '
            'Considerar 3 opções de tese: estrita / conservadora / intermediária. '
            'Vide SKILL.md § Casos especiais.' if saldo_liquido < 0 else None
        ),
    }
