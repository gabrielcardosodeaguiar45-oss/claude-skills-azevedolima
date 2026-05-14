"""Gera 2 iniciais PG ELETRON do RAIMUNDO NONATO BASTOS.

Comarca: Presidente Figueiredo/AM (foro do domicílio, art. 101 I CDC).
Autor IDOSO (nascido 23/08/1956 → 69 anos em 06/05/2026 — prioridade
art. 1.048 I CPC). Conta Bradesco Ag 3732, conta 19707-6.
Renda: INSS R$ 1.096,58 (último crédito 02/01/2026).

2 teses PG ELETRON, 1 inicial por terceiro:
- ODONTOPREV S/A (CNPJ 58.119.199/0001-51, Barueri/SP): 2 lançamentos
  (05/02/2024 R$ 549,90 + 28/02/2025 R$ 590,57). Total R$ 1.140,47.
- BRADESCO AUTO/RE COMPANHIA DE SEGUROS (CNPJ 92.682.038/0001-00,
  Rio de Janeiro/RJ): 1 lançamento ÚNICO em 01/06/2022 R$ 145,90.

Tabela 7-TABELA.pdf da pasta ODONTOPREV é mista — traz os 3 lançamentos
de ambas as teses. Cada inicial leva APENAS os lançamentos da sua rubrica.

Pasta KIT contém material para outras teses (MORA CRED + ENCARGO,
TARIFA - PACOTE DE SERVIÇOS + CESTA CLASSIC, e NÃO CONTRATADO -
contrato 0123493821574). Pelo escopo do batch (PG ELETRON), KIT é
ignorado. Se quiser as outras teses, processar pasta KIT em batch separado
(MORA + TARIFA via inicial-bradesco; NÃO CONTRATADO via outra skill).
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import gerar_inicial_pg_eletron, montar_dados_padrao

BASE_ODONTOPREV = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - BRADESCO\0. TESTE 1\RAIMUNDO NONATO BASTOS - Ruth\PGTO ELETRÕNICO DE COBRANÇA\ODONTOPREV'
BASE_SEGRESID   = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - BRADESCO\0. TESTE 1\RAIMUNDO NONATO BASTOS - Ruth\PGTO ELETRÕNICO DE COBRANÇA\SEG-RESID'

autora = {
    'nome': 'RAIMUNDO NONATO BASTOS',
    'nacionalidade': 'brasileiro',
    'estado_civil': '',  # não consta nas notificações — omitir
    'profissao': 'aposentado',  # notificação diz "beneficiário do INSS"; profissão social compatível
    'cpf': '000.000.029-39',
    'rg': '1000027-7',
    'orgao_expedidor_prefixo': 'SSP/AM',
    'logradouro': 'Rodovia BR 174, KM 165, Ramal do Puraquê',
    'numero': 's/nº',
    'bairro': 'Zona Rural',
    'cidade': 'Presidente Figueiredo',
    'cep': '69.735-000',
}
conta = {'agencia': '3732', 'numero': '19707-6'}
renda = {'valor_float': 1096.58}

# ===================== INICIAL 1: ODONTOPREV =====================
tese_odonto = {
    'rubrica': 'PAGTO ELETRON COBRANCA ODONTOPREV S/A',
    'lancamentos': [
        ('05/02/2024', 549.90),
        ('28/02/2025', 590.57),
    ],
}
terceiro_odonto = {
    'nome': 'ODONTOPREV S/A',
    'cnpj': '58.119.199/0001-51',
    'logradouro': 'Alameda Araguaia',
    'numero': '2.104, 21º andar, Conj. 211 ao 214',
    'bairro': 'Alphaville',
    'cidade': 'Barueri',
    'uf': 'SP',
    'cep': '06.455-000',
}

dados, totais = montar_dados_padrao(
    autora, conta, renda, tese_odonto, terceiro_odonto,
    eh_idoso=True,
    competência='Presidente Figueiredo',
    uf='AM',
)
print('--- ODONTOPREV ---')
print('Total simples:', totais['total'])
print('Dobro:', totais['dobro'])
print('Valor causa:', totais['valor_causa'])

docx, rel, alertas = gerar_inicial_pg_eletron(
    pasta_destino=BASE_ODONTOPREV,
    nome_arquivo_base='INICIAL_PgEletron_ODONTOPREV_RAIMUNDO_BASTOS',
    terceiro_slug='ODONTOPREV',
    dados=dados,
    estado_civil_omitido=True,
    renda_alerta=True,
    cobranca_anual=False,
    pendencias_extras=[
        ('TABELA MISTA — 7-TABELA.pdf cobre ODONTOPREV + SEG-RESID',
         'A tabela "7 - TABELA.pdf" da pasta ODONTOPREV traz os 3 '
         'lançamentos do cliente (1 BRADESCO SEG-RESID em 01/06/2022 '
         'R$ 145,90 + 2 ODONTOPREV em 05/02/2024 R$ 549,90 e 28/02/2025 '
         'R$ 590,57). TOTAL impresso R$ 1.286,37. Esta inicial usa APENAS '
         'os 2 lançamentos da ODONTOPREV (R$ 1.140,47 simples / '
         'R$ 2.280,94 dobro). A tese SEG-RESID é objeto de inicial '
         'separada (1 inicial por terceiro, regra absoluta de PG ELETRON).'),
        ('LANÇAMENTOS ANUAIS — padrão de plano odontológico',
         'Os 2 lançamentos ocorreram com intervalo de ~1 ano (05/02/2024 '
         'e 28/02/2025), padrão típico de mensalidade de plano odontológico '
         'com cobrança anual de matrícula/manutenção. Confirmar com cliente '
         'que NUNCA aderiu a plano da ODONTOPREV, NUNCA recebeu carteirinha, '
         'NUNCA usou consulta odontológica vinculada à ODONTOPREV.'),
        ('PROFISSÃO — notificação diz "beneficiário do INSS"',
         'A notificação extrajudicial qualifica o autor como "brasileiro, '
         'beneficiário do INSS" (não "aposentado"). Considerando o '
         'recebimento contínuo de INSS desde 2019 com valores que '
         'acompanharam o salário-mínimo (R$ 998 em 2019 a R$ 1.096,58 em '
         '2025–2026), provável aposentadoria ou pensão por morte. Esta '
         'inicial usa "aposentado" como profissão (compatível). Confirmar '
         'tipo de benefício e ajustar para "pensionista" se necessário.'),
        ('COMPETÊNCIA — Presidente Figueiredo/AM',
         'Comarca de PRESIDENTE FIGUEIREDO/AM (foro do domicílio do '
         'consumidor, art. 101 I CDC). Não é Maués. Confirmar se a Comarca '
         'tem Vara Única ou se há JEF/JEC.'),
        ('VALORES UNITÁRIOS RELEVANTES — diferente do padrão "centavos"',
         'Os 2 lançamentos têm valores significativos (R$ 549,90 e R$ 590,57). '
         'Diferente da Bradesco Vida e Prev. (centavos), aqui o banco '
         'pode alegar com mais força que o consumidor "deveria perceber" o '
         'desconto e que o silêncio constitui anuência tácita. Reforçar na '
         'inicial: nomenclatura genérica, ausência de termo de adesão, '
         'inexistência de utilização do plano (cliente nunca consultou '
         'dentista pela ODONTOPREV).'),
        ('OUTRAS TESES NA PASTA KIT — não processadas neste run',
         'A pasta KIT contém material para 3 teses adicionais não '
         'processadas neste run: (1) MORA CRED + ENCARGO LIMITE DE CRÉDITO '
         '+ SERVIÇO CARTÃO PROTEGIDO; (2) TARIFA - PACOTE DE SERVIÇOS + '
         'CESTA CLASSIC; (3) NÃO CONTRATADO - contrato 0123493821574. As '
         'duas primeiras podem ser processadas em batch separado pela '
         'própria skill `inicial-bradesco` apontando para as subpastas do '
         'KIT. A tese NÃO CONTRATADO precisa de skill diferente '
         '(`replica-nao-contratado` para a réplica, ou outra inicial).'),
    ],
)
print('OK ->', docx)
print('  rel ->', rel)
print('  alertas:', alertas['severidade'], 'total=', alertas['total_alertas'])
print()

# ===================== INICIAL 2: SEG-RESID =====================
tese_segresid = {
    'rubrica': 'PAGTO ELETRON COBRANCA BRADESCO SEG-RESID/OUTROS',
    'lancamentos': [
        ('01/06/2022', 145.90),
    ],
}
terceiro_segresid = {
    'nome': 'BRADESCO AUTO/RE COMPANHIA DE SEGUROS',
    'cnpj': '92.682.038/0001-00',
    'logradouro': 'Avenida Rio de Janeiro',
    'numero': '555',
    'bairro': 'Caju',
    'cidade': 'Rio de Janeiro',
    'uf': 'RJ',
    'cep': '20.931-675',
}

dados2, totais2 = montar_dados_padrao(
    autora, conta, renda, tese_segresid, terceiro_segresid,
    eh_idoso=True,
    competência='Presidente Figueiredo',
    uf='AM',
)
print('--- SEG-RESID ---')
print('Total simples:', totais2['total'])
print('Dobro:', totais2['dobro'])
print('Valor causa:', totais2['valor_causa'])

docx2, rel2, alertas2 = gerar_inicial_pg_eletron(
    pasta_destino=BASE_SEGRESID,
    nome_arquivo_base='INICIAL_PgEletron_SEGRESID_RAIMUNDO_BASTOS',
    terceiro_slug='SEGRESID',
    dados=dados2,
    estado_civil_omitido=True,
    renda_alerta=True,
    cobranca_anual=False,
    pendencias_extras=[
        ('LANÇAMENTO ÚNICO + VALOR BAIXO — RISCO DE TESE FRACA',
         'Há APENAS 1 lançamento da rubrica BRADESCO SEG-RESID/OUTROS, '
         'em 01/06/2022, no valor de R$ 145,90 (simples) / R$ 291,80 '
         '(dobro). O lançamento isolado de pequeno valor é tipicamente '
         'cobrança de APÓLICE ANUAL DE SEGURO RESIDENCIAL — produto da '
         'BRADESCO AUTO/RE para imóvel residencial. A defesa do banco '
         'normalmente apresenta apólice ativa, comprovante de '
         'contratação por canal eletrônico, ou alegação de que o valor é '
         'compatível com proteção contra eventos comuns (incêndio, roubo, '
         'danos elétricos). CONFIRMAR ANTES DO PROTOCOLO: (a) o autor '
         'JAMAIS recebeu apólice ou comunicação da Bradesco Auto/RE; '
         '(b) NÃO foi proprietário ou arrendatário de imóvel coberto na '
         'data; (c) NÃO houve sinistro coberto, comunicação prévia, '
         'renovação automática ou aviso de cobrança. Se houver qualquer '
         'evidência de adesão (canal digital, telefone, oferta no '
         'aplicativo), reavaliar viabilidade.'),
        ('CESSAÇÃO DE COBRANÇA — apenas 1 desconto',
         'A cobrança ocorreu uma única vez em 01/06/2022 e não se repetiu '
         'desde então (extrato 2022-2026 confirmado). Esse fato pode '
         'sugerir que (i) houve cancelamento automático após 1 anuidade, '
         '(ii) houve uma cobrança avulsa/excepcional, ou (iii) a apólice '
         'expirou. O pedido de cessação imediata (item I) tem força '
         'limitada porque a cobrança já cessou de fato. Pode ser '
         'reformulado para "obrigação de não cobrar novamente sob a mesma '
         'rubrica ou produto correlato".'),
        ('VALOR DA CAUSA BAIXO — Juizado Especial?',
         'VC R$ 15.291,80. Está acima do teto do JEC (40 SM ≈ R$ 60.720) '
         'mas abaixo do limite que define competência relativa em comarcas '
         'do interior. Avaliar se Comarca de Presidente Figueiredo tem '
         'JEC instalado e se o autor prefere o rito ordinário (comum) '
         'pela complexidade da tese ou por estratégia de não submeter ao '
         'JEC. Em Maués/AM o juízo costuma ser único — confirmar para '
         'Presidente Figueiredo.'),
        ('PRESCRIÇÃO — NÃO se aplica',
         'O lançamento ocorreu em 01/06/2022. Hoje (06/05/2026) decorreram '
         '3 anos, 11 meses e 5 dias. Pelo art. 27 CDC (5 anos) ou pelo '
         'art. 205 CC (10 anos), a pretensão NÃO está prescrita. Termo '
         'final pelo CDC: 01/06/2027. Não há urgência prescricional, mas '
         'o ajuizamento dentro do prazo é recomendado.'),
        ('PROFISSÃO — notificação diz "beneficiário do INSS"',
         'Mesma observação da inicial ODONTOPREV: notificação qualifica '
         'como "brasileiro, beneficiário do INSS". Esta inicial usa '
         '"aposentado" (compatível). Confirmar tipo de benefício INSS.'),
        ('COMPETÊNCIA — Presidente Figueiredo/AM',
         'Mesma comarca da outra inicial (Presidente Figueiredo). 1 '
         'inicial por terceiro = 2 processos distintos no mesmo juízo, '
         'com possibilidade de distribuição por dependência ou conexão se '
         'o juízo entender pertinente.'),
    ],
)
print('OK ->', docx2)
print('  rel ->', rel2)
print('  alertas:', alertas2['severidade'], 'total=', alertas2['total_alertas'])

# limpar tmp se existir
import shutil
for p in (BASE_ODONTOPREV, BASE_SEGRESID):
    tmp = os.path.join(p, '_tmp_pages')
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
        print('limpo:', tmp)
