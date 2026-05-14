"""
Popular `contratos_impugnar_ids` nos `_estado_cliente.json` JÁ EXISTENTES,
sem re-rodar a kit-juridico inteira. Aplica a heurística do seletor a cada
JSON encontrado em PASTA_BATCH e regrava com o campo novo + planilha.
"""
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from seletor_contratos import selecionar_para_todas_pastas
from planilha_impugnar import gerar_planilha

PASTA_BATCH = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - ORGANIZAÇÃO PASTA AL\TESTE - Fazer inicial'

def main():
    if not os.path.isdir(PASTA_BATCH):
        print(f'PASTA_BATCH não existe: {PASTA_BATCH}')
        return
    total_pastas = 0
    total_ids = 0
    for nome in sorted(os.listdir(PASTA_BATCH)):
        cli_dir = os.path.join(PASTA_BATCH, nome)
        if not os.path.isdir(cli_dir):
            continue
        json_path = os.path.join(cli_dir, '_estado_cliente.json')
        if not os.path.exists(json_path):
            continue
        with open(json_path, encoding='utf-8') as f:
            d = json.load(f)
        pastas = d.get('pastas_acao') or []
        contratos = d.get('contratos') or []
        cadeias = d.get('cadeias') or []
        if not pastas:
            continue
        pastas_atualizadas, linhas = selecionar_para_todas_pastas(
            pastas, contratos, cadeias, pasta_cliente_abs=cli_dir
        )
        d['pastas_acao'] = pastas_atualizadas
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        # Planilha
        if linhas:
            xlsx_path = os.path.join(cli_dir, '_contratos_a_impugnar.xlsx')
            try:
                gerar_planilha(linhas, xlsx_path)
            except Exception as e:
                print(f'  [WARN] {nome}: planilha falhou: {e}')
        n_ids = sum(len(pa.get('contratos_impugnar_ids') or []) for pa in pastas_atualizadas)
        print(f'{nome:40s}  {len(pastas_atualizadas):2d} pastas  {n_ids:3d} ids  {len(linhas)} linhas planilha')
        total_pastas += len(pastas_atualizadas)
        total_ids += n_ids
    print(f'\nTotal: {total_pastas} pastas_acao, {total_ids} ids sugeridos')


if __name__ == '__main__':
    main()
