# -*- coding: utf-8 -*-
"""Pente fino nos 6 templates Bradesco: busca tudo que parece hardcoded mas
deveria ser placeholder. NÃO altera nada — só lista para revisão humana."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
from docx import Document
from collections import defaultdict

VAULT = Path(r"C:\Users\gabri\OneDrive\Documentos\Obsidian Vault\Modelos\IniciaisBradesco\_templates")

TEMPLATES = ["inicial-mora.docx", "inicial-mora-encargo.docx",
             "inicial-tarifas.docx", "inicial-aplic-invest.docx",
             "inicial-pg-eletron.docx", "inicial-combinada.docx"]

# ============================================================
# CATEGORIAS DE BUSCA
# ============================================================

def cat_profissao(t):
    """Profissões/condição soltas (não dentro de {{...}})."""
    out = []
    # Não pegar palavras que estão dentro de placeholders
    t_sanitized = re.sub(r"\{\{[^}]+\}\}", "___PH___", t)
    palavras = [
        r"aposentad[oa]", r"pensionist[oa]", r"trabalhador(?:a)?\s+rural",
        r"do\s+lar", r"agricultor(?:a)?", r"servidor(?:a)?\s+público",
        r"funcionário\s+público", r"benefici[áa]ri[oa]\s+do\s+INSS",
        r"segurad[oa]\s+do\s+INSS",
    ]
    for p in palavras:
        for m in re.finditer(p, t_sanitized, re.IGNORECASE):
            out.append(("profissão/condição", m.group(0)))
    return out

def cat_comarca(t):
    """Comarcas, UFs, varas hardcoded (template AL não deve ter AM/SC etc)."""
    out = []
    t_sanitized = re.sub(r"\{\{[^}]+\}\}", "___PH___", t)
    # Comarcas conhecidas que podem ser sobra de templates antigos
    cidades = [
        "Manaus", "Boa Vista do Ramos", "Maués", "Capinzal", "Joaçaba",
        "Salvador", "Recife", "Belo Horizonte", "Maceió", "Arapiraca",
        "Penedo", "Coruripe",
    ]
    for c in cidades:
        for m in re.finditer(rf"\b{c}\b", t_sanitized):
            out.append(("comarca/cidade", m.group(0)))
    # UFs
    for m in re.finditer(r"\b/(AM|AL|BA|MG|PE|RS|SC|SP|RJ)\b", t_sanitized):
        out.append(("UF", m.group(0)))
    # Varas/Juízos
    for m in re.finditer(r"\d+ª\s+Vara", t_sanitized):
        out.append(("vara", m.group(0)))
    return out

def cat_valores_rs(t):
    """Valores monetários literais R$ X,XX (fora de placeholder)."""
    out = []
    t_sanitized = re.sub(r"\{\{[^}]+\}\}", "___PH___", t)
    for m in re.finditer(r"R\$\s*[\d\.]+,\d{2}", t_sanitized):
        out.append(("valor R$", m.group(0)))
    # Valor sem R$ tipo "15.000,00"
    for m in re.finditer(r"\b\d{1,3}(?:\.\d{3})+,\d{2}\b", t_sanitized):
        out.append(("valor numérico", m.group(0)))
    return out

def cat_datas(t):
    """Datas literais DD/MM/YYYY."""
    out = []
    t_sanitized = re.sub(r"\{\{[^}]+\}\}", "___PH___", t)
    for m in re.finditer(r"\b\d{2}/\d{2}/\d{4}\b", t_sanitized):
        out.append(("data", m.group(0)))
    return out

def cat_genero(t):
    """Forma flexionada (sem o(a)/o/a entre parênteses)."""
    out = []
    t_sanitized = re.sub(r"\{\{[^}]+\}\}", "___PH___", t)
    # 'a parte autora' está OK (gênero neutro);
    # 'o autor' / 'a autora' (sem '(a)') é hardcode
    for m in re.finditer(r"\bo\s+autor(?!a|izad)\b", t_sanitized):
        out.append(("gênero hard", m.group(0)))
    for m in re.finditer(r"\ba\s+autora\b", t_sanitized):
        out.append(("gênero hard", m.group(0)))
    # Sr./Sra. fixos
    for m in re.finditer(r"\bSr(?:a)?\.\s+[A-Z]", t_sanitized):
        out.append(("Sr/Sra hard", m.group(0)))
    return out

def cat_estado_civil(t):
    """Estado civil literal."""
    out = []
    t_sanitized = re.sub(r"\{\{[^}]+\}\}", "___PH___", t)
    palavras = [r"solteir[oa]", r"casad[oa]", r"divorciad[oa]",
                r"viúv[oa]", r"separad[oa]", r"união\s+estável"]
    for p in palavras:
        for m in re.finditer(p, t_sanitized, re.IGNORECASE):
            # Filtrar 'casado' que aparece em "casado o entendimento"
            ctx = t_sanitized[max(0, m.start()-15):m.end()+15]
            if "RAIZEL" in ctx or "advogado" in ctx.lower():
                continue
            out.append(("estado civil", m.group(0)))
    return out

def cat_documentos(t):
    """CPF/RG/Agência/Conta literais."""
    out = []
    t_sanitized = re.sub(r"\{\{[^}]+\}\}", "___PH___", t)
    for m in re.finditer(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", t_sanitized):
        out.append(("CPF literal", m.group(0)))
    for m in re.finditer(r"\bCPF\s*(?:n[º°]?\s*)?\d{6,}", t_sanitized):
        out.append(("CPF literal", m.group(0)))
    return out

def cat_outros_bancos(t):
    """Banco diferente de Bradesco/INSS (pode ser sobra de template não-Bradesco)."""
    out = []
    t_sanitized = re.sub(r"\{\{[^}]+\}\}", "___PH___", t)
    bancos = ["Itaú", "Santander", "BMG", "PAN", "C6", "Caixa Econômica",
              "Mercantil", "Inter", "Daycoval", "Agibank", "Crefisa",
              "Bonsucesso", "Olé", "Inbursa", "Digio", "Master"]
    for b in bancos:
        for m in re.finditer(rf"\b{re.escape(b)}\b", t_sanitized):
            ctx = t_sanitized[max(0, m.start()-20):m.end()+20]
            out.append(("banco diferente", f"{m.group(0)} ({ctx[:60]}...)"))
    return out

def cat_nomes_proprios(t):
    """Nomes próprios soltos (sobras de casos)."""
    out = []
    t_sanitized = re.sub(r"\{\{[^}]+\}\}", "___PH___", t)
    # Lista de nomes que apareceram em runs anteriores
    nomes = ["Cécila", "Otaviano", "Idalvo", "Joaquim", "Maria", "José",
             "Francisco", "Domício", "Edina", "Luiz", "João", "Manuel",
             "Vitor", "Raimunda", "Raimundo", "Sebastião", "Mídia",
             "Nilciene", "Cláudio", "Ana", "Denival", "Elinaldo"]
    for n in nomes:
        for m in re.finditer(rf"\b{n}\b", t_sanitized):
            ctx = t_sanitized[max(0, m.start()-20):m.end()+30]
            # Filtrar se o nome aparece como parte do título da peça (Maria não é raro)
            out.append(("nome próprio", f"{m.group(0)} (...{ctx[:80]}...)"))
    return out

CATEGORIAS = {
    "profissão": cat_profissao,
    "comarca/UF/vara": cat_comarca,
    "valor R$ literal": cat_valores_rs,
    "data literal": cat_datas,
    "gênero hardcoded": cat_genero,
    "estado civil": cat_estado_civil,
    "CPF/RG literal": cat_documentos,
    "outros bancos": cat_outros_bancos,
    "nome próprio": cat_nomes_proprios,
}


def varrer_template(nome_arq):
    caminho = VAULT / nome_arq
    if not caminho.exists():
        return None
    doc = Document(caminho)
    achados = defaultdict(list)
    for i, p in enumerate(doc.paragraphs):
        t = p.text
        for nome_cat, fn in CATEGORIAS.items():
            for tag, match in fn(t):
                achados[nome_cat].append((i, match, t[:120]))
    return dict(achados)


for nome in TEMPLATES:
    res = varrer_template(nome)
    if res is None:
        print(f"\n=== {nome}: NÃO EXISTE ===")
        continue
    print(f"\n{'='*70}\n{nome}\n{'='*70}")
    if not res:
        print("  ✓ Limpo — nada hardcoded suspeito")
        continue
    for cat, lst in res.items():
        print(f"\n  [{cat}] — {len(lst)} ocorrência(s):")
        for par_i, match, ctx in lst[:5]:
            print(f"    par {par_i}: '{match}'")
            print(f"      ctx: {ctx[:100]}...")
        if len(lst) > 5:
            print(f"    [+ {len(lst)-5} adicional(is)]")
