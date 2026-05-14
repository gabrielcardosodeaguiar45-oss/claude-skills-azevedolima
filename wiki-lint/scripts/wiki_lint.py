#!/usr/bin/env python3
"""
wiki-lint: auditoria automatica do vault Obsidian.

Detecta:
1. Wikilinks quebrados
2. Tags fora do vocabulario canonico (_tags.md)
3. Paginas orfas (sem incoming link)
4. Conceitos orfaos (precedentes citados >=2x sem ficha em Precedentes/)
5. Divergencias em datas de precedentes

Gera relatorio markdown em <vault>/_lint/lint-YYYY-MM-DD.md.
"""

import argparse
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

PRECEDENTE_PATTERNS = [
    (r'Tema\s+(\d+)\s+(?:do\s+)?(STF|STJ|TJAM|TST|TJ[A-Z]{2})', 'Tema'),
    (r'EAREsp\s+([\d.]+)', 'EAREsp'),
    (r'EREsp\s+([\d.]+)', 'EREsp'),
    (r'REsp\s+([\d.]+)', 'REsp'),
    (r'AREsp\s+([\d.]+)', 'AREsp'),
    (r'S[uú]mula\s+(?:Vinculante\s+)?(\d+)\s+(?:do\s+)?(STF|STJ|TST)', 'Sumula'),
    (r'ADI\s+(\d+)', 'ADI'),
    (r'IRDR\s+(\d+)', 'IRDR'),
]

DATA_RE = re.compile(r'\b(\d{1,2}/\d{1,2}/\d{4})\b')
DATA_COM_KEYWORD_RE = re.compile(
    r'(?:publicad[oa]\s+(?:em\s+)?|julgad[oa]\s+(?:em\s+)?|j\.\s+|DJe[-\s]?[\d\s]*\s*(?:de\s+)?|acórdão\s+(?:de\s+)?|tr[aâ]nsito\s+em\s+julgado\s+(?:em\s+)?|relat(?:or|ado)\s+[^,]*,?\s*)(\d{1,2}/\d{1,2}/\d{4})',
    re.IGNORECASE,
)
WIKILINK_RE = re.compile(r'\[\[([^\]]+?)\]\]')
TAG_INLINE_RE = re.compile(r'(?<![a-zA-Z0-9_/-])#([a-zA-Z][a-zA-Z0-9_/-]*)')
HEX_COLOR_RE = re.compile(r'^[0-9a-fA-F]{3,8}$')
FRONTMATTER_RE = re.compile(r'\A---\n(.*?)\n---', re.DOTALL)

ORFA_EXCLUSIONS_PATTERNS = [
    re.compile(r'^_index$'),
    re.compile(r'^_MOC$'),
    re.compile(r'^MOC-'),
    re.compile(r'^_template$'),
    re.compile(r'^_tags$'),
    re.compile(r'^Home$'),
    re.compile(r'^README$'),
    re.compile(r'^_checkpoint'),
    re.compile(r'^Bem-vindo$'),
]

EXCLUDED_DIRS = {'.obsidian', '.trash', '_lint', 'node_modules', '.git'}


def parse_canonical_tags(tags_md_path):
    """Vocabulario canonico: tags em backticks dentro de _tags.md."""
    text = tags_md_path.read_text(encoding='utf-8')
    return {m.group(1) for m in re.finditer(r'`#([a-zA-Z][a-zA-Z0-9_/-]*)`', text)}


def find_md_files(vault_path):
    files = []
    for p in vault_path.rglob('*.md'):
        rel_parts = p.relative_to(vault_path).parts
        if any(part in EXCLUDED_DIRS for part in rel_parts):
            continue
        files.append(p)
    return files


def file_canonical_name(path, vault_path):
    return str(path.relative_to(vault_path).with_suffix('')).replace('\\', '/')


def file_basename(path):
    return path.stem


def parse_frontmatter(text):
    """Retorna dict com tags e aliases extraidos do frontmatter."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {'tags': set(), 'aliases': set(), 'end': 0}

    fm = m.group(1)
    tags = set()
    aliases = set()

    # tags: [a, b, c]
    inline_tags = re.search(r'^tags:\s*\[(.*?)\]', fm, re.MULTILINE)
    if inline_tags:
        for t in inline_tags.group(1).split(','):
            t = t.strip().strip('"').strip("'").lstrip('#')
            if t:
                tags.add(t)

    # tags:\n  - a\n  - b
    list_tags = re.search(r'^tags:\s*\n((?:\s*-\s*\S.*\n?)+)', fm, re.MULTILINE)
    if list_tags:
        for line in list_tags.group(1).split('\n'):
            line = line.strip()
            if line.startswith('-'):
                t = line[1:].strip().strip('"').strip("'").lstrip('#')
                if t:
                    tags.add(t)

    # aliases idem
    inline_al = re.search(r'^aliases:\s*\[(.*?)\]', fm, re.MULTILINE)
    if inline_al:
        for a in inline_al.group(1).split(','):
            a = a.strip().strip('"').strip("'")
            if a:
                aliases.add(a)
    list_al = re.search(r'^aliases:\s*\n((?:\s*-\s*\S.*\n?)+)', fm, re.MULTILINE)
    if list_al:
        for line in list_al.group(1).split('\n'):
            line = line.strip()
            if line.startswith('-'):
                a = line[1:].strip().strip('"').strip("'")
                if a:
                    aliases.add(a)

    return {'tags': tags, 'aliases': aliases, 'end': m.end()}


def extract_inline_tags(text, body_start):
    body = text[body_start:]
    body = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
    body = re.sub(r'`[^`]*`', '', body)
    body = re.sub(r'^#{1,6}\s.*$', '', body, flags=re.MULTILINE)
    out = set()
    for m in TAG_INLINE_RE.finditer(body):
        tag = m.group(1)
        # Exclui cores hex (3-8 chars hex puro = provavelmente cor, nao tag)
        if HEX_COLOR_RE.match(tag) and len(tag) in (3, 6, 8):
            continue
        out.add(tag)
    return out


def candidates_for_wikilink(target, source_file, vault):
    """Lista os caminhos canonicos possiveis para um wikilink Obsidian.

    Obsidian resolve por (a) basename quando unico, (b) path absoluto do vault,
    (c) path relativo ao arquivo atual (com `./` `../` ou implicito quando ha `/`).
    Geramos os 3 candidatos.
    """
    target = target.rstrip('\\').strip()
    out = [target]
    try:
        base = source_file.parent
        abs_p = (base / target).resolve()
        rel = abs_p.relative_to(vault.resolve())
        out.append(str(rel).replace('\\', '/'))
    except (ValueError, OSError):
        pass
    if '/' in target:
        out.append(target.rsplit('/', 1)[-1])
    return out


def extract_wikilinks(text, source_file, vault):
    """Retorna lista de tuplas (target_original, candidatos[])."""
    out = []
    for m in WIKILINK_RE.finditer(text):
        raw = m.group(1).strip().rstrip('\\')
        target = raw.split('|', 1)[0].split('#', 1)[0].strip().rstrip('\\')
        if target:
            cands = candidates_for_wikilink(target, source_file, vault)
            out.append((target, cands))
    return out


def extract_precedentes(text):
    found = []
    for pattern, kind in PRECEDENTE_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            full = m.group(0).strip()
            ident = normalize_precedente(full, kind)
            # Janela apertada (120 chars) e EXIGE keyword (publicado/julgado/DJe/...)
            data_search = text[max(0, m.start() - 120):min(len(text), m.end() + 120)]
            data_match = DATA_COM_KEYWORD_RE.search(data_search)
            data = data_match.group(1) if data_match else None
            line_start = text.rfind('\n', 0, m.start()) + 1
            line_end = text.find('\n', m.end())
            if line_end == -1:
                line_end = len(text)
            context = text[line_start:line_end].strip()[:200]
            found.append({
                'tipo': kind,
                'identificador': ident,
                'data': data,
                'contexto': context,
            })
    return found


def normalize_precedente(full, kind):
    """Normaliza identificador para agrupamento (remove pontos em numeros, padroniza case)."""
    s = re.sub(r'\s+', ' ', full).strip()
    # Remove pontos de milhares em numeros (1.280.825 -> 1280825)
    s = re.sub(r'(\d)\.(\d)', r'\1\2', s)
    # Capitaliza prefixo
    parts = s.split(' ', 1)
    if len(parts) == 2:
        prefix = kind  # usa o kind canonico
        rest = parts[1]
        # Para Tema/Sumula com tribunal no final, deixa tribunal upper
        m = re.match(r'(\d+)\s+(.+)', rest)
        if m:
            return f'{prefix} {m.group(1)} {m.group(2).upper()}'
        return f'{prefix} {rest}'
    return s


def resolve_wikilink(target, by_canonical, by_basename, by_alias):
    t = target.strip()
    if t in by_canonical or t in by_basename or t in by_alias:
        return True
    tl = t.lower()
    if tl in {k.lower() for k in by_canonical}:
        return True
    if tl in {k.lower() for k in by_basename}:
        return True
    if tl in {k.lower() for k in by_alias}:
        return True
    return False


def slugify_precedente(ident):
    s = ident.lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'\s+', '-', s).strip('-')
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('vault', help='Caminho do vault Obsidian')
    ap.add_argument('--saida', help='Caminho do relatorio (default: <vault>/_lint/lint-YYYY-MM-DD.md)')
    ap.add_argument('--orfa-min-tamanho', type=int, default=200,
                    help='Tamanho minimo (chars) para considerar orfao')
    args = ap.parse_args()

    vault = Path(args.vault)
    if not vault.exists() or not vault.is_dir():
        print(f'ERRO: vault invalido: {vault}', file=sys.stderr)
        sys.exit(1)

    tags_md = vault / '_tags.md'
    canonical_tags = parse_canonical_tags(tags_md) if tags_md.exists() else set()

    md_files = find_md_files(vault)
    by_canonical = {file_canonical_name(f, vault) for f in md_files}
    by_basename = {file_basename(f) for f in md_files}
    by_alias = set()

    file_data = {}

    for f in md_files:
        try:
            text = f.read_text(encoding='utf-8')
        except Exception as e:
            print(f'AVISO: erro lendo {f}: {e}', file=sys.stderr)
            continue
        fm = parse_frontmatter(text)
        by_alias.update(fm['aliases'])
        inline_tags = extract_inline_tags(text, fm['end'])
        all_tags = fm['tags'] | inline_tags
        wls = extract_wikilinks(text, f, vault)
        precs = extract_precedentes(text)
        file_data[f] = {
            'wikilinks': wls,
            'tags': all_tags,
            'aliases': fm['aliases'],
            'precedentes': precs,
            'size': len(text),
        }

    # Grafo de incoming (registra todos os candidatos como destinos)
    incoming = defaultdict(set)
    for f, d in file_data.items():
        origem = file_canonical_name(f, vault)
        for target_orig, cands in d['wikilinks']:
            for c in cands:
                incoming[c].add(origem)
                if '/' in c:
                    incoming[c.rsplit('/', 1)[-1]].add(origem)

    # 1. Wikilinks quebrados (todos os candidatos falharam)
    broken = []
    for f, d in file_data.items():
        origem = file_canonical_name(f, vault)
        for target_orig, cands in d['wikilinks']:
            if not any(resolve_wikilink(c, by_canonical, by_basename, by_alias) for c in cands):
                broken.append({'origem': origem, 'destino': target_orig})

    # 2. Tags invalidas
    invalid_tags = []
    if canonical_tags:
        for f, d in file_data.items():
            arq = file_canonical_name(f, vault)
            for tag in d['tags']:
                if tag not in canonical_tags:
                    invalid_tags.append({'arquivo': arq, 'tag': tag})

    # 3. Paginas orfas
    orfas = []
    for f, d in file_data.items():
        canon = file_canonical_name(f, vault)
        base = file_basename(f)
        if any(p.match(base) for p in ORFA_EXCLUSIONS_PATTERNS):
            continue
        if d['size'] < args.orfa_min_tamanho:
            continue
        # Tem incoming?
        if canon in incoming or base in incoming:
            continue
        # Algum alias dele tem incoming?
        if any(a in incoming for a in d['aliases']):
            continue
        orfas.append(canon)

    # 4. Conceitos orfaos e 5. Divergencias
    all_precs = defaultdict(list)
    for f, d in file_data.items():
        arq = file_canonical_name(f, vault)
        for p in d['precedentes']:
            all_precs[p['identificador']].append({
                'arquivo': arq,
                'data': p['data'],
                'contexto': p['contexto'],
                'tipo': p['tipo'],
            })

    def dedup_por_arquivo(cits):
        """Mantem 1 citacao por arquivo (preferindo a que tem data)."""
        por_arq = {}
        for c in cits:
            arq = c['arquivo']
            if arq not in por_arq or (c['data'] and not por_arq[arq]['data']):
                por_arq[arq] = c
        return list(por_arq.values())

    conceitos_orfaos = []
    fichas_em_teses = []
    divergencias = []
    for ident, cits in all_precs.items():
        if len(cits) < 2:
            continue
        cits_dedup = dedup_por_arquivo(cits)
        if len(cits_dedup) < 2:
            continue
        tem_ficha_precedentes = any('Precedentes/' in c['arquivo'] for c in cits_dedup)
        tem_ficha_teses = any('Teses/' in c['arquivo'] for c in cits_dedup)
        if not tem_ficha_precedentes:
            entry = {'precedente': ident, 'citacoes': cits_dedup, 'tem_em_teses': tem_ficha_teses}
            if tem_ficha_teses:
                fichas_em_teses.append(entry)
            else:
                conceitos_orfaos.append(entry)
        datas_por_arq = {c['arquivo']: c['data'] for c in cits_dedup if c['data']}
        datas = sorted(set(datas_por_arq.values()))
        if len(datas) > 1:
            divergencias.append({
                'precedente': ident,
                'datas_encontradas': datas,
                'citacoes': [c for c in cits_dedup if c['data']],
            })

    # Relatorio
    today = date.today().isoformat()
    if args.saida:
        out_path = Path(args.saida)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = vault / '_lint'
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f'lint-{today}.md'

    L = []
    L.append('---')
    L.append('tipo: lint')
    L.append(f'data: {today}')
    L.append('tags: [meta, lint]')
    L.append('---')
    L.append('')
    L.append(f'# Wiki Lint — {today}')
    L.append('')
    L.append(f'Auditoria automatica gerada pela skill `wiki-lint`.')
    L.append('')
    L.append(f'**Estatisticas**: {len(md_files)} arquivos analisados.')
    L.append('')
    L.append('## Resumo')
    L.append('')
    L.append('| Categoria | Total |')
    L.append('|---|---:|')
    L.append(f'| Wikilinks quebrados | {len(broken)} |')
    L.append(f'| Tags fora do vocabulario | {len(invalid_tags)} |')
    L.append(f'| Paginas orfas | {len(orfas)} |')
    L.append(f'| Conceitos orfaos (sem ficha em Precedentes/ nem Teses/) | {len(conceitos_orfaos)} |')
    L.append(f'| Precedentes em Teses/ sem ficha consolidada em Precedentes/ | {len(fichas_em_teses)} |')
    L.append(f'| Divergencias em precedentes | {len(divergencias)} |')
    L.append('')

    # 1
    L.append('## 1. Wikilinks quebrados')
    L.append('')
    if not broken:
        L.append('_Nenhum wikilink quebrado._')
    else:
        por_origem = defaultdict(list)
        for b in broken:
            por_origem[b['origem']].append(b['destino'])
        for origem in sorted(por_origem):
            destinos = sorted(set(por_origem[origem]))
            L.append(f'**[[{origem}]]** cita destinos inexistentes:')
            L.append('')
            for d in destinos:
                L.append(f'1. `[[{d}]]`')
            L.append('')
    L.append('')

    # 2
    L.append('## 2. Tags fora do vocabulario canonico')
    L.append('')
    if not canonical_tags:
        L.append('_Sem `_tags.md` no vault — verificacao ignorada._')
    elif not invalid_tags:
        L.append('_Todas as tags estao no vocabulario._')
    else:
        por_arq = defaultdict(set)
        for it in invalid_tags:
            por_arq[it['arquivo']].add(it['tag'])
        for arq in sorted(por_arq):
            tags_str = ', '.join(f'`#{t}`' for t in sorted(por_arq[arq]))
            L.append(f'1. **[[{arq}]]**: {tags_str}')
        L.append('')
        L.append('> Vocabulario em [[_tags]]. Tag nova exige update do `_tags.md` antes.')
    L.append('')

    # 3
    L.append('## 3. Paginas orfas')
    L.append('')
    L.append(f'Sem incoming wikilink (excluindo estruturais e arquivos < {args.orfa_min_tamanho} chars).')
    L.append('')
    if not orfas:
        L.append('_Nenhuma pagina orfa._')
    else:
        for p in sorted(orfas):
            L.append(f'1. [[{p}]]')
    L.append('')

    # 4
    L.append('## 4. Conceitos orfaos (precedentes citados >=2x sem ficha)')
    L.append('')
    L.append('### 4.1. Sem ficha em Precedentes/ nem em Teses/')
    L.append('')
    if not conceitos_orfaos:
        L.append('_Nenhum conceito sem ficha._')
    else:
        for c in sorted(conceitos_orfaos, key=lambda x: -len(x['citacoes'])):
            L.append(f'#### {c["precedente"]}')
            L.append('')
            L.append(f'Citado em {len(c["citacoes"])} arquivo(s) distintos:')
            L.append('')
            for cit in sorted(c['citacoes'], key=lambda x: x['arquivo']):
                data_str = f' (data: {cit["data"]})' if cit['data'] else ''
                L.append(f'1. [[{cit["arquivo"]}]]{data_str}')
            L.append('')
            slug = slugify_precedente(c['precedente'])
            L.append(f'> Sugestao: criar `Precedentes/{slug}.md` consolidando.')
            L.append('')
    L.append('')
    L.append('### 4.2. Em Teses/ mas sem ficha consolidada em Precedentes/')
    L.append('')
    L.append('_Estes precedentes ja sao tema de uma ficha de tese, mas nao tem ficha de precedente isolada. Pode ser intencional (tese e o foco) ou pode pedir consolidacao._')
    L.append('')
    if not fichas_em_teses:
        L.append('_Nenhum._')
    else:
        for c in sorted(fichas_em_teses, key=lambda x: -len(x['citacoes'])):
            L.append(f'#### {c["precedente"]}')
            L.append('')
            L.append(f'Citado em {len(c["citacoes"])} arquivo(s) distintos:')
            L.append('')
            for cit in sorted(c['citacoes'], key=lambda x: x['arquivo']):
                data_str = f' (data: {cit["data"]})' if cit['data'] else ''
                L.append(f'1. [[{cit["arquivo"]}]]{data_str}')
            L.append('')
    L.append('')

    # 5
    L.append('## 5. Divergencias em datas de precedentes')
    L.append('')
    if not divergencias:
        L.append('_Nenhuma divergencia._')
    else:
        for d in divergencias:
            L.append(f'### {d["precedente"]}')
            L.append('')
            L.append(f'Datas distintas: {", ".join(d["datas_encontradas"])}')
            L.append('')
            for cit in d['citacoes']:
                if cit['data']:
                    L.append(f'1. [[{cit["arquivo"]}]] -> **{cit["data"]}**')
            L.append('')
            L.append('> Verificar qual e correta e padronizar.')
            L.append('')

    L.append('')
    L.append('---')
    L.append('')
    L.append(f'_Para reaplicar: `python ~/.claude/skills/wiki-lint/scripts/wiki_lint.py "{vault}"`._')

    out_path.write_text('\n'.join(L), encoding='utf-8')

    print(f'Relatorio: {out_path}')
    print(f'  Wikilinks quebrados: {len(broken)}')
    print(f'  Tags invalidas: {len(invalid_tags)}')
    print(f'  Paginas orfas: {len(orfas)}')
    print(f'  Conceitos orfaos: {len(conceitos_orfaos)}')
    print(f'  Divergencias: {len(divergencias)}')


if __name__ == '__main__':
    main()
