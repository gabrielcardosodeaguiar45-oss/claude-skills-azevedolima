# Como adicionar uma nova UF / template

> Tempo estimado: 10 a 30 minutos (dependendo se reaproveita pipeline existente).

A skill `inicial-nao-contratado` foi desenhada para HERDAR todas as regras
(procuração obrigatória, fontes Segoe UI Bold, pedidos empréstimo vs
refinanciamento, prioridade idoso, grifo amarelo, etc.) automaticamente.
Para adicionar uma nova UF/foro NÃO precisa criar pipeline novo nem helper
novo na maioria dos casos.

## Pré-requisitos

- Modelo `.docx` do escritório com dados de caso piloto (FULANO DE TAL, etc.)
- Conhecimento da OAB do procurador local (se for novo)
- Saber se inclui INSS no polo passivo (Federal sim / Estadual não)

## 5 PASSOS

### 1. Copie o template para o vault

```bash
cp seu-modelo.docx \
   "C:/Users/gabri/OneDrive/Documentos/Obsidian Vault/Modelos/IniciaisNaoContratado/_templates/inicial-jfpe-base.docx"
```

Convenção de nome: `inicial-{j[ef|e]}{uf}-{cenario}.docx`
- `jf` = Justiça Federal | `je` = Justiça Estadual
- `cenario` = `base` / `1banco` / `2bancos` / `multiplos` / `refin`

### 2. Valide o template (checklist automático)

```bash
cd C:/Users/gabri/.claude/skills/inicial-nao-contratado/references
python validar_template.py inicial-jfpe-base.docx
```

Resolva os 🚨 que aparecerem. ⚠ recomendados podem ser tolerados.

A checklist verifica:
- Cabeçalho "Ao Juízo..."
- Qualificação do autor (placeholder ou nome piloto)
- Polo passivo "em face de"
- Síntese fática "recebe benefício previdenciário"
- Intro "tomou conhecimento" ou "constatou a existência"
- Bloco fático "No que diz respeito"
- DOS PEDIDOS + Declarar a inexistência + danos morais
- Valor da causa "Dá-se a causa"
- Assinatura do procurador + OAB

### 3. Cadastre o procurador (se novo) em `escritorios.py`

Adicione ao dict `PROCURADORES`:

```python
'novo_procurador': {
    'nome': 'Nome Completo',
    'oab': 'OAB/PE 12345',  # principal
    'oabs_por_uf': {'PE': 'OAB/PE 12345', 'BA': 'OAB/BA 80000'},
    'jurisdicoes': ['PE'],
    'enderecos_escritorio': [_e('Recife/PE')],  # adicionar a filial em ENDERECOS_FILIAIS
    'endereco_por_uf': {'PE': _e('Recife/PE')},
},
```

E adicione a regra de protocolo em `PROTOCOLA_POR_UF`:

```python
PROTOCOLA_POR_UF = {
    ...
    'PE': 'novo_procurador',
}
```

### 4. Cadastre o perfil de jurisdição em `perfis_juridicos.py`

```python
PERFIS = {
    ...
    'PE_FEDERAL': {
        'uf': 'PE',
        'foro': 'federal',
        'inclui_inss': True,
        'procurador_chave_default': 'novo_procurador',
        'comarcas_validas': ['Recife', 'Olinda', 'Jaboatão dos Guararapes'],
        'templates_por_cenario': {
            '1contrato': 'inicial-jfpe-base.docx',
            'multiplos': 'inicial-jfpe-multiplos.docx',
        },
        'end_inss_polo_passivo': 'Av. ..., Recife/PE',
        'cabecalho_template': 'Ao Juízo do Juizado Especial Federal Subseção de {comarca}/PE',
        'convencao_placeholders': 'BA',  # ou 'AM' — depende do template
        'pipeline_modulo': '_pipeline_caso',     # reaproveita BA
        'pipeline_func_montar': 'montar_dados_inicial',
        'pipeline_func_gerar': 'gerar_inicial',
        'pipeline_kwargs_extra': {'subsecao': 'Recife', 'banco_jurisdicao': 'matriz'},
    },
}
```

**Decisão importante:** qual pipeline reaproveitar?
- Se o template usa convenção BA (`{{nome_autor}}, {{cpf_autor}}, ...`) e estrutura
  similar → `_pipeline_caso`
- Se usa convenção AM (`{{nome_completo}}, {{cpf}}, {{quali_banco}}`) → `_pipeline_caso_am`
- Se usa estrutura genérica (Opção B do AL) → `_pipeline_caso_al`

### 5. Crie o runner do caso

Copie `_run_caso_padrao.py` como `_run_<nome_cliente>.py` e preencha o dict
`CASO`. Rode:

```bash
python _run_<nome_cliente>.py
```

A skill **HERDA AUTOMATICAMENTE** todas as regras gravadas (procuração
obrigatória, fontes, pedidos, prioridade idoso, grifo amarelo, etc.).

## Quando preciso CRIAR pipeline novo?

Apenas quando o template tem estrutura **fundamentalmente diferente** dos 3
pipelines existentes — por exemplo:
- Estrutura totalmente diferente (não tem polo passivo, ou tem 5 réus, etc.)
- Necessidade de blocos custom (ex.: TJSC tem hipótese específica de tutela
  antecipada que precisa parágrafo dedicado)
- Convenção de placeholders incompatível com BA/AM/AL

Nesses casos:
1. Copie `_pipeline_caso_al.py` como `_pipeline_caso_<uf>.py`
2. Adapte as funções específicas (cabeçalho, qualificação, polo passivo)
3. **MANTENHA** os imports de `helpers_redacao` e `extrator_procuracao`
4. **MANTENHA** a classe `ProcuracaoSemFiltroError` e o helper `extrair_numeros_contrato_de_pasta`
5. Cadastre no perfil: `'pipeline_modulo': '_pipeline_caso_pe', ...`

## Checklist final antes de protocolar

- [ ] `python validar_template.py <novo_template>` → ✅ sem críticos faltando
- [ ] `python escritorios.py` → procurador novo aparece com endereço/OAB corretos
- [ ] `python perfis_juridicos.py` → perfil novo aparece na lista
- [ ] `python _run_<cliente>.py` → roda sem erro, gera DOCX
- [ ] Abrir o DOCX gerado:
  - Cabeçalho com comarca correta
  - Nome do autor em Segoe UI Bold + amarelo
  - Polo passivo (banco + INSS) com nomes em Segoe UI Bold + amarelo
  - Intro "...junto ao **BANCO X**, **CONTRATO Nº ...**:" em Bold
  - Bloco fático com valores reais (sem `xxxxxxxx`)
  - Pedido declaratório com "empréstimo" ou "refinanciamento" (não a barra)
  - Prioridade idoso só se autor ≥ 60 anos
  - Valor da causa preenchido
  - Cidade + data atualizada
  - Assinatura do procurador correto

## Exemplos de adições passadas

| UF | Foro | Pipeline | Tempo gasto na 1ª vez |
|---|---|---|---|
| BA | Federal | `_pipeline_caso.py` | ~3 dias (1ª vez — sem helpers) |
| AM | Estadual | `_pipeline_caso_am.py` | ~1 dia (com adaptador AM) |
| AL | Federal/Estadual | `_pipeline_caso_al.py` | ~3 dias (Opção B simplificada) |
| **PE/MG/SE** *(futuro)* | qualquer | reaproveitar BA ou AL | **30 minutos** ✨ |

A redução de tempo é o resultado direto dos 5 mecanismos:
1. `perfis_juridicos.py` — 1 dict por UF
2. `_pipeline_generico.py` — 1 wrapper para tudo
3. `validar_template.py` — alerta o que falta
4. `_run_caso_padrao.py` — 30s pra criar runner
5. `GUIA_NOVA_UF.md` — passo-a-passo
