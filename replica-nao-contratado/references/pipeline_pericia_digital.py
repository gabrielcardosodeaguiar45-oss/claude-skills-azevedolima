# -*- coding: utf-8 -*-
"""
Pipeline de perícia digital para contratos de empréstimo consignado não contratado.

Executa as 12 verificações (A–L) da `tabela-mestre-achado-piloto.md` sobre os
contratos digitais identificados nas fatias do processo, gera o JSON estruturado
conforme `schema-pericia.md`, e o salva em `_pericia/_pericia.json` ao lado do PDF.

Uso típico (chamado pela skill replica-nao-contratado no passo 4.5 do fluxo):

    from pipeline_pericia_digital import executar_pericia, carregar_cache

    cache = carregar_cache(pasta_processo)
    if cache:
        pericia = cache
    else:
        pericia = executar_pericia(
            pasta_processo,
            contratos_digitais=[...],   # lista de dicts com numero/banco/etc
            textos_ccb=[...],            # lista de strings (texto extraído)
            textos_trilha=[...],         # idem
            comprovantes_ted=[...],      # idem
            hiscre_por_competencia={...},
            endereco_autora="...",
            uf_autora="AL"
        )

NÃO automatiza:
    - Validador ITI (verificação B): print externo manual
    - Comparação visual de selfies (H.2): exige leitura visual nativa de Claude

Dependências: pymupdf (fitz), Pillow opcional para imagens.
"""
from __future__ import annotations

import os
import re
import json
import hashlib
import datetime
import ipaddress
import unicodedata
from typing import Optional


# ============================================================
# UTILITÁRIOS
# ============================================================

def _slug(s: str, mx: int = 50) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:mx]


def _norm(s: Optional[str]) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip().lower()


def _hash_sha256_arquivo(caminho_arquivo: str) -> Optional[str]:
    """Calcula SHA-256 de um arquivo (PDF, imagem, etc.)."""
    if not caminho_arquivo or not os.path.isfile(caminho_arquivo):
        return None
    h = hashlib.sha256()
    with open(caminho_arquivo, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


# ============================================================
# DDD-UF (verificação J)
# ============================================================

DDD_UF = {
    # AC
    "68": "AC",
    # AL
    "82": "AL",
    # AM
    "92": "AM", "97": "AM",
    # AP
    "96": "AP",
    # BA
    "71": "BA", "73": "BA", "74": "BA", "75": "BA", "77": "BA",
    # CE
    "85": "CE", "88": "CE",
    # DF
    "61": "DF",
    # ES
    "27": "ES", "28": "ES",
    # GO
    "62": "GO", "64": "GO",
    # MA
    "98": "MA", "99": "MA",
    # MG
    "31": "MG", "32": "MG", "33": "MG", "34": "MG", "35": "MG", "37": "MG", "38": "MG",
    # MS
    "67": "MS",
    # MT
    "65": "MT", "66": "MT",
    # PA
    "91": "PA", "93": "PA", "94": "PA",
    # PB
    "83": "PB",
    # PE
    "81": "PE", "87": "PE",
    # PI
    "86": "PI", "89": "PI",
    # PR
    "41": "PR", "42": "PR", "43": "PR", "44": "PR", "45": "PR", "46": "PR",
    # RJ
    "21": "RJ", "22": "RJ", "24": "RJ",
    # RN
    "84": "RN",
    # RO
    "69": "RO",
    # RR
    "95": "RR",
    # RS
    "51": "RS", "53": "RS", "54": "RS", "55": "RS",
    # SC
    "47": "SC", "48": "SC", "49": "SC",
    # SE
    "79": "SE",
    # SP
    "11": "SP", "12": "SP", "13": "SP", "14": "SP", "15": "SP", "16": "SP",
    "17": "SP", "18": "SP", "19": "SP",
    # TO
    "63": "TO",
}


# ============================================================
# VERIFICAÇÕES INDIVIDUAIS A–L
# ============================================================

def verificar_A_email(texto_ccb: str) -> dict:
    """A — E-mail cadastrado. Detecta vazio, placeholder, e-mail do banco."""
    # Buscar campo e-mail
    match = re.search(r"e-?mail[:\s]+([\S@]+)", texto_ccb, re.IGNORECASE)
    valor = match.group(1).strip() if match else ""
    valor = valor.strip(".,;:\n")

    if not valor or valor in ("-", "—"):
        return {
            "resultado": "vazio",
            "valor": None,
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-digital/inconsistencias-dados-cadastrais",
            "variante": "A.1",
            "texto_achado": "Campo e-mail vazio na CCB - em contratacao supostamente digital, ausencia injustificavel"
        }

    # Placeholder
    placeholders = ["nnnn@", "email@email", "xxx@xxx", "test@", "noreply@", "abc@"]
    if any(p in valor.lower() for p in placeholders):
        return {
            "resultado": "irregular",
            "valor": valor,
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-digital/inconsistencias-dados-cadastrais",
            "variante": "A.2",
            "texto_achado": f"Campo e-mail preenchido com placeholder generico ({valor}), sem correspondencia com endereco real"
        }

    # E-mail do próprio banco (heurística por domínio)
    bancos_dominios = ["safra.com.br", "itau.com.br", "bradesco.com.br", "santander.com.br",
                       "panamericano", "c6consig", "daycoval", "bb.com.br"]
    for dom in bancos_dominios:
        if dom in valor.lower():
            return {
                "resultado": "irregular",
                "valor": valor,
                "risco": "ALTO",
                "piloto_acionado": "merito-probatorio-digital/inconsistencias-dados-cadastrais",
                "variante": "A.3",
                "texto_achado": f"Identificacao eletronica por e-mail do proprio banco ({valor}), nao por e-mail pessoal do consumidor"
            }

    return {
        "resultado": "compativel",
        "valor": valor,
        "risco": "BAIXO",
        "piloto_acionado": None,
        "variante": None,
        "texto_achado": None
    }


def verificar_B_iti(numero_contrato: str) -> dict:
    """B — Validador ITI. Retorna placeholder MANUAL — exige print externo."""
    return {
        "resultado": "manual",
        "valor_validador": None,
        "risco": "manual",
        "piloto_acionado": "merito-probatorio-digital/assinatura-invalida-validador-iti",
        "variante": "B.1",
        "texto_achado": f"Validador ITI requer consulta externa em validar.iti.gov.br para o contrato {numero_contrato}",
        "placeholder_visual": f"[INSERIR — Imagem: print do validador ITI para o contrato {numero_contrato}, demonstrando assinatura INVALIDA]"
    }


def verificar_C_hash(caminho_pdf_contrato: str, hash_esperado: Optional[str] = None,
                     hashes_outros_contratos: Optional[dict] = None) -> dict:
    """
    C — Hash SHA-256.
    - hash_esperado: se a CCB imprime um hash, comparar.
    - hashes_outros_contratos: dict {contrato: hash} — para detectar idêntico entre contratos (C.3).
    """
    calculado = _hash_sha256_arquivo(caminho_pdf_contrato)

    if hash_esperado and calculado:
        if calculado.split(":")[1] != hash_esperado.split(":")[-1]:
            return {
                "resultado": "irregular",
                "hash_calculado": calculado,
                "hash_esperado": hash_esperado,
                "compartilhado_com": [],
                "risco": "ALTO",
                "piloto_acionado": "merito-probatorio-digital/codigo-hash",
                "variante": "C.1",
                "texto_achado": f"Hash impresso na CCB ({hash_esperado}) diverge do calculado ({calculado}) - documento adulterado, efeito avalanche (REsp 2.159.442/PR)"
            }

    # C.3 — idêntico entre contratos
    compartilhado = []
    if calculado and hashes_outros_contratos:
        for outro_num, outro_hash in hashes_outros_contratos.items():
            if outro_hash == calculado:
                compartilhado.append(outro_num)

    if compartilhado:
        # Decisão flexível por caso concreto: se há ≥3 padrões na matriz cruzada,
        # acionar kit-fraude; caso contrário, cadeia-custodia. A skill réplica decide
        # com base no `padroes_count` da matriz cruzada após consolidação.
        return {
            "resultado": "irregular",
            "hash_calculado": calculado,
            "hash_esperado": None,
            "compartilhado_com": compartilhado,
            "risco": "ALTO",
            "piloto_acionado": "FLEX:kit-fraude_OU_cadeia-custodia",  # decidido na consolidação
            "variante": "C.3",
            "texto_achado": f"Hash SHA-256 do contrato identico ao(s) contrato(s) {', '.join(compartilhado)} - mesmo PDF reutilizado"
        }

    if not hash_esperado:
        return {
            "resultado": "ausente",
            "hash_calculado": calculado,
            "hash_esperado": None,
            "compartilhado_com": [],
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-digital/ausencia-codigo-hash",
            "variante": "C.2",
            "texto_achado": "CCB desprovida de codigo hash impresso - impossivel verificar integridade"
        }

    return {
        "resultado": "compativel",
        "hash_calculado": calculado,
        "hash_esperado": hash_esperado,
        "compartilhado_com": [],
        "risco": "BAIXO",
        "piloto_acionado": None,
        "variante": None,
        "texto_achado": None
    }


def verificar_D_metadados(caminho_pdf: str, data_alegada_contrato: str) -> dict:
    """D — Metadados do PDF. Compara data de criação/modificação com data alegada."""
    try:
        import fitz
        doc = fitz.open(caminho_pdf)
        meta = doc.metadata or {}
        doc.close()
    except Exception as e:
        return {
            "resultado": "erro",
            "data_criacao": None, "data_modificacao": None,
            "software": None, "data_alegada_contrato": data_alegada_contrato,
            "risco": "manual",
            "piloto_acionado": None, "variante": None,
            "texto_achado": f"Erro ao ler metadados: {e}"
        }

    data_criacao = meta.get("creationDate", "") or ""
    data_mod = meta.get("modDate", "") or ""
    software = (meta.get("producer") or "") + " | " + (meta.get("creator") or "")
    software = software.strip(" | ")

    # Parse de data PDF (formato D:YYYYMMDDHHmmSS...)
    def _parse_pdf_date(s):
        m = re.search(r"D:(\d{4})(\d{2})(\d{2})", s)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        return None

    dc = _parse_pdf_date(data_criacao)
    dm = _parse_pdf_date(data_mod)

    # Software automatizado
    softs_problematicos = ["Aspose", "PDFium", "iText", "ReportLab"]
    soft_problematico = any(s.lower() in software.lower() for s in softs_problematicos)

    # D.1 - criação posterior
    if dc and data_alegada_contrato:
        try:
            d_criacao = datetime.date.fromisoformat(dc)
            d_alegada = datetime.date.fromisoformat(data_alegada_contrato)
            if d_criacao > d_alegada + datetime.timedelta(days=30):
                return {
                    "resultado": "irregular",
                    "data_criacao": dc, "data_modificacao": dm,
                    "software": software, "data_alegada_contrato": data_alegada_contrato,
                    "risco": "ALTO",
                    "piloto_acionado": "merito-probatorio-digital/analise-metadados",
                    "variante": "D.1",
                    "texto_achado": f"Metadados revelam criacao do arquivo em {dc}, posterior a data alegada de contratacao {data_alegada_contrato} - indicio de adulteracao"
                }
        except Exception:
            pass

    if soft_problematico:
        return {
            "resultado": "irregular",
            "data_criacao": dc, "data_modificacao": dm,
            "software": software, "data_alegada_contrato": data_alegada_contrato,
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-digital/analise-metadados",
            "variante": "D.2",
            "texto_achado": f"Documento gerado por software automatizado ({software}), incompativel com fluxo de assinatura digital legitima"
        }

    # D.3 — modificação posterior à criação
    if dc and dm and dm != dc:
        return {
            "resultado": "irregular",
            "data_criacao": dc, "data_modificacao": dm,
            "software": software, "data_alegada_contrato": data_alegada_contrato,
            "risco": "MEDIO",
            "piloto_acionado": "merito-probatorio-digital/analise-metadados",
            "variante": "D.3",
            "texto_achado": f"Documento modificado em {dm}, apos criacao em {dc} - quebra de integridade pos-assinatura"
        }

    return {
        "resultado": "compativel",
        "data_criacao": dc, "data_modificacao": dm,
        "software": software, "data_alegada_contrato": data_alegada_contrato,
        "risco": "BAIXO",
        "piloto_acionado": None, "variante": None, "texto_achado": None
    }


def verificar_E_F_ip_geo(texto_trilha: str, endereco_autora_uf: str = "",
                          ips_outros_contratos: Optional[dict] = None) -> dict:
    """E — IP + F — Geolocalização (combinados)."""
    # Buscar IP
    m_ip = re.search(r"IP[:\s]+(\d+\.\d+\.\d+\.\d+)", texto_trilha)
    ip_valor = m_ip.group(1) if m_ip else None

    if not ip_valor:
        return {
            "resultado": "nao_aplicavel",
            "valor": None, "tipo": None,
            "geolocalizacao": None, "distancia_residencia_km": None,
            "compartilhado_com": [],
            "risco": "BAIXO", "piloto_acionado": None, "variante": None,
            "texto_achado": None
        }

    # Classificar
    try:
        ip_obj = ipaddress.ip_address(ip_valor)
        eh_privado = ip_obj.is_private
    except Exception:
        eh_privado = False

    # Compartilhamento
    compartilhado = []
    if ips_outros_contratos:
        for outro_num, outro_ip in ips_outros_contratos.items():
            if outro_ip == ip_valor:
                compartilhado.append(outro_num)

    if eh_privado:
        return {
            "resultado": "irregular",
            "valor": ip_valor, "tipo": "privado_RFC1918",
            "geolocalizacao": None, "distancia_residencia_km": None,
            "compartilhado_com": compartilhado,
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-digital/ip-desconhecido",
            "variante": "E.1",
            "texto_achado": f"IP {ip_valor} pertence a faixa privada RFC 1918 - acesso originado em rede corporativa interna, nao domestica"
        }

    # IP público — geolocalização requer chamada externa, marcar como manual aqui
    # F + E combinados: verificar coords explícitas na trilha
    m_geo = re.search(r"(-?\d+\.\d+),\s*(-?\d+\.\d+)", texto_trilha)
    coords = None
    if m_geo:
        coords = {"lat": float(m_geo.group(1)), "lon": float(m_geo.group(2))}

    # Sem geolocalização automática — registra manual
    return {
        "resultado": "verificar",
        "valor": ip_valor, "tipo": "publico",
        "geolocalizacao": coords, "distancia_residencia_km": None,
        "compartilhado_com": compartilhado,
        "risco": "manual",
        "piloto_acionado": "merito-probatorio-misto/ip-correspondente-bancario",
        "variante": "E.2",
        "texto_achado": f"IP publico {ip_valor} - geolocalizar via ipinfo.io e comparar com residencia da autora ({endereco_autora_uf})"
    }


def verificar_G_sessao(texto_trilha: str, sessoes_outros_contratos: Optional[dict] = None,
                        horario_aceite: Optional[str] = None,
                        horarios_outros: Optional[dict] = None) -> dict:
    """G — Session ID + horário do aceite."""
    m_sess = re.search(r"(?:session|sess[ãa]o|ID\s*sess[ãa]o|SessionID)[:\s]+(\S+)",
                       texto_trilha, re.IGNORECASE)
    sess_id = m_sess.group(1).strip() if m_sess else None

    # Trilha 100% Incompleto (G.3)
    incompletas = re.findall(r"Incompleto", texto_trilha, re.IGNORECASE)
    if len(incompletas) >= 3:
        return {
            "resultado": "irregular",
            "id": sess_id,
            "compartilhada_com": [],
            "horario_aceite": horario_aceite,
            "horarios_proximos_outros": [],
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-digital/inconsistencias-trilha-auditoria",
            "variante": "G.3",
            "texto_achado": "Trilha de auditoria com status 'Incompleto' em todos os passos, incluindo a etapa final"
        }

    # G.1 — sessão compartilhada
    compartilhada = []
    if sess_id and sessoes_outros_contratos:
        for outro_num, outra_sess in sessoes_outros_contratos.items():
            if outra_sess == sess_id:
                compartilhada.append(outro_num)
    if compartilhada:
        return {
            "resultado": "irregular",
            "id": sess_id, "compartilhada_com": compartilhada,
            "horario_aceite": horario_aceite, "horarios_proximos_outros": [],
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-digital/inconsistencias-trilha-auditoria",
            "variante": "G.1",
            "texto_achado": f"Session ID {sess_id} repetido nos contratos {', '.join(compartilhada)} - operacao automatizada em lote"
        }

    # G.2 — aceite ao segundo
    proximos = []
    if horario_aceite and horarios_outros:
        try:
            this_t = datetime.datetime.fromisoformat(horario_aceite)
            for outro_num, outro_h in horarios_outros.items():
                outro_t = datetime.datetime.fromisoformat(outro_h)
                diff = abs((this_t - outro_t).total_seconds())
                if diff < 60:
                    proximos.append({"contrato": outro_num, "horario": outro_h,
                                      "diferenca_segundos": int(diff)})
        except Exception:
            pass

    if proximos:
        return {
            "resultado": "irregular",
            "id": sess_id, "compartilhada_com": [],
            "horario_aceite": horario_aceite, "horarios_proximos_outros": proximos,
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-digital/trilha-incompativel-comportamento-humano",
            "variante": "G.2",
            "texto_achado": f"Aceite registrado as {horario_aceite} com diferenca <=60s do(s) outro(s) contrato(s) - humanamente impossivel"
        }

    return {
        "resultado": "compativel" if sess_id else "nao_aplicavel",
        "id": sess_id, "compartilhada_com": [],
        "horario_aceite": horario_aceite, "horarios_proximos_outros": [],
        "risco": "BAIXO",
        "piloto_acionado": None, "variante": None, "texto_achado": None
    }


def verificar_H_selfie(presente: bool, hash_selfie: Optional[str] = None,
                        hashes_outros_contratos: Optional[dict] = None,
                        rg_impossibilidade_assinar: bool = False) -> dict:
    """H — Selfie / liveness. Comparação visual entre contratos exige Claude visual."""
    # H.1 — ausente
    if not presente:
        return {
            "resultado": "ausente", "presente": False,
            "reutilizada_com": [], "comparacao_visual": None,
            "liveness_adequado": None,
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-digital/selfie-liveness",
            "variante": "H.1", "ativa_kit_fraude": False,
            "texto_achado": "Contrato desprovido de captura biometrica (selfie) - impossivel atestar autoria do ato"
        }

    # H.4 — RG impossibilidade de assinar + selfie pretensamente apresentada
    if rg_impossibilidade_assinar:
        return {
            "resultado": "irregular", "presente": True,
            "reutilizada_com": [], "comparacao_visual": None,
            "liveness_adequado": None,
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-digital/selfie-liveness",
            "variante": "H.4", "ativa_kit_fraude": False,
            "texto_achado": "RG do autor consigna 'IMPOSSIBILIDADE DE ASSINAR', porem banco apresenta selfie como prova de assinatura - inconciliavel",
            "piloto_secundario": "merito-probatorio-misto/contratacao-digital-parte-analfabeta"
        }

    # H.2 — reutilizada (por hash; comparação visual fica para Claude)
    reutilizada = []
    if hash_selfie and hashes_outros_contratos:
        for outro_num, outro_hash in hashes_outros_contratos.items():
            if outro_hash == hash_selfie:
                reutilizada.append(outro_num)

    if reutilizada:
        return {
            "resultado": "reutilizada", "presente": True,
            "reutilizada_com": reutilizada,
            "comparacao_visual": "Hash idêntico - imagem estática reutilizada",
            "liveness_adequado": False,
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-digital/selfie-liveness",
            "variante": "H.2", "ativa_kit_fraude": True,
            "texto_achado": f"Mesma imagem facial detectada (hash idêntico) nos contratos {', '.join(reutilizada)} - imagem estática reutilizada, nao captura ao vivo (violacao ISO 30107-3 / IEEE 2790-2020)"
        }

    return {
        "resultado": "verificar", "presente": True,
        "reutilizada_com": [], "comparacao_visual": "manual: comparar visualmente entre contratos via Claude",
        "liveness_adequado": None,
        "risco": "manual",
        "piloto_acionado": "merito-probatorio-digital/selfie-liveness",
        "variante": "H.3", "ativa_kit_fraude": False,
        "texto_achado": "Selfie presente - comparacao visual entre contratos e analise de liveness exigem leitura visual nativa"
    }


def verificar_I_correspondente(texto_ccb: str, uf_autora: str = "",
                                 corresp_outros_contratos: Optional[dict] = None) -> dict:
    """I — Correspondente bancário."""
    # Buscar campo correspondente / originador
    campos = ["Dados do correspondente", "Dados do originador", "Razão Social do Originador",
              "FONTES PROMOTORA", "PROMOTORA"]
    nome = cidade = cnpj = None
    for campo in campos:
        m = re.search(rf"{re.escape(campo)}[:\s]+([^\n]+)", texto_ccb, re.IGNORECASE)
        if m:
            nome = m.group(1).strip()[:60]
            break

    m_cnpj = re.search(r"CNPJ[:\s]+(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[/\s]?\d{4}[-\s]?\d{2})",
                       texto_ccb)
    if m_cnpj:
        cnpj = m_cnpj.group(1)

    # Cidade — heurística: pegar UF (2 letras maiúsculas) e cidade próxima
    m_cid = re.search(r"([A-Z][A-Za-zçãáéíóúâêôõà ]+)\s*[-/]\s*([A-Z]{2})", texto_ccb)
    cidade_uf = None
    if m_cid:
        cidade_uf = f"{m_cid.group(1).strip()}/{m_cid.group(2)}"

    if not nome and not cidade_uf:
        return {
            "resultado": "nao_aplicavel",
            "nome": None, "cnpj": None, "cidade": None,
            "distancia_km": None, "uf_autora": uf_autora,
            "compartilhado_com_contratos": [], "compartilhado_entre_bancos": False,
            "risco": "BAIXO", "piloto_acionado": None, "variante": None, "texto_achado": None
        }

    # Compartilhamento
    compartilhado = []
    if nome and corresp_outros_contratos:
        for outro_num, outro_nome in corresp_outros_contratos.items():
            if _norm(outro_nome) == _norm(nome):
                compartilhado.append(outro_num)

    # Heurística distância UF (sem geocoding aqui)
    uf_corresp = cidade_uf.split("/")[1] if cidade_uf and "/" in cidade_uf else None
    if uf_corresp and uf_autora and uf_corresp != uf_autora:
        # AM × SC, AL × SP, etc
        return {
            "resultado": "irregular",
            "nome": nome, "cnpj": cnpj, "cidade": cidade_uf,
            "distancia_km": None,  # estimar manual
            "uf_autora": uf_autora,
            "compartilhado_com_contratos": compartilhado,
            "compartilhado_entre_bancos": False,
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-misto/dados-correspondente-originador",
            "variante": "I.1",
            "texto_achado": f"Correspondente {nome} situado em {cidade_uf}, em UF distinta da residencia da autora ({uf_autora}) - inverossimil deslocamento ou contato remoto"
        }

    return {
        "resultado": "verificar" if compartilhado else "compativel",
        "nome": nome, "cnpj": cnpj, "cidade": cidade_uf,
        "distancia_km": None, "uf_autora": uf_autora,
        "compartilhado_com_contratos": compartilhado,
        "compartilhado_entre_bancos": False,
        "risco": "MEDIO" if compartilhado else "BAIXO",
        "piloto_acionado": "merito-probatorio-misto/dados-correspondente-originador" if compartilhado else None,
        "variante": "I.3" if compartilhado else None,
        "texto_achado": f"Correspondente {nome} originou multiplos contratos: {', '.join(compartilhado)}" if compartilhado else None
    }


def verificar_J_telefone(texto_ccb: str, uf_autora: str = "",
                           tels_outros_contratos: Optional[dict] = None) -> dict:
    """J — Telefone (DDD divergente da UF, telefones distintos entre contratos)."""
    m_tel = re.search(r"\((\d{2})\)\s*\d{4,5}-?\d{4}", texto_ccb)
    tel = re.search(r"\(\d{2}\)\s*\d{4,5}-?\d{4}", texto_ccb)
    tel_str = tel.group(0) if tel else None
    ddd = m_tel.group(1) if m_tel else None

    if not ddd:
        return {
            "resultado": "nao_aplicavel",
            "numero": None, "ddd_registrado": None, "ddd_esperado": None,
            "telefones_distintos_outros_contratos": [],
            "risco": "BAIXO", "piloto_acionado": None, "variante": None, "texto_achado": None
        }

    uf_ddd = DDD_UF.get(ddd, "?")

    # J.1 — DDD divergente
    if uf_autora and uf_ddd != uf_autora and uf_ddd != "?":
        return {
            "resultado": "irregular",
            "numero": tel_str, "ddd_registrado": ddd,
            "ddd_esperado": "?", "uf_residencia": uf_autora,
            "uf_telefone": uf_ddd,
            "telefones_distintos_outros_contratos": [],
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-digital/inconsistencias-dados-cadastrais",
            "variante": "J.1",
            "texto_achado": f"Telefone {tel_str} (DDD {ddd} - {uf_ddd}) cadastrado para autora residente em {uf_autora} - incompatibilidade geografica"
        }

    # J.2 — telefones distintos entre contratos
    distintos = []
    if tels_outros_contratos:
        for outro_num, outro_tel in tels_outros_contratos.items():
            if outro_tel and outro_tel != tel_str:
                distintos.append({"contrato": outro_num, "telefone": outro_tel})
    if distintos:
        return {
            "resultado": "irregular",
            "numero": tel_str, "ddd_registrado": ddd,
            "ddd_esperado": uf_autora, "uf_residencia": uf_autora,
            "uf_telefone": uf_ddd,
            "telefones_distintos_outros_contratos": distintos,
            "risco": "MEDIO",
            "piloto_acionado": "merito-probatorio-digital/inconsistencias-dados-cadastrais",
            "variante": "J.2",
            "texto_achado": f"Telefones divergentes entre contratos da mesma autora - dados inseridos por terceiros"
        }

    return {
        "resultado": "compativel",
        "numero": tel_str, "ddd_registrado": ddd,
        "ddd_esperado": uf_autora, "uf_residencia": uf_autora, "uf_telefone": uf_ddd,
        "telefones_distintos_outros_contratos": [],
        "risco": "BAIXO", "piloto_acionado": None, "variante": None, "texto_achado": None
    }


def verificar_K_ausencia(contrato_numero: str, contratos_juntados: list) -> dict:
    """K — Contrato citado mas não juntado."""
    juntado = any(_norm(contrato_numero) in _norm(c) or _norm(c) in _norm(contrato_numero)
                  for c in contratos_juntados)
    if juntado:
        return {
            "resultado": "juntado", "contrato_juntado": True,
            "evidencia_pdf": None, "risco": "BAIXO",
            "piloto_acionado": None, "variante": None, "texto_achado": None
        }
    return {
        "resultado": "ausente", "contrato_juntado": False,
        "evidencia_pdf": None, "risco": "ALTO",
        "piloto_acionado": "processuais-especiais/ausencia-total-contrato-master",
        "variante": "K.1",
        "texto_achado": f"Contrato {contrato_numero} impugnado na inicial nao foi juntado pelo banco - presuncao art. 400, par. unico, CPC"
    }


def verificar_L_ted(texto_comprovante_ted: str, valor_ccb: float,
                     horario_aceite: Optional[str] = None,
                     hiscre_banco_inss_por_competencia: Optional[dict] = None) -> dict:
    """L — TED / PIX. L.1 valor divergente, L.2 horário, L.3 conta divergente HISCRE (CALIBRADO), L.4 ausente, L.5 sem NSU."""
    if not texto_comprovante_ted:
        return {
            "resultado": "ausente",
            "valor_ted": None, "valor_ccb": valor_ccb, "diferenca": None,
            "data_ted": None, "horario_ted": None, "horario_aceite": horario_aceite,
            "banco_destino": None, "agencia_destino": None, "conta_destino": None,
            "banco_inss_hiscre": None, "competencias_verificadas_hiscre": [],
            "destino_coincide_com_inss": None,
            "comprovante_presente": False, "nsu_endtoendid_presente": False,
            "risco": "ALTO",
            "piloto_acionado": "merito-probatorio-misto/insuficiencia-probatoria-prova-unilateral",
            "variante": "L.4",
            "texto_achado": "Banco alega liberacao de credito mas nao junta comprovante SPB - onus probatorio nao atendido"
        }

    # L.5 — NSU/EndToEndID
    tem_nsu = bool(re.search(r"NSU|EndToEndID|E2E", texto_comprovante_ted, re.IGNORECASE))

    # Valor TED
    m_val = re.search(r"R\$?\s*([\d\.]+,\d{2})", texto_comprovante_ted)
    valor_ted = None
    if m_val:
        valor_ted = float(m_val.group(1).replace(".", "").replace(",", "."))

    # Banco destino
    m_bd = re.search(r"(\d{3,4})\s*-\s*(BRADESCO|BANCO\s+[A-Z]+|CAIXA[^\n]*|ITAU[^\n]*|SANTANDER[^\n]*|BANCO\s+DO\s+BRASIL)",
                     texto_comprovante_ted, re.IGNORECASE)
    banco_dest = m_bd.group(0) if m_bd else None
    cod_banco_dest = m_bd.group(1) if m_bd else None

    # Agência/conta
    m_ag = re.search(r"AG[ÊE]NCIA[:\s]+(\d+)", texto_comprovante_ted, re.IGNORECASE)
    m_cc = re.search(r"CONTA[:\s]+(\d[\d\.\-]+)", texto_comprovante_ted, re.IGNORECASE)
    ag_dest = m_ag.group(1) if m_ag else None
    cc_dest = m_cc.group(1) if m_cc else None

    # L.3 — destino coincide com banco INSS no HISCRE?
    coincide = None
    competencias_ver = []
    if hiscre_banco_inss_por_competencia and cod_banco_dest:
        for compet, banco_hiscre in hiscre_banco_inss_por_competencia.items():
            competencias_ver.append(compet)
            # Heurística: extrair primeiro número
            m_h = re.match(r"(\d+)", str(banco_hiscre))
            cod_hiscre = m_h.group(1) if m_h else ""
            if cod_hiscre and cod_hiscre.lstrip("0") == cod_banco_dest.lstrip("0"):
                coincide = True
                break
        else:
            coincide = False

    if coincide is False:
        # L.3 ATIVO — calibrado
        return {
            "resultado": "irregular",
            "valor_ted": valor_ted, "valor_ccb": valor_ccb,
            "diferenca": (valor_ted - valor_ccb) if valor_ted else None,
            "data_ted": None, "horario_ted": None, "horario_aceite": horario_aceite,
            "banco_destino": banco_dest, "agencia_destino": ag_dest, "conta_destino": cc_dest,
            "banco_inss_hiscre": list(hiscre_banco_inss_por_competencia.values())[0] if hiscre_banco_inss_por_competencia else None,
            "competencias_verificadas_hiscre": competencias_ver,
            "destino_coincide_com_inss": False,
            "comprovante_presente": True, "nsu_endtoendid_presente": tem_nsu,
            "risco": "ALTO",
            "piloto_acionado": "merito-argumentativo/compensacao-valores-tese-nova",
            "variante": "L.3",
            "texto_calibrado_etico": "PROIBIDO afirmar 'conta de terceiro' / 'autora nao recebeu' / pedir intimacao - apenas mencionar divergencia + 'autora nao percebeu o deposito' + acionar tese da compensacao",
            "texto_achado": f"TED destinado a {banco_dest} (ag {ag_dest}, conta {cc_dest}), conta diversa daquela em que a autora recebia INSS na epoca ({list(hiscre_banco_inss_por_competencia.values())[0] if hiscre_banco_inss_por_competencia else '?'}). Aciona-se a tese da compensacao - o deposito nao e prova de contratacao, mas elemento da fraude."
        }

    # L.1 — valor divergente
    if valor_ted and valor_ccb:
        diff = abs(valor_ted - valor_ccb)
        if diff > 1.0:  # ignorar diferenças centavos
            return {
                "resultado": "irregular",
                "valor_ted": valor_ted, "valor_ccb": valor_ccb, "diferenca": diff,
                "data_ted": None, "horario_ted": None, "horario_aceite": horario_aceite,
                "banco_destino": banco_dest, "agencia_destino": ag_dest, "conta_destino": cc_dest,
                "banco_inss_hiscre": None, "competencias_verificadas_hiscre": competencias_ver,
                "destino_coincide_com_inss": coincide,
                "comprovante_presente": True, "nsu_endtoendid_presente": tem_nsu,
                "risco": "ALTO",
                "piloto_acionado": "merito-argumentativo/compensacao-valores-tese-nova",
                "variante": "L.1",
                "texto_achado": f"Valor do TED (R$ {valor_ted:.2f}) divergente do valor liberado na CCB (R$ {valor_ccb:.2f}), diferenca de R$ {diff:.2f}"
            }

    # L.5 — sem NSU
    if not tem_nsu:
        return {
            "resultado": "irregular",
            "valor_ted": valor_ted, "valor_ccb": valor_ccb,
            "diferenca": 0.0,
            "data_ted": None, "horario_ted": None, "horario_aceite": horario_aceite,
            "banco_destino": banco_dest, "agencia_destino": ag_dest, "conta_destino": cc_dest,
            "banco_inss_hiscre": None, "competencias_verificadas_hiscre": competencias_ver,
            "destino_coincide_com_inss": coincide,
            "comprovante_presente": True, "nsu_endtoendid_presente": False,
            "risco": "MEDIO",
            "piloto_acionado": "merito-probatorio-misto/insuficiencia-probatoria-prova-unilateral",
            "variante": "L.5",
            "texto_achado": "Comprovante apresentado nao traz NSU ou EndToEndID - impossibilidade de rastreamento tecnico da operacao"
        }

    return {
        "resultado": "compativel",
        "valor_ted": valor_ted, "valor_ccb": valor_ccb, "diferenca": 0.0,
        "data_ted": None, "horario_ted": None, "horario_aceite": horario_aceite,
        "banco_destino": banco_dest, "agencia_destino": ag_dest, "conta_destino": cc_dest,
        "banco_inss_hiscre": None, "competencias_verificadas_hiscre": competencias_ver,
        "destino_coincide_com_inss": coincide,
        "comprovante_presente": True, "nsu_endtoendid_presente": tem_nsu,
        "risco": "BAIXO", "piloto_acionado": None, "variante": None, "texto_achado": None
    }


# ============================================================
# CONSOLIDAÇÃO DA MATRIZ CRUZADA
# ============================================================

def consolidar_matriz_cruzada(contratos_pericia: list) -> dict:
    """Recebe lista de contratos com achados e gera tabela cruzada."""
    if len(contratos_pericia) < 2:
        return {"tabela_comparativa": [], "padroes_count": 0,
                "ativa_kit_fraude": False, "ativa_cadeia_custodia": False,
                "observacao_padrao": "Apenas 1 contrato digital — matriz cruzada nao aplicavel"}

    tabela = []

    def _coletar(campo: str, getter) -> dict:
        d = {}
        for c in contratos_pericia:
            val = getter(c)
            if val is not None:
                d[c["numero"]] = val
        return d

    pares = [
        ("ip",            lambda c: (c["achados"].get("E_ip") or {}).get("valor")),
        ("sessao",        lambda c: (c["achados"].get("G_sessao") or {}).get("id")),
        ("correspondente",lambda c: (c["achados"].get("I_correspondente") or {}).get("nome")),
        ("horario_aceite",lambda c: (c["achados"].get("G_sessao") or {}).get("horario_aceite")),
        ("hash_pdf",      lambda c: (c["achados"].get("C_hash") or {}).get("hash_calculado")),
        ("selfie_hash",   lambda c: (c["achados"].get("H_selfie") or {}).get("hash_selfie")),
    ]

    padroes_count = 0
    for campo, getter in pares:
        valores = _coletar(campo, getter)
        # Detecta padrão se houver ≥2 contratos com mesmo valor
        from collections import Counter
        contagem = Counter(valores.values())
        repetidos = {v: ct for v, ct in contagem.items() if ct >= 2 and v}
        padrao = bool(repetidos)
        if padrao:
            padroes_count += 1
        tabela.append({
            "campo": campo,
            "linhas": [{"contrato": k, "valor": v} for k, v in valores.items()],
            "padrao_detectado": padrao
        })

    ativa_kit_fraude = padroes_count >= 3
    ativa_cadeia_custodia = (padroes_count >= 1 and padroes_count < 3)

    obs = ""
    if ativa_kit_fraude:
        obs = f"{padroes_count} padroes sistemicos detectados — esquema estruturado, aciona kit-fraude"
    elif ativa_cadeia_custodia:
        obs = f"{padroes_count} padrao(es) isolado(s) — quebra de individualizacao, aciona cadeia-custodia-digital-inexistente"
    else:
        obs = "Sem padroes sistemicos entre os contratos digitais"

    return {
        "tabela_comparativa": tabela,
        "padroes_count": padroes_count,
        "ativa_kit_fraude": ativa_kit_fraude,
        "ativa_cadeia_custodia": ativa_cadeia_custodia,
        "observacao_padrao": obs
    }


# ============================================================
# CLASSIFICAÇÃO INDIVIDUAL DO CONTRATO
# ============================================================

def classificar_contrato(achados: dict) -> str:
    """ALTO_RISCO se ≥3 achados ALTO; MEDIO se 2 ALTO; senão BAIXO."""
    riscos = [a.get("risco") for a in achados.values() if isinstance(a, dict)]
    altos = sum(1 for r in riscos if r == "ALTO")
    medios = sum(1 for r in riscos if r == "MEDIO")
    if altos >= 3:
        return "ALTO_RISCO"
    if altos >= 1 or medios >= 2:
        return "MEDIO_RISCO"
    return "BAIXO_RISCO"


# ============================================================
# ORQUESTRAÇÃO
# ============================================================

def executar_pericia(pasta_processo: str, contratos_digitais: list,
                      textos_ccb: list, textos_trilha: list,
                      caminhos_pdf_contratos: list,
                      comprovantes_ted: list,
                      hiscre_por_competencia: Optional[dict] = None,
                      contratos_juntados: Optional[list] = None,
                      meta_processo: Optional[dict] = None) -> dict:
    """
    Executa todas as verificações para a lista de contratos digitais e gera o JSON.

    Listas paralelas indexadas pelo mesmo i: contratos_digitais[i] usa
    textos_ccb[i], textos_trilha[i], caminhos_pdf_contratos[i], comprovantes_ted[i].
    """
    contratos_juntados = contratos_juntados or [c["numero"] for c in contratos_digitais]

    # Hashes calculados (necessário para C.3)
    hashes_calc = {}
    for i, c in enumerate(contratos_digitais):
        if i < len(caminhos_pdf_contratos):
            h = _hash_sha256_arquivo(caminhos_pdf_contratos[i]) if caminhos_pdf_contratos[i] else None
            if h:
                hashes_calc[c["numero"]] = h

    # IPs e sessões já extraídos para detectar compartilhamento
    ips_pre = {}
    sess_pre = {}
    horarios_pre = {}
    corresp_pre = {}
    tels_pre = {}
    for i, c in enumerate(contratos_digitais):
        txt = textos_trilha[i] if i < len(textos_trilha) else ""
        ccb_txt = textos_ccb[i] if i < len(textos_ccb) else ""
        m_ip = re.search(r"IP[:\s]+(\d+\.\d+\.\d+\.\d+)", txt)
        if m_ip: ips_pre[c["numero"]] = m_ip.group(1)
        m_s = re.search(r"(?:session|ID\s*sess)[:\s]+(\S+)", txt, re.IGNORECASE)
        if m_s: sess_pre[c["numero"]] = m_s.group(1).strip()
        m_h = re.search(r"(\d{2}:\d{2}:\d{2})", txt)
        if m_h and c.get("data_alegada"):
            horarios_pre[c["numero"]] = f"{c['data_alegada']}T{m_h.group(1)}"
        m_corr = re.search(r"(?:correspondente|originador)[:\s]+([^\n]+)", ccb_txt, re.IGNORECASE)
        if m_corr: corresp_pre[c["numero"]] = m_corr.group(1).strip()[:60]
        m_tel = re.search(r"\(\d{2}\)\s*\d{4,5}-?\d{4}", ccb_txt)
        if m_tel: tels_pre[c["numero"]] = m_tel.group(0)

    # Loop principal
    contratos_pericia = []
    for i, c in enumerate(contratos_digitais):
        ccb_txt = textos_ccb[i] if i < len(textos_ccb) else ""
        trl_txt = textos_trilha[i] if i < len(textos_trilha) else ""
        ted_txt = comprovantes_ted[i] if i < len(comprovantes_ted) else ""
        pdf = caminhos_pdf_contratos[i] if i < len(caminhos_pdf_contratos) else None
        num = c["numero"]

        # Outros contratos (excluir o atual)
        outros_ips   = {k: v for k, v in ips_pre.items() if k != num}
        outros_sess  = {k: v for k, v in sess_pre.items() if k != num}
        outros_hor   = {k: v for k, v in horarios_pre.items() if k != num}
        outros_corr  = {k: v for k, v in corresp_pre.items() if k != num}
        outros_tels  = {k: v for k, v in tels_pre.items() if k != num}
        outros_hash  = {k: v for k, v in hashes_calc.items() if k != num}

        achados = {
            "A_email": verificar_A_email(ccb_txt),
            "B_iti": verificar_B_iti(num),
            "C_hash": verificar_C_hash(pdf, hash_esperado=c.get("hash_esperado"),
                                        hashes_outros_contratos=outros_hash) if pdf else
                       {"resultado": "nao_aplicavel", "risco": "BAIXO", "piloto_acionado": None,
                        "variante": None, "texto_achado": None,
                        "hash_calculado": None, "hash_esperado": None, "compartilhado_com": []},
            "D_metadados": verificar_D_metadados(pdf, c.get("data_alegada", "")) if pdf else
                            {"resultado": "nao_aplicavel", "risco": "BAIXO",
                             "piloto_acionado": None, "variante": None, "texto_achado": None,
                             "data_criacao": None, "data_modificacao": None, "software": None,
                             "data_alegada_contrato": c.get("data_alegada")},
            "E_ip": verificar_E_F_ip_geo(trl_txt, c.get("uf_autora", ""), outros_ips),
            "F_geo": {"resultado": "combinado_com_E", "lat": None, "lon": None,
                       "distancia_residencia_km": None, "risco": "BAIXO",
                       "piloto_acionado": None, "variante": None, "texto_achado": None},
            "G_sessao": verificar_G_sessao(trl_txt, outros_sess,
                                            horarios_pre.get(num), outros_hor),
            "H_selfie": verificar_H_selfie(c.get("selfie_presente", False),
                                            hash_selfie=c.get("hash_selfie"),
                                            hashes_outros_contratos={k: v for k, v in
                                                {co["numero"]: co.get("hash_selfie")
                                                 for co in contratos_digitais if co["numero"] != num}.items()
                                                if v},
                                            rg_impossibilidade_assinar=c.get("rg_impossibilidade_assinar", False)),
            "I_correspondente": verificar_I_correspondente(ccb_txt, c.get("uf_autora", ""), outros_corr),
            "J_telefone": verificar_J_telefone(ccb_txt, c.get("uf_autora", ""), outros_tels),
            "K_ausencia": verificar_K_ausencia(num, contratos_juntados),
            "L_ted": verificar_L_ted(ted_txt, c.get("valor_liberado", 0.0),
                                       horarios_pre.get(num), hiscre_por_competencia),
        }

        achados_aplicaveis = sum(1 for a in achados.values()
                                  if isinstance(a, dict) and a.get("piloto_acionado"))
        achados_alto = sum(1 for a in achados.values()
                            if isinstance(a, dict) and a.get("risco") == "ALTO")

        contratos_pericia.append({
            **c,
            "achados": achados,
            "achados_aplicaveis_count": achados_aplicaveis,
            "achados_alto_risco_count": achados_alto,
            "classificacao_individual": classificar_contrato(achados)
        })

    # Matriz cruzada
    matriz = consolidar_matriz_cruzada(contratos_pericia)

    # Resolver C.3 flexível: se kit-fraude está ativa, usar kit-fraude; senão cadeia-custodia
    for c in contratos_pericia:
        ach_c = c["achados"].get("C_hash") or {}
        if ach_c.get("piloto_acionado") == "FLEX:kit-fraude_OU_cadeia-custodia":
            if matriz["ativa_kit_fraude"]:
                ach_c["piloto_acionado"] = "merito-probatorio-digital/kit-fraude"
            else:
                ach_c["piloto_acionado"] = "merito-probatorio-digital/cadeia-custodia-digital-inexistente"

    # Padrões sistêmicos como strings prontas
    padroes = []
    for col in matriz["tabela_comparativa"]:
        if col["padrao_detectado"]:
            valores = [l["valor"] for l in col["linhas"]]
            from collections import Counter
            mc = Counter(valores).most_common(1)[0]
            contratos_compartilhando = [l["contrato"] for l in col["linhas"] if l["valor"] == mc[0]]
            padroes.append(
                f"{col['campo'].upper()}: valor '{mc[0]}' compartilhado entre os contratos "
                f"{', '.join(contratos_compartilhando)}"
            )

    # Alertas
    alertas = []
    for c in contratos_pericia:
        if c["achados"]["B_iti"]["risco"] == "manual":
            alertas.append(f"Validador ITI do contrato {c['numero']}: print externo manual pendente")
        if c["achados"]["L_ted"].get("variante") == "L.3":
            alertas.append(
                f"L.3 ATIVO no contrato {c['numero']}: TED para conta diversa do INSS - usar tese CALIBRADA "
                "(NAO afirmar 'conta de terceiro' / 'autora nao recebeu' / pedir intimacao)"
            )

    pericia_json = {
        "meta": meta_processo or {},
        "contratos_digitais": contratos_pericia,
        "matriz_cruzada": matriz,
        "padroes_sistemicos": padroes,
        "alertas": alertas
    }
    return pericia_json


def salvar_pericia(pasta_processo: str, pericia: dict) -> str:
    """Salva o JSON em _pericia/_pericia.json e retorna o caminho."""
    dest = os.path.join(pasta_processo, "_pericia")
    os.makedirs(dest, exist_ok=True)
    caminho = os.path.join(dest, "_pericia.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(pericia, f, ensure_ascii=False, indent=2)
    return caminho


def carregar_cache(pasta_processo: str) -> Optional[dict]:
    """Carrega _pericia.json se existe (cache). Retorna None se não."""
    caminho = os.path.join(pasta_processo, "_pericia", "_pericia.json")
    if os.path.isfile(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
