"""Gera a inicial PG ELETRON ODONTOPREV de CLIENTE EXEMPLO SOUZA DE FREITAS VIANA.

Comarca: Caapiranga/AM. Não idosa (08/02/1978 → 48 anos em 06/05/2026).
Conta: Bradesco Ag 3707, conta 501049-7.
Renda: TRANSF SALDO C/SAL P/CC mensal R$ 3.575,38 (último crédito recorrente,
01/10/2025) — provavelmente conta-salário de servidora aposentada do
município de Caapiranga. Em 2024 era R$ 3.376,64 (aumento anual do
funcionalismo). Adotar R$ 3.575,38 (mais recente).

Tese: 1 lançamento ÚNICO em 28/03/2025 — R$ 879,90 simples / R$ 1.759,80
dobro / dano moral R$ 15.000,00 / VC R$ 16.759,80. Pasta KIT presente
mas IGNORADA por padrão (regra § 4 da SKILL).
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import gerar_inicial_pg_eletron, montar_dados_padrao

BASE = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - BRADESCO\0. TESTE 1\CLIENTE EXEMPLO SOUZA DE FREITAS VIANA - Ney Pedroza'

autora = {
    'nome': 'CLIENTE EXEMPLO SOUZA DE FREITAS VIANA',
    'nacionalidade': 'brasileira',
    'estado_civil': 'solteira',
    'profissao': 'aposentada',
    'cpf': '000.000.023-33',
    'rg': '1000021-1',
    'orgao_expedidor_prefixo': 'SSP/AM',
    'logradouro': 'CM Paraná do Mari',
    'numero': '7.955',
    'bairro': 'Zona Rural',
    'cidade': 'Caapiranga',
    'cep': '69.425-000',
}
conta = {'agencia': '3707', 'numero': '501049-7'}
renda = {'valor_float': 3575.38}

tese = {
    'rubrica': 'PAGTO ELETRON COBRANCA ODONTOPREV S/A',
    'lancamentos': [
        ('28/03/2025', 879.90),
    ],
}
terceiro = {
    'nome': 'ODONTOPREV S/A',
    'cnpj': '58.119.199/0001-51',
    'logradouro': 'Alameda Araguaia',
    'numero': '2.104, 21º andar, Conj. 211 ao 214',
    'bairro': 'Alphaville',
    'cidade': 'Barueri',
    'uf': 'SP',
    'cep': '06.455-000',
}

dados, _ = montar_dados_padrao(autora, conta, renda, tese, terceiro, eh_idoso=False)

docx, rel, alertas = gerar_inicial_pg_eletron(
    pasta_destino=BASE,
    nome_arquivo_base='INICIAL_PgEletron_ODONTOPREV_CLIENTE EXEMPLO',
    terceiro_slug='ODONTOPREV',
    dados=dados,
    estado_civil_omitido=False,
    renda_alerta=True,
    cobranca_anual=False,
    pendencias_extras=[
        ('LANÇAMENTO ÚNICO',
         'Único débito em 28/03/2025 R$ 879,90 (regra § "Lançamento isolado" da SKILL). '
         'Confirmar com a cliente que NÃO houve adesão pontual a plano odontológico '
         '(fatura única, mensalidade anual antecipada, matrícula, etc.). A notificação '
         'extrajudicial já registra a negativa expressa, mas o procurador deve '
         'reconfirmar antes do protocolo.'),
        ('RENDA — APOSENTADORIA OU ATIVIDADE',
         'TRANSF SALDO C/SAL P/CC mensal R$ 3.575,38 (em 2024 era R$ 3.376,64). Padrão '
         'típico de servidor público que recebe via conta-salário. A notificação chama '
         '"aposentada", mas a transferência mensal entre contas do mesmo banco indica '
         'conta-salário ativa do município de Caapiranga. Confirmar se a cliente é '
         'APOSENTADA (RPPS municipal) ou ainda em atividade — pode mudar a profissão '
         'informada na qualificação.'),
        ('COMPETÊNCIA',
         'Comarca de CAAPIRANGA/AM (foro do domicílio do consumidor, art. 101, I, CDC). '
         'NÃO é Maués nem o foro de eleição de Bradesco/Odontoprev. Conferir '
         'distribuição na Comarca de Caapiranga.'),
    ],
)
print('CLIENTE EXEMPLO ODONTOPREV OK ->', docx)
print('  relatorio paralelo ->', rel)
print('  alertas:', alertas['severidade'], 'total=', alertas['total_alertas'])

# limpar tmp
import shutil
tmp = os.path.join(BASE, '_tmp_pages')
if os.path.exists(tmp):
    shutil.rmtree(tmp)
    print('limpo:', tmp)
