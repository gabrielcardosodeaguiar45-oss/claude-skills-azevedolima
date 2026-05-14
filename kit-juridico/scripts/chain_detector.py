"""
Detector de cadeias de contratos consignados.

Recebe a saída do hiscon_parser (lista de contratos com situação/datas/valor/origem)
e detecta cadeias de:
    - Refinanciamento direto (1→1)
    - Consolidação (N→1)
    - Fracionamento (1→N)
    - Portabilidade (entre bancos diferentes)
    - Substituição imediata RMC/RCC (caso especial cartão)

Constrói grafo onde nodes = contratos e edges = relações de cadeia. Encontra
componentes conectados — cada componente é uma "ação judicial" candidata.

Uso:
    python chain_detector.py <hiscon_json_pensao> [<hiscon_json_apos> ...]

Ou via Python:
    from chain_detector import detectar_cadeias
    cadeias = detectar_cadeias(contratos_lista)

Retorna lista de componentes:
[
    {
        "id": "C-01",
        "tipo": "CADEIA",
        "subtipo": "REFIN_DIRETO",  // REFIN_DIRETO | CONSOLIDACAO | FRACIONAMENTO | PORTABILIDADE_INTER_BANCO | SUBSTITUICAO_BANCO | ISOLADO
        "bancos": ["BANCO ITAU CONSIGNADO SA"],
        "beneficio": "PENSAO",
        "contratos": [
            {"contrato": "626702215", "papel": "ANCESTRAL", "ordem": 1, ...},
            {"contrato": "632948666", "papel": "ATUAL",     "ordem": 2, ...},
        ],
        "valor_parcela_referencia": "R$236,30",
        "data_referencia": "14/09/2021",
        "cor_grifo": (1.00, 0.95, 0.40),
    }
]
"""
import sys
import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


PALETA_CORES = [
    ((1.00, 0.95, 0.40), "Amarelo"),
    ((0.60, 1.00, 0.60), "Verde claro"),
    ((1.00, 0.75, 0.40), "Laranja claro"),
    ((1.00, 0.70, 0.85), "Rosa claro"),
    ((0.50, 0.85, 1.00), "Azul claro"),
    ((0.85, 0.70, 1.00), "Violeta claro"),
]
COR_NEUTRA = ((1.0, 1.0, 0.5), "Amarelo neutro")


def parse_data(s: str | None):
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def parse_valor(s: str | None) -> float | None:
    if not s:
        return None
    s = s.replace("R$", "").replace(" ", "").strip()
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def datas_proximas(d1, d2, tolerancia_dias: int = 1) -> bool:
    if d1 is None or d2 is None:
        return False
    return abs((d2 - d1).days) <= tolerancia_dias


def valores_compativeis(v1: float | None, v2: float | None, tolerancia: float = 0.50,
                        tol_pct: float = 0.005) -> bool:
    """Tolerância de R$0,50 ou tol_pct (default 0,5%)."""
    if v1 is None or v2 is None:
        return False
    if abs(v1 - v2) <= tolerancia:
        return True
    if v1 > 0 and abs(v1 - v2) / v1 <= tol_pct:
        return True
    return False


def detectar_cadeias(contratos: list[dict], beneficio_pasta: str = "") -> list[dict]:
    """
    Detecta cadeias e retorna lista de componentes conectados.

    contratos: lista de dicts saída do hiscon_parser, com chaves:
        contrato, banco, banco_codigo, situacao, origem, data_inclusao,
        data_exclusao, motivo_exclusao, valor_parcela, tipo (CONSIGNADO/RMC/RCC)
    """
    # Normalizar
    for c in contratos:
        c["_dt_inclusao"] = parse_data(c.get("data_inclusao"))
        c["_dt_exclusao"] = parse_data(c.get("data_exclusao"))
        c["_v_parcela"] = parse_valor(c.get("valor_parcela"))

    # Construir adjacência (grafo não-direcional)
    adj = defaultdict(set)
    arestas = []  # lista de (a, b, motivo) para auditoria

    excluidos_refin = [c for c in contratos
                       if c.get("motivo_exclusao") and "refinanciament" in c["motivo_exclusao"].lower()]
    excluidos_port = [c for c in contratos
                      if c.get("motivo_exclusao") and "portabilidade" in c["motivo_exclusao"].lower()]
    excluidos_banco_rmc = [c for c in contratos
                           if c.get("tipo") in ("RMC", "RCC") and c.get("motivo_exclusao") == "Exclusão Banco"]

    novos_refin = [c for c in contratos
                   if c.get("origem") and "refinanciament" in c["origem"].lower()]
    novos_port = [c for c in contratos
                  if c.get("origem") and "portabilidade" in c["origem"].lower()]
    novos_averb_rmc = [c for c in contratos
                       if c.get("tipo") in ("RMC", "RCC")
                       and c.get("origem") and "nova" in c["origem"].lower()
                       and c.get("situacao") == "Ativo"]

    # 1) Refinanciamento intra-banco
    # Estratégia em 2 passes:
    # - PASSE 1: refin direto/recursivo (1→1) — match estrito por banco + data + valor de parcela
    # - PASSE 2: consolidação/fracionamento — match por banco + data quando valor não bate 1→1
    refins_emparelhados_old = set()
    refins_emparelhados_new = set()

    for old in excluidos_refin:
        if old.get("tipo") in ("RMC", "RCC"):
            continue
        for new in novos_refin:
            if new.get("tipo") in ("RMC", "RCC"):
                continue
            if new.get("banco") != old.get("banco"):
                continue
            if not datas_proximas(old["_dt_exclusao"], new["_dt_inclusao"]):
                continue
            # PASSE 1: exigir valor compatível
            if not valores_compativeis(old.get("_v_parcela"), new.get("_v_parcela")):
                continue
            adj[old["contrato"]].add(new["contrato"])
            adj[new["contrato"]].add(old["contrato"])
            arestas.append((old["contrato"], new["contrato"], "REFIN"))
            refins_emparelhados_old.add(old["contrato"])
            refins_emparelhados_new.add(new["contrato"])

    # PASSE 2: o que sobrou (sem par 1→1) tenta cadeias N→1 e 1→N
    # agrupando old/new por (banco, data)
    sobra_old = [o for o in excluidos_refin
                 if o.get("tipo") not in ("RMC", "RCC")
                 and o["contrato"] not in refins_emparelhados_old]
    sobra_new = [n for n in novos_refin
                 if n.get("tipo") not in ("RMC", "RCC")
                 and n["contrato"] not in refins_emparelhados_new]

    # Agrupar por (banco, data ± 1 dia)
    grupos_old = defaultdict(list)
    for o in sobra_old:
        grupos_old[(o.get("banco"), o["_dt_exclusao"])].append(o)
    grupos_new = defaultdict(list)
    for n in sobra_new:
        grupos_new[(n.get("banco"), n["_dt_inclusao"])].append(n)

    for (banco_o, data_o), olds in grupos_old.items():
        for (banco_n, data_n), news in grupos_new.items():
            if banco_o != banco_n:
                continue
            if not datas_proximas(data_o, data_n):
                continue
            # Verificar soma dos valores: N→1 (soma das parcelas excluídas ≈ parcela do novo)
            # ou 1→N (parcela do excluído ≈ soma dos novos)
            total_old = sum(o.get("_v_parcela") or 0 for o in olds)
            total_new = sum(n.get("_v_parcela") or 0 for n in news)
            # Consolidação/fracionamento: tolerância de 25% (refins podem ter
            # aporte adicional ou abatimento de IOF, alterando soma de parcelas).
            if not valores_compativeis(total_old, total_new, tolerancia=10.0, tol_pct=0.25):
                continue
            # Conectar todos com todos no grupo
            for o in olds:
                for n in news:
                    adj[o["contrato"]].add(n["contrato"])
                    adj[n["contrato"]].add(o["contrato"])
                    arestas.append((o["contrato"], n["contrato"], "REFIN"))

    # 2) Portabilidade (atravessa bancos)
    for old in excluidos_port:
        for new in novos_port:
            if not datas_proximas(old["_dt_exclusao"], new["_dt_inclusao"], tolerancia_dias=3):
                continue
            adj[old["contrato"]].add(new["contrato"])
            adj[new["contrato"]].add(old["contrato"])
            arestas.append((old["contrato"], new["contrato"], "PORT"))

    # 3) Substituição RMC/RCC (mesmo banco, exclusão banco + averbação nova no dia seguinte)
    for old in excluidos_banco_rmc:
        for new in novos_averb_rmc:
            if new.get("banco") != old.get("banco"):
                continue
            if old.get("contrato") == new.get("contrato"):
                continue
            if not datas_proximas(old["_dt_exclusao"], new["_dt_inclusao"], tolerancia_dias=2):
                continue
            adj[old["contrato"]].add(new["contrato"])
            adj[new["contrato"]].add(old["contrato"])
            arestas.append((old["contrato"], new["contrato"], "SUBST_BANCO"))

    # Encontrar componentes conectados (BFS)
    todos_ids = {c["contrato"] for c in contratos}
    visitados = set()
    componentes = []
    contratos_dict = {c["contrato"]: c for c in contratos}

    for cid in todos_ids:
        if cid in visitados:
            continue
        # BFS
        comp = []
        fila = [cid]
        while fila:
            x = fila.pop()
            if x in visitados:
                continue
            visitados.add(x)
            comp.append(x)
            for viz in adj[x]:
                if viz not in visitados:
                    fila.append(viz)
        componentes.append(comp)

    # Classificar cada componente
    resultado = []
    cor_idx = 0
    for comp_ids in componentes:
        comp_contratos = [contratos_dict[i] for i in comp_ids if i in contratos_dict]
        if not comp_contratos:
            continue
        comp_contratos.sort(key=lambda c: c["_dt_inclusao"] or datetime.min)

        bancos = sorted(set(c.get("banco", "?") for c in comp_contratos))
        is_cadeia = len(comp_contratos) > 1
        subtipo = "ISOLADO"
        cor, cor_nome = COR_NEUTRA

        if is_cadeia:
            # Atribuir cor da paleta
            cor, cor_nome = PALETA_CORES[cor_idx % len(PALETA_CORES)]
            cor_idx += 1

            # Verificar tipos de cadeia
            arestas_comp = [a for a in arestas if a[0] in comp_ids and a[1] in comp_ids]
            tipos_aresta = set(a[2] for a in arestas_comp)

            if "PORT" in tipos_aresta:
                subtipo = "PORTABILIDADE_INTER_BANCO"
            elif "SUBST_BANCO" in tipos_aresta:
                subtipo = "SUBSTITUICAO_BANCO"
            elif "REFIN" in tipos_aresta:
                # Distinguir 1→1, N→1, 1→N, recursivo
                excluidos_no_comp = [c for c in comp_contratos
                                     if c.get("motivo_exclusao") and "refinanciament" in c["motivo_exclusao"].lower()]
                novos_no_comp = [c for c in comp_contratos
                                 if c.get("origem") and "refinanciament" in c["origem"].lower()]
                if len(excluidos_no_comp) == 1 and len(novos_no_comp) == 1:
                    subtipo = "REFIN_DIRETO"
                elif len(excluidos_no_comp) > 1 and len(novos_no_comp) == 1:
                    subtipo = "CONSOLIDACAO"
                elif len(excluidos_no_comp) == 1 and len(novos_no_comp) > 1:
                    subtipo = "FRACIONAMENTO"
                else:
                    subtipo = "CADEIA_RECURSIVA"

        # Determinar papéis (ANCESTRAL / ATUAL)
        for i, c in enumerate(comp_contratos):
            if i == len(comp_contratos) - 1:
                c["_papel"] = "ATUAL"
            else:
                c["_papel"] = "ANCESTRAL"
            c["_ordem"] = i + 1

        # Valor de referência (parcela do mais recente)
        ref = comp_contratos[-1]
        valor_ref = ref.get("valor_parcela") or "?"
        data_ref = ref.get("data_inclusao") or "?"

        resultado.append({
            "id": f"C-{len(resultado)+1:02d}",
            "tipo": "CADEIA" if is_cadeia else "ISOLADO",
            "subtipo": subtipo,
            "bancos": bancos,
            "beneficio": beneficio_pasta,
            "contratos": [
                {**{k: v for k, v in c.items() if not k.startswith("_")},
                 "papel": c["_papel"],
                 "ordem": c["_ordem"]}
                for c in comp_contratos
            ],
            "valor_parcela_referencia": valor_ref,
            "data_referencia": data_ref,
            "cor_grifo": cor,
            "cor_nome": cor_nome,
        })

    # Ordenar componentes: cadeias primeiro, depois isolados; por banco
    resultado.sort(key=lambda r: (
        0 if r["tipo"] == "CADEIA" else 1,
        r["bancos"][0] if r["bancos"] else "",
        r["data_referencia"] or "",
    ))
    # Reatribuir IDs sequenciais após sort
    for i, r in enumerate(resultado):
        r["id"] = f"C-{i+1:02d}"
    return resultado


def agrupar_em_pastas_acao(componentes: list[dict]) -> dict:
    """
    Decide o nome de pasta de cada componente.

    Regras:
    - Componente todo do mesmo banco → pasta = nome do banco
    - Componente envolve >1 banco (portabilidade) → pasta = "Banco A + Banco B"
    - Sufixo " - RMC-RCC" se algum contrato é RMC/RCC

    Componentes do mesmo banco SEM cadeia inter-banco vão pra mesma pasta.
    """
    # Agrupar por chave (frozenset de bancos + tipo)
    pastas = defaultdict(list)
    for comp in componentes:
        bancos = tuple(sorted(comp["bancos"]))
        tipos = set(c.get("tipo", "CONSIGNADO") for c in comp["contratos"])
        eh_cartao = "RMC" in tipos or "RCC" in tipos
        chave = (bancos, eh_cartao)
        pastas[chave].append(comp)

    out = {}
    for (bancos, eh_cartao), comps in pastas.items():
        nome = " + ".join(_nome_pasta_banco(b) for b in bancos)
        if eh_cartao:
            nome += " - RMC-RCC"
        out[nome] = comps
    return out


def _nome_pasta_banco(banco_completo: str) -> str:
    """
    Normaliza nome do banco para pasta. Ex:
    'BANCO ITAU CONSIGNADO SA' → 'BANCO ITAU CONSIGNADO'
    'CAIXA ECONOMICA FEDERAL' → 'CAIXA ECONOMICA FEDERAL'
    """
    s = banco_completo.upper().strip()
    s = re.sub(r"\s+S\.?A\.?$", "", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    todos_contratos = []
    for arg in sys.argv[1:]:
        with open(arg, encoding="utf-8") as f:
            d = json.load(f)
        beneficio = d.get("beneficio", {}).get("pasta_beneficio", "")
        for c in d.get("contratos", []):
            c["_beneficio_pasta"] = beneficio
        todos_contratos.extend(d.get("contratos", []))

    # Agrupar por benefício antes de detectar (cadeias não cruzam benefícios)
    por_beneficio = defaultdict(list)
    for c in todos_contratos:
        por_beneficio[c.get("_beneficio_pasta", "")].append(c)

    todas_cadeias = []
    for benef, contratos in por_beneficio.items():
        cadeias = detectar_cadeias(contratos, beneficio_pasta=benef)
        todas_cadeias.extend(cadeias)

    # Agrupar em pastas de ação
    pastas = agrupar_em_pastas_acao(todas_cadeias)

    print(f"Total de componentes: {len(todas_cadeias)}")
    print(f"Pastas de ação: {len(pastas)}")
    for nome_pasta, comps in pastas.items():
        print(f"\n  [{nome_pasta}] - {len(comps)} componente(s)")
        for c in comps:
            contratos_str = " → ".join(x["contrato"] for x in c["contratos"])
            print(f"    {c['id']} [{c['subtipo']}] {contratos_str}")


if __name__ == "__main__":
    main()
