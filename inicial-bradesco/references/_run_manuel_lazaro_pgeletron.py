"""Inicial PG ELETRON SUDACRED — EXEMPLO MANUEL CORDOVIL.

Comarca Barreirinha/AM. Pessoa IDOSA. Aposentado pelo INSS R$ 846,22.
Conta 2782-0 / Ag 3725.

Tabela: 4 lançamentos PAGTO ELETRON COBRANCA SUDACRED de R$ 58,67 entre
02/04/2025 e 02/07/2025. Total R$ 234,68 / dobro R$ 469,36.
VC R$ 15.469,36.

Terceiro: SUDACRED Sociedade de Crédito Direto S.A. CNPJ 20.251.847/0001-56.
Rua Inácio Lustosa, 755, São Francisco, Curitiba/PR, CEP 80510-000.
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import gerar_inicial_pg_eletron, montar_dados_padrao

PASTA = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - BRADESCO\0.0 - Procução de iniciais\4. Pagamento Eletrônico de Cobrança\EXEMPLO MANUEL CORDOVIL - Wilson - TARIFA\PAGTO ELETRÔNICO DE COBRANÇA'

LANCAMENTOS = [
    ('02/04/2025', 58.67), ('05/05/2025', 58.67),
    ('03/06/2025', 58.67), ('02/07/2025', 58.67),
]

autora = {
    'nome': 'EXEMPLO MANUEL CORDOVIL', 'nacionalidade': 'brasileiro',
    'estado_civil': '', 'profissao': 'aposentado',
    'cpf': '000.000.018-28', 'rg': '1000016-6', 'orgao_expedidor_prefixo': 'SSP/AM',
    'logradouro': 'Rua Pimentel Tavares', 'numero': '341',
    'bairro': 'CM Terra P do Limão', 'cidade': 'Barreirinha', 'cep': '69.160-000',
}
conta = {'agencia': '3725', 'numero': '2782-0'}
renda = {'valor_float': 846.22}
tese = {'rubrica': 'PAGTO ELETRON COBRANCA SUDACRED', 'lancamentos': LANCAMENTOS}
terceiro = {
    'nome': 'SUDACRED SOCIEDADE DE CRÉDITO DIRETO S.A.',
    'cnpj': '20.251.847/0001-56',
    'logradouro': 'Rua Inácio Lustosa',
    'numero': '755',
    'bairro': 'São Francisco',
    'cidade': 'Curitiba',
    'uf': 'PR',
    'cep': '80510-000',
}

dados, calc = montar_dados_padrao(autora=autora, conta=conta, renda=renda, tese=tese, terceiro=terceiro,
                                  eh_idoso=True, competência='Barreirinha', uf='AM')
dados['remuneração'] = 'aposentadoria pelo INSS'

print(f'=== EXEMPLO MANUEL — PG ELETRON SUDACRED ===')
print(f'Lançamentos: {len(LANCAMENTOS)}, total: R$ {calc["total"]:.2f} / dobro: R$ {calc["dobro"]:.2f} / VC: R$ {calc["valor_causa"]:.2f}')

docx, rel, alertas = gerar_inicial_pg_eletron(
    pasta_destino=PASTA,
    nome_arquivo_base='INICIAL_PgEletron_SUDACRED_MANUEL_LAZARO',
    terceiro_slug='SUDACRED',
    dados=dados, estado_civil_omitido=True, renda_alerta=True, cobranca_anual=False,
    pendencias_extras=[
        ('TERCEIRO SUDACRED — sociedade de crédito direto',
         'SUDACRED é fintech de crédito direto (CDC art. 14). Anexar print/dados do '
         'BACEN sobre a empresa se possível. Confirmar com cliente que NUNCA tomou '
         'empréstimo nem aderiu a programa SUDACRED.'),
        ('CLIENTE TEM 3 TESES SEPARADAS',
         'EXEMPLO MANUEL aparece em TARIFAS+MORA (já geradas) e PG ELETRON (esta). '
         'PG ELETRON mantém-se separada (responsabilidade solidária do terceiro).'),
        ('TETO JEC — coberto', 'VC R$ 15.469,36 ≈ 10,2 SM.'),
    ],
)
print(f'OK -> {docx}')
print(f'OK -> {rel}')
print(f'Alertas auditoria: {alertas.get("severidade")}')
