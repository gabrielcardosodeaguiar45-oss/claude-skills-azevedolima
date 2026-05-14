"""Roda pipeline para o EXEMPLO GEORGE — pasta atual `BANCO FACTA\\1 AVERBAÇÃO NOVA INATIVO`
(reestruturada para a raiz de APP - NÃO CONTRATADO).

Valida o ciclo completo após os fixes de:
  - bug do typo no nome do arquivo da procuração (fuzzy match dist=1)
  - bug da competência fim 1 mês antes (parser HISCON agora extrai col 5/6)
  - regra dos 2+ fuzzy matches (alerta CRÍTICO de erro sistemático)
"""
import io, sys, os
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import (montar_dados_inicial, gerar_inicial,
                             gerar_relatorio_paralelo)

AUTORA = {
    'nome': 'EXEMPLO GEORGE DA SILVA SOUZA',
    'nacionalidade': 'brasileiro',
    'estado_civil': 'solteiro',
    'profissao': 'aposentado',
    'cpf': '000.000.009-19',
    'rg': '1000007-7',
    'orgao_expedidor': 'SSP/BA',
    'data_nascimento': datetime(1966, 10, 11),
    'nome_mae': 'ELIETA DA SILVA SOUZA',
    'logradouro': 'Travessa Fernando Tul',
    'numero': '54',
    'bairro': 'Santo Pedro',
    'cidade': 'Camaçari',
    'uf': 'BA',
    'cep': '42.800-149',
    'renda_liquida': None,  # virá do HISCRE
}

PASTA = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\BANCO FACTA\1 AVERBAÇÃO NOVA INATIVO'
DOCX_OUT = os.path.join(PASTA, 'INICIAL_NaoContratado_EXEMPLO GEORGE_FACTA.docx')
RELAT_OUT = os.path.join(PASTA, '_RELATORIO_PENDENCIAS_EXEMPLO GEORGE_FACTA.docx')


def main():
    print('████████████ EXEMPLO GEORGE × FACTA ████████████')
    if not os.path.isdir(PASTA):
        print(f'❌ Pasta não existe: {PASTA}')
        return

    try:
        dados = montar_dados_inicial(PASTA, AUTORA, subsecao='Salvador',
                                      banco_jurisdicao='matriz')
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback; traceback.print_exc()
        return

    print(f'  Procurações:    {len(dados["numeros_procuracoes"])}')
    print(f'  Contratos no HISCON (filtrados): {len(dados["contratos_questionados"])}')
    print(f'  Banco-réu:      {dados["banco_reu"]["nome"]}')
    print(f'  Template:       {os.path.basename(dados["template"])}')
    print(f'  Dano moral:     R$ {dados["dano_moral"]["total"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
    print(f'  Valor causa:    R$ {(dados["calculo"].get("valor_total_geral") or 0):,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
    print(f'  Idoso:          {dados["eh_idoso"]}')
    print()
    print('  Contratos formatados:')
    for c in dados['contratos_questionados']:
        print(f'    {c["numero"]:12} | qtd={c["qtd_parcelas"]:3} | parc=R$ {c["valor_parcela_str"]:>9} '
              f'| {c["competencia_inicio_str"]} → {c["competencia_fim_str"]} | {c["situacao"]}')

    ap = dados.get('audit_procuracoes')
    if ap:
        print()
        print('  AUDITORIA PROCURAÇÕES vs HISCON:')
        print(f'    casados exato: {len(ap["casados_exato"])}')
        print(f'    casados fuzzy: {len(ap["casados_fuzzy"])}')
        print(f'    suspeitos:     {len(ap["suspeitos"])}')
        print(f'    informativos:  {len(ap["informativos"])}')

    print()
    print('  ALERTAS GLOBAIS:')
    for a in (dados['alertas_seletor'] or []):
        print(f'    [seletor] {a[:240]}')
    if ap:
        for a in ap['alertas']:
            print(f'    [audit]   {a[:240]}')

    if dados.get('divergencias_pessoais'):
        print()
        print('  DIVERGÊNCIAS doc vs HISCRE:')
        for d in dados['divergencias_pessoais']:
            print(f'    [{d["severidade"]}] {d["campo"]}: {d["msg"]}')

    # === GERAR ===
    print()
    print('  GERANDO INICIAL...')
    r = gerar_inicial(dados, DOCX_OUT)
    print(f'    ✓ DOCX: {DOCX_OUT}')
    print(f'      modificações: {r["modificados"]}, residuais: {r["residuais"] or "nenhum"}')

    print()
    print('  GERANDO RELATÓRIO PARALELO...')
    gerar_relatorio_paralelo(dados, RELAT_OUT)
    print(f'    ✓ RELATÓRIO: {RELAT_OUT}')


if __name__ == '__main__':
    main()
