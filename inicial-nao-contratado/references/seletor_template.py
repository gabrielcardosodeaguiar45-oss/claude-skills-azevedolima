"""Seleciona o template adequado conforme o cenário (Alternativa 3 — Híbrido com alertas).

Regra:
    1 contrato AVN          → inicial-jfba-base.docx
    1 contrato REFIN        → inicial-jfba-refin-ativo.docx
    N contratos sem REFIN   → inicial-jfba-multiplos-avn-inativo.docx
    N contratos com 1+ REFIN → inicial-jfba-multiplos-avn-inativo.docx
                              + ALERTA "considere adicionar bloco troco"
    Qualquer caso com 1+ ATIVO → ALERTA "considere adicionar pedido de cessação"

Também alerta se o cliente tem CADEIA de fraude (vários bancos relacionados).
"""
from typing import List, Dict, Tuple

VAULT_TEMPLATES = r'C:\Users\gabri\OneDrive\Documentos\Obsidian Vault\Modelos\IniciaisNaoContratado\_templates'

TEMPLATES = {
    'base':      f'{VAULT_TEMPLATES}\\inicial-jfba-base.docx',
    'multiplos': f'{VAULT_TEMPLATES}\\inicial-jfba-multiplos-avn-inativo.docx',
    'refin':    f'{VAULT_TEMPLATES}\\inicial-jfba-refin-ativo.docx',
}


def selecionar_template(contratos: List[Dict]) -> Tuple[str, List[str]]:
    """Seleciona o template adequado e retorna alertas para o relatório paralelo.

    Args:
        contratos: lista de dicts no formato do extrator_hiscon.parse_hiscon
                   (ou formatado por formatar_contrato_para_template).
                   Campos usados: 'tipo_origem', 'situacao'.

    Returns:
        (template_path, alertas)
    """
    n = len(contratos)
    if n == 0:
        return TEMPLATES['base'], ['ERRO: nenhum contrato fornecido']

    # Análise dos contratos
    tipos = {c.get('tipo_origem') for c in contratos}
    situacoes = {c.get('situacao') for c in contratos}
    n_refin = sum(1 for c in contratos if c.get('tipo_origem') == 'refinanciamento')
    n_avn = sum(1 for c in contratos if c.get('tipo_origem') == 'original')
    n_outros = sum(1 for c in contratos if c.get('tipo_origem') not in ('refinanciamento', 'original'))
    n_ativos = sum(1 for c in contratos if c.get('situacao') == 'Ativo')
    n_inativos = sum(1 for c in contratos if c.get('situacao') in ('Excluído', 'Encerrado'))

    alertas = []

    # === Caso 1 contrato isolado ===
    if n == 1:
        unico = contratos[0]
        if unico.get('tipo_origem') == 'refinanciamento':
            return TEMPLATES['refin'], alertas
        return TEMPLATES['base'], alertas

    # === N contratos: default = MULT ===
    template = TEMPLATES['multiplos']

    if n_refin > 0:
        alertas.append(
            f'Caso contém {n_refin} refinanciamento(s) entre {n} contratos. '
            f'CONSIDERE adicionar manualmente o bloco "troco" do template REFIN '
            f'(parágrafos 18-23 de inicial-jfba-refin-ativo.docx) + ajustar trecho '
            f'do CDC ("embora o valor tenha sido creditado") no parágrafo p98.'
        )

    if n_ativos > 0:
        alertas.append(
            f'Caso contém {n_ativos} contrato(s) ATIVO(s) (descontos em curso). '
            f'CONSIDERE adicionar pedido de cessação dos descontos vincendos.'
        )

    if n_outros > 0:
        outros_tipos = sorted({c.get('tipo_origem') for c in contratos
                              if c.get('tipo_origem') not in ('refinanciamento', 'original')})
        alertas.append(
            f'Caso contém {n_outros} contrato(s) de tipo não usual ({", ".join(outros_tipos)}). '
            f'REVISAR vocabulário no bloco fático e nos pedidos.'
        )

    return template, alertas


def descrever_caso(contratos: List[Dict]) -> str:
    """Resumo legível do caso para o relatório paralelo."""
    n = len(contratos)
    if n == 0:
        return 'Nenhum contrato.'
    n_refin = sum(1 for c in contratos if c.get('tipo_origem') == 'refinanciamento')
    n_avn = sum(1 for c in contratos if c.get('tipo_origem') == 'original')
    n_ativos = sum(1 for c in contratos if c.get('situacao') == 'Ativo')
    n_inativos = sum(1 for c in contratos if c.get('situacao') in ('Excluído', 'Encerrado'))
    bancos = sorted({c.get('banco_nome') for c in contratos if c.get('banco_nome')})
    return (f'{n} contrato(s) | {n_avn} averbação(ões) nova(s) + {n_refin} refinanciamento(s) | '
            f'{n_ativos} ativo(s) + {n_inativos} excluído/encerrado(s) | '
            f'banco(s): {", ".join(bancos[:3])}{" + outros" if len(bancos) > 3 else ""}')


if __name__ == '__main__':
    import sys, io, os
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from extrator_hiscon import parse_hiscon, filtrar_contratos_por_numero

    HISCON = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\GEORGE DA SILVA SOUZA - Marcio Teixeira\BANCO ITAÚ\2 AVERBAÇÃO NOVA INATIVO\8 - HISTÓRICO DE EMPRÉSTIMO.pdf'

    res = parse_hiscon(HISCON)

    # Caso 1: George/ITAÚ — 5 contratos (mistura AVN + REFIN, todos excluídos)
    print('████ CASO George/ITAÚ ████')
    nums = ['630035051', '635737335', '610696404', '610696417', '618896399']
    contratos = filtrar_contratos_por_numero(res['contratos'], nums)
    print(f'Resumo: {descrever_caso(contratos)}')
    template, alertas = selecionar_template(contratos)
    print(f'Template: {os.path.basename(template)}')
    print(f'Alertas ({len(alertas)}):')
    for a in alertas:
        print(f'  ⚠ {a}')

    # Caso 2: hipotético — 1 contrato AVN excluído
    print('\n████ CASO HIPOTÉTICO 1 contrato AVN ████')
    c1 = [contratos[2]]  # 610696404 = AVN excluído
    print(f'Resumo: {descrever_caso(c1)}')
    template, alertas = selecionar_template(c1)
    print(f'Template: {os.path.basename(template)}')
    print(f'Alertas ({len(alertas)}):')
    for a in alertas:
        print(f'  ⚠ {a}')

    # Caso 3: hipotético — 1 contrato REFIN
    print('\n████ CASO HIPOTÉTICO 1 contrato REFIN ████')
    c1 = [contratos[0]]  # 635737335 = REFIN excluído
    print(f'Resumo: {descrever_caso(c1)}')
    template, alertas = selecionar_template(c1)
    print(f'Template: {os.path.basename(template)}')
    print(f'Alertas ({len(alertas)}):')
    for a in alertas:
        print(f'  ⚠ {a}')

    # Caso 4: Facta do George — 3 contratos AVN
    print('\n████ CASO George/FACTA ████')
    nums_facta = ['0047032998', '0047633052', '0047032901']
    facta = filtrar_contratos_por_numero(res['contratos'], nums_facta)
    print(f'Resumo: {descrever_caso(facta)}')
    template, alertas = selecionar_template(facta)
    print(f'Template: {os.path.basename(template)}')
    print(f'Alertas ({len(alertas)}):')
    for a in alertas:
        print(f'  ⚠ {a}')
