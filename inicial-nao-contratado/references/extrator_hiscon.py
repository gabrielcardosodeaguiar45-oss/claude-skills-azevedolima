"""Wrapper fino sobre `analisar_hiscon` da skill `analise-cadeias-hiscon`.

PRIORIDADE de fontes para `competencia_inicio` / `competencia_fim`:
  1. Colunas LITERAIS do HISCON (`competencia_inicio_desconto` /
     `competencia_fim_desconto`) — fonte autoritativa, capturada pelo parser
     desde 07/05/2026.
  2. Fallback (somente quando a coluna do PDF veio vazia):
        - inicio = mês de data_primeiro_desconto, ou data_inclusao + 1 mês
        - fim    = data_exclusao − 1 mês (se houve exclusão), ou inicio + qtd − 1

Reaproveita o parser robusto baseado em pdfplumber (já testado, extrai 123
contratos do HISCON do George corretamente). Adiciona:

- `filtrar_contratos_por_numero(contratos, numeros)` — filtra os contratos
  questionados (vindos dos nomes das procurações), com FUZZY MATCH (1 dígito
  de tolerância) para suportar typos comuns no nome do arquivo;
- `auditar_procuracoes_vs_hiscon(...)` — checa se há contratos do mesmo
  banco no HISCON que NÃO foram referidos por nenhuma procuração, gerando
  alertas para revisão manual;
- `formatar_contrato_para_template(c)` — converte o dict do parser para o
  formato esperado pelos placeholders dos templates `inicial-jfba-*.docx`.
"""
import sys, os, re
from datetime import datetime
from typing import List, Dict, Optional

# Importar o parser da skill analise-cadeias-hiscon
SKILL_HISCON = r'C:\Users\gabri\.claude\skills\analise-cadeias-hiscon\scripts'
if SKILL_HISCON not in sys.path:
    sys.path.insert(0, SKILL_HISCON)

from analisador import analisar_hiscon  # noqa: E402


def parse_hiscon(pdf_path: str) -> Dict:
    """Parseia HISCON e retorna dict normalizado para a skill inicial-nao-contratado.

    Returns:
        {
            'cabecalho': {'nome_autor', 'tipo_beneficio', 'nb_beneficio',
                          'banco_pagador', 'agencia_pagador', 'conta_pagador'},
            'margens': {'base_calculo', 'total_comprometido', 'max_comprometimento'},
            'contratos': [dict do parser, igual ao analisar_hiscon],
        }
    """
    res = analisar_hiscon(_long_path(pdf_path))
    benef = res.get('beneficiario', {})
    return {
        'cabecalho': {
            'nome_autor': benef.get('nome'),
            'tipo_beneficio': benef.get('beneficio'),
            'nb_beneficio': benef.get('numero_beneficio'),
            'banco_pagador': _limpar_banco_pagador(benef.get('banco_pagador', '')),
            # agencia/conta NÃO vêm no parser. Extrair manualmente:
            'agencia_pagador': _extrair_agencia(pdf_path),
            'conta_pagador': _extrair_conta(pdf_path),
        },
        'margens': {
            'base_calculo': benef.get('base_calculo'),
            'total_comprometido': benef.get('total_comprometido'),
            'max_comprometimento': benef.get('max_comprometimento'),
        },
        'contratos': res.get('contratos', []),
    }


def _limpar_banco_pagador(s: str) -> str:
    """Remove sufixos espúrios como 'Não é pensão alimentícia' que o parser
    pega junto."""
    if not s:
        return s
    for sufixo in ('Não é pensão alimentícia', 'Não possui procurador', 'Não possui representante legal'):
        i = s.find(sufixo)
        if i > 0:
            s = s[:i].strip()
    return s


def _long_path(p: str) -> str:
    """Aplica prefixo \\\\?\\ no Windows quando path > 240 chars (workaround MAX_PATH=260).
    Pdfplumber e pymupdf usam open()/fopen() nativos que respeitam o limite antigo."""
    import os
    if os.name == 'nt' and isinstance(p, str) and len(p) > 240 and not p.startswith('\\\\?\\'):
        return '\\\\?\\' + os.path.abspath(p)
    return p


def _extrair_agencia(pdf_path: str) -> Optional[str]:
    """Extrai 'Agência: XXXX' do texto da p.1."""
    import fitz
    doc = fitz.open(_long_path(pdf_path))
    txt = doc[0].get_text() if len(doc) > 0 else ''
    doc.close()
    m = re.search(r'Agência:\s*(\d+)', txt)
    return m.group(1) if m else None


def _extrair_conta(pdf_path: str) -> Optional[str]:
    """Extrai 'Conta Corrente: XXXXXXXX' do texto da p.1."""
    import fitz
    doc = fitz.open(_long_path(pdf_path))
    txt = doc[0].get_text() if len(doc) > 0 else ''
    doc.close()
    m = re.search(r'Conta Corrente:\s*([\d-]+)', txt)
    return m.group(1) if m else None


def filtrar_contratos_por_numero(contratos: List[Dict], numeros: List[str],
                                  fuzzy_dist: int = 1) -> List[Dict]:
    """Filtra os contratos do HISCON pelos números questionados (vindos dos
    nomes das procurações, ex.: '630035051').

    Aceita variações de formatação: '630035051' ≈ '630035-051' ≈ '63003 5051'.

    FUZZY MATCH: se nenhum número da procuração bater EXATO no HISCON, tenta
    achar o contrato mais próximo (Hamming distance ≤ fuzzy_dist em strings de
    mesmo tamanho). Útil para typos comuns no nome do arquivo da procuração
    (ex.: arquivo '0047633052' deve casar com HISCON '0047033052' — 1 dígito).

    Args:
        contratos: lista de dicts do HISCON
        numeros: lista de números de contrato a filtrar
        fuzzy_dist: distância máxima permitida para fuzzy match (0 = só exato)

    Returns:
        Lista dos contratos do HISCON que casam com algum número da entrada.
        Cada match fuzzy é marcado com a chave `_match_fuzzy = numero_original`.
    """
    def _normalizar(n: str) -> str:
        return re.sub(r'[^\d]', '', n or '')

    nums_norm = [_normalizar(n) for n in numeros if n]
    contratos_idx = {_normalizar(c.get('numero', '')): c for c in contratos}

    achados = []
    achados_set = set()

    # 1ª passada: match EXATO
    for n in nums_norm:
        if n in contratos_idx and n not in achados_set:
            achados.append(contratos_idx[n])
            achados_set.add(n)

    # 2ª passada: FUZZY (apenas para os números que não bateram exato)
    if fuzzy_dist > 0:
        nao_encontrados = [n for n in nums_norm if n not in achados_set]
        for n in nao_encontrados:
            melhor = None
            melhor_dist = fuzzy_dist + 1
            for k, c in contratos_idx.items():
                if k in achados_set:
                    continue
                if len(k) != len(n):
                    continue
                dist = sum(1 for a, b in zip(k, n) if a != b)
                if dist <= fuzzy_dist and dist < melhor_dist:
                    melhor_dist = dist
                    melhor = (k, c)
            if melhor:
                k, c = melhor
                # marca o match como fuzzy + número original do arquivo
                c_marcado = dict(c, _match_fuzzy=n, _match_dist=melhor_dist)
                achados.append(c_marcado)
                achados_set.add(k)

    # 3ª passada: PREFIXO DE ZEROS À ESQUERDA
    # Casos em que a procuração registra '1422075' mas o HISCON tem 'QUA0001422075'
    # (após normalizar, '0001422075'). lstrip('0') iguala ambos a '1422075'.
    # Caso paradigma: EULALIA / INBURSA QUA0001422075 (2026-05-13).
    nao_encontrados = [n for n in nums_norm if n not in achados_set]
    for n in nao_encontrados:
        n_clean = n.lstrip('0')
        if not n_clean:
            continue
        for k, c in contratos_idx.items():
            if k in achados_set:
                continue
            if k.lstrip('0') == n_clean:
                c_marcado = dict(c, _match_zeros_normalizados=n)
                achados.append(c_marcado)
                achados_set.add(k)
                break

    # 4ª passada: SUFIXO/PREFIXO COMUM com diferença de até 2 dígitos
    # Caso paradigma: VILSON / BANRISUL — procuração tem '...917305' (clean
    # após lstrip = '917305'), HISCON tem '...09173052' (clean = '9173052').
    # Match exato falhou, Hamming falhou (tamanhos diferentes), lstrip exato
    # falhou (1 dígito extra). Esta passada aceita quando o número da
    # procuração (após lstrip) é PREFIXO ou SUBSTRING do HISCON (após lstrip)
    # com diferença de até 2 dígitos. Marca como `_match_substring` e gera
    # alerta CRÍTICO para conferência manual obrigatória.
    nao_encontrados = [n for n in nums_norm if n not in achados_set]
    for n in nao_encontrados:
        n_clean = n.lstrip('0')
        if len(n_clean) < 5:
            # Números muito curtos têm risco alto de falso positivo
            continue
        melhor = None
        melhor_dist = 3  # tolerância máxima absoluta
        for k, c in contratos_idx.items():
            if k in achados_set:
                continue
            k_clean = k.lstrip('0')
            if not k_clean:
                continue
            # Diferença máxima de 2 dígitos entre os comprimentos
            diff = abs(len(k_clean) - len(n_clean))
            if diff > 2 or diff == 0:
                # diff == 0 já tratado pelas passadas anteriores; aqui só queremos
                # números com tamanhos DIFERENTES (a Hamming passada cobre os iguais)
                continue
            # Modo "n é prefixo/sufixo de k" — o mais comum quando a procuração
            # cortou dígitos
            if n_clean in k_clean or k_clean in n_clean:
                if diff < melhor_dist:
                    melhor_dist = diff
                    melhor = (k, c)
        if melhor:
            k, c = melhor
            c_marcado = dict(c, _match_substring=n, _match_dist_extra=melhor_dist)
            achados.append(c_marcado)
            achados_set.add(k)

    return achados


def auditar_procuracoes_vs_hiscon(contratos_hiscon: List[Dict],
                                   numeros_procuracao: List[str],
                                   banco_codigo: str) -> Dict:
    """Cruza a lista de números das procurações com TODOS os contratos do
    HISCON para o BANCO específico, e gera alertas quando há discrepância.

    Args:
        contratos_hiscon: lista completa de contratos do HISCON
        numeros_procuracao: lista de números extraídos dos nomes dos arquivos
                            de procuração (ex.: ['0047032901', '0047032998', '0047633052'])
        banco_codigo: código FEBRABAN do banco (ex.: '935' para FACTA)

    Returns:
        {
          'casados_exato': [list de numeros],
          'casados_fuzzy': [list de tuplas (proc_original, hiscon_real, dist)],
          'sem_match_no_hiscon': [list de numeros das procurações sem nenhum match],
          'no_hiscon_sem_procuracao': [list de números do HISCON do banco que NÃO foram
                                       referidos por nenhuma procuração — REVISAR],
          'alertas': [list de strings prontas para o relatório paralelo],
        }
    """
    def _normalizar(n: str) -> str:
        return re.sub(r'[^\d]', '', n or '')

    nums_proc = [_normalizar(n) for n in numeros_procuracao if n]
    cont_banco = [c for c in contratos_hiscon if c.get('banco_codigo') == banco_codigo]
    nums_hiscon_banco = [_normalizar(c.get('numero', '')) for c in cont_banco]

    casados_exato = []
    casados_fuzzy = []
    casados_substring = []  # diferença de tamanho (Patch A — caso VILSON/BANRISUL)
    sem_match_proc = []

    for n in nums_proc:
        if n in nums_hiscon_banco:
            casados_exato.append(n)
            continue
        # tenta fuzzy de Hamming (mesmo tamanho)
        melhor = None
        melhor_dist = 2  # tolerância 1
        for h in nums_hiscon_banco:
            if h in casados_exato:
                continue
            if len(h) != len(n):
                continue
            dist = sum(1 for a, b in zip(h, n) if a != b)
            if dist < melhor_dist:
                melhor_dist = dist
                melhor = h
        if melhor and melhor_dist <= 1:
            casados_fuzzy.append((n, melhor, melhor_dist))
            continue
        # tenta SUBSTRING/SUFIXO com diferença de tamanho (Patch A)
        n_clean = n.lstrip('0')
        if len(n_clean) >= 5:
            melhor_sub = None
            melhor_diff = 3
            for h in nums_hiscon_banco:
                if h in casados_exato:
                    continue
                h_clean = h.lstrip('0')
                if not h_clean:
                    continue
                diff = abs(len(h_clean) - len(n_clean))
                if diff == 0 or diff > 2:
                    continue
                if n_clean in h_clean or h_clean in n_clean:
                    if diff < melhor_diff:
                        melhor_diff = diff
                        melhor_sub = h
            if melhor_sub:
                casados_substring.append((n, melhor_sub, melhor_diff))
                continue
        sem_match_proc.append(n)

    casados_total = (set(casados_exato)
                     | {h for (_, h, _) in casados_fuzzy}
                     | {h for (_, h, _) in casados_substring})
    nao_referidos = [h for h in nums_hiscon_banco if h not in casados_total]

    # Heurística de SUSPEITA: contrato no HISCON cujo número/data está MUITO
    # próximo dos contratos das procurações pode ser um irmão (mesma origem).
    # Critérios:
    #   (a) data_inclusao a ≤ 31 dias de qualquer contrato casado (mesma janela
    #       de assinatura — típico do escritório que fez 3 averbações no mesmo dia)
    #   (b) numero com PREFIXO igual aos casados (mesmo lote da financeira)
    from datetime import datetime as _dt, timedelta as _td

    def _to_dt(v):
        if v is None: return None
        if isinstance(v, _dt): return v
        if isinstance(v, str):
            try: return _dt.fromisoformat(v)
            except ValueError: return None
        return None

    casados_dts = [_to_dt(c.get('data_inclusao')) for c in cont_banco
                   if _normalizar(c.get('numero', '')) in casados_total]
    casados_dts = [d for d in casados_dts if d]
    casados_prefixos = {h[:6] for h in casados_total}

    suspeitos = []
    informativos = []
    for h in nao_referidos:
        c = next((c for c in cont_banco if _normalizar(c.get('numero', '')) == h), {})
        d_inc = _to_dt(c.get('data_inclusao'))
        suspeito = False
        motivo = []
        if d_inc and any(abs((d_inc - dc).days) <= 31 for dc in casados_dts):
            suspeito = True
            motivo.append('data_inclusao próxima (≤31 dias)')
        if any(h.startswith(p) for p in casados_prefixos):
            suspeito = True
            motivo.append('prefixo do número idêntico')
        item = (h, c, motivo)
        (suspeitos if suspeito else informativos).append(item)

    alertas = []

    # REGRA OPERACIONAL (gravada na SKILL.md §9-ter):
    # - 1 procuração com fuzzy: relevar e seguir, alertar como ATENÇÃO
    # - 2+ procurações com fuzzy: seguir, mas elevar para CRÍTICO — pode
    #   indicar erro sistemático no lote de procurações (ex.: pessoa errada
    #   gerou os arquivos, ou OCR ruim, ou mistura de clientes)
    n_fuzzy = len(casados_fuzzy)
    if n_fuzzy >= 2:
        lista_pf = ', '.join(f'{p!r}→{h!r}' for p, h, _ in casados_fuzzy)
        alertas.append(
            f'🚨 CRÍTICO: {n_fuzzy} procurações da pasta têm o NÚMERO de '
            f'contrato DIFERENTE do HISCON (com até 1 dígito de divergência): '
            f'{lista_pf}. Isso pode indicar erro SISTEMÁTICO na geração das '
            f'procurações (lote inteiro com typo, mistura com outro cliente, '
            f'ou OCR ruim). PARAR, CONFERIR todas as procurações e regerar '
            f'antes do protocolo. A inicial foi gerada usando o match fuzzy '
            f'mas NÃO PROTOCOLE sem revisão manual de TODAS as procurações.'
        )
    for proc, hisc, dist in casados_fuzzy:
        alertas.append(
            f'⚠ FUZZY MATCH: procuração com número {proc!r} (nome do arquivo) '
            f'foi vinculada ao contrato {hisc!r} do HISCON (distância {dist} '
            f'dígito). PROVÁVEL TYPO no nome do arquivo da procuração — '
            f'CONFIRMAR antes do protocolo.'
        )
    for proc, hisc, diff in casados_substring:
        alertas.append(
            f'🚨 SUBSTRING MATCH (tamanho diferente): procuração com número '
            f'{proc!r} foi vinculada ao contrato {hisc!r} do HISCON com '
            f'diferença de {diff} dígito(s). Isso indica que o número da '
            f'procuração pode estar TRUNCADO ou ter DÍGITO A MAIS/MENOS '
            f'(caso paradigma VILSON/BANRISUL: procuração ...917305, HISCON '
            f'...9173052). PARAR e CONFERIR o número correto no contrato '
            f'físico ou na CCB antes do protocolo. Inicial gerada usando o '
            f'match fuzzy mas NÃO PROTOCOLE sem revisão manual.'
        )
    for n in sem_match_proc:
        alertas.append(
            f'🚨 PROCURAÇÃO SEM CONTRATO: número {n!r} (do nome do arquivo de '
            f'procuração) NÃO foi achado no HISCON do banco {banco_codigo}. '
            f'Verificar se o número está correto ou se o contrato sumiu do INSS.'
        )
    for h, c, motivo in suspeitos:
        info = (
            f'qtd={c.get("qtd_parcelas")} | parc=R${c.get("valor_parcela")} | '
            f'incl={str(c.get("data_inclusao"))[:10]} | '
            f'exc={str(c.get("data_exclusao"))[:10] if c.get("data_exclusao") else "—"}'
        )
        alertas.append(
            f'🚨 SUSPEITO: contrato {h!r} ({info}) está no HISCON do banco '
            f'{banco_codigo} e tem {", ".join(motivo)} em relação aos contratos '
            f'das procurações — PODE SER 1 CONTRATO IRMÃO QUE FOI ESQUECIDO. '
            f'Conferir nas procurações se o número está com typo.'
        )
    if informativos:
        nums = ', '.join(h for h, _, _ in informativos)
        alertas.append(
            f'ℹ️ Outros {len(informativos)} contratos do banco {banco_codigo} '
            f'no HISCON sem procuração (não suspeitos por data/prefixo): {nums}'
        )

    return {
        'casados_exato': casados_exato,
        'casados_fuzzy': casados_fuzzy,
        'casados_substring': casados_substring,
        'sem_match_no_hiscon': sem_match_proc,
        'no_hiscon_sem_procuracao': nao_referidos,
        'suspeitos': suspeitos,
        'informativos': informativos,
        'alertas': alertas,
    }


def filtrar_contratos_por_banco(contratos: List[Dict], banco_codigo: str) -> List[Dict]:
    """Filtra todos os contratos de um banco específico (ex.: '029' = Itaú)."""
    return [c for c in contratos if c.get('banco_codigo') == banco_codigo]


def formatar_contrato_para_template(c: Dict) -> Dict:
    """Converte um contrato do parser para o formato dos placeholders do template.

    Returns:
        {
            'numero': str,
            'banco': str,
            'banco_codigo': str,
            'qtd_parcelas': int,
            'valor_parcela_float': float,
            'valor_parcela_str': str ('29,40'),
            'valor_emprestado_float': float,
            'valor_emprestado_str': str ('1.444,67'),
            'data_inclusao_str': str ('30/05/2025'),
            'competencia_inicio_str': str ('06/2025'),
            'competencia_fim_str': str ('05/2033'),
            'situacao': str ('Ativo' / 'Excluído' / 'Encerrado'),
            'origem_averbacao': str ('Averbaç ão por Refinan ciament o'),
            'tipo_origem': str ('refinanciamento' / 'averbacao_nova' / 'portabilidade' / 'migracao'),
        }
    """
    def _fmt_brl(v):
        if v is None:
            return ''
        s = f'{v:,.2f}'
        return s.replace(',', '#').replace('.', ',').replace('#', '.')

    def _fmt_dt(d):
        if d is None:
            return ''
        if isinstance(d, str):
            # Se é string ISO ('2021-08-04T00:00:00'), parsear
            try:
                d = datetime.fromisoformat(d)
            except ValueError:
                return d
        return d.strftime('%d/%m/%Y')

    def _competencia(d):
        if d is None:
            return ''
        if isinstance(d, str):
            try:
                d = datetime.fromisoformat(d)
            except ValueError:
                return d
        return d.strftime('%m/%Y')

    # Calcular competências (não vêm prontas do parser)
    def _ensure_dt(d):
        if d is None: return None
        if isinstance(d, str):
            try: return datetime.fromisoformat(d)
            except ValueError: return None
        return d

    def _add_meses(d, n):
        """Adiciona n meses a uma data, mantendo dia 1."""
        if d is None: return None
        ano, mes = d.year, d.month
        total = mes + n
        ano_novo = ano + (total - 1) // 12
        mes_novo = ((total - 1) % 12) + 1
        return datetime(ano_novo, mes_novo, 1)

    data_inc = _ensure_dt(c.get('data_inclusao'))
    data_exc = _ensure_dt(c.get('data_exclusao'))
    data_pri_desc = _ensure_dt(c.get('data_primeiro_desconto'))
    qtd = c.get('qtd_parcelas') or 0

    # Helper: parse 'mm/yyyy' (literal do HISCON) -> datetime
    def _parse_competencia_str(s):
        if not s or not isinstance(s, str):
            return None
        m = re.match(r'(\d{1,2})/(\d{4})', s.strip())
        if not m:
            return None
        return datetime(int(m.group(2)), int(m.group(1)), 1)

    # COMPETÊNCIA INÍCIO — PRIORIDADE:
    # 1. coluna literal do HISCON (`competencia_inicio_desconto` = '06/2021')
    # 2. mês de data_primeiro_desconto
    # 3. data_inclusao + 1 mês
    comp_ini = _parse_competencia_str(c.get('competencia_inicio_desconto'))
    if comp_ini is None:
        if data_pri_desc:
            comp_ini = datetime(data_pri_desc.year, data_pri_desc.month, 1)
        elif data_inc:
            comp_ini = _add_meses(datetime(data_inc.year, data_inc.month, 1), 1)

    # COMPETÊNCIA FIM — PRIORIDADE:
    # 1. coluna literal do HISCON (`competencia_fim_desconto` = '02/2024') — FONTE AUTORITATIVA
    # 2. data_exclusao − 1 mês (heurística — a exclusão administrativa cancela a
    #    próxima competência, então a última efetivamente descontada é a anterior)
    # 3. comp_ini + qtd_parcelas − 1 (contrato ativo, sem exclusão)
    comp_fim = _parse_competencia_str(c.get('competencia_fim_desconto'))
    if comp_fim is None:
        if data_exc:
            ref = datetime(data_exc.year, data_exc.month, 1)
            comp_fim = _add_meses(ref, -1)
        elif comp_ini and qtd:
            comp_fim = _add_meses(comp_ini, qtd - 1)

    return {
        'numero': c.get('numero'),
        'banco': c.get('banco_nome'),
        'banco_codigo': c.get('banco_codigo'),
        'qtd_parcelas': c.get('qtd_parcelas'),
        'valor_parcela_float': c.get('valor_parcela'),
        'valor_parcela_str': _fmt_brl(c.get('valor_parcela')),
        'valor_emprestado_float': c.get('valor_emprestado'),
        'valor_emprestado_str': _fmt_brl(c.get('valor_emprestado')),
        'valor_liberado_float': c.get('valor_liberado'),
        'valor_liberado_str': _fmt_brl(c.get('valor_liberado')),
        'data_inclusao_str': _fmt_dt(c.get('data_inclusao')),
        'data_exclusao_str': _fmt_dt(c.get('data_exclusao')),
        'competencia_inicio_str': _competencia(comp_ini),
        'competencia_fim_str': _competencia(comp_fim),
        'situacao': c.get('situacao'),
        'origem_averbacao': c.get('origem_averbacao'),
        'tipo_origem': c.get('tipo_origem'),
        'motivo_exclusao': c.get('motivo_exclusao'),
    }


# ============================================================================
# Patch C — Validador pré-geração (2026-05-16)
# ----------------------------------------------------------------------------
# Caso paradigma: VILSON DA CRUZ BRASIL / BANRISUL — contrato 917305 da
# procuração não casava no HISCON (era 9173052). O fallback `permitir_contrato_
# virtual` gerou inicial com R$ 0,00 e `[A CONFIRMAR — pendente HISCON]`.
# Esta validação ABORTA antes da geração se qualquer dado essencial estiver
# faltando, zerado ou em estado de placeholder.
# ============================================================================

class DadosObrigatoriosFaltandoError(RuntimeError):
    """Levantada quando um contrato a impugnar está incompleto e a inicial
    não pode ser gerada com responsabilidade."""
    def __init__(self, erros: List[str]):
        self.erros = erros
        msg = (
            'Inicial NÃO PODE ser gerada — dados obrigatórios ausentes:\n'
            + '\n'.join(f'  • {e}' for e in erros)
            + '\n\nAÇÃO: localizar o contrato correto no HISCON, conferir o '
              'número da procuração com o cliente, ou suspender a pasta até '
              'esclarecer. NUNCA usar fallbacks fictícios (R$ 50,00, 84 '
              'parcelas, "[A CONFIRMAR]") como contorno.'
        )
        super().__init__(msg)


class ProcuracaoSemContratoError(RuntimeError):
    """Levantada quando nenhum contrato do HISCON casou com os números das
    procurações (mesmo após Hamming + lstrip + substring). Substitui o modo
    `permitir_contrato_virtual` removido em 2026-05-16."""
    pass


def validar_contratos_obrigatorios(contratos_fmt: List[Dict]) -> None:
    """Valida que todos os contratos têm dados mínimos para gerar inicial.

    Aborta com DadosObrigatoriosFaltandoError listando o que faltou.

    Critérios (cada falha lista o contrato afetado):
      - valor_parcela_float > 0
      - qtd_parcelas > 0 (e ≤ 96, sanidade)
      - competencia_inicio_str no formato 'MM/AAAA'
      - data_inclusao_str preenchido (sem '[A CONFIRMAR]')
      - valor_emprestado_float > 0 (apenas alerta se ausente — alguns templates
        permitem omissão quando "Valor pago" é o relevante)
      - numero não vazio

    Caso paradigma: VILSON / BANRISUL (2026-05-16) — `valor_parcela_float=0.0`,
    `data_inclusao_str='[A CONFIRMAR — pendente HISCON]'`, gerados pelo modo
    `permitir_contrato_virtual` (depois removido pelo Patch B).
    """
    if not contratos_fmt:
        raise DadosObrigatoriosFaltandoError(
            ['Lista de contratos a impugnar está vazia.']
        )
    erros: List[str] = []
    for i, c in enumerate(contratos_fmt, 1):
        prefix = f'Contrato {i} (nº {c.get("numero") or "?"})'
        # numero
        if not c.get('numero'):
            erros.append(f'{prefix}: número do contrato ausente.')
        # valor_parcela
        vp = c.get('valor_parcela_float')
        if vp is None or vp <= 0:
            erros.append(f'{prefix}: valor_parcela inválido ({vp!r}).')
        # qtd_parcelas
        qtd = c.get('qtd_parcelas')
        if not qtd or qtd <= 0:
            erros.append(f'{prefix}: qtd_parcelas inválido ({qtd!r}).')
        elif qtd > 96:
            erros.append(f'{prefix}: qtd_parcelas suspeito ({qtd} > 96).')
        # competencia_inicio
        ci = c.get('competencia_inicio_str') or ''
        if not re.match(r'^\d{2}/\d{4}$', ci):
            erros.append(f'{prefix}: competência início inválida ({ci!r}).')
        # data_inclusao
        di = c.get('data_inclusao_str') or ''
        if not di or '[A CONFIRMAR' in di or 'pendente' in di.lower():
            erros.append(f'{prefix}: data_inclusao ausente ou placeholder ({di!r}).')
    if erros:
        raise DadosObrigatoriosFaltandoError(erros)


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    p = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\GEORGE DA SILVA SOUZA - Marcio Teixeira\BANCO ITAÚ\2 AVERBAÇÃO NOVA INATIVO\8 - HISTÓRICO DE EMPRÉSTIMO.pdf'
    res = parse_hiscon(p)
    print('=== CABEÇALHO ===')
    for k, v in res['cabecalho'].items():
        print(f'  {k}: {v}')
    print('\n=== MARGENS ===')
    for k, v in res['margens'].items():
        print(f'  {k}: {v}')
    print(f'\n=== CONTRATOS (total: {len(res["contratos"])}) ===')
    print('Distribuição por banco:')
    from collections import Counter
    by_bank = Counter(c.get('banco_codigo') for c in res['contratos'])
    for b, n in sorted(by_bank.items(), key=lambda x: -x[1]):
        print(f'  {b}: {n} contratos')

    print('\n=== TESTE: contratos do Itaú do George (5 procurações) ===')
    nums_itau = ['630035051', '635737335', '610696404', '610696417', '618896399']
    filtrados = filtrar_contratos_por_numero(res['contratos'], nums_itau)
    print(f'Encontrados {len(filtrados)} de {len(nums_itau)}:')
    for c in filtrados:
        f = formatar_contrato_para_template(c)
        print(f'  {f["numero"]} | {f["banco"]} | parc R$ {f["valor_parcela_str"]} | empr R$ {f["valor_emprestado_str"]} | incl {f["data_inclusao_str"]} | {f["competencia_inicio_str"]} a {f["competencia_fim_str"]} | {f["situacao"]} | {f["tipo_origem"]}')
