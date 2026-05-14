# -*- coding: utf-8 -*-
"""
Exportação do resultado da conferência para o vault Obsidian.

Ao final da conferência, grava uma nota markdown no vault com:
  - número do processo, partes, data
  - resultado 🟢🟡🔴
  - links para os DOCX gerados
  - tags padronizadas do vocabulário `_tags.md`
  - link para a ficha do cliente, se existir

Uso:

    from obsidian_export import exportar_conferencia

    exportar_conferencia(
        processo="0001384-02.2025.8.04.5800",
        resultado="🔴 NÃO PROTOCOLAR — REQUER AJUSTES",
        autor="Emilia Michiles da Silva",
        reu="Banco C6 S.A.",
        tipo_peca="Apelação",
        docx_relatorio=r"C:\\caminho\\Relatorio.docx",
        docx_edicoes=r"C:\\caminho\\Edicoes.docx",
        tags=["bancario", "consignado-nao-contratado", "maues", "juiz-anderson"],
        resumo="Apelação com 11 edições — 4 críticas.",
    )
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional


VAULT_DEFAULT = os.path.expanduser(r"~/OneDrive/Documentos/Obsidian Vault")
PASTA_CONFERENCIAS = "Conferencias"


def _slug(texto: str, max_len: int = 60) -> str:
    s = re.sub(r"[^\w\-\.\s]", "", texto, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s.strip())
    return s[:max_len]


def exportar_conferencia(
    processo: str,
    resultado: str,
    autor: str,
    reu: str,
    tipo_peca: str,
    docx_relatorio: Optional[str] = None,
    docx_edicoes: Optional[str] = None,
    tags: Optional[List[str]] = None,
    resumo: str = "",
    vault_path: Optional[str] = None,
    link_cliente: Optional[str] = None,
) -> str:
    """Grava a nota no vault e retorna o caminho absoluto do arquivo criado."""
    vp = Path(vault_path or VAULT_DEFAULT)
    pasta = vp / PASTA_CONFERENCIAS
    pasta.mkdir(parents=True, exist_ok=True)

    data = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M")
    tags_list = tags or []
    tags_list = list(dict.fromkeys(["conferencia"] + tags_list))  # dedupe

    slug = _slug(processo)
    nome_arquivo = f"{data}-{slug}.md"
    caminho = pasta / nome_arquivo

    tags_fm = "\n".join(f"  - {t}" for t in tags_list)

    linhas = [
        "---",
        "tipo: conferencia",
        f"processo: {processo}",
        f"autor: {autor}",
        f"reu: {reu}",
        f"tipo-peca: {tipo_peca}",
        f"data-conferencia: {data}",
        f"resultado: {resultado}",
        "tags:",
        tags_fm,
        "---",
        "",
        f"# Conferência — {processo}",
        "",
        f"**Data:** {data} {hora}",
        f"**Autor:** {autor}",
        f"**Réu:** {reu}",
        f"**Peça:** {tipo_peca}",
        f"**Resultado:** {resultado}",
        "",
    ]

    if resumo:
        linhas.append("## Resumo")
        linhas.append("")
        linhas.append(resumo)
        linhas.append("")

    if docx_relatorio or docx_edicoes:
        linhas.append("## Arquivos")
        linhas.append("")
        if docx_relatorio:
            linhas.append(f"- [Relatório de Conferência]({docx_relatorio})")
        if docx_edicoes:
            linhas.append(f"- [Edições Sugeridas]({docx_edicoes})")
        linhas.append("")

    if link_cliente:
        linhas.append("## Cliente")
        linhas.append("")
        linhas.append(f"Ver ficha: [[{link_cliente}]]")
        linhas.append("")

    linhas.append("## Próximos passos")
    linhas.append("")
    linhas.append("- [ ] Aplicar edições sugeridas no .docx da peça")
    linhas.append("- [ ] Revisar resultado antes de protocolar")
    linhas.append("- [ ] Protocolar no sistema")
    linhas.append("- [ ] Registrar movimentação no [[Diario/" + data + "|diário]]")
    linhas.append("")

    caminho.write_text("\n".join(linhas), encoding="utf-8")
    return str(caminho)


def atualizar_indice(vault_path: Optional[str] = None) -> str:
    """(Opcional) Cria/atualiza Conferencias/_index.md com lista dataview."""
    vp = Path(vault_path or VAULT_DEFAULT)
    pasta = vp / PASTA_CONFERENCIAS
    pasta.mkdir(parents=True, exist_ok=True)
    indice = pasta / "_index.md"
    conteudo = """---
tipo: indice
tags: [indice, conferencia]
---

# Conferências Processuais

Registro das conferências realizadas com a skill `conferencia-processual`.

## Últimas conferências

```dataview
TABLE resultado AS "Resultado", autor AS "Autor", reu AS "Réu", tipo-peca AS "Peça"
FROM "Conferencias"
WHERE tipo = "conferencia"
SORT data-conferencia DESC
LIMIT 30
```

## Semáforo agregado

```dataview
TABLE WITHOUT ID resultado AS "Resultado", length(rows) AS "Qtd"
FROM "Conferencias"
WHERE tipo = "conferencia"
GROUP BY resultado
```
"""
    indice.write_text(conteudo, encoding="utf-8")
    return str(indice)


if __name__ == "__main__":
    caminho = exportar_conferencia(
        processo="0000000-00.0000.0.00.0000",
        resultado="🟢 Pronta para protocolo",
        autor="Fulano de Tal",
        reu="Banco Exemplo",
        tipo_peca="Teste",
        tags=["teste"],
        resumo="Teste do módulo.",
    )
    print(f"Nota criada em: {caminho}")
