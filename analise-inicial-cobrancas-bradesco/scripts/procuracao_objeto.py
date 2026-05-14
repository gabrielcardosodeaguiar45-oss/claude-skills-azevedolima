# -*- coding: utf-8 -*-
"""
Verificação do objeto da procuração contra o tipo de ação.

Heurística: cruza o nome do arquivo + texto do PDF da procuração com a lista
de termos esperados para o tipo da ação (de teses.json).

Saída:
{
  'caminho': '...pdf',
  'nome_arquivo': '...',
  'objeto_no_nome': bool,
  'objeto_no_texto': bool,
  'objeto_esperado': [...],
  'objeto_encontrado': '...',
  'status': 'OK' | 'ALERTA' | 'INCONSISTENTE',
  'observacao': '...'
}
"""
from __future__ import annotations

import os
import re
import unicodedata
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


def verificar_procuracao(
    caminho_procuracao: Optional[str],
    objetos_esperados: List[str],
    tipo_acao: str,
) -> Dict:
    """Verifica se a procuração está aderente ao tipo da ação.

    Args:
        caminho_procuracao: caminho do PDF (pode ser None).
        objetos_esperados: lista de termos esperados no nome ou no texto
            (ex.: ['mora credito pessoal', 'mora cred pess']).
        tipo_acao: rótulo legível (ex.: 'MORA_CRED_PESS').
    """
    if not caminho_procuracao or not os.path.exists(caminho_procuracao):
        return {
            "caminho": caminho_procuracao,
            "tipo_acao": tipo_acao,
            "objetos_esperados": objetos_esperados,
            "status": "INCONSISTENTE",
            "observacao": "Procuração não encontrada na pasta.",
            "severidade": "ALTA",
        }

    nome = os.path.basename(caminho_procuracao)
    nome_norm = _norm(nome)

    objetos_norm = [_norm(o) for o in objetos_esperados]

    # Verifica no nome
    objeto_no_nome = None
    for o in objetos_norm:
        if o and o in nome_norm:
            objeto_no_nome = o
            break

    # Verifica no texto do PDF
    texto = _ler_pdf(caminho_procuracao)
    texto_norm = _norm(texto)
    objeto_no_texto = None
    for o in objetos_norm:
        if o and o in texto_norm:
            objeto_no_texto = o
            break

    # Detecta se procuração menciona Bradesco
    menciona_bradesco = "BRADESCO" in nome_norm or "BRADESCO" in texto_norm

    if objeto_no_nome and objeto_no_texto:
        status = "OK"
        obs = (
            f"Procuração com objeto compatível ('{objeto_no_texto}') no nome do arquivo "
            f"e no texto. Bradesco {'presente' if menciona_bradesco else 'AUSENTE'}."
        )
        sev = None
    elif objeto_no_nome and not objeto_no_texto:
        if texto.strip():
            status = "ALERTA"
            obs = (
                f"Nome do arquivo indica '{objeto_no_nome}' mas no texto do PDF não foi "
                f"encontrado nenhum dos termos esperados ({objetos_esperados}). "
                f"Pode ser variação textual ou procuração genérica."
            )
            sev = "MEDIA"
        else:
            status = "ALERTA"
            obs = (
                f"Nome do arquivo indica '{objeto_no_nome}'. Texto do PDF ilegível "
                f"(provavelmente escaneado) - confirmar manualmente o objeto."
            )
            sev = "BAIXA"
    elif objeto_no_texto and not objeto_no_nome:
        status = "OK"
        obs = (
            f"Texto da procuração contém objeto compatível ('{objeto_no_texto}'), "
            f"embora o nome do arquivo não o reflita."
        )
        sev = "BAIXA"
    else:
        # Nem no nome, nem no texto
        if texto.strip():
            status = "INCONSISTENTE"
            obs = (
                f"Procuração não menciona nenhum dos objetos esperados "
                f"({objetos_esperados}). Verificar se é a procuração correta."
            )
            sev = "ALTA"
        else:
            status = "ALERTA"
            obs = (
                f"Texto do PDF da procuração ilegível e nome do arquivo não indica "
                f"o objeto. Validar manualmente."
            )
            sev = "MEDIA"

    return {
        "caminho": caminho_procuracao,
        "nome_arquivo": nome,
        "tipo_acao": tipo_acao,
        "objetos_esperados": objetos_esperados,
        "objeto_no_nome": objeto_no_nome,
        "objeto_no_texto": objeto_no_texto,
        "menciona_bradesco": menciona_bradesco,
        "status": status,
        "observacao": obs,
        "severidade": sev,
    }


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 3:
        print("Uso: python procuracao_objeto.py <procuracao.pdf> <obj1,obj2,...> [tipo]")
        sys.exit(1)
    objs = sys.argv[2].split(",")
    tipo = sys.argv[3] if len(sys.argv) > 3 else "?"
    print(json.dumps(verificar_procuracao(sys.argv[1], objs, tipo), indent=2, ensure_ascii=False))
