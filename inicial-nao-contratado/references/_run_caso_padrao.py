"""Runner padrão — copie este arquivo para cada caso novo.

USO:
    1. Copie como `_run_<NOME_CLIENTE>.py`
    2. Preencha o dict CASO abaixo (perfil, pasta, autora, comarca, contratos)
    3. Rode: `python _run_<NOME_CLIENTE>.py`

A skill se encarrega do resto:
    - Identifica banco-réu pelo HISCON (ou pasta)
    - Filtra contratos pela procuração (ABORTA se não conseguir)
    - Aplica fontes Segoe UI Bold no autor/banco/INSS
    - Escolhe empréstimo vs refinanciamento nos pedidos
    - Mantém prioridade idoso só quando autor é idoso
    - Aplica grifo amarelo em todas as alterações
    - Gera DOCX no caminho informado
"""
import io, os, sys
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_generico import gerar_inicial_padrao


# ============================================================
#  PREENCHA AQUI O CASO
# ============================================================

CASO = {
    # Chave do perfil de jurisdição (ver perfis_juridicos.PERFIS):
    #   'BA_FEDERAL' / 'AM_ESTADUAL' / 'AL_FEDERAL' / 'AL_ESTADUAL'
    'perfil_chave': 'AL_FEDERAL',

    # Pasta do cliente com HISCON, procurações, RG, comprovante etc.
    'pasta_cliente': r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\NOME DO CLIENTE',

    # Comarca (deve estar em comarcas_validas do perfil)
    'comarca': 'Arapiraca',

    # Números de contrato OUTORGADOS na procuração (lidos manualmente do PDF
    # se o OCR falhar). SEMPRE preencher para evitar pipeline tentar/falhar.
    'numeros_contrato_explicitos': ['XXXXXXXXXX'],

    # Qualificação da autora (extraída via OCR de RG, CPF, comprovante)
    'autora': {
        'nome':              'NOME COMPLETO DA AUTORA',
        'nacionalidade':     'brasileira',          # ou 'brasileiro'
        'estado_civil':      'casada',               # ou ''
        'profissao':         'aposentada',
        'cpf':               'XXX.XXX.XXX-XX',
        'rg':                '1000003-3',
        'orgao_expedidor':   'SSP/AL',
        'data_nascimento':   datetime(1960, 1, 1),  # crítico para detectar idoso
        'logradouro':        'Rua X',
        'numero':            '123',
        'bairro':            'Centro',
        'cidade':            'Arapiraca',
        'uf':                'AL',
        'cep':               'XXXXX-XXX',
    },

    # Output (default = pasta_cliente/INICIAL_<perfil>.docx)
    'output_path': None,

    # Overrides opcionais (None = usar default do perfil)
    'forcar_procurador': None,                       # 'tiago' / 'alexandre' / etc.
    'forcar_foro': None,                             # AL: 'federal' / 'estadual'
    'representante_legal': None,                     # AM: dict da mãe quando autor é menor
    'assume_com_deposito': False,                    # AL: True só se HISCRE confirmar
}


def main():
    print(f'████████████ {CASO["autora"]["nome"]} | {CASO["perfil_chave"]} ████████████')
    res = gerar_inicial_padrao(**CASO)

    dados = res['dados']
    print(f'  Perfil:        {res["perfil"]}')
    print(f'  Banco-réu:     {dados.get("banco_reu", {}).get("nome", "?")}')
    print(f'  Contratos:     {len(dados.get("contratos_questionados") or [])}')
    print(f'  Output:        {res["output"]}')

    r = res['resultado']
    print(f'  Modificações:  {r.get("modificados", 0)}')
    print(f'  Residuais:     {r.get("residuais") or "nenhum"}')


if __name__ == '__main__':
    main()
