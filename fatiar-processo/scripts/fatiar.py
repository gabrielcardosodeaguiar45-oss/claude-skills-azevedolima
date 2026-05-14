"""
Fatia PDF consolidado de processo eletrônico em um PDF por evento/movimentação.

Sistemas suportados (detecção automática):
  1. eproc / TRF4 / TJSC      — marcador "PÁGINA DE SEPARAÇÃO" + "Evento N"
  2. PJe TJAM (8.04.xxxx)     — tríade "Data:" + "Movimentação:" + "Por:"
  3. PJe TJBA (8.05.xxxx)     — marcador "Num. NNNNN - Pág. 1" + "Assinado eletronicamente por:"

Detecção e fatiamento usam pymupdf (fitz) com garbage=4 + deflate + clean — copia
páginas SEM arrastar todos os recursos compartilhados do documento original.

Salvaguarda: aborta se a soma dos arquivos fatiados ultrapassar 2x o original
(sintoma de inflate por recursos compartilhados não removidos).

Uso:
    python fatiar.py <pdf_path> [--saida <pasta>] [--sistema eproc|pje_tjam|pje_tjba]
"""

import argparse
import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# Detecção de sistema
# ---------------------------------------------------------------------------

def detectar_sistema(doc):
    """Olha as primeiras páginas e infere qual sistema gerou o PDF.

    Retorna 'eproc' | 'pje_tjam' | 'pje_tjba' | 'desconhecido'.
    """
    amostra = ""
    for i in range(min(15, len(doc))):
        amostra += doc[i].get_text() + "\n"

    if "PÁGINA DE SEPARAÇÃO" in amostra or "PAGINA DE SEPARACAO" in amostra:
        return "eproc"

    tem_num_pag1 = bool(re.search(r"Num\.\s+\d+\s*-\s*P[áa]g\.\s*1\b", amostra))
    tem_pje_tjba = "pje.tjba.jus.br" in amostra.lower() or "TJBA" in amostra

    if tem_num_pag1 and tem_pje_tjba:
        return "pje_tjba"
    if tem_num_pag1:
        return "pje_tjba"

    tem_data = bool(re.search(r"^\s*Data:\s+\d{2}/\d{2}/\d{4}", amostra, re.MULTILINE))
    tem_mov = bool(re.search(r"Movimenta[çc][ãa]o:\s*", amostra))
    tem_por = bool(re.search(r"Por:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ]", amostra))
    tem_amazonas = "AMAZONAS" in amostra.upper() or "TJAM" in amostra
    if tem_data and tem_mov and tem_por:
        return "pje_tjam" if tem_amazonas else "pje_tjam"

    return "desconhecido"


# ---------------------------------------------------------------------------
# Detector eproc / TRF4
# ---------------------------------------------------------------------------

def detectar_marcos_eproc(doc):
    """Retorna lista de dicts: {pag_inicial, numero, descricao, tipo}."""
    marcos = []
    for i in range(len(doc)):
        text = doc[i].get_text() or ""
        if "PÁGINA DE SEPARAÇÃO" not in text and "PAGINA DE SEPARACAO" not in text:
            continue
        m = re.search(r"Evento\s+(\d+)", text)
        if not m:
            continue
        numero = int(m.group(1))

        descricao = ""
        linhas = [l.strip() for l in text.split("\n") if l.strip()]
        for j, l in enumerate(linhas):
            if "Sequência Evento" in l or "Sequencia Evento" in l:
                for k in range(j + 1, min(j + 8, len(linhas))):
                    cand = linhas[k]
                    if not cand or cand.isdigit():
                        continue
                    if re.match(r"^\d{2}/\d{2}/\d{4}", cand):
                        continue
                    if len(cand) >= 5 and sum(1 for c in cand if c.isupper() or not c.isalpha()) >= len(cand) * 0.7:
                        descricao = cand
                        break
                break

        marcos.append({
            "pag_inicial": i,
            "numero": numero,
            "descricao": descricao or "SEM DESCRIÇÃO",
            "tipo": None,
        })
    return marcos


def extrair_tipo_eproc(doc, pag_inicial, pag_final):
    tipos = []
    for p in range(pag_inicial + 1, min(pag_final + 1, len(doc))):
        text = doc[p].get_text() or ""
        for m in re.finditer(r"Evento\s+\d+\s*,\s*([A-Za-z][A-Za-z0-9]{1,12})\s*,\s*P[aá]gina", text):
            tipos.append(m.group(1))
    if not tipos:
        return None
    unicos = []
    for t in tipos:
        if t not in unicos:
            unicos.append(t)
    return "_".join(unicos[:3])


# ---------------------------------------------------------------------------
# Detector PJe TJAM
# ---------------------------------------------------------------------------

def detectar_marcos_pje_tjam(doc):
    """Cada movimentação no PJe TJAM tem página 'de rosto' com tríade
    Data: + Movimentação: + Por: na mesma página."""
    marcos = []
    for i in range(len(doc)):
        t = doc[i].get_text() or ""
        m_data = re.search(r"Data:\s+(\d{2}/\d{2}/\d{4})", t)
        m_mov = re.search(r"Movimenta[çc][ãa]o:\s*([^\n|]+)", t)
        m_por = re.search(r"Por:\s+([^\n|]+)", t)
        if not (m_data and m_mov and m_por):
            continue

        data = m_data.group(1)
        mov = m_mov.group(1).strip()
        por = m_por.group(1).strip()

        # Filtra falsos positivos: a tríade tem que estar próxima no texto.
        # Se a página tem mais de 2.000 caracteres, provavelmente é um anexo
        # que reproduz o cabeçalho do evento, não a página de rosto. Mantemos
        # o ponto como marco apenas se "Movimentação:" aparecer no primeiro
        # terço do texto da página.
        idx_mov = t.find("Movimenta")
        if idx_mov < 0 or idx_mov > len(t) * 0.5:
            continue

        marcos.append({
            "pag_inicial": i,
            "numero": len(marcos) + 1,
            "descricao": f"{data} - {mov}",
            "tipo": _tipo_curto_pje_tjam(mov),
            "_data": data,
            "_mov": mov,
            "_por": por,
        })
    return marcos


def _tipo_curto_pje_tjam(mov):
    """Heurística para reduzir 'JUNTADA DE PETIÇÃO DE CONTESTAÇÃO' → 'CONTES'."""
    upper = mov.upper()
    mapa = [
        ("INICIAL", "INIC"),
        ("CONTESTA", "CONTES"),
        ("R\u00c9PLICA", "REPLI"),
        ("REPLICA", "REPLI"),
        ("SENTEN", "SENT"),
        ("DESPACHO", "DESP"),
        ("DECIS", "DEC"),
        ("CERTID", "CERT"),
        ("HABILITA", "HAB"),
        ("DI\u00c1RIO", "DJE"),
        ("DIARIO", "DJE"),
        ("INTIMA", "INTIM"),
        ("PROCURA", "PROC"),
        ("REQUERIMENTO", "REQ"),
        ("PETI", "PET"),
    ]
    for chave, sigla in mapa:
        if chave in upper:
            return sigla
    return "MOV"


# ---------------------------------------------------------------------------
# Detector PJe TJBA
# ---------------------------------------------------------------------------

def detectar_marcos_pje_tjba(doc):
    """Cada documento no PJe TJBA inicia em página marcada por
    'Num. NNNNNNN - Pág. 1' + linha 'Assinado eletronicamente por: NOME - DATA'."""
    marcos = []
    for i in range(len(doc)):
        t = doc[i].get_text() or ""
        m = re.search(r"Num\.\s+(\d+)\s*-\s*P[áa]g\.\s*1\b", t)
        if not m:
            continue
        num_doc = m.group(1)

        m_ass = re.search(
            r"Assinado\s+eletronicamente\s+por:\s*([^\n-]+?)\s+-\s+(\d{2}/\d{2}/\d{4})",
            t,
        )
        assinante = m_ass.group(1).strip() if m_ass else ""
        data = m_ass.group(2) if m_ass else ""

        # Tipo do documento: tenta inferir das primeiras linhas após o cabeçalho
        # técnico (assinatura, link, número do documento).
        tipo = _tipo_pje_tjba(t)

        descricao = " - ".join(filter(None, [data, tipo, assinante[:30]]))
        marcos.append({
            "pag_inicial": i,
            "numero": len(marcos) + 1,
            "descricao": descricao or f"DOC {num_doc}",
            "tipo": _tipo_curto_pje_tjba(tipo, t),
            "_num_doc": num_doc,
            "_data": data,
            "_assinante": assinante,
        })
    return marcos


def _tipo_pje_tjba(t):
    """Procura uma palavra-chave de tipo de documento no texto da página 1."""
    palavras_chave = [
        "PETIÇÃO INICIAL", "INICIAL",
        "CONTESTAÇÃO", "CONTESTACAO",
        "RÉPLICA", "REPLICA",
        "SENTENÇA", "SENTENCA",
        "DESPACHO",
        "DECISÃO", "DECISAO",
        "CERTIDÃO", "CERTIDAO",
        "PROCURAÇÃO", "PROCURACAO",
        "ANEXO",
        "MANIFESTAÇÃO", "MANIFESTACAO",
        "EMBARGO",
        "RECURSO",
    ]
    upper = t.upper()
    for kw in palavras_chave:
        if kw in upper:
            return kw
    return ""


def _tipo_curto_pje_tjba(tipo_long, texto):
    if not tipo_long:
        # Tenta detectar pelo título isolado: apenas linhas A-Z compostas só
        # de letras/espaços (evita PDFs com fontes danificadas que extraem
        # caracteres ASCII espúrios como '!8EFGHI9;')
        for ln in [l.strip() for l in texto.split("\n")][:30]:
            if not ln:
                continue
            if 4 <= len(ln) <= 25 and re.fullmatch(r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ ]+", ln):
                return ln.replace(" ", "")[:10]
        return "DOC"
    upper = tipo_long.upper()
    mapa = [
        ("INICIAL", "INIC"),
        ("CONTESTA", "CONTES"),
        ("REPLICA", "REPLI"),
        ("R\u00c9PLICA", "REPLI"),
        ("SENTEN", "SENT"),
        ("DESPACHO", "DESP"),
        ("DECIS", "DEC"),
        ("CERTID", "CERT"),
        ("PROCURA", "PROC"),
        ("ANEXO", "ANEX"),
        ("MANIFEST", "MANIF"),
        ("EMBARG", "EMB"),
        ("RECURSO", "REC"),
    ]
    for chave, sigla in mapa:
        if chave in upper:
            return sigla
    return "DOC"


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def sanitize(s, limite=70):
    # Remove caracteres de controle e proibidos pelo Windows
    s = re.sub(r'[<>:"/\\|?*\n\r\t]', "", s)
    # Remove qualquer caractere fora de letras/dígitos/espaços/símbolos seguros
    # (evita lixo extraído de fontes corrompidas como '!8EFGHI9;')
    s = re.sub(r"[^\w\sÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç().,\-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limite]


def montar_segmentos(marcos, total_paginas, sistema):
    """Calcula pag_final de cada marco e (opcionalmente) prepende segmento 'Início'."""
    segmentos = []

    # Para eproc, costuma haver conteúdo antes da primeira página de separação
    # (geralmente a petição inicial). Para PJe, o primeiro marco já é a inicial.
    if sistema == "eproc" and marcos and marcos[0]["pag_inicial"] > 0:
        segmentos.append({
            "numero": 1,
            "descricao": "INICIAL E DOCUMENTOS",
            "pag_inicial": 0,
            "pag_final": marcos[0]["pag_inicial"] - 1,
            "tipo": "INIC",
        })
        # renumera os marcos eproc para evitar colisão
        for m in marcos:
            m["numero"] = m["numero"] + 1 if m["numero"] == 1 else m["numero"]

    for idx, m in enumerate(marcos):
        pag_final = (
            marcos[idx + 1]["pag_inicial"] - 1
            if idx + 1 < len(marcos)
            else total_paginas - 1
        )
        seg = dict(m)
        seg["pag_final"] = pag_final
        segmentos.append(seg)

    return segmentos


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------

def fatiar(pdf_path: Path, output_dir: Path, sistema_forcado=None):
    src_size = pdf_path.stat().st_size
    src_doc = fitz.open(str(pdf_path))
    total_paginas = len(src_doc)
    print(f"PDF original: {src_size/1024/1024:.1f} MB, {total_paginas} páginas")
    print(f"Média por página: {src_size/total_paginas/1024:.0f} KB\n")

    sistema = sistema_forcado or detectar_sistema(src_doc)
    print(f"Sistema detectado: {sistema}")

    if sistema == "desconhecido":
        print("Nenhum padrão de marcação reconhecido (eproc, PJe TJAM, PJe TJBA).")
        print("Use --sistema para forçar um detector específico, se você sabe o sistema de origem.")
        src_doc.close()
        return

    print("Detectando marcadores de evento...")
    if sistema == "eproc":
        marcos = detectar_marcos_eproc(src_doc)
    elif sistema == "pje_tjam":
        marcos = detectar_marcos_pje_tjam(src_doc)
    elif sistema == "pje_tjba":
        marcos = detectar_marcos_pje_tjba(src_doc)
    else:
        marcos = []

    print(f"Encontrados {len(marcos)} marcadores.")
    if not marcos:
        print("Sem marcadores — abortando sem gerar saída.")
        src_doc.close()
        return

    # Para eproc, complementa com tipo extraído do rodapé
    if sistema == "eproc":
        for m in marcos:
            pf = m["pag_inicial"]  # pag_final será definido depois; tipo só precisa do range
        # tipo será preenchido no loop de geração

    segmentos = montar_segmentos(marcos, total_paginas, sistema)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nSalvando {len(segmentos)} arquivos em: {output_dir}\n")

    total_out = 0
    arquivos_gerados = []
    abortou = False

    try:
        for seg in segmentos:
            # Resolve tipo
            tipo = seg.get("tipo")
            if not tipo and sistema == "eproc":
                tipo = extrair_tipo_eproc(src_doc, seg["pag_inicial"], seg["pag_final"])
            tipo = (tipo or "DOC")[:30]

            num_fmt = f"{seg['numero']:03d}"
            desc = sanitize(seg["descricao"], limite=50)

            prefixo = {
                "eproc": "Ev",
                "pje_tjam": "Mov",
                "pje_tjba": "Doc",
            }.get(sistema, "It")

            nome = f"{prefixo}{num_fmt}-{tipo}-{desc}.pdf"
            nome = sanitize(nome, limite=90)
            if not nome.lower().endswith(".pdf"):
                nome = nome[:86] + ".pdf"

            new_doc = fitz.open()
            try:
                new_doc.insert_pdf(
                    src_doc,
                    from_page=seg["pag_inicial"],
                    to_page=seg["pag_final"],
                )
                out_path = output_dir / nome
                new_doc.save(str(out_path), garbage=4, deflate=True, clean=True)
            finally:
                new_doc.close()

            arquivos_gerados.append(out_path)
            tam = out_path.stat().st_size
            total_out += tam
            npags = seg["pag_final"] - seg["pag_inicial"] + 1
            print(f"  {nome}  ({npags} pág., {tam/1024:.0f} KB)")

            if total_out > src_size * 2:
                abortou = True
                print(f"\nABORTANDO: total fatiado ({total_out/1024/1024:.1f} MB) excede 2x o original ({src_size/1024/1024:.1f} MB).")
                print("Sintoma de inflate por recursos compartilhados não removidos.")
                break
    finally:
        src_doc.close()

    if abortou:
        print(f"\nLimpando {len(arquivos_gerados)} arquivos gerados...")
        for f in arquivos_gerados:
            try: f.unlink()
            except: pass
        try: output_dir.rmdir()
        except: pass
        print("Pasta removida. Skill abortada — investigar inflate antes de tentar novamente.")
        sys.exit(2)

    print(f"\nConcluído. {len(segmentos)} arquivos gerados.")
    print(f"Total: {total_out/1024/1024:.1f} MB ({total_out/src_size:.2f}x o original)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="Caminho do PDF consolidado do processo")
    parser.add_argument("--saida", help="Pasta de saída (default: <nome>_eventos na mesma pasta)")
    parser.add_argument(
        "--sistema",
        choices=["eproc", "pje_tjam", "pje_tjba"],
        help="Força um detector específico (em vez da auto-detecção)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"ERRO: PDF não encontrado: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.saida) if args.saida else pdf_path.parent / "eventos"
    fatiar(pdf_path, output_dir, sistema_forcado=args.sistema)


if __name__ == "__main__":
    main()
