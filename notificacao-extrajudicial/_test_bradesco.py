"""
Testes 4-7 — Teses BRADESCO (Encargos, Tarifas, Capitalização, Pagamento Eletrônico).

Cada tese tem:
  - BASE: assets/__BASE_sem-escritorio__bradesco-{slug}.docx (Patrick AM)
  - Template SEM: assets/template_bradesco-{slug}__sem-escritorio.docx
  - Template COM: assets/template_bradesco-{slug}__com-escritorio.docx
                  (gerado clonando o SEM e trocando headers/footers para o
                   BASE COM com logo Tiago/Eduardo)

PE (Pagamento Eletrônico) tem complexidade extra: parágrafos de destinatário
TERCEIRO (EAGLE no exemplo). Esse template usa mais um conjunto de placeholders
{{TERCEIRO_*}} que devem ser preenchidos pela skill com dados do terceiro
recebedor real (consultando o vault em terceiros-pagamento-eletronico/<slug>.md).

------------------------------------------------------------------------------
ATUALIZAÇÃO 13/05/2026 (Gabriel):
O parágrafo "Tais descontos vêm ocorrendo, em síntese, no período aproximado
de {{DATA_INICIAL}} a {{DATA_FINAL}}, totalizando até o momento
{{NUMERO_DESCONTOS}} lançamentos e um montante de R$ {{VALOR_TOTAL}}..."
foi REMOVIDO dos 4 templates Bradesco (e dos 4 __BASE_). O procurador prefere
demonstrar os descontos diretamente via tabela/extrato anexo, sem repetir
período/total em texto corrido.

Por consequência, os mapas abaixo CONTÊM substituições que tentam parametrizar
DATA_INICIAL/DATA_FINAL/NUMERO_DESCONTOS/VALOR_TOTAL/RUBRICAS — essas
substituições ficam INERTES quando os BASE não têm mais o parágrafo (não
encontram match e nada acontece). Mantidas como histórico/referência. Se você
restaurar os BASE da versão anterior (.bak_20260513_091514) os mapas voltam
a funcionar normalmente.
------------------------------------------------------------------------------
"""
import sys, os, io, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'scripts')

from scripts.docx_replace import substituir_em_docx
from docx import Document

BASE_DIR = os.path.dirname(__file__)
ASSETS = os.path.join(BASE_DIR, 'assets')


def map_genero_cliente(genero):
    if genero.upper() == 'F':
        return {
            '{{CLIENTE_NACIONALIDADE_GENERO}}': 'brasileira',
            '{{INSCRITO_A}}': 'inscrita',
            '{{DOMICILIADO_A}}': 'domiciliada',
        }
    return {
        '{{CLIENTE_NACIONALIDADE_GENERO}}': 'brasileiro',
        '{{INSCRITO_A}}': 'inscrito',
        '{{DOMICILIADO_A}}': 'domiciliado',
    }


def map_genero_advogado(g):
    return {'{{SEU_SUA_ADVOGADO_A}}': 'sua advogada' if g.upper() == 'F' else 'seu advogado'}


# ===================== Mapas de substituição =====================
# Comum a todas as teses Bradesco — qualificação Bradesco e endereço
banco_bradesco_substituir = {
    # Banco notificado
    'À Ouvidoria do Banco Bradesco S. A.': 'À Ouvidoria do {{BANCO_NOME_QUALIFICADO}}',
    'CNPJ: 60.746.948.0001-12': 'CNPJ: {{BANCO_CNPJ}}',
    'Rua Cidade de Deus': '{{BANCO_LOGRADOURO}}',
    'Vila Yara, S/N': '{{BANCO_BAIRRO}}',
    'CEP 060029-9000– Osasco/SP': 'CEP {{BANCO_CEP}} – {{BANCO_MUNICIPIO}}/{{BANCO_UF}}',

    # Banco mencionado no corpo
    'Banco do Bradesco': '{{NOME_BANCO_CONTRATO}}',
    'Banco Bradesco': '{{NOME_BANCO_CONTRATO}}',
    'banco Bradesco': '{{NOME_BANCO_CONTRATO}}',

    # Advogado/escritório (rodapé/assinatura)
    'Patrick Willian da Silva': '{{ADVOGADO_NOME}}',
    'OAB/AM A2638': '{{ADVOGADO_OAB_UF}}',
}


def mapa_encargos():
    """Mapa de substituições para a tese de Encargos (José Nogueira)."""
    return {
        **banco_bradesco_substituir,
        # Cabeçalho data
        'Caapiranga/AM, 5 de fevereiro de 2026': '{{CIDADE_ASSINATURA}}/{{UF_ASSINATURA}}, {{DATA_EXTENSO}}',
        # Cliente (qualificação real → placeholders)
        'JOSÉ NOGUEIRA TAVARES': '{{CLIENTE_NOME}}',
        'brasileiro,': '{{CLIENTE_NACIONALIDADE_GENERO}},',
        'casado,': '{{CLIENTE_ESTADO_CIVIL}},',
        'aposentado, inscrito no CPF sob o nº 073.526.972-68, Cédula de Identidade nº 0545791-2, órgão expedidor SSP/MG':
            '{{CLIENTE_PROFISSAO}}, {{INSCRITO_A}} no CPF sob o nº {{CLIENTE_CPF}}, Cédula de Identidade nº {{CLIENTE_RG}}, órgão expedidor {{CLIENTE_RG_ORGAO}}',
        # Dados específicos do caso real (período/valor/lançamentos) → placeholders
        'no período aproximado de 26/06/2018 a 28/10/2024':
            'no período aproximado de {{DATA_INICIAL}} a {{DATA_FINAL}}',
        'totalizando até o momento 30 lançamentos':
            'totalizando até o momento {{NUMERO_DESCONTOS}} lançamentos',
        'um montante de R$ 4.447,80':
            'um montante de R$ {{VALOR_TOTAL}}',
        # Rubricas (já consta no template Encargos como literais — só placeholderizamos)
        '"MORA CREDITO PESSOAL", "ENCARGOS LIMITE DE CRED"': '{{RUBRICAS}}',
        '"MORA CREDITO PESSOAL", \"ENCARGOS LIMITE DE CRED\"': '{{RUBRICAS}}',
        '“MORA CREDITO PESSOAL”, "ENCARGOS LIMITE DE CRED”': '{{RUBRICAS}}',
        # Por intermédio do advogado
        'por intermédio de seu advogado': 'por intermédio de {{SEU_SUA_ADVOGADO_A}}',
    }


def mapa_tarifas():
    """Mapa para Tarifas (Leila Soares)."""
    return {
        **banco_bradesco_substituir,
        'Cidade/UF, 1 de dezembro de 2025': '{{CIDADE_ASSINATURA}}/{{UF_ASSINATURA}}, {{DATA_EXTENSO}}',
        'Maués/AM, 1 de dezembro de 2025': '{{CIDADE_ASSINATURA}}/{{UF_ASSINATURA}}, {{DATA_EXTENSO}}',
        'LEILA SOARES DA SILVA': '{{CLIENTE_NOME}}',
        'brasileira,': '{{CLIENTE_NACIONALIDADE_GENERO}},',
        'viúva,': '{{CLIENTE_ESTADO_CIVIL}},',
        'aposentada, inscrita no CPF sob o nº 691.802.376-49, Cédula de Identidade nº 6840337, órgão expedidor SSP/MG':
            '{{CLIENTE_PROFISSAO}}, {{INSCRITO_A}} no CPF sob o nº {{CLIENTE_CPF}}, Cédula de Identidade nº {{CLIENTE_RG}}, órgão expedidor {{CLIENTE_RG_ORGAO}}',
        # Placeholders já legacy → padrão canônico
        '[DATA INICIAL]': '{{DATA_INICIAL}}',
        '[DATA FINAL]': '{{DATA_FINAL}}',
        '[NÚMERO DE DESCONTOS]': '{{NUMERO_DESCONTOS}}',
        '[VALOR TOTAL]': '{{VALOR_TOTAL}}',
        # Rubrica fixa para Tarifas
        '"tarifa bancária"': '{{RUBRICAS}}',
        '“tarifa bancária”': '{{RUBRICAS}}',
        'por intermédio de seu advogado': 'por intermédio de {{SEU_SUA_ADVOGADO_A}}',
    }


def mapa_capitalizacao():
    """Mapa para Título de Capitalização (Leila Soares)."""
    return {
        **banco_bradesco_substituir,
        'Cidade/UF, 1 de dezembro de 2025': '{{CIDADE_ASSINATURA}}/{{UF_ASSINATURA}}, {{DATA_EXTENSO}}',
        'Maués/AM, 1 de dezembro de 2025': '{{CIDADE_ASSINATURA}}/{{UF_ASSINATURA}}, {{DATA_EXTENSO}}',
        'LEILA SOARES DA SILVA': '{{CLIENTE_NOME}}',
        'brasileira,': '{{CLIENTE_NACIONALIDADE_GENERO}},',
        'viúva,': '{{CLIENTE_ESTADO_CIVIL}},',
        'aposentada, inscrita no CPF sob o nº 691.802.376-49, Cédula de Identidade nº 6840337, órgão expedidor SSP/MG':
            '{{CLIENTE_PROFISSAO}}, {{INSCRITO_A}} no CPF sob o nº {{CLIENTE_CPF}}, Cédula de Identidade nº {{CLIENTE_RG}}, órgão expedidor {{CLIENTE_RG_ORGAO}}',
        '[DATA INICIAL]': '{{DATA_INICIAL}}',
        '[DATA FINAL]': '{{DATA_FINAL}}',
        '[NÚMERO DE DESCONTOS]': '{{NUMERO_DESCONTOS}}',
        '[VALOR TOTAL]': '{{VALOR_TOTAL}}',
        '"Título de Capitalização"': '{{RUBRICAS}}',
        '“Título de Capitalização”': '{{RUBRICAS}}',
        'por intermédio de seu advogado': 'por intermédio de {{SEU_SUA_ADVOGADO_A}}',
    }


def mapa_pe():
    """Mapa para Pagamento Eletrônico (Sebastião Furtado, terceiro EAGLE)."""
    return {
        **banco_bradesco_substituir,
        'Barreirinha/AM, 3 de março de 2026': '{{CIDADE_ASSINATURA}}/{{UF_ASSINATURA}}, {{DATA_EXTENSO}}',
        # Cliente
        'SEBASTIÃO FURTADO DA SILVA': '{{CLIENTE_NOME}}',
        'brasileiro,': '{{CLIENTE_NACIONALIDADE_GENERO}},',
        'beneficiário, inscrito no CPF sob o nº 618.371.562-04':
            '{{CLIENTE_PROFISSAO}}, {{INSCRITO_A}} no CPF sob o nº {{CLIENTE_CPF}}, Cédula de Identidade nº {{CLIENTE_RG}}, órgão expedidor {{CLIENTE_RG_ORGAO}}',
        'residente e domiciliado na Rua Augusto Montenegro, s/nº, bairro Centro, Município de Barreirinha, CEP 69.':
            'residente e {{DOMICILIADO_A}} na {{CLIENTE_LOGRADOURO}}, bairro {{CLIENTE_BAIRRO}}, em {{CLIENTE_MUNICIPIO}}/{{CLIENTE_UF}}, CEP {{CLIENTE_CEP}}',
        # Terceiro recebedor (EAGLE)
        'À Ouvidoria da EAGLE SOCIDADE DE CRÉDITO DIRETO S.A.': 'À Ouvidoria da {{TERCEIRO_NOME}}',
        'CNPJ: 45.745.141/0001-19': 'CNPJ: {{TERCEIRO_CNPJ}}',
        'Rua Furriel Luiz Antônio de Vargas': '{{TERCEIRO_LOGRADOURO}}',
        'Bela Vista, nº 250, 14º andar, Sala 1403': '{{TERCEIRO_BAIRRO}}',
        'CEP 90470-130– Porto Alegre/RS': 'CEP {{TERCEIRO_CEP}} – {{TERCEIRO_MUNICIPIO}}/{{TERCEIRO_UF}}',
        # Dados do extrato
        'no período aproximado de 28/12/2023 a 28/06/2024':
            'no período aproximado de {{DATA_INICIAL}} a {{DATA_FINAL}}',
        'totalizando até o momento 6 lançamentos':
            'totalizando até o momento {{NUMERO_DESCONTOS}} lançamentos',
        'um montante de R$ 13.792,22':
            'um montante de R$ {{VALOR_TOTAL}}',
        # Rubrica EAGLE (vai virar placeholder genérico {{RUBRICA_PE}})
        '"PAGTO ELETRON COBRANÇA EAGLE SOCIEDADE DE CREDITO DIRET"': '{{RUBRICAS}}',
        '“PAGTO ELETRON COBRANÇA EAGLE SOCIEDADE DE CREDITO DIRET”': '{{RUBRICAS}}',
        'por intermédio de seu advogado': 'por intermédio de {{SEU_SUA_ADVOGADO_A}}',
    }


# ===================== Cliente fictício para teste =====================
cliente_F = {
    '{{CIDADE_ASSINATURA}}': 'Maués',
    '{{UF_ASSINATURA}}': 'AM',
    '{{DATA_EXTENSO}}': '15 de maio de 2026',

    '{{BANCO_NOME_QUALIFICADO}}': 'BANCO BRADESCO S/A, sociedade anônima',
    '{{BANCO_CNPJ}}': '60.746.948/0001-12',
    '{{BANCO_LOGRADOURO}}': 'Cidade de Deus',
    '{{BANCO_BAIRRO}}': 'Vila Yara',
    '{{BANCO_CEP}}': '06029-900',
    '{{BANCO_MUNICIPIO}}': 'Osasco',
    '{{BANCO_UF}}': 'SP',
    '{{NOME_BANCO_CONTRATO}}': 'Banco Bradesco S/A',

    '{{CLIENTE_NOME}}': 'MARIA APARECIDA',
    '{{CLIENTE_ESTADO_CIVIL}}': 'viúva',
    '{{CLIENTE_PROFISSAO}}': 'aposentada',
    '{{CLIENTE_CPF}}': '000.111.222-33',
    '{{CLIENTE_RG}}': '1.234.567',
    '{{CLIENTE_RG_ORGAO}}': 'SSP/AM',
    '{{CLIENTE_LOGRADOURO}}': 'Rua Exemplo das Flores, nº 100',
    '{{CLIENTE_BAIRRO}}': 'Centro',
    '{{CLIENTE_MUNICIPIO}}': 'Maués',
    '{{CLIENTE_UF}}': 'AM',
    '{{CLIENTE_CEP}}': '69190-000',

    # Dados do extrato (Encargos/Tarifas/Capitalização/PE)
    '{{DATA_INICIAL}}': '01/01/2022',
    '{{DATA_FINAL}}': '31/12/2024',
    '{{NUMERO_DESCONTOS}}': '36',
    '{{VALOR_TOTAL}}': '5.420,33',
    '{{RUBRICAS}}': '"Tarifa exemplo"',

    # Terceiro PE (EAGLE)
    '{{TERCEIRO_NOME}}': 'EAGLE SOCIEDADE DE CRÉDITO DIRETO S.A.',
    '{{TERCEIRO_CNPJ}}': '45.745.141/0001-19',
    '{{TERCEIRO_LOGRADOURO}}': 'Rua Furriel Luiz Antônio de Vargas, nº 250',
    '{{TERCEIRO_BAIRRO}}': 'Bela Vista, 14º andar, Sala 1403',
    '{{TERCEIRO_CEP}}': '90470-130',
    '{{TERCEIRO_MUNICIPIO}}': 'Porto Alegre',
    '{{TERCEIRO_UF}}': 'RS',

    **map_genero_cliente('F'),
}

# Cliente Patrick AM (única versão das teses Bradesco — só protocola no AM)
cliente_sem = {
    **cliente_F,
    '{{ADVOGADO_NOME}}': 'Patrick Willian da Silva',
    '{{ADVOGADO_OAB_UF}}': 'OAB/AM A2638',
    **map_genero_advogado('M'),
}


# ===================== Loop principal =====================
teses = [
    ('encargos', mapa_encargos()),
    ('tarifas', mapa_tarifas()),
    ('capitalizacao', mapa_capitalizacao()),
    ('pe', mapa_pe()),
]

for slug, mapa in teses:
    print(f'\n{"="*60}')
    print(f'TESE BRADESCO-{slug.upper()}')
    print('='*60)

    BASE_SEM = os.path.join(ASSETS, f'__BASE_sem-escritorio__bradesco-{slug}.docx')
    TPL_SEM = os.path.join(ASSETS, f'template_bradesco-{slug}__sem-escritorio.docx')

    # As teses Bradesco são exclusivamente do AM (Patrick) — não há versão COM-escritório.

    # ETAPA 1: placeholderizar template SEM (BASE Patrick AM → template SEM)
    print(f'\n  ETAPA 1: Template SEM (placeholderizar)')
    rel = substituir_em_docx(BASE_SEM, mapa, TPL_SEM)
    print(f'    Substituições: {rel["total_substituicoes"]}')
    print(f'    Parágrafos vazios removidos: {rel["paragrafos_vazios_removidos"]}')

    # ETAPA 2: gerar teste com cliente fictício
    teste_sem = os.path.join(BASE_DIR, f'_TESTE_bradesco-{slug}__sem-escritorio.docx')
    print(f'  ETAPA 2: Teste SEM (Patrick AM)')
    rel = substituir_em_docx(TPL_SEM, cliente_sem, teste_sem)
    print(f'    Substituições: {rel["total_substituicoes"]}')

    # Verificação
    import re
    d = Document(teste_sem)
    restantes = []
    for p in d.paragraphs:
        m = re.findall(r'\{\{[A-Z_]+\}\}', p.text)
        restantes.extend(m)
    if restantes:
        print(f'  Placeholders pendentes: {set(restantes)}')
    else:
        print(f'  Placeholders pendentes: tudo preenchido!')

print('\n' + '='*60)
print('TODAS AS TESES BRADESCO GERADAS (apenas SEM — Patrick AM)')
print('='*60)
