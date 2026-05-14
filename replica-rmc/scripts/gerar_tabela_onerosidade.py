"""
Gera os 6 valores da tabela de onerosidade do mérito da réplica RMC/RCC,
adaptando a 6ª coluna conforme o cenário do caso.

Entrada: caminho para _analise.json
Saída: JSON estruturado com os 6 cabeçalhos + 6 valores, prontos para inserção
       em python-docx.

Regra de adaptação da 6ª coluna:
. Se faturas.refin_maquiador_detectado == True:
    cabeçalho = "Valor supostamente refinanciado"
    valor = R$ <faturas.valor_refin_maquiador>
. Caso contrário:
    cabeçalho = "Excesso pago sobre o principal"
    valor = "R$ <delta> (<percentual>%)" onde delta = valor_pago - valor_emprestado

Uso:
    python gerar_tabela_onerosidade.py <caminho>/_analise.json
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path


MESES_PT = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
    7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
}


def fmt_brl(valor):
    """Formata float como R$ no padrão brasileiro (vírgula decimal, ponto milhar)."""
    if valor is None:
        return "—"
    s = f"{valor:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def fmt_competencia(data_iso):
    """De '2023-04-10' para 'maio/2023' (mês seguinte da averbação)."""
    if not data_iso:
        return "—"
    dt = datetime.strptime(data_iso, "%Y-%m-%d").date()
    mes = dt.month + 1
    ano = dt.year
    if mes > 12:
        mes = 1
        ano += 1
    return f"{MESES_PT[mes]}/{ano}"


def meses_decorridos(data_inicio_iso, data_fim=None):
    """Conta meses entre data_inicio (mês seguinte à averbação) e data_fim (default hoje)."""
    if data_fim is None:
        data_fim = date.today()
    inicio = datetime.strptime(data_inicio_iso, "%Y-%m-%d").date()
    inicio_mes_seg = date(
        inicio.year + (1 if inicio.month == 12 else 0),
        1 if inicio.month == 12 else inicio.month + 1,
        1,
    )
    if data_fim < inicio_mes_seg:
        return 0
    return (data_fim.year - inicio_mes_seg.year) * 12 + (data_fim.month - inicio_mes_seg.month) + 1


def gerar_tabela(analise):
    contrato = analise.get("contrato_principal", {}) or {}
    teds = analise.get("teds", []) or []
    faturas = analise.get("faturas", {}) or {}

    valor_emprestimo = sum((t.get("valor") or 0) for t in teds) or contrato.get("limite") or 0
    data_averbacao = contrato.get("data_averbacao")
    parcela_media = contrato.get("parcela_media") or 0
    n_parcelas = meses_decorridos(data_averbacao) if data_averbacao else 0
    valor_pago = n_parcelas * parcela_media

    refin = bool(faturas.get("refin_maquiador_detectado"))
    valor_refin = faturas.get("valor_refin_maquiador")

    if refin:
        cab_6 = "Valor supostamente refinanciado"
        val_6 = fmt_brl(valor_refin)
    else:
        delta = valor_pago - valor_emprestimo
        if valor_emprestimo > 0:
            pct = (delta / valor_emprestimo) * 100
            sinal = "+" if delta >= 0 else "−"
            val_6 = f"{fmt_brl(abs(delta))} ({sinal}{abs(pct):.1f}%)"
        else:
            val_6 = "—"
        cab_6 = "Excesso pago sobre o principal"

    return {
        "cabecalhos": [
            "Valor do empréstimo",
            "Início dos descontos",
            "Valor médio das parcelas",
            "Nº de parcelas pagas",
            "Valor pago até o momento",
            cab_6,
        ],
        "valores": [
            fmt_brl(valor_emprestimo),
            fmt_competencia(data_averbacao),
            fmt_brl(parcela_media),
            str(n_parcelas),
            fmt_brl(valor_pago),
            val_6,
        ],
        "_meta": {
            "refin_maquiador_detectado": refin,
            "valor_emprestimo_numerico": valor_emprestimo,
            "valor_pago_numerico": valor_pago,
            "delta_numerico": valor_pago - valor_emprestimo if not refin else None,
        },
    }


def main():
    if len(sys.argv) != 2:
        print("Uso: python gerar_tabela_onerosidade.py <caminho>/_analise.json", file=sys.stderr)
        sys.exit(1)

    caminho = Path(sys.argv[1])
    if not caminho.is_file():
        print(f"Arquivo não encontrado: {caminho}", file=sys.stderr)
        sys.exit(1)

    analise = json.loads(caminho.read_text(encoding="utf-8"))
    resultado = gerar_tabela(analise)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
