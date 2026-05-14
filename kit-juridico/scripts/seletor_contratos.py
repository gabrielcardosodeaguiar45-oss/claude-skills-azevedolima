"""
Seletor de contratos a impugnar por pasta_acao.

Para cada pasta_acao gerada pela kit-juridico, decide quais contratos do
HISCON do cliente serão objeto de ação. Resultado é gravado no
`_estado_cliente.json` em `pastas_acao[].contratos_impugnar_ids` e em uma
planilha de revisão `_contratos_a_impugnar.xlsx` na raiz do cliente.

Heurística (conservadora, sempre passível de revisão humana):

  1. Banco da pasta + benefício → recorta contratos candidatos.
  2. Pasta com "RMC-RCC" no nome → tipo deve ser RMC ou RCC. Senão → CONSIGNADO.
  3. Para cada cadeia que tem ALGUM contrato candidato → toda a cadeia entra
     (refinanciamentos antecessores também respondem solidariamente).
  4. Contratos independentes (não estão em cadeia):
     - Ativos → entram.
     - Excluídos/Encerrados → entram com flag `revisar_prescricao`.
     - Para RMC/RCC: todos os candidatos entram (margem encerrada pode ter
       cobranças residuais).
  5. De-duplica por número de contrato, preferindo Ativo.

Cada contrato selecionado leva um dict com `id_interno`, `motivo` e flags.
"""
from typing import Iterable


CHAVES_BANCO = [
    'BMG', 'BRADESCO', 'ITAU', 'C6', 'PAN', 'CAIXA',
    'SANTANDER', 'DAYCOVAL', 'MERCANTIL', 'FACTA',
    'AGIBANK', 'OLE', 'BGN', 'CETELEM', 'MASTER',
    'SAFRA', 'CREFISA', 'PARANA', 'DIGIO', 'BANRISUL',
    'INTER', 'NUBANK', 'INBURSA', 'SENFF', 'PARATI',
    'PINE', 'VOTORANTIM', 'PICPAY', 'QI', 'CAPITAL',
    'SICOOB', 'BB', 'BRB', 'BNP',
]


def _norm(s: str) -> str:
    """Normaliza string removendo whitespace para fuzzy matching."""
    import re
    return re.sub(r'\s+', '', (s or '').upper())


def _bancos_da_pasta(path_relativo: str) -> tuple[list[str], bool, str]:
    """Extrai (bancos_chave, is_rmc_rcc, beneficio) do path_relativo.
    Suporta litisconsórcio ('BANCO X + BANCO Y') e nomes com whitespace ruim.
    """
    partes = path_relativo.replace('/', '\\').split('\\')
    if not partes:
        return ([], False, '')
    if len(partes) == 1:
        beneficio = ''
        pasta_banco = partes[0]
    else:
        beneficio = partes[0].strip().upper()
        pasta_banco = partes[1]
    pasta_norm = _norm(pasta_banco)
    is_rmc_rcc = 'RMC-RCC' in pasta_norm or 'RMC/RCC' in pasta_norm
    bancos = [ch for ch in CHAVES_BANCO if ch in pasta_norm]
    return (bancos, is_rmc_rcc, beneficio)


def _contratos_candidatos(contratos: list, bancos: list, is_rmc_rcc: bool,
                          beneficio: str) -> list:
    """Filtra contratos pelo banco/benefício/tipo da pasta_acao."""
    out = []
    for c in contratos:
        bc = (c.get('banco_chave') or '').upper()
        if not bc or bc not in bancos:
            continue
        bp = (c.get('beneficio_pasta') or '').upper()
        if beneficio in ('APOSENTADORIA', 'PENSAO') and bp != beneficio:
            continue
        tipo = (c.get('tipo') or '').upper()
        if is_rmc_rcc:
            if tipo not in ('RMC', 'RCC'):
                continue
        else:
            if tipo != 'CONSIGNADO':
                continue
        out.append(c)
    return out


def _ids_em_cadeias_que_intersectam(candidatos_ids: set, cadeias: list) -> set:
    """Para cada cadeia que tem PELO MENOS UM contrato candidato, retorna
    todos os ids da cadeia (refinanciamentos antecessores entram juntos).
    """
    out = set()
    for cad in cadeias or []:
        ids_cad = set(cad.get('contratos_ids') or [])
        if ids_cad & candidatos_ids:
            out.update(ids_cad)
    return out


def _resolver_pasta_acao(pasta_cliente_abs: str, path_relativo: str) -> str | None:
    """Resolve path_relativo do JSON para pasta real no disco com fuzzy matching.
    Tolera whitespace ruim (ex: 'MERCA NTIL' vs 'MERCANTIL').
    """
    import os
    import re
    if not pasta_cliente_abs or not path_relativo:
        return None
    direto = os.path.join(pasta_cliente_abs, path_relativo)
    if os.path.isdir(direto):
        return direto

    def _norm(s: str) -> str:
        return re.sub(r'\s+', '', (s or '').upper())

    partes = path_relativo.replace('/', '\\').split('\\')
    base_dir = pasta_cliente_abs
    for parte in partes:
        if not os.path.isdir(base_dir):
            return None
        candidatos = os.listdir(base_dir)
        match_exato = next((n for n in candidatos if n == parte), None)
        if match_exato:
            base_dir = os.path.join(base_dir, match_exato)
            continue
        target = _norm(parte)
        match_fuzzy = next((n for n in candidatos if _norm(n) == target), None)
        if match_fuzzy:
            base_dir = os.path.join(base_dir, match_fuzzy)
            continue
        return None
    return base_dir if os.path.isdir(base_dir) else None


def _extrair_nums_procuracoes(pasta_acao_abs: str | None) -> set:
    """Lê os PDFs de procuração na pasta e extrai números de contrato do nome.
    Retorna set de strings (com sufixo -N preservado, se houver).
    """
    import os
    import re
    if not pasta_acao_abs or not os.path.isdir(pasta_acao_abs):
        return set()
    nums = set()
    for nome in os.listdir(pasta_acao_abs):
        if 'procura' not in nome.lower() or not nome.lower().endswith('.pdf'):
            continue
        for m in re.finditer(r'[Cc]ontrato\s+(?:n[º°]\s*)?(\d{6,}(?:-\d+)?)', nome):
            nums.add(m.group(1))
    return nums


def selecionar_contratos_impugnar(pasta_acao: dict, contratos: list,
                                   cadeias: list,
                                   pasta_acao_abs: str | None = None) -> dict:
    """Decide quais contratos vão para `contratos_impugnar_ids` da pasta_acao.

    Se pasta_acao_abs for fornecido E houver procurações com número de contrato
    no nome do arquivo, a sugestão respeita a procuração:
      - contratos que batem procuração → `impugnar=S`
      - contratos que NÃO batem (mas se encaixam na heurística) → `impugnar=N`,
        ficam visíveis na planilha para o advogado optar por incluir.

    Retorna dict com:
      - ids: lista de id_interno apenas dos `S`
      - linhas_planilha: TODOS os candidatos (S + N) para revisão
      - origem: "sugestao_automatica"
    """
    path_rel = pasta_acao.get('path_relativo', '')
    bancos, is_rmc_rcc, beneficio = _bancos_da_pasta(path_rel)
    if not bancos:
        return {"ids": [], "linhas_planilha": [], "origem": "sugestao_automatica"}

    candidatos = _contratos_candidatos(contratos, bancos, is_rmc_rcc, beneficio)

    # Fallback para JSONs com banco_chave=None (bug da kit-juridico em alguns
    # parses de HISCON). Se nada bateu pelo banco mas há procurações nesta
    # pasta, recupera contratos pelos números das procurações ignorando banco.
    nums_procuracao_preview = _extrair_nums_procuracoes(pasta_acao_abs)
    if not candidatos and nums_procuracao_preview:
        nums_raiz = {n.split('-')[0] for n in nums_procuracao_preview}
        for c in contratos:
            num = str(c.get('contrato') or '')
            if not num:
                continue
            if num in nums_procuracao_preview or num.split('-')[0] in nums_raiz:
                # Filtro de tipo + benefício ainda aplica
                tipo = (c.get('tipo') or '').upper()
                bp = (c.get('beneficio_pasta') or '').upper()
                if is_rmc_rcc and tipo not in ('RMC', 'RCC'):
                    continue
                if not is_rmc_rcc and tipo != 'CONSIGNADO':
                    continue
                if beneficio in ('APOSENTADORIA', 'PENSAO') and bp != beneficio:
                    continue
                candidatos.append(c)

    candidatos_ids = {c.get('id_interno') for c in candidatos if c.get('id_interno')}

    # Toda cadeia que tem candidato → toda a cadeia entra
    ids_via_cadeia = _ids_em_cadeias_que_intersectam(candidatos_ids, cadeias)

    # Resultado final: união de candidatos + cadeias intersectadas
    ids_finais = candidatos_ids | (ids_via_cadeia & {c.get('id_interno') for c in contratos})

    # Mapear id → contrato (incluindo os trazidos pela cadeia)
    contratos_por_id = {c.get('id_interno'): c for c in contratos if c.get('id_interno')}
    cadeia_por_id = {}
    for cad in cadeias or []:
        for cid in (cad.get('contratos_ids') or []):
            cadeia_por_id[cid] = cad.get('id') or cad.get('subtipo')

    # De-duplicar por número de contrato, preferindo Ativo
    selecionados_por_num = {}
    for cid in ids_finais:
        c = contratos_por_id.get(cid)
        if not c:
            continue
        num = c.get('contrato')
        if not num:
            continue
        atual = selecionados_por_num.get(num)
        if atual is None:
            selecionados_por_num[num] = c
        elif c.get('situacao') == 'Ativo' and atual.get('situacao') != 'Ativo':
            selecionados_por_num[num] = c

    # Procurações da pasta_acao são fonte autoritativa.
    # Sem procuração não há mandato — não pode entrar na ação.
    nums_procuracao = _extrair_nums_procuracoes(pasta_acao_abs)

    def _bate_procuracao(num_contrato: str) -> bool:
        """Match exato OU pela raiz numérica (tolera sufixo -N)."""
        if num_contrato in nums_procuracao:
            return True
        raiz = num_contrato.split('-')[0]
        return any(n.split('-')[0] == raiz for n in nums_procuracao)

    # Se a pasta tem procurações, restringe a elas.
    # Se NÃO tem procurações, retorna vazio com flag — sem mandato, sem ação.
    if not nums_procuracao:
        return {
            'ids': [],
            'linhas_planilha': [],
            'origem': 'sem_procuracoes',
            'aviso': f'Pasta {path_rel} não tem procurações com número de contrato no nome. '
                     'Sem mandato específico, advogado não pode incluir contratos. '
                     'Gerar procurações e re-rodar.',
        }

    # Filtra: só contratos que batem com procurações entram
    linhas = []
    ids_ordenados = []
    for c in selecionados_por_num.values():
        cid = c.get('id_interno')
        num = str(c.get('contrato') or '')
        if not _bate_procuracao(num):
            continue
        flags = []
        if c.get('situacao') in ('Excluído', 'Encerrado') and cid not in ids_via_cadeia:
            flags.append('revisar_prescricao')
        cad_id = cadeia_por_id.get(cid)
        if cad_id:
            motivo = f'cadeia_{cad_id}'
        elif c.get('situacao') == 'Ativo':
            motivo = 'ativo_independente'
        else:
            motivo = 'encerrado_independente'

        ids_ordenados.append(cid)
        linhas.append({
            'pasta_acao': path_rel,
            'id': cid,
            'contrato': num,
            'banco': c.get('banco_chave'),
            'tipo': c.get('tipo'),
            'situacao': c.get('situacao'),
            'motivo': motivo,
            'flags': ','.join(flags),
            'impugnar': 'S',
        })

    return {
        'ids': ids_ordenados,
        'linhas_planilha': linhas,
        'origem': 'sugestao_automatica',
    }


def selecionar_para_todas_pastas(pastas_acao: list, contratos: list,
                                   cadeias: list,
                                   pasta_cliente_abs: str | None = None) -> tuple[list, list]:
    """Aplica o seletor para todas as pastas_acao do cliente.

    Se `pasta_cliente_abs` for fornecido, o seletor cruza com as procurações
    de cada pasta_acao para definir o default S/N na planilha.

    Mutates pastas_acao adicionando `contratos_impugnar_ids` e
    `contratos_impugnar_origem`. Retorna (pastas_acao_atualizadas, linhas_planilha_total).
    """
    import os
    linhas_total = []
    for pa in pastas_acao:
        path_rel = pa.get('path_relativo', '')
        pasta_abs = None
        if pasta_cliente_abs and path_rel:
            # Fuzzy resolve para tolerar whitespace ruim no path_relativo do JSON
            pasta_abs = _resolver_pasta_acao(pasta_cliente_abs, path_rel)
        rel = selecionar_contratos_impugnar(pa, contratos, cadeias, pasta_acao_abs=pasta_abs)
        pa['contratos_impugnar_ids'] = rel['ids']
        pa['contratos_impugnar_origem'] = rel['origem']
        if rel.get('aviso'):
            pa['aviso'] = rel['aviso']
        linhas_total.extend(rel['linhas_planilha'])
    return pastas_acao, linhas_total
