"""
Aplica a revisão humana da planilha _contratos_a_impugnar.xlsx ao
_estado_cliente.json.

Workflow:
  1. Advogado abre _contratos_a_impugnar.xlsx em cada cliente
  2. Marca a coluna `impugnar (S/N)`:
     - S → contrato entra em contratos_impugnar_ids
     - N → contrato fica fora
  3. Salva o XLSX
  4. Roda este script (única pasta ou batch)
  5. JSON é atualizado: contratos_impugnar_ids + contratos_impugnar_origem='sugestao_automatica_revisada'

Uso:
  python _aplicar_revisao.py                  # batch em PASTA_BATCH
  python _aplicar_revisao.py <pasta_cliente>  # cliente único

Trigger: rodar este script ANTES de qualquer skill consumidora
(notificacao-extrajudicial, inicial-*) re-gerar peças. Depois disso, a
hierarquia da skill consumidora vai usar `contratos_impugnar_ids` com
prioridade sobre procurações na pasta_acao (origem revisada vence tudo).
"""
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from planilha_impugnar import ler_planilha

PASTA_BATCH_DEFAULT = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - ORGANIZAÇÃO PASTA AL\TESTE - Fazer inicial'


def aplicar_revisao_cliente(cli_dir: str) -> dict:
    """Aplica revisão de um cliente. Retorna stats."""
    stats = {'cliente': os.path.basename(cli_dir), 'status': '', 'pastas_alteradas': 0,
             'ids_antes': 0, 'ids_depois': 0}

    json_path = os.path.join(cli_dir, '_estado_cliente.json')
    xlsx_path = os.path.join(cli_dir, '_contratos_a_impugnar.xlsx')
    if not os.path.exists(json_path):
        stats['status'] = 'sem_json'
        return stats
    if not os.path.exists(xlsx_path):
        stats['status'] = 'sem_xlsx'
        return stats

    with open(json_path, encoding='utf-8') as f:
        d = json.load(f)
    pastas = d.get('pastas_acao') or []

    # Total antes
    stats['ids_antes'] = sum(len(p.get('contratos_impugnar_ids') or []) for p in pastas)

    # Lê planilha — pasta_acao path → lista de ids marcados S
    revisao = ler_planilha(xlsx_path)
    if not revisao:
        stats['status'] = 'planilha_vazia'
        return stats

    # Aplica — só marca como `revisada` quando houve diff real (S↔N alterado)
    n_alteradas = 0
    for p in pastas:
        path_rel = p.get('path_relativo')
        ids_revisados = revisao.get(path_rel)
        if ids_revisados is None:
            continue
        ids_atuais = p.get('contratos_impugnar_ids') or []
        if set(ids_revisados) != set(ids_atuais):
            n_alteradas += 1
            p['contratos_impugnar_origem'] = 'sugestao_automatica_revisada'
        # Se não houver diff, mantém origem atual (não rebatiza como "revisada"
        # apenas por leitura — preserva a distinção de status real)
        p['contratos_impugnar_ids'] = list(ids_revisados)

    # Total depois
    stats['ids_depois'] = sum(len(p.get('contratos_impugnar_ids') or []) for p in pastas)
    stats['pastas_alteradas'] = n_alteradas

    # Salva JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

    stats['status'] = 'ok'
    return stats


def main():
    if len(sys.argv) > 1:
        # Cliente único
        target = sys.argv[1]
        if os.path.isdir(target):
            r = aplicar_revisao_cliente(target)
            print(json.dumps(r, indent=2, ensure_ascii=False))
            return
        else:
            print(f'Pasta inexistente: {target}')
            sys.exit(1)

    # Batch
    pasta_batch = PASTA_BATCH_DEFAULT
    if not os.path.isdir(pasta_batch):
        print(f'PASTA_BATCH não existe: {pasta_batch}')
        return
    print(f'Aplicando revisão em batch: {pasta_batch}\n')
    print(f'{"Cliente":42s} {"Status":18s} {"Antes→Depois":>14s} {"Pastas alt.":>11s}')
    print('-' * 90)
    total_antes = total_depois = total_alt = 0
    for nome in sorted(os.listdir(pasta_batch)):
        cli_dir = os.path.join(pasta_batch, nome)
        if not os.path.isdir(cli_dir):
            continue
        r = aplicar_revisao_cliente(cli_dir)
        if r['status'] == 'ok':
            antes_depois = f"{r['ids_antes']}→{r['ids_depois']}"
            print(f'{nome:42s} {r["status"]:18s} {antes_depois:>14s} {r["pastas_alteradas"]:>11d}')
            total_antes += r['ids_antes']
            total_depois += r['ids_depois']
            total_alt += r['pastas_alteradas']
        else:
            print(f'{nome:42s} {r["status"]:18s}')
    print(f'\nTOTAL: {total_antes} → {total_depois} ids ({total_alt} pastas alteradas)')


if __name__ == '__main__':
    main()
