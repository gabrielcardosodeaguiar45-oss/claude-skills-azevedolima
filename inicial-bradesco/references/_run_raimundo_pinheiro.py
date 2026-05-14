"""Gera 4 iniciais PG ELETRON do RAIMUNDO NONATO PINHEIRO SAMPAIO.

Comarca: Manaus/AM (foro do domicílio, art. 101 I CDC).
Autor IDOSO (nascido 27/12/1964 → 61 anos em 06/05/2026 — prioridade
art. 1.048 I CPC). Conta Bradesco Ag 3726, conta 43422-1.
Renda: INSS R$ 1.812,93 (último crédito 07/10/2025).

4 teses PG ELETRON, 1 inicial por terceiro:
1. BINCLUB SERVIÇOS DE ADMINISTRAÇÃO E DE PROGRAMAS DE FIDELIDADE LTDA
   (CNPJ 38.056.833/0001-47, São Paulo/SP): 18 lançamentos
   08/05/2023–07/06/2024, R$ 1.371,92.
2. PAULISTA SERVIÇOS DE RECEBIMENTOS E PAGAMENTOS LTDA
   (CNPJ 15.245.499/0001-74, São Paulo/SP): 13 lançamentos
   07/07/2023–05/07/2024, R$ 1.065,70.
3. BRADESCO VIDA E PREVIDÊNCIA S.A. (CNPJ 51.990.695/0001-37,
   São Paulo/SP): 70 lançamentos 06/01/2020–06/10/2025, R$ 2.651,34.
   ALERTA PRESCRIÇÃO: lançamentos < 06/05/2021 prescritos pelo CDC art. 27
   (5 anos); todos vivos pelo CC art. 205 (10 anos). Estratégia decenal.
4. ZURICH MINAS BRASIL SEGUROS S.A. (CNPJ 17.197.385/0001-21,
   Belo Horizonte/MG): 34 lançamentos 12/05/2020–13/02/2023, R$ 776,44.
   ALERTA PRESCRIÇÃO: idem item 3.

INVERSÃO DAS NOTIFICAÇÕES: as notificações de Vida e Prev e Paulista
foram trocadas pelo escritório (terceiro + rubrica). Os DADOS objetivos
(período, lançamentos, total) batem com cada tabela, mas a notificação
na pasta Vida e Prev menciona PSERV e vice-versa. Pendência sinalizada.

ESTADO CIVIL: notificação tem literal "[ESTADO CIVIL]" não preenchido.
RG: doc origem livro B-5 (livro B = certidão de casamento), sugere autor
CASADO. Pendência sinalizada — confirmar antes do protocolo.
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import gerar_inicial_pg_eletron, montar_dados_padrao

ROOT = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - BRADESCO\0. TESTE 1\RAIMUNDO NONATO PINHEIRO SAMPAIO - Maria Seixas'
BASE_BINCLUB    = os.path.join(ROOT, 'Bradesco e Binclub')
BASE_PSERV      = os.path.join(ROOT, 'Bradesco e Paulista Serviços')
BASE_VIDAPREV   = os.path.join(ROOT, 'Bradesco e Vida e Previdência')
BASE_ZURICH     = os.path.join(ROOT, 'Bradesco e Zurich Seguros')

autora = {
    'nome': 'RAIMUNDO NONATO PINHEIRO SAMPAIO',
    'nacionalidade': 'brasileiro',
    'estado_civil': '',  # placeholder não preenchido na notificação; provável CASADO via RG livro B-5
    'profissao': 'aposentado',
    'cpf': '000.000.030-40',
    'rg': '1000028-8',
    'orgao_expedidor_prefixo': 'SSP/AM',
    'logradouro': 'Rua Beco do Igarapé II',
    'numero': '121',
    'bairro': 'Compensa',
    'cidade': 'Manaus',
    'cep': '69.035-001',
}
conta = {'agencia': '3726', 'numero': '43422-1'}
renda = {'valor_float': 1812.93}

# Pendências comuns que aparecem em todas as 4 iniciais
PEND_COMUNS = [
    ('ESTADO CIVIL — placeholder não preenchido + provável casamento',
     'A notificação extrajudicial qualifica o autor como "brasileiro, '
     '[ESTADO CIVIL], aposentado" — o placeholder não foi preenchido pelo '
     'escritório. O RG (2ª via, expedida em 29/10/2003) foi emitido com '
     'documento de origem "CERT.CAS.N.1.134 FLS.127 LV.B-5 CART.6 OF. '
     'MANAUS-AM" — livro B = certidão de CASAMENTO. Sugere fortemente que '
     'o autor era CASADO em 29/10/2003. Confirmar com cliente o estado '
     'civil ATUAL antes do protocolo (casado, viúvo, divorciado, separado) '
     'e ajustar manualmente a inicial. Esta inicial omite o placeholder '
     'limpamente — preencher manualmente após confirmação.'),
    ('IDADE / IDOSO — prioridade processual aplicada',
     'Autor nascido em 27/12/1964 → 61 anos completos em 06/05/2026. Aplica '
     'prioridade processual de idoso (art. 1.048 I CPC). Cabeçalho e '
     'pedido preliminar já incluem o pleito.'),
    ('COMPETÊNCIA — Manaus/AM',
     'Comarca de MANAUS/AM (foro do domicílio do consumidor, art. 101 I CDC). '
     'NÃO é Maués nem comarca delegada de Caapiranga. Em Manaus há varas '
     'cíveis especializadas e juizados especiais civis. Avaliar valor da '
     'causa para definir rito (JEC se ≤ 40 SM ≈ R$ 60.720, ou rito comum). '
     'Distribuição em Manaus segue regime de varas múltiplas.'),
    ('NOTIFICAÇÕES — INVERSÃO ENTRE VIDA E PREV E PSERV',
     'A notificação na pasta "Bradesco e Vida e Previdência" (8 - '
     'NOTIFICAÇÃO.pdf) menciona como terceiro o PSERV (PAULISTA SERVIÇOS) '
     'com período/total/lançamentos da tese PSERV. A notificação na pasta '
     '"Bradesco e Paulista Serviços" menciona BRADESCO VIDA E PREVIDÊNCIA '
     'com período/total/lançamentos da tese Vida e Prev. Os dois '
     'documentos foram trocados pelo escritório. As iniciais geradas usam '
     'os DADOS CORRETOS por tese (que coincidem com cada tabela na pasta '
     'respectiva), mas se a notificação for juntada como anexo precisa '
     'ser CORRIGIDA antes do protocolo (gerar 2 novas notificações com '
     'os terceiros corretos, ou usar apenas as outras 2 notificações '
     'íntegras — Binclub e Zurich).'),
]

# ===================== INICIAL 1: BINCLUB =====================
LANC_BINCLUB = [
    ('08/05/2023', 62.90), ('07/06/2023', 62.90), ('07/07/2023', 62.90),
    ('07/08/2023', 62.90), ('11/09/2023', 62.90), ('06/10/2023', 62.90),
    ('08/11/2023', 74.90), ('07/12/2023', 84.90),
    ('08/01/2024', 84.90), ('07/02/2024', 89.99), ('07/03/2024', 89.99),
    ('13/03/2024', 29.90), ('20/03/2024', 89.99), ('01/04/2024', 89.99),
    ('10/04/2024', 89.99), ('23/04/2024', 89.99), ('08/05/2024', 89.99),
    ('07/06/2024', 89.99),
]
tese_binclub = {
    'rubrica': 'PAGTO ELETRON COBRANCA BINCLUB SERVICOS DE ADMINISTRACAO',
    'lancamentos': LANC_BINCLUB,
}
terceiro_binclub = {
    'nome': 'BINCLUB SERVIÇOS DE ADMINISTRAÇÃO E DE PROGRAMAS DE FIDELIDADE LTDA',
    'cnpj': '38.056.833/0001-47',
    'logradouro': 'Avenida Nove de Julho',
    'numero': '3.228, Sala 404-A',
    'bairro': 'Jardim Paulista',
    'cidade': 'São Paulo',
    'uf': 'SP',
    'cep': '01.406-000',
}
dados, totais = montar_dados_padrao(
    autora, conta, renda, tese_binclub, terceiro_binclub,
    eh_idoso=True, competência='Manaus', uf='AM',
)
print('--- BINCLUB ---')
print('Total simples:', totais['total'], 'Dobro:', totais['dobro'], 'VC:', totais['valor_causa'])
docx, rel, alertas = gerar_inicial_pg_eletron(
    pasta_destino=BASE_BINCLUB,
    nome_arquivo_base='INICIAL_PgEletron_BINCLUB_RAIMUNDO_PINHEIRO',
    terceiro_slug='BINCLUB',
    dados=dados, estado_civil_omitido=True, renda_alerta=False, cobranca_anual=False,
    pendencias_extras=PEND_COMUNS + [
        ('PRESCRIÇÃO — NÃO se aplica',
         'Lançamentos entre 08/05/2023 e 07/06/2024. Pelo art. 27 CDC (5 '
         'anos), termo final do primeiro lançamento será em 08/05/2028. '
         'Pelo art. 205 CC (10 anos), 08/05/2033. Em 06/05/2026 nenhum '
         'lançamento está prescrito. Tese livre de problema prescricional.'),
        ('LANÇAMENTOS COM VALORES VARIÁVEIS',
         'Os 18 lançamentos têm valores entre R$ 29,90 e R$ 89,99, com '
         'reajustes ao longo dos meses (62,90 → 74,90 → 84,90 → 89,99) e '
         'um lançamento extra de R$ 29,90 em 13/03/2024. O banco pode '
         'argumentar que se trata de plano de fidelidade com mensalidade '
         'crescente em razão de adesão a benefícios premium. Reforçar '
         'que o autor JAMAIS aderiu a programa "Binclub" e jamais '
         'recebeu carteirinha, comunicação ou benefício.'),
    ],
)
print('OK ->', docx)
print()

# ===================== INICIAL 2: PSERV =====================
LANC_PSERV = [
    ('07/07/2023', 76.90), ('07/08/2023', 76.90), ('08/09/2023', 76.90),
    ('06/10/2023', 76.90), ('08/11/2023', 76.90), ('07/12/2023', 76.90),
    ('08/01/2024', 76.90), ('07/02/2024', 86.90), ('07/03/2024', 86.90),
    ('05/04/2024', 86.90), ('08/05/2024', 86.90), ('07/06/2024', 89.90),
    ('05/07/2024', 89.90),
]
tese_pserv = {
    'rubrica': 'PAGTO ELETRON COBRANCA PAULISTA SERVIÇOS (PSERV)',
    'lancamentos': LANC_PSERV,
}
terceiro_pserv = {
    'nome': 'PAULISTA SERVIÇOS DE RECEBIMENTOS E PAGAMENTOS LTDA',
    'cnpj': '15.245.499/0001-74',
    'logradouro': 'Avenida Brigadeiro Faria Lima',
    'numero': '1.355, Andar 1',
    'bairro': 'Jardim Paulistano',
    'cidade': 'São Paulo',
    'uf': 'SP',
    'cep': '01.452-919',
}
dados2, totais2 = montar_dados_padrao(
    autora, conta, renda, tese_pserv, terceiro_pserv,
    eh_idoso=True, competência='Manaus', uf='AM',
)
print('--- PSERV ---')
print('Total simples:', totais2['total'], 'Dobro:', totais2['dobro'], 'VC:', totais2['valor_causa'])
docx2, rel2, alertas2 = gerar_inicial_pg_eletron(
    pasta_destino=BASE_PSERV,
    nome_arquivo_base='INICIAL_PgEletron_PSERV_RAIMUNDO_PINHEIRO',
    terceiro_slug='PSERV',
    dados=dados2, estado_civil_omitido=True, renda_alerta=False, cobranca_anual=False,
    pendencias_extras=PEND_COMUNS + [
        ('PRESCRIÇÃO — NÃO se aplica',
         'Lançamentos entre 07/07/2023 e 05/07/2024. Termo final pelo CDC '
         '(5 anos): 07/07/2028. Em 06/05/2026 nenhum lançamento está '
         'prescrito.'),
        ('VARIAÇÃO DE NOMENCLATURA NA RUBRICA',
         'A tabela 7 - TABELA PSERV.pdf mostra duas variações na '
         'nomenclatura: "PAGTO ELETRON COBRANCA PAULISTA SERVIÇOS (PSERV)" '
         '(9 lançamentos a partir de 08/11/2023) e "PAGTO ELETRON '
         'COBRANCA PSERV (PAULISTA SERVIÇOS)" (4 lançamentos de 07/07 a '
         '06/10/2023). Trata-se da MESMA empresa terceira (Paulista '
         'Serviços de Recebimentos e Pagamentos LTDA). A inicial usa a '
         'forma mais consolidada como rubrica principal e menciona a '
         'variação no relatório fático, sem prejudicar a tese.'),
    ],
)
print('OK ->', docx2)
print()

# ===================== INICIAL 3: VIDA E PREV =====================
LANC_VIDA_PREV = [
    ('06/01/2020', 24.42), ('05/02/2020', 24.42), ('05/03/2020', 24.42),
    ('06/04/2020', 24.42), ('05/05/2020', 24.42), ('05/06/2020', 24.42),
    ('06/07/2020', 24.42), ('05/08/2020', 26.21), ('08/09/2020', 26.21),
    ('05/10/2020', 26.21), ('05/11/2020', 26.21), ('07/12/2020', 26.21),
    ('05/01/2021', 26.21), ('05/02/2021', 26.21), ('05/03/2021', 26.21),
    ('05/04/2021', 26.21), ('05/05/2021', 26.21), ('17/06/2021', 26.21),
    ('05/07/2021', 26.21), ('05/08/2021', 35.58), ('06/09/2021', 35.58),
    ('05/10/2021', 35.58), ('05/11/2021', 35.58), ('06/12/2021', 35.58),
    ('05/01/2022', 35.58), ('07/02/2022', 35.58), ('07/03/2022', 35.58),
    ('05/04/2022', 35.58), ('05/05/2022', 35.58), ('06/06/2022', 35.58),
    ('05/07/2022', 35.58), ('05/08/2022', 39.39), ('06/09/2022', 39.39),
    ('05/10/2022', 39.39), ('07/11/2022', 39.39), ('05/12/2022', 39.39),
    ('05/01/2023', 39.39), ('06/02/2023', 39.39), ('06/03/2023', 39.39),
    ('05/04/2023', 39.39), ('05/05/2023', 39.39), ('05/06/2023', 39.39),
    ('05/07/2023', 39.39), ('07/08/2023', 36.69), ('06/09/2023', 36.69),
    ('10/10/2023', 36.69), ('06/11/2023', 36.69), ('05/12/2023', 36.69),
    ('05/01/2024', 36.69), ('05/02/2024', 36.69), ('05/03/2024', 36.69),
    ('05/04/2024', 36.69), ('06/05/2024', 36.69), ('05/06/2024', 36.69),
    ('12/07/2024', 36.69), ('05/08/2024', 37.58), ('06/09/2024', 37.58),
    ('07/10/2024', 37.58), ('05/11/2024', 58.79), ('05/12/2024', 58.79),
    ('06/01/2025', 58.79), ('05/02/2025', 58.79), ('05/03/2025', 58.79),
    ('05/04/2025', 58.79), ('05/05/2025', 58.79), ('05/06/2025', 58.79),
    ('07/07/2025', 58.79), ('05/08/2025', 61.37), ('08/09/2025', 61.37),
    ('06/10/2025', 61.37),
]
tese_vidaprev = {
    'rubrica': 'PAGTO ELETRON COBRANCA BRADESCO VIDA E PREVIDENCIA',
    'lancamentos': LANC_VIDA_PREV,
}
terceiro_vidaprev = {
    'nome': 'BRADESCO VIDA E PREVIDÊNCIA S.A.',
    'cnpj': '51.990.695/0001-37',
    'logradouro': 'Avenida Paulista',
    'numero': '1.450',
    'bairro': 'Bela Vista',
    'cidade': 'São Paulo',
    'uf': 'SP',
    'cep': '01.310-917',
}
dados3, totais3 = montar_dados_padrao(
    autora, conta, renda, tese_vidaprev, terceiro_vidaprev,
    eh_idoso=True, competência='Manaus', uf='AM',
)
print('--- VIDA E PREV ---')
print('Total simples:', totais3['total'], 'Dobro:', totais3['dobro'], 'VC:', totais3['valor_causa'])
print('Lançamentos:', len(LANC_VIDA_PREV))
docx3, rel3, alertas3 = gerar_inicial_pg_eletron(
    pasta_destino=BASE_VIDAPREV,
    nome_arquivo_base='INICIAL_PgEletron_VIDAPREV_RAIMUNDO_PINHEIRO',
    terceiro_slug='VIDAPREV',
    dados=dados3, estado_civil_omitido=True, renda_alerta=False, cobranca_anual=False,
    pendencias_extras=PEND_COMUNS + [
        ('PRESCRIÇÃO — RISCO PARCIAL (CDC) / TODOS VIVOS PELO DECENAL',
         'Lançamentos entre 06/01/2020 e 06/10/2025. Pelo art. 27 CDC (5 '
         'anos, corrente majoritária STJ Tema 1061 + EAREsp 1.280.825/RS) '
         'os lançamentos anteriores a 06/05/2021 estão PRESCRITOS — '
         'aproximadamente os 16 primeiros (06/01/2020 a 05/04/2021). Pelo '
         'art. 205 CC (10 anos, corrente minoritária acolhida em algumas '
         'câmaras do TJ-AM) TODOS os 70 lançamentos estão vivos. ESTRATÉGIA '
         'ADOTADA: ajuizar com fundamento na corrente decenal + actio nata '
         'diferida, pleiteando a totalidade dos R$ 2.651,34 (dobro R$ '
         '5.302,68). Se o juízo aplicar a tese quinquenal, perde-se '
         'aproximadamente R$ 416,55 (16 × R$ 26 médios) e remanesce o '
         'valor restante. Preparar recurso de apelação ou inominado para '
         'Turma Recursal caso a sentença reconheça prescrição quinquenal. '
         'Notificação extrajudicial (14/04/2026) NÃO interrompe prescrição '
         '(CC 202).'),
        ('VARIAÇÃO PROGRESSIVA DOS VALORES MENSAIS',
         'Os 70 lançamentos têm 5 patamares de valor (R$ 24,42 → 26,21 → '
         '35,58 → 39,39 → 36,69 → 37,58 → 58,79 → 61,37), com reajustes '
         'periódicos. Padrão típico de produto previdenciário com '
         'reajuste anual por idade ou por correção monetária. O banco '
         'pode alegar que os reajustes refletem cláusula contratual de '
         'apólice ativa. Reforçar que JAMAIS o autor aderiu, JAMAIS '
         'recebeu apólice ou comunicação de reajuste.'),
        ('COBRANÇA EM ANDAMENTO — ÚLTIMO LANÇAMENTO 06/10/2025',
         'A cobrança ainda está ATIVA (último lançamento 06/10/2025, valor '
         'R$ 61,37). Pedido de cessação imediata (item I) tem força '
         'plena. Tutela de urgência pode ser cogitada para suspensão '
         'imediata dos descontos.'),
    ],
)
print('OK ->', docx3)
print()

# ===================== INICIAL 4: ZURICH =====================
LANC_ZURICH = [
    ('12/05/2020', 19.60), ('12/06/2020', 19.60), ('13/07/2020', 19.60),
    ('12/08/2020', 19.60), ('14/09/2020', 19.60), ('13/10/2020', 19.60),
    ('12/11/2020', 19.60), ('14/12/2020', 19.60), ('12/01/2021', 19.60),
    ('12/02/2021', 19.60), ('12/03/2021', 22.06), ('12/04/2021', 22.06),
    ('12/05/2021', 22.06), ('14/06/2021', 22.06), ('12/07/2021', 22.06),
    ('12/08/2021', 22.06), ('13/09/2021', 22.06), ('13/10/2021', 22.06),
    ('12/11/2021', 22.06), ('13/12/2021', 22.06), ('12/01/2022', 22.06),
    ('14/02/2022', 22.06), ('14/03/2022', 26.31), ('12/04/2022', 26.31),
    ('12/05/2022', 26.31), ('13/06/2022', 26.31), ('12/07/2022', 26.31),
    ('12/08/2022', 26.31), ('12/09/2022', 26.31), ('13/10/2022', 26.31),
    ('14/11/2022', 26.31), ('12/12/2022', 26.31), ('12/01/2023', 26.31),
    ('13/02/2023', 26.31),
]
tese_zurich = {
    'rubrica': 'PAGTO ELETRON COBRANCA ZURICH SEGUROS',
    'lancamentos': LANC_ZURICH,
}
terceiro_zurich = {
    'nome': 'ZURICH MINAS BRASIL SEGUROS S.A.',
    'cnpj': '17.197.385/0001-21',
    'logradouro': 'Avenida Getúlio Vargas',
    'numero': '1.420, andares 5 e 6',
    'bairro': 'Funcionários',
    'cidade': 'Belo Horizonte',
    'uf': 'MG',
    'cep': '30.112-020',
}
dados4, totais4 = montar_dados_padrao(
    autora, conta, renda, tese_zurich, terceiro_zurich,
    eh_idoso=True, competência='Manaus', uf='AM',
)
print('--- ZURICH ---')
print('Total simples:', totais4['total'], 'Dobro:', totais4['dobro'], 'VC:', totais4['valor_causa'])
docx4, rel4, alertas4 = gerar_inicial_pg_eletron(
    pasta_destino=BASE_ZURICH,
    nome_arquivo_base='INICIAL_PgEletron_ZURICH_RAIMUNDO_PINHEIRO',
    terceiro_slug='ZURICH',
    dados=dados4, estado_civil_omitido=True, renda_alerta=False, cobranca_anual=False,
    pendencias_extras=PEND_COMUNS + [
        ('PRESCRIÇÃO — RISCO ALTO PELA TESE QUINQUENAL',
         'Lançamentos entre 12/05/2020 e 13/02/2023. Pelo art. 27 CDC '
         '(5 anos): lançamentos anteriores a 06/05/2021 estão PRESCRITOS '
         '(aproximadamente os 12 primeiros, 12/05/2020 a 12/04/2021). Os '
         'demais 22 lançamentos estão vivos. Pelo art. 205 CC (10 anos): '
         'TODOS os 34 lançamentos vivos (último termo 13/02/2033). '
         'ESTRATÉGIA: ajuizar com fundamento decenal + actio nata diferida. '
         'Perda potencial pelo CDC: ~R$ 235,20 (12 × R$ 19,60); remanesce '
         'R$ 541,24. Preparar recurso preventivamente.'),
        ('CESSAÇÃO ESPONTÂNEA EM 13/02/2023',
         'A cobrança parou em 13/02/2023 e não se repetiu até hoje '
         '(extrato 2023–2025 conferido). Padrão típico de seguro com '
         'apólice anual cancelada após não-renovação. Pedido de cessação '
         'definitiva (item I) tem força limitada porque a cobrança já '
         'cessou — pode ser reformulado para "obrigação de não cobrar '
         'novamente" ou suprimido. Avaliar.'),
        ('VALOR BAIXO — RISCO PROCESSUAL NULO',
         'Total simples R$ 776,44, dobro R$ 1.552,88. Dano moral 15.000. '
         'VC R$ 16.552,88. Mesmo com perda parcial pelo quinquenal, o '
         'valor remanescente é viável.'),
    ],
)
print('OK ->', docx4)
print()

# limpar tmp se existir
import shutil
for p in (BASE_BINCLUB, BASE_PSERV, BASE_VIDAPREV, BASE_ZURICH):
    tmp = os.path.join(p, '_tmp_pages')
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
        print('limpo:', tmp)

print('TODAS AS 4 INICIAIS GERADAS')
