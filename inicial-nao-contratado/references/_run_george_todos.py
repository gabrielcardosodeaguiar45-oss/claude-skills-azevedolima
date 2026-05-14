"""Processa os 4 bancos do EXEMPLO GEORGE DA SILVA SOUZA em sequência:
- ITAÚ (5 contratos misto AVN+REFIN, todos excluídos)
- FACTA (3 contratos AVN, encerrados)
- AGIBANK (2 contratos REFINANCIAMENTO ATIVO, hoje refinanciados)
- PAN (2 contratos AVN, excluídos)

Caso paradigma para validar a Alternativa 3 do seletor de templates.
"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso import montar_dados_inicial, gerar_inicial, gerar_relatorio_paralelo

# === DADOS COMUNS DA AUTORA (mesmo cliente em todos os bancos) ===
# Hierarquia (SKILL.md §9-bis): doc físico > HISCRE > erro
# Aqui passamos TUDO que conseguimos ler do RG/CPF físico — a skill compara
# com HISCRE e alerta divergências. Se um campo não puder ser lido do doc,
# deixar como None — a skill puxa do HISCRE com alerta "subsidiário".
from datetime import datetime
AUTORA = {
    'nome': 'EXEMPLO GEORGE DA SILVA SOUZA',
    'nacionalidade': 'brasileiro',
    'estado_civil': 'solteiro',
    'profissao': 'aposentado',
    # CPF + RG lidos do RG físico (3 - RG.pdf, escaneado, OCR via Read multimodal)
    'cpf': '000.000.009-19',
    'rg': '1000007-7',
    'orgao_expedidor': 'SSP/BA',
    # Dados extras do RG físico para a verificação cruzada vs HISCRE
    'data_nascimento': datetime(1966, 10, 11),
    'nome_mae': 'ELIETA DA SILVA SOUZA',
    # Endereço (do contrato + autodeclaração — ainda manuscrito)
    'logradouro': 'Travessa Fernando Tul',  # CONFIRMAR (manuscrito do contrato)
    'numero': '54',
    'bairro': 'Santo Pedro',                # CONFIRMAR (manuscrito do contrato)
    'cidade': 'Camaçari',
    'uf': 'BA',
    'cep': '42.800-149',
    'renda_liquida': None,                  # ← preenchido pelo HISCRE
}

BASE_EXEMPLO GEORGE = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\EXEMPLO GEORGE DA SILVA SOUZA - Marcio Teixeira'

CASOS = [
    {
        'banco': 'ITAU',
        'pasta': os.path.join(BASE_EXEMPLO GEORGE, r'BANCO ITAÚ\2 AVERBAÇÃO NOVA INATIVO'),
        'docx_out': 'INICIAL_NaoContratado_EXEMPLO GEORGE_ITAU.docx',
        'relat_out': '_RELATORIO_PENDENCIAS_EXEMPLO GEORGE_ITAU.docx',
    },
    {
        'banco': 'FACTA',
        'pasta': os.path.join(BASE_EXEMPLO GEORGE, r'BANCO FACTA\1 AVERBAÇÃO NOVA INATIVO'),
        'docx_out': 'INICIAL_NaoContratado_EXEMPLO GEORGE_FACTA.docx',
        'relat_out': '_RELATORIO_PENDENCIAS_EXEMPLO GEORGE_FACTA.docx',
    },
    {
        'banco': 'AGIBANK',
        'pasta': os.path.join(BASE_EXEMPLO GEORGE, r'BANCO AGIBANK\1 REFINANCIAMENTO INATIVO'),
        'docx_out': 'INICIAL_NaoContratado_EXEMPLO GEORGE_AGIBANK.docx',
        'relat_out': '_RELATORIO_PENDENCIAS_EXEMPLO GEORGE_AGIBANK.docx',
    },
    {
        'banco': 'PAN',
        'pasta': os.path.join(BASE_EXEMPLO GEORGE, r'BANCO PAN\1 AVERBAÇÃO NOVA INATIVO'),
        'docx_out': 'INICIAL_NaoContratado_EXEMPLO GEORGE_PAN.docx',
        'relat_out': '_RELATORIO_PENDENCIAS_EXEMPLO GEORGE_PAN.docx',
    },
]


def processar_caso(caso):
    print(f'\n████████████ {caso["banco"]} ████████████')
    pasta = caso['pasta']
    if not os.path.isdir(pasta):
        print(f'  ❌ Pasta não existe: {pasta}')
        return None
    try:
        dados = montar_dados_inicial(pasta, AUTORA, subsecao='Salvador', banco_jurisdicao='matriz')
    except Exception as e:
        print(f'  ❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return None

    print(f'  Procurações: {len(dados["numeros_procuracoes"])}')
    print(f'  Contratos no HISCON: {len(dados["contratos_questionados"])}')
    print(f'  Banco-réu: {dados["banco_reu"]["nome"]}')
    print(f'  Template: {os.path.basename(dados["template"])}')
    print(f'  Dano moral (regra): R$ {dados["dano_moral"]["total"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
    print(f'  Dano moral (PDF):   {dados["calculo"]["dano_moral_pleiteado_pdf"]}')
    print(f'  VC: R$ {dados["calculo"]["valor_total_geral"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
    print(f'  Idoso: {dados["eh_idoso"]}')
    if dados['audit_dm']['divergencia']:
        print(f'  ⚠ {dados["audit_dm"]["alerta"][:200]}')
    if dados['alertas_seletor']:
        for a in dados['alertas_seletor']:
            print(f'  ⚠ {a[:200]}')
    div = dados.get('divergencias_pessoais', [])
    if div:
        print(f'  🚨 DIVERGÊNCIAS DOC vs HISCRE: {len(div)}')
        for d in div:
            print(f'     [{d["severidade"]}] {d["campo"]}: doc={d["doc"]} vs hiscre={d["hiscre"]}')
    else:
        print(f'  ✓ Doc físico bate com HISCRE (sem divergências)')

    # Gerar arquivos
    output_docx = os.path.join(pasta, caso['docx_out'])
    output_relat = os.path.join(pasta, caso['relat_out'])
    res = gerar_inicial(dados, output_docx)
    print(f'  ✓ Inicial: {res["modificados"]} subs, residuais: {res["residuais"] or "nenhum"}')
    gerar_relatorio_paralelo(dados, output_relat)
    print(f'  ✓ Relatório: {os.path.basename(output_relat)}')
    return {
        'banco': caso['banco'],
        'docx': output_docx,
        'relat': output_relat,
        'n_contratos': len(dados['contratos_questionados']),
        'vc': dados['calculo']['valor_total_geral'],
        'dm': dados['dano_moral']['total'],
        'template': os.path.basename(dados['template']),
        'alertas': dados['alertas_seletor'] + ([dados['audit_dm']['alerta']] if dados['audit_dm']['divergencia'] else []),
    }


if __name__ == '__main__':
    print(f'=== Cliente: {AUTORA["nome"]} ===\n')
    resultados = []
    for caso in CASOS:
        r = processar_caso(caso)
        if r:
            resultados.append(r)

    # Resumo
    print('\n\n████ RESUMO FINAL ████\n')
    print(f'{"Banco":10s} | {"Contratos":3s} | {"VC":>15s} | {"DM":>12s} | {"Template":40s} | Alertas')
    print('-' * 130)
    for r in resultados:
        vc_str = f'R$ {r["vc"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.')
        dm_str = f'R$ {r["dm"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.')
        print(f'{r["banco"]:10s} | {r["n_contratos"]:9d} | {vc_str:>15s} | {dm_str:>12s} | {r["template"]:40s} | {len(r["alertas"])}')

    print(f'\n✅ {len(resultados)} iniciais geradas em: {BASE_EXEMPLO GEORGE}')
