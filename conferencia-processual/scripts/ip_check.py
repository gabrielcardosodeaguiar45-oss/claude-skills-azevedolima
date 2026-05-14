# -*- coding: utf-8 -*-
"""
Verificação local de endereços IP citados em peças e contratos.

Classifica IPs como público/privado/reservado sem consultar rede externa
— usa a tabela estática de blocos reservados (RFC 1918, RFC 4193, RFC
3927, etc.) e os prefixos de alocação regional (LACNIC, RIPE, ARIN,
APNIC, AFRINIC).

Objetivo prático: impedir que a skill deixe passar afirmações como
"IP 2804:18:... é rede privada" (falso: 2804::/12 é público brasileiro
alocado pela LACNIC).

Uso:

    from ip_check import classificar_ip

    info = classificar_ip("2804:18:6821:8052:29e2:ddad:4060:eefe")
    # -> {
    #   'versao': 6,
    #   'tipo': 'publico',
    #   'regiao': 'LACNIC (Brasil / América do Sul)',
    #   'privado': False,
    #   'mensagem': 'IPv6 público alocado pela LACNIC...'
    # }
"""

from __future__ import annotations

import ipaddress
from typing import Dict


# Prefixos IPv6 relevantes e suas alocações regionais
# (simplificado — cobre os casos mais comuns em peças brasileiras)
PREFIXOS_IPV6 = [
    ("2001:1200::/23", "LACNIC (Brasil / América do Sul)"),
    ("2800::/12", "LACNIC (América Latina)"),
    ("2001:0db8::/32", "DOCUMENTAÇÃO (RFC 3849)"),
    ("2001::/32", "TEREDO (túnel IPv6)"),
    ("2002::/16", "6to4 (transição)"),
    ("2620::/23", "ARIN (América do Norte)"),
    ("2610::/23", "ARIN (América do Norte)"),
    ("2001:0400::/23", "ARIN"),
    ("2001:0200::/23", "APNIC (Ásia-Pacífico)"),
    ("2400::/12", "APNIC"),
    ("2a00::/12", "RIPE NCC (Europa/MENA)"),
    ("2001:0600::/23", "RIPE NCC"),
    ("2001:4200::/23", "AFRINIC (África)"),
]

PREFIXOS_IPV6_PRIVADOS_OU_RESERVADOS = [
    ("fc00::/7", "Unique Local Address (ULA) — rede privada IPv6"),
    ("fe80::/10", "Link-local IPv6"),
    ("::1/128", "Loopback IPv6"),
    ("::/128", "Unspecified IPv6"),
    ("ff00::/8", "Multicast IPv6"),
    ("100::/64", "Discard prefix"),
]


def _match_prefix(ip_obj, prefix_list) -> str:
    for cidr, descricao in prefix_list:
        try:
            if ip_obj in ipaddress.ip_network(cidr, strict=False):
                return descricao
        except ValueError:
            continue
    return ""


def classificar_ip(endereco: str) -> Dict:
    """Classifica um endereço IPv4 ou IPv6.

    Retorna dict com:
        versao (int 4 ou 6)
        tipo: 'publico' | 'privado' | 'reservado' | 'documentacao'
              | 'loopback' | 'link-local' | 'multicast' | 'invalido'
        regiao: str
        privado: bool
        mensagem: str — explicação pronta para o relatório
    """
    endereco = endereco.strip()
    try:
        ip = ipaddress.ip_address(endereco)
    except ValueError:
        return {
            "versao": None,
            "tipo": "invalido",
            "regiao": "",
            "privado": False,
            "mensagem": f"Endereço IP inválido: {endereco!r}.",
        }

    versao = 4 if isinstance(ip, ipaddress.IPv4Address) else 6

    # Loopback, link-local, multicast, reserved (cobre v4 e v6)
    if ip.is_loopback:
        return {
            "versao": versao, "tipo": "loopback", "regiao": "",
            "privado": True,
            "mensagem": f"IPv{versao} de loopback (endereço interno da própria máquina).",
        }
    if ip.is_link_local:
        return {
            "versao": versao, "tipo": "link-local", "regiao": "",
            "privado": True,
            "mensagem": f"IPv{versao} link-local — válido apenas no segmento de rede local, não roteável na Internet pública.",
        }
    if ip.is_multicast:
        return {
            "versao": versao, "tipo": "multicast", "regiao": "",
            "privado": False,
            "mensagem": f"IPv{versao} multicast — não identifica hospedeiro único.",
        }
    if ip.is_private:
        return {
            "versao": versao, "tipo": "privado", "regiao": "",
            "privado": True,
            "mensagem": f"IPv{versao} privado (RFC 1918/RFC 4193) — usado em redes internas, NÃO roteável na Internet pública.",
        }
    if ip.is_reserved or ip.is_unspecified:
        return {
            "versao": versao, "tipo": "reservado", "regiao": "",
            "privado": True,
            "mensagem": f"IPv{versao} reservado/não especificado.",
        }

    # IPv6 ULA tem prioridade (fc00::/7) — mas already is_private
    if versao == 6:
        privado_desc = _match_prefix(ip, PREFIXOS_IPV6_PRIVADOS_OU_RESERVADOS)
        if privado_desc:
            return {
                "versao": 6, "tipo": "privado", "regiao": "",
                "privado": True,
                "mensagem": f"IPv6 {privado_desc} — NÃO roteável na Internet pública.",
            }
        regiao = _match_prefix(ip, PREFIXOS_IPV6) or "alocação IPv6 pública"
        if "DOCUMENTAÇÃO" in regiao:
            return {
                "versao": 6, "tipo": "documentacao", "regiao": regiao,
                "privado": False,
                "mensagem": "IPv6 reservado para documentação (RFC 3849) — não é endereço real de produção.",
            }
        return {
            "versao": 6, "tipo": "publico", "regiao": regiao,
            "privado": False,
            "mensagem": (
                f"IPv6 público — prefixo pertence à {regiao}. "
                f"É endereço roteável na Internet, comumente atribuído por operadoras de "
                f"telefonia móvel ou banda larga. A identificação individual do usuário "
                f"exige requisição formal ao provedor de conexão, pois endereços IPv6 "
                f"móveis costumam ser dinâmicos e rotacionados."
            ),
        }

    # IPv4 público
    return {
        "versao": 4, "tipo": "publico", "regiao": "IPv4 global",
        "privado": False,
        "mensagem": (
            "IPv4 público, roteável na Internet. A identificação individual do usuário "
            "exige requisição formal ao provedor de conexão."
        ),
    }


def alerta_se_alegacao_incorreta(endereco: str, texto_peca: str) -> str:
    """Detecta alegações incorretas sobre IP na peça.

    Se o IP for público e a peça o descrever como 'privado'/'interno',
    retorna mensagem de alerta. Caso contrário, retorna string vazia.
    """
    info = classificar_ip(endereco)
    if info["tipo"] == "invalido":
        return ""
    texto_l = texto_peca.lower()

    alegado_privado = any(
        termo in texto_l
        for termo in (
            "rede interna", "rede privada", "faixa privada",
            "faixa interna", "ip privado", "ip interno",
            "rede interna/privada",
        )
    )
    if alegado_privado and not info["privado"]:
        return (
            f"[ALERTA TÉCNICO] A peça descreve o IP {endereco} como 'rede "
            f"privada/interna', mas a análise estática mostra que se trata "
            f"de {info['mensagem']} "
            f"Manter essa alegação exposta permite ao banco demoli-la em "
            f"contrarrazões com simples consulta a whois."
        )
    return ""


if __name__ == "__main__":
    import sys
    enderecos = sys.argv[1:] or [
        "2804:18:6821:8052:29e2:ddad:4060:eefe",
        "192.168.1.1",
        "10.0.0.1",
        "8.8.8.8",
        "fc00::1",
        "fe80::1",
        "2a00:1450:4001:830::200e",
    ]
    for e in enderecos:
        r = classificar_ip(e)
        print(f"{e}: {r['tipo']} | {r['mensagem'][:80]}")
