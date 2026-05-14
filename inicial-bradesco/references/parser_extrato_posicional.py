"""Parser posicional preciso de extrato bancário Bradesco (text-layer).

Estrutura típica do extrato digital Bradesco:
    DATA (linha n)
      RUBRICA_pt1 (n+1)
      [RUBRICA_pt2] (n+2, opcional — quando descrição quebra em 2 linhas)
      DOCTO (n+x)
      VALOR (n+x+1)  ← débito ou crédito
      SALDO (n+x+2)
    ...próximo lançamento (mesmo dia ou data nova)...

Vantagem sobre `parsear_lancamentos_extrato`:
  - Captura TODOS os lançamentos da página, não só os que casam um único
    padrão de rubrica
  - Reconhece corretamente data + valor + saldo posicionalmente
  - Suporta múltiplos lançamentos no mesmo dia (mesma rubrica) sem confundir

Use quando o extrato tem text-layer (PDF digital baixado do app Bradesco).
Para extratos imagem (escaneados), continuar usando OCR.
"""
import re
from typing import List, Dict, Optional


RE_DATA = re.compile(r'^(\d{2}/\d{2}/\d{4})$')
RE_VALOR = re.compile(r'^\d{1,3}(?:\.\d{3})*,\d{2}$')
RE_DOCTO = re.compile(r'^[A-Za-z0-9]{4,}$')


def parsear_extrato_digital(extrato_path: str) -> List[Dict]:
    """Parsing posicional do extrato com text-layer.

    Retorna lista de {data, descricao, docto, valor, saldo} ordenados
    como aparecem no PDF.

    Se o PDF não tiver text-layer, retorna lista vazia. Use OCR como
    alternativa (`parsear_lancamentos_extrato` em extrator_documentos.py).
    """
    import os
    import fitz
    if not os.path.exists(extrato_path):
        return []
    try:
        doc = fitz.open(extrato_path)
    except Exception:
        return []
    texto = '\n'.join(p.get_text() for p in doc)
    doc.close()
    if len(texto.strip()) < 100:
        return []  # provavelmente PDF imagem; usar OCR

    linhas = [ln.strip() for ln in texto.split('\n')]

    eventos = []
    data_atual = None
    i = 0
    while i < len(linhas):
        ln = linhas[i]
        if RE_DATA.match(ln):
            data_atual = ln
            i += 1
            continue
        if not data_atual or not ln or not ln[0].isalpha():
            i += 1
            continue
        # Coletar descrição (1 ou 2 linhas que começam com letra)
        desc = ln
        j = i + 1
        if j < len(linhas) and linhas[j] and linhas[j][0].isalpha() and not RE_DATA.match(linhas[j]):
            nxt = linhas[j]
            if not RE_VALOR.match(nxt) and not (nxt.isdigit() and len(nxt) >= 4):
                desc = desc + ' ' + nxt
                j += 1
        # Pular linhas vazias
        while j < len(linhas) and not linhas[j]:
            j += 1
        if j >= len(linhas) or not RE_DOCTO.match(linhas[j]):
            i += 1
            continue
        docto = linhas[j]
        # Próxima não-vazia é VALOR
        k = j + 1
        while k < len(linhas) and not linhas[k]:
            k += 1
        if k >= len(linhas) or not RE_VALOR.match(linhas[k]):
            i += 1
            continue
        valor = float(linhas[k].replace('.', '').replace(',', '.'))
        # Próxima é SALDO
        m = k + 1
        while m < len(linhas) and not linhas[m]:
            m += 1
        saldo = linhas[m] if m < len(linhas) and RE_VALOR.match(linhas[m]) else None

        eventos.append({
            'data': data_atual,
            'descricao': desc.strip(),
            'docto': docto,
            'valor': valor,
            'saldo': saldo,
        })
        i = (m + 1) if saldo else (k + 1)
    return eventos


def filtrar_por_palavra_chave(eventos: List[Dict], palavra: str) -> List[Dict]:
    """Filtra eventos cuja descrição contém a palavra-chave (case-insensitive).

    Útil para 'TUDO de TARIFA': passar palavra='TARIFA' e capturar CESTA cheia,
    VR.PARCIAL, EMISSÃO EXTRATO, etc. — tudo numa lista só.
    """
    pal = palavra.upper()
    return [e for e in eventos if pal in e['descricao'].upper()]


def encontrar_extratos_digitais(pasta_cliente: str) -> List[str]:
    """Procura na pasta do cliente E em TODAS as subpastas (recursivo) os PDFs
    que têm text-layer COM o cabeçalho típico de extrato digital Bradesco
    ("Bradesco Celular", "Bradesco Internet Banking" ou "Extrato de:").

    Retorna lista de paths (pode haver vários — cliente pode ter fragmentado
    o extrato em PDFs por período/ano).
    """
    import os
    import fitz
    candidatos_pdf = []

    # Varredura recursiva — captura raiz, KITs, e pastas de ação (MORA/, ENCARGOS/, etc.)
    if os.path.isdir(pasta_cliente):
        for raiz, _dirs, files in os.walk(pasta_cliente):
            for nome in files:
                if nome.lower().endswith('.pdf'):
                    candidatos_pdf.append(os.path.join(raiz, nome))

    extratos = []
    for path in candidatos_pdf:
        try:
            doc = fitz.open(path)
            # Tem text-layer útil?
            primeira_pag = doc[0].get_text() if doc.page_count else ''
            doc.close()
            if len(primeira_pag.strip()) < 100:
                continue
            # É extrato Bradesco digital? Confere cabeçalho típico.
            # Pega 1500 primeiros chars (algumas variantes têm o cabeçalho no meio)
            cabecalho = primeira_pag[:1500]
            if ('Bradesco Celular' in cabecalho or
                'Bradesco Internet Banking' in cabecalho or
                ('Extrato de' in cabecalho and 'Bradesco' in cabecalho) or
                ('Agência' in cabecalho and 'Conta' in cabecalho and 'Bradesco' in cabecalho) or
                ('Ag:' in cabecalho and 'Conta:' in cabecalho and 'Bradesco' in cabecalho)):
                extratos.append(path)
        except Exception:
            continue
    return extratos


def encontrar_extrato_digital_no_kit(pasta_cliente: str) -> Optional[str]:
    """Compat: retorna o PRIMEIRO extrato digital encontrado.
    Para múltiplos, use encontrar_extratos_digitais().
    """
    lst = encontrar_extratos_digitais(pasta_cliente)
    return lst[0] if lst else None


def parsear_multiplos_extratos(extrato_paths: List[str]) -> List[Dict]:
    """Parseia múltiplos PDFs de extrato digital e retorna lista única
    de eventos com de-duplicação (data + descricao + valor + docto).
    Útil quando o cliente fragmenta extrato em vários PDFs (um por ano/período).
    """
    todos = []
    seen = set()
    for path in extrato_paths:
        eventos = parsear_extrato_digital(path)
        for ev in eventos:
            chave = (ev.get('data'), ev.get('descricao'), round(ev.get('valor', 0), 2),
                     ev.get('docto'))
            if chave in seen:
                continue
            seen.add(chave)
            todos.append(ev)
    return todos


def classificar_tarifa(descricao: str) -> str:
    """Classifica uma descrição de TARIFA em sub-rubrica canônica.
    Útil para gerar abas separadas na planilha.
    """
    u = descricao.upper()
    if 'EMISSAO' in u or ('EXTRATO' in u and 'BANCARIA' not in u):
        return 'TARIFA EMISSÃO EXTRATO'
    if 'VR.PARCIAL' in u or 'VR PARCIAL' in u or 'PARCIAL' in u:
        return 'TARIFA BANCÁRIA - VR.PARCIAL CESTA B.EXPRESSO'
    if 'CESTA' in u or 'B.EXPRESSO' in u or 'BEXPRESSO' in u:
        return 'TARIFA BANCÁRIA - CESTA B.EXPRESSO'
    if 'CARTAO' in u and ('CREDITO' in u or 'DEBITO' in u):
        return 'TARIFA CARTÃO'
    if 'PACOTE' in u:
        return 'TARIFA PACOTE DE SERVIÇOS'
    return 'TARIFA OUTRA'
