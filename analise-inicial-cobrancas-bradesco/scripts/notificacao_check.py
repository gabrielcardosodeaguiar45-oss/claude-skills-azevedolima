# -*- coding: utf-8 -*-
"""
Verificação da notificação extrajudicial juntada à inicial.

Confere:
- presença do PDF da notificação;
- presença do AR (comprovante de envio);
- correspondência entre o tipo da notificação (Encargos / Tarifas / Título / PG Eletrônico / Não contratado)
  e o tipo da ação;
- destinatário Bradesco;
- data de envio em janela razoável (≥ 15 dias antes da inicial).
"""
from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional


def _norm(s: str) -> str:
    if not s:
        return ""
    n = unicodedata.normalize("NFKD", s)
    n = "".join(c for c in n if not unicodedata.combining(c))
    return n.upper().strip()


def _ler_pdf(caminho: str) -> str:
    if not caminho or not os.path.exists(caminho):
        return ""
    try:
        import pdfplumber
        texto = ""
        with pdfplumber.open(caminho) as pdf:
            for pg in pdf.pages:
                t = pg.extract_text() or ""
                texto += t + "\n"
        if texto.strip():
            return texto
    except Exception:
        pass
    try:
        import fitz
        doc = fitz.open(caminho)
        texto = ""
        for pg in doc:
            texto += pg.get_text() + "\n"
        doc.close()
        return texto
    except Exception:
        return ""


def _parse_data_pt(s: str) -> Optional[datetime]:
    s = (s or "").strip()
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if not m:
        return None
    try:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


PALAVRAS_TIPO = {
    "AM - Encargos": ["ENCARGO", "MORA CRED", "LIM. CREDITO", "LIM CREDITO"],
    "AM - Tarifas": ["TARIFA"],
    "AM - Título de Capitalização": ["TITULO DE CAPITALIZACAO", "TÍTULO DE CAPITALIZAÇÃO"],
    "AM - Pagamento Eletrônico": ["PAGAMENTO ELETRONICO", "PG ELETRON"],
    "AM - Não contratado": ["NAO CONTRATADO", "NÃO CONTRATADO", "EMPRESTIMO NAO CONTRATADO"],
}


def _detectar_tipo_notificacao(nome_arquivo: str, texto: str) -> List[str]:
    """Identifica que tipo(s) de notificação o arquivo representa."""
    fonte = _norm(nome_arquivo + " " + texto)
    detectados = []
    for tipo, palavras in PALAVRAS_TIPO.items():
        for p in palavras:
            if p in fonte:
                detectados.append(tipo)
                break
    return detectados


def verificar_notificacao(
    caminho_notificacao: Optional[str],
    caminho_ar: Optional[str],
    tipos_notificacao_esperados: List[str],
    data_inicial: Optional[datetime] = None,
) -> Dict:
    """Verifica a notificação extrajudicial.

    Args:
        caminho_notificacao: PDF da notificação (ou None).
        caminho_ar: PDF do comprovante de envio (ou None).
        tipos_notificacao_esperados: lista de tipos esperados (de teses.json).
        data_inicial: data presumida da inicial (datetime, ou None para usar hoje).
    """
    out: Dict = {
        "tem_notificacao": bool(caminho_notificacao and os.path.exists(caminho_notificacao)),
        "tem_ar": bool(caminho_ar and os.path.exists(caminho_ar)),
        "tipos_esperados": tipos_notificacao_esperados,
        "tipos_detectados": [],
        "destinatario_bradesco": False,
        "data_envio": None,
        "divergencias": [],
        "status": "OK",
    }

    if not out["tem_notificacao"]:
        out["divergencias"].append({
            "campo": "notificacao_ausente",
            "observacao": "Notificação Extrajudicial não encontrada na pasta. Sem ela, a preliminar de prévio requerimento administrativo fica enfraquecida (REsp 2.209.304/MG).",
            "severidade": "MEDIA",
        })
        out["status"] = "ALERTA"

    if not out["tem_ar"]:
        out["divergencias"].append({
            "campo": "ar_ausente",
            "observacao": "Comprovante de envio (AR ou similar) não encontrado. Sem ele não há prova de que o banco foi notificado.",
            "severidade": "MEDIA",
        })
        out["status"] = "ALERTA"

    if out["tem_notificacao"]:
        nome = os.path.basename(caminho_notificacao)
        texto = _ler_pdf(caminho_notificacao)

        # Detecta tipo da notificação
        detectados = _detectar_tipo_notificacao(nome, texto)
        out["tipos_detectados"] = detectados

        # Bradesco
        if "BRADESCO" in _norm(nome + " " + texto):
            out["destinatario_bradesco"] = True
        else:
            out["divergencias"].append({
                "campo": "destinatario_nao_identificado",
                "observacao": "Notificação não menciona explicitamente o BRADESCO no nome ou no texto. Confirmar.",
                "severidade": "BAIXA",
            })

        # Tipo bate com a ação?
        if tipos_notificacao_esperados:
            esperados_norm = [_norm(t) for t in tipos_notificacao_esperados]
            detec_norm = [_norm(t) for t in detectados]
            interseccao = set(esperados_norm) & set(detec_norm)
            if not interseccao:
                out["divergencias"].append({
                    "campo": "tipo_notificacao_divergente",
                    "esperado": tipos_notificacao_esperados,
                    "detectado": detectados or "[indeterminado]",
                    "observacao": (
                        f"Tipo da notificação juntada {detectados or '[indeterminado]'} "
                        f"não corresponde ao tipo esperado para a ação {tipos_notificacao_esperados}. "
                        f"Sem notificação do tipo correto, a preliminar pode ser rebatida."
                    ),
                    "severidade": "ALTA",
                })

        # Data de envio: tenta encontrar primeira data no PDF da notificação
        m = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", texto)
        if m:
            d = _parse_data_pt(m.group(1))
            if d:
                out["data_envio"] = d.strftime("%d/%m/%Y")
                if data_inicial:
                    delta = (data_inicial - d).days
                    if delta < 15 and delta >= 0:
                        out["divergencias"].append({
                            "campo": "data_envio_recente",
                            "observacao": (
                                f"Notificação enviada em {out['data_envio']}, apenas {delta} dia(s) "
                                f"antes da inicial. Recomendado ≥ 15 dias para preservar tese de "
                                f"pretensão resistida."
                            ),
                            "severidade": "BAIXA",
                        })
                    elif delta < 0:
                        out["divergencias"].append({
                            "campo": "data_envio_posterior",
                            "observacao": (
                                f"Data da notificação ({out['data_envio']}) é POSTERIOR à inicial "
                                f"- inviabiliza preliminar."
                            ),
                            "severidade": "ALTA",
                        })

    if any(d["severidade"] == "ALTA" for d in out["divergencias"]):
        out["status"] = "INCONSISTENTE"
    elif out["divergencias"]:
        out["status"] = "ALERTA"

    return out


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 3:
        print("Uso: python notificacao_check.py <notif.pdf> <ar.pdf> [tipo1,tipo2,...]")
        sys.exit(1)
    tipos = sys.argv[3].split(",") if len(sys.argv) > 3 else ["AM - Encargos"]
    print(json.dumps(verificar_notificacao(sys.argv[1], sys.argv[2], tipos), indent=2, ensure_ascii=False))
