"""
Auditor universal: detecta procurações ÓRFÃS — presentes no PDF
consolidado do cliente (`0. Kit/Procurações.pdf` ou similar) mas que NÃO foram
materializadas em pasta-banco para ajuizamento.

Caso paradigma (2026-05-16): VILSON DA CRUZ BRASIL — PDF de procurações tinha
2 procurações Banrisul (pág. 9 e pág. 10) + 1 procuração PAN 340715594-8 (pág. 11).
O orquestrador detectou as 3, mas só criou pasta para 1 das 3 (a 1ª Banrisul,
PAN 382433312-8 e PAN 767234649-6). As outras viraram "pendência" no JSON e
ninguém percebeu — meses depois, advogado tentou rodar inicial e descobriu.

ESTRATÉGIA:
1. Lê o `_estado_cliente.json` (lista oficial de contratos do cliente).
2. Lê o PDF de procurações (text-layer ou OCR fallback) e extrai
   pares (banco, contrato) usando regex sobre os "Poderes Especiais".
3. Lista todos os arquivos `2. Procuração – ... – Contrato XXX.pdf` nas
   pastas-banco do cliente.
4. Cruza:
   - Procurações no PDF que NÃO têm pasta-banco correspondente → ÓRFÃS
   - Procurações com arquivo na pasta-banco mas SEM procuração no PDF
     → INCONSISTÊNCIA (não deveria acontecer)
   - Contratos do JSON sem procuração nem no PDF nem em pasta → AVISO
5. Gera relatório XLSX/Markdown na raiz do cliente.

USO:
    python auditor_procuracoes_orfas.py <pasta_cliente>

ou via Python:
    from auditor_procuracoes_orfas import auditar_cliente
    rel = auditar_cliente(r'.../VILSON DA CRUZ BRASIL - Maurivã')
    for o in rel['orfas']:
        print(f"ORFÃ: pág {o['pagina']}, banco {o['banco']}, contrato {o['contrato']}")
"""
import os
import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================================
# Padrões de extração
# ============================================================================

# Padrão 1: text-layer típico — "em face do Banco BANRISUL S.A, referente ao
# contrato de empréstimo sob nº 0000000000000917305 e INSS"
# Tolerante a quebras de linha e ruído OCR no separador (· _ — etc).
# Tolerante a "o"/"O"/"q" no lugar de "0" (confusão OCR comum).
# Aceita ruído OCR: ªo/ª0 em vez de ao, S.A vs SA, vírgula às vezes vira "x",
# underscores no lugar de espaços (CamScanner), "à" em diferentes encodings, etc.
# Caso paradigma VILSON (2026-05-16): PDF de procurações escaneado com
# CamScanner — easyocr inseriu "_" no lugar de muitos espaços
# ("em_face", "Banco_BANRISUL", "empréstimo_sob"), e confundiu "ao" com "ªo".
#
# AFROUXAMENTO 2026-05-16 (paradigma MARILDA GARCIA): OCR de scan de celular
# devolve `Banco BRADESCO S A,referente ª ...` (sem vírgula entre 'A' e
# 'referente', tipo de espaçamento variável, "ªo" ↔ "ª" sozinho). O regex
# antigo exigia `[\s_,xX]*` entre banco e referente — frouxei para também
# aceitar vírgula colada (sem espaço). Também aceito `referente` sozinho sem
# `ao/à` (case visto na MARILDA: `referente ª PAGTO ELETRON ...`). E
# permito `referente \w` (tese-tradicional Bradesco descreve a rubrica em
# vez de número de contrato — não capturamos contrato nesse caso, mas
# achamos o banco, e o auditor pode marcar como "procuração sem contrato
# numerado").
_SEP = r'[\s_]*'  # whitespace OU underscore (qualquer quantidade)
_RE_PODERES_ESPECIAIS = re.compile(
    rf'em{_SEP}face{_SEP}(?:do|da|de){_SEP}(?:Banco{_SEP})?'
    r'(?P<banco>[A-ZÇÁÉÍÓÚÂÊÔÃÕÀ][A-ZÇÁÉÍÓÚÂÊÔÃÕÀ\s\.\-/&_]+?)'
    rf'{_SEP}(?:S\.?{_SEP}A\.?)?[\s_,xX]*'
    rf'{_SEP}referente{_SEP}(?:[aàªA][o0O0]|ao|à|a|ª|°)?{_SEP}'
    rf'(?:contrato{_SEP}(?:de{_SEP}empréstimo{_SEP})?(?:sob{_SEP}(?:o{_SEP})?n[º°ª\.\?"]*{_SEP})?|'
    rf'contrato{_SEP}(?:RMC|RCC){_SEP}sob{_SEP}n[º°ª\.\?"]*{_SEP})'
    r'(?P<contrato>[\dA-Zo0OqQ\-]{6,30})',
    re.IGNORECASE | re.DOTALL,
)

# Padrão 1b: "em face do Banco X (S.A/SA)? referente [ª/à/ao/a] [TESE]"
# — quando NÃO há número de contrato (procurações Bradesco por tese, ex:
# "referente ª MORA CRED PESS", "referente 0 TITULO DE CAPITALIZACAO",
# "referente PAGTO ELETRON COBRANCA ASPECIR"). Captura banco + tese textual.
_RE_PODERES_POR_TESE = re.compile(
    rf'em{_SEP}face{_SEP}(?:do|da|de){_SEP}(?:Banco{_SEP})?'
    r'(?P<banco>[A-ZÇÁÉÍÓÚÂÊÔÃÕÀ][A-ZÇÁÉÍÓÚÂÊÔÃÕÀ\s\.\-/&_]+?)'
    rf'{_SEP}(?:S\.?{_SEP}A\.?)?[\s_,xX]*'
    rf'{_SEP}(?:e{_SEP}[A-Z][\wÇÁÉÍÓÚÂÊÔÃÕÀ\s\.\-/&_]+?{_SEP})?'  # opcional "e TERCEIRO"
    rf'referente{_SEP}(?:[aàªA][o0O0]|ao|à|a|ª|°)?{_SEP}'
    r'(?P<tese>(?:MORA|TARIFA|CART[AÃ]O|T[IÍ]TULO|CAPITALIZA[CÇ]|PAG(?:TO|AMENTO)|APLIC|ANUIDADE|CESTA|CR[ÉE]DIT|ELETR[OÔ]N|COBRAN|EXPRESS)[\w\s\.\-/&]+?)'
    r'(?:[\.,]|podendo|\s+os\s+Advogados|\s+OS\s+Advogados|$)',
    re.IGNORECASE | re.DOTALL,
)

# Padrão 2: variação com "em face do" + número antes do banco
_RE_CONTRATO_SIMPLES = re.compile(
    r'contrato[\s_]*(?:sob[\s_]*(?:o[\s_]*)?)?n[º°ª\.]?[\s_]*(?P<contrato>[\dA-Zo0OqQ\-]{6,30})',
    re.IGNORECASE,
)


def _limpar_numero_ocr(s: str) -> str:
    """Limpa números que o OCR errou (o/q/O viraram zeros, etc.).

    Delega para `ocr_learning.aplicar_correcoes` quando disponível
    (combina histórico aprendido + substituições determinísticas).
    Fallback: tabela hardcoded.
    """
    if not s:
        return ''
    # Tenta usar o sistema de aprendizado
    try:
        import sys as _sys, os as _os
        _here = _os.path.dirname(_os.path.abspath(__file__))
        if _here not in _sys.path:
            _sys.path.insert(0, _here)
        from ocr_learning import aplicar_correcoes  # type: ignore
        return aplicar_correcoes(s)
    except Exception:
        pass
    # Fallback: substituições mais comuns
    tab = {'o': '0', 'O': '0', 'q': '0', 'Q': '0',
           'l': '1', 'I': '1', '|': '1',
           'S': '5', 's': '5',
           'B': '8'}
    out = []
    for ch in s:
        if ch.isdigit() or ch == '-':
            out.append(ch)
        elif ch in tab:
            out.append(tab[ch])
    return ''.join(out)

# Bancos canônicos (mapeamento varia mas serve para classificação)
BANCOS_KW = [
    'BANRISUL', 'BMG', 'PAN', 'BRADESCO', 'FACTA', 'C6', 'ITAU', 'ITAÚ',
    'DAYCOVAL', 'OLE', 'SANTANDER', 'SAFRA', 'MERCANTIL', 'INTER',
    'INBURSA', 'PARANA', 'PARATI', 'SENFF', 'SICOOB', 'CETELEM', 'BGN',
    'AGIBANK', 'CREFISA', 'MASTER', 'PICPAY', 'CAPITAL', 'NUBANK',
    'CAIXA', 'BB ', 'BRASIL S/A', 'BRASIL S.A',
    'BANCO DO ESTADO DO RIO GRANDE DO SUL',
]


def _norm_banco(nome: str) -> str:
    """Mapeia nome encontrado para chave canônica."""
    s = (nome or '').upper().strip()
    if not s:
        return ''
    if 'BANRISUL' in s or 'RIO GRANDE DO SUL' in s:
        return 'BANRISUL'
    for kw in BANCOS_KW:
        if kw in s:
            return kw.strip().replace(' S/A', '').replace(' S.A', '').strip()
    return s[:30]


def _norm_contrato(num: str) -> str:
    """Remove espaços e pontuação para comparar."""
    return re.sub(r'[^0-9A-Z]', '', (num or '').upper())


# ============================================================================
# Extração de procurações do PDF
# ============================================================================

def _ocr_pagina_easyocr(pdf_path: str, pag_num: int) -> str:
    """OCR de UMA página usando easyocr. Devolve texto bruto concatenado.

    Lazy import — só carrega easyocr se realmente precisar.
    Aprende com o histórico via `ocr_learning` (allowlist guiada).
    """
    import fitz
    try:
        import easyocr  # type: ignore
        import numpy as np  # type: ignore
        from PIL import Image  # type: ignore
        import io as _io
    except ImportError:
        return ''
    # Renderiza página em PNG
    doc = fitz.open(pdf_path)
    page = doc[pag_num - 1]
    mat = fitz.Matrix(2.0, 2.0)  # zoom para OCR ler melhor
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes('png')
    doc.close()
    img = Image.open(_io.BytesIO(img_bytes))
    arr = np.array(img)
    # Reader singleton via atributo de função (carrega 1x por processo)
    reader = getattr(_ocr_pagina_easyocr, '_reader', None)
    if reader is None:
        try:
            reader = easyocr.Reader(['pt'], gpu=False, verbose=False)
            _ocr_pagina_easyocr._reader = reader
        except Exception:
            return ''
    # Allowlist do aprendizado contínuo — guia o OCR a preferir caracteres
    # comuns em procurações (dígitos, letras, pontuação típica).
    allowlist = None
    try:
        import sys as _sys, os as _os
        _here = _os.path.dirname(_os.path.abspath(__file__))
        if _here not in _sys.path:
            _sys.path.insert(0, _here)
        from ocr_learning import obter_allowlist_easyocr  # type: ignore
        allowlist = obter_allowlist_easyocr()
    except Exception:
        pass
    try:
        if allowlist:
            textos = reader.readtext(arr, detail=0, paragraph=True,
                                       allowlist=allowlist)
        else:
            textos = reader.readtext(arr, detail=0, paragraph=True)
    except Exception:
        return ''
    return '\n'.join(textos)


def extrair_procuracoes_do_pdf(pdf_path: str, *, usar_ocr: bool = True) -> List[Dict]:
    """Lê o PDF e devolve lista de procurações detectadas.

    Tenta primeiro text-layer (rápido). Para páginas sem texto, faz OCR via
    easyocr (se disponível). Caso paradigma VILSON: PDF de 16 páginas escaneadas
    (CamScanner) — sem fallback OCR, o auditor não detectava nada.

    Returns:
        [{'pagina': int, 'banco': str (chave canônica), 'contrato': str (normalizado),
          'banco_bruto': str, 'contrato_bruto': str, 'metodo': 'text-layer'|'ocr'}]
    """
    try:
        import fitz
    except ImportError:
        return [{'erro': 'PyMuPDF (fitz) não instalado'}]
    if not os.path.exists(pdf_path):
        return [{'erro': f'PDF não encontrado: {pdf_path}'}]

    achados = []
    paginas_sem_texto = []
    paginas_ocr_sem_match = []
    doc = fitz.open(pdf_path)
    total = len(doc)
    doc.close()

    # KWs de tese para fallback Bradesco (cobre OCR comum: IITULO/CARTAQ/etc.)
    TESES_KW = [
        ('MORA', r'MORA[\s_]*(?:CR[EÉ]DIT[OQ]?[\s_]*PESS|CRED[\s_]*PESS|PESSOAL)?'),
        ('TARIFA', r'TARIFA[\s_]*(?:BANC[AÁ]RIA)?(?:[\s_]*CESTA|[\s_]*EXPRESS)?'),
        ('ANUIDADE', r'CART[AÃ]Q?[\s_]*CR[ÉE]DIT[OQ]?[\s_]*ANUIDADE|ANUIDADE'),
        ('CAPITALIZACAO', r'(?:[ITI]+ITULO|T[IÍ]TULO)[\s_]*DE[\s_]*CAPITALIZA[CÇ][AÃ]Q?[OQ]?'),
        ('APLIC_INVEST', r'APLIC[\s_\.]*INVEST(?:[\s_]*F[AÁ]CIL)?'),
        # PAGTO ELETRON pode virar PAGIO ELEIRON / PAGTO ELETORN / PAGIO ELETRON
        # (OCR confunde T↔I). Padrão tolera [TI] em ambas posições.
        ('PG_ELETRON', r'PAG[\s_]*(?:TO|AMENTO|IO)?[\s_]*EL[EÉ]?[TI][OR]+[NM][\s_]*COBRAN[CÇ]A?'),
    ]

    for i in range(1, total + 1):
        doc2 = fitz.open(pdf_path)
        txt = doc2[i - 1].get_text() or ''
        doc2.close()
        metodo = 'text-layer'
        if len(txt.strip()) < 50:
            if usar_ocr:
                txt = _ocr_pagina_easyocr(pdf_path, i)
                metodo = 'ocr'
                if len(txt.strip()) < 50:
                    paginas_sem_texto.append(i)
                    continue
            else:
                paginas_sem_texto.append(i)
                continue

        # ESTRATÉGIA 2-ETAPAS (paradigma MARILDA 2026-05-16):
        # Em vez de um regex monolítico (frágil contra OCR sujo), extrai
        # PRIMEIRO o trecho "em face d[oae]...podendo|INSS|sob as penas" e
        # depois detecta banco/contrato/tese DENTRO desse trecho. Imune a:
        # palavras coladas ("BancoBRADESCO"), separadores estranhos
        # ("S Axreferente", "S Ae"), "ao" virando "go"/"90"/"0"/"ª".
        #
        # AMPLIAÇÃO 2026-05-16 (paradigma lote 02 ao 06): aceita "em face de"
        # (não só "do/da"). Formato novo de cartão consignado usa "em face de
        # Banco X S.A – Cartão RMC - Contrato: NNN" — sem "referente". Também
        # detecta tipo (RMC/RCC/CONSIGNADO) a partir do trecho.
        m_face = re.search(
            r'em\s*face\s*d[oae](.{0,400}?)(?:podendo|INSS|sob\s+as\s+penas|outorgo|maciça)',
            txt, re.IGNORECASE | re.DOTALL,
        )
        if m_face:
            trecho = m_face.group(1)
            # Banco: primeiro KW da BANCOS_KW que aparece NO TRECHO (não na página inteira)
            banco_det = None
            trecho_upper = trecho.upper()
            for kw in BANCOS_KW:
                if kw.upper() in trecho_upper:
                    banco_det = _norm_banco(kw)
                    break
            # Detectar TIPO da ação: RMC/RCC/CONSIGNADO/REFINANCIAMENTO.
            # "Cartão RMC", "RMC", "Reserva de Margem" → RMC
            # "Cartão RCC", "RCC", "Cartão de Crédito Consignado" → RCC
            # "refinanciamento", "refin" → REFIN (futuro)
            # Padrão: CONSIGNADO
            tipo_det = 'CONSIGNADO'
            if re.search(r'CART[AÃ]O[\s_\-–—]+RCC|\bRCC\b|CART[AÃ]O\s+DE\s+CR[EÉ]DITO\s+CONSIGNADO', trecho, re.IGNORECASE):
                tipo_det = 'RCC'
            elif re.search(r'CART[AÃ]O[\s_\-–—]+RMC|\bRMC\b|RESERVA\s+DE\s+MARGEM', trecho, re.IGNORECASE):
                tipo_det = 'RMC'
            # Contrato: regex permissivo de número.
            # Aceita formatos: "nº NNN", "contrato sob o nº NNN", "Contrato: NNN",
            # "Contrato - NNN", "Contrato NNN".
            contrato_det = ''
            m_num = re.search(
                r'(?:n[º°ª\.]?[\s_]*|contrato[\s_\-–—:]*(?:sob[\s_]*)?(?:o[\s_]*)?(?:n[º°ª\.]?[\s_]*)?)'
                r'(\d{6,}(?:-\d+)?)',
                trecho, re.IGNORECASE,
            )
            if not m_num:
                # fallback: qualquer número longo isolado dentro do trecho
                m_num = re.search(r'(\d{8,}(?:-\d+)?)', trecho)
            if m_num:
                bruto = m_num.group(1)
                contrato_det = (_limpar_numero_ocr(bruto)
                                if metodo.startswith('ocr')
                                else _norm_contrato(bruto))
            if banco_det and contrato_det:
                achados.append({
                    'pagina': i,
                    'banco': banco_det,
                    'tipo': tipo_det,
                    'contrato': contrato_det,
                    'banco_bruto': banco_det,
                    'contrato_bruto': m_num.group(1) if m_num else '',
                    'metodo': metodo,
                })
                continue
            # Sem contrato — tenta tese (procurações Bradesco por rubrica)
            if banco_det:
                tese_det = None
                for tese_nome, tese_pat in TESES_KW:
                    if re.search(tese_pat, trecho, re.IGNORECASE):
                        tese_det = tese_nome
                        break
                if tese_det:
                    achados.append({
                        'pagina': i,
                        'banco': banco_det,
                        'contrato': '',
                        'tese': tese_det,
                        'banco_bruto': banco_det,
                        'contrato_bruto': '',
                        'metodo': f'{metodo}-por-tese',
                    })
                    continue

        # Página com texto mas sem trecho "em face do" — registrar para revisão
        if metodo == 'ocr':
            paginas_ocr_sem_match.append(i)

    aviso = {}
    if paginas_sem_texto:
        aviso['_aviso_paginas_sem_texto'] = paginas_sem_texto
    if paginas_ocr_sem_match:
        aviso['_aviso_ocr_sem_match'] = paginas_ocr_sem_match
    if aviso:
        achados.append(aviso)
    return achados


# ============================================================================
# Inventário de procurações em pastas-banco
# ============================================================================

# Padrões de TESE para Bradesco (a procuração é por tese, não por contrato)
TESES_BRADESCO = [
    'TARIFA', 'TARIFAS',
    'MORA CRED PESS', 'MORA',
    'GASTOS CARTÃO DE CRÉDITO', 'GASTOS CARTAO', 'GASTOS CARTÃO',
    'APLIC.INVEST', 'APLIC INVEST', 'APLICAÇÃO INVEST', 'APLICACAO INVEST',
    'TÍTULO DE CAPITALIZAÇÃO', 'TITULO DE CAPITALIZACAO', 'CAPITALIZAÇÃO',
    'CAPITALIZACAO',
    'PG ELETRON', 'PAGAMENTO ELETRÔNICO', 'PAGAMENTO ELETRONICO',
    'ENCARGO', 'ENCARGOS LIMITE',
    'CESTA', 'CESTA B.EXPRESSO', 'CESTA EXPRESSO',
]


def _norm_tese(s: str) -> str:
    """Normaliza nome de tese para comparação (remove acentos, padroniza)."""
    import unicodedata
    if not s:
        return ''
    s = s.upper()
    nfkd = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in nfkd if not unicodedata.combining(c))
    s = re.sub(r'[^A-Z0-9 ]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    # Sinônimos
    sinonimos = {
        'TARIFAS': 'TARIFA',
        'GASTOS CARTAO DE CREDITO': 'GASTOS CARTAO',
        'GASTOS CARTAO DE CREDITO SEM MODELO': 'GASTOS CARTAO',
        'APLIC INVEST': 'APLICACAO INVEST',
        'CAPITALIZACAO': 'TITULO CAPITALIZACAO',
        'TITULO DE CAPITALIZACAO': 'TITULO CAPITALIZACAO',
        'MORA CRED PESS': 'MORA',
        'PAGAMENTO ELETRONICO': 'PG ELETRON',
        'CESTA BEXPRESSO': 'CESTA',
        'CESTA EXPRESSO': 'CESTA',
        'CESTA B EXPRESSO': 'CESTA',
        'ENCARGOS LIMITE': 'ENCARGO',
    }
    return sinonimos.get(s, s)


def _detectar_tese_no_nome(nome_arquivo: str) -> Optional[str]:
    """Detecta o nome da tese Bradesco no nome do arquivo de procuração."""
    u = nome_arquivo.upper()
    for tese in TESES_BRADESCO:
        if tese.upper() in u:
            return _norm_tese(tese)
    return None


def listar_procuracoes_em_pastas(pasta_cliente: str) -> List[Dict]:
    """Varre subpastas do cliente procurando arquivos
    `2. Procuração – BANCO – Contrato NNN.pdf` (padrão NC kit-juridico v2.x)
    OU `2 - PROCURAÇÃO BRADESCO TESE.pdf` (padrão Bradesco).

    Retorna pares (banco, contrato) para NC e (banco, tese) para Bradesco.

    Returns:
        [{'pasta_rel': str, 'arquivo': str, 'banco': str (canônico),
          'contrato': str (normalizado, se houver),
          'tese': str (normalizada, se houver — Bradesco),
          'tipo': 'contrato'|'tese'}]
    """
    base = Path(pasta_cliente)
    if not base.is_dir():
        return []
    achados = []
    for root, dirs, files in os.walk(base):
        rel = Path(root).relative_to(base)
        # No NC: ignora pastas do kit consolidado (procurações ficam em pastas-banco)
        # No Bradesco: a procuração pode estar EM `0. Kit/SUBTESE/` — não ignorar.
        rel_lower = str(rel).lower()
        # Ignora só `_proc_crops` e `_lint`
        if rel_lower.startswith(('_proc_crops', '_lint')):
            continue
        for f in files:
            if not f.lower().startswith(('2.', '2 -', '2-')):
                continue
            if 'procura' not in f.lower():
                continue
            if not f.lower().endswith('.pdf'):
                continue
            # Banco
            banco_norm = ''
            for kw in BANCOS_KW:
                if kw.upper() in f.upper():
                    banco_norm = _norm_banco(kw)
                    break
            # Contrato (padrão NC)
            m_cont = re.search(r'[Cc]ontrato\s+(?:n[º°ª\.]?\s*)?([0-9A-Z\-]{6,30})',
                                f, re.IGNORECASE)
            contrato_norm = _norm_contrato(m_cont.group(1)) if m_cont else ''
            # Tese (padrão Bradesco)
            tese_norm = _detectar_tese_no_nome(f) if banco_norm == 'BRADESCO' else None
            # Tipo
            if contrato_norm:
                tipo = 'contrato'
            elif tese_norm:
                tipo = 'tese'
            else:
                tipo = 'desconhecido'
            achados.append({
                'pasta_rel': str(rel).replace('\\', '/'),
                'arquivo': f,
                'banco': banco_norm,
                'contrato': contrato_norm,
                'tese': tese_norm or '',
                'tipo': tipo,
                'arquivo_completo': str(Path(root) / f),
                'dentro_do_kit': 'kit' in rel_lower or rel_lower.startswith('0.'),
            })
    return achados


# ============================================================================
# Cruzamento e relatório
# ============================================================================

def detectar_escopo_executado(pasta_cliente: str) -> Dict:
    """Infere quais teses estão no escopo do cliente OLHANDO a estrutura física
    de pastas. Útil para distinguir "órfã verdadeira" de "tese fora do escopo
    desta rodada".

    Regras:
      - Pasta `Não contratado/` (ou variantes) na raiz → escopo inclui 'NC'
      - Pasta `RMC/` → escopo 'RMC'
      - Pasta `RCC/` → escopo 'RCC'
      - Pasta `Bradesco/` na raiz OU subpastas-tese Bradesco
        (`MORA CRED PESS/`, `TARIFA/`, `GASTOS CARTAO/`, etc.) na raiz
        → escopo 'BRADESCO'
      - Também checa o `_estado_cliente.json` se existir (campo
        `escopo_executado` explícito tem prioridade).

    Returns:
        {
          'escopo': set[str],   # ex.: {'NC', 'RMC'} ou {'BRADESCO'}
          'origem': str,        # 'json' | 'auto-detectado' | 'vazio'
          'pastas_raiz': list[str],  # nomes que indicaram escopo
        }
    """
    base = Path(pasta_cliente)
    if not base.is_dir():
        return {'escopo': set(), 'origem': 'vazio', 'pastas_raiz': []}

    # 1. Tentar JSON explícito primeiro
    json_path = base / '_estado_cliente.json'
    if json_path.exists():
        try:
            import json as _j
            estado = _j.loads(json_path.read_text(encoding='utf-8'))
            esc = estado.get('escopo_executado')
            if esc and isinstance(esc, list):
                return {
                    'escopo': set(str(e).upper() for e in esc),
                    'origem': 'json',
                    'pastas_raiz': [],
                }
        except Exception:
            pass

    # 2. Auto-detecção pela estrutura física
    escopo = set()
    pastas_indicadoras = []
    raiz_lower = {n.lower(): n for n in os.listdir(base) if (base / n).is_dir()}
    # NC / RMC / RCC
    for lab, kw in [
        ('NC', ['não contratado', 'nao contratado']),
        ('RMC', ['rmc']),
        ('RCC', ['rcc']),
        ('BRADESCO', ['bradesco']),
    ]:
        for k in kw:
            if k in raiz_lower:
                escopo.add(lab)
                pastas_indicadoras.append(raiz_lower[k])
                break
    # Bradesco também detectado por subpastas-tese específicas na raiz
    bradesco_teses_raiz = set()
    for n_lower, n_real in raiz_lower.items():
        nu = n_real.upper()
        if any(t in nu for t in TESES_BRADESCO):
            bradesco_teses_raiz.add(n_real)
    if bradesco_teses_raiz:
        escopo.add('BRADESCO')
        pastas_indicadoras.extend(sorted(bradesco_teses_raiz))

    return {
        'escopo': escopo,
        'origem': 'auto-detectado' if escopo else 'vazio',
        'pastas_raiz': pastas_indicadoras,
    }


def _orfa_esta_no_escopo(orfa: Dict, escopo: set) -> bool:
    """Retorna True se a procuração órfã está dentro do escopo executado.

    Lógica:
      - Órfã do tipo 'tese' (Bradesco) → escopo deve incluir 'BRADESCO'
      - Órfã do tipo 'contrato' (NC) → escopo deve incluir 'NC', 'RMC' ou 'RCC'
        (qualquer um — o auditor genérico não diferencia, mas se o escopo
        só tem BRADESCO, claramente o operador não rodou NC nessa rodada)
      - Sem escopo detectado → não filtra (mostra tudo)
    """
    if not escopo:
        return True
    if orfa.get('tipo') == 'tese':
        return 'BRADESCO' in escopo
    # Tipo contrato: aceita se há QUALQUER escopo NC-related
    return bool(escopo & {'NC', 'RMC', 'RCC'})


def auditar_cliente(pasta_cliente: str, *, escopo_override: Optional[set] = None) -> Dict:
    """Cruza procurações no PDF consolidado vs procurações em pastas-banco.

    Procura o PDF em:
      - `0. Kit/Procurações.pdf`
      - `0. Kit/Processo *.pdf`
      - Qualquer outro arquivo na raiz / Kit que pareça ser o consolidado

    Returns:
        {
          'pasta_cliente': str,
          'pdf_consolidado': str,
          'procuracoes_pdf': [...] (do PDF),
          'procuracoes_pastas': [...] (das pastas-banco),
          'orfas': [...] (no PDF mas SEM pasta correspondente),
          'extras': [...] (pasta tem procuração que NÃO está no PDF),
          'duplicatas_mesmo_banco': [...] (banco com 2+ contratos no PDF
                                            quando só 1 foi materializado),
          'paginas_sem_texto': [...] (necessitam OCR manual),
          'recomendacoes': [str, ...]
        }
    """
    base = Path(pasta_cliente)
    pdf_path = None
    # Procura padrão "Procurações" primeiro
    candidatos = []
    for sub in ['0. Kit', '0.Kit', 'Kit', '']:
        d = base / sub if sub else base
        if not d.is_dir():
            continue
        for n in os.listdir(d):
            ln = n.lower()
            if not ln.endswith('.pdf'):
                continue
            if 'procura' in ln:
                candidatos.insert(0, str(d / n))  # prioridade
            elif 'processo' in ln or 'consolidado' in ln:
                candidatos.append(str(d / n))
    if not candidatos:
        # Sem PDF consolidado: pode ser fluxo Bradesco (procurações já vêm
        # separadas em arquivos individuais dentro do Kit). Não é erro fatal —
        # ainda fazemos a auditoria comparando subpastas Kit vs subpastas-ação.
        pdf_path = None
        procs_pdf = []
    else:
        pdf_path = candidatos[0]
        procs_pdf = extrair_procuracoes_do_pdf(pdf_path)
    # Separa avisos de páginas sem texto
    paginas_sem_texto = []
    paginas_ocr_sem_match = []
    procs_pdf_limpas = []
    for p in procs_pdf:
        if p.get('_aviso_paginas_sem_texto'):
            paginas_sem_texto = p['_aviso_paginas_sem_texto']
        elif p.get('_aviso_ocr_sem_match'):
            paginas_ocr_sem_match = p['_aviso_ocr_sem_match']
        elif p.get('erro'):
            return p  # propaga erro
        else:
            procs_pdf_limpas.append(p)

    procs_pastas = listar_procuracoes_em_pastas(pasta_cliente)

    # Detecta MODO: NC (procurações por contrato) ou BRADESCO (por tese)
    procs_bradesco_pdf = [p for p in procs_pdf_limpas if p['banco'] == 'BRADESCO']
    procs_bradesco_pastas = [p for p in procs_pastas if p.get('banco') == 'BRADESCO']
    modo_bradesco = bool(procs_bradesco_pdf or procs_bradesco_pastas)

    # Comparação tolerante: normaliza contratos para comparação
    # (lstrip('0') + remove hífen, igual ao filtrar_contratos_por_numero
    # do extrator_hiscon — Patch A do caso VILSON).
    def _chave_comparacao(banco: str, contrato: str) -> tuple:
        c = re.sub(r'\D', '', contrato).lstrip('0') if contrato else ''
        return (banco.upper(), c)

    def _bate_com_tolerancia(banco_a: str, cont_a: str, banco_b: str, cont_b: str) -> bool:
        """Retorna True se os pares (banco, contrato) batem com tolerância de
        até 2 dígitos no número (lstrip('0'), depois Hamming ou substring).
        """
        if banco_a.upper() != banco_b.upper():
            return False
        ca = re.sub(r'\D', '', cont_a).lstrip('0')
        cb = re.sub(r'\D', '', cont_b).lstrip('0')
        if not ca or not cb:
            return False
        if ca == cb:
            return True
        # Tolerância: diferença de comprimento ≤ 2 + substring
        if abs(len(ca) - len(cb)) <= 2 and (ca in cb or cb in ca):
            return True
        # Hamming distance ≤ 1 (mesmo tamanho)
        if len(ca) == len(cb):
            dist = sum(1 for x, y in zip(ca, cb) if x != y)
            if dist <= 1:
                return True
        return False

    # Órfãs: no PDF mas NÃO em pasta (com tolerância de comparação)
    orfas = []
    for p in procs_pdf_limpas:
        achou = False
        for pp in procs_pastas:
            if _bate_com_tolerancia(p['banco'], p['contrato'],
                                      pp['banco'], pp.get('contrato', '')):
                achou = True
                break
        if not achou:
            # Tolerância já aplicada acima — se chegou aqui, é órfã real
            orfas.append({**p, 'tipo': 'contrato', 'proximidade_pasta': None})

    # Extras: pasta com contrato que NÃO está no PDF (com tolerância)
    extras = []
    for p in procs_pastas:
        if p.get('tipo') != 'contrato':
            continue  # procurações por tese (Bradesco) tratadas abaixo
        achou = False
        for pp in procs_pdf_limpas:
            if _bate_com_tolerancia(p['banco'], p.get('contrato', ''),
                                      pp['banco'], pp['contrato']):
                achou = True
                break
        if not achou:
            extras.append(p)

    # ========================================================================
    # MODO BRADESCO: comparação por TESE (não por contrato)
    # Detecta procurações Bradesco que estão DENTRO do `0. Kit/` em subpastas
    # mas NÃO viraram subpasta-tese de ação na raiz do cliente.
    # Caso paradigma: Ana Caroline tem `0. Kit/GASTOS CARTÃO DE CRÉDITO SEM
    # MODELO/2 - PROCURAÇÃO BRADESCO GASTOS CARTÃO DE CRÉDITO.pdf` mas só
    # subpasta `MORA CRED PESS/` foi criada — gastos cartão ficou órfã.
    # ========================================================================
    orfas_bradesco = []
    if procs_bradesco_pastas:
        teses_pdf = set()
        for p in procs_bradesco_pdf:
            tese = _detectar_tese_no_nome(p.get('contrato_bruto', '')) or _detectar_tese_no_nome(p.get('banco_bruto', ''))
            if tese:
                teses_pdf.add(tese)
        # Teses presentes em qualquer procuração da pasta
        teses_em_proc_kit = set()
        teses_em_proc_acao = set()
        for p in procs_bradesco_pastas:
            tese = p.get('tese')
            if not tese:
                continue
            if p.get('dentro_do_kit'):
                teses_em_proc_kit.add(tese)
            else:
                teses_em_proc_acao.add(tese)
        # Teses ÓRFÃS: tem procuração no Kit (ou subpasta do Kit) mas SEM
        # pasta-tese de ação correspondente na raiz do cliente.
        for tese in teses_em_proc_kit - teses_em_proc_acao:
            # Pegar dados detalhados da procuração no kit
            proc_kit = next((p for p in procs_bradesco_pastas
                             if p.get('tese') == tese and p.get('dentro_do_kit')), None)
            orfas_bradesco.append({
                'banco': 'BRADESCO',
                'tese': tese,
                'tipo': 'tese',
                'arquivo_no_kit': proc_kit['arquivo'] if proc_kit else '',
                'pasta_rel_kit': proc_kit['pasta_rel'] if proc_kit else '',
                'pagina': None,
            })

    # Duplicatas: bancos com múltiplos contratos no PDF
    from collections import Counter
    bancos_pdf = Counter(p['banco'] for p in procs_pdf_limpas)
    bancos_pastas = Counter(p['banco'] for p in procs_pastas)
    duplicatas = []
    for banco, n_pdf in bancos_pdf.items():
        n_pasta = bancos_pastas.get(banco, 0)
        if n_pdf > n_pasta:
            duplicatas.append({
                'banco': banco,
                'qtd_no_pdf': n_pdf,
                'qtd_em_pastas': n_pasta,
                'contratos_no_pdf': [p['contrato'] for p in procs_pdf_limpas
                                      if p['banco'] == banco],
                'contratos_em_pastas': [p['contrato'] for p in procs_pastas
                                          if p['banco'] == banco],
            })

    # Detecta escopo executado (qual tese rodou nessa pasta)
    info_escopo = detectar_escopo_executado(str(base))
    escopo = escopo_override if escopo_override is not None else info_escopo['escopo']

    # Junta órfãs NC + órfãs Bradesco
    orfas_total_brutas = list(orfas) + list(orfas_bradesco)

    # Filtra por escopo: separa "órfãs no escopo" (alerta crítico) das
    # "fora-de-escopo" (apenas informativo — operador disse que rodaria só
    # NC/RMC e Bradesco ficou para outra rodada)
    orfas_no_escopo = [o for o in orfas_total_brutas if _orfa_esta_no_escopo(o, escopo)]
    orfas_fora_escopo = [o for o in orfas_total_brutas if not _orfa_esta_no_escopo(o, escopo)]

    # Para retrocompatibilidade: campos `orfas`, `orfas_nc`, `orfas_bradesco`
    # passam a refletir APENAS as do escopo. As fora-de-escopo ficam num
    # campo separado.
    orfas_total = orfas_no_escopo
    orfas = [o for o in orfas_no_escopo if o.get('tipo') != 'tese']
    orfas_bradesco = [o for o in orfas_no_escopo if o.get('tipo') == 'tese']

    recomendacoes = []
    if orfas:
        recomendacoes.append(
            f'🚨 {len(orfas)} procuração(ões) ÓRFÃ(s) detectada(s) NO ESCOPO — '
            f'presentes no PDF consolidado mas sem pasta-banco. Criar a(s) '
            f'pasta(s) e rodar a inicial-nao-contratado para cada uma.'
        )
    if orfas_bradesco:
        teses_str = ', '.join(o['tese'] for o in orfas_bradesco)
        recomendacoes.append(
            f'🚨 {len(orfas_bradesco)} procuração(ões) BRADESCO ÓRFÃ(s) NO ESCOPO — '
            f'presentes em subpasta(s) do `0. Kit/` mas sem pasta-tese de ação '
            f'correspondente na raiz do cliente: {teses_str}. Criar a(s) '
            f'subpasta(s)-tese e rodar a inicial-bradesco para cada uma.'
        )
    if orfas_fora_escopo:
        # Por tipo
        for_fora_nc = [o for o in orfas_fora_escopo if o.get('tipo') != 'tese']
        for_fora_br = [o for o in orfas_fora_escopo if o.get('tipo') == 'tese']
        partes = []
        if for_fora_nc:
            partes.append(f'{len(for_fora_nc)} de NC/RMC/RCC')
        if for_fora_br:
            teses_fora = ', '.join(o['tese'] for o in for_fora_br)
            partes.append(f'{len(for_fora_br)} de Bradesco ({teses_fora})')
        recomendacoes.append(
            f'ℹ️ {len(orfas_fora_escopo)} procuração(ões) FORA DO ESCOPO atual '
            f'({", ".join(partes)}). Escopo desta rodada: {sorted(escopo) or "vazio"}. '
            f'Verificar se foram processadas em RODADA ANTERIOR ou se ficaram '
            f'pendentes para próxima.'
        )
    if duplicatas:
        for d in duplicatas:
            recomendacoes.append(
                f'⚠ Banco {d["banco"]}: {d["qtd_no_pdf"]} procuração(ões) no PDF '
                f'mas só {d["qtd_em_pastas"]} pasta(s) materializada(s). '
                f'Contratos no PDF: {d["contratos_no_pdf"]}. '
                f'Em pastas: {d["contratos_em_pastas"]}.'
            )
    if extras:
        recomendacoes.append(
            f'ℹ️ {len(extras)} procuração(ões) em pasta-banco que NÃO bate(m) com '
            f'o PDF consolidado. Pode ser OCR errado ou procuração avulsa.'
        )
    if paginas_sem_texto:
        recomendacoes.append(
            f'⚠ {len(paginas_sem_texto)} página(s) do PDF sem text-layer e o '
            f'OCR também não recuperou texto utilizável: {paginas_sem_texto}. '
            f'Necessário leitura visual manual (Claude Read).'
        )
    if paginas_ocr_sem_match:
        recomendacoes.append(
            f'⚠ {len(paginas_ocr_sem_match)} página(s) com texto via OCR mas '
            f'sem padrão "Poderes Especiais" reconhecido: {paginas_ocr_sem_match}. '
            f'Conferir manualmente se é procuração ou documento avulso.'
        )

    return {
        'pasta_cliente': str(base),
        'pdf_consolidado': pdf_path,
        'procuracoes_pdf': procs_pdf_limpas,
        'procuracoes_pastas': procs_pastas,
        'orfas': orfas_total,            # SÓ dentro do escopo
        'orfas_nc': orfas,                # SÓ NC dentro do escopo
        'orfas_bradesco': orfas_bradesco, # SÓ Bradesco dentro do escopo
        'orfas_fora_escopo': orfas_fora_escopo,  # NÃO alerta, mas registra
        'escopo_detectado': sorted(escopo),
        'origem_escopo': info_escopo['origem'],
        'pastas_indicadoras_escopo': info_escopo['pastas_raiz'],
        'extras': extras,
        'duplicatas_mesmo_banco': duplicatas,
        'paginas_sem_texto': paginas_sem_texto,
        'paginas_ocr_sem_match': paginas_ocr_sem_match,
        'modo_bradesco': modo_bradesco,
        'recomendacoes': recomendacoes,
    }


def gerar_relatorio_md(rel: Dict, output_path: Optional[str] = None) -> str:
    """Gera relatório legível em Markdown."""
    if output_path is None:
        output_path = os.path.join(rel.get('pasta_cliente', '.'),
                                    '_AUDITORIA_PROCURACOES.md')
    linhas = []
    linhas.append('# Auditoria — Procurações vs Pastas-Banco\n')
    linhas.append(f'**Cliente:** `{rel.get("pasta_cliente")}`')
    linhas.append(f'**PDF consolidado:** `{rel.get("pdf_consolidado")}`')
    linhas.append(f'**Procurações no PDF:** {len(rel.get("procuracoes_pdf", []))}')
    linhas.append(f'**Procurações em pastas-banco:** {len(rel.get("procuracoes_pastas", []))}')
    linhas.append('')

    linhas.append('## Recomendações')
    for r in rel.get('recomendacoes', []) or ['Nenhuma.']:
        linhas.append(f'- {r}')
    linhas.append('')

    if rel.get('orfas'):
        linhas.append('## 🚨 Procurações ÓRFÃS')
        for o in rel['orfas']:
            if o.get('tipo') == 'tese':
                # Órfã Bradesco (por tese)
                linhas.append(
                    f'- **BRADESCO** · tese `{o.get("tese","")}` está no kit '
                    f'(`{o.get("pasta_rel_kit","")}/{o.get("arquivo_no_kit","")}`) '
                    f'mas NÃO há subpasta-tese de ação na raiz do cliente.'
                )
            else:
                # Órfã NC (por contrato)
                prox = ''
                if o.get('proximidade_pasta'):
                    pp = o['proximidade_pasta']
                    prox = f' ⚠ Possível typo: pasta tem `{pp.get("contrato","")}` (parecido — conferir)'
                pag = f'Pág. {o.get("pagina","?")}: ' if o.get('pagina') else ''
                linhas.append(
                    f'- {pag}**{o.get("banco","?")}** · contrato `{o.get("contrato","")}` '
                    f'(bruto: `{o.get("contrato_bruto","")}`){prox}'
                )
        linhas.append('')

    if rel.get('duplicatas_mesmo_banco'):
        linhas.append('## ⚠ Bancos com múltiplas procurações no PDF')
        for d in rel['duplicatas_mesmo_banco']:
            linhas.append(
                f'- **{d["banco"]}**: {d["qtd_no_pdf"]} procurações no PDF '
                f'(`{d["contratos_no_pdf"]}`) vs {d["qtd_em_pastas"]} pastas '
                f'(`{d["contratos_em_pastas"]}`)'
            )
        linhas.append('')

    if rel.get('extras'):
        linhas.append('## ℹ️ Procurações em pasta sem correspondência no PDF')
        for e in rel['extras']:
            linhas.append(
                f'- `{e["pasta_rel"]}/{e["arquivo"]}` (banco {e["banco"]}, '
                f'contrato `{e["contrato"]}`)'
            )
        linhas.append('')

    if rel.get('paginas_sem_texto'):
        linhas.append('## ⚠ Páginas do PDF sem text-layer (precisam OCR)')
        for p in rel['paginas_sem_texto']:
            linhas.append(f'- Pág. {p}')
        linhas.append('')

    linhas.append('## Detalhamento — procurações detectadas no PDF')
    for p in rel.get('procuracoes_pdf', []):
        linhas.append(
            f'- Pág. {p["pagina"]}: {p["banco"]} · contrato `{p["contrato"]}` '
            f'(bruto: `{p.get("contrato_bruto","")}`)'
        )
    linhas.append('')
    linhas.append('## Detalhamento — procurações em pastas-banco')
    for p in rel.get('procuracoes_pastas', []):
        linhas.append(
            f'- `{p["pasta_rel"]}/{p["arquivo"]}` → banco {p["banco"]}, '
            f'contrato `{p["contrato"]}`'
        )

    md = '\n'.join(linhas)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)
    return output_path


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print('USO:')
        print('  python auditor_procuracoes_orfas.py <pasta_cliente>')
        print('  python auditor_procuracoes_orfas.py <pasta_cliente> --escopo NC,RMC')
        print('  python auditor_procuracoes_orfas.py <pasta_cliente> --escopo TUDO   (sem filtro)')
        sys.exit(1)
    pasta = sys.argv[1]
    # Parse --escopo flag
    escopo_override = None
    if '--escopo' in sys.argv:
        idx = sys.argv.index('--escopo')
        if idx + 1 < len(sys.argv):
            valor = sys.argv[idx + 1].upper()
            if valor == 'TUDO' or valor == 'ALL':
                escopo_override = set()  # vazio = sem filtro (mostra tudo)
                # Mas vazio também = auto-detecta — preciso sinal explícito
                # Usar valor sentinela 'TODOS':
                escopo_override = {'NC', 'RMC', 'RCC', 'BRADESCO'}
            else:
                escopo_override = set(v.strip() for v in valor.split(','))
    rel = auditar_cliente(pasta, escopo_override=escopo_override)
    if 'erro' in rel:
        print(f'ERRO: {rel["erro"]}')
        print(f'  {rel.get("sugestao", "")}')
        sys.exit(2)
    out = gerar_relatorio_md(rel)
    print(f'Relatório: {out}')
    print()
    print(f'Procurações no PDF: {len(rel["procuracoes_pdf"])}')
    print(f'Procurações em pastas: {len(rel["procuracoes_pastas"])}')
    print(f'Escopo detectado: {rel.get("escopo_detectado") or "(vazio — sem filtro)"} '
          f'(origem: {rel.get("origem_escopo")})')
    if rel.get('pastas_indicadoras_escopo'):
        print(f'  Pastas que indicaram o escopo: {rel["pastas_indicadoras_escopo"]}')
    print()
    print(f'ÓRFÃS NO ESCOPO: {len(rel["orfas"])}')
    for o in rel['orfas']:
        if o.get('tipo') == 'tese':
            print(f'  • BRADESCO tese {o.get("tese","?")} — no Kit, sem pasta-tese')
        else:
            print(f'  • pág {o.get("pagina","?")}: {o.get("banco","?")} '
                   f'contrato {o.get("contrato","")}')
    if rel.get('orfas_fora_escopo'):
        print()
        print(f'PROCURAÇÕES FORA DO ESCOPO ATUAL: {len(rel["orfas_fora_escopo"])} '
              f'(informativo — verificar se já processadas antes)')
        for o in rel['orfas_fora_escopo']:
            if o.get('tipo') == 'tese':
                print(f'  • BRADESCO tese {o.get("tese","?")}')
            else:
                print(f'  • {o.get("banco","?")} contrato {o.get("contrato","")}')
    if rel.get('paginas_sem_texto'):
        print(f'Páginas sem text-layer (precisam OCR): {rel["paginas_sem_texto"]}')


if __name__ == '__main__':
    main()
