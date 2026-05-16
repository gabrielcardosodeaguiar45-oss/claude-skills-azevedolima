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


def substituir_in_run(p, mapa):
    """Substitui ocorrências de chave por valor em todos os runs do parágrafo,
    preservando rPr de origem (run-aware). Mapa: {string_a_buscar: string_substituta}.
    Retorna True se alguma substituição foi feita."""
    plain_chars = []
    for r in p.findall('.//' + W + 'r'):
        rpr = r.find(W + 'rPr')
        for t in r.findall(W + 't'):
            for ch in (t.text or ''):
                plain_chars.append([ch, rpr])
    plain = ''.join(c[0] for c in plain_chars)
    if not any(k in plain for k in mapa):
        return False

    for k, v in mapa.items():
        while True:
            atual = ''.join(c[0] for c in plain_chars)
            i = atual.find(k)
            if i < 0:
                break
            j = i + len(k)
            rpr_origem = plain_chars[i][1] if i < len(plain_chars) else None
            del plain_chars[i:j]
            novos = [[ch, rpr_origem] for ch in v]
            plain_chars[i:i] = novos

    for child in list(p):
        if child.tag != W + 'pPr':
            p.remove(child)

    if not plain_chars:
        return True

    grupos = []
    grupo = [plain_chars[0][0]]
    ref = plain_chars[0][1]
    for ch, rpr in plain_chars[1:]:
        if rpr is ref:
            grupo.append(ch)
        else:
            grupos.append((''.join(grupo), ref))
            grupo = [ch]
            ref = rpr
    grupos.append((''.join(grupo), ref))

    for txt, rpr in grupos:
        if not txt:
            continue
        r = etree.SubElement(p, W + 'r')
        if rpr is not None:
            r.append(copy.deepcopy(rpr))
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
    # CORREÇÃO 2026-05-10: lookup case-insensitive + skip-on-unknown.
    # Bug anterior: o template usa {{NOME_COMPLETO}} (UPPERCASE) e o dict
    # entrega 'nome_completo' (lowercase). A regra antiga `if nome not in dados:
    # break` interrompia o parágrafo INTEIRO no primeiro placeholder não
    # encontrado, deixando NOME, nacionalidade, profissão, CPF, RG e endereço
    # crus na inicial. Agora montamos um índice case-insensitive e, quando o
    # token não está no dict, mascaramos com sentinels NÃO-MATCHÁVEIS para
    # continuar varrendo os próximos placeholders. No fim, restauramos os
    # placeholders desconhecidos para a forma {{xxx}} (e o aplicar_template
    # detecta como residual, fail-fast).
    SENT_OPEN = 'PHL'   # caracteres da PUA — não aparecem no acervo
    SENT_CLOSE = 'PHR'
    dados_ci = {k.lower(): (k, v) for k, v in dados.items()}

    while True:
        atual = ''.join(c[0] for c in plain_chars)
        m = re.search(r'\{\{([^{}\s][^{}]*?)\}\}', atual)
        if not m:
            break
        nome = m.group(1)
        i, j = m.span()
        # Lookup case-insensitive para sobreviver a {{NOME_COMPLETO}} vs nome_completo
        match_ci = dados_ci.get(nome.lower())
        if match_ci is None:
            # Token desconhecido: mascarar com sentinel para continuar varrendo
            # os demais placeholders neste parágrafo, sem perder a referência
            # original (será restaurada como {{nome}} no fim e capturada como
            # residual pelo aplicar_template em modo strict).
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
# expedidor) foram OPCIONAIS omitidos. Esse texto é template-fixo no
# escritório, então sobrevive à omissão. Removemos in-place.
RE_ORFAO_CEDULA = re.compile(
    r'C[eé]dula de Identidade n[º°o]?\s*,?\s*(?=residente|,)'
)


def pos_processar_documento(root):
    """Limpeza pós-substituição que NÃO mexe na rPr de nenhum run.

    Resolve dois artefatos recorrentes:

    (i) Órfão "Cédula de Identidade nº " quando o RG é OPCIONAL omitido. O
        texto-fixo do template "Cédula de Identidade nº " sobrevive porque
        a omissão de OPCIONAIS no `processar_paragrafo` só consome a vírgula
        adjacente, não a frase introdutória. Aqui detectamos esse padrão
        e removemos só o texto órfão dentro do <w:t> que o contém.

    (ii) Duplicação de rubrica: o template MoraEncargo, por exemplo, tem
        3 ocorrências de {{rubrica_encargo_canonica_caps}} (pensado para 3
        encargos distintos). Quando todos viram o mesmo valor (ex.: 'ENC LIM
        CRÉDITO'), o documento sai com "ENC LIM CRÉDITO; ENC LIM CRÉDITO;
        ENC LIM CRÉDITO; MORA CRED PESS". Aqui detectamos runs adjacentes
        com o mesmo texto separados apenas por '; ' e removemos os
        duplicados, mantendo o primeiro e seu separador.
    """
    # (i) órfão Cédula de Identidade nº
    for tt in root.iter(W + 't'):
        txt = tt.text or ''
        if 'Cédula de Identidade' not in txt and 'Cedula de Identidade' not in txt:
            continue
        novo = RE_ORFAO_CEDULA.sub('', txt)
        if novo != txt:
            tt.text = novo

    # (ii) Dedup de runs adjacentes com mesmo texto (rubricas duplicadas)
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

    # (iii) Limpeza fina de pontuação dentro de cada <w:t> (vírgulas duplas
    # e espaço extra após abre-aspas).
    for tt in root.iter(W + 't'):
        txt = tt.text or ''
        novo = re.sub(r',\s*,', ',', txt)
        novo = re.sub(r'  +', ' ', novo)
        novo = re.sub(r'“\s+', '“', novo)
        if novo != txt:
            tt.text = novo


# ============================================================
# Endereço composto do escritório (matriz Joaçaba/SC + unidade de apoio)
# ============================================================
# Regex que casa as VARIAÇÕES do trecho hardcoded nos 6 templates Bradesco:
#   - "com unidade na (Rua )?Travessa Michiles, (SN|S/N|sn|s/n), Centro,
#      no município de Maués(/|-)AM, CEP 69(.)?195-000"
# Tolerante a capitalização (SN/sn), barra ou hífen na separação Maués/AM,
# e ponto opcional no CEP. Substitui o trecho inteiro pelo formato canônico.
_RE_TRECHO_ENDERECO_OLD_BRADESCO = re.compile(
    r'com unidade na (?:Rua )?Travessa Michiles, [sS]/?[nN], Centro, '
    r'no município de Mau[ée]s[/-]AM, CEP 69\.?195-?000',
    re.UNICODE,
)


def inserir_endereco_composto_se_faltando(root, uf: str) -> int:
    """Substitui o trecho hardcoded dos templates Bradesco (`com unidade na
    Rua Travessa Michiles, ..., Maués/AM, CEP 69.195-000`) pelo formato
    canônico do escritório: matriz Joaçaba/SC SEMPRE primeiro + unidade de
    apoio da UF do cliente. Para UFs sem apoio confirmado, fica só a matriz
    — nunca placeholder visível.

    Lê o endereço composto do cadastro central
    `skills/_common/escritorios_cadastro.py:montar_endereco_escritorio_completo`,
    fonte única de verdade compartilhada com notificacao-extrajudicial e
    inicial-nao-contratado.

    Idempotente: se o parágrafo já contém "Frei Rogério" (matriz), não toca.

    Retorna o número de parágrafos atualizados.
    """
    # Import preguiçoso para não obrigar todas as importações da skill
    # a conhecerem o _common.
    import sys, os
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    common_dir = os.path.normpath(os.path.join(skill_dir, '..', '..', '_common'))
    if common_dir not in sys.path:
        sys.path.insert(0, common_dir)
    try:
        from escritorios_cadastro import montar_endereco_escritorio_completo
    except ImportError as e:
        raise ImportError(
            f'Cadastro central não encontrado em skills/_common/escritorios_cadastro.py: {e}. '
            f'Verifique se a pasta _common/ existe ao lado de inicial-bradesco/.'
        ) from e

    novo_endereco_composto = montar_endereco_escritorio_completo(uf)
    novo_trecho = f'com escritório na {novo_endereco_composto}'

    feitos = 0
    for p in root.iter(W + 'p'):
        texto = ''.join((t.text or '') for t in p.iter(W + 't'))
        if 'Frei Rogério' in texto:
            continue
        m = _RE_TRECHO_ENDERECO_OLD_BRADESCO.search(texto)
        if not m:
            continue
        trecho_exato = m.group(0)
        if substituir_in_run(p, {trecho_exato: novo_trecho}):
            feitos += 1
    return feitos


class PlaceholdersResiduaisError(RuntimeError):
    """Levantada por aplicar_template quando o DOCX gerado ainda contém
    placeholders {{...}} não substituídos. Em modo strict (padrão) isso
    impede que uma inicial incompleta seja entregue ao usuário ou ao
    pipeline. Use ``strict=False`` apenas se o chamador for absolutamente
    capaz de revisar manualmente os residuais antes do protocolo.
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
            quando sobrar qualquer ``{{xxx}}`` no DOCX final. Esse é o
            comportamento correto — o erro evita que iniciais com bloco de
            qualificação cru (NOME, CPF, RG, endereço) cheguem ao protocolo.

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

    # Pós-processamento: limpeza de artefatos que sobram quando OPCIONAIS
    # são omitidos ou quando o template tem N ocorrências repetidas de
    # uma rubrica que vira o mesmo valor. Preserva rPr de cada run.
    pos_processar_documento(root)

    # Endereço composto do escritório: matriz Joaçaba/SC + unidade de apoio
    # da UF do caso. Substitui o trecho hardcoded "com unidade na Rua
    # Travessa Michiles, ..., Maués/AM" dos templates Bradesco. Para UFs sem
    # apoio confirmado retorna só a matriz (sem placeholder visível).
    inserir_endereco_composto_se_faltando(root, dados.get('uf', 'AM'))

    buf['word/document.xml'] = etree.tostring(
        root, xml_declaration=True, encoding='UTF-8', standalone=True
    )
    os.remove(dst_path)
    with zipfile.ZipFile(dst_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in nomes:
            z.writestr(n, buf[n])

    # Verifica residuais — varre TODO o XML, não só os parágrafos do corpo,
    # para pegar também placeholders em headers/footers/tabelas.
    with zipfile.ZipFile(dst_path, 'r') as z:
        xml_total = z.read('word/document.xml').decode('utf-8')
    residuais = sorted(set(re.findall(r'\{\{([^{}]+)\}\}', xml_total)))

    if residuais and strict:
        # Renomeia o DOCX falho para deixar visualmente óbvio que NÃO pode ser
        # protocolado. Mantém o arquivo (não deleta) para que o operador possa
        # inspecionar quais placeholders ficaram crus.
        base, ext = os.path.splitext(dst_path)
        falha_path = base + '_FALHOU_PLACEHOLDERS' + ext
        if os.path.exists(falha_path):
            os.remove(falha_path)
        os.rename(dst_path, falha_path)
        raise PlaceholdersResiduaisError(residuais, falha_path)

    # VALIDADOR PÓS-DOCX (paridade com inicial-nao-contratado, 2026-05-16):
    # detecta R$ 0,00, [A CONFIRMAR, "pendente HISCON", competências/datas
    # vazias entre vírgulas. Se algum dispara, renomeia para
    # *_FALHOU_VALIDACAO_FINAL.docx e levanta DocxValidacaoFinalError.
    # Importa via importlib.util para evitar colisão com helpers_docx
    # local da skill (que tem `validar_docx_gerado` em outra implementação).
    if strict:
        try:
            import importlib.util as _ilu
            _nc_helpers_path = r"C:/Users/gabri/.claude/skills/inicial-nao-contratado/references/helpers_docx.py"
            if os.path.exists(_nc_helpers_path):
                _spec = _ilu.spec_from_file_location("_nc_helpers_docx", _nc_helpers_path)
                _mod = _ilu.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                if hasattr(_mod, 'validar_docx_gerado'):
                    _mod.validar_docx_gerado(dst_path, abortar=True)
        except Exception as _e:
            # Re-levanta se for o erro de validação (queremos travar mesmo)
            from importlib.util import spec_from_file_location as _sfl
            tipo_nome = type(_e).__name__
            if tipo_nome == 'DocxValidacaoFinalError':
                raise
            # Outros erros: registra mas não bloqueia
            print(f"  ⚠ validador pós-DOCX não rodou: {tipo_nome}: {str(_e)[:120]}")

    return {'modificados': mod, 'residuais': residuais}
