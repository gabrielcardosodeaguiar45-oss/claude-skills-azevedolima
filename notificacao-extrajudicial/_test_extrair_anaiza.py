"""Teste isolado de extração de qualificação na ANAIZA."""
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from extrair_qualificacao import extrair_qualificacao, _extrair_texto_pdf

PASTA = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - ORGANIZAÇÃO PASTA AL\TESTE - Fazer inicial\ANAIZA MARIA DA CONCEIÇÃO\KIT'

# Listar PDFs no KIT
print('PDFs no KIT:')
for n in os.listdir(PASTA):
    if n.lower().endswith('.pdf'):
        print(f'  - {n}')

# Procurar a procuração
procuracao = None
for n in os.listdir(PASTA):
    if 'procura' in n.lower() and n.lower().endswith('.pdf'):
        procuracao = os.path.join(PASTA, n)
        print(f'\nProcuração escolhida: {n}')
        break

if not procuracao:
    print('Nenhuma procuração encontrada')
    sys.exit(1)

# Extrair texto bruto
print('\n--- Extraindo texto (text-layer + OCR fallback) ---')
texto = _extrair_texto_pdf(procuracao, max_pages=3)
print(f'Texto extraído: {len(texto)} chars')
print('\nPrimeiros 2000 chars:')
print(texto[:2000])

# Parsear
qual = extrair_qualificacao(procuracao, max_pages=3)
print('\n--- Qualificação parseada ---')
print(json.dumps({k: v for k, v in qual.items() if k != '_texto_extraido'},
                 indent=2, ensure_ascii=False))
