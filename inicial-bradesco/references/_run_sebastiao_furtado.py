"""Gera 3 iniciais PG ELETRON do EXEMPLO SEBASTIÃO DA SILVA.

Comarca: Barreirinha/AM (foro do domicílio, art. 101 I CDC).
Autor IDOSO 73 anos (nascido 20/01/1953 → prioridade art. 1.048 I CPC).
Naturalidade Maués/AM. **ANALFABETO/INCAPAZ DE ASSINAR** (RG 2024 traz
literal "NÃO ASSINOU NESSE ATO" — assinatura a rogo confirmada com RG do
rogado + 2 testemunhas Eliçon da Silva Mendes e Wilson Jose Marques da
Silva). Conta Bradesco Ag 3703, conta 33565-7. Renda INSS R$ 846,60
(último crédito direto na conta 30/09/2024; em 2025 INSS vai para outra
conta e ele transfere via TED — provável conta-salário ou Caixa).

3 teses PG ELETRON, 1 inicial por terceiro:
1. ASPECIR UNIÃO SEGURADORA S.A. (CNPJ 95.611.141/0001-57, Porto Alegre/RS):
   5 lançamentos R$ 79,00 entre 02/01/2024 e 28/06/2024. Total real
   R$ 395,00 / dobro R$ 790,00 / VC R$ 15.790,00.
2. EAGLE SOCIDADE [sic] DE CRÉDITO DIRETO S.A. (CNPJ 45.745.141/0001-19,
   Porto Alegre/RS): 6 lançamentos R$ 64,00 entre 28/12/2023 e 28/06/2024.
   Total real R$ 384,00 / dobro R$ 768,00 / VC R$ 15.768,00. ATENÇÃO: SCD
   é instituição financeira — pode estar cobrando parcela de empréstimo;
   confirmar com cliente.
3. VIZAPREV CORRETORA DE SEGUROS DE VIDA LTDA (CNPJ 01.174.455/0001-96,
   Curitiba/PR): 11 lançamentos R$ 64,00 entre 31/05/2023 e 30/09/2024.
   Total real R$ 704,00 / dobro R$ 1.408,00 / VC R$ 16.408,00.

ERRO ESTRUTURAL DAS TABELAS E NOTIFICAÇÕES: As 3 tabelas
(9 - TABELA.pdf) somam a coluna SALDO APÓS em vez do VALOR DÉBITO,
gerando totais inflados (R$ 10.164,74 em vez de R$ 395 para ASPECIR,
R$ 13.792,22 em vez de R$ 384 para EAGLE, R$ 17.483,46 em vez de R$ 704
para VIZA). As 3 notificações extrajudiciais REPETIRAM esse total errado.
ANTES DO PROTOCOLO o escritório precisa REFAZER as 3 notificações com os
totais corretos, OU as iniciais devem trazer ressalva expressa sobre a
discrepância. Esta skill já gerou as iniciais com os VALORES CORRETOS
(do extrato bancário, item por item).
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import gerar_inicial_pg_eletron, montar_dados_padrao

ROOT = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - BRADESCO\0. TESTE 1\EXEMPLO SEBASTIÃO DA SILVA - Canario - OK'
BASE_ASPECIR = os.path.join(ROOT, 'Bradesco e Aspecir')
BASE_EAGLE   = os.path.join(ROOT, 'Bradesco e Eagle')
BASE_VIZA    = os.path.join(ROOT, 'Bradesco e Viza Prevseguros')

autora = {
    'nome': 'EXEMPLO SEBASTIÃO DA SILVA',
    'nacionalidade': 'brasileiro',
    'estado_civil': '',  # não consta na notificação nem no RG novo (CIN); omitir
    'profissao': 'aposentado',  # notificação diz "beneficiário"; INSS confirmado no extrato
    'cpf': '000.000.031-41',
    'rg': '1000029-9',  # CIN unifica RG e CPF
    'orgao_expedidor_prefixo': 'SSP/AM',
    'logradouro': 'Rua Augusto Montenegro',
    'numero': 's/nº',
    'bairro': 'Centro',
    'cidade': 'Barreirinha',
    'cep': '69.160-000',
}
conta = {'agencia': '3703', 'numero': '33565-7'}
renda = {'valor_float': 846.60}  # último INSS direto na conta antes do redirecionamento via TED

# Pendências comuns às 3 iniciais
PEND_COMUNS = [
    ('ASSINATURA A ROGO — AUTOR ANALFABETO/INCAPAZ DE ASSINAR',
     'O RG do autor (CIN expedida em 25/03/2024) traz literalmente '
     '"NÃO ASSINOU NESSE ATO" no campo de assinatura. A procuração foi '
     'firmada por ROGADO a pedido do outorgante, com 2 testemunhas '
     'instrumentárias (Eliçon da Silva Mendes e Wilson Jose Marques da '
     'Silva — RGs anexos). Esta inicial NÃO inclui cláusula expressa de '
     'assinatura a rogo na qualificação da parte autora. **AÇÃO '
     'OBRIGATÓRIA ANTES DO PROTOCOLO**: ajustar manualmente o parágrafo '
     'da qualificação para inserir, após o nome e endereço, fórmula como: '
     '"... pessoa analfabeta, motivo pelo qual a procuração foi assinada '
     'a rogo por [NOME ROGADO], a pedido do Outorgante, na presença das '
     'testemunhas [NOME 1] e [NOME 2], conforme documentos em anexo." '
     'Anexar à inicial os 4 documentos: procuração com firma do rogado + '
     'RG do rogado + RG das 2 testemunhas. Considerar pleitear curador '
     'especial (art. 72 II CPC) se o juízo entender necessária a '
     'representação processual.'),
    ('TABELAS E NOTIFICAÇÕES COM TOTAIS INFLADOS — REFAZER ANTES DO PROTOCOLO',
     'As 3 tabelas anexadas (9-TABELA.pdf) e as 3 notificações '
     'extrajudiciais (8-Notificação.pdf) trazem TOTAL incorreto, somando '
     'a coluna "Saldo Após" em vez da coluna "Valor Débito". Os totais '
     'impressos são: ASPECIR R$ 10.164,74 (real R$ 395,00), EAGLE '
     'R$ 13.792,22 (real R$ 384,00), VIZA R$ 17.483,46 (real R$ 704,00). '
     'Esta inicial usa os VALORES CORRETOS extraídos item a item do '
     'extrato bancário Bradesco. **AÇÃO OBRIGATÓRIA ANTES DO PROTOCOLO**: '
     '(a) refazer as 3 notificações extrajudiciais com totais corretos e '
     'reenviar ao banco/terceiros; (b) regenerar as 3 tabelas '
     '(7-TABELA.pdf) corrigindo a soma; (c) anexar à inicial APENAS as '
     'versões corrigidas. Caso opte por anexar as versões originais, '
     'incluir parágrafo expresso de ressalva na inicial explicando a '
     'discrepância e juntar planilha auxiliar com os cálculos corretos.'),
    ('IDADE / IDOSO — prioridade processual aplicada',
     'Autor nascido em 20/01/1953 → 73 anos completos em 06/05/2026. '
     'Aplica prioridade processual de idoso (art. 1.048 I CPC). '
     'Cabeçalho e pedido preliminar incluem o pleito.'),
    ('COMPETÊNCIA — Barreirinha/AM',
     'Comarca de BARREIRINHA/AM (foro do domicílio do consumidor, '
     'art. 101 I CDC). NÃO é Maués (apesar de a naturalidade do autor '
     'ser Maués). A Comarca de Barreirinha/AM é estadual delegada — '
     'avaliar se há vara única ou JEC instalado.'),
    ('RENDA — INSS REDIRECIONADO PARA OUTRA CONTA EM 2025',
     'Renda adotada R$ 846,60 (último crédito INSS direto no extrato '
     'Bradesco em 30/09/2024). A partir de 31/01/2025, o INSS deixou de '
     'ser creditado diretamente nesta conta — em vez disso, o autor faz '
     'TED de outra conta (provavelmente Caixa, BB ou conta-salário do '
     'INSS) para esta conta Bradesco em valores próximos a R$ 557-566. '
     'A RENDA BRUTA do benefício INSS em 2025/2026 é provavelmente '
     'R$ 1.518,00 (salário-mínimo). CONFERIR HISCON antes do protocolo '
     'para informar o salário-de-benefício BRUTO no parágrafo da '
     'Justiça Gratuita, se mais favorável à hipossuficiência.'),
    ('OUTRAS TESES PRESENTES NO KIT — não processadas neste run',
     'A pasta KIT contém procurações específicas para 4 outras teses '
     'que não foram processadas nesta rodada: (1) MORA CRED PESSOAL + '
     'PARCELA CREDITO PESSOAL Bradesco (skill `inicial-bradesco` cobre); '
     '(2) TARIFA BANCARIA - CESTA B.EXPRESSO4 Bradesco (idem); (3) RCC '
     'BMG contrato 18142727 (skill `replica-rmc` ou inicial específica); '
     '(4) RMC BMG contrato 17383681 (idem). Para as duas primeiras, '
     'rodar a skill `inicial-bradesco` apontando para subpasta do KIT '
     'após a primeira batelada. Para RMC/RCC BMG, fluxo distinto. '
     'O extrato 2020-2021 também mostra recorrência de PAGTO ELETRON '
     'COBRANCA CREFISA CREDITO PESSOAL — possível 5ª tese a investigar.'),
]

# ===================== INICIAL 1: ASPECIR =====================
LANC_ASPECIR = [
    ('02/01/2024', 79.00),
    ('01/02/2024', 79.00),
    ('04/03/2024', 79.00),
    ('02/05/2024', 79.00),
    ('28/06/2024', 79.00),
]
tese_aspecir = {
    'rubrica': 'PAGTO ELETRON COBRANCA ASPECIR - UNIAO SEGURADORA',
    'lancamentos': LANC_ASPECIR,
}
terceiro_aspecir = {
    'nome': 'ASPECIR UNIÃO SEGURADORA S.A.',
    'cnpj': '95.611.141/0001-57',
    'logradouro': 'Praça Otávio Rocha',
    'numero': '65, 1º andar',
    'bairro': 'Centro Histórico',
    'cidade': 'Porto Alegre',
    'uf': 'RS',
    'cep': '90.020-140',
}
dados, totais = montar_dados_padrao(
    autora, conta, renda, tese_aspecir, terceiro_aspecir,
    eh_idoso=True, competência='Barreirinha', uf='AM',
)
print('--- ASPECIR ---')
print('Total simples:', totais['total'], 'Dobro:', totais['dobro'], 'VC:', totais['valor_causa'])
docx, rel, alertas = gerar_inicial_pg_eletron(
    pasta_destino=BASE_ASPECIR,
    nome_arquivo_base='INICIAL_PgEletron_ASPECIR_SEBASTIAO',
    terceiro_slug='ASPECIR',
    dados=dados, estado_civil_omitido=True, renda_alerta=True, cobranca_anual=False,
    pendencias_extras=PEND_COMUNS + [
        ('PRESCRIÇÃO — NÃO se aplica',
         'Lançamentos entre 02/01/2024 e 28/06/2024. Pelo art. 27 CDC '
         '(5 anos), termo final do primeiro lançamento será em '
         '02/01/2029. Em 06/05/2026 nenhum lançamento está prescrito.'),
    ],
)
print('OK ->', docx)
print()

# ===================== INICIAL 2: EAGLE =====================
LANC_EAGLE = [
    ('28/12/2023', 64.00),
    ('31/01/2024', 64.00),
    ('29/02/2024', 64.00),
    ('28/03/2024', 64.00),
    ('30/04/2024', 64.00),
    ('28/06/2024', 64.00),
]
tese_eagle = {
    'rubrica': 'PAGTO ELETRON COBRANCA EAGLE SOCIEDADE DE CREDITO DIRET',
    'lancamentos': LANC_EAGLE,
}
terceiro_eagle = {
    'nome': 'EAGLE SOCIEDADE DE CRÉDITO DIRETO S.A.',
    'cnpj': '45.745.141/0001-19',
    'logradouro': 'Rua Furriel Luiz Antônio de Vargas',
    'numero': '250, 14º andar, Sala 1403',
    'bairro': 'Bela Vista',
    'cidade': 'Porto Alegre',
    'uf': 'RS',
    'cep': '90.470-130',
}
dados2, totais2 = montar_dados_padrao(
    autora, conta, renda, tese_eagle, terceiro_eagle,
    eh_idoso=True, competência='Barreirinha', uf='AM',
)
print('--- EAGLE ---')
print('Total simples:', totais2['total'], 'Dobro:', totais2['dobro'], 'VC:', totais2['valor_causa'])
docx2, rel2, alertas2 = gerar_inicial_pg_eletron(
    pasta_destino=BASE_EAGLE,
    nome_arquivo_base='INICIAL_PgEletron_EAGLE_SEBASTIAO',
    terceiro_slug='EAGLE',
    dados=dados2, estado_civil_omitido=True, renda_alerta=True, cobranca_anual=False,
    pendencias_extras=PEND_COMUNS + [
        ('TERCEIRO É SCD (SOCIEDADE DE CRÉDITO DIRETO) — RISCO ALTO DE TESE FRACA',
         'EAGLE SOCIEDADE DE CRÉDITO DIRETO S.A. é instituição financeira '
         'autorizada pelo BACEN (resolução CMN 4.656/2018) — não é '
         'seguradora, associação ou sindicato como os terceiros típicos '
         'de PG ELETRON. SCDs operam com empréstimos pessoais (crédito '
         'direto sem intermediação bancária) e cobram parcelas via '
         'débito automático autorizado. Há RISCO ALTO de o banco/SCD '
         'apresentar em contestação cópia de cédula de crédito bancário '
         '(CCB) com débito autorizado, demonstrando empréstimo real '
         'contratado pelo autor (ou por terceiro com seus dados, se '
         'houver fraude). **AÇÃO OBRIGATÓRIA ANTES DO PROTOCOLO**: '
         '(a) confirmar com cliente, com firmeza, que JAMAIS contratou '
         'empréstimo com EAGLE SCD; (b) solicitar HISCON do INSS para '
         'verificar se há averbação de empréstimo consignado vinculado a '
         'EAGLE; (c) se o cliente tiver alguma memória de empréstimo '
         'contratado por canal digital ou rural, RECONSIDERAR a tese — '
         'pode ser caso de inicial de empréstimo NÃO CONTRATADO (skill '
         'separada `replica-nao-contratado` para a réplica) em vez de '
         'PG ELETRON pura; (d) avaliar litisconsórcio EAGLE + Bradesco '
         'pode ser fraco se a SCD apresentar CCB com hash, IP, selfie '
         'etc.'),
        ('PRESCRIÇÃO — NÃO se aplica',
         'Lançamentos entre 28/12/2023 e 28/06/2024. Termo final pelo '
         'CDC (5 anos): 28/12/2028. Não prescrito.'),
        ('LANÇAMENTOS PARARAM EM 28/06/2024',
         'A cobrança cessou espontaneamente em 28/06/2024 e não se '
         'repetiu até hoje (extrato 2024-2025 conferido). Pode indicar '
         '6 parcelas de empréstimo total (6 × R$ 64 = R$ 384) já '
         'liquidado. Reforça a hipótese de empréstimo real.'),
    ],
)
print('OK ->', docx2)
print()

# ===================== INICIAL 3: VIZA PREVSEGUROS =====================
LANC_VIZA = [
    ('31/05/2023', 64.00),
    ('31/07/2023', 64.00),
    ('31/10/2023', 64.00),
    ('28/12/2023', 64.00),
    ('31/01/2024', 64.00),
    ('29/02/2024', 64.00),
    ('01/04/2024', 64.00),
    ('30/04/2024', 64.00),
    ('28/06/2024', 64.00),
    ('30/08/2024', 64.00),
    ('30/09/2024', 64.00),
]
tese_viza = {
    'rubrica': 'PAGTO ELETRON COBRANCA VIZAPREVSEGUROS',
    'lancamentos': LANC_VIZA,
}
terceiro_viza = {
    'nome': 'VIZAPREV CORRETORA DE SEGUROS DE VIDA LTDA',
    'cnpj': '01.174.455/0001-96',
    'logradouro': 'Rua José Naves da Cunha',
    'numero': '100',
    'bairro': 'Seminário',
    'cidade': 'Curitiba',
    'uf': 'PR',
    'cep': '80.310-080',
}
dados3, totais3 = montar_dados_padrao(
    autora, conta, renda, tese_viza, terceiro_viza,
    eh_idoso=True, competência='Barreirinha', uf='AM',
)
print('--- VIZA ---')
print('Total simples:', totais3['total'], 'Dobro:', totais3['dobro'], 'VC:', totais3['valor_causa'])
docx3, rel3, alertas3 = gerar_inicial_pg_eletron(
    pasta_destino=BASE_VIZA,
    nome_arquivo_base='INICIAL_PgEletron_VIZA_SEBASTIAO',
    terceiro_slug='VIZA',
    dados=dados3, estado_civil_omitido=True, renda_alerta=True, cobranca_anual=False,
    pendencias_extras=PEND_COMUNS + [
        ('PRESCRIÇÃO — NÃO se aplica',
         'Lançamentos entre 31/05/2023 e 30/09/2024. Termo final pelo '
         'CDC (5 anos): 31/05/2028. Não prescrito.'),
        ('LANÇAMENTOS COM PADRÃO IRREGULAR',
         'Os 11 lançamentos NÃO seguem padrão estritamente mensal: '
         'mai/2023, jul/2023, out/2023, dez/2023, jan/2024, fev/2024, '
         '01-abr e 30-abr/2024 (2 no mesmo mês), jun/2024, ago/2024, '
         'set/2024. Pular meses (jun, ago, set, nov/2023; mar, mai, '
         'jul/2024) sugere que a cobrança era irregular ou que houve '
         'falhas de débito automático em meses sem saldo (a conta tinha '
         'saldo zerado em vários momentos). Também há 2 cobranças no '
         'mesmo mês de abril/2024 (01/04 e 30/04). Padrão de cobrança '
         'sem critério lógico claro REFORÇA a tese de produto não '
         'contratado.'),
        ('CESSAÇÃO ESPONTÂNEA EM 30/09/2024',
         'A última cobrança foi 30/09/2024 e desde então não houve mais '
         'débitos da rubrica. Pedido de cessação tem força limitada '
         '(cobrança já cessou). Pode ser reformulado para "obrigação de '
         'não cobrar novamente" ou suprimido.'),
    ],
)
print('OK ->', docx3)
print()

# limpar tmp se existir
import shutil
for p in (BASE_ASPECIR, BASE_EAGLE, BASE_VIZA):
    tmp = os.path.join(p, '_tmp_pages')
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
        print('limpo:', tmp)

print('TODAS AS 3 INICIAIS GERADAS')
