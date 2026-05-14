"""Gera 9 iniciais FICTÍCIAS (1 por template) para revisão visual.

Estratégia: usa HISCONs reais que ainda existem na máquina (FABIO, EXEMPLA EDMUNDA)
mas força combinações distintas para exercitar TODOS os 9 templates do vault.

Saída: pasta `_DEMOS_FICTICIAS/` na raiz do APP - NÃO CONTRATADO/
"""
import io, os, sys, shutil
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_generico import gerar_inicial_padrao
from perfis_juridicos import PERFIS

OUT_DIR = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\_DEMOS_FICTICIAS'
os.makedirs(OUT_DIR, exist_ok=True)


# ============================================================
#  AUTORAS FICTÍCIAS (mas usando docs/HISCONs reais como base)
# ============================================================

# Exempla Edmunda real (AL — idosa, casada, beneficiária)
AUTORA_AL = {
    'nome': 'JOANA EXEMPLO DOS SANTOS',
    'nacionalidade': 'brasileira', 'estado_civil': 'casada',
    'profissao': 'aposentada', 'cpf': '000.000.007-17',
    'rg': '1000005-5', 'orgao_expedidor': 'SSP/AL',
    'data_nascimento': datetime(1965, 4, 13),
    'logradouro': 'Rua Projetada', 'numero': '07',
    'bairro': 'Campo Alegre', 'cidade': 'Jaramataia',
    'uf': 'AL', 'cep': '57425-000',
}

# Fabio real (AM — não-idoso, solteiro, aposentado)
AUTORA_AM = {
    'nome': 'FÁBIO MARINHO DE OLIVEIRA',
    'nacionalidade': 'brasileiro', 'estado_civil': 'solteiro',
    'profissao': 'aposentado', 'cpf': '000.000.003-13',
    'rg': '1000001-1', 'orgao_expedidor': 'SSP/AM',
    'data_nascimento': datetime(1980, 11, 20),
    'logradouro': 'Ramal da Lixeira', 'numero': 's/nº',
    'bairro': 'Zona Rural', 'cidade': 'Presidente Figueiredo',
    'uf': 'AM', 'cep': '69.735-000',
}

# Fictícia BA (autora hipotética usando HISCON do Fabio como base)
AUTORA_BA = {
    'nome': 'MARIA APARECIDA DE SOUZA',
    'nacionalidade': 'brasileira', 'estado_civil': 'viúva',
    'profissao': 'aposentada', 'cpf': '000.000.008-18',
    'rg': '1000006-6', 'orgao_expedidor': 'SSP/BA',
    'data_nascimento': datetime(1958, 6, 15),  # 67 anos = idosa
    'logradouro': 'Rua das Flores', 'numero': '100',
    'bairro': 'Centro', 'cidade': 'Camaçari',
    'uf': 'BA', 'cep': '42.800-000',
}


# ============================================================
#  9 DEMOS — 1 POR TEMPLATE
# ============================================================
DEMOS = [
    # ---- BA Federal (3 templates) ----
    {
        'label': 'BA-FEDERAL — base (1 contrato AVN inativo)',
        'perfil_chave': 'BA_FEDERAL',
        'pasta_cliente': r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\FABIO MARINHO DE OLIVEIRA - Ruth\C6 CONSIGNADO',
        'autora': AUTORA_BA,
        'comarca': 'Salvador',
        'numeros_contrato_explicitos': ['90135039498'],
        'output_path': os.path.join(OUT_DIR, 'DEMO_BA-Federal_base.docx'),
    },
    {
        'label': 'BA-FEDERAL — multiplos (N contratos AVN)',
        'perfil_chave': 'BA_FEDERAL',
        'pasta_cliente': r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\FABIO MARINHO DE OLIVEIRA - Ruth\C6 CONSIGNADO',
        'autora': AUTORA_BA,
        'comarca': 'Salvador',
        # Forçar 2+ contratos para usar template MULT (tem 7 contratos do C6 no HISCON)
        'numeros_contrato_explicitos': ['90135039498', '0093571320'],
        'output_path': os.path.join(OUT_DIR, 'DEMO_BA-Federal_multiplos.docx'),
    },
    {
        'label': 'BA-FEDERAL — refin ativo (REFIN)',
        'perfil_chave': 'BA_FEDERAL',
        'pasta_cliente': r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\FABIO MARINHO DE OLIVEIRA - Ruth\AGIBANK',
        'autora': AUTORA_BA,
        'comarca': 'Salvador',
        # Esse contrato 1527829615 do AGIBANK é REFIN ATIVO (validado anteriormente)
        'numeros_contrato_explicitos': ['1527829615'],
        'output_path': os.path.join(OUT_DIR, 'DEMO_BA-Federal_refin.docx'),
    },

    # ---- AM Estadual (2 templates) ----
    {
        'label': 'AM-ESTADUAL — base (1 contrato AVN)',
        'perfil_chave': 'AM_ESTADUAL',
        'pasta_cliente': r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\FABIO MARINHO DE OLIVEIRA - Ruth\C6 CONSIGNADO',
        'autora': AUTORA_AM,
        'comarca': 'Presidente Figueiredo',
        'numeros_contrato_explicitos': ['90135039498'],
        'output_path': os.path.join(OUT_DIR, 'DEMO_AM-Estadual_base.docx'),
    },
    {
        'label': 'AM-ESTADUAL — refin (REFIN ATIVO)',
        'perfil_chave': 'AM_ESTADUAL',
        'pasta_cliente': r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\FABIO MARINHO DE OLIVEIRA - Ruth\AGIBANK',
        'autora': AUTORA_AM,
        'comarca': 'Presidente Figueiredo',
        'numeros_contrato_explicitos': ['1527829615'],
        'output_path': os.path.join(OUT_DIR, 'DEMO_AM-Estadual_refin.docx'),
    },

    # ---- AL Federal (2 templates) ----
    {
        'label': 'AL-FEDERAL — 1 banco (Bradesco)',
        'perfil_chave': 'AL_FEDERAL',
        'pasta_cliente': r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\JOANA EXEMPLO DOS SANTOS',
        'autora': AUTORA_AL,
        'comarca': 'Arapiraca',
        'numeros_contrato_explicitos': ['0123527065102'],
        'output_path': os.path.join(OUT_DIR, 'DEMO_AL-Federal_1banco.docx'),
    },
    {
        'label': 'AL-FEDERAL — 2 bancos (Bradesco + outro)',
        'perfil_chave': 'AL_FEDERAL',
        'pasta_cliente': r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\JOANA EXEMPLO DOS SANTOS',
        'autora': AUTORA_AL,
        'comarca': 'Arapiraca',
        # Apenas 1 banco real disponível na pasta — vai cair no template 1banco.
        # Para um teste 2bancos real, precisaria de uma pasta com 2 bancos.
        # NOTA: o pipeline AL detecta n_bancos automaticamente; aqui forçamos
        # via duplicação fictícia para exercitar o template 2bancos.
        'numeros_contrato_explicitos': ['0123527065102', '0123466323825'],
        'output_path': os.path.join(OUT_DIR, 'DEMO_AL-Federal_2bancos_TENTATIVA.docx'),
    },

    # ---- AL Estadual (2 templates) ----
    {
        'label': 'AL-ESTADUAL — 1 banco (forçar foro estadual)',
        'perfil_chave': 'AL_ESTADUAL',
        'pasta_cliente': r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\JOANA EXEMPLO DOS SANTOS',
        'autora': AUTORA_AL,
        'comarca': 'Arapiraca',
        'numeros_contrato_explicitos': ['0123527065102'],
        'output_path': os.path.join(OUT_DIR, 'DEMO_AL-Estadual_1banco.docx'),
    },
    {
        'label': 'AL-ESTADUAL — 2 bancos',
        'perfil_chave': 'AL_ESTADUAL',
        'pasta_cliente': r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\JOANA EXEMPLO DOS SANTOS',
        'autora': AUTORA_AL,
        'comarca': 'Arapiraca',
        'numeros_contrato_explicitos': ['0123527065102', '0123466323825'],
        'output_path': os.path.join(OUT_DIR, 'DEMO_AL-Estadual_2bancos_TENTATIVA.docx'),
    },
]


def main():
    print(f'\n{"="*70}')
    print(f'  GERANDO 9 INICIAIS DEMO em {OUT_DIR}')
    print(f'{"="*70}\n')

    sucessos = 0
    falhas = []

    for i, demo in enumerate(DEMOS, 1):
        label = demo.pop('label')
        print(f'[{i}/9] {label}')
        try:
            res = gerar_inicial_padrao(**demo)
            r = res['resultado']
            d = res['dados']
            print(f'    ✓ Banco: {d.get("banco_reu", {}).get("nome", "?")}')
            print(f'    ✓ Contratos: {len(d.get("contratos_questionados") or [])}')
            print(f'    ✓ Modificações: {r.get("modificados", 0)}')
            print(f'    ✓ Output: {os.path.basename(res["output"])}')
            sucessos += 1
        except Exception as e:
            print(f'    ❌ FALHOU: {type(e).__name__}: {str(e)[:200]}')
            falhas.append((label, str(e)[:200]))
        print()

    print(f'\n{"="*70}')
    print(f'  RESUMO: {sucessos}/9 sucessos')
    print(f'{"="*70}')
    if falhas:
        print('\nFalhas:')
        for label, err in falhas:
            print(f'  - {label}: {err}')


if __name__ == '__main__':
    main()
