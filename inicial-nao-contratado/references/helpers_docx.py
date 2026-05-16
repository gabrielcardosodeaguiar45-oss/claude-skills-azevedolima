"""
Helpers de manipulação DOCX para a skill inicial-bradesco.

Funções principais:
- forcar_cambria_global(): aplica Cambria no theme + rPrDefault + estilos custom
- substituir_in_run(p, mapa): substituição run-aware preservando rPr de origem
- set_paragrafo_1run / set_paragrafo_2runs: reescreve paragrafo
- processar_paragrafo(p, dados): aplica TODAS substituições de placeholders
  com formatação adequada (grifo amarelo, formato de rubrica, omissão de opcionais)
- aplicar_template(template_path, dados, dst_path): pipeline completo
"""
import os, re, shutil, zipfile, copy
from lxml import etree

NSURI = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W = '{' + NSURI + '}'
XMLSPC = '{http://www.w3.org/XML/1998/namespace}space'

# ============================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================

# Placeholders OPCIONAIS: se valor vazio, omitir limpamente (apaga vírgula adjacente)
OPCIONAIS = {
    'estado_civil', 'profissao', 'rg', 'orgao_expedidor',
    'orgao_expedidor_prefixo',
    # Renda nunca é opcional — quando faltar, deixa [A CONFIRMAR] explicito
}

# Placeholders que recebem formatação especial de RUBRICA:
# CAIXA ALTA + bold + italic + underline + amarelo
RUBRICA_FORMATADA = {
    'titulo',                  # tarifas — junção de TODAS rubricas
    'rubrica_curta',           # mora/encargo Title Case
    'rubrica_curta_caps',      # CAPS — mora/encargo/aplic/pgeletron
    'rubrica_completa',        # mora.docx Title Case (subtitulo)
    'rubrica_completa_caps',   # mora.docx CAPS (jurisprudência)
}

# Placeholders que mantêm rStyle "2TtuloChar" (Segoe UI Bold) — destaque visual
DESTAQUE_NOME = {
    'nome_completo',   # autor (qualificação)
    'nome_terceiro',   # PG ELETRON — nome do terceiro réu
}

# Estilos de CORPO (forçar Cambria) — somente texto corrido, listas e citações.
# Não inclui títulos/subtítulos: esses preservam Segoe UI / Franklin Gothic
# do modelo original do escritório.
ESTILOS_CORPO = [
    'Normal',
    '1Pargrafo', '1PargrafoChar',
    'CORPOHOMERO', 'CORPOHOMEROChar',
    '5Listaalfabtica', '5ListaalfabticaChar',
    'PargrafodaLista', 'PargrafodaListaChar',
    'Estilo1', 'Estilo1Char',
    '4Citao', '4CitaoChar',
    'citacao',
    'Corpodetexto', 'CorpodetextoChar', 'BodyTextChar',
]

# Estilos de TÍTULO/SUBTÍTULO — NUNCA forçar Cambria.
# Mantêm Segoe UI / Segoe UI Semibold / Franklin Gothic do modelo.
ESTILOS_TITULO_PRESERVAR = {
    '2Ttulo', '2TtuloChar',
    '3Subttulo', '3SubttuloChar',
    '31Subttulointermedirio', '31SubttulointermedirioChar',
    '31Subttulosecundrio',
    'Ttulo', 'Ttulo1', 'Ttulo2', 'Ttulo3', 'Ttulo4', 'Ttulo5',
}

# Mantido para compatibilidade — agora é apenas alias dos estilos de corpo
ESTILOS_CUSTOM = ESTILOS_CORPO


# ============================================================
# CAMBRIA GLOBAL
# ============================================================
def forcar_cambria_global(buf):
    """Aplica Cambria APENAS nos estilos de CORPO + rPrDefault + theme1.
    PRESERVA fontes dos estilos de TÍTULO/SUBTÍTULO (Segoe UI, Franklin Gothic, etc.)
    `buf` é dict {nome_arquivo_no_zip: bytes}. Modifica in-place.

    REGRA CRÍTICA: o modelo do escritório usa Segoe UI nos títulos e Cambria
    no corpo. NÃO sobrescrever os títulos.
    """
    if 'word/theme/theme1.xml' in buf:
        tx = buf['word/theme/theme1.xml'].decode('utf-8')
        # NÃO mexer em majorFont (usado por títulos) — apenas minorFont (corpo)
        tx = re.sub(r'(<a:minorFont>\s*<a:latin typeface=)"[^"]+"', r'\1"Cambria"', tx, count=1)
        buf['word/theme/theme1.xml'] = tx.encode('utf-8')

    styles = buf['word/styles.xml'].decode('utf-8')

    # rPrDefault → Cambria (afeta corpo padrão, não estilos com fonte explícita)
    def fix_default(m):
        bloco = m.group(0)
        return re.sub(r'<w:rFonts[^/]*/>',
                      '<w:rFonts w:ascii="Cambria" w:eastAsia="Cambria" w:hAnsi="Cambria" w:cs="Cambria"/>',
                      bloco, count=1)
    styles = re.sub(r'<w:rPrDefault>.*?</w:rPrDefault>', fix_default, styles, count=1, flags=re.DOTALL)

    # Substituição cega Sitka/Calibri → Cambria.
    # Antes de aplicar, isolar os estilos de TÍTULO para não trocar suas fontes
    # (mesmo sendo Segoe UI, hoje não estão em Sitka/Calibri, mas garantimos).
    # A trocas afeta só "Sitka Text" e '"Calibri"' literais — segura.
    styles = styles.replace('Sitka Text', 'Cambria').replace('"Calibri"', '"Cambria"')

    # Aplica Cambria APENAS nos estilos de CORPO
    for sid in ESTILOS_CORPO:
        if sid in ESTILOS_TITULO_PRESERVAR:
            continue  # nunca tocar
        pat = r'(<w:style[^>]*styleId="' + sid + r'"[^>]*>(?:(?!</w:style>).)*?</w:style>)'
        def fix_estilo(m):
            bloco = m.group(0)
            rf_m = re.search(r'<w:rFonts[^/]*/>', bloco)
            if rf_m:
                return bloco.replace(rf_m.group(0), '<w:rFonts w:ascii="Cambria" w:hAnsi="Cambria" w:cs="Cambria"/>', 1)
            rpr_m = re.search(r'<w:rPr>', bloco)
            if rpr_m:
                return bloco[:rpr_m.end()] + '<w:rFonts w:ascii="Cambria" w:hAnsi="Cambria" w:cs="Cambria"/>' + bloco[rpr_m.end():]
            return bloco.replace('</w:style>', '<w:rPr><w:rFonts w:ascii="Cambria" w:hAnsi="Cambria" w:cs="Cambria"/></w:rPr></w:style>', 1)
        styles = re.sub(pat, fix_estilo, styles, count=1, flags=re.DOTALL)

    buf['word/styles.xml'] = styles.encode('utf-8')

    # Demais XMLs: troca Sitka/Calibri inline (NÃO mexe em Segoe UI)
    for n in ['word/document.xml', 'word/numbering.xml', 'word/footnotes.xml',
              'word/header1.xml', 'word/header2.xml', 'word/header3.xml',
              'word/footer1.xml', 'word/footer2.xml']:
        if n not in buf:
            continue
        try:
            x = buf[n].decode('utf-8')
            x = x.replace('Sitka Text', 'Cambria').replace('"Calibri"', '"Cambria"')
            buf[n] = x.encode('utf-8')
        except UnicodeDecodeError:
            pass


# ============================================================
# HELPERS LXML
# ============================================================
def get_text(p):
    """Texto plain de um <w:p>."""
    return ''.join(t.text or '' for t in p.iter(W + 't'))


def primeiro_rpr(p):
    """Devolve cópia do <w:rPr> do primeiro <w:r> do parágrafo."""
    for r in p.iter(W + 'r'):
        rpr = r.find(W + 'rPr')
        if rpr is not None:
            return copy.deepcopy(rpr)
    return None


def add_highlight(rpr_elem):
    """Adiciona <w:highlight w:val='yellow'/> ao rPr (remove existente antes)."""
    if rpr_elem is None:
        return
    for h in rpr_elem.findall(W + 'highlight'):
        rpr_elem.remove(h)
    h = etree.SubElement(rpr_elem, W + 'highlight')
    h.set(W + 'val', 'yellow')


def add_rubrica_formato(rpr_elem):
    """Aplica formato completo de RUBRICA: bold + italic + underline + amarelo."""
    if rpr_elem is None:
        return
    for tag in ('b', 'bCs', 'i', 'iCs', 'u', 'highlight'):
        for el in rpr_elem.findall(W + tag):
            rpr_elem.remove(el)
    etree.SubElement(rpr_elem, W + 'b')
    etree.SubElement(rpr_elem, W + 'bCs')
    etree.SubElement(rpr_elem, W + 'i')
    etree.SubElement(rpr_elem, W + 'iCs')
    u = etree.SubElement(rpr_elem, W + 'u')
    u.set(W + 'val', 'single')
    h = etree.SubElement(rpr_elem, W + 'highlight')
    h.set(W + 'val', 'yellow')


def remove_caps_destaque(rpr_elem):
    """Remove <w:caps/> e <w:rStyle val='2TtuloChar'/> — chamado quando a substituição
    não é o nome em destaque (evita herdar Segoe UI Bold para outros campos)."""
    if rpr_elem is None:
        return
    for c in rpr_elem.findall(W + 'caps'):
        rpr_elem.remove(c)
    for s in rpr_elem.findall(W + 'rStyle'):
        if s.get(W + 'val') in ('2TtuloChar', '2TtuloCharChar'):
            rpr_elem.remove(s)


def set_paragrafo_1run(p, texto, rpr=None):
    """Reescreve paragrafo com 1 run."""
    for child in list(p):
        if child.tag != W + 'pPr':
            p.remove(child)
    r = etree.SubElement(p, W + 'r')
    if rpr is not None:
        r.append(rpr)
    t = etree.SubElement(r, W + 't')
    t.text = texto
    t.set(XMLSPC, 'preserve')


def set_paragrafo_2runs(p, run1_text, run1_rpr, run2_text, run2_rpr):
    """Reescreve paragrafo com 2 runs (ex.: nome em destaque + resto neutro)."""
    for child in list(p):
        if child.tag != W + 'pPr':
            p.remove(child)
    if run1_text:
        r1 = etree.SubElement(p, W + 'r')
        if run1_rpr is not None:
            r1.append(run1_rpr)
        t1 = etree.SubElement(r1, W + 't')
        t1.text = run1_text
        t1.set(XMLSPC, 'preserve')
    if run2_text:
        r2 = etree.SubElement(p, W + 'r')
        if run2_rpr is not None:
            r2.append(run2_rpr)
        t2 = etree.SubElement(r2, W + 't')
        t2.text = run2_text
        t2.set(XMLSPC, 'preserve')


def substituir_in_run(p, mapa, grifo=True):
    """Substitui ocorrências de chave por valor em todos os runs do parágrafo,
    preservando rPr de origem (run-aware). Mapa: {string_a_buscar: string_substituta}.

    Args:
        p: elemento <w:p> do parágrafo
        mapa: dict {string_a_buscar: string_substituta}
        grifo: se True (default), aplica grifo amarelo (<w:highlight val="yellow"/>)
               nos caracteres SUBSTITUÍDOS. Permite revisão visual rápida das
               alterações da skill.

    Conserto do bug do loop infinito (quando NOVO contém ANTIGO): usamos
    flag por caractere `inserido` para não reprocessar substituições.

    Retorna True se alguma substituição foi feita."""
    # Cada elemento: [char, rpr, foi_inserido]
    plain_chars = []
    for r in p.findall('.//' + W + 'r'):
        rpr = r.find(W + 'rPr')
        for t in r.findall(W + 't'):
            for ch in (t.text or ''):
                plain_chars.append([ch, rpr, False])
    plain = ''.join(c[0] for c in plain_chars)
    if not any(k in plain for k in mapa):
        return False

    for k, v in mapa.items():
        # Procurar SOMENTE em segmentos que NÃO foram inseridos (evita loop)
        while True:
            # Reconstruir string e mapa de índices "originais"
            indices_originais = [idx for idx, c in enumerate(plain_chars) if not c[2]]
            atual = ''.join(plain_chars[idx][0] for idx in indices_originais)
            i_atual = atual.find(k)
            if i_atual < 0:
                break
            # Mapear de volta para os índices reais
            i_real_ini = indices_originais[i_atual]
            i_real_fim = indices_originais[i_atual + len(k) - 1] + 1
            rpr_origem = plain_chars[i_real_ini][1] if i_real_ini < len(plain_chars) else None
            del plain_chars[i_real_ini:i_real_fim]
            novos = [[ch, rpr_origem, True] for ch in v]  # marca como "inserido"
            plain_chars[i_real_ini:i_real_ini] = novos

    for child in list(p):
        if child.tag != W + 'pPr':
            p.remove(child)

    if not plain_chars:
        return True

    # Agrupar por (rpr, inserido). Caracteres consecutivos com mesmo rpr E
    # mesmo flag de inserção viram 1 run. Quando o flag é "inserido" e
    # grifo=True, adicionamos highlight amarelo no run.
    grupos = []
    grupo_chars = [plain_chars[0][0]]
    grupo_rpr = plain_chars[0][1]
    grupo_inserido = plain_chars[0][2]
    for ch, rpr, inserido in plain_chars[1:]:
        if rpr is grupo_rpr and inserido == grupo_inserido:
            grupo_chars.append(ch)
        else:
            grupos.append((''.join(grupo_chars), grupo_rpr, grupo_inserido))
            grupo_chars = [ch]
            grupo_rpr = rpr
            grupo_inserido = inserido
    grupos.append((''.join(grupo_chars), grupo_rpr, grupo_inserido))

    for txt, rpr, inserido in grupos:
        if not txt:
            continue
        r = etree.SubElement(p, W + 'r')
        if rpr is not None:
            rpr_novo = copy.deepcopy(rpr)
            r.append(rpr_novo)
        else:
            rpr_novo = None
        # Se grifo=True e o segmento foi inserido, aplicar highlight amarelo
        if grifo and inserido:
            if rpr_novo is None:
                rpr_novo = etree.SubElement(r, W + 'rPr')
                # rPr precisa ser o primeiro filho de r — reposicionar
                r.remove(rpr_novo)
                r.insert(0, rpr_novo)
            # Adicionar/substituir highlight amarelo
            existing_highlight = rpr_novo.find(W + 'highlight')
            if existing_highlight is None:
                hl = etree.SubElement(rpr_novo, W + 'highlight')
                hl.set(W + 'val', 'yellow')
            else:
                existing_highlight.set(W + 'val', 'yellow')
        t = etree.SubElement(r, W + 't')
        t.text = txt
        t.set(XMLSPC, 'preserve')
    return True


# ============================================================
# PROCESSAMENTO DE PARÁGRAFO COM PLACEHOLDERS
# ============================================================
def processar_paragrafo(p, dados):
    """Aplica todas substituições de placeholders {{xxx}} em um parágrafo:
    - Omite limpamente OPCIONAIS vazios (com vírgula adjacente)
    - Aplica grifo amarelo nos campos modificados
    - Aplica formato de RUBRICA (caps+bold+italic+underline+amarelo) em rubricas
    - Mantém rStyle 2TtuloChar (Segoe UI Bold) apenas em nome_completo e nome_terceiro
    Retorna True se modificou."""
    plain_chars = []
    for r in p.findall('.//' + W + 'r'):
        rpr = r.find(W + 'rPr')
        for t in r.findall(W + 't'):
            for ch in (t.text or ''):
                # 4 flags: char, rpr, foi_modificado, eh_rubrica
                plain_chars.append([ch, rpr, False, False])
    plain = ''.join(c[0] for c in plain_chars)
    if '{{' not in plain:
        return False

    # Etapa 1: omissão de OPCIONAIS vazios
    for k in OPCIONAIS:
        if dados.get(k, '') != '':
            continue
        while True:
            atual = ''.join(c[0] for c in plain_chars)
            ph = '{{' + k + '}}'
            i = atual.find(ph)
            if i < 0:
                break
            j = i + len(ph)
            antes2 = atual[max(0, i-2):i]
            depois2 = atual[j:min(len(atual), j+2)]
            consumir_antes = 0
            consumir_depois = 0
            if antes2.endswith(', '):
                consumir_antes = 2
            elif depois2 == ', ':
                consumir_depois = 2
            elif depois2.startswith(' '):
                consumir_depois = 1
            del plain_chars[i-consumir_antes: j+consumir_depois]

    # Etapa 2: substituir placeholders restantes.
    #
    # CORREÇÃO 2026-05-10 (E15 — herdado de inicial-bradesco):
    # lookup case-insensitive + skip-on-unknown.
    # Bug original: o template uniformizado usa {{NOME_COMPLETO}} (UPPERCASE)
    # e o dict entrega 'nome_completo' (lowercase). A regra antiga `if nome
    # not in dados: break` interrompia o parágrafo INTEIRO no primeiro
    # placeholder não encontrado, deixando NOME, nacionalidade, profissão,
    # CPF, RG e endereço crus na inicial. Agora montamos um índice
    # case-insensitive e, quando o token não está no dict, mascaramos com
    # sentinels NÃO-MATCHÁVEIS para continuar varrendo os próximos
    # placeholders. No fim, restauramos para a forma {{xxx}} (e o
    # aplicar_template detecta como residual, fail-fast).
    SENT_OPEN = 'PHL'
    SENT_CLOSE = 'PHR'
    dados_ci = {k.lower(): (k, v) for k, v in dados.items()}

    while True:
        atual = ''.join(c[0] for c in plain_chars)
        m = re.search(r'\{\{([^{}\s][^{}]*?)\}\}', atual)
        if not m:
            break
        nome = m.group(1)
        i, j = m.span()
        match_ci = dados_ci.get(nome.lower())
        if match_ci is None:
            del plain_chars[i:j]
            mask = SENT_OPEN + nome + SENT_CLOSE
            novos = [[ch, None, False, False] for ch in mask]
            plain_chars[i:i] = novos
            continue
        valor = str(match_ci[1])
        rpr_origem = plain_chars[i][1] if i < len(plain_chars) else None
        novo_rpr = copy.deepcopy(rpr_origem) if rpr_origem is not None else None
        chave_canonica = match_ci[0]
        if chave_canonica not in DESTAQUE_NOME and nome not in DESTAQUE_NOME:
            remove_caps_destaque(novo_rpr)
        is_rubrica = chave_canonica in RUBRICA_FORMATADA or nome in RUBRICA_FORMATADA
        del plain_chars[i:j]
        novos = [[ch, novo_rpr, True, is_rubrica] for ch in valor]
        plain_chars[i:i] = novos

    # Restaurar sentinels para a forma {{xxx}} para que aplicar_template detecte
    while True:
        atual = ''.join(c[0] for c in plain_chars)
        m = re.search(re.escape(SENT_OPEN) + r'(.+?)' + re.escape(SENT_CLOSE), atual)
        if not m:
            break
        i, j = m.span()
        nome = m.group(1)
        del plain_chars[i:j]
        novos = [[ch, None, True, False] for ch in '{{' + nome + '}}']
        plain_chars[i:i] = novos

    # Etapa 3: reconstruir runs
    for child in list(p):
        if child.tag != W + 'pPr':
            p.remove(child)
    if not plain_chars:
        return True

    grupos = []
    grupo = [plain_chars[0][0]]
    chave = (id(plain_chars[0][1]), plain_chars[0][2], plain_chars[0][3])
    rpr_ref = plain_chars[0][1]
    hl_ref = plain_chars[0][2]
    rub_ref = plain_chars[0][3]
    for ch, rpr, hl, rub in plain_chars[1:]:
        if (id(rpr), hl, rub) == chave:
            grupo.append(ch)
        else:
            grupos.append((''.join(grupo), rpr_ref, hl_ref, rub_ref))
            grupo = [ch]
            chave = (id(rpr), hl, rub)
            rpr_ref = rpr
            hl_ref = hl
            rub_ref = rub
    grupos.append((''.join(grupo), rpr_ref, hl_ref, rub_ref))

    for txt, rpr_elem, hl, rub in grupos:
        if not txt:
            continue
        r = etree.SubElement(p, W + 'r')
        if rpr_elem is not None:
            r.append(copy.deepcopy(rpr_elem))
        rpr_local = r.find(W + 'rPr')
        if rub:
            if rpr_local is None:
                rpr_local = etree.SubElement(r, W + 'rPr')
            add_rubrica_formato(rpr_local)
        elif hl:
            if rpr_local is None:
                rpr_local = etree.SubElement(r, W + 'rPr')
            add_highlight(rpr_local)
        t = etree.SubElement(r, W + 't')
        t.text = txt
        t.set(XMLSPC, 'preserve')
    return True


# ============================================================
# PIPELINE DE APLICAÇÃO
# ============================================================

# Padrão de "Cédula de Identidade nº " que ficou órfão quando RG (e órgão
# expedidor) foram OPCIONAIS omitidos. Texto template-fixo do escritório,
# sobrevive à omissão. Removemos in-place no pós-processamento.
RE_ORFAO_CEDULA = re.compile(
    r'C[eé]dula de Identidade n[º°o]?\s*,?\s*(?=residente|,)'
)


def pos_processar_documento(root):
    """Limpeza pós-substituição que NÃO mexe na rPr de nenhum run.

    (i)  Remove órfão "Cédula de Identidade nº " quando RG é OPCIONAL omitido.
    (ii) Deduplica runs adjacentes com mesmo texto separados apenas por '; '
         (evita duplicação de rubrica em templates com N placeholders iguais).
    (iii) Limpeza fina de pontuação (vírgulas duplas, espaço pós-aspas).

    Idêntico ao mesmo helper em inicial-bradesco — manter sincronizado.
    """
    for tt in root.iter(W + 't'):
        txt = tt.text or ''
        if 'Cédula de Identidade' not in txt and 'Cedula de Identidade' not in txt:
            continue
        novo = RE_ORFAO_CEDULA.sub('', txt)
        if novo != txt:
            tt.text = novo

    for p in root.iter(W + 'p'):
        runs = list(p.iter(W + 'r'))
        if len(runs) < 3:
            continue

        def run_text(r):
            return ''.join((t.text or '') for t in r.iter(W + 't'))

        i = 0
        a_remover = []
        while i < len(runs) - 2:
            t_atual = run_text(runs[i]).strip()
            if not t_atual or len(t_atual) < 6:
                i += 1
                continue
            j = i + 1
            ultima_dup = None
            while j < len(runs):
                t_j = run_text(runs[j])
                if re.fullmatch(r'\s*;\s*', t_j):
                    j += 1
                    continue
                if run_text(runs[j]).strip() == t_atual:
                    ultima_dup = j
                    j += 1
                    continue
                break
            if ultima_dup is not None:
                for k in range(i + 1, ultima_dup + 1):
                    a_remover.append(runs[k])
                i = ultima_dup + 1
            else:
                i += 1
        for r in a_remover:
            parent = r.getparent()
            if parent is not None:
                parent.remove(r)

    for tt in root.iter(W + 't'):
        txt = tt.text or ''
        novo = re.sub(r',\s*,', ',', txt)
        novo = re.sub(r'  +', ' ', novo)
        novo = re.sub(r'“\s+', '“', novo)
        if novo != txt:
            tt.text = novo


class PlaceholdersResiduaisError(RuntimeError):
    """Levantada por aplicar_template quando o DOCX gerado ainda contém
    placeholders {{...}} não substituídos. Em modo strict (padrão) isso
    impede que uma inicial incompleta seja entregue ao usuário ou ao
    pipeline.
    """

    def __init__(self, residuais, dst_path):
        self.residuais = list(residuais)
        self.dst_path = dst_path
        super().__init__(
            f'INICIAL INCOMPLETA — placeholders {{{{...}}}} restaram em '
            f'{os.path.basename(dst_path)}: {self.residuais}. '
            f'Causa típica: o dict não cobre o token, '
            f'ou o template usou um nome novo que ainda não foi mapeado em '
            f'_pipeline_caso.montar_dados_padrao. Adicione o(s) token(s) ao '
            f'dict OU registre como OPCIONAIS em helpers_docx.py.'
        )


def aplicar_template(template_path, dados, dst_path, strict=True):
    """Pipeline completo: copia template, aplica substituições, salva.

    Args:
        template_path: caminho do template no Obsidian (vault)
        dados: dict {placeholder_name: value} — lookup é case-insensitive,
            então tanto ``{{NOME_COMPLETO}}`` quanto ``{{nome_completo}}``
            casam com a chave ``nome_completo`` do dict.
        dst_path: onde salvar o DOCX gerado
        strict: se True (padrão), LEVANTA :class:`PlaceholdersResiduaisError`
            quando sobrar qualquer ``{{xxx}}`` no DOCX final.

    Returns:
        dict com {'modificados': N, 'residuais': [...]}
    """
    shutil.copy(template_path, dst_path)
    with zipfile.ZipFile(dst_path, 'r') as z:
        nomes = z.namelist()
        buf = {n: z.read(n) for n in nomes}

    # (Re)forçar Cambria como segurança
    forcar_cambria_global(buf)

    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(buf['word/document.xml'], parser)

    mod = 0
    for p in root.iter(W + 'p'):
        if processar_paragrafo(p, dados):
            mod += 1

    # Pós-processamento limpa artefatos (órfão Cédula, dedup rubrica)
    pos_processar_documento(root)

    buf['word/document.xml'] = etree.tostring(
        root, xml_declaration=True, encoding='UTF-8', standalone=True
    )
    os.remove(dst_path)
    with zipfile.ZipFile(dst_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in nomes:
            z.writestr(n, buf[n])

    # Verifica residuais — varre TODO o XML, não só os parágrafos do corpo
    with zipfile.ZipFile(dst_path, 'r') as z:
        xml_total = z.read('word/document.xml').decode('utf-8')
    residuais = sorted(set(re.findall(r'\{\{([^{}]+)\}\}', xml_total)))

    if residuais and strict:
        # Renomeia o DOCX falho para deixar visualmente óbvio que NÃO pode ser
        # protocolado. Mantém o arquivo (não deleta) para inspeção.
        base, ext = os.path.splitext(dst_path)
        falha_path = base + '_FALHOU_PLACEHOLDERS' + ext
        if os.path.exists(falha_path):
            os.remove(falha_path)
        os.rename(dst_path, falha_path)
        raise PlaceholdersResiduaisError(residuais, falha_path)

    return {'modificados': mod, 'residuais': residuais}


# ============================================================================
# Patch D — Validador pós-DOCX (2026-05-16)
# ----------------------------------------------------------------------------
# Caso paradigma: VILSON DA CRUZ BRASIL / BANRISUL — inicial saiu com
# "no valor de R$ 0,00 (zero reais)", "de um total de , no valor de",
# "[A CONFIRMAR – pendente HISCON]". Os placeholders {{...}} foram substituídos
# (sem PlaceholdersResiduaisError), mas por valores zerados/placeholders.
# Esta varredura PEGA o problema no fim e renomeia o arquivo para
# _FALHOU_VALIDACAO_FINAL antes de devolver erro.
# ============================================================================

class DocxValidacaoFinalError(RuntimeError):
    """Levantada quando o DOCX gerado contém marcas de inicial incompleta:
    R$ 0,00 no contexto de valor de empréstimo/parcela, [A CONFIRMAR],
    competências vazias entre vírgulas, etc."""
    def __init__(self, achados, dst_path):
        self.achados = list(achados)
        self.dst_path = dst_path
        super().__init__(
            f'INICIAL INCOMPLETA — validação pós-DOCX detectou marcas de '
            f'fallback fictício em {os.path.basename(dst_path)}:\n'
            + '\n'.join(f'  • {a}' for a in self.achados)
            + '\n\nCausa típica: contrato sem HISCON real (placeholders '
              'preenchidos com 0,0 / vazio / "[A CONFIRMAR]"). NÃO PROTOCOLE. '
              'Conferir HISCON e refazer geração.'
        )


def validar_docx_gerado(dst_path: str, *, abortar: bool = True) -> list:
    """Varre o DOCX procurando sintomas de inicial incompleta.

    Procura por estes padrões no texto do XML:
      1. 'R$ 0,00'  (valor zerado de empréstimo/parcela/desconto)
      2. '[A CONFIRMAR'
      3. 'pendente HISCON'
      4. 'de um total de , '  (competência vazia entre vírgulas)
      5. 'início de desconto em ,'
      6. 'no valor de , '
      7. 'inclusão em ,'
      8. 'competência , '  (vírgula imediatamente após "competência")

    Se `abortar=True` (padrão), renomeia o arquivo para
    `<base>_FALHOU_VALIDACAO_FINAL<ext>` e levanta DocxValidacaoFinalError.
    Se `abortar=False`, apenas devolve a lista de achados.

    Returns:
        list[str]: lista descritiva dos sintomas encontrados (vazia = OK).
    """
    if not os.path.exists(dst_path):
        return [f'arquivo inexistente: {dst_path}']

    with zipfile.ZipFile(dst_path, 'r') as z:
        xml_total = z.read('word/document.xml').decode('utf-8')

    # Remove tags XML para varrer só o texto visível (evita match em
    # estilos/atributos que contenham 0,00 legitimamente)
    txt = re.sub(r'<[^>]+>', '', xml_total)
    # Normaliza espaços
    txt_normal = re.sub(r'\s+', ' ', txt)

    achados = []
    if 'R$ 0,00' in txt or 'R$0,00' in txt:
        achados.append('valor "R$ 0,00" encontrado no texto (provável fallback fictício)')
    if '[A CONFIRMAR' in txt:
        achados.append('placeholder "[A CONFIRMAR" sobrou no texto final')
    if re.search(r'pendente\s+HISCON', txt, re.IGNORECASE):
        achados.append('"pendente HISCON" sobrou no texto final')
    if re.search(r'de\s+um\s+total\s+de\s*,', txt_normal):
        achados.append('"de um total de ," — qtd_parcelas vazio entre vírgulas')
    if re.search(r'in[ií]cio\s+de\s+desconto\s+em\s*,', txt_normal):
        achados.append('"início de desconto em ," — competência vazia entre vírgulas')
    if re.search(r'no\s+valor\s+de\s*,', txt_normal):
        achados.append('"no valor de ," — valor vazio entre vírgulas')
    if re.search(r'inclus[aã]o\s+em\s*,', txt_normal):
        achados.append('"inclusão em ," — data vazia entre vírgulas')
    if re.search(r'compet[eê]ncia\s*,', txt_normal):
        achados.append('"competência ," — competência vazia entre vírgulas')

    if achados and abortar:
        base, ext = os.path.splitext(dst_path)
        falha_path = base + '_FALHOU_VALIDACAO_FINAL' + ext
        if os.path.exists(falha_path):
            os.remove(falha_path)
        os.rename(dst_path, falha_path)
        raise DocxValidacaoFinalError(achados, falha_path)

    return achados
