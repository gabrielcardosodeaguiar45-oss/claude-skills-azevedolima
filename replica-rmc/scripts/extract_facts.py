#!/usr/bin/env python3
"""
extract_facts.py — camada determinística pré-LLM para o pipeline /replica-rmc.

Lê todos os PDFs de uma pasta de processo, varre cada página com regex/heurísticas
calibradas, e emite _facts.json com ocorrências auditáveis (arquivo, página, contexto).

Uso:
    python extract_facts.py "<caminho da pasta>"
    python extract_facts.py "<caminho da pasta>" --output _facts.json
    python extract_facts.py "<caminho da pasta>" --skip "Réplica.pdf,Foto.pdf"

Saída padrão: <pasta>/_facts.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import fitz


VERSAO_SCRIPT = "1.0.0"
CONTEXTO_BYTES = 60


PATTERNS = {
    "cpf": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "cnpj": re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"),
    "cnj": re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b"),
    "oab_classic": re.compile(
        r"\bOAB[/\s]?(AM|AL|BA|MG|SC|SP|RJ|PE|CE|PR|RS|GO|DF|MT|MS|PA|PB|RN|MA|PI|TO|RO|AC|RR|AP|SE|ES)\s*\d{1,6}[A-Z]?\b",
        re.IGNORECASE,
    ),
    "oab_pje": re.compile(
        r"\b\d{4,6}N(SC|SP|AM|AL|BA|MG|RJ|PE|CE|PR|RS|GO|DF|MT|MS|PA|PB|RN|MA|PI|TO|RO|AC|RR|AP|SE|ES)\b"
    ),
    "data_br": re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"),
    "data_dot": re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{4}\b"),
    "data_iso": re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    "data_extenso": re.compile(
        r"\b\d{1,2}\s+de\s+(janeiro|fevereiro|mar[çc]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+\d{4}\b",
        re.IGNORECASE,
    ),
    "valor_real": re.compile(r"R\$\s*[\d\.\,]{3,}"),
    "ip": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "sha256": re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE),
    "email": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    "telefone": re.compile(r"\(\d{2}\)\s*\d{4,5}-?\d{4}"),
    "cep": re.compile(r"\b\d{5}-\d{3}\b"),
}


BANCOS_CANONICOS = {
    "BMG": ["BANCO BMG", "BMG S.A.", "BMG S/A"],
    "SANTANDER": ["BANCO SANTANDER", "SANTANDER BRASIL"],
    "BRADESCO": ["BANCO BRADESCO", "BRADESCO S.A.", "BRADESCO S/A"],
    "ITAU": ["BANCO ITA", "ITAÚ UNIBANCO", "ITAU UNIBANCO", "ITAÚ S/A", "ITAÚ S.A."],
    "PAN": ["BANCO PAN", "PAN S.A.", "PAN S/A"],
    "DAYCOVAL": ["BANCO DAYCOVAL", "DAYCOVAL S.A."],
    "PARATI": ["BANCO PARATI", "PARATI S.A."],
    "SAFRA": ["BANCO SAFRA", "SAFRA S.A."],
    "MERCANTIL": ["BANCO MERCANTIL", "MERCANTIL DO BRASIL"],
    "OLE": ["BANCO OLE", "BANCO OLÉ", "OLÉ CONSIGNADO", "OLE CONSIGNADO"],
    "FACTA": ["BANCO FACTA", "FACTA FINANCEIRA"],
    "C6": ["BANCO C6", "C6 BANK"],
    "CREFISA": ["CREFISA"],
    "AGIBANK": ["AGIBANK", "BANCO AGIBANK"],
    "INTER": ["BANCO INTER"],
    "BANRISUL": ["BANRISUL"],
    "MASTER": ["BANCO MASTER"],
    "CCB": ["CCB BRASIL", "BANCO INDUSTRIAL E COMERCIAL"],
    "CETELEM": ["CETELEM", "BANCO CETELEM"],
    "BV": ["BANCO BV", "BV FINANCEIRA"],
    "CAIXA": ["CAIXA ECONOMICA", "CAIXA ECONÔMICA"],
}


MARCADORES = {
    "hiscon": ["HISCON", "Hist. de Empr", "Hist. de Empréstimo Consignado", "Histórico de Empréstimo Consignado"],
    "hiscre": ["HISCRE", "Histórico de Crédito"],
    "ccb": ["CCB", "Cédula de Crédito Bancário", "CEDULA DE CREDITO BANCARIO"],
    "ted": ["TED", "TRANSFERÊNCIA ELETRÔNICA", "TRANSFERENCIA ELETRONICA", "COMPROVANTE DE TRANSFERÊNCIA"],
    "fatura": ["Fatura do Cartão", "FATURA DO CARTAO", "FATURA DO CARTÃO"],
    "fatura_postagem": ["Postagem", "POSTAGEM"],
    "rmc": ["Reserva de Margem Consignável", "RESERVA DE MARGEM CONSIGNAVEL", "RMC"],
    "rcc": ["Cartão de Crédito Consignado", "CARTAO DE CREDITO CONSIGNADO", "RCC"],
    "icp_brasil": ["ICP-Brasil", "ICP Brasil"],
    "clicksign": ["Clicksign", "ClickSign", "CLICKSIGN"],
    "docusign": ["DocuSign", "DOCUSIGN"],
    "hash_label": ["SHA-256", "SHA256", "Hash SHA"],
    "biometria": ["biometria", "BIOMETRIA"],
    "selfie_liveness": ["liveness", "LIVENESS", "selfie"],
    "geolocalizacao": ["Geolocalização", "GEOLOCALIZACAO", "geolocalização"],
    "in_28_2008": ["Instrução Normativa INSS/PRES", "IN n° 28", "IN nº 28"],
    "res_cnj_159": ["Resolução nº 159", "Resolução CNJ"],
    "litigancia_predatoria": ["litigância predatória", "litigancia predatoria", "demandas predatórias"],
    "videochamada_092023": ["videochamada", "vídeochamada", "video-chamada"],
    "procuracao": ["PROCURAÇÃO", "PROCURACAO"],
    "contestacao": ["CONTESTAÇÃO", "CONTESTACAO", "DA CONTESTAÇÃO"],
    "inicial": ["PETIÇÃO INICIAL", "PETICAO INICIAL"],
    "saque": ["SAQUE", "saque complementar"],
    "averbacao": ["averbação", "AVERBAÇÃO", "averbacao"],
    "comprovante_residencia": ["comprovante de residência", "COMPROVANTE DE RESIDÊNCIA"],
}


def normalize(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    ).lower()


def extract_context(text: str, start: int, end: int, span: int = CONTEXTO_BYTES) -> str:
    a = max(0, start - span)
    b = min(len(text), end + span)
    snippet = text[a:b]
    snippet = re.sub(r"\s+", " ", snippet).strip()
    return snippet


def parse_valor(raw: str) -> float | None:
    inner = raw.replace("R$", "").strip()
    if not inner:
        return None
    inner = inner.replace(" ", "")
    if "," in inner and "." in inner:
        if inner.rfind(",") > inner.rfind("."):
            inner = inner.replace(".", "").replace(",", ".")
        else:
            inner = inner.replace(",", "")
    elif "," in inner:
        inner = inner.replace(",", ".")
    try:
        return float(inner)
    except ValueError:
        return None


def parse_data_br(raw: str) -> str | None:
    parts = raw.split("/")
    if len(parts) != 3:
        return None
    d, m, y = parts
    try:
        dt = datetime(int(y), int(m), int(d))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


MESES = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12,
}


def parse_data_extenso(raw: str) -> str | None:
    m = re.match(
        r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", raw.strip(), re.IGNORECASE
    )
    if not m:
        return None
    d, mes, y = m.group(1), normalize(m.group(2)), m.group(3)
    if mes not in MESES:
        return None
    try:
        dt = datetime(int(y), MESES[mes], int(d))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def is_caixa_alta_header(line: str) -> bool:
    line = line.strip()
    if len(line) < 12 or len(line) > 140:
        return False
    letters = [c for c in line if c.isalpha()]
    if len(letters) < 8:
        return False
    upper = sum(1 for c in letters if c.isupper())
    ratio = upper / len(letters)
    if ratio < 0.85:
        return False
    if any(line.startswith(p) for p in ("DA ", "DO ", "DAS ", "DOS ", "DE ", "PRELIMINAR", "MÉRITO", "MERITO")):
        return True
    if "ALEGA" in line or "INÉPCIA" in line or "INEPCIA" in line:
        return True
    return ratio > 0.92


def add_fact(bucket: list, value: str, normalized, file: str, page: int, context: str) -> None:
    bucket.append(
        {
            "valor": value,
            "valor_normalizado": normalized,
            "arquivo": file,
            "pagina": page,
            "contexto": context,
        }
    )


def should_skip(filename: str, skip_tokens: set[str]) -> bool:
    name_norm = normalize(filename)
    return any(tok in name_norm for tok in skip_tokens)


def extract_pdf(path: Path, skip_tokens: set[str]) -> dict:
    facts = {
        "cpfs": [],
        "cnpjs": [],
        "cnjs": [],
        "oabs": [],
        "datas": [],
        "valores": [],
        "ips": [],
        "hashes": [],
        "emails": [],
        "telefones": [],
        "ceps": [],
        "headers_caixa_alta": [],
        "bancos_mencionados": [],
        "marcadores": [],
    }
    if should_skip(path.name, skip_tokens):
        return {"_skipped": True, "arquivo": path.name}

    try:
        doc = fitz.open(path)
    except Exception as e:
        return {"_error": str(e), "arquivo": path.name}

    paginas_com_texto = 0
    paginas_vazias_ou_imagem = []
    file_label = path.name

    for pno, page in enumerate(doc, start=1):
        try:
            text = page.get_text()
        except Exception:
            text = ""
        if not text.strip():
            paginas_vazias_ou_imagem.append(pno)
            continue
        paginas_com_texto += 1

        for m in PATTERNS["cpf"].finditer(text):
            add_fact(facts["cpfs"], m.group(), m.group(), file_label, pno, extract_context(text, m.start(), m.end()))
        for m in PATTERNS["cnpj"].finditer(text):
            add_fact(facts["cnpjs"], m.group(), m.group(), file_label, pno, extract_context(text, m.start(), m.end()))
        for m in PATTERNS["cnj"].finditer(text):
            add_fact(facts["cnjs"], m.group(), m.group(), file_label, pno, extract_context(text, m.start(), m.end()))
        for m in PATTERNS["oab_classic"].finditer(text):
            add_fact(facts["oabs"], m.group(), {"formato": "classico", "uf": m.group(1).upper()}, file_label, pno, extract_context(text, m.start(), m.end()))
        for m in PATTERNS["oab_pje"].finditer(text):
            add_fact(facts["oabs"], m.group(), {"formato": "pje", "uf": m.group(1).upper()}, file_label, pno, extract_context(text, m.start(), m.end()))

        for m in PATTERNS["data_br"].finditer(text):
            add_fact(facts["datas"], m.group(), parse_data_br(m.group()), file_label, pno, extract_context(text, m.start(), m.end()))
        for m in PATTERNS["data_dot"].finditer(text):
            iso = parse_data_br(m.group().replace(".", "/"))
            if iso:
                add_fact(facts["datas"], m.group(), iso, file_label, pno, extract_context(text, m.start(), m.end()))
        for m in PATTERNS["data_iso"].finditer(text):
            try:
                datetime.strptime(m.group(), "%Y-%m-%d")
                add_fact(facts["datas"], m.group(), m.group(), file_label, pno, extract_context(text, m.start(), m.end()))
            except ValueError:
                pass
        for m in PATTERNS["data_extenso"].finditer(text):
            iso = parse_data_extenso(m.group())
            add_fact(facts["datas"], m.group(), iso, file_label, pno, extract_context(text, m.start(), m.end()))

        for m in PATTERNS["valor_real"].finditer(text):
            add_fact(facts["valores"], m.group(), parse_valor(m.group()), file_label, pno, extract_context(text, m.start(), m.end()))

        for m in PATTERNS["ip"].finditer(text):
            ip = m.group()
            ctx = extract_context(text, m.start(), m.end())
            if re.search(r"\d+\.\d+\.\d+\.\d+", ip):
                ctx_norm = normalize(ctx)
                if any(noise in ctx_norm for noise in ("processo", "art.", "lei n", "publicacao", "conforme", "n.")):
                    continue
                add_fact(facts["ips"], ip, classify_ip(ip), file_label, pno, ctx)
        for m in PATTERNS["sha256"].finditer(text):
            add_fact(facts["hashes"], m.group(), m.group(), file_label, pno, extract_context(text, m.start(), m.end()))
        for m in PATTERNS["email"].finditer(text):
            add_fact(facts["emails"], m.group(), m.group(), file_label, pno, extract_context(text, m.start(), m.end()))
        for m in PATTERNS["telefone"].finditer(text):
            add_fact(facts["telefones"], m.group(), m.group(), file_label, pno, extract_context(text, m.start(), m.end()))
        for m in PATTERNS["cep"].finditer(text):
            add_fact(facts["ceps"], m.group(), m.group(), file_label, pno, extract_context(text, m.start(), m.end()))

        for line in text.splitlines():
            stripped = line.strip()
            if is_caixa_alta_header(stripped):
                facts["headers_caixa_alta"].append(
                    {"texto": stripped, "arquivo": file_label, "pagina": pno}
                )

        text_norm = normalize(text)
        for canonico, variantes in BANCOS_CANONICOS.items():
            for variante in variantes:
                if normalize(variante) in text_norm:
                    facts["bancos_mencionados"].append(
                        {
                            "canonico": canonico,
                            "variante_encontrada": variante,
                            "arquivo": file_label,
                            "pagina": pno,
                        }
                    )
                    break
        for marcador, termos in MARCADORES.items():
            for termo in termos:
                if normalize(termo) in text_norm:
                    facts["marcadores"].append(
                        {
                            "marcador": marcador,
                            "termo": termo,
                            "arquivo": file_label,
                            "pagina": pno,
                        }
                    )
                    break

    facts["_arquivo_meta"] = {
        "arquivo": file_label,
        "total_paginas": len(doc),
        "paginas_com_texto": paginas_com_texto,
        "paginas_vazias_ou_imagem": paginas_vazias_ou_imagem,
    }
    doc.close()
    return facts


def classify_ip(ip: str) -> dict:
    parts = [int(p) for p in ip.split(".") if p.isdigit() and 0 <= int(p) <= 255]
    if len(parts) != 4:
        return {"valido": False}
    a, b = parts[0], parts[1]
    privado = False
    if a == 10:
        privado = True
    elif a == 172 and 16 <= b <= 31:
        privado = True
    elif a == 192 and b == 168:
        privado = True
    return {"valido": True, "privado": privado, "publico": not privado}


def merge(global_facts: dict, file_facts: dict) -> None:
    if "_skipped" in file_facts or "_error" in file_facts:
        global_facts["_arquivos_problemas"].append(file_facts)
        return
    for k in (
        "cpfs", "cnpjs", "cnjs", "oabs", "datas", "valores",
        "ips", "hashes", "emails", "telefones", "ceps",
        "headers_caixa_alta", "bancos_mencionados", "marcadores",
    ):
        global_facts[k].extend(file_facts.get(k, []))
    global_facts["_arquivos"].append(file_facts.get("_arquivo_meta", {}))


def consolidar_unicos(facts: dict) -> dict:
    """Para cada categoria, agrupa por valor e devolve sumário com total + ocorrências."""
    summary = {}
    for cat in ("cpfs", "cnpjs", "cnjs", "ips", "hashes", "emails", "telefones", "ceps"):
        agrupado: dict[str, dict] = {}
        for item in facts[cat]:
            v = item["valor"]
            if v not in agrupado:
                agrupado[v] = {"valor": v, "valor_normalizado": item["valor_normalizado"], "ocorrencias": []}
            agrupado[v]["ocorrencias"].append(
                {"arquivo": item["arquivo"], "pagina": item["pagina"], "contexto": item["contexto"]}
            )
        summary[cat] = list(agrupado.values())

    oab_agrup: dict[str, dict] = {}
    for item in facts["oabs"]:
        v = item["valor"]
        if v not in oab_agrup:
            oab_agrup[v] = {"valor": v, "info": item["valor_normalizado"], "ocorrencias": []}
        oab_agrup[v]["ocorrencias"].append(
            {"arquivo": item["arquivo"], "pagina": item["pagina"], "contexto": item["contexto"]}
        )
    summary["oabs"] = list(oab_agrup.values())

    datas_agrup: dict[str, dict] = {}
    for item in facts["datas"]:
        key = item.get("valor_normalizado") or item["valor"]
        if not key:
            continue
        if key not in datas_agrup:
            datas_agrup[key] = {"valor_iso": key, "ocorrencias": []}
        datas_agrup[key]["ocorrencias"].append(
            {
                "valor_original": item["valor"],
                "arquivo": item["arquivo"],
                "pagina": item["pagina"],
                "contexto": item["contexto"],
            }
        )
    summary["datas"] = sorted(datas_agrup.values(), key=lambda d: d["valor_iso"])

    valores_agrup: dict[str, dict] = {}
    for item in facts["valores"]:
        v = item["valor"]
        if v not in valores_agrup:
            valores_agrup[v] = {
                "valor": v,
                "valor_numerico": item["valor_normalizado"],
                "ocorrencias": [],
            }
        valores_agrup[v]["ocorrencias"].append(
            {"arquivo": item["arquivo"], "pagina": item["pagina"], "contexto": item["contexto"]}
        )
    summary["valores"] = sorted(
        valores_agrup.values(),
        key=lambda d: d["valor_numerico"] if d["valor_numerico"] is not None else 0,
        reverse=True,
    )

    bancos_agrup: dict[str, dict] = {}
    for item in facts["bancos_mencionados"]:
        c = item["canonico"]
        if c not in bancos_agrup:
            bancos_agrup[c] = {"banco": c, "ocorrencias": []}
        bancos_agrup[c]["ocorrencias"].append(
            {"arquivo": item["arquivo"], "pagina": item["pagina"], "variante": item["variante_encontrada"]}
        )
    summary["bancos_mencionados"] = sorted(
        bancos_agrup.values(), key=lambda d: len(d["ocorrencias"]), reverse=True
    )

    marc_agrup: dict[str, dict] = {}
    for item in facts["marcadores"]:
        m = item["marcador"]
        if m not in marc_agrup:
            marc_agrup[m] = {"marcador": m, "paginas_por_arquivo": defaultdict(list)}
        marc_agrup[m]["paginas_por_arquivo"][item["arquivo"]].append(item["pagina"])
    saida_marc = []
    for v in marc_agrup.values():
        saida_marc.append(
            {
                "marcador": v["marcador"],
                "paginas_por_arquivo": {k: sorted(set(p)) for k, p in v["paginas_por_arquivo"].items()},
                "total_ocorrencias": sum(len(p) for p in v["paginas_por_arquivo"].values()),
            }
        )
    summary["marcadores"] = sorted(saida_marc, key=lambda d: d["total_ocorrencias"], reverse=True)

    headers_agrup: dict[str, dict] = {}
    for item in facts["headers_caixa_alta"]:
        t = item["texto"]
        if t not in headers_agrup:
            headers_agrup[t] = {"texto": t, "ocorrencias": []}
        headers_agrup[t]["ocorrencias"].append(
            {"arquivo": item["arquivo"], "pagina": item["pagina"]}
        )
    summary["headers_caixa_alta"] = sorted(
        headers_agrup.values(), key=lambda d: d["ocorrencias"][0]["pagina"]
    )

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pasta", help="Caminho absoluto da pasta de processo")
    parser.add_argument("--output", default="_facts.json", help="Nome do arquivo de saída (default _facts.json na própria pasta)")
    parser.add_argument(
        "--skip",
        default="replica,foto",
        help="Lista separada por vírgula de tokens (busca por substring case/accent-insensitive). Default pula arquivos que contenham 'replica' ou 'foto' no nome (peças produzidas pelo escritório).",
    )
    args = parser.parse_args()

    pasta = Path(args.pasta).expanduser().resolve()
    if not pasta.is_dir():
        print(f"ERRO: pasta não encontrada: {pasta}", file=sys.stderr)
        return 2

    skip_files = {s.strip() for s in args.skip.split(",") if s.strip()}

    pdfs = sorted([p for p in pasta.glob("*.pdf")])
    if not pdfs:
        print(f"ERRO: nenhum PDF em {pasta}", file=sys.stderr)
        return 2

    global_facts: dict = {
        "cpfs": [],
        "cnpjs": [],
        "cnjs": [],
        "oabs": [],
        "datas": [],
        "valores": [],
        "ips": [],
        "hashes": [],
        "emails": [],
        "telefones": [],
        "ceps": [],
        "headers_caixa_alta": [],
        "bancos_mencionados": [],
        "marcadores": [],
        "_arquivos": [],
        "_arquivos_problemas": [],
    }

    for pdf in pdfs:
        print(f"  Processando {pdf.name} ...", file=sys.stderr)
        file_facts = extract_pdf(pdf, skip_files)
        merge(global_facts, file_facts)

    summary = consolidar_unicos(global_facts)

    out = {
        "_meta": {
            "pasta": str(pasta),
            "data_extracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "versao_script": VERSAO_SCRIPT,
            "arquivos_processados": global_facts["_arquivos"],
            "arquivos_problemas": global_facts["_arquivos_problemas"],
            "arquivos_pulados": [a for a in skip_files if (pasta / a).exists()],
        },
        "fatos_unicos": summary,
        "fatos_brutos_total": {k: len(global_facts[k]) for k in summary if k in global_facts},
    }

    out_path = pasta / args.output if not Path(args.output).is_absolute() else Path(args.output)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK — {out_path}", file=sys.stderr)
    print(f"     {len(summary['cpfs'])} CPFs únicos, {len(summary['cnjs'])} CNJs, {len(summary['datas'])} datas, {len(summary['valores'])} valores, {len(summary['bancos_mencionados'])} bancos", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
