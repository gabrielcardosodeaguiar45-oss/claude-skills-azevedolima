#!/usr/bin/env python3
"""
validate_against_facts.py — checagem agressiva da réplica contra _facts.json + PDFs.

Para cada parágrafo da réplica gerada, extrai dados pontuais (CPFs, CNJs, datas,
valores R$, CNPJs, IPs) e citações literais entre aspas, e checa se cada um existe
em _facts.json (dado pontual) ou no texto extraído do PDF do processo (citação).

Saída: <PASTA>/_validacao_fonte.json + _validacao_fonte.txt (resumo legível).

Uso:
    python validate_against_facts.py --replica "<caminho>/Réplica.docx" \
                                     --facts "<caminho>/_facts.json" \
                                     --pasta "<caminho>"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import fitz
from docx import Document


PATTERNS = {
    "cpf": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "cnpj": re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"),
    "cnj": re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b"),
    "data_br": re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"),
    "valor_real": re.compile(r"R\$\s*[\d\.\,]{3,}"),
    "ip": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "sha256": re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE),
    "citacao_literal": re.compile(r"[\"“]([^\"”]{20,400})[\"”]"),
}


SKIP_VALOR_CONTEXTOS = (
    "dano moral",
    "danos morais",
    "indenizatorio",
    "indenizatório",
    "pleiteia",
    "pleiteado",
    "pretende",
    "requer",
    "fixar em",
    "arbitrar em",
    "arbitra-se",
    "fixa-se",
    "majorar",
    "majoração",
)


def normalize(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    ).lower()


def parse_valor(raw: str) -> float | None:
    inner = raw.replace("R$", "").strip()
    inner = inner.replace(" ", "").rstrip(",.;:")
    if not inner:
        return None
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
        return datetime(int(y), int(m), int(d)).strftime("%Y-%m-%d")
    except ValueError:
        return None


def is_pleito_contexto(contexto: str) -> bool:
    norm = normalize(contexto)
    return any(p in norm for p in (normalize(t) for t in SKIP_VALOR_CONTEXTOS))


def extract_pdf_text_concat(pasta: Path, skip_tokens: set[str]) -> str:
    """Concatena texto de todos os PDFs do processo (para grep de citação literal)."""
    parts = []
    for pdf in sorted(pasta.glob("*.pdf")):
        if any(tok in normalize(pdf.name) for tok in skip_tokens):
            continue
        try:
            with fitz.open(pdf) as doc:
                for page in doc:
                    parts.append(page.get_text())
        except Exception as e:
            print(f"AVISO: falha ao ler {pdf.name}: {e}", file=sys.stderr)
    return "\n".join(parts)


def normalize_for_grep(s: str) -> str:
    """Normaliza texto para fuzzy grep: lowercase, sem acentos, espaços colapsados."""
    s = normalize(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def validar_replica(replica_path: Path, facts_path: Path, pasta: Path) -> dict:
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    fatos = facts["fatos_unicos"]

    cpfs_facts = {c["valor"] for c in fatos["cpfs"]}
    cnpjs_facts = {c["valor"] for c in fatos["cnpjs"]}
    cnjs_facts = {c["valor"] for c in fatos["cnjs"]}
    datas_facts_iso = {d["valor_iso"] for d in fatos["datas"]}
    valores_facts = set()
    for v in fatos["valores"]:
        if v["valor_numerico"] is not None:
            valores_facts.add(round(v["valor_numerico"], 2))
    ips_facts = {i["valor"] for i in fatos["ips"]}
    hashes_facts = {h["valor"].lower() for h in fatos["hashes"]}

    pdf_text = extract_pdf_text_concat(pasta, skip_tokens={"replica", "foto"})
    pdf_text_norm = normalize_for_grep(pdf_text)

    doc = Document(replica_path)
    achados = []
    stats = {
        "valores_verificados": 0,
        "valores_ancorados": 0,
        "valores_pleito_skip": 0,
        "datas_verificadas": 0,
        "datas_ancoradas": 0,
        "cnjs_verificados": 0,
        "cnjs_ancorados": 0,
        "cpfs_verificados": 0,
        "cpfs_ancorados": 0,
        "cnpjs_verificados": 0,
        "cnpjs_ancorados": 0,
        "ips_verificados": 0,
        "ips_ancorados": 0,
        "hashes_verificados": 0,
        "hashes_ancorados": 0,
        "citacoes_literais_verificadas": 0,
        "citacoes_literais_ancoradas": 0,
    }

    for p_idx, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text
        if not text.strip():
            continue

        for m in PATTERNS["cpf"].finditer(text):
            stats["cpfs_verificados"] += 1
            v = m.group()
            if v in cpfs_facts:
                stats["cpfs_ancorados"] += 1
            else:
                achados.append({
                    "tipo": "cpf_sem_ancora",
                    "valor": v,
                    "paragrafo": p_idx,
                    "trecho": text[:200],
                    "severidade": "CRITICO",
                    "acao_sugerida": "CPF não encontrado em _facts.json. Verificar fonte ou remover.",
                })

        for m in PATTERNS["cnpj"].finditer(text):
            stats["cnpjs_verificados"] += 1
            v = m.group()
            if v in cnpjs_facts:
                stats["cnpjs_ancorados"] += 1
            else:
                achados.append({
                    "tipo": "cnpj_sem_ancora",
                    "valor": v,
                    "paragrafo": p_idx,
                    "trecho": text[:200],
                    "severidade": "CRITICO",
                    "acao_sugerida": "CNPJ não encontrado em _facts.json. Verificar fonte ou remover.",
                })

        for m in PATTERNS["cnj"].finditer(text):
            stats["cnjs_verificados"] += 1
            v = m.group()
            if v in cnjs_facts:
                stats["cnjs_ancorados"] += 1
            else:
                achados.append({
                    "tipo": "cnj_sem_ancora",
                    "valor": v,
                    "paragrafo": p_idx,
                    "trecho": text[:200],
                    "severidade": "MEDIO",
                    "acao_sugerida": "CNJ não encontrado no processo (provável precedente jurisprudencial externo). Confirmar se a citação é autêntica.",
                })

        for m in PATTERNS["data_br"].finditer(text):
            stats["datas_verificadas"] += 1
            v = m.group()
            iso = parse_data_br(v)
            if iso and iso in datas_facts_iso:
                stats["datas_ancoradas"] += 1
            else:
                achados.append({
                    "tipo": "data_sem_ancora",
                    "valor": v,
                    "paragrafo": p_idx,
                    "trecho": text[:200],
                    "severidade": "MEDIO",
                    "acao_sugerida": f"Data {v} não encontrada em _facts.json. Pode ser data de precedente; confirmar.",
                })

        for m in PATTERNS["valor_real"].finditer(text):
            stats["valores_verificados"] += 1
            raw = m.group()
            n = parse_valor(raw)
            if n is None:
                continue
            n = round(n, 2)
            ctx_start = max(0, m.start() - 80)
            ctx_end = min(len(text), m.end() + 80)
            ctx = text[ctx_start:ctx_end]
            if n in valores_facts:
                stats["valores_ancorados"] += 1
            elif is_pleito_contexto(ctx):
                stats["valores_pleito_skip"] += 1
            else:
                achados.append({
                    "tipo": "valor_sem_ancora",
                    "valor": raw,
                    "valor_numerico": n,
                    "paragrafo": p_idx,
                    "trecho": text[:200],
                    "severidade": "CRITICO",
                    "acao_sugerida": f"Valor {raw} não encontrado em _facts.json e contexto não é pleito. Confirmar ou remover.",
                })

        for m in PATTERNS["ip"].finditer(text):
            v = m.group()
            partes = v.split(".")
            if len(partes) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in partes):
                continue
            stats["ips_verificados"] += 1
            if v in ips_facts:
                stats["ips_ancorados"] += 1
            else:
                achados.append({
                    "tipo": "ip_sem_ancora",
                    "valor": v,
                    "paragrafo": p_idx,
                    "trecho": text[:200],
                    "severidade": "CRITICO",
                    "acao_sugerida": f"IP {v} não está em _facts.json. Verificar fonte.",
                })

        for m in PATTERNS["sha256"].finditer(text):
            stats["hashes_verificados"] += 1
            v = m.group().lower()
            if v in hashes_facts:
                stats["hashes_ancorados"] += 1
            else:
                achados.append({
                    "tipo": "hash_sem_ancora",
                    "valor": v,
                    "paragrafo": p_idx,
                    "trecho": text[:200],
                    "severidade": "CRITICO",
                    "acao_sugerida": "Hash não encontrado em _facts.json. Verificar fonte.",
                })

        for m in PATTERNS["citacao_literal"].finditer(text):
            citacao = m.group(1).strip()
            if len(citacao) < 25:
                continue
            stats["citacoes_literais_verificadas"] += 1
            citacao_norm = normalize_for_grep(citacao)
            citacao_chave = citacao_norm[: min(80, len(citacao_norm))]
            if citacao_chave in pdf_text_norm:
                stats["citacoes_literais_ancoradas"] += 1
            else:
                achados.append({
                    "tipo": "citacao_literal_nao_encontrada",
                    "valor": citacao[:200],
                    "paragrafo": p_idx,
                    "trecho": text[:200],
                    "severidade": "CRITICO",
                    "acao_sugerida": "Citação entre aspas não encontrada literalmente nos PDFs do processo. Substituir por trecho real ou retirar aspas se for paráfrase.",
                })

    return {
        "_meta": {
            "replica": str(replica_path),
            "facts": str(facts_path),
            "pasta": str(pasta),
            "data_validacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "estatisticas": stats,
        "achados": achados,
        "classificacao_sugerida": classificar(achados),
    }


def classificar(achados: list) -> str:
    criticos = sum(1 for a in achados if a["severidade"] == "CRITICO")
    medios = sum(1 for a in achados if a["severidade"] == "MEDIO")
    if criticos > 0:
        return "AJUSTES NECESSÁRIOS"
    if medios > 0:
        return "APTO COM RESSALVAS"
    return "APTO"


def gerar_resumo_txt(resultado: dict) -> str:
    s = []
    s.append("=" * 70)
    s.append("VALIDAÇÃO DA RÉPLICA CONTRA _facts.json + PDFs DO PROCESSO")
    s.append("=" * 70)
    s.append("")
    s.append(f"Réplica: {resultado['_meta']['replica']}")
    s.append(f"Facts:   {resultado['_meta']['facts']}")
    s.append(f"Data:    {resultado['_meta']['data_validacao']}")
    s.append("")
    s.append("Estatísticas:")
    st = resultado["estatisticas"]
    s.append(f"  CPFs:     {st['cpfs_ancorados']}/{st['cpfs_verificados']} ancorados")
    s.append(f"  CNPJs:    {st['cnpjs_ancorados']}/{st['cnpjs_verificados']} ancorados")
    s.append(f"  CNJs:     {st['cnjs_ancorados']}/{st['cnjs_verificados']} ancorados")
    s.append(f"  Datas:    {st['datas_ancoradas']}/{st['datas_verificadas']} ancoradas")
    s.append(f"  Valores:  {st['valores_ancorados']}/{st['valores_verificados']} ancorados ({st['valores_pleito_skip']} pulados como pleito)")
    s.append(f"  IPs:      {st['ips_ancorados']}/{st['ips_verificados']} ancorados")
    s.append(f"  Hashes:   {st['hashes_ancorados']}/{st['hashes_verificados']} ancorados")
    s.append(f"  Citações: {st['citacoes_literais_ancoradas']}/{st['citacoes_literais_verificadas']} encontradas no PDF")
    s.append("")
    s.append(f"Classificação sugerida: {resultado['classificacao_sugerida']}")
    s.append(f"Total de achados: {len(resultado['achados'])}")
    s.append("")
    if resultado["achados"]:
        s.append("Achados (em ordem de aparição):")
        for i, a in enumerate(resultado["achados"], 1):
            s.append(f"  [{a['severidade']}] #{i} parágrafo {a['paragrafo']} — {a['tipo']}")
            s.append(f"      Valor/trecho: {a['valor'][:120]!r}")
            s.append(f"      Ação: {a['acao_sugerida']}")
            s.append("")
    s.append("=" * 70)
    return "\n".join(s)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--replica", required=True, help="Caminho do .docx da réplica")
    p.add_argument("--facts", required=True, help="Caminho do _facts.json")
    p.add_argument("--pasta", required=True, help="Pasta do processo (para grep nos PDFs)")
    p.add_argument("--output-json", default=None, help="Caminho do JSON de saída (default: <pasta>/_validacao_fonte.json)")
    p.add_argument("--output-txt", default=None, help="Caminho do resumo TXT (default: <pasta>/_validacao_fonte.txt)")
    args = p.parse_args()

    replica_path = Path(args.replica).expanduser().resolve()
    facts_path = Path(args.facts).expanduser().resolve()
    pasta = Path(args.pasta).expanduser().resolve()

    if not replica_path.exists():
        print(f"ERRO: réplica não encontrada: {replica_path}", file=sys.stderr)
        return 2
    if not facts_path.exists():
        print(f"ERRO: _facts.json não encontrado: {facts_path}", file=sys.stderr)
        return 2
    if not pasta.is_dir():
        print(f"ERRO: pasta não encontrada: {pasta}", file=sys.stderr)
        return 2

    resultado = validar_replica(replica_path, facts_path, pasta)

    out_json = Path(args.output_json) if args.output_json else pasta / "_validacao_fonte.json"
    out_txt = Path(args.output_txt) if args.output_txt else pasta / "_validacao_fonte.txt"

    out_json.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    out_txt.write_text(gerar_resumo_txt(resultado), encoding="utf-8")

    print(f"OK — {out_json}", file=sys.stderr)
    print(f"OK — {out_txt}", file=sys.stderr)
    print(f"     Classificação: {resultado['classificacao_sugerida']}", file=sys.stderr)
    print(f"     Achados: {len(resultado['achados'])}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
