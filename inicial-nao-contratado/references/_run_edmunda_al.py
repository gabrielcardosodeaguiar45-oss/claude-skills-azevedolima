"""Roda pipeline AL para JOANA EXEMPLO DOS SANTOS — caso de validação.

Pasta: APP - NÃO CONTRATADO/JOANA EXEMPLO DOS SANTOS
Bancos no HISCON: BANCO BRADESCO (2 contratos AVN ATIVOS)

Sem HISCRE e sem PDF de cálculo (caso ainda não organizado pelo cliente).
Por isso:
  - CPF/RG vêm só do que sabemos (precisará confirmar manualmente)
  - renda_liquida vai ficar vazia → alerta
  - valor_causa será estimado pela skill (soma_dobros + dano_moral)

Resultado esperado:
  - Federal AL (2 contratos × ~R$ 398 × 84 + ~R$ 130 × 25 < R$ 91.080)
  - Template inicial-jfal-1banco.docx (1 banco)
  - Bloco fático: (2 CONTRATOS, ATIVOS COM DEPÓSITOS) — assumindo COM depósito
  - Procurador: Tiago (OAB/AL 20906A)
"""
import io, sys, os
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _pipeline_caso_al import montar_dados_inicial_al, gerar_inicial_al

# Dados extraídos via OCR multimodal em 07/05/2026:
#  - CPF do comprovante CPF físico (Receita Federal)
#  - Endereço, estado civil, BAIRRO real, NÚMERO da PROCURAÇÃO ('Bairro Campo Alegre')
#  - Contrato específico da PROCURAÇÃO: 0123527065102 (apenas 1 — o outro
#    contrato do HISCON, 0123466323825, NÃO foi outorgado)
#  - Data de nascimento do CPF físico → IDADE 60 anos = IDOSA (CPC art. 1.048)
#  - RG físico ilegível (PDF escaneado de baixa qualidade); a procuração diz
#    'documento de identidade RG/CPF' citando só CPF → registrar como PENDENTE
AUTORA_EXEMPLA EDMUNDA = {
    'nome': 'JOANA EXEMPLO DOS SANTOS',
    'nacionalidade': 'brasileira',
    'estado_civil': 'casada',                      # OCR procuração
    'profissao': 'aposentada',
    'cpf': '000.000.007-17',                       # OCR comprovante CPF
    'rg': '1000005-5',                              # OCR zoom RG (2ª via, exp. 17/02/2022)
    'orgao_expedidor': 'SSP/AL',
    'data_nascimento': datetime(1965, 4, 13),      # OCR CPF físico — 60 anos (idosa!)
    'nome_mae': None,
    'logradouro': 'Rua Projetada',                 # OCR fatura/procuração
    'numero': '07',                                # OCR procuração ('nº 07')
    'bairro': 'Campo Alegre',                      # OCR procuração ('Bairro Campo Alegre')
    'cidade': 'Jaramataia',                        # OCR fatura (CEP 57425-000)
    'uf': 'AL',
    'cep': '57425-000',
    'renda_liquida': None,                         # sem HISCRE, virá do BASE_CÁLCULO HISCON
}

# Contrato OUTORGADO na procuração (apenas 1 — o outro contrato do HISCON,
# 0123466323825, NÃO consta na procuração).
NUMEROS_CONTRATO_EXEMPLA EDMUNDA = ['0123527065102']

PASTA = r'C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\JOANA EXEMPLO DOS SANTOS'
DOCX_OUT = os.path.join(PASTA, 'INICIAL_NaoContratado_EXEMPLA EDMUNDA.docx')


def main():
    print('████████████ JOANA EXEMPLO DOS SANTOS × BANCO BRADESCO ████████████')
    if not os.path.isdir(PASTA):
        print(f'❌ Pasta não existe: {PASTA}')
        return

    try:
        dados = montar_dados_inicial_al(
            pasta_cliente=PASTA,
            autora=AUTORA_EXEMPLA EDMUNDA,
            comarca='Arapiraca',
            forcar_foro=None,            # auto pelo valor da causa
            forcar_procurador='tiago',
            assume_com_deposito=False,   # default seguro: SEM DEPÓSITO sem confirmação
            numeros_contrato_explicitos=NUMEROS_CONTRATO_EXEMPLA EDMUNDA,
        )
    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback; traceback.print_exc()
        return

    print(f'  Banco-réu:        {dados["banco_reu"]["nome"]}')
    print(f'  N de bancos:      {dados["n_bancos"]}')
    print(f'  Contratos:        {len(dados["contratos_questionados"])}')
    for c in dados['contratos_questionados']:
        print(f'    {c["numero"]:14} | qtd={c["qtd_parcelas"]:3} | parc=R$ {c["valor_parcela_str"]:>9} '
              f'| {c["competencia_inicio_str"]} → {c["competencia_fim_str"]} | {c["situacao"]}')
    print(f'  Foro decidido:    {dados["foro"].upper()}')
    print(f'                    motivo: {dados["decisao_foro"]["motivo"]}')
    print(f'  Template:         {os.path.basename(dados["template"])}')
    print(f'  Procurador:       {dados["procurador"]["nome"]} ({dados["procurador"]["oab_uf"]})')
    cen = dados['cenario']
    print(f'  Cenário:          {cen["n_contratos"]} contrato(s) | tipos={cen["tipos"]} | situações={cen["situacoes"]}')
    print(f'  Idoso:            {dados["eh_idoso"]}')
    print(f'  Dano moral:       R$ {dados["dano_moral"]["total"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
    print(f'  Valor causa:      R$ {dados["valor_causa"]:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'))
    print(f'                    fonte: {dados["fonte_vc"]}')
    print(f'  Renda líquida:    {dados["renda_liquida"]} (fonte: {dados["fonte_renda"]})')

    if dados.get('alertas'):
        print()
        print('  ALERTAS:')
        for a in dados['alertas']:
            print(f'    {a[:240]}')

    audit_p = dados.get('audit_procuracoes') or {}
    if audit_p.get('alertas'):
        print()
        print('  ALERTAS DE AUDITORIA DE PROCURAÇÕES:')
        for a in audit_p['alertas']:
            print(f'    {a[:240]}')

    if dados.get('divergencias_pessoais'):
        print()
        print('  DIVERGÊNCIAS doc vs HISCRE:')
        for d in dados['divergencias_pessoais']:
            print(f'    [{d["severidade"]}] {d["campo"]}: {d["msg"]}')

    print()
    print('  GERANDO INICIAL...')
    r = gerar_inicial_al(dados, DOCX_OUT)
    print(f'    ✓ DOCX:  {r["output"]}')
    print(f'      modif: {r["modificados"]}')
    print(f'      campos a preencher manualmente no bloco: {r["placeholders_para_preencher_no_bloco"]}')
    if r['placeholders_amostra']:
        print(f'      amostra: {r["placeholders_amostra"]}')


if __name__ == '__main__':
    main()
