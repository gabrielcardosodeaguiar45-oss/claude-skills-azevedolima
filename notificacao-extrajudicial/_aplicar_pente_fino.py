# -*- coding: utf-8 -*-
"""Aplica todas as correções do pente fino nos 10 templates de notificação.

Backup: <arquivo>.bak_pre_pente_fino
"""
import sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
sys.path.insert(0, r"C:\Users\gabri\.claude\skills\inicial-bradesco\references")
from docx import Document
from helpers_docx import substituir_in_run
from lxml import etree
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

ASSETS = Path(r"C:\Users\gabri\.claude\skills\notificacao-extrajudicial\assets")

# === FASE A: Substituições UNIVERSAIS (todos os 10) ===
SUBS_UNIVERSAIS = {
    # #2 padronizar nome do advogado (Title Case via {{ADVOGADO_NOME}})
    "{{ADVOGADO_NOME_MAIUSCULO}}":  "{{ADVOGADO_NOME}}",
    # #3 renomear placeholder do banco do meio do texto
    "{{NOME_BANCO_CONTRATO}}":      "{{BANCO_NOME}}",
    # #9 fornecedora → fornecedor (Banco é masculino)
    "Banco Notificado, na condição de fornecedora de serviços":
        "Banco Notificado, na condição de fornecedor de serviços",
    # #11 "por cada contrato" → "por contrato"
    "(quinze mil reais) por cada contrato":  "(quinze mil reais) por contrato",
    "(dez mil reais) por cada contrato":     "(dez mil reais) por contrato",
    # #15 S. A. redundante (já vem no nome canônico)
    "{{BANCO_NOME}} S. A., responde objetivamente":
        "{{BANCO_NOME}}, responde objetivamente",
    # #4 (parcial) hardcode feminino "da notificante" no fim do par dos pedidos
    "sobre o benefício previdenciário da notificante;":
        "sobre o benefício previdenciário {{DO_DA_NOTIFICANTE}} notificante;",
}


# === FASE B: Substituições POR TEMPLATE (correções específicas) ===
SUBS_POR_TEMPLATE = {
    # ---------- CONSIGNADO ----------
    'template_consignado-nao-contratado__sem-escritorio.docx': {
        # #18 "seu advogado" hardcoded → placeholder
        "por intermédio de seu advogado {{ADVOGADO_NOME}}":
            "por intermédio de {{SEU_SUA_ADVOGADO_A}} {{ADVOGADO_NOME}}",
        # #7 hardcode BANCO BRADESCO + contrato 0123528031058
        "supostamente celebrado com o BANCO BRADESCO S.A., sob o Contrato(s) nº 0123528031058":
            "supostamente celebrado com o {{BANCO_NOME}}, sob o(s) Contrato(s) nº {{CONTRATO_NUMEROS}}",
        # #8 data hardcoded "05/2025"
        "início dos descontos em 05/2025":
            "início dos descontos em {{CONTRATO_COMPETENCIA_INICIO}}",
    },
    # ---------- RCC ----------
    'template_rcc__com-escritorio.docx': {
        # #5 BANCO BMG + 15076520 hardcoded
        "(RCC) pelo BANCO BMG S.A, sob o contrato nº 15076520.":
            "(RCC) pelo {{BANCO_NOME}}, sob o(s) Contrato(s) nº {{CONTRATO_NUMEROS}}.",
        # #23 título errado
        "Cartão de Crédito RCC":  "Cartão de Benefício Consignado RCC",
    },
    'template_rcc__sem-escritorio.docx': {
        "(RCC) pelo BANCO BMG S.A, sob o contrato nº 15076520.":
            "(RCC) pelo {{BANCO_NOME}}, sob o(s) Contrato(s) nº {{CONTRATO_NUMEROS}}.",
        "Cartão de Crédito RCC":  "Cartão de Benefício Consignado RCC",
    },
    # ---------- BRADESCO TARIFAS ----------
    'template_bradesco-tarifas__sem-escritorio.docx': {
        # #1 endereço cliente + advogado hardcoded
        "residente e domiciliada à Av. Toledo, n° 150, bairro Laranjeiras, Município de Uberlândia, CEP 38410-526, estado de Minas Gerais, por intermédio de {{SEU_SUA_ADVOGADO_A}} TIAGO DE AZEVEDO LIMA, OAB/MG nº 228.433":
            "residente e {{DOMICILIADO_A}} à {{CLIENTE_LOGRADOURO}}, n° {{CLIENTE_NUMERO}}, bairro {{CLIENTE_BAIRRO}}, Município de {{CLIENTE_MUNICIPIO}}, CEP {{CLIENTE_CEP}}, estado {{CLIENTE_UF_EXTENSO}}, por intermédio de {{SEU_SUA_ADVOGADO_A}} {{ADVOGADO_NOME}}, {{ADVOGADO_OAB_UF}}",
        # #12 "e. ao consultar" → "e, ao consultar"
        "junto ao {{BANCO_NOME}} e. ao consultar":  "junto ao {{BANCO_NOME}}, e ao consultar",
        # #13 "tarifas bancárias a, tais como"
        "A cobrança de tarifas bancárias a, tais como":
            "A cobrança de tarifas bancárias, tais como",
        # #14 falta "ou"
        "pacote de serviços qualquer instrumento":
            "pacote de serviços ou qualquer instrumento",
    },
    # ---------- BRADESCO ENCARGOS ----------
    'template_bradesco-encargos__sem-escritorio.docx': {
        # #3 endereço Caapiranga + OAB/AM hardcoded
        "residente e domiciliada à Rua Couto Vale, n° 1337, bairro Centro, Município de Caapiranga, CEP 69.425-000, estado do Amazonas, por intermédio de {{SEU_SUA_ADVOGADO_A}} {{ADVOGADO_NOME}}, OAB/AM nº A2638":
            "residente e {{DOMICILIADO_A}} à {{CLIENTE_LOGRADOURO}}, n° {{CLIENTE_NUMERO}}, bairro {{CLIENTE_BAIRRO}}, Município de {{CLIENTE_MUNICIPIO}}, CEP {{CLIENTE_CEP}}, estado {{CLIENTE_UF_EXTENSO}}, por intermédio de {{SEU_SUA_ADVOGADO_A}} {{ADVOGADO_NOME}}, {{ADVOGADO_OAB_UF}}",
        "junto ao {{BANCO_NOME}} e. ao consultar":  "junto ao {{BANCO_NOME}}, e ao consultar",
    },
    # ---------- BRADESCO CAPITALIZACAO ----------
    'template_bradesco-capitalizacao__sem-escritorio.docx': {
        # #2 endereço Uberlândia + TIAGO hardcoded
        "residente e domiciliada à Av. Toledo, n° 150, bairro Laranjeiras, Município de Uberlândia, CEP 38410-526, estado de Minas Gerais, por intermédio de {{SEU_SUA_ADVOGADO_A}} TIAGO DE AZEVEDO LIMA, OAB/MG nº 228.433":
            "residente e {{DOMICILIADO_A}} à {{CLIENTE_LOGRADOURO}}, n° {{CLIENTE_NUMERO}}, bairro {{CLIENTE_BAIRRO}}, Município de {{CLIENTE_MUNICIPIO}}, CEP {{CLIENTE_CEP}}, estado {{CLIENTE_UF_EXTENSO}}, por intermédio de {{SEU_SUA_ADVOGADO_A}} {{ADVOGADO_NOME}}, {{ADVOGADO_OAB_UF}}",
        "junto ao {{BANCO_NOME}} e. ao consultar":  "junto ao {{BANCO_NOME}}, e ao consultar",
    },
    # ---------- BRADESCO PE (mais complexo) ----------
    'template_bradesco-pe__sem-escritorio.docx': {
        # #4 vários hardcodes + bug CEP + falta estado civil + PATRICK
        # #19 ausência de {{CLIENTE_ESTADO_CIVIL}}
        # #20 PATRICK hardcoded
        # bug {{CLIENTE_CEP}}160-000 — sobrou pedaço
        "{{CLIENTE_NACIONALIDADE_GENERO}}, {{CLIENTE_PROFISSAO}}, {{INSCRITO_A}} no CPF sob o nº {{CLIENTE_CPF}}, Cédula de Identidade nº {{CLIENTE_RG}}, órgão expedidor {{CLIENTE_RG_ORGAO}}, residente e {{DOMICILIADO_A}} na {{CLIENTE_LOGRADOURO}}, bairro {{CLIENTE_BAIRRO}}, em {{CLIENTE_MUNICIPIO}}/{{CLIENTE_UF}}, CEP {{CLIENTE_CEP}}160-000, estado do Amazonas, por intermédio de {{SEU_SUA_ADVOGADO_A}} PATRICK WILLIAN DA SILVA, OAB/AM, nº A2638":
            "{{CLIENTE_NACIONALIDADE_GENERO}}, {{CLIENTE_ESTADO_CIVIL}}, {{CLIENTE_PROFISSAO}}, {{INSCRITO_A}} no CPF sob o nº {{CLIENTE_CPF}}, Cédula de Identidade nº {{CLIENTE_RG}}, órgão expedidor {{CLIENTE_RG_ORGAO}}, residente e {{DOMICILIADO_A}} na {{CLIENTE_LOGRADOURO}}, bairro {{CLIENTE_BAIRRO}}, em {{CLIENTE_MUNICIPIO}}/{{CLIENTE_UF}}, CEP {{CLIENTE_CEP}}, por intermédio de {{SEU_SUA_ADVOGADO_A}} {{ADVOGADO_NOME}}, {{ADVOGADO_OAB_UF}}",
        "junto ao {{BANCO_NOME}} e. ao consultar":  "junto ao {{BANCO_NOME}}, e ao consultar",
    },
}


def aplicar_em_template(caminho, todas_subs):
    backup = caminho.with_suffix(caminho.suffix + ".bak_pre_pente_fino")
    if not backup.exists():
        shutil.copy2(caminho, backup)
    doc = Document(caminho)
    n = 0
    for p in doc.paragraphs:
        if substituir_in_run(p._p, todas_subs):
            n += 1
    doc.save(caminho)
    return n


total = 0
for nome in [
    'template_consignado-nao-contratado__com-escritorio.docx',
    'template_consignado-nao-contratado__sem-escritorio.docx',
    'template_rmc__com-escritorio.docx',
    'template_rmc__sem-escritorio.docx',
    'template_rcc__com-escritorio.docx',
    'template_rcc__sem-escritorio.docx',
    'template_bradesco-tarifas__sem-escritorio.docx',
    'template_bradesco-encargos__sem-escritorio.docx',
    'template_bradesco-capitalizacao__sem-escritorio.docx',
    'template_bradesco-pe__sem-escritorio.docx',
]:
    caminho = ASSETS / nome
    todas = {**SUBS_UNIVERSAIS, **SUBS_POR_TEMPLATE.get(nome, {})}
    n = aplicar_em_template(caminho, todas)
    total += n
    print(f"  {nome}: {n} parágrafos modificados")

print(f"\nTotal alterações: {total}")
