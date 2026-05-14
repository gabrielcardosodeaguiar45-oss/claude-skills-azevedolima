"""
Grifador de extratos: aplica highlights coloridos sobre os contratos
de cada cadeia detectada, em PDF do HISCON.

Funciona com text-layer (PDFs do Meu INSS sempre têm). Tenta múltiplas
estratégias para achar o número do contrato:
  1. String inteira como aparece
  2. Dividida em 6+resto (quebra mais comum no layout)
  3. Dividida em 5+resto, 7+resto
  4. Dividida em 3 partes para números longos (CAIXA RMC com 15 dígitos)
  5. Sem hífen final (ex: "326994938-8" → tenta "326994938")

Uso:
    python grifador.py <input.pdf> <output.pdf> <cadeias.json>

Onde cadeias.json é a saída do chain_detector contendo lista de componentes
com a chave 'contratos' (com 'contrato') e 'cor_grifo' (RGB tuple).
"""
import sys
import os
import json
from pathlib import Path

try:
    import fitz
except ImportError as e:
    raise ImportError(
        f"Dependência ausente: {e}. "
        f"Instale via: pip install -r requirements.txt"
    ) from e


def _open_pdf(path):
    """Abre PDF tolerando paths com chars Unicode problemáticos no Windows."""
    try:
        return fitz.open(path)
    except Exception:
        with open(path, "rb") as f:
            return fitz.open(stream=f.read(), filetype="pdf")


def grifar_contrato(page, contrato: str, cor: tuple) -> int:
    """
    Aplica highlight em todas as ocorrências do contrato na página.
    Tenta múltiplas estratégias de busca. Retorna número de retângulos grifados.
    """
    rects_pra_grifar = []

    # 1. String inteira
    rects = page.search_for(contrato)
    if rects:
        rects_pra_grifar.extend(rects)

    if not rects_pra_grifar and len(contrato) >= 7:
        # 2-3. Tentar dividido em 6+resto, 5+resto, 7+resto
        for split in [6, 5, 7, 8]:
            if split >= len(contrato):
                continue
            p1 = contrato[:split]
            p2 = contrato[split:]
            r1 = page.search_for(p1)
            r2 = page.search_for(p2)
            if r1 and r2:
                pares = _achar_pares_verticais(r1, r2)
                if pares:
                    for a, b in pares:
                        rects_pra_grifar.append(a)
                        rects_pra_grifar.append(b)
                    break

    if not rects_pra_grifar and len(contrato) >= 12:
        # 4. Dividido em 3 partes (números longos)
        terco = len(contrato) // 3
        if terco >= 4:
            p1 = contrato[:terco]
            p2 = contrato[terco:terco*2]
            p3 = contrato[terco*2:]
            r1 = page.search_for(p1)
            r2 = page.search_for(p2)
            r3 = page.search_for(p3)
            if r1 and r2 and r3:
                trios = _achar_trios_verticais(r1, r2, r3)
                if trios:
                    for a, b, c in trios:
                        rects_pra_grifar.extend([a, b, c])

    if not rects_pra_grifar and "-" in contrato:
        # 5. Sem hífen final
        base = contrato.split("-")[0]
        return grifar_contrato(page, base, cor)

    # Aplicar highlights
    for r in rects_pra_grifar:
        annot = page.add_highlight_annot(r)
        annot.set_colors(stroke=cor)
        annot.update()
    return len(rects_pra_grifar)


def _achar_pares_verticais(r1_list, r2_list, max_dx: float = 15, max_dy: float = 35) -> list:
    """Encontra pares (a, b) onde a e b estão alinhados verticalmente (mesma coluna)."""
    pares = []
    for a in r1_list:
        for b in r2_list:
            dx = abs(a.x0 - b.x0)
            dy = b.y0 - a.y0
            if dx < max_dx and 0 < dy < max_dy:
                pares.append((a, b))
    return pares


def _achar_trios_verticais(r1, r2, r3, max_dx: float = 15, max_dy: float = 35) -> list:
    trios = []
    for a in r1:
        for b in r2:
            for c in r3:
                dx12 = abs(a.x0 - b.x0)
                dy12 = b.y0 - a.y0
                dx23 = abs(b.x0 - c.x0)
                dy23 = c.y0 - b.y0
                if dx12 < max_dx and 0 < dy12 < max_dy and dx23 < max_dx and 0 < dy23 < max_dy:
                    trios.append((a, b, c))
    return trios


def grifar_extrato(input_path: str, output_path: str,
                   contratos_com_cor: list[tuple]) -> dict:
    """
    Grifa o extrato com cores específicas por contrato.

    contratos_com_cor: lista de (contrato_str, cor_rgb_tuple)
    Retorna dict com relatório de grifos por contrato.
    """
    relatorio = {}
    doc = _open_pdf(input_path)
    for contrato, cor in contratos_com_cor:
        total = 0
        for page in doc:
            total += grifar_contrato(page, contrato, cor)
        relatorio[contrato] = total
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return relatorio


def grifar_por_cadeias(input_path: str, output_path: str,
                       componentes: list[dict],
                       contratos_filtro: list[str] | None = None) -> dict:
    """
    Recebe lista de componentes (saída do chain_detector) e grifa o extrato.

    contratos_filtro: se fornecido, grifa apenas os contratos cujo número
    está nessa lista (útil pra grifar apenas o subset de uma pasta de ação).
    """
    contratos_com_cor = []
    for comp in componentes:
        cor = tuple(comp.get("cor_grifo", (1.0, 1.0, 0.5)))
        for c in comp.get("contratos", []):
            num = c.get("contrato")
            if not num:
                continue
            if contratos_filtro and num not in contratos_filtro:
                continue
            contratos_com_cor.append((num, cor))
    return grifar_extrato(input_path, output_path, contratos_com_cor)


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    inp, out, cadeias_json = sys.argv[1:4]
    with open(cadeias_json, encoding="utf-8") as f:
        comps = json.load(f)
    rel = grifar_por_cadeias(inp, out, comps)
    print(f"Grifos aplicados em {out}:")
    for c, n in rel.items():
        marca = "OK" if n > 0 else "NAO ACHADO"
        print(f"  {c}: {n} hits [{marca}]")


if __name__ == "__main__":
    main()
