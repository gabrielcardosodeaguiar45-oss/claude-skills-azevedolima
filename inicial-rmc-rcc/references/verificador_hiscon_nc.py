"""Verificador HISCON para casos de empréstimo NÃO CONTRATADO.

Regra (paradigma do usuario, 2026-05-13):
Para CASOS NC (rubrica 216 CONSIGNACAO EMPRESTIMO BANCARIO), os descontos
podem ser PRESUMIDOS a partir dos campos do HISCON:
  - data_inclusao
  - competencia_inicio / competencia_fim
  - qtd_parcelas
  - valor_parcela

Diferente de RMC/RCC (onde precisamos do HISCRE para descontos reais), no
NC o HISCON declara a estrutura do contrato e podemos somar valor_parcela x
qtd_parcelas (ou competencia_inicio -> competencia_fim).

Esta funcao NAO bloqueia a geracao da inicial — apenas valida que o
contrato no JSON tem os campos minimos para presumir os descontos.
"""


def verificar_contrato_nc(contrato):
    """Valida se o contrato (do _estado_cliente.json) tem dados suficientes
    para presumir os descontos no NC.

    Args:
        contrato: dict do _estado_cliente.json com campos do HISCON

    Returns:
        dict {
            'gera_inicial': bool,
            'motivos_bloqueio': list[str],
            'avisos': list[str],
            'descontos_presumidos': int (qtd parcelas previstas),
            'soma_presumida': float (valor_parcela * qtd_parcelas),
        }
    """
    motivos = []
    avisos = []
    gera = True

    valor_parcela = contrato.get("valor_parcela")
    qtd = contrato.get("qtd_parcelas")
    inicio = contrato.get("competencia_inicio")
    fim = contrato.get("competencia_fim")
    data_inclusao = contrato.get("data_inclusao")
    virtual = contrato.get("_virtual", False)

    if virtual:
        motivos.append(
            "Contrato marcado como 'Nao localizado no HISCON' (_virtual: true). "
            "Sem rastro de averbacao para calcular descontos presumidos."
        )
        gera = False

    if not valor_parcela:
        motivos.append("Campo 'valor_parcela' ausente no _estado_cliente.json.")
        gera = False
    if not qtd:
        motivos.append("Campo 'qtd_parcelas' ausente.")
        gera = False
    if not inicio:
        avisos.append("Campo 'competencia_inicio' ausente — usar data_inclusao como aproximacao.")

    # Calcular descontos presumidos
    soma = 0.0
    if valor_parcela and qtd:
        try:
            vp = float(str(valor_parcela).replace("R$", "").replace(".", "").replace(",", ".").strip())
            soma = vp * int(qtd)
        except (ValueError, TypeError):
            avisos.append(f"Nao foi possivel parsear valor_parcela={valor_parcela}")

    return {
        "gera_inicial": gera,
        "motivos_bloqueio": motivos,
        "avisos": avisos,
        "descontos_presumidos": int(qtd) if qtd else 0,
        "soma_presumida": soma,
        "valor_parcela_str": valor_parcela,
        "competencia_inicio": inicio,
        "competencia_fim": fim,
        "data_inclusao": data_inclusao,
    }
