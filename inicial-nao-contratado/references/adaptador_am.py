"""Adaptador BA→AM: traduz placeholders dos templates AM (do escritório de
Patrick) a partir dos dados extraídos pelo pipeline (que segue convenção BA).

Os templates AM têm naming diferente:
  BA: {{nome_autor}}, {{cpf_autor}}, {{rg_autor}}, ...
  AM: {{nome_completo}}, {{cpf}}, {{rg}}, ...

Além disso, AM:
- NÃO tem INSS no polo passivo
- Usa 1 placeholder consolidado {{quali_banco}} em vez de 4 separados
- Tem campo combinado {{conta_agencia_conta}} em vez de agencia + conta separados
- Tem placeholder {{data_da_inclusão}} (com til!) em vez de {{contrato_data_inclusao}}

Ver placeholders-template.md (vault) para tabela completa de mapeamento.
"""
from typing import Dict, Optional
from datetime import datetime, date


QUALI_BANCO_SEP = '¤¤¤'  # ¤¤¤ — separador único usado para quebrar em 2 runs no pós-processamento


def classificar_menor(data_nascimento, ref: Optional[date] = None) -> Dict:
    """Classifica o menor pela idade segundo o Código Civil:
    - < 16 anos → IMPÚBERE → REPRESENTADO pelo genitor (CC arts. 3º + 1.690)
    - 16–18 anos → PÚBERE → ASSISTIDO pelo genitor (CC arts. 4º + 1.690)

    Args:
        data_nascimento: datetime ou date.
        ref: data de referência (default = hoje).

    Returns:
        dict: {
            'idade_anos': int,
            'classe': 'impúbere' | 'púbere' | 'maior',
            'tratamento': 'representada' | 'assistida' | None,
            'verbo_repr': 'representada por sua genitora' | 'assistida por sua genitora' | None,
        }

    Concorda no FEMININO porque a maioria dos casos do escritório é menor F,
    mas idealmente o gênero deveria vir do dado da autora. (TODO: gênero.)
    """
    if isinstance(data_nascimento, datetime):
        data_nascimento = data_nascimento.date()
    if ref is None:
        ref = date.today()
    idade = ref.year - data_nascimento.year - (
        (ref.month, ref.day) < (data_nascimento.month, data_nascimento.day)
    )
    if idade < 16:
        return {
            'idade_anos': idade,
            'classe': 'impúbere',
            'tratamento': 'representada',
            'verbo_repr': 'representada por sua genitora',
        }
    if idade < 18:
        return {
            'idade_anos': idade,
            'classe': 'púbere',
            'tratamento': 'assistida',
            'verbo_repr': 'assistida por sua genitora',
        }
    return {'idade_anos': idade, 'classe': 'maior', 'tratamento': None, 'verbo_repr': None}


def montar_qualificacao_menor(autora: Dict, representante: Dict, data_nascimento) -> str:
    """Gera a qualificação completa do parágrafo de qualificação para autor
    MENOR (impúbere ou púbere) já com a representação/assistência da genitora.

    Exemplo (PAOLA, 5 anos, impúbere):
        "PAOLA MAITÊ RODRIGUES DE CASTRO, brasileira, menor impúbere, beneficiária,
         inscrita no CPF sob o nº 095.239.132-55, neste ato representada por sua
         genitora NAYEZA BRAGA RODRIGUES, brasileira, solteira, beneficiária do
         INSS, inscrita no CPF sob o nº 031.113.782-25, Cédula de Identidade nº
         2.943.060-7, órgão expedidor SSP/AM, residente e domiciliada na Rua
         Emanoel Mafra, nº 312, bairro Centro, Boa Vista do Ramos/AM, CEP
         69.220-134"

    O CHAMADOR é responsável por concatenar com o restante do parágrafo
    (".. requer a presente AÇÃO DECLARATÓRIA..."). Esta função devolve só a
    qualificação até o CEP.

    Args:
        autora: dict com nome, nacionalidade, profissão (geralmente 'beneficiária'),
                cpf, logradouro, numero, bairro, cidade, uf, cep
        representante: dict do genitor com nome, nacionalidade, estado_civil,
                       profissao, cpf, rg, orgao_expedidor
        data_nascimento: datetime/date da autora — usado para classificar
                         impúbere vs púbere e escolher 'representada'/'assistida'

    Returns:
        string única (sem quebras), pronta para ser inserida no parágrafo.
    """
    cls = classificar_menor(data_nascimento)
    estado_menor = f'menor {cls["classe"]}'  # "menor impúbere" ou "menor púbere"
    verbo = cls['verbo_repr'] or 'representada por sua genitora'
    profissao_aut = autora.get('profissao') or 'beneficiária'

    rep = representante
    rep_nac = rep.get('nacionalidade', 'brasileira')
    rep_ec = rep.get('estado_civil', '')
    rep_prof = rep.get('profissao', '')
    rep_cpf = rep['cpf']
    rep_rg = rep['rg']
    rep_orgao = rep.get('orgao_expedidor', 'SSP/AM')

    quali_rep_partes = [rep['nome'], rep_nac]
    if rep_ec:
        quali_rep_partes.append(rep_ec)
    if rep_prof:
        quali_rep_partes.append(rep_prof)
    quali_rep_partes.append(f'inscrita no CPF sob o nº {rep_cpf}')
    quali_rep_partes.append(f'Cédula de Identidade nº {rep_rg}, órgão expedidor {rep_orgao}')
    quali_rep = ', '.join(quali_rep_partes)

    endereco = (
        f'residente e domiciliada na {autora["logradouro"]}'
        f', nº {autora.get("numero", "s/nº")}'
        f', bairro {autora.get("bairro", "")}'
        f', {autora.get("cidade", "")}/{autora.get("uf", "AM")}'
        f', CEP {autora.get("cep", "")}'
    )

    return (
        f'{autora["nome"]}, {autora.get("nacionalidade", "brasileira")}, '
        f'{estado_menor}, {profissao_aut}, '
        f'inscrita no CPF sob o nº {autora["cpf"]}, '
        f'neste ato {verbo} {quali_rep}, {endereco}'
    )


def montar_quali_banco(banco_reu: Dict) -> str:
    """Monta a string consolidada da qualificação do banco para o
    placeholder {{quali_banco}} do template AM.

    Usa o SEPARADOR `¤¤¤` para que o pós-processamento consiga DIVIDIR a
    string em 2 runs distintos: nome do banco (Segoe UI Bold) e resto (Cambria).

    Ex.: 'BANCO C6 CONSIGNADO S.A.¤¤¤, pessoa jurídica de direito privado,
    inscrita no CNPJ/MF sob o nº 61.348.538/0001-86, com endereço na Av. Nove
    de Julho, nº 3148, Jardim Paulista, São Paulo/SP, CEP 01.406-000'
    """
    return (f'{banco_reu["nome"]}{QUALI_BANCO_SEP}'
            f', {banco_reu["descricao_pj"]}, '
            f'inscrita no CNPJ/MF sob o nº {banco_reu["cnpj"]}, '
            f'com endereço na {banco_reu["endereco"]}')


def adaptar_dados_para_am(dados_ba: Dict, hiscre: Dict, autora: Dict,
                          contrato: Dict, banco_reu: Dict, comarca_am: str,
                          procurador: Dict, valor_causa: float,
                          valor_causa_extenso: str,
                          representante_legal: Dict = None) -> Dict:
    """Converte os dados (no formato dos placeholders BA) para o formato
    dos placeholders AM.

    Args:
        dados_ba: dict de dados_template do pipeline BA
        hiscre: dict do parse_hiscre
        autora: dict da AUTORA (do KIT/RG)
        contrato: dict do PRIMEIRO contrato formatado para template (AM = 1 contrato)
        banco_reu: dict do resolver_banco
        comarca_am: cidade da comarca AM (ex.: 'Boa Vista do Ramos')
        procurador: dict do procurador
        valor_causa: float
        valor_causa_extenso: str
        representante_legal: dict opcional (quando autor menor) com chaves
                             nome, nacionalidade, estado_civil, profissao,
                             cpf, rg, orgao_expedidor, endereco completo

    Returns:
        dict com placeholders no formato AM
    """
    # Combinar agência+conta no formato AM
    ag = dados_ba.get('{{agencia_pagador}}', '')
    cc = dados_ba.get('{{conta_pagador}}', '')
    conta_agencia_conta = f'agência {ag}, conta corrente nº {cc}' if ag or cc else ''

    # Qualificação consolidada do banco
    quali_banco = montar_quali_banco(banco_reu)

    # Banco que averbou (referência curta no bloco fático)
    banco_que_averbou_str = banco_reu['nome']

    # Data inclusão (formato dd/mm/aaaa)
    data_inclusao = contrato.get('data_inclusao_str', '')

    # Para representante legal (PAOLA): construir prefixo de qualificação
    if representante_legal:
        # Formato: "PAOLA MAITE..., menor, neste ato representada por sua genitora
        # NAYEZA BRAGA RODRIGUES, brasileira, ..."
        rep = representante_legal
        prefixo_rep = (
            f'menor de idade, neste ato representada por sua genitora '
            f'{rep["nome"]}, {rep.get("nacionalidade", "brasileira")}, '
            f'{rep.get("estado_civil", "")}, {rep.get("profissao", "")}, '
            f'inscrita no CPF sob o nº {rep["cpf"]}, '
            f'Cédula de Identidade nº {rep["rg"]}, órgão expedidor {rep.get("orgao_expedidor", "SSP/AM")}, '
            f'residente e domiciliada no mesmo endereço'
        )
    else:
        prefixo_rep = None

    out = {
        # Cabeçalho
        '{{competencia}}': comarca_am,
        # Autor
        '{{nome_completo}}': autora['nome'],
        '{{nacionalidade}}': autora.get('nacionalidade', 'brasileiro'),
        '{{estado_civil}}': autora.get('estado_civil', ''),
        '{{profissao}}': autora.get('profissao', ''),
        '{{cpf}}': dados_ba.get('{{cpf_autor}}', ''),
        '{{rg}}': autora.get('rg', ''),
        '{{orgao_expedidor}}': autora.get('orgao_expedidor', 'SSP/AM'),
        '{{logradouro}}': autora.get('logradouro', ''),
        '{{numero}}': autora.get('numero', ''),
        '{{bairro}}': autora.get('bairro', ''),
        '{{cidade_de_residencia}}': autora.get('cidade', ''),
        '{{uf}}': autora.get('uf', 'AM'),
        '{{cep}}': autora.get('cep', ''),
        # Banco-réu (consolidado)
        '{{quali_banco}}': quali_banco,
        '{{banco_que_averbou}}': banco_que_averbou_str,
        # Benefício
        '{{tipo_de_beneficio}}': (hiscre.get('especie_descricao') or '').lower(),
        '{{numero_do_beneficio}}': hiscre.get('nb_beneficio') or '',
        '{{conta_agencia_conta}}': conta_agencia_conta,
        '{{banco_que_recebe}}': dados_ba.get('{{banco_pagador}}', ''),
        # Renda
        '{{valor_liquido_beneficio}}': dados_ba.get('{{valor_renda_liquida}}', ''),
        # Contrato (1 só — AM ainda não tem MULT)
        '{{numero_do_contrato}}': contrato.get('numero', ''),
        '{{data_do_primeiro_desconto}}': contrato.get('competencia_inicio_str', ''),
        '{{total_de_parcelas}}': str(contrato.get('qtd_parcelas') or ''),
        '{{valor_da_parcela}}': contrato.get('valor_parcela_str', ''),
        '{{valor_emprestado_do_emprestimo}}': contrato.get('valor_emprestado_str', ''),
        '{{data_da_inclusão}}': data_inclusao,
        # Valor causa
        '{{valor_final_da_causa}}': f'{valor_causa:,.2f}'.replace(',', '#').replace('.', ',').replace('#', '.'),
        '{{valor_final_da_causa_por_extenso}}': valor_causa_extenso,
    }

    # Procurador (se diferente do default Patrick) — substituir no rodapé do template
    out['_procurador_nome'] = procurador['nome']
    out['_procurador_oab'] = procurador['oab']
    out['_representante_legal'] = representante_legal  # para inclusão na qualificação

    return out
