#!/usr/bin/env python3
"""
insert_comments_rmc.py — Insere Word Comments no .docx da replica.
Uso: python insert_comments_rmc.py <caminho_docx>
"""
import zipfile
import sys
from pathlib import Path
from lxml import etree

SRC = Path(sys.argv[1])
TMP = SRC.with_suffix('.tmp.docx')

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W = f'{{{W_NS}}}'
PKG_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'
XML_NS = 'http://www.w3.org/XML/1998/namespace'

def wt(tag): return f'{W}{tag}'

DATE = "2026-04-26T00:00:00Z"
AUTHOR = "Revisor-RMC"

ACHADOS = [
    {
        "id": 1,
        "sev": "MEDIO",
        "busca": "0745371-43.2022.8.02.0001",
        "texto": (
            "[MEDIO] CNJs dos precedentes TJAL (0745371-43.2022.8.02.0001 e 0740736-48.2024.8.02.0001) "
            "nao constam do _facts.json pois sao precedentes externos ao processo. "
            "As datas 15/05/2024 e 05/02/2025 tambem nao estao no _facts.json pelo mesmo motivo. "
            "Acao: confirmar autenticidade com a ementa original do TJAL. "
            "Precedentes estao alinhados ao _plano.json — manter se autenticos."
        ),
    },
    {
        "id": 2,
        "sev": "CRITICO-FALSO-POSITIVO",
        "busca": "264,11 mensais dispon",
        "texto": (
            "[CRITICO — FALSO POSITIVO CONFIRMADO] R$ 264,11 nao esta em _facts.json mas e valor derivado: "
            "30% x R$ 880,35 = R$ 264,105 ~ R$ 264,11. Calculo explicitado no texto, bases ancoradas. "
            "Nao requer alteracao."
        ),
    },
    {
        "id": 3,
        "sev": "CRITICO-FALSO-POSITIVO",
        "busca": "1.929,41 pagos",
        "texto": (
            "[CRITICO — FALSO POSITIVO CONFIRMADO] R$ 1.929,41 e R$ 763,41 sao valores derivados: "
            "43 x R$ 44,87 = R$ 1.929,41 (conferido, diferenca zero); "
            "R$ 1.929,41 - R$ 1.166,00 = R$ 763,41 (conferido, diferenca zero). "
            "Prescritos no _plano.json. Bases ancoradas. Nao requer alteracao."
        ),
    },
    {
        "id": 4,
        "sev": "MEDIO",
        "busca": "ambiente eletrônico seguro e auditável",
        "texto": (
            "[MEDIO] Heading duplicado: duas secoes Heading 2 com 'PRATICA ABUSIVA' em sequencia. "
            "'DA PRATICA ABUSIVA E DA NULIDADE CONTRATUAL' (par. 52) e "
            "'DA PRATICA ABUSIVA - NULIDADE CONTRATUAL E SUMULA 532 STJ' (par. 56). "
            "Titulos quase identicos cobrem teses do banco 'ausencia_defeito_servico' e 'ausencia_abusividade'. "
            "Acao sugerida: fundir as duas secoes ou diferenciar os titulos claramente."
        ),
    },
]


def get_para_text(p_elem):
    return ''.join(t.text or '' for t in p_elem.findall(f'.//{wt("t")}'))


def insert_comment_ref(p_elem, comment_id):
    crs = etree.Element(wt('commentRangeStart'))
    crs.set(wt('id'), str(comment_id))
    cre = etree.Element(wt('commentRangeEnd'))
    cre.set(wt('id'), str(comment_id))
    cr_run = etree.Element(wt('r'))
    cr_ref = etree.SubElement(cr_run, wt('commentReference'))
    cr_ref.set(wt('id'), str(comment_id))

    ppr = p_elem.find(wt('pPr'))
    if ppr is not None:
        idx = list(p_elem).index(ppr)
        p_elem.insert(idx + 1, crs)
    else:
        p_elem.insert(0, crs)
    p_elem.append(cre)
    p_elem.append(cr_run)


def make_comment_xml(comments_root, comment_id, author, date, text):
    c = etree.SubElement(comments_root, wt('comment'))
    c.set(wt('id'), str(comment_id))
    c.set(wt('author'), author)
    c.set(wt('date'), date)
    c.set(wt('initials'), 'RV')
    p_el = etree.SubElement(c, wt('p'))
    r_el = etree.SubElement(p_el, wt('r'))
    t_el = etree.SubElement(r_el, wt('t'))
    t_el.set(f'{{{XML_NS}}}space', 'preserve')
    t_el.text = text
    return c


with zipfile.ZipFile(SRC, 'r') as z:
    all_files = {name: z.read(name) for name in z.namelist()}

doc_xml = all_files['word/document.xml']
rels_xml = all_files['word/_rels/document.xml.rels']
ct_xml = all_files['[Content_Types].xml']

doc_tree = etree.fromstring(doc_xml)
body = doc_tree.find(f'.//{wt("body")}')
paragraphs = body.findall(f'.//{wt("p")}')

comments_root = etree.Element(wt('comments'), nsmap={'w': W_NS})

comments_added = 0
for achado in ACHADOS:
    found = False
    for p_elem in paragraphs:
        txt = get_para_text(p_elem)
        if achado['busca'] in txt:
            make_comment_xml(comments_root, achado['id'], AUTHOR, DATE, achado['texto'])
            insert_comment_ref(p_elem, achado['id'])
            print(f"Comment {achado['id']} [{achado['sev']}] -> '{txt[:70]}...'")
            comments_added += 1
            found = True
            break
    if not found:
        print(f"AVISO: paragrafo nao encontrado para '{achado['busca']}'")

doc_xml_new = etree.tostring(doc_tree, xml_declaration=True, encoding='UTF-8', standalone=True)
comments_xml_bytes = etree.tostring(comments_root, xml_declaration=True, encoding='UTF-8', standalone=True)

rels_tree = etree.fromstring(rels_xml)
has_comments = any('comments' in str(el.get('Type', '')).lower() for el in rels_tree)
if not has_comments:
    r = etree.SubElement(rels_tree, f'{{{PKG_NS}}}Relationship')
    r.set('Id', 'rIdComments1')
    r.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments')
    r.set('Target', 'comments.xml')
rels_xml_new = etree.tostring(rels_tree, xml_declaration=True, encoding='UTF-8', standalone=True)

ct_tree = etree.fromstring(ct_xml)
has_ct = any('comments' in str(el.get('PartName', '')).lower() for el in ct_tree)
if not has_ct:
    ov = etree.SubElement(ct_tree, f'{{{CT_NS}}}Override')
    ov.set('PartName', '/word/comments.xml')
    ov.set('ContentType', 'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml')
ct_xml_new = etree.tostring(ct_tree, xml_declaration=True, encoding='UTF-8', standalone=True)

with zipfile.ZipFile(TMP, 'w', zipfile.ZIP_DEFLATED) as zout:
    for name, data in all_files.items():
        if name == 'word/document.xml':
            zout.writestr(name, doc_xml_new)
        elif name == 'word/_rels/document.xml.rels':
            zout.writestr(name, rels_xml_new)
        elif name == '[Content_Types].xml':
            zout.writestr(name, ct_xml_new)
        else:
            zout.writestr(name, data)
    zout.writestr('word/comments.xml', comments_xml_bytes)

TMP.replace(SRC)
print(f"\nSalvo com {comments_added} Word Comments: {SRC}")
