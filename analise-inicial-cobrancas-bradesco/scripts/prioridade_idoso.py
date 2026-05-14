# -*- coding: utf-8 -*-
"""
Verificação da prioridade de tramitação por idoso (art. 1.048 CPC).

A inicial pode trazer "Prioridade de tramitação: art. 1.048 do CPC (Idoso)".
Confirmar pelo RG do cliente: idade ≥ 60 anos na data da propositura.

Lê o PDF do RG, extrai a data de nascimento (padrão DD/MM/AAAA), calcula a
idade na data atual ou na data da inicial.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, date
from typing import Dict, List, Optional


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


def _parse_data(s: str) -> Optional[date]:
    s = (s or "").strip()
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def _extrair_data_nascimento_rg(texto: str) -> Optional[date]:
    """Tenta achar data de nascimento no texto do RG.

    RGs digitalizados às vezes têm:
        "Data de Nascimento: DD/MM/AAAA"
        "DATA NASCIMENTO DD/MM/AAAA"
        Linha solta com data.
    """
    if not texto:
        return None

    # Padrões em ordem de preferência
    padroes = [
        r"DATA\s+DE\s+NASCIMENTO[:\s]+(\d{1,2}/\d{1,2}/\d{4})",
        r"NASCIMENTO[:\s]+(\d{1,2}/\d{1,2}/\d{4})",
        r"NASC\.?\s*[:\s]+(\d{1,2}/\d{1,2}/\d{4})",
        r"NASCIDO\s+EM\s+(\d{1,2}/\d{1,2}/\d{4})",
        r"NASCIDA\s+EM\s+(\d{1,2}/\d{1,2}/\d{4})",
    ]
    for p in padroes:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            d = _parse_data(m.group(1))
            if d:
                return d

    # Fallback: pega a primeira data plausível (entre 1900 e 30 anos atrás)
    todas = re.findall(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", texto)
    hoje = date.today()
    candidatas: List[date] = []
    for s in todas:
        d = _parse_data(s)
        if d and 1900 <= d.year <= (hoje.year - 18):
            candidatas.append(d)
    if candidatas:
        # Pega a mais antiga (provavelmente nascimento)
        return min(candidatas)

    return None


def _idade(nasc: date, ref: date) -> int:
    anos = ref.year - nasc.year
    if (ref.month, ref.day) < (nasc.month, nasc.day):
        anos -= 1
    return anos


def verificar_idoso(
    caminho_rg: Optional[str],
    inicial_alega_idoso: bool,
    data_referencia: Optional[date] = None,
) -> Dict:
    """Verifica se a alegação de idoso bate com a data de nascimento do RG.

    Args:
        caminho_rg: caminho do PDF do RG (ou None).
        inicial_alega_idoso: True se a inicial cita "art. 1.048 CPC (Idoso)".
        data_referencia: data para cálculo de idade (default: hoje).
    """
    if data_referencia is None:
        data_referencia = date.today()

    out: Dict = {
        "tem_rg": bool(caminho_rg and os.path.exists(caminho_rg)),
        "data_nascimento": None,
        "idade": None,
        "inicial_alega_idoso": inicial_alega_idoso,
        "divergencias": [],
        "status": "OK",
    }

    if not out["tem_rg"]:
        out["divergencias"].append({
            "campo": "rg_ausente",
            "observacao": "RG não encontrado para validar idade.",
            "severidade": "MEDIA",
        })
        out["status"] = "ALERTA"
        return out

    texto = _ler_pdf(caminho_rg)
    nasc = _extrair_data_nascimento_rg(texto)

    if not nasc:
        out["divergencias"].append({
            "campo": "rg_sem_data",
            "observacao": "Não foi possível extrair data de nascimento do RG (provavelmente escaneado). Validar manualmente.",
            "severidade": "BAIXA",
        })
        out["status"] = "ALERTA"
        return out

    idade = _idade(nasc, data_referencia)
    out["data_nascimento"] = nasc.strftime("%d/%m/%Y")
    out["idade"] = idade

    if inicial_alega_idoso and idade < 60:
        out["divergencias"].append({
            "campo": "alega_idoso_sem_idade",
            "observacao": (
                f"Inicial alega prioridade de idoso (art. 1.048 CPC), mas o cliente "
                f"tem {idade} anos (nasc. {out['data_nascimento']}). REMOVER a "
                f"prioridade de idoso da inicial para evitar litigância de má-fé."
            ),
            "severidade": "ALTA",
        })
        out["status"] = "INCONSISTENTE"
    elif (not inicial_alega_idoso) and idade >= 60:
        out["divergencias"].append({
            "campo": "idoso_nao_invocado",
            "observacao": (
                f"Cliente é idoso ({idade} anos, nasc. {out['data_nascimento']}) mas a "
                f"inicial não invoca a prioridade de tramitação do art. 1.048 do CPC. "
                f"Considerar adicionar a prioridade no preâmbulo da peça."
            ),
            "severidade": "BAIXA",
        })
        out["status"] = "ALERTA"

    return out


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Uso: python prioridade_idoso.py <rg.pdf> [alega_idoso=0|1]")
        sys.exit(1)
    alega = bool(int(sys.argv[2])) if len(sys.argv) > 2 else False
    print(json.dumps(verificar_idoso(sys.argv[1], alega), indent=2, ensure_ascii=False))
