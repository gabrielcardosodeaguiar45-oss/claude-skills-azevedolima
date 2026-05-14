"""
Biblioteca de análise de HISCON do INSS.
Recebe um caminho/bytes de PDF, retorna dict estruturado com beneficiário, contratos,
cadeias (grafo), red flags e avisos de leitura.
"""
import pdfplumber, re, io, os
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Union

BANCOS_OFICIAIS = {
    '001': 'Banco do Brasil S.A.',
    '012': 'Banco Inbursa S.A.',
    '029': 'Banco Itaú Consignado S.A.',
    '033': 'Banco Santander (Brasil) S.A.',
    '041': 'Banco do Estado do Rio Grande do Sul S.A. (Banrisul)',
    '070': 'BRB Banco de Brasília S.A.',
    '077': 'Banco Inter S.A.',
    '104': 'Caixa Econômica Federal',
    '121': 'Banco Agibank S.A.',
    '237': 'Banco Bradesco S.A.',
    '254': 'Paraná Banco S.A.',
    '318': 'Banco BMG S.A.',
    '320': 'China Construction Bank (Brasil) Banco Múltiplo S.A.',
    '329': 'QI Sociedade de Crédito Direto S.A.',
    '335': 'Banco Digio S.A.',
    '341': 'Banco Itaú S.A.',
    '389': 'Banco Mercantil do Brasil S.A.',
    '394': 'Banco Bradesco Financiamentos S.A.',
    '422': 'Banco Safra S.A.',
    '465': 'Banco Captalys S.A.',
    '623': 'Banco PAN S.A.',
    '626': 'Banco C6 Consignado S.A.',
    '643': 'Banco Pine S.A.',
    '707': 'Banco Daycoval S.A.',
    '739': 'Banco Cetelem S.A.',
    '748': 'Banco Cooperativo Sicredi S.A. (Cresol)',
    '925': 'BRB Crédito, Financiamento e Investimento S.A.',
    '935': 'Facta Financeira S.A.',
}

def _limpar(s):
    if s is None: return ''
    return re.sub(r'\s+', ' ', str(s)).strip()

def _limpar_data(s):
    if s is None: return ''
    return re.sub(r'\s+', '', str(s))

def _parse_date(s):
    s = _limpar_data(s)
    m = re.search(r'(\d{2})/(\d{2})/(\d{2,4})', s)
    if not m: return None
    d, mm, y = m.groups()
    y = int(y)
    if y < 100:
        y = 2000 + y if y < 70 else 1900 + y
    try: return datetime(int(y), int(mm), int(d))
    except: return None

def _parse_money(s):
    s = _limpar(s).replace('R$','').replace(' ','').replace('.','').replace(',','.')
    try: return float(s)
    except: return 0.0

def _parse_num(s):
    s = _limpar(s).replace(',', '.')
    try: return float(re.sub(r'[^\d.]', '', s) or 0)
    except: return 0.0

def _entrada(c):
    if c.get('data_inclusao'): return c['data_inclusao']
    if c.get('data_primeiro_desconto'):
        return c['data_primeiro_desconto'] - timedelta(days=30)
    return None

def _nid(c): return f"{c['numero']}@{c['banco_codigo']}"

def analisar_hiscon(pdf_source: Union[str, bytes, io.IOBase]) -> dict:
    """
    Parseia um PDF HISCON e retorna dict com:
      - beneficiario: dict
      - contratos: list[dict]
      - cadeias: list[list[str]] (cada cadeia é lista de node_ids)
      - ligacoes: list[dict]
      - avisos: list[dict]
      - problemas: list[dict]
      - red_flags: list[dict] (por cadeia)
      - estatisticas: dict
    """
    avisos, problemas = [], []
    def add_aviso(tipo, texto, contrato=None):
        avisos.append({'tipo': tipo, 'texto': texto, 'contrato': contrato})

    beneficiario = {}
    contratos = []

    if isinstance(pdf_source, bytes):
        pdf_source = io.BytesIO(pdf_source)

    # No Windows, paths > 260 chars precisam de prefixo \\?\ para o open()
    # nativo do Python (pdfplumber usa open() padrão, sem APIs Win32).
    if (isinstance(pdf_source, str) and os.name == 'nt'
            and len(pdf_source) > 240 and not pdf_source.startswith('\\\\?\\')):
        pdf_source = '\\\\?\\' + os.path.abspath(pdf_source)

    with pdfplumber.open(pdf_source) as pdf:
        p1 = pdf.pages[0].extract_text() or ''
        m = re.search(r'([A-ZÁ-Ú ]{5,})\nBenefício\n([^\n]+)', p1)
        if m:
            beneficiario['nome'] = _limpar(m.group(1))
            beneficiario['beneficio'] = _limpar(m.group(2))
        m = re.search(r'N[ºo°]\s*Benef[íi]cio[:\s]+([\d.\-]+)', p1)
        if m: beneficiario['numero_beneficio'] = m.group(1)
        m = re.search(r'Pago em:\s*([^\n]+)', p1)
        if m: beneficiario['banco_pagador'] = _limpar(m.group(1))

        p2 = pdf.pages[1].extract_text() if len(pdf.pages) > 1 else ''
        m = re.search(r'BASE DE CÁLCULO\s+R\$\s*([\d.,]+)', p2 or '')
        if m: beneficiario['base_calculo'] = _parse_money(m.group(1))
        m = re.search(r'MÁXIMO DE COMPROMETIMENTO PERMITIDO\s+R\$\s*([\d.,]+)', p2 or '')
        if m: beneficiario['max_comprometimento'] = _parse_money(m.group(1))
        m = re.search(r'TOTAL COMPROMETIDO\s+R\$\s*([\d.,]+)', p2 or '')
        if m: beneficiario['total_comprometido'] = _parse_money(m.group(1))

        for page in pdf.pages:
            for t in page.extract_tables():
                if not t or len(t) < 4: continue
                header = _limpar(t[0][0] or '')
                if 'ATIVOS' not in header and 'EXCLU' not in header and 'ENCERRAD' not in header:
                    continue

                rows = [list(r) + ['']*(25-len(r)) for r in t[3:]]
                merged = []
                for row in rows:
                    num = re.sub(r'\s+', '', str(row[0] or ''))
                    if merged and re.fullmatch(r'\d{1,5}', num) and str(merged[-1][0] or '').rstrip().endswith('-'):
                        merged[-1][0] = re.sub(r'\s+','',str(merged[-1][0])) + num
                        continue
                    if 0 < len(num) < 6 and not re.search(r'\d{5,}', num):
                        add_aviso('linha_fragmentada', f'Linha com número curto "{num}" descartada.')
                        continue
                    merged.append(row)

                for row in merged:
                    if not row[0] or not re.search(r'\d', str(row[0])): continue
                    contrato_num = re.sub(r'\s+', '', str(row[0]))
                    if len(contrato_num) < 5: continue

                    banco_full = _limpar(row[1])
                    mb = re.match(r'(\d+)\s*-\s*(.+)', banco_full)
                    banco_codigo = mb.group(1) if mb else ''
                    banco_nome_raw = _limpar(mb.group(2)) if mb else banco_full
                    banco_nome = BANCOS_OFICIAIS.get(banco_codigo, banco_nome_raw)
                    if len(banco_nome_raw) < 10 and banco_codigo in BANCOS_OFICIAIS:
                        add_aviso('banco_normalizado', f'Nome reconstruído via FEBRABAN: {banco_nome_raw!r} → {banco_nome!r}', contrato_num)

                    situacao = _limpar(row[2]).replace(' ', '')
                    origem_averb = _limpar(row[3])
                    data_incl = _parse_date(row[4])
                    # row[5] = COMPETÊNCIA INÍCIO DE DESCONTO ("06/2021")
                    # row[6] = COMPETÊNCIA FIM DE DESCONTO    ("02/2024")
                    comp_ini_desc = _limpar(row[5]) if len(row) > 5 else ''
                    comp_fim_desc = _limpar(row[6]) if len(row) > 6 else ''
                    qtd_parc = int(_parse_num(row[7]))
                    valor_parc = _parse_money(row[8])
                    valor_emp = _parse_money(row[9])
                    valor_lib = _parse_money(row[10])
                    iof = _parse_money(row[11])
                    cet_m = _parse_num(row[12])
                    cet_a = _parse_num(row[13])
                    juros_m = _parse_num(row[14])
                    juros_a = _parse_num(row[15])
                    valor_pago = _parse_money(row[16])
                    data_prim_desc = _parse_date(row[17])
                    data_exclusao = _parse_date(row[22])
                    motivo_exclusao = _limpar(row[23])

                    origem_norm = origem_averb.lower().replace(' ', '')
                    if 'migrado' in origem_norm: tipo_origem = 'migracao'
                    elif 'refinan' in origem_norm: tipo_origem = 'refinanciamento'
                    elif 'portabil' in origem_norm: tipo_origem = 'portabilidade'
                    elif 'nova' in origem_norm: tipo_origem = 'original'
                    else:
                        tipo_origem = 'desconhecido'
                        add_aviso('origem_desconhecida', f'Tipo de origem não classificado ({origem_averb!r}).', contrato_num)

                    migrado_de = None
                    m2 = re.search(r'contrato\s+([\d\-]+)', origem_averb.replace('\n',' '))
                    if m2 and tipo_origem == 'migracao':
                        migrado_de = re.sub(r'[^\d]', '', m2.group(1))

                    contratos.append({
                        'numero': contrato_num,
                        'banco_codigo': banco_codigo,
                        'banco_nome': banco_nome,
                        'banco_nome_raw': banco_nome_raw,
                        'situacao': situacao,
                        'origem_averbacao': origem_averb,
                        'tipo_origem': tipo_origem,
                        'migrado_de': migrado_de,
                        'data_inclusao': data_incl,
                        'qtd_parcelas': qtd_parc,
                        'valor_parcela': valor_parc,
                        'valor_emprestado': valor_emp,
                        'valor_liberado': valor_lib,
                        'iof': iof,
                        'cet_mensal': cet_m,
                        'cet_anual': cet_a,
                        'juros_mensal': juros_m,
                        'juros_anual': juros_a,
                        'valor_pago': valor_pago,
                        'data_primeiro_desconto': data_prim_desc,
                        'data_exclusao': data_exclusao,
                        'motivo_exclusao': motivo_exclusao,
                        # Competências EFETIVAS de desconto (colunas 5 e 6 do HISCON):
                        # 'mm/yyyy'. São a fonte autoritativa para a data fim — não
                        # devem ser estimadas via (data_exclusao − 1 mês).
                        'competencia_inicio_desconto': comp_ini_desc,
                        'competencia_fim_desconto': comp_fim_desc,
                    })

    # ===== CADEIAS =====
    nodes = {_nid(c): c for c in contratos}
    edges = defaultdict(list); rev_edges = defaultdict(list)
    ligacoes = []
    def add_edge(p, s, regra, conf):
        if s in edges[p]: return
        edges[p].append(s); rev_edges[s].append(p)
        ligacoes.append({'pred': p, 'suc': s, 'regra': regra, 'confianca': conf})

    usados_pred, usados_suc = set(), set()

    for c in contratos:
        if c['tipo_origem'] == 'migracao' and c['migrado_de']:
            num_atual = re.sub(r'[-/]', '', c['numero'])
            cands = []
            for p in contratos:
                if p is c or _nid(p) == _nid(c): continue
                num_p = re.sub(r'[-/]', '', p['numero'])
                score = 100 if num_p == num_atual else (10 if (num_p.startswith(c['migrado_de']) or c['migrado_de'] in num_p) else 0)
                if score > 0:
                    if p['data_exclusao']: score += 50
                    cands.append((score, p))
            cands.sort(key=lambda x: -x[0])
            if cands:
                add_edge(_nid(cands[0][1]), _nid(c), 'migração', 'alta')
                usados_pred.add(_nid(cands[0][1])); usados_suc.add(_nid(c))

    ativos_novos = [c for c in contratos if c['tipo_origem'] in ('refinanciamento','portabilidade','migracao')]
    excluidos_refin = [c for c in contratos if c['data_exclusao'] and any(k in (c['motivo_exclusao'] or '').lower() for k in ('refinan','portabili','troca'))]

    for suc in sorted(ativos_novos, key=lambda x: _entrada(x) or datetime.max):
        if _nid(suc) in usados_suc: continue
        e = _entrada(suc)
        if not e: continue
        melhor, melhor_dt = None, None
        for pred in excluidos_refin:
            if _nid(pred) in usados_pred: continue
            de = pred['data_exclusao']
            if not de: continue
            delta = (e - de).days
            if not (-60 <= delta <= 60): continue
            if abs(pred['valor_parcela'] - suc['valor_parcela']) < 0.01:
                if melhor is None or abs(delta) < melhor_dt:
                    melhor, melhor_dt = pred, abs(delta)
        if melhor:
            add_edge(_nid(melhor), _nid(suc), 'parcela_igual', 'alta')
            usados_pred.add(_nid(melhor)); usados_suc.add(_nid(suc))

    pred_por_data = defaultdict(list)
    for pred in excluidos_refin:
        if _nid(pred) in usados_pred: continue
        if pred['data_exclusao']: pred_por_data[pred['data_exclusao'].date()].append(pred)

    for data_ex, preds in pred_por_data.items():
        sucs = [s for s in ativos_novos if _nid(s) not in usados_suc and _entrada(s) and -10 <= (_entrada(s).date()-data_ex).days <= 60]
        if not sucs or not preds: continue
        soma_preds = sum(p['valor_parcela'] for p in preds)
        soma_sucs = sum(s['valor_parcela'] for s in sucs)
        for s in sucs:
            if abs(s['valor_parcela']-soma_preds) < 0.5 and len(preds) > 1:
                for p in preds: add_edge(_nid(p), _nid(s), f'consolidação {len(preds)}→1', 'média'); usados_pred.add(_nid(p))
                usados_suc.add(_nid(s)); break
        for p in preds:
            if _nid(p) in usados_pred: continue
            if abs(p['valor_parcela']-soma_sucs) < 0.5 and len(sucs) > 1:
                for s in sucs:
                    if _nid(s) in usados_suc: continue
                    add_edge(_nid(p), _nid(s), f'fracionamento 1→{len(sucs)}', 'média'); usados_suc.add(_nid(s))
                usados_pred.add(_nid(p)); break

    for suc in sorted([s for s in ativos_novos if _nid(s) not in usados_suc], key=lambda x: _entrada(x) or datetime.max):
        e = _entrada(suc)
        if not e: continue
        melhor, melhor_dt = None, None
        for pred in excluidos_refin:
            if _nid(pred) in usados_pred: continue
            de = pred['data_exclusao']
            if not de: continue
            delta = abs((e-de).days)
            if delta <= 60:
                bonus = 0 if pred['banco_codigo']==suc['banco_codigo'] else 5
                if melhor is None or delta+bonus < melhor_dt:
                    melhor, melhor_dt = pred, delta+bonus
        if melhor:
            add_edge(_nid(melhor), _nid(suc), 'fallback_data', 'baixa')
            usados_pred.add(_nid(melhor)); usados_suc.add(_nid(suc))

    for c in excluidos_refin:
        if _nid(c) not in usados_pred:
            add_aviso('orfao_sem_sucessor',
                      f'Contrato {c["numero"]} ({BANCOS_OFICIAIS.get(c["banco_codigo"], c["banco_nome"])}) excluído em {c["data_exclusao"].strftime("%d/%m/%Y")} por {c["motivo_exclusao"]} sem sucessor identificado. Pode ter migrado para crédito fora do consignado INSS.',
                      c['numero'])

    contr_sem_juros = sum(1 for c in contratos if c['juros_mensal'] == 0 and c['situacao'] in ('Ativo','Suspenso'))
    if contr_sem_juros:
        add_aviso('campo_faltante', f'{contr_sem_juros} contrato(s) ativo(s)/suspenso(s) sem taxa de juros informada no HISCON (campo não disponibilizado pelo INSS para contratos anteriores a 2019).')

    # Componentes conexos
    visited = set(); cadeias = []
    def dfs(n, comp):
        if n in visited: return
        visited.add(n); comp.add(n)
        for x in edges.get(n, []): dfs(x, comp)
        for x in rev_edges.get(n, []): dfs(x, comp)
    for n in nodes:
        if n in visited: continue
        c = set(); dfs(n, c); cadeias.append(sorted(c))

    def cadeia_inicio(comp):
        datas = [_entrada(nodes[n]) for n in comp]; datas=[d for d in datas if d]
        return min(datas) if datas else datetime(2099,1,1)
    cadeias.sort(key=cadeia_inicio)

    # ===== RED FLAGS =====
    def analisar_cadeia_flags(comp):
        conts = [nodes[n] for n in comp]
        flags = []
        if len(conts) >= 3:
            vals = sorted([c['valor_emprestado'] for c in conts if c['valor_emprestado'] > 0])
            if vals and max(vals) > 3 * min(vals):
                flags.append({'tipo':'Crescimento anormal','severidade':'alta',
                             'desc': f'Valor emprestado cresceu de R$ {min(vals):,.2f} para R$ {max(vals):,.2f} ({max(vals)/min(vals):.1f}×) ao longo dos refinanciamentos sucessivos — indício clássico de anatocismo.'.replace(',','X').replace('.',',').replace('X','.')})
        if len(conts) >= 5:
            flags.append({'tipo':'Cadeia longa','severidade':'alta',
                         'desc': f'{len(conts)} contratos encadeados — padrão de captura por correspondente com refinanciamentos predatórios.'})
        banco_pag = (beneficiario.get('banco_pagador') or '').lower()
        for c in conts:
            if c['tipo_origem'] == 'original' and c['banco_codigo']:
                nome_b = (c['banco_nome'] or '').lower()
                if not any(w in banco_pag for w in nome_b.split()[:3] if len(w) > 3):
                    flags.append({'tipo':'Banco sem vínculo','severidade':'alta',
                                 'desc': f'Contrato {c["numero"]} celebrado no {c["banco_nome"]}, distinto do banco pagador do benefício ({beneficiario.get("banco_pagador","?")}).'})
                    break
        for c in conts:
            if c['data_exclusao'] and _entrada(c):
                dur = (c['data_exclusao'] - _entrada(c)).days
                if 0 < dur < 60:
                    flags.append({'tipo':'Operação-ponte','severidade':'alta',
                                 'desc': f'Contrato {c["numero"]} teve duração de apenas {dur} dias — possível lançamento-fantasma.'})
                    break
        for n in comp:
            pais = [p for p in rev_edges.get(n, []) if p in comp]
            filhos = [f for f in edges.get(n, []) if f in comp]
            if len(pais) >= 2:
                flags.append({'tipo':'Consolidação','severidade':'média',
                             'desc': f'Contrato {nodes[n]["numero"]} consolidou {len(pais)} contratos anteriores.'})
                break
            if len(filhos) >= 2:
                flags.append({'tipo':'Fracionamento','severidade':'média',
                             'desc': f'Contrato {nodes[n]["numero"]} foi fracionado em {len(filhos)} novos.'})
                break
        return flags

    red_flags_por_cadeia = {}
    for i, comp in enumerate(cadeias):
        red_flags_por_cadeia[i] = analisar_cadeia_flags(comp)

    # ===== CONVERTER DATAS PARA ISO =====
    def iso(d): return d.isoformat() if isinstance(d, datetime) else d
    for c in contratos:
        for k in ('data_inclusao','data_primeiro_desconto','data_exclusao'):
            c[k] = iso(c[k])

    # Estatísticas
    ativos_total = sum(1 for c in contratos if 'Ativ' in c['situacao'])
    estat = {
        'total_contratos': len(contratos),
        'total_cadeias': len(cadeias),
        'cadeias_multi': sum(1 for c in cadeias if len(c) > 1),
        'cadeias_isoladas': sum(1 for c in cadeias if len(c) == 1),
        'contratos_ativos': ativos_total,
        'contratos_encerrados': len(contratos) - ativos_total,
        'total_liberado': sum(c['valor_liberado'] for c in contratos),
        'total_pago': sum(c['valor_pago'] for c in contratos),
        'saldo_projetado': sum(c['valor_parcela']*c['qtd_parcelas'] for c in contratos if 'Ativ' in c['situacao']),
        'ligacoes_total': len(ligacoes),
        'ligacoes_alta': sum(1 for l in ligacoes if l['confianca']=='alta'),
        'ligacoes_media': sum(1 for l in ligacoes if l['confianca']=='média'),
        'ligacoes_baixa': sum(1 for l in ligacoes if l['confianca']=='baixa'),
        'red_flags_total': sum(len(f) for f in red_flags_por_cadeia.values()),
        'avisos_total': len(avisos),
        'problemas_total': len(problemas),
    }

    return {
        'beneficiario': beneficiario,
        'contratos': contratos,
        'cadeias': cadeias,
        'ligacoes': ligacoes,
        'edges': {k: v for k, v in edges.items()},
        'rev_edges': {k: v for k, v in rev_edges.items()},
        'avisos': avisos,
        'problemas': problemas,
        'red_flags': red_flags_por_cadeia,
        'estatisticas': estat,
    }
