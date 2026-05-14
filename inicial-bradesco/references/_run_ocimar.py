"""Gera as 2 iniciais do CLIENTE EXEMPLO (BINCLUB + ODONTOPREV)."""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import gerar_inicial_pg_eletron, montar_dados_padrao

BASE = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - BRADESCO\0. TESTE 1\CLIENTE EXEMPLO CUNHA DA ROCHA - Nei Maués\PGTO ELETRÔNICO DE COBRANÇA'

autora_comum = {
    'nome': 'CLIENTE EXEMPLO CUNHA DA ROCHA',
    'nacionalidade': 'brasileiro',
    'estado_civil': '',  # OPCIONAL — não informado
    'profissao': 'aposentado',
    'cpf': '000.000.024-34',
    'rg': '1000022-2',
    'orgao_expedidor_prefixo': 'SSP/AM',
    'logradouro': 'Comunidade Galileia',
    'numero': '4992',
    'bairro': 'Rio Apocuitaua, Zona Rural',
    'cidade': 'Maués',
    'cep': '69.190-000',
}
conta = {'agencia': '3706', 'numero': '15075-4'}
renda = {'valor_float': 782.86}

# === BINCLUB ===
tese_binclub = {
    'rubrica': 'PAGTO ELETRON COBRANCA BINCLUB',
    'lancamentos': [
        ('26/04/2023', 61.90), ('29/05/2023', 61.90), ('28/06/2023', 61.90),
        ('27/07/2023', 61.90), ('29/08/2023', 61.90), ('27/09/2023', 61.90),
        ('27/10/2023', 74.90), ('28/11/2023', 74.90), ('26/12/2023', 74.90),
        ('29/01/2024', 84.90), ('27/02/2024', 89.99), ('26/03/2024', 89.99),
        ('26/04/2024', 89.99), ('17/05/2024', 89.99), ('28/05/2024', 89.99),
        ('26/06/2024', 89.99), ('05/07/2024', 89.99), ('10/07/2024', 89.99),
        ('23/07/2024', 89.99), ('29/07/2024', 89.99),
        ('08/08/2024', 99.99), ('20/08/2024', 99.99), ('02/09/2024', 99.99),
        ('09/09/2024', 99.99), ('01/10/2024', 99.99), ('11/10/2024', 99.99),
        ('29/10/2024', 99.99), ('27/11/2024', 99.99), ('11/12/2024', 99.99),
        ('26/12/2024', 99.99),
    ],
}
terceiro_binclub = {
    'nome': 'BINCLUB SERVIÇOS DE ADMINISTRAÇÃO E DE PROGRAMAS DE FIDELIDADE LTDA',
    'cnpj': '38.056.833/0001-47',
    'logradouro': 'Avenida Nove de Julho',
    'numero': '3.228, Sala 404, Letra A',
    'bairro': 'Jardim Paulista',
    'cidade': 'São Paulo',
    'uf': 'SP',
    'cep': '01.406-000',
}
dados_binclub, _ = montar_dados_padrao(autora_comum, conta, renda, tese_binclub, terceiro_binclub, eh_idoso=True)

docx, rel, alertas = gerar_inicial_pg_eletron(
    pasta_destino=os.path.join(BASE, 'BINCLUB'),
    nome_arquivo_base='INICIAL_PgEletron_BINCLUB_CLIENTE EXEMPLO',
    terceiro_slug='BINCLUB',
    dados=dados_binclub,
    estado_civil_omitido=True,
    renda_alerta=True,
    cobranca_anual=False,
)
print('BINCLUB OK ->', docx)
print('  alertas:', alertas['severidade'], alertas['total_alertas'])

# === ODONTOPREV ===
tese_odonto = {
    'rubrica': 'PAGTO ELETRON COBRANCA ODONTOPREV S/A',
    'lancamentos': [
        ('26/03/2024', 54.99), ('08/04/2024', 54.99),
        ('06/05/2024', 54.99), ('04/06/2024', 54.99),
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
dados_odonto, _ = montar_dados_padrao(autora_comum, conta, renda, tese_odonto, terceiro_odonto, eh_idoso=True)

docx, rel, alertas = gerar_inicial_pg_eletron(
    pasta_destino=os.path.join(BASE, 'ODONTOPREV'),
    nome_arquivo_base='INICIAL_PgEletron_ODONTOPREV_CLIENTE EXEMPLO',
    terceiro_slug='ODONTOPREV',
    dados=dados_odonto,
    estado_civil_omitido=True,
    renda_alerta=True,
    cobranca_anual=False,
)
print('ODONTOPREV OK ->', docx)
print('  alertas:', alertas['severidade'], alertas['total_alertas'])

# limpar tmp
import shutil
tmp = os.path.join(BASE, 'BINCLUB', '_tmp_pages')
if os.path.exists(tmp):
    shutil.rmtree(tmp)
print('limpo:', tmp)
