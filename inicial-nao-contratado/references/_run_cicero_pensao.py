# -*- coding: utf-8 -*-
"""Gera iniciais CICERO PENSÃO/Itaú + PENSÃO/Mercantil usando helper."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _gerar_inicial_padrao import gerar_inicial_pasta, BANCOS_REUS

# Dados do autor — extraídos antes (procuração + RG + comprovante)
AUTOR_CICERO = {
    'nome':            'JOSÉ EXEMPLO DA SILVA',
    'nacionalidade':   'brasileiro',
    'estado_civil':    'viúvo',
    'profissao':       'aposentado',
    'cpf':             '000.000.006-16',
    'rg':              '1000004-4',
    'orgao_expedidor': 'SSP/AL',
    'logradouro':      'Rua Floriano Leite',
    'numero':          '28',
    'bairro':          'Centro',
    'cidade':          'Lagoa da Canoa',
    'uf':              'AL',
    'cep':             '57330-000',
    'eh_idoso':        True,
}

TEMPLATE_JFAL = Path(r"C:\Users\gabri\OneDrive\Documentos\Obsidian Vault\Modelos\IniciaisNaoContratado\_templates\inicial-jfal-1banco.docx")
PASTA_BASE = Path(r"C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\JOSÉ EXEMPLO DA SILVA - ALEXANDRE-ESCRITÓRIO")

CASOS = [
    {
        'pasta': PASTA_BASE / 'PENSÃO' / 'BANCO ITAÚ',
        'banco_reu': BANCOS_REUS['ITAU_CONSIGNADO'],
        'saida': 'INICIAL_CICERO_PENSAO_ITAU.docx',
    },
    {
        'pasta': PASTA_BASE / 'PENSÃO' / 'MERCANTIL',
        'banco_reu': BANCOS_REUS['MERCANTIL'],
        'saida': 'INICIAL_CICERO_PENSAO_MERCANTIL.docx',
    },
]

for caso in CASOS:
    print(f"\n{'='*70}\n{caso['pasta'].name}\n{'='*70}")
    try:
        out, n, dados = gerar_inicial_pasta(
            pasta_acao=caso['pasta'],
            template=TEMPLATE_JFAL,
            banco_reu=caso['banco_reu'],
            autor=AUTOR_CICERO,
            cidade_protocolo='Arapiraca',
            uf_protocolo='AL',
            eh_federal=True,
            saida_nome=caso['saida'],
        )
        print(f"OK: {out.name} ({n} substituições)")
        print(f"  banco_reu: {dados['{{banco_reu_nome}}']}")
        print(f"  NB: {dados['{{nb_beneficio}}']}")
        print(f"  renda: R$ {dados['{{valor_renda_liquida}}']}")
        print(f"  valor_causa: R$ {dados['{{valor_causa}}']}")
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
