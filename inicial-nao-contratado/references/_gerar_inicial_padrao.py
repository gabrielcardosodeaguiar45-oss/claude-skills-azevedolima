# -*- coding: utf-8 -*-
"""Gerador genérico de inicial não-contratado para 1 banco (jeal/jfal/jemg).
Recebe pasta da ação (com docs típicos), template, dados do banco réu, e
preenche tudo extraindo dos documentos da pasta.

Uso:
    gerar(pasta_acao, template, banco_reu_dict, autor_extra, federal=True)
"""
import sys, io, shutil, re
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))
from docx import Document
from helpers_docx import substituir_in_run
from extenso import extenso_moeda
from extrator_hiscre import parse_hiscre
from extrator_hiscon import parse_hiscon
from extrator_calculo import parse_calculo
from _blocos_narrativos import (
    gerar_bloco_contratos_fraudulentos,
    gerar_bloco_pedido_declaracao,
    normalizar_banco_reu,
)


def _achar_pdf(pasta: Path, *padroes_substr_lower) -> Optional[Path]:
    """Acha PDF cujo nome contém TODOS os padrões (case-insensitive)."""
    for f in pasta.iterdir():
        if not (f.is_file() and f.suffix.lower() == '.pdf'):
            continue
        nl = f.name.lower()
        if all(p in nl for p in padroes_substr_lower):
            return f
    return None


def _fmt_brl(v):
    if v is None:
        return ''
    return f'{float(v):,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.')


def gerar_inicial_pasta(
    pasta_acao: Path,
    template: Path,
    banco_reu: Dict,         # {nome, cnpj, endereco, descricao_pj}
    autor: Dict,             # {nome, estado_civil, profissao, cpf, rg, orgao_expedidor, logradouro, numero, bairro, cidade, uf, cep, nacionalidade}
    cidade_protocolo: str,
    uf_protocolo: str,
    eh_federal: bool,
    contrato_explicito: Optional[Dict] = None,  # se quiser sobrescrever extração HISCON
    saida_nome: str = 'INICIAL_GERADA.docx',
) -> Path:
    """Gera a inicial pra UMA pasta de ação (1 banco). Retorna caminho do
    arquivo gerado."""

    # === Achar PDFs principais ===
    pdf_proc = _achar_pdf(pasta_acao, 'procura')
    pdf_hiscon = _achar_pdf(pasta_acao, 'histórico', 'empréstimo') or _achar_pdf(pasta_acao, 'historico', 'emprest')
    pdf_hiscre = _achar_pdf(pasta_acao, 'histórico', 'crédito') or _achar_pdf(pasta_acao, 'historico', 'credit')
    pdf_calc = _achar_pdf(pasta_acao, 'cálculo') or _achar_pdf(pasta_acao, 'calculo')

    if not (pdf_proc and pdf_hiscre):
        raise FileNotFoundError(f'Faltam docs em {pasta_acao.name}: '
                                  f'proc={bool(pdf_proc)} hiscre={bool(pdf_hiscre)}')

    # === Parse HISCRE (benefício, NB, renda) ===
    hiscre = parse_hiscre(str(pdf_hiscre))
    nb = hiscre.get('nb_beneficio') or ''
    tipo_beneficio = (hiscre.get('especie_descricao') or '').lower()
    valor_renda = hiscre.get('valor_liquido') or 0.0
    banco_pagador_raw = (hiscre.get('banco_pagador') or '')
    # 'XXX - NOME' → 'NOME'
    banco_pagador = re.sub(r'^\d+\s*-\s*', '', banco_pagador_raw).strip()
    # detectar cartão magnético vs conta corrente — olhar primeiro registro
    # (parse simplificado: assume conta-corrente, pode refinar depois)
    op_pagador = hiscre.get('op_banco_pagador', '')

    # === Parse HISCON pra extrair contrato ===
    contrato_dict = None
    if contrato_explicito:
        contrato_dict = contrato_explicito
    elif pdf_hiscon:
        # Tentar extrair número do contrato do nome da procuração
        m = re.search(r'(\d{6,})', pdf_proc.name)
        num_alvo = m.group(1) if m else None
        if num_alvo:
            hiscon = parse_hiscon(str(pdf_hiscon))
            for c in hiscon.get('contratos', []):
                if str(c.get('numero', '')) == num_alvo:
                    contrato_dict = {
                        'numero':              c.get('numero'),
                        'valor_emprestado':    c.get('valor_emprestado'),
                        'valor_parcela':       c.get('valor_parcela'),
                        'qtd_parcelas':        c.get('qtd_parcelas'),
                        'competencia_inicio':  c.get('competencia_inicio_desconto'),
                        'data_inclusao':       (c.get('data_inclusao') or '').strftime('%d/%m/%Y') if hasattr(c.get('data_inclusao'), 'strftime') else (str(c.get('data_inclusao')) if c.get('data_inclusao') else ''),
                    }
                    break
    if not contrato_dict:
        raise RuntimeError(f'Contrato não localizado em {pasta_acao.name}')

    # === Parse Cálculo pra valor da causa ===
    valor_causa = None
    if pdf_calc:
        calc = parse_calculo(str(pdf_calc))
        valor_causa = calc.get('valor_total_geral')
    if not valor_causa:
        raise RuntimeError(f'Valor da causa não extraível de {pasta_acao.name}')

    # === Normalizar dados ===
    banco_reu_nome = normalizar_banco_reu(banco_reu['nome'])

    dados = {
        '{{vara_protocolo}}':    autor.get('vara_protocolo', '___'),
        '{{cidade_protocolo}}':  cidade_protocolo,
        '{{uf_protocolo}}':      uf_protocolo,

        '{{nome_autor}}':         autor['nome'],
        '{{nacionalidade}}':      autor.get('nacionalidade', 'brasileiro'),
        '{{estado_civil}}':       autor['estado_civil'],
        '{{profissao}}':          autor.get('profissao', 'aposentado'),
        '{{cpf_autor}}':          autor['cpf'],
        '{{rg_autor}}':           autor['rg'],
        '{{orgao_expedidor}}':    autor.get('orgao_expedidor', 'SSP/AL'),
        '{{logradouro_autor}}':   autor['logradouro'],
        '{{numero_autor}}':       autor['numero'],
        '{{bairro_autor}}':       autor['bairro'],
        '{{cidade_autor}}':       autor['cidade'],
        '{{uf_autor}}':           autor['uf'],
        '{{cep_autor}}':          autor['cep'],

        '{{banco_reu_nome}}':         banco_reu_nome,
        '{{banco_reu_descricao_pj}}': banco_reu.get('descricao_pj', 'pessoa jurídica de direito privado'),
        '{{banco_reu_cnpj}}':         banco_reu['cnpj'],
        '{{banco_reu_endereco}}':     banco_reu['endereco'],

        '{{tipo_beneficio}}':   tipo_beneficio,
        '{{nb_beneficio}}':     nb,
        '{{banco_pagador}}':    banco_pagador,
        '{{agencia_pagador}}':  re.sub(r'^.*?(\d+)\s*-.*', r'\1', op_pagador) if op_pagador else '',
        '{{conta_pagador}}':    'CARTÃO MAGNÉTICO',  # placeholder genérico; ajustar manual se for conta

        '{{valor_renda_liquida}}':         _fmt_brl(valor_renda),
        '{{valor_renda_liquida_extenso}}': extenso_moeda(valor_renda),

        '{{pedido_prioridade}}': (
            'A prioridade na tramitação, tendo em vista que a parte autora é pessoa idosa, '
            'nos termos do art. 1.048, inciso I, do Código de Processo Civil'
            if autor.get('eh_idoso', True) else ''
        ),

        '{{valor_causa}}':         _fmt_brl(valor_causa),
        '{{valor_causa_extenso}}': extenso_moeda(valor_causa),

        '{{BLOCO_CONTRATOS_FRAUDULENTOS}}': gerar_bloco_contratos_fraudulentos(
            [contrato_dict], banco_reu_nome),
        '{{BLOCO_PEDIDO_DECLARACAO}}': gerar_bloco_pedido_declaracao(
            [contrato_dict], nb),
    }

    out = pasta_acao / saida_nome
    shutil.copy2(template, out)
    doc = Document(out)
    n = 0
    for p in doc.paragraphs:
        for k, v in dados.items():
            if k in p.text:
                if substituir_in_run(p._p, {k: v}):
                    n += 1
    doc.save(out)
    return out, n, dados


# Endereços/CNPJs de bancos comuns (matriz)
BANCOS_REUS = {
    'ITAU_CONSIGNADO': {
        'nome': 'BANCO ITAÚ CONSIGNADO S.A.',
        'cnpj': '33.885.724/0001-19',
        'endereco': 'Praça Alfredo Egydio de Souza Aranha, nº 100, Torre Itaúsa, Parque Jabaquara, São Paulo/SP, CEP 04344-902',
        'descricao_pj': 'pessoa jurídica de direito privado',
    },
    'MERCANTIL': {
        'nome': 'BANCO MERCANTIL DO BRASIL S.A.',
        'cnpj': '17.184.037/0001-10',
        'endereco': 'Rua Rio de Janeiro, nº 654, Centro, Belo Horizonte/MG, CEP 30160-040',
        'descricao_pj': 'pessoa jurídica de direito privado',
    },
    'BRADESCO': {
        'nome': 'BANCO BRADESCO S.A.',
        'cnpj': '60.746.948/0001-12',
        'endereco': 'Cidade de Deus, s/nº, Vila Yara, Osasco/SP, CEP 06029-900',
        'descricao_pj': 'pessoa jurídica de direito privado',
    },
    'C6': {
        'nome': 'BANCO C6 CONSIGNADO S.A.',
        'cnpj': '61.348.538/0001-86',
        'endereco': 'Avenida Nove de Julho, 3148, Jardim Paulista, São Paulo/SP, CEP 01406-000',
        'descricao_pj': 'pessoa jurídica de direito privado',
    },
    'BMG': {
        'nome': 'BANCO BMG S.A.',
        'cnpj': '61.186.680/0001-74',
        'endereco': 'Av. Brigadeiro Faria Lima, nº 3477, Itaim Bibi, São Paulo/SP, CEP 04538-133',
        'descricao_pj': 'pessoa jurídica de direito privado',
    },
    'PAN': {
        'nome': 'BANCO PAN S.A.',
        'cnpj': '59.285.411/0001-13',
        'endereco': 'Av. Paulista, nº 1374, Bela Vista, São Paulo/SP, CEP 01310-100',
        'descricao_pj': 'pessoa jurídica de direito privado',
    },
}
