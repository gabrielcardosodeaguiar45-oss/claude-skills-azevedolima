"""Gera a inicial PG ELETRON BRADESCO VIDA E PREVIDÊNCIA de EXEMPLA RAIMUNDA DA SILVA.

Comarca: Caapiranga/AM (foro do domicílio, art. 101 I CDC). NÃO idosa
(nascida 04/01/1974 → 52 anos em 06/05/2026).
Conta: Bradesco Ag 3707, conta 410430-7.
Renda: INSS R$ 1.518,00 (último crédito 24/09/2025; em 2024 R$ 1.412,00).
Em 2016-2020 a autora recebia DUPLA renda (INSS + CRÉDITO DE SALÁRIO/TRANSF
SALDO C/SAL P/CC da PREFEITURA MUNICIPAL DE CAAPIRANGA — provavelmente
servidora pública municipal aposentada do RPPS em 2020). A partir de 2021
só INSS — ALERTAR no relatório paralelo.

Tese: 56 lançamentos mensais PAGTO ELETRON COBRANCA BRADESCO VIDA E
PREVIDENCIA entre 25/01/2016 e 25/08/2020. Total simples R$ 240,04 / dobro
R$ 480,08 / dano moral R$ 15.000,00 / valor da causa R$ 15.480,08.

ALERTA CRÍTICO DE PRESCRIÇÃO (a ser destacado no relatório paralelo):
- Pelo art. 27 CDC (5 anos) — corrente majoritária STJ, Tema 1061 + EAREsp
  1.280.825/RS — TODOS OS 56 LANÇAMENTOS ESTÃO PRESCRITOS (último em
  25/08/2020 + 5 anos = 25/08/2025; hoje 06/05/2026 já se passaram ~8 meses).
- Pelo art. 205 CC (10 anos) — corrente minoritária — apenas os 4 primeiros
  lançamentos (25/01/2016, 25/02/2016, 28/03/2016, 25/04/2016) estão
  prescritos; os 52 demais (a partir de 25/05/2016) ainda estão vivos.
- Notificação extrajudicial (14/04/2026) NÃO interrompe prescrição (CC 202).
- Decisão do procurador (Ney Pedroza, 06/05/2026): ajuizar com fundamento
  na corrente decenal (algumas câmaras do TJ-AM acolhem), assumindo o risco
  de prescrição quinquenal em 1ª instância e levando a tese para Turma
  Recursal/2ª instância se necessário.
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import gerar_inicial_pg_eletron, montar_dados_padrao

BASE = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - BRADESCO\0. TESTE 1\EXEMPLA RAIMUNDA DA SILVA - Ney Pedroza'

autora = {
    'nome': 'EXEMPLA RAIMUNDA DA SILVA',
    'nacionalidade': 'brasileira',
    'estado_civil': '',  # não consta em nenhum documento — omitir limpamente
    'profissao': 'aposentada',
    'cpf': '000.000.028-38',
    'rg': '1000026-6',
    'orgao_expedidor_prefixo': 'SSP/AM',
    'logradouro': 'Rua Lázaro Andrade',
    'numero': '130',
    'bairro': 'Santo Antônio',
    'cidade': 'Caapiranga',
    'cep': '69.425-000',
}
conta = {'agencia': '3707', 'numero': '410430-7'}
renda = {'valor_float': 1518.00}

LANCAMENTOS = [
    ('25/01/2016', 3.74), ('25/02/2016', 3.74), ('28/03/2016', 3.74),
    ('25/04/2016', 3.74), ('25/05/2016', 3.74), ('27/06/2016', 3.74),
    ('25/07/2016', 3.74), ('25/08/2016', 3.74),
    ('26/09/2016', 4.19), ('25/10/2016', 4.19), ('25/11/2016', 4.19),
    ('26/12/2016', 4.19), ('25/01/2017', 4.19), ('01/03/2017', 4.19),
    ('27/03/2017', 4.19), ('25/04/2017', 4.19), ('25/05/2017', 4.19),
    ('26/06/2017', 4.19), ('25/07/2017', 4.19), ('25/08/2017', 4.19),
    ('25/09/2017', 4.12), ('25/10/2017', 4.12), ('27/11/2017', 4.12),
    ('26/12/2017', 4.12), ('25/01/2018', 4.12), ('26/02/2018', 4.12),
    ('26/03/2018', 4.12), ('25/04/2018', 4.12), ('25/05/2018', 4.12),
    ('25/06/2018', 4.12), ('25/07/2018', 4.12), ('27/08/2018', 4.12),
    ('25/09/2018', 4.46), ('25/10/2018', 4.46), ('26/11/2018', 4.46),
    ('26/12/2018', 4.46), ('25/01/2019', 4.46), ('25/02/2019', 4.46),
    ('25/03/2019', 4.46), ('25/04/2019', 4.46), ('27/05/2019', 4.46),
    ('25/06/2019', 4.46), ('25/07/2019', 4.46), ('28/08/2019', 4.46),
    ('25/09/2019', 4.74), ('25/10/2019', 4.74), ('25/11/2019', 4.74),
    ('26/12/2019', 4.74), ('27/01/2020', 4.74), ('26/02/2020', 4.74),
    ('25/03/2020', 4.74), ('27/04/2020', 4.74), ('25/05/2020', 4.74),
    ('25/06/2020', 4.74), ('27/07/2020', 4.74), ('25/08/2020', 4.74),
]

tese = {
    'rubrica': 'PAGTO ELETRON COBRANCA BRADESCO VIDA E PREVIDENCIA',
    'lancamentos': LANCAMENTOS,
}
terceiro = {
    'nome': 'BRADESCO VIDA E PREVIDÊNCIA S.A.',
    'cnpj': '51.990.695/0001-37',
    'logradouro': 'Avenida Paulista',
    'numero': '1.450',
    'bairro': 'Bela Vista',
    'cidade': 'São Paulo',
    'uf': 'SP',
    'cep': '01.310-917',
}

dados, totais = montar_dados_padrao(
    autora, conta, renda, tese, terceiro,
    eh_idoso=False,
    competência='Caapiranga',
    uf='AM',
)
print('Total simples:', totais['total'])
print('Dobro:', totais['dobro'])
print('Dano moral:', totais['dano_moral'])
print('Valor causa:', totais['valor_causa'])
print('Datas:', totais['datas'])

docx, rel, alertas = gerar_inicial_pg_eletron(
    pasta_destino=BASE,
    nome_arquivo_base='INICIAL_PgEletron_BRADESCO_VIDA_PREV_RAIMUNDA',
    terceiro_slug='BRADESCO_VIDA_PREV',
    dados=dados,
    estado_civil_omitido=True,
    renda_alerta=True,         # INSS líquido vs renda bruta + DUPLA renda histórica
    cobranca_anual=False,
    pendencias_extras=[
        ('PRESCRIÇÃO — RISCO ALTO (PONTO MAIS CRÍTICO)',
         'Tese central de risco. Pelo art. 27 do CDC (5 anos) — corrente '
         'majoritária do STJ, Tema Repetitivo 1061 + EAREsp 1.280.825/RS '
         '(Corte Especial, j. 30/03/2021) — TODOS OS 56 LANÇAMENTOS ESTÃO '
         'PRESCRITOS. O último desconto ocorreu em 25/08/2020; o termo final '
         'do prazo quinquenal venceu em 25/08/2025. Na data de ajuizamento '
         '(06/05/2026) já se passaram cerca de 8 meses e 11 dias do termo '
         'final. A notificação extrajudicial enviada em 14/04/2026 NÃO '
         'interrompe prescrição (CC art. 202 — rol taxativo). '
         'CONTRA-ARGUMENTO ADOTADO PARA AJUIZAR: aplicação do art. 205 do CC '
         '(prazo decenal de 10 anos para repetição de indébito por '
         'enriquecimento sem causa), entendimento minoritário ainda acolhido '
         'em algumas câmaras do TJ-AM. Pelo decenal, apenas os 4 primeiros '
         'lançamentos (25/01/2016, 25/02/2016, 28/03/2016 e 25/04/2016) '
         'estão prescritos; os 52 demais (a partir de 25/05/2016) ainda '
         'estão vivos. Se o juízo aplicar a tese decenal, perde-se cerca de '
         'R$ 14,96 simples / R$ 29,92 dobro dos 4 lançamentos iniciais e '
         'remanesce R$ 225,08 simples / R$ 450,16 dobro. Se o juízo aplicar '
         'a tese quinquenal, perda total. Recomenda-se reforço expresso na '
         'inicial da tese decenal + actio nata diferida (conhecimento tardio '
         'do dano), preparar imediatamente recurso de apelação ou inominado '
         'para Turma Recursal caso a sentença reconheça prescrição '
         'quinquenal. ALERTA EXTRA: Maués/AM tem alerta de cautela com Juiz '
         'Anderson — confirmar antes do protocolo se o processo será '
         'distribuído em Caapiranga (sede própria) ou em Maués (caso seja '
         'Comarca delegada).'),
        ('VALORES UNITÁRIOS BAIXÍSSIMOS — IMPACTO NA TESE',
         'Os 56 lançamentos têm valor unitário entre R$ 3,74 e R$ 4,74. O '
         'banco certamente alegará na contestação que (i) o valor é ínfimo, '
         '(ii) é compatível com adesão tácita a seguro de vida ou produto '
         'previdenciário básico, e (iii) a autora teve ciência por 4 anos e '
         '7 meses sem reclamar (silêncio qualificado). Reforçar na inicial '
         'que (a) a autora não recebeu nem assinou apólice, proposta ou '
         'termo de adesão, (b) a rubrica genérica "PAGTO ELETRON COBRANCA" '
         'não permite o consumidor identificar de imediato a natureza do '
         'débito, (c) a baixa expressão individual é justamente a estratégia '
         'do banco para passar despercebido em consumidor hipossuficiente, '
         '(d) Súmula 297 STJ (CDC se aplica a instituições financeiras) e '
         '(e) art. 6º III + art. 46 CDC (dever de informação clara).'),
        ('RENDA — DUPLA FONTE HISTÓRICA + INSS PROVAVELMENTE LÍQUIDO',
         'Renda adotada: R$ 1.518,00 (último crédito INSS no extrato, em '
         '24/09/2025). PORÉM: (a) o extrato 2016–2020 mostra que a autora '
         'recebia paralelamente "TRANSF SALDO C/SAL P/CC" e "CREDITO DE '
         'SALARIO PREFEITURA MUNICIPAL DE CAAPIRAN" (R$ 809,60 a R$ 966,63 '
         'mensais), o que indica vínculo ativo com o RPPS municipal de '
         'Caapiranga até 2020 e provável aposentadoria DUPLA (RPPS + INSS). '
         'A partir de 2021 só aparece INSS no extrato — confirmar se a '
         'autora deixou de receber a aposentadoria municipal ou se passou a '
         'receber em outra conta. (b) O valor do INSS no extrato pode estar '
         'LÍQUIDO de consignações descontadas pelo próprio INSS — conferir '
         'HISCON antes do protocolo. Se houver renda adicional ou bruta '
         'maior, ajustar o parágrafo de Justiça Gratuita.'),
        ('PROFISSÃO E IDADE',
         'Autora declarada como aposentada na notificação extrajudicial; '
         'nascida em 04/01/1974 (52 anos em 06/05/2026). NÃO se aplica '
         'prioridade processual de idoso (art. 1.048 I CPC). A '
         'aposentadoria precoce + benefício INSS desde 2016 (com 42 anos) '
         'sugere aposentadoria por invalidez ou pensão por morte — '
         'confirmar com a cliente o tipo de benefício para evitar erro '
         'na qualificação (se for "pensionista" em vez de "aposentada", '
         'ajustar).'),
        ('COMPETÊNCIA — CAAPIRANGA/AM',
         'Comarca de CAAPIRANGA/AM (foro do domicílio do consumidor, '
         'art. 101 I CDC). NÃO é Maués. Confirmar distribuição na '
         'Comarca de Caapiranga (Comarca Delegada da JEF? Verificar se a '
         'Vara Única de Caapiranga é estadual ou também federal delegada).'),
        ('NOTIFICAÇÃO EXTRAJUDICIAL — DATA POSTERIOR À PRESCRIÇÃO QUINQUENAL',
         'A notificação extrajudicial foi enviada em 14/04/2026 — ou seja, '
         '~8 meses APÓS o término do prazo quinquenal do art. 27 CDC '
         '(25/08/2025). O banco usará esse fato em contestação para '
         'reforçar (i) que a autora reconheceu tardiamente o suposto dano, '
         '(ii) que não há ato de constituição em mora dentro do prazo, '
         'e (iii) que o protesto extrajudicial não interrompe prescrição. '
         'Pré-armar resposta na réplica.'),
    ],
)
print('EXEMPLA RAIMUNDA BRADESCO VIDA OK ->', docx)
print('  relatorio paralelo ->', rel)
print('  alertas:', alertas['severidade'], 'total=', alertas['total_alertas'])

# limpar tmp se existir
import shutil
tmp = os.path.join(BASE, '_tmp_pages')
if os.path.exists(tmp):
    shutil.rmtree(tmp)
    print('limpo:', tmp)
