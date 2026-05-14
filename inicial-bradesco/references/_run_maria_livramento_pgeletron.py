"""Inicial PG ELETRON PSERV — MARIA DO LIVRAMENTO LIMA DOS SANTOS.

Comarca Presidente Figueiredo/AM. Pessoa IDOSA. Aposentada pelo INSS
R$ 986,58. Conta 21528-7 / Ag 3732.

Tabela: 8 lançamentos PAGTO ELETRON COBRANCA PSERV de R$ 89,91-89,93
entre 04/02/2025 e 02/10/2025. Total R$ 719,30 / dobro R$ 1.438,60.
VC R$ 16.438,60.

Terceiro: PAULISTA SERVIÇOS DE RECEBIMENTOS E PAGAMENTOS LTDA (PSERV).
CNPJ 15.245.499/0001-74. Av. Brigadeiro Faria Lima, 1.355, Jardim
Paulistano, São Paulo/SP, CEP 01452-919.
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import gerar_inicial_pg_eletron, montar_dados_padrao

PASTA = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - BRADESCO\0.0 - Procução de iniciais\4. Pagamento Eletrônico de Cobrança\MARIA DO LIVRAMENTO LIMA DOS SANTOS - Ruth\PAGTO ELETRÔNICO DE COBRANÇA'

LANCAMENTOS = [
    ('04/02/2025', 89.91), ('07/03/2025', 89.91), ('02/04/2025', 89.91),
    ('03/06/2025', 89.91), ('03/06/2025', 89.93), ('02/07/2025', 89.91),
    ('02/09/2025', 89.91), ('02/10/2025', 89.91),
]

autora = {
    'nome': 'MARIA DO LIVRAMENTO LIMA DOS SANTOS', 'nacionalidade': 'brasileira',
    'estado_civil': '', 'profissao': 'aposentada',
    'cpf': '000.000.021-31', 'rg': '1000019-9', 'orgao_expedidor_prefixo': 'SSP/AM',
    'logradouro': 'Ramal do Rumo Certo, BR 174 - KM 165', 'numero': 's/nº',
    'bairro': 'Comunidade Boa União', 'cidade': 'Presidente Figueiredo', 'cep': '69.735-000',
}
conta = {'agencia': '3732', 'numero': '21528-7'}
renda = {'valor_float': 986.58}
tese = {'rubrica': 'PAGTO ELETRON COBRANCA PSERV', 'lancamentos': LANCAMENTOS}
terceiro = {
    'nome': 'PAULISTA SERVIÇOS DE RECEBIMENTOS E PAGAMENTOS LTDA',
    'cnpj': '15.245.499/0001-74',
    'logradouro': 'Avenida Brigadeiro Faria Lima',
    'numero': '1.355, 1º andar',
    'bairro': 'Jardim Paulistano',
    'cidade': 'São Paulo',
    'uf': 'SP',
    'cep': '01452-919',
}

dados, calc = montar_dados_padrao(autora=autora, conta=conta, renda=renda, tese=tese, terceiro=terceiro,
                                  eh_idoso=True, competência='Presidente Figueiredo', uf='AM')
dados['remuneração'] = 'aposentadoria pelo INSS'

print(f'=== MARIA DO LIVRAMENTO — PG ELETRON PSERV ===')
print(f'Lançamentos: {len(LANCAMENTOS)}, total: R$ {calc["total"]:.2f} / dobro: R$ {calc["dobro"]:.2f} / VC: R$ {calc["valor_causa"]:.2f}')

docx, rel, alertas = gerar_inicial_pg_eletron(
    pasta_destino=PASTA,
    nome_arquivo_base='INICIAL_PgEletron_PSERV_MARIA_LIVRAMENTO',
    terceiro_slug='PSERV',
    dados=dados, estado_civil_omitido=True, renda_alerta=True, cobranca_anual=False,
    pendencias_extras=[
        ('TERCEIRO PSERV — empresa de recebimentos e pagamentos',
         'PAULISTA SERVIÇOS DE RECEBIMENTOS E PAGAMENTOS LTDA é processadora de '
         'recebimentos. Provavelmente intermedia cobranças de outra empresa. CONFIRMAR '
         'com cliente que NUNCA contratou serviço/produto que justifique débito de '
         'R$ 89,91 mensal.'),
        ('LANÇAMENTO DUPLICADO em 03/06/2025',
         'Em 03/06/2025 a tabela registra 2 lançamentos (R$ 89,91 + R$ 89,93). '
         'Conferir extrato — pode ser cobrança em duplicidade.'),
        ('CLIENTE TEM 3 TESES SEPARADAS',
         'MARIA aparece em TARIFAS, TÍTULO (já geradas) e PG ELETRON (esta). '
         'PG ELETRON mantém-se separada (terceiro solidário).'),
        ('CASAL CO-DEMANDANTE',
         'Endereço idêntico ao EXEMPLO MANUEL DOS SANTOS — provavelmente cônjuges.'),
        ('TETO JEC — coberto', 'VC R$ 16.438,60 ≈ 10,8 SM.'),
    ],
)
print(f'OK -> {docx}')
print(f'OK -> {rel}')
print(f'Alertas auditoria: {alertas.get("severidade")}')
