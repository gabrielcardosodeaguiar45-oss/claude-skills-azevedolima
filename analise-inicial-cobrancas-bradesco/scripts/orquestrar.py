# -*- coding: utf-8 -*-
"""
Orquestrador da skill `analise-inicial-cobrancas-bradesco`.

Recebe o caminho da pasta do cliente (ou da subpasta da ação), localiza os
arquivos relevantes, roda todos os scripts e gera os DOCX de saída.

Uso:

    python orquestrar.py "<caminho-da-pasta>" "<pasta-saida>" "<nome-cliente>"
"""
from __future__ import annotations

import os
import sys
import re
import json
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SKILL_DIR)

from docx_helper import PecaDocx
from tipo_acao import detectar_tipo, carregar_teses
from cruzamento_extrato import cruzar_extrato
from cruzamento_tabela import cruzar_tabela
from procuracao_objeto import verificar_procuracao
from notificacao_check import verificar_notificacao
from prioridade_idoso import verificar_idoso
from comarca_residencia import verificar_comarca
from placeholders import detectar_placeholders
from peca_nao_adaptada import analisar as analisar_modelo
from oab_check import verificar_oab, localizar_advogado
from gerar_relatorio import gerar_relatorio_e_edicoes


# ---------------------------------------------------------------- #
# Localização de arquivos na pasta
# ---------------------------------------------------------------- #
def _busca_arquivo(pasta: str, padroes: List[str]) -> Optional[str]:
    """Retorna o primeiro arquivo da pasta que casa com algum padrão (regex)."""
    if not os.path.isdir(pasta):
        return None
    arquivos = sorted(os.listdir(pasta))
    for arq in arquivos:
        nome_low = arq.lower()
        for p in padroes:
            if re.search(p, nome_low, re.IGNORECASE):
                return os.path.join(pasta, arq)
    return None


def localizar_documentos(pasta: str) -> Dict[str, Optional[str]]:
    """Mapeia documentos esperados por padrões no nome do arquivo."""
    return {
        "inicial": _busca_arquivo(pasta, [
            r"^1[\.\s].*peti.*inicial.*\.docx$",
            r"^peti.*inicial.*\.docx$",
            r"inicial.*\.docx$",
        ]),
        "procuracao": _busca_arquivo(pasta, [
            r"^2[\.\s].*procura",
            r"procura.*bradesco",
            r"procura",
        ]),
        "rg": _busca_arquivo(pasta, [
            r"^3[\.\s].*rg",
            r"^_aux.*rg",
            r"rg.*\.pdf$",
            r"rg\.pdf$",
        ]),
        "hipossuficiencia": _busca_arquivo(pasta, [
            r"hipossufici",
        ]),
        "comprovante": _busca_arquivo(pasta, [
            r"^5[\.\s].*comprov.*resid",
            r"comprov.*resid",
            r"residencia",
        ]),
        "extrato": _busca_arquivo(pasta, [
            r"^6[\.\s].*extrato",
            r"extrato.*banc",
            r"extrato\.pdf$",
        ]),
        "tabela": _busca_arquivo(pasta, [
            r"^7[\.\s].*tabela.*\.(pdf|xlsx)$",
            r"tabela.*\.(pdf|xlsx)$",
        ]),
        "notificacao": _busca_arquivo(pasta, [
            r"^8[\.\s].*notifi",
            r"notifi.*extra",
            r"notifi",
        ]),
        "ar": _busca_arquivo(pasta, [
            r"^8\.1.*",
            r"comprov.*notifi",
            r"\bar\b.*notifi",
        ]),
    }


# ---------------------------------------------------------------- #
# Extração de dados da inicial
# ---------------------------------------------------------------- #
def _extrair_dados_inicial(peca: PecaDocx) -> Dict:
    """Extrai dados-chave do texto da inicial: nome, CPF, RG, conta/agência,
    comarca, subscritor+OAB, prioridade de idoso etc."""
    texto = "\n".join(peca.paragrafos)

    out: Dict = {}

    # Nome do cliente: primeiro nome em CAIXA-ALTA antes do CPF
    m = re.search(
        r"\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ\s]+),\s*brasileir[ao]",
        texto,
    )
    out["nome"] = m.group(1).strip() if m else None

    # CPF
    m = re.search(r"CPF\s+sob\s+o?\s*n[ºo°]\s*([\d\.\-]+)", texto, re.IGNORECASE)
    out["cpf"] = m.group(1).strip() if m else None

    # RG
    m = re.search(r"C[ée]dula\s+de\s+Identidade[^\d]*([\d\.X\-]+)", texto)
    out["rg"] = m.group(1).strip() if m else None

    # Conta + agência
    m = re.search(r"conta\s+corrente.*?n[ºo°]\s*([\d\-]+),?\s*ag[êe]ncia\s+n[ºo°]\s*([\d\-]+)", texto, re.IGNORECASE)
    if m:
        out["conta"] = m.group(1).strip()
        out["agencia"] = m.group(2).strip()
    else:
        out["conta"] = None
        out["agencia"] = None

    # Prioridade idoso
    out["alega_idoso"] = bool(
        re.search(r"art\.\s*1\.?048\s+do\s+CPC", texto, re.IGNORECASE) or
        re.search(r"prioridade.*idoso", texto, re.IGNORECASE)
    )

    # Gênero (heurística: presença de "autora" vs "autor")
    autora_count = len(re.findall(r"\bautora\b", texto, re.IGNORECASE))
    autor_count = len(re.findall(r"\bautor\b", texto, re.IGNORECASE)) - autora_count
    out["genero"] = "F" if autora_count > autor_count else "M"

    # Subscritor: tenta achar nome + OAB
    m = re.search(
        r"([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ]+){1,4})\s*\n*\s*"
        r"OAB[\s/\-]*([A-Z]{2})[\s/\-]*([A-Z]?\d{3,7}[A-Z]?)",
        texto,
    )
    if m:
        out["subscritor"] = m.group(1).strip()
        out["oab_uf"] = m.group(2).strip()
        out["oab_numero"] = m.group(3).strip()
    else:
        out["subscritor"] = None
        out["oab_uf"] = None
        out["oab_numero"] = None

    # Valor da causa
    m = re.search(r"valor.*?causa.*?R\$\s*([\d\.\,]+)", texto, re.IGNORECASE)
    if m:
        out["valor_causa"] = m.group(1)
    else:
        out["valor_causa"] = None

    return out


# ---------------------------------------------------------------- #
# Construção do contexto e edições
# ---------------------------------------------------------------- #
def _semaforo_status(divergencias: List[Dict]) -> str:
    if any((d.get("severidade") or "").upper() == "ALTA" for d in divergencias):
        return "INCONSISTENTE"
    if divergencias:
        return "ALERTA"
    return "OK"


def montar_contexto(
    pasta_cliente: str,
    nome_cliente_dir: str,
    peca: PecaDocx,
    docs_localizados: Dict[str, Optional[str]],
) -> Tuple[Dict, List[Dict]]:
    """Roda todos os scripts e monta o contexto completo + lista de edições."""

    paragrafos = peca.paragrafos
    texto_inicial = "\n".join(paragrafos)

    # 1) Tipo da ação
    nome_subpasta = os.path.basename(pasta_cliente)
    tipo_info = detectar_tipo(nome_subpasta, texto_inicial)

    # Carrega teses para puxar objeto da procuração e tipos de notificação
    teses = carregar_teses()
    objetos_procuracao = []
    tipos_notif_esperados = []
    rubricas_alvo = []
    for t in tipo_info["tipos_detectados"]:
        info_t = teses["tipos"].get(t, {})
        objetos_procuracao.extend(info_t.get("objeto_procuracao", []))
        if info_t.get("tipo_notificacao"):
            tipos_notif_esperados.append(info_t["tipo_notificacao"])
        rubricas_alvo.extend(info_t.get("rubrica_extrato", []))
    rubricas_alvo = list(dict.fromkeys(rubricas_alvo))

    # 2) Dados extraídos da inicial
    dados = _extrair_dados_inicial(peca)

    # 3) Cruzamentos
    cruz_extrato = cruzar_extrato(
        texto_inicial,
        docs_localizados.get("extrato") or "",
        rubricas_alvo,
    )
    cruz_tabela = cruzar_tabela(
        docs_localizados.get("tabela") or "",
        cruz_extrato.get("inicial", {}).get("total"),
        cruz_extrato.get("inicial", {}).get("qtd"),
    )

    # 4) Procuração
    proc = verificar_procuracao(
        docs_localizados.get("procuracao"),
        objetos_procuracao,
        ", ".join(tipo_info["tipos_detectados"]) or "?",
    )

    # 5) Notificação
    notif = verificar_notificacao(
        docs_localizados.get("notificacao"),
        docs_localizados.get("ar"),
        tipos_notif_esperados,
    )

    # 6) Idoso
    idoso = verificar_idoso(
        docs_localizados.get("rg"),
        dados.get("alega_idoso", False),
    )

    # 7) Comarca / domicílio
    comarca = verificar_comarca(texto_inicial, docs_localizados.get("comprovante"))

    # 8) Placeholders
    plhrs = detectar_placeholders(paragrafos)

    # 9) Modelo não adaptado
    n_reus = max(1, tipo_info.get("n_reus", 1))
    pna = analisar_modelo(
        paragrafos,
        genero_cliente=dados.get("genero"),
        n_reus=n_reus,
        tipo_acao="bancario",
        tipo_peca=None,
    )

    # 10) OAB
    oab_info = {}
    if dados.get("subscritor") and dados.get("oab_uf") and dados.get("oab_numero"):
        try:
            oab_info = verificar_oab(
                dados["subscritor"], dados["oab_numero"], dados["oab_uf"]
            )
            oab_info["oab_uf"] = dados["oab_uf"]
            oab_info["oab_numero"] = dados["oab_numero"]
        except Exception as e:
            oab_info = {"ok": False, "mensagem": f"Erro: {e}"}

    # ------------------- Construir tabela semáforo ------------------- #
    semaforo = []
    semaforo.append({
        "eixo": "1. Tipo de ação x Modelo",
        "status": tipo_info.get("consistencia", "OK"),
        "observacao": (
            f"Tipos detectados: {', '.join(tipo_info.get('tipos_detectados', [])) or '-'}; "
            f"IRDR no texto: {tipo_info.get('irdr_no_texto') or '-'}; "
            f"Esperado: {', '.join(tipo_info.get('irdr_esperado') or [])}"
        ),
    })

    semaforo.append({
        "eixo": "2. Identidade do cliente",
        "status": idoso.get("status", "OK"),
        "observacao": (
            f"Nome: {dados.get('nome') or '?'}; CPF: {dados.get('cpf') or '?'}; "
            f"Idade: {idoso.get('idade')}; Idoso alegado: {dados.get('alega_idoso')}"
        ),
    })

    semaforo.append({
        "eixo": "3. Comarca x Domicílio",
        "status": comarca.get("status", "OK"),
        "observacao": (
            f"Inicial: {comarca.get('comarca_inicial')}; "
            f"Comprovante: {comarca.get('cidade_comprovante') or 'ilegível'}; "
            f"Qualif.: {comarca.get('cidade_qualificacao')}"
        ),
    })

    # Banco-réu (eixo 4) - validação textual simples
    banco_status = "OK"
    banco_obs = "Bradesco com CNPJ correto"
    if "60.746.948" not in texto_inicial:
        banco_status = "ALERTA"
        banco_obs = "CNPJ do Bradesco (60.746.948) não localizado no texto da inicial"
    semaforo.append({
        "eixo": "4. Banco-réu",
        "status": banco_status,
        "observacao": banco_obs,
    })

    # Conta+agência (eixo 5)
    conta_status = "OK" if dados.get("conta") and dados.get("agencia") else "ALERTA"
    semaforo.append({
        "eixo": "5. Conta + agência",
        "status": conta_status,
        "observacao": f"Conta {dados.get('conta')} / agência {dados.get('agencia')}",
    })

    # Período + qtd + total (eixo 6)
    semaforo.append({
        "eixo": "6. Período + qtd + total",
        "status": cruz_extrato.get("status", "OK"),
        "observacao": (
            f"Inicial: {cruz_extrato.get('inicial', {}).get('data_inicio')} a "
            f"{cruz_extrato.get('inicial', {}).get('data_fim')}; "
            f"qtd={cruz_extrato.get('inicial', {}).get('qtd')}; "
            f"total=R$ {cruz_extrato.get('inicial', {}).get('total')}"
        ),
    })

    semaforo.append({
        "eixo": "7. Procuração específica",
        "status": proc.get("status", "OK"),
        "observacao": proc.get("observacao", ""),
    })

    semaforo.append({
        "eixo": "8. Notificação extrajudicial",
        "status": notif.get("status", "OK"),
        "observacao": (
            f"Notificação: {'OK' if notif.get('tem_notificacao') else 'AUSENTE'}; "
            f"AR: {'OK' if notif.get('tem_ar') else 'AUSENTE'}; "
            f"Tipo detectado: {notif.get('tipos_detectados')}"
        ),
    })

    oab_status = "OK" if oab_info.get("ok") else "ALERTA"
    semaforo.append({
        "eixo": "9. OAB / template",
        "status": oab_status,
        "observacao": oab_info.get("mensagem", "[não verificada]"),
    })

    adapt_alertas = list(plhrs) + [{
        "paragrafo": a["paragrafo"], "trecho": a["trecho"], "padrao": a.get("tipo"),
        "severidade": a.get("severidade"), "mensagem": a.get("mensagem"),
        "tipo": a.get("tipo"),
    } for a in pna]
    altas = sum(1 for a in adapt_alertas if (a.get("severidade") or "").upper() == "ALTA")
    if altas >= 3:
        adapt_status = "INCONSISTENTE"
    elif adapt_alertas:
        adapt_status = "ALERTA"
    else:
        adapt_status = "OK"
    semaforo.append({
        "eixo": "10. Adaptação do modelo",
        "status": adapt_status,
        "observacao": f"{len(adapt_alertas)} alertas ({altas} ALTAS).",
    })

    # ------------------- Alertas destacados ------------------- #
    alertas: List[str] = []
    for s in semaforo:
        if (s["status"] or "").upper() == "INCONSISTENTE":
            alertas.append(f"🔴 {s['eixo']}: {s['observacao']}")
    for d in cruz_extrato.get("divergencias", []):
        if d.get("severidade") == "ALTA":
            alertas.append(f"🔴 [Período/Total] {d.get('observacao', '')}")
    for d in (notif.get("divergencias") or []):
        if d.get("severidade") == "ALTA":
            alertas.append(f"🔴 [Notificação] {d.get('observacao', '')}")
    for d in (idoso.get("divergencias") or []):
        if d.get("severidade") == "ALTA":
            alertas.append(f"🔴 [Idoso] {d.get('observacao', '')}")
    for d in (comarca.get("divergencias") or []):
        if d.get("severidade") == "ALTA":
            alertas.append(f"🔴 [Comarca] {d.get('observacao', '')}")

    # ------------------- Cruzamentos para Seção 4 ------------------- #
    cruzamentos = []
    cruzamentos.append({
        "dado": "Conta corrente",
        "inicial": dados.get("conta"),
        "fonte": "Inicial / Extrato (cabeçalho)",
        "status": "OK" if dados.get("conta") else "ALERTA",
        "observacao": "",
    })
    cruzamentos.append({
        "dado": "Agência",
        "inicial": dados.get("agencia"),
        "fonte": "Inicial / Extrato (cabeçalho)",
        "status": "OK" if dados.get("agencia") else "ALERTA",
        "observacao": "",
    })
    if cruz_extrato.get("inicial"):
        cruzamentos.append({
            "dado": "Período",
            "inicial": f"{cruz_extrato['inicial'].get('data_inicio')} a {cruz_extrato['inicial'].get('data_fim')}",
            "fonte": "Extrato (lançamentos)",
            "status": cruz_extrato.get("status"),
            "observacao": "; ".join(d.get("observacao", "") for d in cruz_extrato.get("divergencias", []))[:200],
        })
        cruzamentos.append({
            "dado": "Qtd descontos",
            "inicial": cruz_extrato["inicial"].get("qtd"),
            "fonte": f"Extrato={cruz_extrato.get('extrato', {}).get('qtd_rubrica')}; Tabela={cruz_tabela.get('qtd_tabela')}",
            "status": cruz_extrato.get("status"),
            "observacao": "",
        })
        cruzamentos.append({
            "dado": "Total descontado",
            "inicial": cruz_extrato["inicial"].get("total"),
            "fonte": f"Extrato=R$ {cruz_extrato.get('extrato', {}).get('total_rubrica')}; Tabela=R$ {cruz_tabela.get('total_tabela')}",
            "status": cruz_extrato.get("status"),
            "observacao": "",
        })
    cruzamentos.append({
        "dado": "Comarca",
        "inicial": comarca.get("comarca_inicial"),
        "fonte": f"Comprovante: {comarca.get('cidade_comprovante') or 'ilegível'}",
        "status": comarca.get("status"),
        "observacao": "",
    })

    # ------------------- Documentos ------------------- #
    docs_lista = []
    for k, v in docs_localizados.items():
        if v:
            docs_lista.append({"nome": k, "caminho": v, "observacao": ""})
    ausencias = [k for k, v in docs_localizados.items() if not v]

    # ------------------- Edições sugeridas ------------------- #
    edicoes = construir_edicoes(peca, paragrafos, dados, tipo_info,
                                cruz_extrato, idoso, comarca, plhrs, pna, oab_info)

    criticas = sum(1 for e in edicoes if e.get("gravidade") == "🔴")
    medias = sum(1 for e in edicoes if e.get("gravidade") == "⚠️")
    baixas = sum(1 for e in edicoes if e.get("gravidade") == "🟡")

    if any((s.get("status") or "").upper() == "INCONSISTENTE" for s in semaforo):
        resultado = "🔴 NÃO PROTOCOLAR - REQUER AJUSTES"
    elif any((s.get("status") or "").upper() == "ALERTA" for s in semaforo):
        resultado = "⚠️ PROTOCOLAR COM RESSALVAS"
    else:
        resultado = "✅ APTA AO PROTOCOLO"

    sintese = {
        "resultado": resultado,
        "total_edicoes": len(edicoes),
        "criticas": criticas,
        "medias": medias,
        "baixas": baixas,
        "resumo": f"{len(adapt_alertas)} alertas de adaptação detectados ({altas} ALTAS).",
    }

    # Cabeçalho
    cabecalho = {
        "cliente": dados.get("nome") or nome_cliente_dir,
        "cpf": dados.get("cpf") or "",
        "tipo_acao_pretty": "; ".join(tipo_info.get("tese_pretty") or []) or "-",
        "comarca": comarca.get("comarca_inicial") or "-",
        "subscritor": dados.get("subscritor") or "-",
        "oab_uf": dados.get("oab_uf") or "-",
        "oab_numero": dados.get("oab_numero") or "-",
        "pasta": pasta_cliente,
        "data_conferencia": date.today().strftime("%d/%m/%Y"),
    }

    contexto = {
        "cabecalho": cabecalho,
        "semaforo": semaforo,
        "alertas": alertas,
        "tipo_acao": tipo_info,
        "cruzamentos": cruzamentos,
        "notificacao": notif,
        "oab": oab_info,
        "adaptacao": adapt_alertas,
        "docs": docs_lista,
        "ausencias": ausencias,
        "sintese": sintese,
    }

    return contexto, edicoes


def construir_edicoes(
    peca: PecaDocx, paragrafos: List[str], dados: Dict, tipo_info: Dict,
    cruz_extrato: Dict, idoso: Dict, comarca: Dict, plhrs: List[Dict],
    pna: List[Dict], oab_info: Dict,
) -> List[Dict]:
    """Constrói lista de edições sugeridas (com âncora literal)."""
    edicoes: List[Dict] = []

    def gravidade_emoji(sev: str) -> str:
        s = (sev or "").upper()
        return {"ALTA": "🔴", "MEDIA": "⚠️"}.get(s, "🟡")

    def safe_paragrafo(num: int) -> Optional[str]:
        try:
            return paragrafos[num - 1]
        except IndexError:
            return None

    def safe_paragrafo_anterior(num: int) -> Optional[str]:
        # Procura o último parágrafo NÃO-VAZIO antes de num
        for i in range(num - 2, -1, -1):
            if paragrafos[i].strip():
                return paragrafos[i]
        return None

    # 1) Período invertido (cruz_extrato com severidade ALTA "periodo_invertido")
    for d in cruz_extrato.get("divergencias", []):
        if d.get("campo") == "periodo_invertido":
            inicio = cruz_extrato.get("inicial", {}).get("data_inicio")
            fim = cruz_extrato.get("inicial", {}).get("data_fim")
            if inicio and fim:
                trecho_orig = f"{inicio} a {fim}"
                texto_sub = f"{fim} a {inicio}"
                # Tenta achar parágrafo que contém essas datas
                for i, par in enumerate(paragrafos, start=1):
                    if inicio in par and fim in par:
                        ancora = safe_paragrafo_anterior(i)
                        edicoes.append({
                            "tipo_acao": "SUBSTITUIR",
                            "gravidade": "🔴",
                            "eixo": "6. Período + qtd + total",
                            "ancoragem": ancora or "[início da síntese fática]",
                            "trecho_original": trecho_orig,
                            "texto_substituto": texto_sub,
                            "justificativa": (
                                f"As datas declaradas estão em ordem inversa: "
                                f"{inicio} é POSTERIOR a {fim}. Inverter para "
                                f"manter cronologia coerente com o extrato."
                            ),
                        })
                        break

    # 2) Idoso alegado sem idade
    for d in idoso.get("divergencias", []):
        if d.get("campo") == "alega_idoso_sem_idade":
            for i, par in enumerate(paragrafos, start=1):
                if "1.048" in par or "1048" in par:
                    ancora = safe_paragrafo_anterior(i)
                    edicoes.append({
                        "tipo_acao": "REMOVER",
                        "gravidade": "🔴",
                        "eixo": "2. Identidade do cliente",
                        "ancoragem": ancora or "[início da inicial]",
                        "trecho_original": par,
                        "texto_substituto": "",
                        "justificativa": (
                            f"Cliente tem {idoso.get('idade')} anos (nasc. "
                            f"{idoso.get('data_nascimento')}). Não preenche o requisito "
                            f"de idoso (≥ 60 anos) do art. 1.048 CPC."
                        ),
                    })
                    break

    # 3) Idoso não invocado mas elegível
    for d in idoso.get("divergencias", []):
        if d.get("campo") == "idoso_nao_invocado":
            # Procura parágrafo do endereçamento (que contém "Comarca")
            for i, par in enumerate(paragrafos, start=1):
                if re.search(r"Ju[íi]zo.*Juizado.*Comarca", par, re.IGNORECASE):
                    edicoes.append({
                        "tipo_acao": "INSERIR DEPOIS",
                        "gravidade": "🟡",
                        "eixo": "2. Identidade do cliente",
                        "ancoragem": par,
                        "trecho_original": "",
                        "texto_substituto": "Prioridade de tramitação: art. 1.048 do Código de Processo Civil (Idoso).",
                        "justificativa": (
                            f"Cliente é idoso ({idoso.get('idade')} anos). "
                            f"Considerar invocar a prioridade do art. 1.048 CPC."
                        ),
                    })
                    break

    # 4) Comarca x comprovante divergente
    for d in comarca.get("divergencias", []):
        if d.get("campo") == "comarca_x_comprovante" and d.get("severidade") == "ALTA":
            edicoes.append({
                "tipo_acao": "REESCREVER",
                "gravidade": "🔴",
                "eixo": "3. Comarca x Domicílio",
                "ancoragem": "[início da peça - endereçamento]",
                "trecho_original": (
                    f"Ao Juízo do Juizado Especial Cível da Comarca de {d.get('comarca_inicial')}/AM"
                ),
                "texto_substituto": (
                    f"Ao Juízo do Juizado Especial Cível da Comarca de {d.get('cidade_comprovante')}/AM"
                ),
                "justificativa": (
                    f"Comprovante de residência indica {d.get('cidade_comprovante')}; "
                    f"endereçar para a comarca correta."
                ),
            })

    # 5) Placeholders Jinja / vírgulas vazias / Cidade
    for ph in plhrs:
        sev = ph.get("severidade", "MEDIA")
        if sev == "ALTA":
            par = safe_paragrafo(ph["paragrafo"])
            ancora = safe_paragrafo_anterior(ph["paragrafo"])
            edicoes.append({
                "tipo_acao": "REESCREVER",
                "gravidade": "🔴",
                "eixo": "10. Adaptação do modelo",
                "ancoragem": ancora or "[parágrafo anterior]",
                "trecho_original": par[:500] if par else ph.get("trecho", ""),
                "texto_substituto": "[PREENCHER MANUALMENTE - placeholder identificado]",
                "justificativa": ph.get("mensagem", ""),
            })

    return edicoes


# ---------------------------------------------------------------- #
# Ponto de entrada
# ---------------------------------------------------------------- #
def rodar(pasta_cliente: str, pasta_saida: Optional[str] = None,
          nome_cliente: Optional[str] = None) -> Dict[str, str]:
    """Executa toda a análise e gera os DOCX. Retorna dict com caminhos."""
    pasta_cliente = os.path.abspath(pasta_cliente)
    if not os.path.isdir(pasta_cliente):
        raise FileNotFoundError(f"Pasta não encontrada: {pasta_cliente}")

    pasta_saida = pasta_saida or pasta_cliente
    nome_cliente = nome_cliente or os.path.basename(pasta_cliente.rstrip(os.sep))

    docs = localizar_documentos(pasta_cliente)
    if not docs.get("inicial"):
        raise FileNotFoundError(f"Petição inicial não encontrada em {pasta_cliente}")

    peca = PecaDocx(docs["inicial"])
    contexto, edicoes = montar_contexto(pasta_cliente, nome_cliente, peca, docs)
    return gerar_relatorio_e_edicoes(pasta_saida, nome_cliente, contexto, edicoes)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python orquestrar.py <pasta-cliente> [pasta-saida] [nome-cliente]")
        sys.exit(1)
    pasta = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else None
    nome = sys.argv[3] if len(sys.argv) > 3 else None
    out = rodar(pasta, saida, nome)
    print(json.dumps(out, indent=2, ensure_ascii=False))
