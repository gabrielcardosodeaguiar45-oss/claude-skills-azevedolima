"""
Pipeline OCR híbrido (proposta C) e verificações automáticas cruzadas
para a skill /replica-nao-contratado.

Filosofia:
1. pymupdf extrai texto puro (rápido) para a maior parte do PDF
2. Para PEÇAS CRÍTICAS, renderiza a página como PNG e disponibiliza para
   leitura visual nativa (Claude lê via Read tool)
3. Tesseract NÃO faz parte do pipeline padrão — só se um caso específico
   demandar OCR em massa de PDF totalmente digitalizado

Uso típico:
    from visual_pipeline import (
        extrair_texto_pdf, identificar_pecas_criticas,
        renderizar_pagina_png, extrair_imagens_pagina,
        # Verificações cruzadas:
        detectar_impossibilidade_temporal,
        comparar_hashes_contratos,
        detectar_anotacao_impossibilidade_assinar,
        detectar_divergencia_contestacao_extrato,
        detectar_cessao_credito,
        capturar_advogado_inicial,
        capturar_filial_escritorio,
        capturar_notificacao_extrajudicial,
    )

    texto = extrair_texto_pdf(caminho_pdf)
    criticas = identificar_pecas_criticas(texto)
    for peca in criticas:
        png = renderizar_pagina_png(caminho_pdf, peca['pagina'], destino)
        # Claude lê o PNG via Read tool e retorna observações
"""
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import fitz  # pymupdf


# ============================================================
# EXTRAÇÃO DE TEXTO E IMAGENS
# ============================================================

def extrair_texto_pdf(caminho_pdf: str, salvar_em: Optional[str] = None) -> str:
    """Extrai texto integral do PDF via pymupdf.

    Se salvar_em for fornecido, salva também em arquivo .txt para grep posterior.
    """
    doc = fitz.open(caminho_pdf)
    partes = []
    for i, page in enumerate(doc):
        partes.append(f"\n\n===== PÁGINA {i + 1} =====\n")
        partes.append(page.get_text())
    doc.close()
    texto = "".join(partes)
    if salvar_em:
        with open(salvar_em, 'w', encoding='utf-8') as f:
            f.write(texto)
    return texto


def renderizar_pagina_png(caminho_pdf: str, numero_pagina: int,
                          destino_png: str, dpi: int = 300) -> str:
    """Renderiza uma página específica do PDF como PNG.

    numero_pagina é 1-indexed (página 1 = primeira página do PDF).
    Retorna o caminho do PNG salvo.
    """
    doc = fitz.open(caminho_pdf)
    page = doc[numero_pagina - 1]
    mat = fitz.Matrix(dpi / 72, dpi / 72)  # escalar para DPI desejado
    pix = page.get_pixmap(matrix=mat)
    pix.save(destino_png)
    doc.close()
    return destino_png


def extrair_imagens_pagina(caminho_pdf: str, numero_pagina: int,
                           destino_dir: str) -> List[str]:
    """Extrai as IMAGENS embutidas em uma página do PDF (não a página inteira).

    Útil para capturar selfies, fotos de RG, prints de tela etc. que estão
    embutidos como imagens no PDF (não como camada de texto).

    Retorna lista de caminhos dos PNGs salvos.
    """
    doc = fitz.open(caminho_pdf)
    page = doc[numero_pagina - 1]
    image_list = page.get_images(full=True)
    salvos = []
    os.makedirs(destino_dir, exist_ok=True)
    for img_index, img in enumerate(image_list):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        ext = base_image["ext"]
        nome = f"pagina{numero_pagina}_img{img_index + 1}.{ext}"
        caminho = os.path.join(destino_dir, nome)
        with open(caminho, 'wb') as f:
            f.write(image_bytes)
        salvos.append(caminho)
    doc.close()
    return salvos


# ============================================================
# IDENTIFICAÇÃO DE PEÇAS CRÍTICAS
# ============================================================

# Padrões que indicam tipos de peças críticas no PDF
PADROES_PECAS_CRITICAS = {
    'ted': [r'DEMTRANSF', r'COMPTRANS', r'comprovante de transferên', r'TED'],
    'selfie': [r'selfie', r'biometria facial', r'foto.*tipo.*Liveness'],
    'trilha_auditoria': [r'trilha de auditoria', r'jornada de assinatura',
                        r'log de opera', r'protocolo de assinatura'],
    'contrato_fisico': [r'Cédula de Crédito Bancária', r'CCB',
                       r'Cart[oó]rio.*T[ií]tulos', r'assinatura.*emitente'],
    'declaracao': [r'Declara[cç][aã]o de Resid[eê]ncia',
                  r'Declara[cç][aã]o de Hipossufici[eê]ncia'],
    'hiscre': [r'Histórico de Créditos', r'HISTCRE', r'HISCRE'],
    'hiscon': [r'Histórico de Empréstimo', r'HISTEMP', r'HISCON'],
    'rg': [r'Carteira de Identidade', r'Cédula de Identidade', r'IMPOSSIBILIDADE DE ASSINAR'],
}


def identificar_pecas_criticas(texto_pdf: str) -> List[Dict]:
    """Identifica páginas/eventos que merecem leitura visual.

    Retorna lista de dicts:
        {'tipo': 'ted', 'pagina': 293, 'evento': 'DEMTRANSF8',
         'preview': 'primeiras 200 chars do contexto'}

    Critérios de criticidade:
    - Pouco texto extraível (< 50 chars na página) sugere imagem
    - Padrões específicos no nome do evento ou contexto
    - Marcadores de TED, selfie, trilha, declaração
    """
    pecas = []
    paginas = texto_pdf.split('===== PÁGINA ')
    for p in paginas[1:]:  # primeiro elemento é vazio
        m = re.match(r'(\d+) =====\n(.*)', p, re.DOTALL)
        if not m:
            continue
        num_pagina = int(m.group(1))
        conteudo = m.group(2)

        # Detecta tipo
        tipo_detectado = None
        for tipo, padroes in PADROES_PECAS_CRITICAS.items():
            for pat in padroes:
                if re.search(pat, conteudo, re.IGNORECASE):
                    tipo_detectado = tipo
                    break
            if tipo_detectado:
                break

        # Critério de "pouco texto" (página possivelmente em imagem)
        texto_limpo = re.sub(r'\s+', ' ', conteudo).strip()
        pouco_texto = len(texto_limpo) < 50

        if tipo_detectado or pouco_texto:
            # Tenta capturar nome do evento ("Evento N, TIPO")
            ev_match = re.search(r'Evento\s+(\d+),\s*([A-Z]+\d*)', conteudo)
            evento = f"Ev {ev_match.group(1)}, {ev_match.group(2)}" if ev_match else None

            # PJe Num. NNN
            pje_match = re.search(r'Num\.\s*(\d+)', conteudo)
            evento = evento or (f"Num. {pje_match.group(1)}" if pje_match else None)

            pecas.append({
                'tipo': tipo_detectado or 'pagina_em_imagem',
                'pagina': num_pagina,
                'evento': evento,
                'preview': texto_limpo[:200],
                'razao': 'padrao_textual' if tipo_detectado else 'pouco_texto_extraido',
            })
    return pecas


# ============================================================
# CAPTURAS DA INICIAL
# ============================================================

def capturar_advogado_inicial(texto_inicial: str) -> Optional[Dict]:
    """Captura nome completo + OAB do advogado que assinou a INICIAL.

    Procura padrões típicos no rodapé da inicial:
    - "Tiago de Azevedo Lima\nOAB/AL 20.906A"
    - "GABRIEL CARDOSO DE AGUIAR\nSC 76040"
    - "Eduardo Fernando Rebonatto - OAB/SC nº 36.592"

    Retorna {'nome': str, 'oab': str} ou None se não encontrar.
    """
    # Padrão 1: Nome em linha + OAB/UF na próxima linha
    pad1 = re.compile(
        r'([A-ZÁÉÍÓÚÂÊÔÇÃÕ][a-záéíóúâêôçãõ]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÇÃÕ][a-záéíóúâêôçãõ]+){1,5})\s*\n\s*'
        r'(OAB[/\s]*[A-Z]{2}\s*(?:n[ºo°]?\s*)?[\d\.\-]+\w?)',
        re.MULTILINE
    )
    m = pad1.search(texto_inicial)
    if m:
        return {'nome': m.group(1).strip(), 'oab': m.group(2).strip()}

    # Padrão 2: NOME EM CAIXA ALTA + UF SC NN
    pad2 = re.compile(
        r'([A-ZÁÉÍÓÚÂÊÔÇÃÕ]{3,}(?:\s+[A-ZÁÉÍÓÚÂÊÔÇÃÕ]{2,}){1,5})\s*\n\s*'
        r'((?:OAB[/\s]*)?[A-Z]{2}\s*\d[\d\.\-]+\w?)',
        re.MULTILINE
    )
    m = pad2.search(texto_inicial)
    if m:
        return {'nome': m.group(1).strip().title(), 'oab': m.group(2).strip()}

    # Padrão 3: linha única "Nome - OAB/UF NN"
    pad3 = re.compile(
        r'([A-ZÁÉÍÓÚÂÊÔÇÃÕ][\w\sáéíóúâêôçãõÁÉÍÓÚÂÊÔÇÃÕ]{15,60})\s*[-—]\s*'
        r'(OAB[/\s]*[A-Z]{2}\s*(?:n[ºo°]?\s*)?[\d\.\-]+\w?)',
    )
    m = pad3.search(texto_inicial)
    if m:
        return {'nome': m.group(1).strip(), 'oab': m.group(2).strip()}

    return None


def capturar_filial_escritorio(texto_inicial: str) -> Optional[str]:
    """Captura cidade/UF da filial do escritório que atende a parte autora.

    Procura na qualificação dos procuradores: "endereço onde recebem avisos
    e intimações" ou "filial em Cidade/UF" ou "escritório profissional na ...".

    Retorna string "Cidade/UF" ou None.
    """
    # Padrão: "filial em <Cidade>/<UF>" ou "filial em <Cidade> - <UF>"
    pad1 = re.search(r'filial\s+em\s+([A-Z][\wáéíóúâêôçãõ\s]+?)/?([A-Z]{2})', texto_inicial, re.IGNORECASE)
    if pad1:
        cidade = pad1.group(1).strip()
        uf = pad1.group(2).strip()
        return f"{cidade}/{uf}"

    # Padrão: "no Município de <Cidade>/<UF>"
    pad2 = re.search(r'no\s+Munic[ií]pio\s+de\s+([A-Z][\wáéíóúâêôçãõ\s]+?)/?([A-Z]{2})',
                     texto_inicial)
    if pad2:
        cidade = pad2.group(1).strip()
        uf = pad2.group(2).strip()
        return f"{cidade}/{uf}"

    # Padrão: "Joaçaba/SC" ou "Arapiraca/AL" no rodapé
    pad3 = re.search(r'\b([A-Z][\wáéíóúâêôçãõ]+(?:\s+[A-Z][\wáéíóúâêôçãõ]+)*)/([A-Z]{2})\b',
                     texto_inicial)
    if pad3:
        return f"{pad3.group(1)}/{pad3.group(2)}"

    return None


def capturar_notificacao_extrajudicial(texto: str) -> Optional[Dict]:
    """Captura datas específicas de notificação extrajudicial / AR digital.

    Procura padrões como "notificação enviada em DD/MM/AAAA" ou
    "AR digital protocolado em DD/MM/AAAA".

    Retorna {'data_envio': str, 'data_entrega': str} ou None.
    """
    resultado = {}
    pad_envio = re.search(
        r'(?:notifica[cç][aã]o|AR[\s-]digital|AR[\s-]E?mail|requerimento).*?'
        r'(?:em|enviad|protocolad).*?(\d{2}/\d{2}/\d{4})',
        texto, re.IGNORECASE | re.DOTALL
    )
    if pad_envio:
        resultado['data_envio'] = pad_envio.group(1)

    pad_entrega = re.search(
        r'entreg[aue].*?(\d{2}/\d{2}/\d{4})',
        texto, re.IGNORECASE
    )
    if pad_entrega:
        resultado['data_entrega'] = pad_entrega.group(1)

    return resultado if resultado else None


def capturar_contratos_impugnados(texto_inicial: str) -> List[Dict]:
    """Captura lista de contratos impugnados na INICIAL.

    Procura por padrões como "contrato nº NNN", "CCB nº NNN" e tenta
    associar valor, parcelas, data se houver.

    Retorna lista de dicts:
        {'numero': '20031787', 'valor': 'R$ X,XX' ou None,
         'parcelas': N ou None, 'data_inclusao': 'DD/MM/AAAA' ou None}
    """
    contratos = []
    # Padrões de número de contrato (mínimo 6 dígitos)
    padrao_contrato = re.compile(
        r'(?:contrato|CCB|c[eé]dula)[\s\w]*?n[º°o]?\s*(\d{6,}\s*\d*)',
        re.IGNORECASE
    )
    encontrados = set()
    for m in padrao_contrato.finditer(texto_inicial):
        num = re.sub(r'\s+', '', m.group(1))
        if num not in encontrados:
            encontrados.add(num)
            contratos.append({'numero': num})
    return contratos


# ============================================================
# VERIFICAÇÕES CRUZADAS AUTOMÁTICAS
# ============================================================

def detectar_impossibilidade_temporal(ccb_data_emissao: str,
                                      hiscon_data_inclusao: str) -> Dict:
    """Verifica se HISCON registra inclusão ANTES da data de emissão da CCB.

    Datas em formato 'DD/MM/AAAA'. Retorna:
        {'detectado': bool, 'dias_diferenca': int, 'descricao': str}
    """
    try:
        d_ccb = datetime.strptime(ccb_data_emissao, '%d/%m/%Y')
        d_hiscon = datetime.strptime(hiscon_data_inclusao, '%d/%m/%Y')
    except ValueError:
        return {'detectado': False, 'erro': 'datas em formato inválido'}

    diff = (d_ccb - d_hiscon).days
    if diff > 0:  # CCB é POSTERIOR à inclusão no HISCON
        return {
            'detectado': True,
            'dias_diferenca': diff,
            'descricao': f'CCB datada de {ccb_data_emissao} foi assinada {diff} dia(s) '
                        f'APÓS a inclusão no HISCON ({hiscon_data_inclusao}). '
                        f'Impossibilidade material: não se averba contrato inexistente.',
        }
    return {'detectado': False, 'dias_diferenca': diff,
            'descricao': 'Cronologia normal (CCB anterior ou igual à inclusão).'}


def comparar_hashes_contratos(contratos: List[Dict]) -> Dict:
    """Compara os hashes de cada componente entre múltiplos contratos digitais.

    contratos: lista de dicts no formato esperado por add_tabela_hashes().

    Retorna:
        {'identicos_detectados': bool,
         'componentes_identicos': [
             {'componente': 'hash_cadastro', 'valor': 'XXXX...',
              'contratos': ['20031787', '20032423']}
         ]}
    """
    if len(contratos) < 2:
        return {'identicos_detectados': False, 'componentes_identicos': []}

    componentes = ['hash_envelope', 'hash_ccb', 'hash_cet',
                   'hash_termo_inss', 'hash_cadastro', 'hash_evidencias']
    identicos = []
    for comp in componentes:
        valores = {}
        for c in contratos:
            v = c.get(comp, '').strip().lower()
            if v:
                valores.setdefault(v, []).append(c['numero'])
        for valor, lista_contratos in valores.items():
            if len(lista_contratos) > 1:
                identicos.append({
                    'componente': comp,
                    'valor': valor,
                    'contratos': lista_contratos,
                })
    return {
        'identicos_detectados': bool(identicos),
        'componentes_identicos': identicos,
    }


def detectar_anotacao_impossibilidade_assinar(texto_rg: str) -> Dict:
    """Verifica se o RG/CNH contém anotação de 'IMPOSSIBILIDADE DE ASSINAR'.

    Retorna {'detectado': bool, 'permanente': bool, 'data_emissao_rg': str ou None}
    """
    permanente = bool(re.search(r'IMPOSSIBILIDADE\s+DE\s+ASSINAR\s+PERMANENTE',
                                texto_rg, re.IGNORECASE))
    qualquer = bool(re.search(r'IMPOSSIBILIDADE\s+DE\s+ASSINAR',
                              texto_rg, re.IGNORECASE))

    data_match = re.search(r'(?:Expedi[cç][aã]o|Emissão).*?(\d{2}/\d{2}/\d{4})',
                          texto_rg, re.IGNORECASE)
    data = data_match.group(1) if data_match else None

    return {
        'detectado': qualquer,
        'permanente': permanente,
        'data_emissao_rg': data,
    }


def detectar_divergencia_contestacao_extrato(
    texto_contestacao: str,
    valores_extrato: Dict
) -> Dict:
    """Compara números afirmados na contestação versus extrato financeiro juntado.

    valores_extrato: dict com 'parcelas', 'valor_parcela', 'total' efetivamente
                     constantes do extrato (já extraídos visualmente ou por OCR).

    Procura na contestação números que conflitam.

    Retorna {'detectado': bool, 'divergencias': [{'campo': str,
             'contestacao': str, 'extrato': str}]}
    """
    div = []

    # Procura "N parcelas de R$ X,XX" na contestação
    pad_parc = re.search(r'(\d+)\s*parcelas?\s*(?:mensais?\s*)?de\s*R\$\s*([\d\.,]+)',
                         texto_contestacao, re.IGNORECASE)
    if pad_parc:
        n_contestacao = int(pad_parc.group(1))
        v_contestacao = pad_parc.group(2)

        if 'parcelas' in valores_extrato:
            n_extrato = valores_extrato['parcelas']
            if n_contestacao != n_extrato:
                div.append({
                    'campo': 'quantidade_parcelas',
                    'contestacao': str(n_contestacao),
                    'extrato': str(n_extrato),
                })

        if 'valor_parcela' in valores_extrato:
            v_extrato = str(valores_extrato['valor_parcela'])
            if v_contestacao.replace(',', '.') != v_extrato.replace(',', '.'):
                div.append({
                    'campo': 'valor_parcela',
                    'contestacao': f'R$ {v_contestacao}',
                    'extrato': f'R$ {v_extrato}',
                })

    return {'detectado': bool(div), 'divergencias': div}


def detectar_cessao_credito(texto_extrato_financeiro: str) -> Dict:
    """Verifica se há marcação 'Cedida' / parcelas em data uniforme no extrato.

    Padrões típicos:
    - 'Cedida' nas parcelas
    - Várias parcelas marcadas como 'Liquidada' em data idêntica
    """
    cedidas = len(re.findall(r'\bCedida\b', texto_extrato_financeiro, re.IGNORECASE))

    # Detecta múltiplas parcelas com data idêntica de liquidação
    datas_liq = re.findall(r'Liquidad\w*\s+\d{2,3},?\d*\s+\d+,\d+\s+\d+,\d+\s+\d+,\d+\s+(\d{2}/\d{2}/\d{4})',
                          texto_extrato_financeiro)
    from collections import Counter
    contagem_datas = Counter(datas_liq)
    datas_uniformes = [(d, n) for d, n in contagem_datas.items() if n >= 3]

    return {
        'detectado': cedidas > 0 or bool(datas_uniformes),
        'parcelas_cedidas': cedidas,
        'datas_liquidacao_uniformes': datas_uniformes,
    }


def detectar_ted_para_terceiro(
    banco_destino_ted: Tuple[str, str, str],  # (banco, agencia, conta)
    banco_inss_hiscre: Tuple[str, str],  # (banco, agencia)
) -> Dict:
    """Verifica se a conta de destino do TED é diferente do banco onde o INSS
    é pago à autora.

    Retorna {'fraude_confirmada': bool, 'detalhes': str}
    """
    banco_ted, ag_ted, conta_ted = banco_destino_ted
    banco_inss, ag_inss = banco_inss_hiscre

    if banco_ted.strip() != banco_inss.strip():
        return {
            'fraude_confirmada': True,
            'detalhes': f'TED foi para Banco {banco_ted} (ag. {ag_ted}, conta {conta_ted}), '
                       f'mas autora recebia INSS no Banco {banco_inss} (ag. {ag_inss}). '
                       f'Conta de destino é de TERCEIRO, não da autora.',
        }
    if ag_ted.strip() != ag_inss.strip():
        return {
            'fraude_confirmada': True,
            'detalhes': f'TED foi para mesmo banco ({banco_ted}) mas agência divergente '
                       f'(ag. {ag_ted} vs INSS recebido em ag. {ag_inss}). Verificar.',
        }
    return {
        'fraude_confirmada': False,
        'detalhes': 'TED para conta no mesmo banco/agência do INSS — autora pode ter recebido.',
    }


def detectar_sms_ddd_diferente(texto_trilha: str, uf_residencia: str) -> Dict:
    """Detecta SMS de formalização para telefone com DDD de UF diferente.

    Procura padrão tipo 'phone=55XXNNNNNNNN' na trilha.
    Retorna {'detectado': bool, 'ddd_sms': str, 'uf_ddd': str, 'uf_residencia': str}
    """
    # Mapa simplificado DDD → UF
    DDD_UF = {
        '11': 'SP', '12': 'SP', '13': 'SP', '14': 'SP', '15': 'SP',
        '16': 'SP', '17': 'SP', '18': 'SP', '19': 'SP',
        '21': 'RJ', '22': 'RJ', '24': 'RJ',
        '27': 'ES', '28': 'ES',
        '31': 'MG', '32': 'MG', '33': 'MG', '34': 'MG', '35': 'MG',
        '37': 'MG', '38': 'MG',
        '41': 'PR', '42': 'PR', '43': 'PR', '44': 'PR', '45': 'PR', '46': 'PR',
        '47': 'SC', '48': 'SC', '49': 'SC',
        '51': 'RS', '53': 'RS', '54': 'RS', '55': 'RS',
        '61': 'DF', '62': 'GO', '64': 'GO', '63': 'TO',
        '65': 'MT', '66': 'MT', '67': 'MS',
        '68': 'AC', '69': 'RO',
        '71': 'BA', '73': 'BA', '74': 'BA', '75': 'BA', '77': 'BA',
        '79': 'SE',
        '81': 'PE', '87': 'PE',
        '82': 'AL', '83': 'PB', '84': 'RN', '85': 'CE', '88': 'CE',
        '86': 'PI', '89': 'PI',
        '91': 'PA', '93': 'PA', '94': 'PA',
        '92': 'AM', '97': 'AM',
        '95': 'RR', '96': 'AP',
        '98': 'MA', '99': 'MA',
    }
    pad = re.search(r'phone=55(\d{2})\d{8,9}', texto_trilha)
    if not pad:
        # Tentativa alternativa: "(DDD) NNNN-NNNN"
        pad = re.search(r'\((\d{2})\)\s*\d{4,5}-?\d{4}', texto_trilha)
    if not pad:
        return {'detectado': False}
    ddd_sms = pad.group(1)
    uf_ddd = DDD_UF.get(ddd_sms, '?')
    detectado = uf_ddd != uf_residencia.upper()
    return {
        'detectado': detectado,
        'ddd_sms': ddd_sms,
        'uf_ddd': uf_ddd,
        'uf_residencia': uf_residencia.upper(),
        'descricao': f'SMS para DDD {ddd_sms} ({uf_ddd}) enquanto autora reside em {uf_residencia}'
                     if detectado else 'SMS para DDD da UF da autora.',
    }


def detectar_email_do_banco(texto_trilha: str, dominios_bancos: List[str] = None) -> Dict:
    """Detecta se a identificação Certisign foi por e-mail do próprio banco.

    Procura por 'Identificação: Por email: <email>' na trilha.
    Retorna {'detectado': bool, 'email': str, 'eh_dominio_banco': bool}
    """
    if dominios_bancos is None:
        dominios_bancos = ['safra.com.br', 'itau.com.br', 'bradesco.com.br',
                          'santander.com.br', 'mercantil.com.br', 'pan.com.br',
                          'caixa.gov.br', 'bb.com.br', 'banco.com.br']
    pad = re.search(r'(?:Identifica[cç][aã]o|email)[:\s]+([\w._-]+@[\w.-]+\.\w+)',
                    texto_trilha, re.IGNORECASE)
    if not pad:
        return {'detectado': False}
    email = pad.group(1)
    eh_banco = any(dom in email.lower() for dom in dominios_bancos)
    return {
        'detectado': eh_banco,
        'email': email,
        'descricao': f'Identificação por e-mail do próprio banco: {email}'
                     if eh_banco else f'E-mail de identificação aparenta ser pessoal: {email}',
    }


def detectar_contratos_ausentes(impugnados_inicial: List[str],
                                juntados_banco: List[str]) -> List[str]:
    """Lista contratos impugnados na inicial que o banco NÃO juntou na contestação.

    Retorna lista de números de contratos ausentes (pedido de presunção art. 400 CPC).
    """
    set_inicial = {re.sub(r'\D', '', c) for c in impugnados_inicial}
    set_juntados = {re.sub(r'\D', '', c) for c in juntados_banco}
    ausentes = set_inicial - set_juntados
    return sorted(ausentes)


# ============================================================
# RELATÓRIO CONSOLIDADO DAS VERIFICAÇÕES
# ============================================================

def gerar_relatorio_verificacoes(resultados: Dict) -> str:
    """Formata os resultados de todas as verificações em texto para
    o resumo de entrega ao usuário.

    resultados: dict com chaves para cada verificação (impossibilidade_temporal,
                hash_identico, ted_para_terceiro, etc.)
    """
    linhas = ["Verificações automáticas executadas:"]

    if 'ted_terceiro' in resultados:
        r = resultados['ted_terceiro']
        status = '⚠ FRAUDE CONFIRMADA' if r.get('fraude_confirmada') else 'OK'
        linhas.append(f"  - HISCRE × TED: {status}")
        if r.get('detalhes'):
            linhas.append(f"      {r['detalhes']}")

    if 'impossibilidade_temporal' in resultados:
        r = resultados['impossibilidade_temporal']
        status = '⚠ DETECTADA' if r.get('detectado') else 'OK'
        linhas.append(f"  - CCB × HISCON (impossibilidade temporal): {status}")
        if r.get('detectado') and r.get('descricao'):
            linhas.append(f"      {r['descricao']}")

    if 'hash_identico' in resultados:
        r = resultados['hash_identico']
        status = '⚠ HASHES IDÊNTICOS DETECTADOS' if r.get('identicos_detectados') else 'OK'
        linhas.append(f"  - Hash idêntico entre digitais: {status}")
        for c in r.get('componentes_identicos', []):
            linhas.append(f"      {c['componente']} idêntico em: {', '.join(c['contratos'])}")

    if 'rg_impossibilidade' in resultados:
        r = resultados['rg_impossibilidade']
        if r.get('detectado'):
            tipo = 'PERMANENTE' if r.get('permanente') else 'TEMPORÁRIA'
            linhas.append(f"  - Anotação RG impossibilidade: ⚠ DETECTADA ({tipo})")
            if r.get('data_emissao_rg'):
                linhas.append(f"      RG emitido em {r['data_emissao_rg']}")
        else:
            linhas.append(f"  - Anotação RG impossibilidade: OK (não detectada)")

    if 'divergencia_contestacao' in resultados:
        r = resultados['divergencia_contestacao']
        status = '⚠ DIVERGÊNCIA DETECTADA' if r.get('detectado') else 'OK'
        linhas.append(f"  - Divergência interna contestação × extrato: {status}")
        for d in r.get('divergencias', []):
            linhas.append(f"      {d['campo']}: contestação={d['contestacao']} vs extrato={d['extrato']}")

    if 'cessao_credito' in resultados:
        r = resultados['cessao_credito']
        status = '⚠ DETECTADA' if r.get('detectado') else 'OK'
        linhas.append(f"  - Cessão de crédito não notificada: {status}")
        if r.get('parcelas_cedidas'):
            linhas.append(f"      {r['parcelas_cedidas']} parcelas marcadas como 'Cedida'")

    if 'sms_ddd' in resultados:
        r = resultados['sms_ddd']
        status = '⚠ DDD DIFERENTE' if r.get('detectado') else 'OK'
        linhas.append(f"  - SMS DDD diferente da residência: {status}")
        if r.get('detectado'):
            linhas.append(f"      {r['descricao']}")

    if 'email_banco' in resultados:
        r = resultados['email_banco']
        status = '⚠ E-MAIL DO BANCO' if r.get('detectado') else 'OK'
        linhas.append(f"  - E-mail do banco como identificação Certisign: {status}")
        if r.get('detectado'):
            linhas.append(f"      {r['descricao']}")

    if 'contratos_ausentes' in resultados:
        r = resultados['contratos_ausentes']
        if r:
            linhas.append(f"  - Contratos impugnados não juntados pelo banco: ⚠ {len(r)}")
            for c in r:
                linhas.append(f"      Contrato {c} (presunção art. 400 CPC + pedido julgamento antecipado)")
        else:
            linhas.append(f"  - Contratos impugnados não juntados: OK")

    return '\n'.join(linhas)


if __name__ == '__main__':
    # Self-test rápido
    print("visual_pipeline — verificações cruzadas e OCR híbrido")
    print()

    # Teste 1: impossibilidade temporal
    r = detectar_impossibilidade_temporal('17/10/2020', '12/10/2020')
    print(f"Impossibilidade temporal: {r}")
    print()

    # Teste 2: hash idêntico
    r = comparar_hashes_contratos([
        {'numero': '20031787', 'hash_cadastro': 'AAAA111'},
        {'numero': '20032423', 'hash_cadastro': 'AAAA111'},
    ])
    print(f"Hash idêntico: {r}")
    print()

    # Teste 3: TED para terceiro
    r = detectar_ted_para_terceiro(
        banco_destino_ted=('33', '3029', '12345'),
        banco_inss_hiscre=('237', '676457'),
    )
    print(f"TED terceiro: {r}")
    print()

    # Teste 4: SMS DDD diferente
    r = detectar_sms_ddd_diferente(
        'phone=5511265099160 - Iniciar formalização',
        uf_residencia='SC',
    )
    print(f"SMS DDD: {r}")
    print()

    # Teste 5: e-mail do banco
    r = detectar_email_do_banco('Identificação: Por email: safra@safra.com.br')
    print(f"E-mail banco: {r}")
