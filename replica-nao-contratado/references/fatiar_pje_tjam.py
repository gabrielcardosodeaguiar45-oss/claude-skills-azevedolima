# -*- coding: utf-8 -*-
"""
Fatia o PDF consolidado do PJe TJAM em PDFs separados por arquivo (Arq:),
agrupados por movimentacao. Usa pymupdf (garbage=4) — NUNCA pypdf, conforme
feedback registrado em memoria.

Uso:
    from fatiar_pje_tjam import fatiar
    fatias = fatiar(
        pdf_in=r"C:\\caminho\\processo.pdf",
        dest=r"C:\\caminho\\_fatias",
    )
    # fatias = lista de dicts com {'arquivo', 'pag_ini', 'pag_fim', 'mov', 'arq_tipo'}

Detecta marcadores:
- "PROJUDI - Processo: ... Ref. mov. N.M" no rodape de cada pagina
- "Arq: <tipo>" no rodape (pode ser ausente em paginas administrativas)

Quebra em fatias por (mov_principal, mov_filho, arq_tipo) consecutivos.
Salva como NNN-movXXX-YY-tipo.pdf na pasta destino.
"""
import fitz, re, os, unicodedata


def _slug(s, max_len=50):
    """Normaliza string para nome de arquivo seguro."""
    if not s:
        return 'sem-arq'
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-').lower()
    return s[:max_len] or 'sem-arq'


def _detectar_pagina(doc, i, arq_re, mov_re, data_re):
    """Detecta os marcadores presentes na pagina i."""
    txt = doc[i].get_text()
    m_arq = arq_re.search(txt)
    m_mov = mov_re.search(txt)
    arq_tipo = m_arq.group(1).strip() if m_arq else None
    mov_pri = m_mov.group(1) if m_mov else None
    mov_fil = m_mov.group(2) if m_mov else None
    return {
        'pag': i + 1,
        'mov_pri': mov_pri,
        'mov_fil': mov_fil,
        'arq': arq_tipo,
        'texto_curto': txt[:1500],
    }


def _nome_admin(texto, data_re):
    """Tenta extrair nome de movimentacao administrativa (sem mov_pri)."""
    m = data_re.search(texto)
    if m:
        return m.group(2).strip()[:50]
    return None


def fatiar(pdf_in, dest):
    """Fatia um PDF consolidado do PJe TJAM em fatias por arquivo.

    Args:
        pdf_in: caminho do PDF consolidado.
        dest: pasta destino (sera criada se nao existir).

    Returns:
        Lista de dicts com {arquivo, pag_ini, pag_fim, mov, arq_tipo}.
    """
    os.makedirs(dest, exist_ok=True)

    arq_re = re.compile(r'Arq:\s*([^\n]+)')
    mov_re = re.compile(r'PROJUDI - Processo:\s*[\d\.\-]+\s*-\s*Ref\.\s*mov\.\s*(\d+)\.(\d+)')
    data_re = re.compile(r'Data:\s*(\S+).*?Movimenta[çc][ãa]o:\s*([^|\n]+)', re.DOTALL)

    doc = fitz.open(pdf_in)
    N = len(doc)

    # Mapear pagina por pagina
    mapa = [_detectar_pagina(doc, i, arq_re, mov_re, data_re) for i in range(N)]

    # Agrupar paginas consecutivas com mesma chave (mov_pri, mov_fil, arq)
    fatias = []
    fatia_atual = None
    for r in mapa:
        chave = (r['mov_pri'], r['mov_fil'], r['arq'])
        if fatia_atual is None or fatia_atual['chave'] != chave:
            if fatia_atual:
                fatias.append(fatia_atual)
            fatia_atual = {
                'chave': chave,
                'pag_ini': r['pag'],
                'pag_fim': r['pag'],
                'texto_curto_primeira': r['texto_curto'],
            }
        else:
            fatia_atual['pag_fim'] = r['pag']
    if fatia_atual:
        fatias.append(fatia_atual)

    # Salvar e gerar resultado
    resultado = []
    for idx, f in enumerate(fatias, 1):
        mov_pri, mov_fil, arq = f['chave']
        if mov_pri is None:
            admin = _nome_admin(f['texto_curto_primeira'], data_re)
            nome_f = f"{idx:03d}-rosto-{_slug(admin or 'admin')}.pdf"
            mov_str = None
        else:
            nome_f = f"{idx:03d}-mov{int(mov_pri):03d}-{int(mov_fil):02d}-{_slug(arq)}.pdf"
            mov_str = f"{mov_pri}.{mov_fil}"
        out = fitz.open()
        out.insert_pdf(doc, from_page=f['pag_ini'] - 1, to_page=f['pag_fim'] - 1)
        caminho_out = os.path.join(dest, nome_f)
        out.save(caminho_out, garbage=4, deflate=True)
        out.close()
        resultado.append({
            'arquivo': nome_f,
            'caminho': caminho_out,
            'pag_ini': f['pag_ini'],
            'pag_fim': f['pag_fim'],
            'mov': mov_str,
            'arq_tipo': arq,
        })

    doc.close()
    return resultado


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if len(sys.argv) < 2:
        print('Uso: python fatiar_pje_tjam.py <pdf_consolidado> [<pasta_destino>]')
        sys.exit(1)
    pdf = sys.argv[1]
    dest = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(pdf), '_fatias')
    fatias = fatiar(pdf, dest)
    print(f'\nGeradas {len(fatias)} fatias em {dest}:')
    for f in fatias:
        print(f"  {f['arquivo']} (pag {f['pag_ini']}-{f['pag_fim']})")
