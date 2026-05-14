# -*- coding: utf-8 -*-
"""
Verificação programática de OAB/subscritor/template a partir de oabs.json.

Uso:

    from oab_check import verificar_oab, template_do_subscritor, localizar_advogado

    info = verificar_oab("Eduardo Fernando Rebonatto", "A2118", "AM")
    # -> {'ok': True, 'advogado': 'EDUARDO FERNANDO REBONATTO', 'template': 1, 'mensagem': '...'}

    tpl = template_do_subscritor("Gabriel Cardoso de Aguiar")  # -> 2
"""

from __future__ import annotations

import json
import os
import unicodedata
from typing import Dict, Optional


_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "oabs.json")


def _norm(s: str) -> str:
    if not s:
        return ""
    n = unicodedata.normalize("NFKD", s)
    n = "".join(c for c in n if not unicodedata.combining(c))
    return n.upper().strip()


def carregar_base(caminho: str = _DEFAULT_PATH) -> Dict:
    caminho = os.path.abspath(caminho)
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def localizar_advogado(nome: str, base: Optional[Dict] = None) -> Optional[Dict]:
    """Retorna o registro do advogado (ou None)."""
    if base is None:
        base = carregar_base()
    alvo = _norm(nome)
    for adv in base.get("advogados", []):
        nome_base = _norm(adv["nome"])
        # Match por nome cheio, sobrenome+nome parcial etc.
        if alvo in nome_base or nome_base in alvo:
            return adv
        # Match por partes — todas as palavras do alvo aparecem no nome
        partes_alvo = alvo.split()
        if partes_alvo and all(p in nome_base for p in partes_alvo):
            return adv
    return None


def verificar_oab(nome: str, numero: str, uf: str,
                  base: Optional[Dict] = None) -> Dict:
    """Confirma: nome bate com algum advogado? número/UF corresponde?

    Retorna:
        ok: bool (True se tudo confere)
        advogado: nome oficial ou None
        template: 1 ou 2 ou None
        mensagem: explicação pronta para relatório
        inconsistencias: lista de alertas
    """
    if base is None:
        base = carregar_base()

    adv = localizar_advogado(nome, base)
    inc = []
    if adv is None:
        return {
            "ok": False, "advogado": None, "template": None,
            "mensagem": f"Advogado {nome!r} não localizado na base do escritório.",
            "inconsistencias": [f"Nome não reconhecido: {nome!r}"],
        }

    uf_up = uf.upper().strip()
    num_norm = numero.upper().replace(" ", "").strip()

    # Encontrar inscrição na UF
    match = None
    for insc in adv["inscricoes"]:
        if insc["uf"].upper() == uf_up:
            match = insc
            break

    if match is None:
        inc.append(f"{adv['nome']} não possui inscrição OAB/{uf_up} cadastrada na base interna.")
        return {
            "ok": False, "advogado": adv["nome"], "template": adv["template"],
            "mensagem": f"{adv['nome']} não tem OAB/{uf_up} — verificar se a inscrição é recente (não cadastrada) ou se há erro no recolhimento.",
            "inconsistencias": inc,
        }

    # Comparar número (ignora letras finais tipo 'A' para contas estendidas/suplementares)
    num_base = match["numero"].upper().replace(" ", "")
    if num_norm != num_base:
        # Aceitar variação com/sem zeros à esquerda
        if num_norm.lstrip("0") != num_base.lstrip("0"):
            inc.append(
                f"Número informado na peça ({numero}) difere do cadastro "
                f"({match['numero']}) para {adv['nome']} na OAB/{uf_up}."
            )
            return {
                "ok": False, "advogado": adv["nome"], "template": adv["template"],
                "mensagem": f"Divergência de número OAB/{uf_up}: peça={numero} x base={match['numero']}.",
                "inconsistencias": inc,
            }

    return {
        "ok": True, "advogado": adv["nome"], "template": adv["template"],
        "mensagem": (
            f"{adv['nome']} — OAB/{uf_up} {match['numero']} — confere. "
            f"Template aplicável: {adv['template']} "
            f"({'sócio' if adv['template'] == 1 else 'colaborador'})."
        ),
        "inconsistencias": [],
    }


def template_do_subscritor(nome: str, base: Optional[Dict] = None) -> Optional[int]:
    adv = localizar_advogado(nome, base)
    return adv["template"] if adv else None


def avaliar_competencia(uf_processo: str, nome: str,
                        base: Optional[Dict] = None) -> Dict:
    """Verifica se o advogado tem inscrição na UF do processo."""
    adv = localizar_advogado(nome, base)
    if not adv:
        return {"ok": False, "mensagem": f"Advogado {nome!r} não localizado."}

    uf_up = uf_processo.upper().strip()
    for insc in adv["inscricoes"]:
        if insc["uf"].upper() == uf_up:
            return {
                "ok": True,
                "mensagem": f"{adv['nome']} tem OAB/{uf_up} {insc['numero']} — habilitado para atuar.",
            }
    return {
        "ok": False,
        "mensagem": (
            f"{adv['nome']} NÃO possui inscrição na OAB/{uf_up} conforme base interna. "
            f"Se a peça vai ser protocolada em {uf_up}, verificar pedido de "
            f"atuação em causa própria (EAOAB art. 7º §1º) ou habilitação suplementar."
        ),
    }


if __name__ == "__main__":
    # Teste
    print(verificar_oab("Eduardo Fernando Rebonatto", "A2118", "AM"))
    print(verificar_oab("Eduardo Fernando Rebonatto", "99999", "AM"))
    print(verificar_oab("Joao Ninguem", "123", "SC"))
    print(template_do_subscritor("Gabriel Cardoso de Aguiar"))
