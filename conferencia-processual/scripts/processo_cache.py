# -*- coding: utf-8 -*-
"""
Cache do processo fatiado — reaproveita o output da skill `fatiar-processo`.

Se o PDF do processo já foi fatiado por evento, esta skill lê só os
eventos relevantes (INIC, CONTES, SENT, RecIno, réplicas) em vez de
abrir o PDF inteiro. Economiza tempo e contexto.

Uso:

    from processo_cache import localizar_fatias, eventos_por_tipo

    fatias = localizar_fatias(pasta_processo)
    # -> [{'evento': 72, 'tipo': 'CONTES1', 'path': '...Evento 072 - CONTES1 - ...pdf'}, ...]

    iniciais = eventos_por_tipo(fatias, ['INIC'])
    contestacoes = eventos_por_tipo(fatias, ['CONTES'])
    sentencas = eventos_por_tipo(fatias, ['SENT'])
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional


# Padrão nome gerado pela skill fatiar-processo:
# "Evento NNN - TIPODOC - descricao.pdf"
RE_FATIA = re.compile(
    r"Evento\s*(?P<n>\d+)\s*-\s*(?P<tipo>[A-Z][A-Za-z0-9]+)\s*-?\s*(?P<desc>.*)\.pdf",
    re.IGNORECASE,
)

# Tipos relevantes para conferência processual
TIPOS_RELEVANTES = {
    "INIC": "Petição inicial",
    "CONTES": "Contestação",
    "REPLI": "Réplica",
    "IMPUG": "Impugnação",
    "SENT": "Sentença",
    "DESPAD": "Despacho",
    "DECIS": "Decisão interlocutória",
    "RecIno": "Recurso inominado",
    "CR": "Contrarrazões",
    "APEL": "Apelação",
    "AGR": "Agravo",
}


def localizar_fatias(pasta: str) -> List[Dict]:
    """Lista os PDFs fatiados dentro de uma pasta de processo."""
    p = Path(pasta)
    if not p.is_dir():
        return []
    fatias = []
    for pdf in p.rglob("Evento*.pdf"):
        m = RE_FATIA.search(pdf.name)
        if not m:
            continue
        fatias.append({
            "evento": int(m.group("n")),
            "tipo": m.group("tipo").upper(),
            "desc": m.group("desc").strip(),
            "path": str(pdf),
            "nome": pdf.name,
        })
    fatias.sort(key=lambda f: f["evento"])
    return fatias


def eventos_por_tipo(fatias: List[Dict], prefixos: Iterable[str]) -> List[Dict]:
    """Filtra fatias por prefixo de tipo (ex.: 'INIC', 'CONTES', 'SENT')."""
    prefixos_up = tuple(p.upper() for p in prefixos)
    return [f for f in fatias if f["tipo"].startswith(prefixos_up)]


def relatorio_cache(pasta: str) -> str:
    fatias = localizar_fatias(pasta)
    if not fatias:
        return (
            f"[Cache vazio] Nenhum arquivo 'Evento NNN - TIPO - desc.pdf' "
            f"encontrado em {pasta!r}. Rode a skill `fatiar-processo` primeiro "
            f"ou trabalhe com o PDF consolidado."
        )
    linhas = [f"Fatias encontradas em '{pasta}': {len(fatias)}"]
    for tipo_prefix, rotulo in TIPOS_RELEVANTES.items():
        ev = eventos_por_tipo(fatias, [tipo_prefix])
        if ev:
            linhas.append(f"  {rotulo}: {len(ev)} — eventos {[e['evento'] for e in ev[:5]]}")
    return "\n".join(linhas)


def encontrar_pasta_fatiada(caminho_inicial: str) -> Optional[str]:
    """Heurística: dado o caminho do PDF original ou da pasta do processo,
    tenta localizar a pasta com as fatias já geradas."""
    p = Path(caminho_inicial)
    if p.is_file():
        p = p.parent
    # Procura em subpastas com 'Eventos' no nome, ou a própria pasta
    candidatas = [p]
    for sub in p.iterdir() if p.is_dir() else []:
        if sub.is_dir() and ("evento" in sub.name.lower() or
                             "fatiado" in sub.name.lower() or
                             "fatia" in sub.name.lower()):
            candidatas.append(sub)
    for c in candidatas:
        if localizar_fatias(str(c)):
            return str(c)
    return None


if __name__ == "__main__":
    import sys
    pasta = sys.argv[1] if len(sys.argv) > 1 else "."
    print(relatorio_cache(pasta))
