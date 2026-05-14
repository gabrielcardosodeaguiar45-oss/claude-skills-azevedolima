"""Caso teste 1: EXEMPLO GEORGE DA SILVA SOUZA × BANCO ITAÚ CONSIGNADO + INSS

5 contratos questionados (3 averbação nova + 2 refinanciamento, todos excluídos).
Cenário: MISTO → template MULT + alerta sobre bloco "troco" do REFIN.
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import montar_dados_inicial, gerar_inicial, gerar_relatorio_paralelo

# === DADOS DA AUTORA (extraídos do KIT visualmente — leitura multimodal Claude) ===
AUTORA = {
    'nome': 'EXEMPLO GEORGE DA SILVA SOUZA',
    'nacionalidade': 'brasileiro',
    'estado_civil': 'solteiro',
    'profissao': 'aposentado',
    'cpf': '000.000.010-20',
    'rg': '1000008-8',
    'orgao_expedidor': 'SSP/BA',
    'logradouro': 'Travessa Fernando Tul',  # CONFIRMAR (manuscrito)
    'numero': '54',
    'bairro': 'Santo Pedro',  # CONFIRMAR (manuscrito)
    'cidade': 'Camaçari',
    'uf': 'BA',
    'cep': '42.800-149',
    'renda_liquida': None,  # vai ser preenchida pelo HISCON.base_calculo (R$ 4.579,99)
}

PASTA = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\EXEMPLO GEORGE DA SILVA SOUZA - Marcio Teixeira\BANCO ITAÚ\2 AVERBAÇÃO NOVA INATIVO'

OUTPUT_DIR = PASTA
NOME_DOCX = 'INICIAL_NaoContratado_EXEMPLO GEORGE_ITAU_v1.docx'
NOME_RELATORIO = '_RELATORIO_PENDENCIAS_EXEMPLO GEORGE_ITAU_v1.docx'


def main():
    print(f'=== Processando: {os.path.basename(PASTA)} ===\n')
    dados = montar_dados_inicial(PASTA, AUTORA, subsecao='Salvador', banco_jurisdicao='matriz')

    # Resumo
    print(f'Procurações encontradas: {len(dados["numeros_procuracoes"])}')
    print(f'  → {dados["numeros_procuracoes"]}')
    print(f'Contratos questionados localizados no HISCON: {len(dados["contratos_questionados"])}')
    print(f'Banco-réu: {dados["banco_reu"]["nome"]} (CNPJ {dados["banco_reu"]["cnpj"]})')
    print(f'Template selecionado: {os.path.basename(dados["template"])}')
    print(f'\nDano moral:')
    print(f'  Regra do escritório: R$ {dados["dano_moral"]["total"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
    print(f'  PDF de cálculo:      R$ {dados["calculo"]["dano_moral_pleiteado_pdf"]}')
    print(f'  Auditoria: {"DIVERGÊNCIA" if dados["audit_dm"]["divergencia"] else "OK"}')
    print(f'\nValor da causa: R$ {dados["calculo"]["valor_total_geral"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
    print(f'Idoso: {dados["eh_idoso"]}')

    if dados['alertas_seletor']:
        print(f'\nAlertas do seletor:')
        for a in dados['alertas_seletor']:
            print(f'  ⚠ {a}')

    # Gerar inicial
    output_docx = os.path.join(OUTPUT_DIR, NOME_DOCX)
    print(f'\nGerando inicial: {NOME_DOCX}')
    res = gerar_inicial(dados, output_docx)
    print(f'  Modificações: {res["modificados"]}')
    print(f'  Placeholders residuais: {res["residuais"] or "nenhum"}')

    # Gerar relatório paralelo
    output_relatorio = os.path.join(OUTPUT_DIR, NOME_RELATORIO)
    print(f'\nGerando relatório: {NOME_RELATORIO}')
    gerar_relatorio_paralelo(dados, output_relatorio)
    print(f'  OK')

    print(f'\n✅ Arquivos gerados em: {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
