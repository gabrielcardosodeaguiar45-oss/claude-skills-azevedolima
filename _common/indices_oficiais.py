"""Índices oficiais para correção monetária e cálculo de juros.

INPC: Índice Nacional de Preços ao Consumidor (IBGE), fonte oficial BCB série
188. Usado para correção monetária de dívidas civis de responsabilidade
(decisão STJ — danos morais e materiais por ilícito).

A tabela é carregada de `dados/inpc_bcb_serie188.json` (snapshot baixado da
API do BCB). Atualizar periodicamente com:

    curl -sL "https://api.bcb.gov.br/dados/serie/bcdata.sgs.188/dados?formato=json&dataInicial=01/01/2017&dataFinal=31/12/2026" \\
         -o skills/_common/dados/inpc_bcb_serie188.json

Funções principais:
  - inpc_acumulado_entre(mes_origem, mes_final) → fator (1.0234 = 2.34%)
  - corrigir_inpc(valor, data_origem, data_final) → valor corrigido
  - juros_simples_mes(valor, data_origem, data_final, taxa_pct=1.0) → juros
"""
import json
import os
from datetime import date
from typing import Tuple

_DADOS_DIR = os.path.join(os.path.dirname(__file__), 'dados')
_INPC_PATH = os.path.join(_DADOS_DIR, 'inpc_bcb_serie188.json')


def _carregar_inpc() -> dict:
    """Retorna dict {(ano, mes): variacao_decimal}. Ex: (2024, 1) → 0.0042."""
    with open(_INPC_PATH, encoding='utf-8') as f:
        raw = json.load(f)
    tab = {}
    for ponto in raw:
        # "data": "01/01/2017", "valor": "0.42" → variação MENSAL em %
        dia, mes, ano = ponto['data'].split('/')
        tab[(int(ano), int(mes))] = float(ponto['valor']) / 100.0
    return tab


_INPC_MENSAL = _carregar_inpc()

# Último mês com dado oficial disponível
INPC_ULTIMO_MES = max(_INPC_MENSAL.keys())  # (ano, mes)


def _iter_meses(ini: Tuple[int, int], fim: Tuple[int, int]):
    """Itera (ano, mes) inclusive de ini até fim. ini ≤ fim."""
    a, m = ini
    while (a, m) <= fim:
        yield (a, m)
        m += 1
        if m > 12:
            m = 1
            a += 1


def inpc_acumulado_entre(mes_origem: Tuple[int, int],
                          mes_final: Tuple[int, int]) -> float:
    """Fator acumulado INPC entre dois meses (inclusive). Retorna 1.0xxx.

    Convenção: correção começa NO MÊS POSTERIOR ao do desconto (não corrige o
    próprio mês de origem porque o valor era "presente" naquele mês). Aplica
    INPC dos meses (origem+1) até (final), inclusive.

    Args:
        mes_origem: (ano, mes) do desconto
        mes_final: (ano, mes) da apuração (geralmente hoje)

    Returns:
        Fator > 1.0 (ex.: 1.0345 = +3.45% de INPC acumulado)
    """
    if mes_origem >= mes_final:
        return 1.0
    # Próximo mês após origem
    a, m = mes_origem
    m += 1
    if m > 12:
        m = 1
        a += 1
    inicio = (a, m)
    if inicio > mes_final:
        return 1.0
    # Limita a mes_final ao último disponível
    fim = min(mes_final, INPC_ULTIMO_MES)
    fator = 1.0
    for ano_mes in _iter_meses(inicio, fim):
        var = _INPC_MENSAL.get(ano_mes)
        if var is None:
            # Mês sem dado: ignora (mantém fator anterior)
            continue
        fator *= (1.0 + var)
    return fator


def corrigir_inpc(valor: float, data_origem: date, data_final: date) -> float:
    """Aplica INPC acumulado entre data_origem e data_final. Retorna valor corrigido."""
    fator = inpc_acumulado_entre(
        (data_origem.year, data_origem.month),
        (data_final.year, data_final.month),
    )
    return valor * fator


def meses_entre(data_origem: date, data_final: date) -> int:
    """Número de meses inteiros entre 2 datas (apenas considerando mês/ano)."""
    if data_final <= data_origem:
        return 0
    return (data_final.year - data_origem.year) * 12 + (data_final.month - data_origem.month)


def juros_simples_mes(valor: float, data_origem: date, data_final: date,
                        taxa_pct: float = 1.0) -> float:
    """Juros simples mensais. Default 1% ao mês (juros legais pré Lei 14.905/2024).

    Para casos pós Lei 14.905/2024 (vigência 30/08/2024), a taxa legal passou
    a ser SELIC menos IPCA. Por ora usamos 1% ao mês simples como padrão (o
    procurador edita se necessário).
    """
    n = meses_entre(data_origem, data_final)
    return valor * (taxa_pct / 100.0) * n


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    # Teste rápido
    print(f'INPC último disponível: {INPC_ULTIMO_MES}')
    print(f'INPC pontos: {len(_INPC_MENSAL)}')
    # Correção de R$ 100,00 de jan/2020 até abr/2026
    fator = inpc_acumulado_entre((2020, 1), (2026, 4))
    print(f'Fator INPC (jan/2020 → abr/2026): {fator:.6f}')
    print(f'R$ 100,00 corrigido: R$ {100*fator:.2f}')
    print(f'Juros 1% jan/2020 → abr/2026: R$ {juros_simples_mes(100, date(2020, 1, 1), date(2026, 4, 1)):.2f}')
