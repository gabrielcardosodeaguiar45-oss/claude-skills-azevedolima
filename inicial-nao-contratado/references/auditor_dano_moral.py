"""Auditor do dano moral pleiteado.

Calcula o valor do dano moral conforme a regra do escritório:
    1 contrato isolado     → R$ 15.000,00
    2+ contratos do mesmo banco → R$ 5.000,00 × N

Compara com o valor "DANOS MORAIS" extraído do PDF de cálculo. Se divergir,
gera ALERTA mas usa o valor da regra (porque o PDF pode ter sido gerado
com outra premissa que precisa ser revisada).

Decisão 07/05/2026: dano TEMPORAL foi removido do projeto. Auditor não checa.
"""
from typing import List, Dict, Optional


def calcular_dano_moral(contratos: List[Dict]) -> Dict:
    """Calcula o dano moral conforme regra do escritório.

    Returns:
        {
            'unitario': float ou None (5k apenas se N>=2),
            'total': float,
            'n_contratos': int,
            'regra_aplicada': str ('1 contrato = R$ 15k' / '2+ contratos = R$ 5k × N')
        }
    """
    n = len(contratos)
    if n == 1:
        return {
            'unitario': None,
            'total': 15000.00,
            'n_contratos': 1,
            'regra_aplicada': '1 contrato isolado = R$ 15.000,00 fixo',
        }
    return {
        'unitario': 5000.00,
        'total': 5000.00 * n,
        'n_contratos': n,
        'regra_aplicada': f'{n} contratos = R$ 5.000,00 × {n} = R$ {5000.00 * n:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'),
    }


def auditar_dano_moral(contratos: List[Dict], dano_moral_pdf: Optional[float]) -> Dict:
    """Compara o cálculo da regra com o valor extraído do PDF.

    Args:
        contratos: lista de contratos questionados
        dano_moral_pdf: valor extraído do PDF de cálculo (linha "DANOS MORAIS")
                        ou None se não foi possível extrair

    Returns:
        {
            'dano_moral_regra': float (calculado pela regra),
            'dano_moral_pdf': float ou None,
            'divergencia': bool (True se PDF != regra),
            'diferenca': float (PDF - regra) ou None,
            'alerta': str ou None,
        }
    """
    regra = calcular_dano_moral(contratos)
    valor_regra = regra['total']

    if dano_moral_pdf is None:
        return {
            'dano_moral_regra': valor_regra,
            'dano_moral_pdf': None,
            'divergencia': False,
            'diferenca': None,
            'alerta': (f'Não foi possível extrair o valor "DANOS MORAIS" do PDF de cálculo. '
                       f'Usando o valor da regra: R$ {valor_regra:,.2f}.').replace(',', '#').replace('.', ',').replace('#', '.'),
        }

    # Comparar (com tolerância de R$ 0,01)
    div = abs(valor_regra - dano_moral_pdf) > 0.01
    if not div:
        return {
            'dano_moral_regra': valor_regra,
            'dano_moral_pdf': dano_moral_pdf,
            'divergencia': False,
            'diferenca': 0.0,
            'alerta': None,
        }

    # Há divergência
    diff = dano_moral_pdf - valor_regra
    sinal = '+' if diff > 0 else ''
    n = regra['n_contratos']
    alerta = (
        f'⚠ DIVERGÊNCIA DANO MORAL: PDF de cálculo traz R$ {dano_moral_pdf:,.2f}; '
        f'regra do escritório para {n} contrato(s) seria R$ {valor_regra:,.2f} '
        f'(diferença {sinal}R$ {diff:,.2f}). '
        f'A inicial USARÁ o valor da regra. CONFERIR antes do protocolo: '
        f'(a) o cálculo está desatualizado? '
        f'(b) refazer o cálculo com a regra correta? '
        f'(c) excepcionalmente manter o valor do PDF na peça?'
    ).replace(',', '#').replace('.', ',').replace('#', '.')

    return {
        'dano_moral_regra': valor_regra,
        'dano_moral_pdf': dano_moral_pdf,
        'divergencia': True,
        'diferenca': diff,
        'alerta': alerta,
    }


if __name__ == '__main__':
    import sys, io, os
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from extrator_hiscon import parse_hiscon, filtrar_contratos_por_numero
    from extrator_calculo import parse_calculo

    BASE = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\GEORGE DA SILVA SOUZA - Marcio Teixeira'
    HISCON = os.path.join(BASE, r'BANCO ITAÚ\2 AVERBAÇÃO NOVA INATIVO\8 - HISTÓRICO DE EMPRÉSTIMO.pdf')
    res = parse_hiscon(HISCON)

    casos = [
        ('ITAÚ',    ['630035051', '635737335', '610696404', '610696417', '618896399'],
         os.path.join(BASE, r'BANCO ITAÚ\2 AVERBAÇÃO NOVA INATIVO\9- CÁLCULO.pdf')),
        ('FACTA',   ['0047032998', '0047633052', '0047032901'],
         os.path.join(BASE, r'BANCO FACTA\1 AVERBAÇÃO NOVA INATIVO\10- CÁLCULO.pdf')),
        ('AGIBANK', ['1500981514', '1500982286'],
         os.path.join(BASE, r'BANCO AGIBANK\1 REFINANCIAMENTO INATIVO\10- CÁLCULO.pdf')),
        ('PAN',     ['3382321366', '3424011702'],
         os.path.join(BASE, r'BANCO PAN\1 AVERBAÇÃO NOVA INATIVO\10- CÁLCULO.pdf')),
    ]

    for label, nums, calc_path in casos:
        print(f'\n████ CASO George/{label} ████')
        contratos = filtrar_contratos_por_numero(res['contratos'], nums)
        print(f'  Contratos questionados (das procurações): {len(nums)}')
        print(f'  Contratos encontrados no HISCON:           {len(contratos)}')

        regra = calcular_dano_moral(contratos)
        print(f'  Regra: {regra["regra_aplicada"]}')

        pdf = parse_calculo(calc_path)
        print(f'  PDF cálculo — Total Geral: R$ {pdf["valor_total_geral"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
        print(f'  PDF cálculo — Dano moral pleiteado: {pdf["dano_moral_pleiteado_pdf"]}')

        audit = auditar_dano_moral(contratos, pdf['dano_moral_pleiteado_pdf'])
        if audit['alerta']:
            print(f'  {audit["alerta"]}')
        else:
            print(f'  ✓ Dano moral OK: R$ {audit["dano_moral_regra"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
