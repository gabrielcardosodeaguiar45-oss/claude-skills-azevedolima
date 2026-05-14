"""Executa pipeline AM para 2 clientes do TJAM:

- FABIO MARINHO DE OLIVEIRA (Presidente Figueiredo/AM): 2 bancos (AGIBANK + C6)
  → 2 iniciais separadas
- PAOLA MAITE RODRIGUES DE CASTRO (Boa Vista do Ramos/AM): 1 banco (C6)
  → 1 inicial
  → MENOR (5 anos) — representada pela mãe NAYEZA BRAGA RODRIGUES

REGRA do escritório: TODAS as iniciais AM são protocoladas pelo Dr. Patrick
Willian da Silva (OAB/AM A2638), independentemente de quem assinou a
notificação extrajudicial (Eduardo, Gabriel, Tiago aparecem na procuração mas
quem protocola é Patrick — sistema PJe/Projudi acessado pelo Patrick).
"""
import io, sys, os
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso_am import montar_dados_inicial_am, gerar_inicial_am

# === FABIO MARINHO DE OLIVEIRA ===
# Dados extraídos da notificação extrajudicial + HISCRE confirmados
AUTORA_FABIO = {
    'nome': 'FÁBIO MARINHO DE OLIVEIRA',
    'nacionalidade': 'brasileiro',
    'estado_civil': 'solteiro',
    'profissao': 'aposentado',
    'cpf': '000.000.003-13',
    'rg': '1000001-1',  # CONFERIR — notificação traz mesmo número do CPF (provável erro)
    'orgao_expedidor': 'SSP/AM',
    'data_nascimento': datetime(1980, 11, 20),  # do HISCRE
    'nome_mae': 'MARIA DULCE MARINHO DE OLIVEIRA',  # do HISCRE
    'logradouro': 'Ramal da Lixeira, s/nº, AM 240 KM 04',
    'numero': 's/nº',
    'bairro': 'Zona Rural',
    'cidade': 'Presidente Figueiredo',
    'uf': 'AM',
    'cep': '69.735-000',
    'renda_liquida': None,  # virá do HISCRE
}

# === PAOLA MAITÊ RODRIGUES DE CASTRO (MENOR IMPÚBERE — 5 anos) ===
# Para menor < 16: REPRESENTADA pela genitora.
# Para menor 16–18: ASSISTIDA pela genitora. (a função em adaptador_am.py decide)
AUTORA_PAOLA = {
    'nome': 'PAOLA MAITÊ RODRIGUES DE CASTRO',
    'nacionalidade': 'brasileira',
    # estado_civil/profissão não se aplicam diretamente — são derivados
    # pela função montar_qualificacao_menor (impúbere/púbere + 'beneficiária')
    'estado_civil': '',
    'profissao': 'beneficiária',
    'cpf': '000.000.004-14',
    'rg': '',  # menor impúbere — sem RG nesta qualificação
    'orgao_expedidor': '',
    'data_nascimento': datetime(2020, 12, 22),  # do HISCRE — 5 anos
    'nome_mae': 'NAYEZA BRAGA RODRIGUES',
    'logradouro': 'Rua Emanoel Mafra',
    'numero': '312',
    'bairro': 'Centro',
    'cidade': 'Boa Vista do Ramos',
    'uf': 'AM',
    'cep': '69.220-134',
    'renda_liquida': None,
}

# Representante legal da PAOLA (mãe NAYEZA BRAGA RODRIGUES)
# Dados confirmados pelo procurador (07/05/2026).
REPRESENTANTE_PAOLA = {
    'nome': 'NAYEZA BRAGA RODRIGUES',
    'nacionalidade': 'brasileira',
    'estado_civil': 'solteira',
    'profissao': 'beneficiária do INSS',
    'cpf': '000.000.005-15',
    'rg': '1000002-2',
    'orgao_expedidor': 'SSP/AM',
}

BASE = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO'

# Contratos OUTORGADOS nas procurações (lidos via OCR multimodal em 07/05/2026):
#  - FABIO/AGIBANK: 1527829615 ("referente ao contrato de empréstimo sob nº ...")
#  - FABIO/C6:      90135039498 ("referente ao contrato de empréstimo sob nº ...")
#  - PAOLA/C6:      pendente (pasta sumiu da máquina nesta data)
CASOS = [
    {
        'nome': 'FABIO_AGIBANK',
        'pasta': os.path.join(BASE, r'FABIO MARINHO DE OLIVEIRA - Ruth\AGIBANK'),
        'autora': AUTORA_FABIO,
        'comarca': 'Presidente Figueiredo',
        'procurador_chave': 'patrick',
        'representante': None,
        'docx_out': 'INICIAL_NaoContratado_FABIO_AGIBANK.docx',
        'numeros_contrato_explicitos': ['1527829615'],
    },
    {
        'nome': 'FABIO_C6',
        'pasta': os.path.join(BASE, r'FABIO MARINHO DE OLIVEIRA - Ruth\C6 CONSIGNADO'),
        'autora': AUTORA_FABIO,
        'comarca': 'Presidente Figueiredo',
        'procurador_chave': 'patrick',
        'representante': None,
        'docx_out': 'INICIAL_NaoContratado_FABIO_C6.docx',
        'numeros_contrato_explicitos': ['90135039498'],
    },
    {
        'nome': 'PAOLA_C6',
        'pasta': os.path.join(BASE, r'PAOLA MAITE RODRIGUES DE CASTRO - Wilson'),
        'autora': AUTORA_PAOLA,
        'comarca': 'Boa Vista do Ramos',
        'procurador_chave': 'patrick',
        'representante': REPRESENTANTE_PAOLA,
        'docx_out': 'INICIAL_NaoContratado_PAOLA_C6.docx',
        'numeros_contrato_explicitos': None,  # ler procuração via OCR quando pasta voltar
    },
]


def processar(caso):
    print(f'\n████████████ {caso["nome"]} ████████████')
    pasta = caso['pasta']
    if not os.path.isdir(pasta):
        print(f'  ❌ Pasta não existe: {pasta}')
        return None
    try:
        dados = montar_dados_inicial_am(
            pasta_banco=pasta,
            autora=caso['autora'],
            comarca=caso['comarca'],
            procurador_chave=caso['procurador_chave'],
            representante_legal=caso['representante'],
            numeros_contrato_explicitos=caso.get('numeros_contrato_explicitos'),
        )
    except Exception as e:
        print(f'  ❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return None

    print(f'  Comarca: {dados["comarca"]}/AM')
    print(f'  Procurador: {dados["procurador"]["nome"]} ({dados["procurador"]["oab"]})')
    print(f'  Banco-réu: {dados["banco_reu"]["nome"]}')
    print(f'  Contratos: {len(dados["contratos_questionados"])}')
    print(f'  Template: {os.path.basename(dados["template"])}')
    print(f'  Dano moral: R$ {dados["dano_moral"]["total"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
    print(f'  Valor da causa: R$ {dados["valor_causa"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
    print(f'  Idoso: {dados["eh_idoso"]}')
    if dados['representante_legal']:
        print(f'  REPRESENTANTE LEGAL: {dados["representante_legal"]["nome"]}')
    if dados['divergencias_pessoais']:
        print(f'  🚨 DIVERGÊNCIAS DOC vs HISCRE: {len(dados["divergencias_pessoais"])}')
        for d in dados['divergencias_pessoais']:
            print(f'     [{d["severidade"]}] {d["campo"]}: doc={d["doc"]} vs hiscre={d["hiscre"]}')
    else:
        print(f'  ✓ Doc bate com HISCRE')
    if dados['alertas']:
        for a in dados['alertas']:
            print(f'  ⚠ {a[:240]}')

    # Gerar
    output = os.path.join(pasta, caso['docx_out'])
    res = gerar_inicial_am(dados, output)
    print(f'  ✓ Inicial: {res["modificados"]} modif, residuais: {res["residuais"] or "nenhum"}')
    return res


if __name__ == '__main__':
    for caso in CASOS:
        processar(caso)
    print('\n✅ FIM')
