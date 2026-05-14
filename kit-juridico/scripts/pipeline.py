"""
Orquestrador da skill kit-juridico.

NÃO é um script "rode-tudo-sozinho" — é uma máquina de estados que
expõe funções para serem chamadas pelo Claude (LLM) em ordem. Cada fase
prepara dados estruturados e/ou crops visuais; algumas fases exigem
o Claude para interpretar (classificar PDF, extrair banco/contrato de
imagem rotacionada).

FASES (chamadas pelo SKILL.md):

    fase_a_inventario(pasta_cliente)
        → lista de arquivos brutos com metadados (tipo MIME, tem text-layer, ...)

    fase_b_classificar_brutos(pasta_cliente)
        → estrutura do que aparenta ser cada PDF (proc/RG/comp/extrato/...).
        Para arquivos ambíguos, retorna paths de crops para o Claude analisar
        visualmente.

    fase_c_extrair_procuracoes(pdf_procuracoes, pasta_cliente)
        → gera crops de cada página do PDF de procurações; o Claude lê e
        retorna lista de {pag, banco, tipo, contrato}.
        A skill então armazena no manifesto.

    fase_d_parsear_extratos(extratos)
        → roda hiscon_parser; retorna estrutura por benefício.

    fase_e_detectar_cadeias(contratos_por_beneficio)
        → roda chain_detector; retorna componentes por benefício.

    fase_f_montar_estrutura(pasta_cliente, manifesto, cadeias)
        → cria pastas finais BENEFÍCIO/BANCO/, fatia procurações, replica
        documentos comuns, grifa extratos, gera ESTUDO.docx.

    fase_g_gerar_pendencias(pasta_cliente, alertas)
        → gera Pendências.xlsx com todos os alertas coletados.

Uso CLI (atalho para validar partes):

    python pipeline.py inventario <pasta_cliente>
    python pipeline.py extratos <hiscon_a.pdf> [<hiscon_b.pdf> ...]
    python pipeline.py cadeias <componentes.json>
    python pipeline.py montar <manifesto.json>
"""
import sys
import os
import json
import shutil
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Imports relativos do mesmo diretório
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

import fitz  # noqa
from pdf_utils import (has_text_layer, count_pages, open_pdf as _open_pdf,
                       score_kit_assinado, escolher_kit_assinado)
from proc_extractor import preparar_crops, crop_linha_contrato
from hiscon_parser import parsear_hiscon
from chain_detector import detectar_cadeias, agrupar_em_pastas_acao, _nome_pasta_banco
from grifador import grifar_extrato
from estudo_docx import gerar_estudo
from gerar_pendencias import create_pendencias_xlsx
from seletor_contratos import selecionar_para_todas_pastas
from planilha_impugnar import gerar_planilha as gerar_planilha_impugnar


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".img", ".bmp", ".tiff", ".tif", ".webp"}
PDF_EXTS = {".pdf"}
DOC_EXTS = {".doc", ".docx", ".odt"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg"}


# =========================================================================
# FASE A — INVENTÁRIO
# =========================================================================

def fase_a_inventario(pasta_cliente: str) -> dict:
    """Lista arquivos brutos da pasta com metadados."""
    base = Path(pasta_cliente)
    inv = {
        "pasta": str(base),
        "data_inventario": datetime.now().isoformat(),
        "arquivos": [],
    }
    for f in base.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(base)
        ext = f.suffix.lower()
        meta = {
            "path_relativo": str(rel),
            "path_absoluto": str(f),
            "tamanho_bytes": f.stat().st_size,
            "extensao": ext,
            "categoria_arquivo": _categoria_extensao(ext),
        }
        if ext in PDF_EXTS:
            try:
                meta["paginas"] = count_pages(str(f))
                meta["tem_text_layer"] = has_text_layer(str(f))
            except Exception as e:
                meta["erro_leitura"] = str(e)
        inv["arquivos"].append(meta)
    return inv


def _categoria_extensao(ext: str) -> str:
    if ext in PDF_EXTS:
        return "PDF"
    if ext in IMAGE_EXTS:
        return "IMAGEM"
    if ext in DOC_EXTS:
        return "WORD"
    if ext in VIDEO_EXTS:
        return "VIDEO"
    if ext in AUDIO_EXTS:
        return "AUDIO"
    return "OUTRO"


# =========================================================================
# FASE B — CLASSIFICAÇÃO DE PDFs (heurísticas + crops para Vision quando precisar)
# =========================================================================

def fase_b_classificar_pdfs(pasta_cliente: str, inv: dict) -> dict:
    """
    Para cada PDF, tenta classificar via heurística sobre nome e text-layer.
    Retorna manifesto preliminar; PDFs ambíguos recebem flag para análise
    visual pelo Claude.
    """
    base = Path(pasta_cliente)
    classificacao = {"pdfs": [], "imagens": [], "outros": []}

    for arq in inv["arquivos"]:
        ext = arq["extensao"]
        path_abs = arq["path_absoluto"]
        nome = Path(path_abs).name
        nome_lower = nome.lower()

        if ext in PDF_EXTS:
            sugestao = _sugerir_tipo_pdf(nome_lower, path_abs)
            classificacao["pdfs"].append({
                **arq,
                "tipo_sugerido": sugestao["tipo"],
                "confianca": sugestao["confianca"],
                "necessita_visao": sugestao["confianca"] < 0.7,
            })
        elif ext in IMAGE_EXTS:
            classificacao["imagens"].append(arq)
        else:
            classificacao["outros"].append(arq)

    # Reconciliação de múltiplos KIT_ASSINADO — só o de maior score fica.
    # Caso paradigma: Guilherme tinha KIT (Word) + Processo (CamScanner) na
    # mesma pasta. Sem reconciliação, ambos viravam KIT_ASSINADO. Agora o
    # de menor score é rebaixado a KIT_MODELO (intacto fisicamente).
    candidatos_kit = [p for p in classificacao["pdfs"]
                      if p.get("tipo_sugerido") == "KIT_ASSINADO"]
    if len(candidatos_kit) > 1:
        # Ordena por score (se disponível) desc, depois tamanho desc
        candidatos_kit.sort(
            key=lambda p: (p.get("score_kit", 0), p.get("tamanho_bytes", 0)),
            reverse=True,
        )
        vencedor = candidatos_kit[0]
        for outro in candidatos_kit[1:]:
            outro["tipo_sugerido"] = "KIT_MODELO"
            outro["motivo_rebaixamento"] = (
                f"Rebaixado para KIT_MODELO porque outro PDF venceu como "
                f"KIT_ASSINADO: {Path(vencedor['path_absoluto']).name} "
                f"(score={vencedor.get('score_kit', '?')}). "
                f"Este: score={outro.get('score_kit', '?')}."
            )

    return classificacao


def _sugerir_tipo_pdf(nome_lower: str, path: str) -> dict:
    """
    Heurística por nome + texto.
    Tipos possíveis:
        PROCURACAO, RG_CPF, CNH, DECLARACAO_HIPOSSUFICIENCIA,
        COMPROVANTE_RESIDENCIA, HISCON, HISCRE, EXTRATO_BANCARIO,
        CONTRATO_HONORARIOS, KIT_ASSINADO, KIT_MODELO, TERMO_LGPD,
        DECLARACAO_RESIDENCIA_TERCEIRO, RG_TERCEIRO, OUTRO
    """
    # Caso especial — PDFs candidatos a "kit do cliente" (nomes ambíguos
    # como "KIT GUILHERME.pdf" ou "Processo Guilherme.pdf"). Aqui o nome
    # NÃO é suficiente: o template em branco ("KIT ...") fica indistinguível
    # do kit completo no nome. Recorremos a sinais físicos do PDF (producer,
    # text-layer, imagens raster, tamanho) via score_kit_assinado.
    # Caso paradigma: Guilherme 2026-05-14.
    if 'kit' in nome_lower or nome_lower.startswith('processo'):
        try:
            score_info = score_kit_assinado(path)
            if score_info['classificacao'] == 'ASSINADO':
                return {"tipo": "KIT_ASSINADO", "confianca": 0.90,
                        "score_kit": score_info['score'],
                        "sinais_kit": score_info['sinais']}
            elif score_info['classificacao'] == 'MODELO':
                return {"tipo": "KIT_MODELO", "confianca": 0.90,
                        "score_kit": score_info['score'],
                        "sinais_kit": score_info['sinais']}
            # AMBIGUO → continua para keywords normais
        except Exception:
            pass

    # Por nome
    keywords = [
        ("PROCURACAO", ["procura"]),
        ("RG_CPF", ["rg", "cpf", "identidade"]),
        ("CNH", ["cnh", "habilita"]),
        ("DECLARACAO_HIPOSSUFICIENCIA", ["hipossuf", "hiposuf"]),
        ("COMPROVANTE_RESIDENCIA", ["comprovante", "residencia", "residência", "energia", "agua", "água", "telefone", "celesc"]),
        ("HISCON", ["historico de emprestimo", "histórico de empréstimo", "hiscon", "extrato de emprestimo", "extrato de empréstimo"]),
        ("HISCRE", ["historico de pagamento", "histórico de pagamento", "hiscre", "historico de credito", "histórico de crédito"]),
        ("EXTRATO_BANCARIO", ["extrato bancario", "extrato bancário"]),
        ("CONTRATO_HONORARIOS", ["honorario", "honorário", "prestacao de servico", "prestação de serviço"]),
        ("KIT_ASSINADO", ["assinad"]),  # "kit" sozinho NÃO é suficiente — ver bloco acima
        ("KIT_MODELO", ["modelo", "branco"]),
        ("TERMO_LGPD", ["lgpd", "consentimento", "atendimento"]),
        ("DECLARACAO_RESIDENCIA_TERCEIRO", ["declaracao de residencia", "declaração de residência"]),
        ("DOC_TESTEMUNHA", ["testemunha"]),
        ("DOC_ROGADO", ["rogado", "rogo"]),
    ]
    for tipo, kws in keywords:
        for kw in kws:
            if kw in nome_lower:
                return {"tipo": tipo, "confianca": 0.85}

    # Por conteúdo (se text-layer existe)
    try:
        if has_text_layer(path, threshold=100):
            with _open_pdf(path) as doc:
                txt = (doc[0].get_text() if len(doc) > 0 else "").upper()
            content_keys = [
                ("PROCURACAO", ["PROCURAÇÃO", "OUTORGANTE", "OUTORGADOS", "PODERES ESPECIAIS"]),
                ("HISCON", ["HISTÓRICO DE", "EMPRÉSTIMO CONSIGNADO", "Nº BENEFÍCIO"]),
                ("HISCRE", ["HISTÓRICO DE CRÉDITOS", "ESPÉCIE:"]),
                ("DECLARACAO_HIPOSSUFICIENCIA", ["HIPOSSUFICIÊNCIA", "INSUFICIÊNCIA DE RECURSOS"]),
                ("COMPROVANTE_RESIDENCIA", ["FATURA", "VENCIMENTO", "CONTA DE ENERGIA", "ÁGUA"]),
                ("CONTRATO_HONORARIOS", ["HONORÁRIOS", "PRESTAÇÃO DE SERVIÇOS ADVOCATÍCIOS"]),
                ("TERMO_LGPD", ["LGPD", "CONSENTIMENTO PARA TRATAMENTO"]),
            ]
            for tipo, kws in content_keys:
                hits = sum(1 for kw in kws if kw in txt)
                if hits >= 2:
                    return {"tipo": tipo, "confianca": 0.75}
                if hits >= 1:
                    return {"tipo": tipo, "confianca": 0.55}
    except Exception:
        pass

    return {"tipo": "AMBIGUO", "confianca": 0.0}


# =========================================================================
# FASE C — EXTRAIR PROCURAÇÕES (gera crops; Claude lê e popula manifesto)
# =========================================================================

def fase_c_preparar_procuracoes(pdf_procuracoes: str, pasta_trabalho: str) -> dict:
    """
    Renderiza cada página do PDF de procurações já com rotação correta e
    crop do bloco PODERES ESPECIAIS. O Claude (orquestrador) deve então
    ler cada crop e devolver banco+tipo+contrato.
    """
    out_dir = os.path.join(pasta_trabalho, "_proc_crops")
    os.makedirs(out_dir, exist_ok=True)
    return preparar_crops(pdf_procuracoes, out_dir)


def fase_c_revalidar_pagina(pdf_procuracoes: str, pag_num: int, pasta_trabalho: str) -> str:
    """Faz crop super-zoom só da linha do contrato (para revalidação)."""
    out = os.path.join(pasta_trabalho, "_proc_crops", f"linha_pag_{pag_num:02d}.png")
    return crop_linha_contrato(pdf_procuracoes, pag_num, out)


# =========================================================================
# FASE D — PARSEAR EXTRATOS HISCON
# =========================================================================

def fase_d_parsear_extratos(paths_hiscon: list[str]) -> list[dict]:
    """Roda hiscon_parser em cada arquivo. Retorna lista de resultados."""
    resultados = []
    for p in paths_hiscon:
        r = parsear_hiscon(p)
        resultados.append(r)
    return resultados


def mapear_contratos_por_beneficio(extratos_parseados: list[dict]) -> dict:
    """Mapeia cada contrato para o benefício (NB) ao qual pertence.

    Quando o cliente tem 2+ benefícios INSS (ex.: aposentadoria + pensão),
    cada HISCON é específico de um benefício. O mesmo número de contrato
    aparece em UM e SÓ UM dos HISCONs — o que indica a quem o contrato
    pertence. Esta função consolida essa informação em um dict para a
    fase F decidir em qual pasta `<BENEFÍCIO>/...` cada contrato vai.

    Args:
        extratos_parseados: saída de `fase_d_parsear_extratos`

    Returns:
        {
            'por_contrato': {numero_contrato: {'nb': str, 'pasta_beneficio': str,
                                                'especie_nome': str}},
            'beneficios': [{'nb': str, 'pasta_beneficio': str, 'especie_nome': str,
                            'qtd_contratos': int}],
            'multiplos_beneficios': bool,
            'avisos': [str],  # contratos órfãos, ambíguos etc.
        }

    Caso paradigma: Guilherme 2026-05-14. Tem APOSENTADORIA (NB 138.604.869-8,
    27 contratos) e PENSÃO (NB 192.327.516-7, 2 contratos). Cada contrato
    impugnado é mapeado para o benefício correto antes de criar a estrutura
    `<CLIENTE>/<BENEFÍCIO>/<TESE>/<BANCO>/`.
    """
    por_contrato = {}
    beneficios = []
    avisos = []

    for ext in extratos_parseados:
        if ext.get('is_ocr_required'):
            continue
        benef = ext.get('beneficio', {}) or {}
        nb = benef.get('numero_beneficio') or benef.get('nb') or ''
        pasta_benef = benef.get('pasta_beneficio') or ''
        especie = benef.get('especie_nome') or benef.get('beneficio') or ''
        contratos_aqui = ext.get('contratos', [])
        beneficios.append({
            'nb': nb,
            'pasta_beneficio': pasta_benef,
            'especie_nome': especie,
            'qtd_contratos': len(contratos_aqui),
        })
        for c in contratos_aqui:
            num = (c.get('numero') or c.get('contrato') or '').strip()
            if not num:
                continue
            if num in por_contrato:
                # Mesmo contrato em 2 HISCONs — incomum mas possível em
                # portabilidades cross-benefício. Manter o primeiro e avisar.
                avisos.append(
                    f"Contrato {num} aparece em 2 benefícios "
                    f"({por_contrato[num]['nb']} e {nb}) — manter primeiro"
                )
                continue
            por_contrato[num] = {
                'nb': nb,
                'pasta_beneficio': pasta_benef,
                'especie_nome': especie,
            }

    multiplos = len(beneficios) > 1

    return {
        'por_contrato': por_contrato,
        'beneficios': beneficios,
        'multiplos_beneficios': multiplos,
        'avisos': avisos,
    }


# =========================================================================
# FASE E — DETECTAR CADEIAS
# =========================================================================

def fase_e_detectar_cadeias(extratos_parseados: list[dict]) -> dict:
    """
    Detecta cadeias por benefício e agrupa em pastas de ação.
    Retorna {beneficio_pasta: [componentes]}
    """
    por_beneficio = defaultdict(list)
    for ext in extratos_parseados:
        if ext.get("is_ocr_required"):
            continue
        beneficio_pasta = ext["beneficio"].get("pasta_beneficio", "")
        for c in ext.get("contratos", []):
            por_beneficio[beneficio_pasta].append(c)

    out = {}
    for benef, contratos in por_beneficio.items():
        cadeias = detectar_cadeias(contratos, beneficio_pasta=benef)
        out[benef] = cadeias
    return out


# =========================================================================
# FASE F — MONTAR ESTRUTURA FINAL
# =========================================================================

def fase_f_montar_estrutura(pasta_cliente: str,
                             pdf_procuracoes_origem: str,
                             procuracoes_extraidas: list[dict],
                             extratos_parseados: list[dict],
                             cadeias_por_beneficio: dict,
                             docs_comuns: dict,
                             cliente_nome: str = "") -> dict:
    """
    Cria estrutura final de pastas, fatia procurações, replica documentos comuns,
    grifa extratos e gera ESTUDO.docx.

    procuracoes_extraidas: lista de dicts com chaves
        {pagina, banco_chave, tipo, contrato}
    docs_comuns: dict mapeando tipo -> path (RG, comprovante, declaracao, ...).
    """
    base = Path(pasta_cliente)
    relatorio = {
        "pastas_criadas": [],
        "procuracoes_fatiadas": [],
        "extratos_grifados": [],
        "estudos_gerados": [],
        "alertas": [],
    }

    # Mapear procuração → benefício via cruzamento com extratos
    contrato_to_beneficio = {}
    contrato_to_dados_extrato = {}
    for ext in extratos_parseados:
        if ext.get("is_ocr_required"):
            continue
        benef = ext["beneficio"].get("pasta_beneficio", "")
        for c in ext.get("contratos", []):
            contrato_to_beneficio[c["contrato"]] = benef
            contrato_to_dados_extrato[c["contrato"]] = c

    # Decidir se o layout terá o nível BENEFICIO.
    # Regra: só criar nível benefício se as procurações cobrem >1 NB
    # (cliente pode ter 2 extratos mas só outorgou procurações pra um deles).
    beneficios_com_procuracoes = set()
    for proc in procuracoes_extraidas:
        contrato = proc.get("contrato")
        b = contrato_to_beneficio.get(contrato)
        if b:
            beneficios_com_procuracoes.add(b)
    multi_beneficio = len(beneficios_com_procuracoes) > 1

    # Para cada procuração, descobrir componente (cadeia) ao qual pertence
    contrato_to_componente = {}
    for benef, comps in cadeias_por_beneficio.items():
        for comp in comps:
            for c in comp.get("contratos", []):
                contrato_to_componente[c["contrato"]] = comp

    # Agrupar componentes em pastas de ação
    pastas_acao_global = {}  # (beneficio, nome_pasta) -> {componentes, procuracoes}

    for proc in procuracoes_extraidas:
        contrato = proc["contrato"]
        benef = contrato_to_beneficio.get(contrato)
        if not benef:
            relatorio["alertas"].append({
                "categoria": "Procuração / Verificação cruzada",
                "pendencia": "Contrato não localizado em nenhum extrato",
                "observacao": f"Contrato {contrato} (banco {proc.get('banco_chave', '?')}) "
                              f"não foi encontrado em nenhum HISCON parseado.",
                "status": "Pendente",
            })
            continue

        comp = contrato_to_componente.get(contrato)
        if comp is None:
            # Criar componente isolado fictício
            comp = {
                "id": f"ISO-{contrato}",
                "tipo": "ISOLADO",
                "subtipo": "ISOLADO",
                "bancos": [proc.get("banco_chave", "?")],
                "beneficio": benef,
                "contratos": [{
                    "contrato": contrato,
                    "papel": "ATUAL",
                    "ordem": 1,
                    **(contrato_to_dados_extrato.get(contrato, {})),
                }],
                "cor_grifo": (1.0, 1.0, 0.5),
                "cor_nome": "Amarelo neutro",
            }

        # Determinar pasta
        bancos_humanos = sorted(set(_nome_pasta_banco(b) for b in comp["bancos"]))
        eh_cartao = any(c.get("tipo") in ("RMC", "RCC")
                        for c in comp.get("contratos", []))
        nome_pasta_acao = " + ".join(bancos_humanos)
        if eh_cartao:
            nome_pasta_acao += " - RMC-RCC"

        chave = (benef, nome_pasta_acao)
        if chave not in pastas_acao_global:
            pastas_acao_global[chave] = {"componentes": [], "procuracoes": []}
        if comp not in pastas_acao_global[chave]["componentes"]:
            pastas_acao_global[chave]["componentes"].append(comp)
        pastas_acao_global[chave]["procuracoes"].append(proc)

    # Criar fisicamente as pastas
    import re as _re
    _PADRAO_ANTIGO_HIFEN = _re.compile(r'^\d+-\s')
    for (benef, nome_pasta_acao), conteudo in pastas_acao_global.items():
        if multi_beneficio:
            pasta_destino = base / benef / nome_pasta_acao
        else:
            pasta_destino = base / nome_pasta_acao
        pasta_destino.mkdir(parents=True, exist_ok=True)
        relatorio["pastas_criadas"].append(str(pasta_destino.relative_to(base)))

        # Limpa arquivos com nomenclatura ANTIGA (formato "X-" hífen, pré v2.2).
        # A skill v2.2 gera tudo com "X." (ponto) + travessão `–`. Sem essa
        # limpeza, ao re-rodar a fase F a pasta acumula duplicados (versão
        # antiga + versão nova). Gravado 13/05/2026.
        for _antigo in pasta_destino.iterdir():
            if _antigo.is_file() and _PADRAO_ANTIGO_HIFEN.match(_antigo.name):
                try:
                    _antigo.unlink()
                    relatorio.setdefault("arquivos_antigos_removidos", []).append(
                        str(_antigo.relative_to(base)))
                except Exception:
                    pass

        # Fatiar procurações desta pasta
        for proc in conteudo["procuracoes"]:
            pag = proc["pagina"]
            contrato = proc["contrato"]
            banco_humano = _humanizar_banco(proc.get("banco_chave", ""))
            tipo = proc.get("tipo", "CONSIGNADO")
            if tipo in ("RMC", "RCC", "RMC-RCC"):
                arq = f"2. Procuração – {banco_humano} – RMC-RCC – Contrato {contrato}.pdf"
            else:
                arq = f"2. Procuração – {banco_humano} – Contrato {contrato}.pdf"
            destino_proc = pasta_destino / arq
            _fatiar_pagina(pdf_procuracoes_origem, pag, str(destino_proc))
            relatorio["procuracoes_fatiadas"].append(str(destino_proc.relative_to(base)))

        # Replicar documentos comuns (exceto HISCRE/HISCRE_X que são tratados depois)
        for tipo_doc, src in docs_comuns.items():
            if tipo_doc.startswith("HISCRE"):
                continue
            if not src or not os.path.exists(src):
                continue
            nome_dest = _nome_doc_comum(tipo_doc)
            shutil.copy2(src, pasta_destino / nome_dest)

        # Grifar extrato (apenas contratos desta pasta)
        ext_relevante = next(
            (e for e in extratos_parseados
             if e.get("beneficio", {}).get("pasta_beneficio") == benef),
            None
        )
        if ext_relevante:
            ext_origem = ext_relevante.get("fonte")
            if ext_origem and os.path.exists(ext_origem):
                nome_grifado = (f"6. Histórico de empréstimo {benef} (grifado).pdf"
                                if multi_beneficio
                                else "6. Histórico de empréstimo (grifado).pdf")
                destino_grifado = pasta_destino / nome_grifado
                contratos_da_pasta = [c["contrato"]
                                       for comp in conteudo["componentes"]
                                       for c in comp.get("contratos", [])]
                contratos_com_cor = []
                for comp in conteudo["componentes"]:
                    cor = tuple(comp.get("cor_grifo", (1.0, 1.0, 0.5)))
                    for c in comp.get("contratos", []):
                        contratos_com_cor.append((c["contrato"], cor))
                grifar_extrato(ext_origem, str(destino_grifado), contratos_com_cor)
                relatorio["extratos_grifados"].append(str(destino_grifado.relative_to(base)))

        # Replicar HISCRE do benefício
        hiscre_path = docs_comuns.get(f"HISCRE_{benef}") or docs_comuns.get("HISCRE")
        if hiscre_path and os.path.exists(hiscre_path):
            nome_hiscre = (f"7. Histórico de créditos {benef}.pdf"
                          if multi_beneficio
                          else "7. Histórico de créditos.pdf")
            shutil.copy2(hiscre_path, pasta_destino / nome_hiscre)

        # Gerar ESTUDO.docx
        nome_estudo = f"ESTUDO DE CADEIA - {nome_pasta_acao}.docx"
        destino_estudo = pasta_destino / nome_estudo
        ext_meta = ext_relevante.get("beneficio", {}) if ext_relevante else {}
        gerar_estudo(
            str(destino_estudo),
            conteudo["componentes"],
            {
                "cliente": cliente_nome,
                "beneficio": ext_meta.get("especie", ""),
                "nb": ext_meta.get("nb", ""),
                "banco_pasta": nome_pasta_acao,
                "procuracoes": conteudo["procuracoes"],
            }
        )
        relatorio["estudos_gerados"].append(str(destino_estudo.relative_to(base)))

        # Gerar CALCULO_INDEBITO.xlsx (regra fixa do escritório, 13/05/2026):
        # cada pasta de ação tem seu cálculo automático pré-gerado. A skill
        # `inicial-nao-contratado` lê esse Excel para usar como valor da causa
        # (em vez de estimar). Pula RMC/RCC porque o regime de cálculo é
        # diferente (cobra-se restituição do limite usado do cartão, não
        # parcelas mensais).
        _eh_rmc_rcc = ("RMC-RCC" in nome_pasta_acao.upper()
                       or "RMC/RCC" in nome_pasta_acao.upper())
        if not _eh_rmc_rcc:
            try:
                import sys as _sys
                _skills_common = os.path.normpath(
                    os.path.join(os.path.dirname(__file__), "..", "..", "_common"))
                if _skills_common not in _sys.path:
                    _sys.path.insert(0, _skills_common)
                from calculadora_indebito import (
                    gerar_excel_indebito, NOME_CANONICO_EXCEL_KIT)
                # Junta todos os contratos dos componentes (que são os contratos
                # autorizados pelas procurações nesta pasta de ação)
                contratos_pasta = []
                for comp in conteudo["componentes"]:
                    for c in comp.get("contratos", []):
                        contratos_pasta.append(c)
                if contratos_pasta:
                    destino_xlsx = pasta_destino / NOME_CANONICO_EXCEL_KIT
                    gerar_excel_indebito(
                        contratos=contratos_pasta,
                        cliente_nome=cliente_nome,
                        output_path=str(destino_xlsx),
                    )
                    relatorio.setdefault("calculos_gerados", []).append(
                        str(destino_xlsx.relative_to(base)))
            except Exception as _e_calc:
                relatorio.setdefault("calculos_erros", []).append(
                    f"{nome_pasta_acao}: {type(_e_calc).__name__}: {_e_calc}")

    return relatorio


def _fatiar_pagina(pdf_origem: str, pag_num: int, destino: str):
    with _open_pdf(pdf_origem) as src:
        novo = fitz.open()
        novo.insert_pdf(src, from_page=pag_num-1, to_page=pag_num-1)
        novo.save(destino, garbage=4, deflate=True)
        novo.close()


def _humanizar_banco(chave: str) -> str:
    mapa = {
        "ITAU": "Banco Itaú Consignado",
        "ITAU_CONSIGNADO": "Banco Itaú Consignado",
        "BMG": "Banco BMG",
        "C6": "Banco C6 Consignado",
        "PAN": "Banco PAN",
        "CAIXA": "Caixa Econômica Federal",
        "BRADESCO": "Banco Bradesco",
        "SAFRA": "Banco Safra",
        "MERCANTIL": "Banco Mercantil",
        "INBURSA": "Banco Inbursa",
        "AGIBANK": "Agibank",
        "DIGIO": "Banco Dígio",
        "PARANA": "Banco Paraná",
        "OLE": "Banco Olé",
        "DAYCOVAL": "Banco Daycoval",
    }
    if chave in mapa:
        return mapa[chave]
    # Fallback: usar chave em title case
    return chave.replace("_", " ").title()


def _nome_doc_comum(tipo: str) -> str:
    """Nomes canônicos v2.2 (2026-05-11) — ponto após número, travessão na procuração.

    Nota: DOC_ROGADO/TESTEMUNHA_* nascem com descritor genérico ("do rogado",
    "da testemunha 1") porque o pipeline cria os arquivos ANTES de extrair o
    nome real do RG. O fluxo posterior (Fase 11+ ou agente) deve renomear
    adicionando o sufixo " - NOME COMPLETO" — ex.: "3.1 - RG e CPF do rogado -
    SANTANA DE SOUZA SERVALHO.pdf". Regras completas em
    `references/regras-nomenclatura.md`.
    """
    mapa = {
        "RG_CPF": "3. RG e CPF.pdf",
        "DOC_ROGADO": "3.1 - RG e CPF do rogado.pdf",
        "TESTEMUNHA_1": "3.2 - RG e CPF da testemunha 1.pdf",
        "TESTEMUNHA_2": "3.3 - RG e CPF da testemunha 2.pdf",
        "DECLARACAO_HIPOSSUFICIENCIA": "4. Declaração de hipossuficiência.pdf",
        "COMPROVANTE_RESIDENCIA": "5. Comprovante de residência.pdf",
        "DECLARACAO_RESIDENCIA_TERCEIRO": "5.1 - Declaração de domicílio.pdf",
        "RG_TERCEIRO": "5.2 - RG do declarante terceiro.pdf",
    }
    return mapa.get(tipo, f"_{tipo}.pdf")


# =========================================================================
# FASE G — PENDÊNCIAS
# =========================================================================

def fase_g_gerar_pendencias(pasta_cliente: str, alertas: list[dict]) -> str | None:
    """Gera Pendências.xlsx se houver alertas. Senão, retorna None (não cria arquivo)."""
    if not alertas:
        return None
    out = os.path.join(pasta_cliente, "Pendências.xlsx")
    create_pendencias_xlsx(out, alertas)
    return out


# =========================================================================
# FASE H — CONSOLIDAR ARQUIVOS RESIDUAIS NO 0. Kit/
# =========================================================================

def fase_h_consolidar_kit(pasta_cliente: str, arquivos_originais_para_mover: list[str] = None,
                           extras_para_mover: list[str] = None) -> dict:
    """
    Garante que existe pasta '0. Kit/' (renomeia 'KIT/' se existir) e move
    pra dentro dela todos os arquivos originais residuais (PDFs/imagens/vídeos
    que ficaram na raiz após o pipeline organizar as pastas de banco).

    arquivos_originais_para_mover: lista de paths absolutos a mover.
    extras_para_mover: outros paths (ex: pasta KIT/ existente).

    Retorna dict com estatísticas.
    """
    base = Path(pasta_cliente)
    kit_path = base / "0. Kit"

    # 1) Se existe 'KIT/' (sem prefixo) e NÃO existe '0. Kit/', renomear
    kit_legado = base / "KIT"
    if kit_legado.is_dir() and not kit_path.exists():
        kit_legado.rename(kit_path)
    elif kit_legado.is_dir() and kit_path.exists():
        # Existem ambos: mover conteúdo do legado pro novo
        for item in kit_legado.iterdir():
            destino = kit_path / item.name
            if not destino.exists():
                shutil.move(str(item), str(destino))
        if not any(kit_legado.iterdir()):
            kit_legado.rmdir()

    # 2) Garantir que '0. Kit/' existe
    kit_path.mkdir(exist_ok=True)

    # 3) Mover arquivos originais especificados (com deduplicação)
    movidos = []
    duplicatas_removidas = []
    nao_movidos = []
    for src in (arquivos_originais_para_mover or []):
        sp = Path(src)
        if not (sp.exists() and sp.is_file()):
            continue
        destino = kit_path / sp.name
        if not destino.exists():
            shutil.move(str(sp), str(destino))
            movidos.append(sp.name)
        else:
            # Já existe — verificar se é o mesmo conteúdo (tamanho + 1ª 4KB)
            if _arquivos_iguais(sp, destino):
                # Duplicata exata: o conteúdo já está preservado no kit.
                # Remover a duplicata da raiz é seguro — não é exclusão de
                # documento (cópia idêntica permanece no 0. Kit/).
                sp.unlink()
                duplicatas_removidas.append(sp.name)
            else:
                # Conteúdo diferente: salvar com sufixo numérico
                stem = sp.stem
                ext = sp.suffix
                i = 2
                while True:
                    novo_destino = kit_path / f"{stem} ({i}){ext}"
                    if not novo_destino.exists():
                        shutil.move(str(sp), str(novo_destino))
                        movidos.append(novo_destino.name)
                        break
                    i += 1

    # 4) Mover extras (ex: pasta KIT/ legada)
    for src in (extras_para_mover or []):
        sp = Path(src)
        if not sp.exists():
            continue
        destino = kit_path / sp.name
        if not destino.exists():
            shutil.move(str(sp), str(destino))
            movidos.append(sp.name)

    return {
        "movidos": movidos,
        "duplicatas_removidas": duplicatas_removidas,
        "nao_movidos": nao_movidos,
        "kit_path": str(kit_path),
    }


def _arquivos_iguais(a: Path, b: Path, sample_bytes: int = 65536) -> bool:
    """
    Compara dois arquivos. True se mesmo tamanho E mesmo conteúdo nos
    primeiros sample_bytes (suficiente pra deduplicar arquivos grandes
    como vídeos sem ler o tudo).
    """
    if a.stat().st_size != b.stat().st_size:
        return False
    with open(a, "rb") as fa, open(b, "rb") as fb:
        return fa.read(sample_bytes) == fb.read(sample_bytes)


# =========================================================================
# FASE I — CRUZAMENTO PROCURAÇÃO × HISCON COM SUGESTÃO DE CORREÇÃO
# =========================================================================

def levenshtein(a: str, b: str) -> int:
    """Distância de Levenshtein entre 2 strings (caracteres)."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j-1] + 1, prev[j-1] + cost))
        prev = curr
    return prev[-1]


def normalizar_contrato(num: str) -> str:
    """Remove pontos, espaços, hífens — mantém só dígitos."""
    return re.sub(r"[^\d]", "", num or "")


def fase_i_cruzar_procuracoes_hiscon(
    procuracoes: list[dict],
    extratos_parseados: list[dict],
    banco_chave_para_codigo: dict | None = None,
) -> dict:
    """
    Cruza cada procuração extraída com os contratos do HISCON.

    procuracoes: lista de dicts com {pagina, banco_chave, tipo, contrato}
    extratos_parseados: saída de fase_d_parsear_extratos

    Retorna dict:
    {
        "exatos":    [{procuracao, contrato_hiscon, beneficio}, ...],
        "aproximados": [{procuracao, candidatos: [{contrato, distancia, beneficio}], ...}],
        "nao_localizados": [{procuracao}, ...],
    }

    Procurações em "aproximados" e "nao_localizados" devem virar pendências
    e/ou solicitação de revisão manual.
    """
    # Indexar contratos do HISCON
    todos_contratos_hiscon = []
    for ext in extratos_parseados:
        if ext.get("is_ocr_required"):
            continue
        benef = ext["beneficio"].get("pasta_beneficio", "")
        for c in ext.get("contratos", []):
            todos_contratos_hiscon.append({
                "contrato": c.get("contrato", ""),
                "contrato_norm": normalizar_contrato(c.get("contrato", "")),
                "banco": c.get("banco", ""),
                "banco_codigo": c.get("banco_codigo", ""),
                "tipo": c.get("tipo", "CONSIGNADO"),
                "beneficio": benef,
                "raw": c,
            })

    resultado = {"exatos": [], "aproximados": [], "nao_localizados": []}

    for proc in procuracoes:
        proc_norm = normalizar_contrato(proc.get("contrato", ""))
        banco_chave = proc.get("banco_chave", "")
        tipo = proc.get("tipo", "CONSIGNADO")

        # Filtrar candidatos do mesmo banco no HISCON
        candidatos_banco = _filtrar_candidatos_por_banco(todos_contratos_hiscon, banco_chave)

        # 1. Match exato
        exato = next(
            (c for c in candidatos_banco if c["contrato_norm"] == proc_norm),
            None
        )
        if exato:
            resultado["exatos"].append({
                "procuracao": proc,
                "contrato_hiscon": exato["contrato"],
                "beneficio": exato["beneficio"],
                "tipo_real": exato["tipo"],
            })
            continue

        # 2. Match aproximado (Lev ≤ 2)
        aproximados = []
        for c in candidatos_banco:
            d = levenshtein(proc_norm, c["contrato_norm"])
            if d <= 2:
                aproximados.append({
                    "contrato": c["contrato"],
                    "distancia": d,
                    "beneficio": c["beneficio"],
                    "tipo_real": c["tipo"],
                })
        if aproximados:
            aproximados.sort(key=lambda x: x["distancia"])
            resultado["aproximados"].append({
                "procuracao": proc,
                "candidatos": aproximados,
            })
            continue

        # 3. Não localizado
        resultado["nao_localizados"].append({"procuracao": proc})

    return resultado


def _filtrar_candidatos_por_banco(contratos_hiscon: list[dict], banco_chave: str) -> list[dict]:
    """Filtra contratos do HISCON pelo banco chave da procuração (heurística)."""
    if not banco_chave:
        return contratos_hiscon
    # Mapeamento aproximado banco_chave (UI) → texto que aparece no HISCON
    mapa = {
        "ITAU":     ["ITAU"],
        "PAN":      ["PAN"],
        "C6":       ["C6"],
        "BMG":      ["BMG"],
        "CAIXA":    ["CAIXA"],
        "BRADESCO": ["BRADESCO"],
        "MERCANTIL":["MERCANTIL"],
        "DAYCOVAL": ["DAYCOVAL"],
        "FACTA":    ["FACTA"],
        "AGIBANK":  ["AGIBANK", "AGI"],
        "OLE":      ["OLE", "OLÉ"],
    }
    keywords = mapa.get(banco_chave, [banco_chave])
    out = []
    for c in contratos_hiscon:
        banco_upper = (c.get("banco", "") or "").upper()
        if any(kw in banco_upper for kw in keywords):
            out.append(c)
    return out if out else contratos_hiscon  # fallback: todos se filtro vazio


# =========================================================================
# FASE J — REGISTRO DE CORREÇÕES (aprendizado/correcoes.md)
# =========================================================================

def fase_j_registrar_correcao(
    cliente: str,
    captador: str | None,
    pagina: int,
    banco: str,
    valor_lido: str,
    valor_correto: str,
    origem: str = "usuario",
    observacao: str | None = None,
    crop_path: str | None = None,
    skill_dir: str | None = None,
):
    """
    Adiciona entrada em aprendizado/correcoes.md.
    Toda correção é registrada (política do _index.md).

    origem: "usuario" | "hiscon_exato" | "hiscon_aproximado" | "deducao"
    """
    if skill_dir is None:
        # Detectar diretório da skill (este arquivo está em scripts/)
        skill_dir = str(Path(__file__).parent.parent)
    correcoes_path = Path(skill_dir) / "aprendizado" / "correcoes.md"
    if not correcoes_path.exists():
        # Cria com cabeçalho mínimo
        correcoes_path.parent.mkdir(parents=True, exist_ok=True)
        correcoes_path.write_text(
            "# Log de Correções de Manuscritos\n\n"
            "Cada correção feita pelo usuário é registrada aqui.\n\n---\n\n",
            encoding="utf-8",
        )

    data = datetime.now().strftime("%Y-%m-%d")
    bloco = [
        f"\n## {data} — {cliente}" + (f" ({captador})" if captador else ""),
        f"\n### Pag {pagina} — Banco {banco}",
        f"- Eu li: `{valor_lido}`",
        f"- Correto: `{valor_correto}`",
        f"- Origem: {origem}",
    ]
    if observacao:
        bloco.append(f"- Observação: {observacao}")
    if crop_path:
        bloco.append(f"- Crop: `{crop_path}`")
    bloco.append("")  # linha em branco
    novo_texto = "\n".join(bloco)

    # Inserir logo abaixo do "<!-- Insira correções abaixo. Mais recentes em cima. -->"
    conteudo = correcoes_path.read_text(encoding="utf-8")
    marcador = "<!-- Insira correções abaixo. Mais recentes em cima. -->"
    if marcador in conteudo:
        conteudo = conteudo.replace(marcador, marcador + novo_texto)
    else:
        conteudo += novo_texto
    correcoes_path.write_text(conteudo, encoding="utf-8")
    return str(correcoes_path)


# =========================================================================
# FASE K — DOSSIÊ DO CLIENTE (_estado_cliente.json)
# =========================================================================

ESTADO_CLIENTE_SCHEMA_VERSION = "1.0"


def fase_k_salvar_estado_cliente(
    pasta_cliente: str,
    cliente_nome: str,
    extratos_parseados: list[dict],
    procuracoes_extraidas: list[dict],
    cadeias_por_beneficio: dict,
    relatorio_montagem: dict,
    captador: dict | None = None,
    advogado: dict | None = None,
    alertas: list[dict] | None = None,
) -> str:
    """
    Cria/atualiza o _estado_cliente.json na raiz da pasta do cliente.

    Lê o JSON existente (se houver) e PRESERVA campos de outras skills
    (notificacoes_extrajudiciais, iniciais, anotacoes_livres). Só atualiza
    os campos que kit-juridico produz.
    """
    import json
    from datetime import datetime
    base = Path(pasta_cliente)
    estado_path = base / "_estado_cliente.json"

    # Carregar estado existente se houver
    if estado_path.exists():
        try:
            estado = json.loads(estado_path.read_text(encoding="utf-8"))
        except Exception:
            estado = {}
    else:
        estado = {}

    # Schema version
    estado["schema_version"] = ESTADO_CLIENTE_SCHEMA_VERSION
    estado["ultima_atualizacao"] = datetime.now().isoformat(timespec="seconds")

    # === Cliente ===
    cliente = estado.get("cliente", {}) or {}
    cliente.setdefault("nome_completo", cliente_nome)
    if not cliente.get("nome_arquivo_padrao"):
        # Capitalize cada palavra: "ANAIZA MARIA" -> "Anaiza Maria"
        cliente["nome_arquivo_padrao"] = " ".join(
            w.capitalize() for w in cliente_nome.split()
        )
    # Tentar pegar CPF do primeiro extrato (ou manter o que está)
    if not cliente.get("cpf"):
        for ext in extratos_parseados:
            cpf = ext.get("beneficio", {}).get("cpf")  # se um dia parser preencher
            if cpf:
                cliente["cpf"] = cpf
                break
    estado["cliente"] = cliente

    # === Benefícios INSS ===
    beneficios = []
    for ext in extratos_parseados:
        if ext.get("is_ocr_required"):
            continue
        b = ext.get("beneficio", {}) or {}
        beneficios.append({
            "nb": b.get("nb"),
            "especie_codigo": b.get("codigo_especie"),
            "especie_nome": b.get("especie"),
            "pasta_label": b.get("pasta_beneficio"),
            "situacao": b.get("situacao"),
            "titular": b.get("titular"),
            "banco_pagador": b.get("banco_pagador"),
            "agencia_pagadora": b.get("agencia"),
            "conta_pagadora": b.get("conta"),
            "renda_mensal": None,  # não temos ainda
        })
    estado["beneficios_inss"] = beneficios

    # === Contratos (todos os do HISCON, indexados) ===
    contratos = []
    contrato_to_id = {}
    for ext in extratos_parseados:
        if ext.get("is_ocr_required"):
            continue
        nb = ext.get("beneficio", {}).get("nb")
        pasta_b = ext.get("beneficio", {}).get("pasta_beneficio")
        for c in ext.get("contratos", []):
            cid = f"C{len(contratos)+1:03d}"
            contrato_to_id[c.get("contrato")] = cid
            contratos.append({
                "id_interno": cid,
                "contrato": c.get("contrato"),
                "banco_chave": _detectar_banco_chave(c.get("banco", "")),
                "banco_nome_completo": c.get("banco"),
                "banco_codigo_inss": c.get("banco_codigo"),
                "tipo": c.get("tipo", "CONSIGNADO"),
                "situacao": c.get("situacao"),
                "origem_averbacao": c.get("origem"),
                "data_inclusao": c.get("data_inclusao"),
                "data_exclusao": c.get("data_exclusao"),
                "motivo_exclusao": c.get("motivo_exclusao"),
                "valor_parcela": c.get("valor_parcela"),
                "valor_emprestado": c.get("valor_emprestado"),
                "qtd_parcelas": c.get("qtd_parcelas"),
                "competencia_inicio": c.get("competencia_inicio"),
                "competencia_fim": c.get("competencia_fim"),
                "primeiro_desconto": c.get("primeiro_desconto"),
                "beneficio_nb": nb,
                "beneficio_pasta": pasta_b,
                "procuracao_origem_pagina": None,
                "procuracao_path_relativo": None,
            })
    # Cruzar com procurações pra preencher páginas
    for proc in procuracoes_extraidas:
        cid = contrato_to_id.get(proc.get("contrato"))
        if cid:
            for c in contratos:
                if c["id_interno"] == cid:
                    c["procuracao_origem_pagina"] = proc.get("pagina")
                    break
    estado["contratos"] = contratos

    # === Cadeias ===
    cadeias_lista = []
    for benef, comps in (cadeias_por_beneficio or {}).items():
        for comp in comps:
            cor_rgb = comp.get("cor_grifo", (1.0, 1.0, 0.5))
            cor_hex = "{:02X}{:02X}{:02X}".format(
                int(cor_rgb[0]*255), int(cor_rgb[1]*255), int(cor_rgb[2]*255)
            )
            contratos_ids = []
            for c in comp.get("contratos", []):
                cid = contrato_to_id.get(c.get("contrato"))
                if cid:
                    contratos_ids.append(cid)
            cadeias_lista.append({
                "id": comp.get("id"),
                "tipo": comp.get("tipo"),
                "subtipo": comp.get("subtipo"),
                "bancos": comp.get("bancos", []),
                "beneficio": benef,
                "contratos_ids": contratos_ids,
                "cor_grifo_hex": cor_hex,
                "cor_nome": comp.get("cor_nome"),
                "valor_parcela_referencia": comp.get("valor_parcela_referencia"),
                "data_referencia": comp.get("data_referencia"),
            })
    estado["cadeias"] = cadeias_lista

    # === Pastas de ação geradas ===
    pastas_acao = []
    for path_rel in (relatorio_montagem.get("pastas_criadas") or []):
        pastas_acao.append({
            "path_relativo": path_rel,
            "tipo_pasta": "banco_unico",  # heurística simples
        })

    # Heurística automática: sugerir contratos_impugnar_ids para cada pasta_acao.
    # Resultado é gravado em pastas_acao[].contratos_impugnar_ids + planilha XLSX.
    # Cruza com procurações já existentes (se houver) para definir default S/N.
    pastas_acao, linhas_planilha = selecionar_para_todas_pastas(
        pastas_acao, contratos, cadeias_lista, pasta_cliente_abs=pasta_cliente
    )
    if linhas_planilha:
        planilha_path = os.path.join(pasta_cliente, '_contratos_a_impugnar.xlsx')
        try:
            gerar_planilha_impugnar(linhas_planilha, planilha_path)
        except Exception as e:
            print(f'  [WARN] não foi possível gerar planilha: {e}')

    estado["pastas_acao"] = pastas_acao

    # === Captador ===
    if captador:
        estado["captador"] = captador

    # === Advogado responsável ===
    if advogado:
        estado["advogado_responsavel"] = advogado

    # === Histórico ===
    historico = estado.get("historico_skills", []) or []
    historico.append({
        "skill": "kit-juridico",
        "versao": "v2.0",
        "data": datetime.now().isoformat(timespec="seconds"),
        "acao": (
            f"Pasta organizada: {len(pastas_acao)} pasta(s) de banco, "
            f"{len(cadeias_lista)} cadeia(s) detectada(s), "
            f"{len(beneficios)} benefício(s) INSS."
        ),
        "alertas": alertas or [],
    })
    estado["historico_skills"] = historico

    # === Preservar campos de outras skills ===
    estado.setdefault("notificacoes_extrajudiciais", [])
    estado.setdefault("iniciais", [])
    estado.setdefault("anotacoes_livres", "")

    # Salvar
    estado_path.write_text(
        json.dumps(estado, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return str(estado_path)


def _detectar_banco_chave(banco_nome_completo: str) -> str | None:
    """Mapeia 'BANCO ITAÚ CONSIGNADO SA' -> 'ITAU' etc."""
    if not banco_nome_completo:
        return None
    s = banco_nome_completo.upper()
    mapa = [
        ("ITAU", ["ITAU", "ITAÚ"]),
        ("PAN", ["BANCO PAN", " PAN "]),
        ("C6", ["C6 CONSIGNADO", "C6"]),
        ("BMG", ["BMG"]),
        ("CAIXA", ["CAIXA"]),
        ("BRADESCO", ["BRADESCO"]),
        ("MERCANTIL", ["MERCANTIL"]),
        ("DAYCOVAL", ["DAYCOVAL"]),
        ("FACTA", ["FACTA"]),
        ("AGIBANK", ["AGIBANK", "AGI BANK"]),
        ("OLE", ["OLÉ", "OLE BONSUCESSO", "BONSUCESSO"]),
        ("SANTANDER", ["SANTANDER"]),
        ("SAFRA", ["SAFRA"]),
        ("BB", ["BANCO DO BRASIL"]),
        ("BANRISUL", ["BANRISUL"]),
        ("BRB", ["BRB"]),
        ("DIGIO", ["DIGIO", "DÍGIO"]),
        ("INBURSA", ["INBURSA"]),
        ("PARANA", ["PARANÁ", "PARANA"]),
        ("MASTER", ["BANCO MASTER"]),
        ("CREFISA", ["CREFISA"]),
    ]
    for chave, kws in mapa:
        if any(kw in s for kw in kws):
            return chave
    return None


def fase_k_carregar_estado_cliente(pasta_cliente: str) -> dict | None:
    """
    Carrega o _estado_cliente.json. Retorna None se não existir.
    Usado pelas skills DOWNSTREAM (notificação, inicial) para reaproveitar
    dados sem precisar reextrair.
    """
    import json
    estado_path = Path(pasta_cliente) / "_estado_cliente.json"
    if not estado_path.exists():
        return None
    try:
        return json.loads(estado_path.read_text(encoding="utf-8"))
    except Exception:
        return None


# =========================================================================
# CLI
# =========================================================================

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]

    if cmd == "inventario":
        inv = fase_a_inventario(sys.argv[2])
        print(json.dumps(inv, indent=2, ensure_ascii=False))

    elif cmd == "extratos":
        rs = fase_d_parsear_extratos(sys.argv[2:])
        print(json.dumps(rs, indent=2, ensure_ascii=False))

    elif cmd == "cadeias":
        with open(sys.argv[2], encoding="utf-8") as f:
            extratos = json.load(f)
        cadeias = fase_e_detectar_cadeias(extratos)
        print(json.dumps(cadeias, indent=2, ensure_ascii=False, default=str))

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
