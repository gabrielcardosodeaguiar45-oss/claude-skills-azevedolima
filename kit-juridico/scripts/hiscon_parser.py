"""
Parser do HISCON (Histórico de Empréstimo Consignado do INSS).

Extrai metadados do benefício e a lista completa de contratos com
situação, datas, valores, origem e motivo de exclusão. Funciona sobre
PDFs com text-layer (saída do Meu INSS).

Para extratos sem text-layer, retorna estrutura vazia com flag is_ocr_required=True
— o orquestrador decide se aplica OCR (easyocr ou Vision Claude) antes.

Uso:
    python hiscon_parser.py <input.pdf> <output.json>

Saída JSON:
{
    "beneficio": {
        "nb": "041.645.683-9",
        "especie": "PENSÃO POR MORTE PREVIDENCIÁRIA",
        "codigo_especie": 21,
        "titular": "ANAIZA MARIA DA CONCEIÇÃO",
        "situacao": "ATIVO",
        "meio_pagamento": "Conta Corrente",
        "banco_pagador": "CAIXA ECONOMICA FEDERAL",
        "agencia": "2046",
        "conta": "8065641529"
    },
    "contratos": [
        {
            "contrato": "631248310",
            "banco_codigo": "029",
            "banco": "BANCO ITAU CONSIGNADO SA",
            "situacao": "Ativo",                    // Ativo | Excluído | Encerrado | Suspenso
            "origem": "Averbação por Refinanciamento",
            "data_inclusao": "14/09/2021",
            "data_exclusao": null,                  // ou "DD/MM/YYYY"
            "motivo_exclusao": null,                // "Exclusão por refinanciamento" | "Exclusão Banco" | etc
            "valor_parcela": "R$27,60",
            "valor_emprestado": "R$1.211,32",
            "qtd_parcelas": 84,
            "competencia_inicio": "10/2021",
            "competencia_fim": "09/2028",
            "primeiro_desconto": null,
            "tipo": "CONSIGNADO"                    // CONSIGNADO | RMC | RCC
        }
    ]
}
"""
import sys
import os
import re
import json
from pathlib import Path

try:
    import fitz
except ImportError as e:
    raise ImportError(
        f"Dependência ausente: {e}. "
        f"Instale via: pip install -r requirements.txt"
    ) from e


def _open_pdf(path):
    """Abre PDF tolerando paths com chars Unicode problemáticos no Windows."""
    try:
        return fitz.open(path)
    except Exception:
        with open(path, "rb") as f:
            return fitz.open(stream=f.read(), filetype="pdf")


ESPECIES = {
    "21": "PENSÃO POR MORTE PREVIDENCIÁRIA",
    "32": "APOSENTADORIA POR INCAPACIDADE PERMANENTE",
    "41": "APOSENTADORIA POR IDADE",
    "42": "APOSENTADORIA POR TEMPO DE CONTRIBUIÇÃO",
    "31": "AUXÍLIO POR INCAPACIDADE TEMPORÁRIA",
    "87": "AMPARO SOCIAL AO IDOSO",
    "88": "AMPARO SOCIAL À PESSOA COM DEFICIÊNCIA",
    "91": "AUXÍLIO-ACIDENTE",
    "25": "AUXÍLIO-RECLUSÃO",
    "57": "APOSENTADORIA POR INVALIDEZ DECORRENTE DO TRABALHO",
}

# Mapeamento espécie → nome de pasta amigável
ESPECIE_PASTA = {
    "21": "PENSÃO",
    "32": "APOSENTADORIA POR INCAPACIDADE",
    "41": "APOSENTADORIA",
    "42": "APOSENTADORIA POR TEMPO DE CONTRIBUIÇÃO",
    "31": "AUXÍLIO-DOENÇA",
    "87": "BPC",
    "88": "BPC",
    "91": "AUXÍLIO-ACIDENTE",
    "25": "AUXÍLIO-RECLUSÃO",
}


def has_text_layer(pdf_path: str, threshold: int = 200) -> bool:
    """Verifica se HISCON tem text-layer (Meu INSS sempre gera com text-layer)."""
    total = 0
    with _open_pdf(pdf_path) as doc:
        for page in doc:
            total += len(page.get_text().strip())
            if total >= threshold:
                return True
    return False


def parsear_cabecalho(texto_pag1: str) -> dict:
    """
    Extrai metadados do benefício da primeira página do HISCON.
    Padrão observado:
        HISTÓRICO DE
        EMPRÉSTIMO CONSIGNADO
        [TITULAR EM CAIXA ALTA]
        Benefício
        [ESPÉCIE]
        Nº Benefício: 041.645.683-9
        Situação: ATIVO
        Meio: Conta Corrente
        Pago em: [BANCO PAGADOR]
        Agência: NNNN
        Conta Corrente: NNNNNNNNNN
    """
    out = {
        "nb": None,
        "especie": None,
        "codigo_especie": None,
        "pasta_beneficio": None,
        "titular": None,
        "situacao": None,
        "meio_pagamento": None,
        "banco_pagador": None,
        "agencia": None,
        "conta": None,
    }

    m = re.search(r"N[ºo°]\s*Benefício:\s*([\d\.\-]+)", texto_pag1)
    if m:
        out["nb"] = m.group(1).strip()
        # codigo da espécie = primeiros 2 dígitos do dígito do meio do NB
        # NÃO é confiável — melhor pegar pelo nome da espécie
    m = re.search(r"Situação:\s*([A-ZÂÊÔ]+)", texto_pag1)
    if m:
        out["situacao"] = m.group(1).strip()
    m = re.search(r"Meio:\s*([^\n]+)", texto_pag1)
    if m:
        out["meio_pagamento"] = m.group(1).strip()
    m = re.search(r"Pago em:\s*([^\n]+)", texto_pag1)
    if m:
        out["banco_pagador"] = m.group(1).strip()
    m = re.search(r"Agência:\s*([\d\-]+)", texto_pag1)
    if m:
        out["agencia"] = m.group(1).strip()
    m = re.search(r"Conta\s+Corrente:\s*([\d\-]+)", texto_pag1)
    if m:
        out["conta"] = m.group(1).strip()

    # Espécie e titular vêm em linhas próximas
    linhas = [l.strip() for l in texto_pag1.split("\n") if l.strip()]
    for i, l in enumerate(linhas):
        if l.upper() == "BENEFÍCIO" and i + 1 < len(linhas):
            out["especie"] = linhas[i+1].strip()
            break
    for i, l in enumerate(linhas):
        if "EMPRÉSTIMO CONSIGNADO" in l.upper() and i + 1 < len(linhas):
            cand = linhas[i+1].strip()
            # Titular é uma linha em CAIXA ALTA antes do "Benefício"
            if cand.upper() == cand and len(cand) > 5:
                out["titular"] = cand
            break

    # Inferir código da espécie pelo nome
    for cod, nome in ESPECIES.items():
        if out["especie"] and nome in out["especie"].upper():
            out["codigo_especie"] = int(cod)
            out["pasta_beneficio"] = ESPECIE_PASTA.get(cod, out["especie"])
            break

    if out["pasta_beneficio"] is None and out["especie"]:
        # Fallback: usar nome da espécie em maiúsculas
        out["pasta_beneficio"] = out["especie"].upper().split()[0]

    return out


def normalizar_texto_extrato(paginas_texto: list[str]) -> str:
    """
    O HISCON quebra texto em colunas. Vamos juntar tudo numa única string
    pra parsear sequencialmente. Mantém ordem das páginas.
    """
    return "\n".join(paginas_texto)


def parsear_contratos_consignado(texto: str, beneficio: dict) -> list[dict]:
    """
    Parseia os blocos de contratos das tabelas:
      - "EMPRÉSTIMOS BANCÁRIOS / CONTRATOS ATIVOS E SUSPENSOS"
      - "EMPRÉSTIMOS BANCÁRIOS / CONTRATOS EXCLUÍDOS E ENCERRADOS"

    Estratégia: dividir o texto pelos cabeçalhos de tabela e processar
    blocos. Cada contrato começa com um número de 6+ dígitos (que pode
    estar quebrado em 2 linhas, ex: "904345" + "4776" = "9043454776").
    """
    contratos = []

    # Achar blocos: tudo entre "EMPRÉSTIMOS BANCÁRIOS" e "CARTÃO DE CRÉDITO" (ou fim)
    bloco_consig_match = re.search(
        r"EMPRÉSTIMOS BANCÁRIOS(.+?)(?=CARTÃO DE CRÉDITO|$)", texto, re.DOTALL
    )
    if not bloco_consig_match:
        return contratos
    bloco_consig = bloco_consig_match.group(1)

    # Dividir entre ATIVOS e EXCLUÍDOS
    partes = re.split(r"CONTRATOS\s+EXCLUÍDOS\s+E\s+ENCERRADOS", bloco_consig)
    bloco_ativos = partes[0]
    bloco_excluidos = partes[1] if len(partes) > 1 else ""

    contratos.extend(_parsear_bloco_ativos(bloco_ativos, beneficio))
    contratos.extend(_parsear_bloco_excluidos(bloco_excluidos, beneficio))
    return contratos


def _juntar_quebras_numericas(texto: str) -> str:
    """
    Junta números quebrados em 2+ linhas pelo Meu INSS.
    Exemplos:
        '904345\n4776\n626 -' → '9043454776\n626 -'
        '303117\n659-1\n623 -' → '303117659-1\n623 -' (PAN com hífen final)
        '15021854318052026\n318 -' → mantém

    Heurística: se uma linha tem só dígitos curtos (3-7) ou dígitos+hífen,
    e a próxima continuação também é numérica, juntar.
    """
    linhas = texto.split("\n")
    out = []
    i = 0
    while i < len(linhas):
        l = linhas[i].strip()
        # Tentar juntar com próximas linhas se forma sequência numérica
        if re.fullmatch(r"\d{3,7}", l):
            j = i + 1
            num = l
            while j < len(linhas):
                next_l = linhas[j].strip()
                # Aceitar dígitos puros OU dígitos + hífen + dígito (ex: "659-1")
                if re.fullmatch(r"\d{1,7}", next_l) or re.fullmatch(r"\d{1,6}-\d{1,2}", next_l):
                    num += next_l
                    j += 1
                else:
                    break
            out.append(num)
            i = j
        else:
            out.append(l)
            i += 1
    return "\n".join(out)


def _parsear_bloco_ativos(bloco: str, beneficio: dict) -> list[dict]:
    """
    Parseia bloco de contratos ATIVOS. Retorna lista de dicts.
    Layout do Meu INSS é em colunas mas o text-layer vem linearizado.

    Cada contrato segue o padrão:
        [contrato] [cod] - [BANCO] [comp_inicio] [comp_fim] [qtd_parc]
        [parcela] [emprestado] [iof?] [Ativo]
        [origem] [data_inclusao]
        [valor_pago?] [taxas?] [primeiro_desc?]
    """
    contratos = []
    bloco = _juntar_quebras_numericas(bloco)

    # Padrão genérico: linha que começa com 6+ dígitos seguido de "  CCC -" (banco)
    # Vamos usar regex multilinha
    padrao = re.compile(
        r"(?P<contrato>\d{6,15})\s*\n+"
        r"(?P<cod_banco>\d{3})\s*-\s*\n*(?P<banco>[A-ZÁÉÊÔÇS\s]+?)\s*\n+"
        r"(?P<comp_ini>\d{2}/\d{4})\s*\n*"
        r"(?P<comp_fim>\d{2}/\d{4})\s*\n*"
        r"(?P<qtd>\d{1,3})\s*\n*"
        r"R\$\s*(?P<parcela>[\d\.,]+)\s*\n*"
        r"R\$\s*(?P<emprestado>[\d\.,]+)\s*\n*"
        r"(?:.*?\n)?"   # IOF/Liberado opcional
        r"(?:R\$\s*(?P<iof>[\d\.,]+)\s*\n*)?"
        r"Ativo\s*\n*"
        r"(?P<origem>Averbação\s+(?:nova|por\s+(?:Refinanciamento|Portabilidade)))\s*\n*"
        r"(?P<inclusao>\d{2}/\d{2}/\d{2})",
        re.DOTALL | re.IGNORECASE
    )

    # Como o text-layer é caótico, vamos usar abordagem mais flexível:
    # achar primeiramente todas as ocorrências de padrões-chave
    contratos.extend(_parsear_iterativo(bloco, beneficio, situacao_padrao="Ativo"))
    return contratos


def _parsear_bloco_excluidos(bloco: str, beneficio: dict) -> list[dict]:
    """Parseia bloco de contratos EXCLUÍDOS e ENCERRADOS."""
    bloco = _juntar_quebras_numericas(bloco)
    return _parsear_iterativo(bloco, beneficio, situacao_padrao=None)


def _parsear_iterativo(bloco: str, beneficio: dict, situacao_padrao: str | None) -> list[dict]:
    """
    Parser flexível que encontra contratos por âncoras múltiplas.

    Estratégia: para cada padrão "[6-15 digitos]\n[3 digitos] -"
    iterar e extrair o que vier nas próximas linhas em janela limitada.
    """
    contratos = []
    linhas = [l.strip() for l in bloco.split("\n")]

    i = 0
    while i < len(linhas):
        l = linhas[i]
        # Âncora: número de 6-15 dígitos (com possível -X final tipo PAN: 326994938-8)
        if re.fullmatch(r"\d{6,15}(-\d)?", l):
            # Próxima linha precisa ser código de banco "NNN -"
            if i + 1 < len(linhas) and re.match(r"\d{3}\s*-", linhas[i+1]):
                contrato = l
                # Coletar próximas ~30 linhas como contexto do contrato
                ctx = "\n".join(linhas[i+1:i+35])
                dados = _parse_contexto_contrato(contrato, ctx, beneficio,
                                                  situacao_padrao=situacao_padrao)
                if dados:
                    contratos.append(dados)
                i += 1  # avançar 1 (resto será capturado em iterações seguintes)
                continue
        i += 1
    return contratos


def _parse_contexto_contrato(contrato: str, ctx: str, beneficio: dict,
                             situacao_padrao: str | None) -> dict | None:
    """Extrai campos do contexto pós-âncora."""
    out = {
        "contrato": contrato,
        "banco_codigo": None,
        "banco": None,
        "situacao": situacao_padrao,
        "origem": None,
        "data_inclusao": None,
        "data_exclusao": None,
        "motivo_exclusao": None,
        "valor_parcela": None,
        "valor_emprestado": None,
        "qtd_parcelas": None,
        "competencia_inicio": None,
        "competencia_fim": None,
        "primeiro_desconto": None,
        "tipo": "CONSIGNADO",
        "beneficio_nb": beneficio.get("nb"),
        "beneficio_pasta": beneficio.get("pasta_beneficio"),
    }

    # Trabalhar com texto compactado (newlines viram espaços)
    ctx_flat = re.sub(r"\s+", " ", ctx).strip()

    # Normalizações pra regex pegar palavras quebradas em múltiplas linhas
    # "refinancia mento" / "refinan ciamento" / "refinan cia mento" → "refinanciamento"
    ctx_flat = re.sub(r"refin\s*an\s*c\s*i?\s*a\s*m\s*e\s*n\s*t\s*o", "refinanciamento",
                      ctx_flat, flags=re.IGNORECASE)
    ctx_flat = re.sub(r"port\s*ab\s*i\s*l\s*i\s*d\s*a\s*d\s*e", "portabilidade",
                      ctx_flat, flags=re.IGNORECASE)
    # "Exclus ão" / "Exclusã o" → "Exclusão"
    ctx_flat = re.sub(r"Exclus\s*ão|Exclusã\s*o", "Exclusão", ctx_flat, flags=re.IGNORECASE)
    # "Excluí do" → "Excluído"
    ctx_flat = re.sub(r"Excluí\s*do", "Excluído", ctx_flat, flags=re.IGNORECASE)
    # "Encerr ado" → "Encerrado"
    ctx_flat = re.sub(r"Encerr\s*ado", "Encerrado", ctx_flat, flags=re.IGNORECASE)
    # "Suspens o" → "Suspenso"
    ctx_flat = re.sub(r"Suspens\s*o", "Suspenso", ctx_flat, flags=re.IGNORECASE)

    # Banco codigo + nome
    m = re.search(r"(\d{3})\s*-\s*(.+?)(?=\s+\d{2}/\d{4})", ctx_flat)
    if m:
        out["banco_codigo"] = m.group(1).strip()
        nome = m.group(2).strip()
        # Compactar duplos espaços que vieram de quebras de linha
        nome = re.sub(r"\s+", " ", nome)
        # "BANCO C6 CONSIG NADO S A" → "BANCO C6 CONSIGNADO SA"
        nome = nome.replace("CONSIG NADO", "CONSIGNADO")
        nome = nome.replace("CONSIGN ADO", "CONSIGNADO")
        nome = nome.replace("S A", "SA")
        nome = nome.replace("S/A", "SA")
        nome = nome.replace("FINANC IAMENTOS", "FINANCIAMENTOS")
        out["banco"] = nome.strip().rstrip("-").strip()

    # Competência início e fim (MM/YYYY)
    comps = re.findall(r"\b(\d{2}/\d{4})\b", ctx_flat)
    if len(comps) >= 1:
        out["competencia_inicio"] = comps[0]
    if len(comps) >= 2:
        out["competencia_fim"] = comps[1]

    # Qtd parcelas: número de 1-3 dígitos antes do primeiro R$
    m = re.search(r"\b(\d{1,3})\s+R\$", ctx_flat)
    if m:
        try:
            out["qtd_parcelas"] = int(m.group(1))
        except ValueError:
            pass

    # Valores R$ parcela e R$ emprestado (primeiros 2)
    # Compactar "R$ 34 ,11" -> "R$34,11" antes de extrair
    ctx_valores = re.sub(r"R\$\s*([\d\.,]+)\s*,\s*(\d{2})", r"R$\1,\2", ctx_flat)
    valores = re.findall(r"R\$\s*([\d\.\,]+)", ctx_valores)
    if len(valores) >= 1:
        out["valor_parcela"] = "R$" + valores[0]
    if len(valores) >= 2:
        out["valor_emprestado"] = "R$" + valores[1]

    # Situação
    if not out["situacao"]:
        if re.search(r"\bExcluído\b|\bExcluí do\b", ctx_flat):
            out["situacao"] = "Excluído"
        elif re.search(r"\bEncerrado\b|\bEncerr ado\b", ctx_flat):
            out["situacao"] = "Encerrado"
        elif re.search(r"\bAtivo\b", ctx_flat):
            out["situacao"] = "Ativo"
        elif re.search(r"\bSuspenso\b|\bSuspens o\b", ctx_flat):
            out["situacao"] = "Suspenso"

    # Origem — formas alternativas com quebra
    # No HISCON aparece com quebras assim: "Averbaç\não por\nRefinan\nciament\no"
    # Após \s+ → ' ', vira: "Averbaç ão por Refinan ciament o"
    # Regex tolerante a espaços internos:
    averb = r"Averba(?:ç\s*ão|cao|ção)"
    origem_patterns = [
        (rf"{averb}\s+por\s+Refinan\s*ciamen?t?\s*o", "Averbação por Refinanciamento"),
        (rf"{averb}\s+por\s+Portabilid\s*ade", "Averbação por Portabilidade"),
        (rf"{averb}\s+nova", "Averbação nova"),
        (r"Migrado\s+do\s+contrato", "Migrado"),
    ]
    for pattern, label in origem_patterns:
        if re.search(pattern, ctx_flat, re.IGNORECASE):
            out["origem"] = label
            break

    # Datas curtas DD/MM/YY (no INSS, sempre formato curto na coluna)
    # Atenção: a data PODE estar quebrada (ex: "04/02/2" + "5" = "04/02/25")
    # Já compactamos com ctx_flat. Mas pode haver "04/02/2 5" (espaço residual).
    ctx_compact_dates = re.sub(r"(\d{2}/\d{2}/\d)\s+(\d{1,2})\b", r"\1\2", ctx_flat)
    datas_curtas = re.findall(r"\b(\d{2}/\d{2}/\d{2})\b(?!\d)", ctx_compact_dates)

    # No layout do HISCON, a primeira data DD/MM/YY após "Ativo" / "Excluído" /
    # "Averbação X" é a data de inclusão.
    # A última data DD/MM/YY antes de "Exclusão por X" / "Exclusão Banco" é
    # a data de exclusão (no caso de excluídos).

    if datas_curtas:
        out["data_inclusao"] = _expandir_ano(datas_curtas[0])

    # Data exclusão e motivo (apenas se Excluído/Encerrado)
    if out["situacao"] in ("Excluído", "Encerrado"):
        # Identificar motivo primeiro (texto já normalizado por sub() acima)
        excl_pattern = r"Exclusão\s+(por\s+refinanciamento|por\s+portabilidade|Banco)"
        m_motivo = re.search(excl_pattern, ctx_flat, re.IGNORECASE)
        if m_motivo:
            tipo = m_motivo.group(1).lower()
            if "refinan" in tipo:
                out["motivo_exclusao"] = "Exclusão por refinanciamento"
            elif "portabilid" in tipo:
                out["motivo_exclusao"] = "Exclusão por Portabilidade"
            else:
                out["motivo_exclusao"] = "Exclusão Banco"

        # A data de exclusão é a ÚLTIMA data DD/MM/YY antes do motivo (no
        # text-layer do HISCON), mas pode estar em qualquer posição. Pegar
        # a última data DD/MM/YY do contexto que NÃO seja a data de inclusão.
        if datas_curtas and len(datas_curtas) >= 2:
            # Eliminar a primeira (data_inclusao) — pegar última distinta
            datas_unique = []
            seen = set()
            for d in datas_curtas:
                if d not in seen:
                    datas_unique.append(d)
                    seen.add(d)
            if len(datas_unique) >= 2:
                # Procurar a data que aparece imediatamente antes da palavra "Exclusão"
                if m_motivo:
                    pos_motivo = m_motivo.start()
                    melhor = None
                    for d in datas_unique:
                        # find última ocorrência de d antes de pos_motivo
                        idx = ctx_compact_dates.rfind(d, 0, pos_motivo + 50)
                        if idx >= 0 and (melhor is None or idx > melhor[1]):
                            melhor = (d, idx)
                    if melhor:
                        out["data_exclusao"] = _expandir_ano(melhor[0])
                else:
                    out["data_exclusao"] = _expandir_ano(datas_unique[-1])

    return out


def _expandir_ano(data_dd_mm_aa: str) -> str:
    """Converte DD/MM/AA para DD/MM/AAAA. Assume 2000+ se AA<70."""
    parts = data_dd_mm_aa.split("/")
    if len(parts) != 3:
        return data_dd_mm_aa
    dd, mm, aa = parts
    aa_int = int(aa)
    if aa_int < 70:
        ano = 2000 + aa_int
    else:
        ano = 1900 + aa_int
    return f"{dd}/{mm}/{ano}"


def parsear_cartao_credito(texto: str, beneficio: dict) -> list[dict]:
    """Parseia tabelas de RMC (Reserva de Margem para Cartão)."""
    contratos = []
    bloco_match = re.search(
        r"CARTÃO DE CRÉDITO - RMC(.+?)(?=DESCONTOS DE CARTÃO|$)", texto, re.DOTALL
    )
    if not bloco_match:
        return contratos
    bloco = bloco_match.group(1)

    linhas = [l.strip() for l in bloco.split("\n") if l.strip()]
    i = 0
    while i < len(linhas):
        l = linhas[i]
        if re.fullmatch(r"\d{6,18}", l):
            ctx = "\n".join(linhas[i+1:i+15])
            dados = _parse_contexto_cartao(l, ctx, beneficio)
            if dados:
                contratos.append(dados)
        i += 1
    return contratos


def _parse_contexto_cartao(contrato: str, ctx: str, beneficio: dict) -> dict | None:
    out = {
        "contrato": contrato,
        "banco_codigo": None,
        "banco": None,
        "situacao": None,
        "origem": None,
        "data_inclusao": None,
        "data_exclusao": None,
        "motivo_exclusao": None,
        "valor_parcela": None,
        "valor_emprestado": None,
        "qtd_parcelas": None,
        "competencia_inicio": None,
        "competencia_fim": None,
        "primeiro_desconto": None,
        "tipo": "RMC",
        "beneficio_nb": beneficio.get("nb"),
        "beneficio_pasta": beneficio.get("pasta_beneficio"),
    }
    ctx_flat = re.sub(r"\s+", " ", ctx).strip()
    m = re.search(r"(\d{3})\s*-\s*(.+?)\s+R\$", ctx_flat)
    if m:
        out["banco_codigo"] = m.group(1).strip()
        nome = m.group(2).strip()
        nome = re.sub(r"\s+", " ", nome)
        nome = nome.replace("CONSIG NADO", "CONSIGNADO")
        nome = nome.replace("S A", "SA").replace("S/A", "SA")
        out["banco"] = nome.strip()
    ctx = ctx_flat  # usar versão compactada nas próximas regex

    valores = re.findall(r"R\$\s*([\d\.,]+)", ctx)
    if valores:
        out["valor_emprestado"] = "R$" + valores[0]
        if len(valores) >= 2:
            out["valor_parcela"] = "R$" + valores[1]

    if "Ativo" in ctx:
        out["situacao"] = "Ativo"
    elif "Excluí" in ctx:
        out["situacao"] = "Excluído"

    m = re.search(r"Averbação\s+(nova|por Refinanciamento|por Portabilidade)", ctx)
    if m:
        out["origem"] = "Averbação " + m.group(1)

    datas = re.findall(r"(\d{2}/\d{2}/\d{2})(?!\d)", ctx)
    if datas:
        out["data_inclusao"] = _expandir_ano(datas[0])
    if out["situacao"] == "Excluído" and len(datas) >= 2:
        out["data_exclusao"] = _expandir_ano(datas[-1])
        if "Exclusão Banco" in ctx:
            out["motivo_exclusao"] = "Exclusão Banco"
        elif "Exclusão por refinanciamento" in ctx:
            out["motivo_exclusao"] = "Exclusão por refinanciamento"
    return out


def parsear_hiscon(pdf_path: str) -> dict:
    """Função principal: parseia HISCON completo."""
    if not has_text_layer(pdf_path):
        return {
            "is_ocr_required": True,
            "beneficio": {},
            "contratos": [],
            "fonte": pdf_path,
        }

    paginas_texto = []
    with _open_pdf(pdf_path) as doc:
        for page in doc:
            paginas_texto.append(page.get_text())
    texto_total = normalizar_texto_extrato(paginas_texto)

    beneficio = parsear_cabecalho(paginas_texto[0])
    contratos_consig = parsear_contratos_consignado(texto_total, beneficio)
    contratos_rmc = parsear_cartao_credito(texto_total, beneficio)

    return {
        "is_ocr_required": False,
        "beneficio": beneficio,
        "contratos": contratos_consig + contratos_rmc,
        "fonte": pdf_path,
    }


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    pdf = sys.argv[1]
    out = sys.argv[2]
    resultado = parsear_hiscon(pdf)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    benef = resultado["beneficio"]
    print(f"Benefício: NB {benef.get('nb')} — {benef.get('especie')}")
    print(f"Total de contratos parseados: {len(resultado['contratos'])}")


if __name__ == "__main__":
    main()
