"""
CLI da skill analise-cadeias-hiscon.

Uso:
  python analisar.py <caminho_hiscon.pdf> [--saida saida.docx] [--json dados.json]

Lê o PDF HISCON, monta as cadeias, detecta red flags, gera DOCX detalhado
(e opcionalmente um JSON com os dados brutos para pós-análise).
"""
import argparse, json, sys, pathlib, os
from datetime import datetime, date

# Garantir que o módulo na mesma pasta seja importável independente do CWD
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from analisador import analisar_hiscon
from gerador_docx import gerar_docx

def _json_default(o):
    if isinstance(o, (datetime, date)): return o.isoformat()
    raise TypeError(f'Não serializável: {type(o)}')

def main():
    ap = argparse.ArgumentParser(description='Análise de Cadeias HISCON do INSS')
    ap.add_argument('pdf', help='Caminho do PDF HISCON')
    ap.add_argument('--saida', '-o', default=None, help='Caminho do DOCX de saída (padrão: mesma pasta do PDF)')
    ap.add_argument('--json', dest='json_path', default=None, help='Opcional: caminho para salvar JSON com dados brutos')
    ap.add_argument('--quieto', action='store_true', help='Silencia output no terminal')
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')

    pdf = pathlib.Path(args.pdf)
    if not pdf.exists():
        print(f'ERRO: arquivo não encontrado: {pdf}', file=sys.stderr)
        return 1

    if not args.quieto:
        print(f'Processando {pdf.name}...')

    resultado = analisar_hiscon(str(pdf))

    saida = args.saida
    if not saida:
        nome_base = pdf.stem
        # Tentar usar o nome do beneficiário para um nome mais significativo
        benef = (resultado['beneficiario'].get('nome') or '').strip()
        if benef:
            nome_cliente = benef.split()[0].capitalize() if benef else 'cliente'
            saida = str(pdf.parent / f'Analise_Cadeias_{nome_cliente}.docx')
        else:
            saida = str(pdf.parent / f'Analise_Cadeias_{nome_base}.docx')

    gerar_docx(resultado, destino=saida)

    if args.json_path:
        with open(args.json_path, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2, default=_json_default)

    e = resultado['estatisticas']
    if not args.quieto:
        print(f'\n✓ DOCX gerado: {saida}')
        print(f'\nBeneficiário : {resultado["beneficiario"].get("nome","?")}')
        print(f'Benefício    : {resultado["beneficiario"].get("beneficio","?")}')
        print(f'Banco pagador: {resultado["beneficiario"].get("banco_pagador","?")[:60]}')
        print(f'\nContratos    : {e["total_contratos"]}')
        print(f'Cadeias      : {e["total_cadeias"]} ({e["cadeias_multi"]} multi + {e["cadeias_isoladas"]} isoladas)')
        print(f'Ativos hoje  : {e["contratos_ativos"]}')
        print(f'Ligações     : {e["ligacoes_total"]} ({e["ligacoes_alta"]} alta, {e["ligacoes_media"]} média, {e["ligacoes_baixa"]} baixa)')
        print(f'Red flags    : {e["red_flags_total"]}')
        print(f'Avisos       : {e["avisos_total"]}')
        print(f'Problemas    : {e["problemas_total"]}')
        if args.json_path:
            print(f'\n✓ JSON salvo: {args.json_path}')
    else:
        print(saida)  # para pipelines

    return 0

if __name__ == '__main__':
    sys.exit(main())
