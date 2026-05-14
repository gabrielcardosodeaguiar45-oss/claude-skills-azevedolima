# -*- coding: utf-8 -*-
"""
Consulta ao banco interno de jurisprudência do escritório no vault Obsidian.

Busca precedentes em `Precedentes/` e verifica se um acórdão citado na peça
já existe na base (evita marcar como "NÃO VERIFICÁVEL" julgados que o
escritório já catalogou).

IMPORTANTE: o usuário precisa alimentar a pasta `Precedentes/` do vault
com as fichas dos julgados que costuma citar. Enquanto não fizer isso,
esta skill apenas registra "base vazia" e não deixa o fluxo travar.

Uso:

    from jurisprudencia_vault import consultar_julgado

    r = consultar_julgado("0002485-74.2025.8.04.5800")
    # -> {'encontrado': True, 'ficha': 'Precedentes/xxx.md', 'resumo': '...'}
    # ou {'encontrado': False, 'sugestao': 'adicionar ao vault'}
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional


VAULT_DEFAULT = os.path.expanduser(
    r"~/OneDrive/Documentos/Obsidian Vault"
)
PASTA_PRECEDENTES = "Precedentes"


def _normalizar_num(processo: str) -> str:
    """Normaliza número CNJ para comparação: extrai só os dígitos relevantes."""
    return re.sub(r"[^\d.\-]", "", processo).strip()


def listar_fichas(vault_path: Optional[str] = None) -> List[Path]:
    vp = Path(vault_path or VAULT_DEFAULT)
    pasta = vp / PASTA_PRECEDENTES
    if not pasta.is_dir():
        return []
    return [p for p in pasta.rglob("*.md") if p.name != "_index.md"]


def consultar_julgado(
    identificador: str,
    vault_path: Optional[str] = None,
) -> Dict:
    """Procura um julgado na base interna.

    O identificador pode ser número CNJ, número de REsp, "Tema X STJ", etc.
    Varre fichas markdown em busca de correspondência por texto contido.
    """
    identificador_norm = _normalizar_num(identificador) or identificador.strip()
    fichas = listar_fichas(vault_path)

    if not fichas:
        return {
            "encontrado": False,
            "base_vazia": True,
            "mensagem": (
                f"Base de precedentes vazia em '{vault_path or VAULT_DEFAULT}/"
                f"{PASTA_PRECEDENTES}/'. Alimentar o vault com fichas dos "
                "julgados habituais para que a skill possa confirmá-los em "
                "conferências futuras."
            ),
        }

    achados = []
    for ficha in fichas:
        try:
            texto = ficha.read_text(encoding="utf-8")
        except Exception:
            continue
        if identificador in texto or identificador_norm in texto:
            # Primeira linha não-vazia do ficheiro como resumo
            primeiro_h = ""
            for linha in texto.splitlines():
                if linha.strip().startswith("#"):
                    primeiro_h = linha.strip().lstrip("#").strip()
                    break
            achados.append({
                "arquivo": str(ficha),
                "titulo": primeiro_h or ficha.stem,
                "tamanho": len(texto),
            })

    if not achados:
        return {
            "encontrado": False,
            "base_vazia": False,
            "mensagem": (
                f"Julgado {identificador!r} não localizado em "
                f"'{vault_path or VAULT_DEFAULT}/{PASTA_PRECEDENTES}/'. "
                "Se o precedente for confiável e for usado com frequência, "
                "criar ficha no vault para reuso em futuras conferências."
            ),
        }

    return {
        "encontrado": True,
        "base_vazia": False,
        "fichas": achados,
        "mensagem": f"{len(achados)} ficha(s) encontrada(s) no vault.",
    }


def sugerir_adicionar(processo: str, ementa_resumo: str = "") -> str:
    """Gera skeleton markdown para nova ficha de precedente."""
    slug = re.sub(r"[^\w\-]", "-", processo).strip("-")[:60]
    return (
        f"---\n"
        f"tipo: precedente\n"
        f"tags: [precedente]\n"
        f"processo: {processo}\n"
        f"---\n\n"
        f"# {processo}\n\n"
        f"## Ementa\n\n{ementa_resumo or '[colar ementa]'}\n\n"
        f"## Tese fixada\n\n[descrever]\n\n"
        f"## Aplicabilidade no escritório\n\n[quando citar]\n"
    ), f"{PASTA_PRECEDENTES}/{slug}.md"


if __name__ == "__main__":
    import sys
    alvo = sys.argv[1] if len(sys.argv) > 1 else "Tema 1061"
    print(consultar_julgado(alvo))
