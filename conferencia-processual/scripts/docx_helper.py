# -*- coding: utf-8 -*-
"""
Extração literal de texto de DOCX com asserção programática.

Objetivo: impedir que a skill parafraseie ou confabule trechos da peça.
Todo texto citado no relatório ou usado como âncora passa por
`extrair_trecho()` ou `assert_trecho_presente()` antes de ser escrito
no DOCX de saída.

Uso típico:

    from docx_helper import PecaDocx

    peca = PecaDocx(r"C:/caminho/apelacao.docx")
    trecho = peca.buscar_unico("A divergência encontrada compromete")
    # -> retorna o parágrafo inteiro que contém o fragmento; levanta
    # se o fragmento não existir ou aparecer mais de uma vez.

    paragrafos = peca.paragrafos_com_numeracao()
    # -> [(1, "Ao Juízo..."), (2, "..."), ...]

    peca.assert_literal("A divergência encontrada compromete a integridade")
    # -> levanta AssertionError se o trecho não existir literalmente.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Tuple

try:
    from docx import Document
except ImportError as e:
    raise RuntimeError(
        "python-docx é obrigatório. Instale com: pip install python-docx"
    ) from e


def _normalizar(texto: str) -> str:
    """Normaliza espaços e hífens tipográficos para busca tolerante.

    Mantém acentos — só o essencial para que um trecho copiado da peça
    (com hífen Unicode U+2010) consiga achar correspondência em busca
    com hífen comum U+002D, e vice-versa. Espaços duplos viram simples.
    """
    if not texto:
        return ""
    # Normaliza hífens e aspas tipográficas
    mapa = {
        "\u2010": "-",  # HYPHEN
        "\u2011": "-",  # NON-BREAKING HYPHEN
        "\u2013": "-",  # EN DASH
        "\u2014": "-",  # EM DASH
        "\u2212": "-",  # MINUS
        "\u201c": '"',  # LEFT DOUBLE QUOTATION
        "\u201d": '"',  # RIGHT DOUBLE QUOTATION
        "\u2018": "'",
        "\u2019": "'",
        "\u00a0": " ",  # NBSP
    }
    for k, v in mapa.items():
        texto = texto.replace(k, v)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


class PecaDocx:
    """Envoltório para leitura literal de um arquivo .docx."""

    def __init__(self, caminho: str):
        self.caminho = caminho
        self._doc = Document(caminho)
        self._paragrafos: List[str] = [
            p.text for p in self._doc.paragraphs
        ]
        # Concatenação normalizada para busca
        self._texto_completo = "\n".join(self._paragrafos)
        self._texto_normalizado = _normalizar(self._texto_completo)

    # ------------------------------------------------------------------ #
    # Leitura básica
    # ------------------------------------------------------------------ #
    @property
    def paragrafos(self) -> List[str]:
        """Lista de parágrafos na ordem em que aparecem no documento."""
        return list(self._paragrafos)

    def paragrafos_com_numeracao(self) -> List[Tuple[int, str]]:
        """Retorna [(n, texto)] apenas dos parágrafos com conteúdo."""
        out = []
        n = 0
        for texto in self._paragrafos:
            n += 1
            if texto.strip():
                out.append((n, texto))
        return out

    # ------------------------------------------------------------------ #
    # Busca e asserção
    # ------------------------------------------------------------------ #
    def ocorrencias(self, fragmento: str) -> int:
        """Conta ocorrências do fragmento no texto completo (normalizado)."""
        frag = _normalizar(fragmento)
        if not frag:
            return 0
        return self._texto_normalizado.count(frag)

    def assert_literal(self, fragmento: str) -> None:
        """Garante que o fragmento existe textualmente na peça."""
        n = self.ocorrencias(fragmento)
        if n == 0:
            raise AssertionError(
                f"Trecho não encontrado literalmente na peça: "
                f"{fragmento[:120]!r}"
            )

    def assert_unico(self, fragmento: str) -> None:
        """Garante que o fragmento aparece EXATAMENTE uma vez (âncora única)."""
        n = self.ocorrencias(fragmento)
        if n == 0:
            raise AssertionError(
                f"Âncora não encontrada: {fragmento[:120]!r}"
            )
        if n > 1:
            raise AssertionError(
                f"Âncora ambígua — aparece {n} vezes: {fragmento[:120]!r}. "
                f"Aumente a âncora até ela ser única em toda a peça."
            )

    def buscar_unico(self, fragmento: str) -> str:
        """Retorna o parágrafo inteiro que contém o fragmento.

        Levanta se inexistente ou se aparecer em mais de um parágrafo.
        """
        frag = _normalizar(fragmento)
        if not frag:
            raise ValueError("Fragmento vazio.")
        candidatos = []
        for texto in self._paragrafos:
            if frag in _normalizar(texto):
                candidatos.append(texto)
        if not candidatos:
            raise AssertionError(
                f"Fragmento não encontrado: {fragmento[:120]!r}"
            )
        if len(candidatos) > 1:
            raise AssertionError(
                f"Fragmento aparece em {len(candidatos)} parágrafos — "
                f"especifique mais: {fragmento[:120]!r}"
            )
        return candidatos[0]

    def paragrafo_apos(self, fragmento: str) -> str:
        """Retorna o parágrafo imediatamente após o que contém o fragmento."""
        frag = _normalizar(fragmento)
        for i, texto in enumerate(self._paragrafos):
            if frag in _normalizar(texto):
                # Avança para o próximo parágrafo com texto
                for j in range(i + 1, len(self._paragrafos)):
                    if self._paragrafos[j].strip():
                        return self._paragrafos[j]
                return ""
        raise AssertionError(f"Fragmento não encontrado: {fragmento[:120]!r}")


# ---------------------------------------------------------------------- #
# Utilitários públicos auxiliares
# ---------------------------------------------------------------------- #
def validar_ancora_e_trecho(
    peca: PecaDocx, ancora: str, trecho_original: str
) -> None:
    """Validação cruzada recomendada para toda edição.

    - A âncora deve aparecer exatamente uma vez.
    - O trecho original deve aparecer na peça.
    - A âncora deve ocorrer ANTES do trecho original no texto.
    """
    peca.assert_unico(ancora)
    peca.assert_literal(trecho_original)

    texto = _normalizar(peca._texto_completo)
    pos_ancora = texto.find(_normalizar(ancora))
    pos_trecho = texto.find(_normalizar(trecho_original))

    if pos_ancora == -1 or pos_trecho == -1:
        raise AssertionError("Posição não localizável.")
    if pos_ancora > pos_trecho:
        raise AssertionError(
            "A âncora aparece DEPOIS do trecho original — "
            "a âncora deve ser o parágrafo IMEDIATAMENTE ANTERIOR ao "
            "trecho a editar."
        )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python docx_helper.py <caminho.docx>")
        sys.exit(1)
    p = PecaDocx(sys.argv[1])
    print(f"Paragrafos totais: {len(p.paragrafos)}")
    print(f"Paragrafos com texto: {len(p.paragrafos_com_numeracao())}")
    print(f"Caracteres totais: {len(p._texto_completo)}")
