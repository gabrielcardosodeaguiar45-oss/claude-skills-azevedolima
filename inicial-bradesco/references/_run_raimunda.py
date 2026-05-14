"""Gera a inicial PG ELETRON SUDAMERICA CLUBE de RAIMUNDA DE ALMEIDA DA SILVA.

Comarca: Codajás/AM (NÃO Maués). IDOSA (nascida 15/08/1953 → 72 anos
em 06/05/2026 — prioridade art. 1.048 I CPC).
Conta: Bradesco Ag 3716, conta 601419-4.
Renda: INSS líquido R$ 853,37 (último crédito 06/11/2025; em 2024 era
R$ 906,89; histórico 2018 R$ 617,66). Padrão de aposentada do INSS com
benefício recebido por crédito direto na conta. ALERTAR: renda BRUTA
provavelmente maior, conforme regra § "INSS líquido vs renda bruta".

Tese: 27 lançamentos mensais SUDAMERICA CLUBE entre 02/01/2020 e
01/03/2024. Total simples R$ 649,39 / dobro R$ 1.298,78 / dano moral
R$ 15.000,00 / VC R$ 16.298,78. PORTO SEGURO (2 lançamentos de 2018
totalizando R$ 31,14) está em pasta separada e provavelmente prescrito
(art. 27 CDC, prazo 5 anos contado de 03-04/2018) — tratado em outra
inicial específica.
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import gerar_inicial_pg_eletron, montar_dados_padrao

BASE = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - BRADESCO\0. TESTE 1\RAIMUNDA DE ALMEIDA DA SILVA - Maria Seixas\PGTO ELETRÔNICO\SUDAMERICA'

autora = {
    'nome': 'RAIMUNDA DE ALMEIDA DA SILVA',
    'nacionalidade': 'brasileira',
    'estado_civil': 'solteira',
    'profissao': 'aposentada',
    'cpf': '000.000.026-36',
    'rg': '1000024-4',
    'orgao_expedidor_prefixo': 'SSP/AM',
    'logradouro': 'Rua Plinio Coelho',
    'numero': 's/n',
    'bairro': 'Centro',
    'cidade': 'Codajás',
    'cep': '69.450-000',
}
conta = {'agencia': '3716', 'numero': '601419-4'}
renda = {'valor_float': 853.37}

tese = {
    'rubrica': 'PAGTO ELETRON COBRANCA SUDAMERICA CLUBE DE SERVICOS',
    'lancamentos': [
        ('02/01/2020', 19.56), ('03/02/2020', 19.56), ('02/03/2020', 19.56),
        ('01/04/2020', 19.56),
        ('04/05/2020', 21.52), ('01/06/2020', 21.52), ('01/07/2020', 21.52),
        ('03/08/2020', 21.52), ('01/09/2020', 21.52), ('01/10/2020', 21.52),
        ('01/12/2020', 21.52), ('04/01/2021', 21.52),
        ('03/01/2022', 23.67),
        ('02/01/2023', 26.03), ('01/02/2023', 26.03), ('01/03/2023', 26.03),
        ('03/04/2023', 26.03),
        ('02/05/2023', 27.12), ('01/06/2023', 27.12), ('03/07/2023', 27.12),
        ('01/08/2023', 27.12), ('01/09/2023', 27.12), ('02/10/2023', 27.12),
        ('01/11/2023', 27.12), ('01/12/2023', 27.12), ('02/01/2024', 27.12),
        ('01/03/2024', 27.12),
    ],
}
terceiro = {
    'nome': 'SUDAMERICA CLUBE DE SERVIÇOS',
    'cnpj': '81.222.267/0001-25',
    'logradouro': 'Rua Inácio Lustosa',
    'numero': '761',
    'bairro': 'São Francisco',
    'cidade': 'Curitiba',
    'uf': 'PR',
    'cep': '80.510-000',
}

dados, totais = montar_dados_padrao(autora, conta, renda, tese, terceiro, eh_idoso=True)
print('Total simples:', totais['total'])
print('Dobro:', totais['dobro'])
print('Dano moral:', totais['dano_moral'])
print('Valor causa:', totais['valor_causa'])
print('Datas:', totais['datas'])

docx, rel, alertas = gerar_inicial_pg_eletron(
    pasta_destino=BASE,
    nome_arquivo_base='INICIAL_PgEletron_SUDAMERICA_RAIMUNDA',
    terceiro_slug='SUDAMERICA',
    dados=dados,
    estado_civil_omitido=False,
    renda_alerta=True,         # INSS líquido vs renda bruta
    cobranca_anual=False,
    pendencias_extras=[
        ('PORTO SEGURO — TESE PRESCRITA',
         'A pasta PGTO ELETRÔNICO/PORTO SEGURO contém 2 lançamentos de 2018 '
         '(03/04/2018 R$ 15,25 e 18/05/2018 R$ 15,89, total R$ 31,14). Como a '
         'data atual é 06/05/2026, AMBOS já passaram do prazo prescricional '
         'de 5 anos (art. 27 CDC). Recomenda-se NÃO ajuizar a tese de PORTO '
         'SEGURO (prescrita). Esta inicial cobre APENAS SUDAMERICA CLUBE '
         '(lançamentos 2020-2024, todos dentro do prazo).'),
        ('RENDA — INSS LÍQUIDO',
         'Renda adotada R$ 853,37 corresponde ao último crédito INSS no '
         'extrato (06/11/2025), recebido APÓS consignações descontadas pelo '
         'próprio INSS na fonte. A renda BRUTA do benefício previdenciário '
         'da autora é maior. Conferir HISCON antes do protocolo para informar '
         'o salário-de-benefício BRUTO no parágrafo da Justiça Gratuita, se '
         'mais favorável à hipossuficiência.'),
        ('COMPETÊNCIA',
         'Comarca de CODAJÁS/AM (foro do domicílio do consumidor, art. 101, I, '
         'CDC). NÃO é Maués nem o foro de eleição de Bradesco/Sudamerica. '
         'Conferir distribuição na Comarca de Codajás.'),
        ('TABELA MISTA — PORTO SEGURO + SUDAMERICA',
         'A tabela 7 - TABELA.pdf da pasta SUDAMERICA traz os 2 lançamentos '
         'de PORTO SEGURO de 2018 + os 27 de SUDAMERICA. Ao calcular esta '
         'inicial, foram considerados APENAS os 27 lançamentos SUDAMERICA. '
         'TOTAL da tabela impressa (R$ 680,53) inclui PORTO SEGURO; o total '
         'real só de SUDAMERICA é R$ 649,39 (verificado item a item).'),
    ],
)
print('RAIMUNDA SUDAMERICA OK ->', docx)
print('  relatorio paralelo ->', rel)
print('  alertas:', alertas['severidade'], 'total=', alertas['total_alertas'])

# limpar tmp
import shutil
tmp = os.path.join(BASE, '_tmp_pages')
if os.path.exists(tmp):
    shutil.rmtree(tmp)
    print('limpo:', tmp)
