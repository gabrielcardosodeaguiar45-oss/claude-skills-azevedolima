"""
Teste 3 — Tese RCC (Reserva de Cartão Consignado).
Gera 2 templates: COM-escritorio (Tiago/Eduardo) + SEM-escritorio (Patrick/Gabriel/Alexandre).

Estrutura idêntica ao RMC; muda só "RMC" → "RCC", "RESERVA DE MARGEM CONSIGNÁVEL" →
"Reserva de Cartão Consignado", dano moral R$ 10.000 fixo (singular ou plural conforme nº contratos).
"""
import sys, os, io, shutil, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'scripts')

from scripts.docx_replace import (
    substituir_em_docx, inserir_paragrafo_antes, aplicar_timbrado_neutro,
)
from docx import Document

BASE = os.path.dirname(__file__)
ASSETS = os.path.join(BASE, 'assets')

COM_BASE = os.path.join(ASSETS, '__BASE_com-escritorio__modelo-rcc-Tiago-AL-BMG.docx')
COM_TEMPLATE = os.path.join(ASSETS, 'template_rcc__com-escritorio.docx')
SEM_TEMPLATE = os.path.join(ASSETS, 'template_rcc__sem-escritorio.docx')
TIMBRADO_NEUTRO = os.path.join(ASSETS, '__BASE_sem-escritorio__modelo-original.docx')


# Substituições granulares (preservar fontes; ordem: longas → curtas)
mapa_rcc = {
    # ENDEREÇO ESCRITÓRIO (substitui PRIMEIRO antes de outras)
    'com escritório na Rua Nossa Senhora da Salete, nº 597, Sala 04, Térreo, Bairro Itapoã, Arapiraca-AL':
        'com escritório na {{ESCRITORIO_ENDERECO_COMPOSTO}}',

    # ENDEREÇO RESIDENCIAL CLIENTE (string longa)
    'residente e domiciliada à Rua Marechal Deodoro da Fonseca, nº 121, bairro Centro, Município de Girau do Ponciano, CEP 57.360-000':
        'residente e {{DOMICILIADO_A}} na {{CLIENTE_LOGRADOURO}}, bairro {{CLIENTE_BAIRRO}}, em {{CLIENTE_MUNICIPIO}}/{{CLIENTE_UF}}, CEP {{CLIENTE_CEP}}',

    # Qualificação cliente — CPF + RG + órgão (cirúrgico)
    'aposentado, inscrito no CPF sob o nº593.964.074-53, Cédula de Identidade nº 690.875 SSP-AL':
        '{{CLIENTE_PROFISSAO}}, {{INSCRITO_A}} no CPF sob o nº {{CLIENTE_CPF}}, Cédula de Identidade nº {{CLIENTE_RG}}, órgão expedidor {{CLIENTE_RG_ORGAO}}',

    # Cabeçalho data
    'Arapiraca/AL, 19 de dezembro de 2025': '{{CIDADE_ASSINATURA}}/{{UF_ASSINATURA}}, {{DATA_EXTENSO}}',

    # Endereçamento ao banco
    'À Ouvidoria do BANCO BMG S.A.': 'À Ouvidoria do {{BANCO_NOME_QUALIFICADO}}',
    'CNPJ: 61.186.680/0001-74,': 'CNPJ: {{BANCO_CNPJ}},',
    'Rua do Sol, 117, Centro, CEP 57020-070, Maceió/AL':
        '{{BANCO_LOGRADOURO}}, {{BANCO_BAIRRO}}, CEP {{BANCO_CEP}}, {{BANCO_MUNICIPIO}}/{{BANCO_UF}}',

    # Strings curtas
    'JOSÉ CÍCERO DA SILVA': '{{CLIENTE_NOME}}',
    'brasileiro,': '{{CLIENTE_NACIONALIDADE_GENERO}},',
    'divorciado,': '{{CLIENTE_ESTADO_CIVIL}},',
    'por intermédio de seu advogado': 'por intermédio de {{SEU_SUA_ADVOGADO_A}}',
    'Tiago Azevedo Lima': '{{ADVOGADO_NOME}}',
    'OAB/AL  20906A': '{{ADVOGADO_OAB_UF}}',
    'TIAGO DE AZEVEDO LIMA': '{{ADVOGADO_NOME_MAIUSCULO}}',
    'OAB/AL 20906A': '{{ADVOGADO_OAB_UF}}',

    # Cancelamento
    'O Cancelamento definitivo do Contrato nº 15076520':
        'O Cancelamento definitivo do(s) Contrato(s) nº {{CONTRATO_NUMEROS}}',

    # Dano moral RCC = R$ 10.000,00 (dez mil reais) — igual ao RMC
    'no valor de R$ 10.000,00 (dez mil reais)':
        'no valor de R$ 10.000,00 (dez mil reais) por cada contrato',
}


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


def map_genero_advogado(genero_adv):
    if genero_adv.upper() == 'F':
        return {'{{SEU_SUA_ADVOGADO_A}}': 'sua advogada'}
    return {'{{SEU_SUA_ADVOGADO_A}}': 'seu advogado'}


def _patch_textbox_wrap(docx_path):
    """Substitui wrapSquare bothSides → wrapTopAndBottom (evita quebra do nome)."""
    with zipfile.ZipFile(docx_path, 'r') as z:
        contents = {n: z.read(n) for n in z.namelist()}
    if 'word/document.xml' in contents:
        xml = contents['word/document.xml'].decode('utf-8')
        xml = xml.replace('<wp:wrapSquare wrapText="bothSides"/>', '<wp:wrapTopAndBottom/>')
        contents['word/document.xml'] = xml.encode('utf-8')
    with zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in contents.items():
            z.writestr(name, data)


# === ETAPA 1: criar template COM ===
print('=== ETAPA 1A: Template RCC COM escritório ===')
rel = substituir_em_docx(COM_BASE, mapa_rcc, COM_TEMPLATE)
print(f'  Substituições: {rel["total_substituicoes"]}')
print(f'  Parágrafos vazios removidos: {rel["paragrafos_vazios_removidos"]}')
_patch_textbox_wrap(COM_TEMPLATE)
print(f'  Wrap textbox patcheado')

# === ETAPA 2: criar template SEM (clonar COM + trocar timbrado) ===
print('\n=== ETAPA 1B: Template RCC SEM escritório (clone COM + timbrado neutro) ===')
aplicar_timbrado_neutro(COM_TEMPLATE, TIMBRADO_NEUTRO, SEM_TEMPLATE)
print(f'  Template SEM gerado: {os.path.basename(SEM_TEMPLATE)}')

# === ETAPA 3: gerar testes COM e SEM ===
cliente_F = {
    '{{CIDADE_ASSINATURA}}': 'Arapiraca',
    '{{UF_ASSINATURA}}': 'AL',
    '{{DATA_EXTENSO}}': '15 de maio de 2026',

    '{{BANCO_NOME_QUALIFICADO}}': 'BANCO BMG S.A., sociedade anônima',
    '{{BANCO_CNPJ}}': '61.186.680/0001-74',
    '{{BANCO_LOGRADOURO}}': 'Avenida Presidente Juscelino Kubitschek, nº 1830',
    '{{BANCO_BAIRRO}}': 'Vila Nova Conceição',
    '{{BANCO_CEP}}': '04.543-900',
    '{{BANCO_MUNICIPIO}}': 'São Paulo',
    '{{BANCO_UF}}': 'SP',

    '{{CLIENTE_NOME}}': 'MARIA APARECIDA',
    '{{CLIENTE_ESTADO_CIVIL}}': 'viúva',
    '{{CLIENTE_PROFISSAO}}': 'aposentada',
    '{{CLIENTE_CPF}}': '000.111.222-33',
    '{{CLIENTE_RG}}': '1.234.567',
    '{{CLIENTE_RG_ORGAO}}': 'SSP/AL',
    '{{CLIENTE_LOGRADOURO}}': 'Rua Exemplo das Flores, nº 100',
    '{{CLIENTE_BAIRRO}}': 'Centro',
    '{{CLIENTE_MUNICIPIO}}': 'Maceió',
    '{{CLIENTE_UF}}': 'AL',
    '{{CLIENTE_CEP}}': '57000-000',
    '{{ESCRITORIO_ENDERECO_COMPOSTO}}': 'Rua Frei Rogério, 541, Centro, Joaçaba/SC, CEP 89600-000, e unidade de apoio em Rua Nossa Senhora da Salete, 597, Sala 04, Itapuã, Arapiraca/AL, CEP 57314-175',

    '{{NOME_BANCO_CONTRATO}}': 'BANCO BMG S.A.',
    '{{CONTRATO_NUMEROS}}': '15076520',

    **map_genero_cliente('F'),
}

# Teste COM
TESTE_COM = os.path.join(BASE, '_TESTE_rcc__com-escritorio.docx')
cliente_com = {
    **cliente_F,
    '{{ADVOGADO_NOME}}': 'Tiago de Azevedo Lima',
    '{{ADVOGADO_NOME_MAIUSCULO}}': 'TIAGO DE AZEVEDO LIMA',
    '{{ADVOGADO_OAB_UF}}': 'OAB/AL 20906A',
    **map_genero_advogado('M'),
}
print('\n=== ETAPA 2A: Gerando teste RCC COM ===')
rel = substituir_em_docx(COM_TEMPLATE, cliente_com, TESTE_COM)
print(f'  Substituições: {rel["total_substituicoes"]}')

# Teste SEM
TESTE_SEM = os.path.join(BASE, '_TESTE_rcc__sem-escritorio.docx')
cliente_sem = {
    **cliente_F,
    '{{CIDADE_ASSINATURA}}': 'Maués',
    '{{UF_ASSINATURA}}': 'AM',
    '{{ADVOGADO_NOME}}': 'Patrick Willian da Silva',
    '{{ADVOGADO_NOME_MAIUSCULO}}': 'PATRICK WILLIAN DA SILVA',
    '{{ADVOGADO_OAB_UF}}': 'OAB/AM A2638',
    **map_genero_advogado('M'),
}
print('\n=== ETAPA 2B: Gerando teste RCC SEM ===')
rel = substituir_em_docx(SEM_TEMPLATE, cliente_sem, TESTE_SEM)
print(f'  Substituições: {rel["total_substituicoes"]}')

# Verificação
import re
print('\n=== Placeholders pendentes ===')
for label, path in [('COM', TESTE_COM), ('SEM', TESTE_SEM)]:
    d = Document(path)
    restantes = []
    for p in d.paragraphs:
        m = re.findall(r'\{\{[A-Z_]+\}\}', p.text)
        restantes.extend(m)
    if restantes:
        print(f'  {label}: {set(restantes)}')
    else:
        print(f'  {label}: tudo preenchido!')

print(f'\nTestes salvos em:')
print(f'  {TESTE_COM}')
print(f'  {TESTE_SEM}')
