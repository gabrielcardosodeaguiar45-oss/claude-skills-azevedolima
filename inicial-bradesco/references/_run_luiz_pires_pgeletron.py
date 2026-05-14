"""Inicial PG ELETRON ASPECIR — CLIENTE EXEMPLO.

Comarca Presidente Figueiredo/AM (Ag 3732 / Conta 20304-1). Pessoa
IDOSA, casado, aposentado pelo INSS R$ 988,00 (último crédito 06/12/2024).
Procuração a rogo.

Tabela: 4 lançamentos PAGTO ELETRON COBRANCA ASPECIR de R$ 79,00 entre
09/09/2024 e 06/12/2024. Total R$ 316,00 / dobro R$ 632,00. VC R$ 15.632,00.
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import gerar_inicial_pg_eletron, montar_dados_padrao

PASTA = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - BRADESCO\0.0 - Procução de iniciais\4. Pagamento Eletrônico de Cobrança\CLIENTE EXEMPLO - Ruth - TARIFA\PGTO ELETRÔNICO DE COBRANÇA'

LANCAMENTOS = [
    ('09/09/2024', 79.00), ('07/10/2024', 79.00),
    ('07/11/2024', 79.00), ('06/12/2024', 79.00),
]

autora = {
    'nome': 'CLIENTE EXEMPLO', 'nacionalidade': 'brasileiro',
    'estado_civil': 'casado', 'profissao': 'aposentado',
    'cpf': '000.000.017-27', 'rg': '1000015-5', 'orgao_expedidor_prefixo': 'SSP/AC',
    'logradouro': 'Av. Joaquim Cardoso', 'numero': '646',
    'bairro': 'Aida Mendonça', 'cidade': 'Presidente Figueiredo', 'cep': '69.735-000',
}
conta = {'agencia': '3732', 'numero': '20304-1'}
renda = {'valor_float': 988.00}
tese = {'rubrica': 'PAGTO ELETRON COBRANCA ASPECIR - UNIAO SEGURADORA', 'lancamentos': LANCAMENTOS}
terceiro = {
    'nome': 'ASPECIR UNIÃO SEGURADORA S.A.',
    'cnpj': '95.611.141/0001-57',
    'logradouro': 'Praça Otávio Rocha',
    'numero': '65, 1º andar',
    'bairro': 'Centro Histórico',
    'cidade': 'Porto Alegre',
    'uf': 'RS',
    'cep': '90020-140',
}

dados, calc = montar_dados_padrao(autora=autora, conta=conta, renda=renda, tese=tese, terceiro=terceiro,
                                  eh_idoso=True, competência='Presidente Figueiredo', uf='AM')
dados['remuneração'] = 'aposentadoria pelo INSS'

print(f'=== CLIENTE EXEMPLO — PG ELETRON ASPECIR ===')
print(f'Lançamentos: {len(LANCAMENTOS)}, total: R$ {calc["total"]:.2f} / dobro: R$ {calc["dobro"]:.2f} / VC: R$ {calc["valor_causa"]:.2f}')

docx, rel, alertas = gerar_inicial_pg_eletron(
    pasta_destino=PASTA,
    nome_arquivo_base='INICIAL_PgEletron_ASPECIR_LUIZ_PIRES',
    terceiro_slug='ASPECIR',
    dados=dados, estado_civil_omitido=False, renda_alerta=True, cobranca_anual=False,
    pendencias_extras=[
        ('PROCURAÇÃO ASSINADA A ROGO',
         'Pasta tem RG da rogada + 2 testemunhas (Evaristo + Nuberlândia). Conferir.'),
        ('CLIENTE TEM 4 TESES SEPARADAS',
         'CLIENTE EXEMPLO aparece em TARIFAS, MORA, TÍTULO e PG ELETRON (esta). PG ELETRON '
         'NÃO se consolida com as outras (responsabilidade solidária do terceiro). '
         'Mantém-se inicial separada.'),
        ('SEM créditos INSS em 2025/2026',
         'Último INSS no extrato é 06/12/2024 R$ 988. Confirmar status atual do '
         'benefício.'),
        ('TETO JEC — coberto',
         'VC R$ 15.632 ≈ 10,3 SM.'),
    ],
)
print(f'OK -> {docx}')
print(f'OK -> {rel}')
print(f'Alertas auditoria: {alertas.get("severidade")}')
