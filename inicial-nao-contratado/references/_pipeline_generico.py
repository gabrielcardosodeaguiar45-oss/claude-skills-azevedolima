"""Pipeline genérico de alto nível para qualquer perfil de jurisdição.

USO TÍPICO:
    from _pipeline_generico import gerar_inicial_padrao

    res = gerar_inicial_padrao(
        perfil_chave='AL_FEDERAL',           # uma chave de perfis_juridicos.PERFIS
        pasta_cliente='.../EDMUNDA LIMA',
        autora=AUTORA_DICT,
        comarca='Arapiraca',
        numeros_contrato_explicitos=['0123527065102'],
        output_path='.../INICIAL.docx',
    )

O que esse wrapper faz:
  1. Resolve o perfil de jurisdição
  2. Importa dinamicamente o pipeline específico (BA / AM / AL)
  3. Chama as funções `montar_dados_*` e `gerar_inicial_*` adequadas
  4. Aplica as regras COMUNS automaticamente:
     - extração OCR de procuração se nada explícito
     - decisão automática de foro AL (por valor da causa)
     - escolha de template apropriado
     - injeção de helpers_redacao (intro Bold, pedidos, prioridade)

Para adicionar uma nova UF (PE, MG, ES, ...):
  1. Cole um perfil em `perfis_juridicos.PERFIS`
  2. Coloque o template no vault
  3. Use a mesma função `gerar_inicial_padrao('NOVO_PERFIL', ...)`

NÃO precisa criar pipeline novo nem helper novo.
"""
import importlib
import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from perfis_juridicos import get_perfil


def gerar_inicial_padrao(
    perfil_chave: str,
    pasta_cliente: str,
    autora: Dict,
    comarca: str,
    numeros_contrato_explicitos: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    forcar_procurador: Optional[str] = None,
    forcar_foro: Optional[str] = None,
    representante_legal: Optional[Dict] = None,
    assume_com_deposito: bool = False,
    banco_codigo_override: Optional[str] = None,
    # DEPRECATED (Patch B — 2026-05-16): aceitos só para abortar com mensagem clara
    permitir_contrato_virtual: bool = False,
    contrato_virtual_overrides: Optional[Dict] = None,
) -> Dict:
    # Patch B — banir fallbacks fictícios no entrypoint público
    if permitir_contrato_virtual or contrato_virtual_overrides:
        raise RuntimeError(
            '🚨 permitir_contrato_virtual / contrato_virtual_overrides FORAM '
            'BANIDOS em 2026-05-16 (caso paradigma VILSON/BANRISUL — inicial '
            'gerada com R$ 0,00 e cálculo com R$ 50 × 29 meses fictícios). '
            'A skill NÃO aceita mais gerar inicial sem contrato real no HISCON. '
            'AÇÃO: remover esses parâmetros da chamada; conferir o número da '
            'procuração com o cliente/CCB; refazer procuração se necessário; '
            'ou suspender a pasta até esclarecer.'
        )
    """Gera inicial usando o pipeline correto pelo perfil informado.

    Args:
        perfil_chave: chave do perfil em PERFIS (ex.: 'BA_FEDERAL', 'AM_ESTADUAL',
                      'AL_FEDERAL', 'AL_ESTADUAL', ou nova chave que você adicionar).
        pasta_cliente: caminho da pasta com HISCON, procurações, RG, etc.
        autora: dict com qualificação (nome, CPF, RG, endereço, etc.)
        comarca: nome da comarca dentro da UF do perfil.
        numeros_contrato_explicitos: lista de contratos a impugnar. SEMPRE
            recomendado passar — evita o pipeline tentar OCR/falhar/abortar.
        output_path: caminho do DOCX a gerar. Se None, usa
            `{pasta_cliente}/INICIAL_{PERFIL}.docx`.
        forcar_procurador: 'gabriel'/'patrick'/'tiago'/'alexandre'/etc.
            Se None, usa o default do perfil.
        forcar_foro: para AL ('federal'/'estadual'). Se None, usa o do perfil.
        representante_legal: opcional (autor menor de idade — apenas AM por enquanto).
        assume_com_deposito: AL — só True se HISCRE/extrato confirmarem (default False).

    Returns:
        {
            'perfil': str,
            'dados': dict completo do montar_dados,
            'resultado': dict do gerar_inicial,
            'output': str,
        }
    """
    perfil = get_perfil(perfil_chave)

    if output_path is None:
        nome_inicial = f'INICIAL_{perfil_chave}.docx'
        output_path = os.path.join(pasta_cliente, nome_inicial)

    # Resolver pipeline (importação dinâmica)
    modulo = importlib.import_module(perfil['pipeline_modulo'])
    func_montar = getattr(modulo, perfil['pipeline_func_montar'])
    func_gerar = getattr(modulo, perfil['pipeline_func_gerar'])

    # Procurador
    procurador_chave = forcar_procurador or perfil['procurador_chave_default']

    # Argumentos comuns
    kwargs = {
        'autora': autora,
        'numeros_contrato_explicitos': numeros_contrato_explicitos,
    }

    # Argumentos específicos por pipeline
    if perfil['pipeline_modulo'] == '_pipeline_caso':
        # BA: usa subsecao + banco_jurisdicao
        kwargs.update({
            'pasta_banco': pasta_cliente,
            'subsecao': comarca,
            'banco_jurisdicao': perfil.get('pipeline_kwargs_extra', {}).get('banco_jurisdicao', 'matriz'),
        })
    elif perfil['pipeline_modulo'] == '_pipeline_caso_am':
        # AM: usa pasta_banco + comarca + procurador_chave + representante_legal
        kwargs.update({
            'pasta_banco': pasta_cliente,
            'comarca': comarca,
            'procurador_chave': procurador_chave,
            'representante_legal': representante_legal,
            'banco_codigo_override': banco_codigo_override,
        })
    elif perfil['pipeline_modulo'] == '_pipeline_caso_al':
        # AL: usa pasta_cliente + comarca + foro
        # Quando o perfil for de outra UF que reaproveita o pipeline AL (ex.: MG),
        # passa uf_override para o pipeline buscar template/cabeçalho corretos.
        foro_efetivo = forcar_foro or perfil.get('forcar_foro')
        uf_perfil = perfil['uf']
        kwargs.update({
            'pasta_cliente': pasta_cliente,
            'comarca': comarca,
            'forcar_foro': foro_efetivo,
            'forcar_procurador': procurador_chave,
            'assume_com_deposito': assume_com_deposito,
            'uf_override': uf_perfil if uf_perfil != 'AL' else None,
        })
    else:
        raise RuntimeError(
            f'Pipeline {perfil["pipeline_modulo"]!r} desconhecido. '
            f'Adicionar suporte em _pipeline_generico.py.'
        )

    # 1. Montar dados
    dados = func_montar(**kwargs)

    # 2. Gerar DOCX
    resultado = func_gerar(dados, output_path)

    return {
        'perfil': perfil_chave,
        'dados': dados,
        'resultado': resultado,
        'output': output_path,
    }


if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print('=== PIPELINE GENÉRICO ===')
    print('USO: from _pipeline_generico import gerar_inicial_padrao')
    print()
    from perfis_juridicos import listar_perfis
    print(f'Perfis disponíveis: {listar_perfis()}')
