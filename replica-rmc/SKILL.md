---
name: replica-rmc
description: Gera réplica à contestação em ações de RMC/RCC (Reserva de Margem Consignável / Cartão Consignado) de forma autônoma. Use quando o usuário pedir réplica de RMC, réplica de RCC, réplica de cartão consignado, réplica bancária sobre margem consignável, ou quando jogar pasta de processo RMC/RCC para análise. Não usar para apelações (existe skill separada).
---

# Skill — replica-rmc

Orquestra a produção autônoma de **réplica à contestação** em ações de RMC/RCC, cobrindo AM/AL/BA/MG. Escopo restrito — réplica. Apelação, inicial ou cumprimento não entram aqui.

## Quando sou invocada

1. Usuário diz "faz a réplica RMC", "gera réplica RCC", "réplica do consignado", "joga a réplica desse processo".
2. Usuário envia pasta/PDF de processo RMC ou RCC e pede peça.
3. Slash command `/replica-rmc <pasta-do-processo>` é disparado.

## Entrada obrigatória

Caminho para **pasta de processo** contendo pelo menos:

1. PDF consolidado do processo (eproc/PJE), OU
2. Pasta já fatiada com inicial + contestação + anexos (`fatiar-processo` prévia).

Se apenas o PDF consolidado estiver presente, a skill roda `fatiar-processo` automaticamente antes de prosseguir.

## Fluxo autônomo — NÃO pedir confirmação ao usuário

```
/replica-rmc <pasta>
      │
      ├─ (0) fatiar-processo se necessário (PDF consolidado vira pasta fatiada)
      │
      ├─ (0.5) extract_facts.py — CAMADA DETERMINÍSTICA
      │        Varre PDFs com regex calibradas e produz _facts.json
      │        com CPFs, CNJs, OABs, datas, valores R$, IPs, hashes,
      │        bancos mencionados, marcadores temáticos (HISCON, TED,
      │        contestação, fatura, etc.) e headers em caixa alta.
      │        Cada fato vem com (arquivo, página, contexto).
      │        Fonte de verdade que ancora etapas 1 e 4.
      │
      ├─ (1) analisador-processo-rmc
      │        CONSOME _facts.json (não re-extrai). Extrai _analise.json
      │        (autor, processo, banco, contratos, anexos, TEDs, faturas,
      │        laudo digital, RCC gêmeo, observações_caso, bloqueadores).
      │        Cada dado pontual ancorado em _facts.json. Trecho literal
      │        OBRIGATÓRIO em cada tese do banco. Preenche _meta.fontes_facts.
      │
      ├─ (1.5) Checagem de bloqueadores
      │        Se houver bloqueador ALTA, pipeline para. Apresenta ao usuário
      │        antes de redigir. Sem confirmação não segue.
      │
      ├─ (2) consultor-vault-rmc
      │        Aplica 16 regras de adaptação. Gera DOIS arquivos:
      │        . _plano.json (modelo-base + teses + precedentes + alertas)
      │        . _contrato_rebate.json (cobertura 100%: cada tese do banco
      │          com seção dedicada, fundamentos, criticidade, min_paragrafos)
      │
      ├─ (3) redator-replica-rmc
      │        Gera .docx Cambria seguindo estrutura espelhada à contestação
      │        (preliminares antes do mérito) com densidade dos parágrafos do
      │        modelo do escritório. Zero travessão como aposto. Frases-modelo
      │        injetadas com dados reais do caso. Autovalidação 11 itens
      │        antes de devolver.
      │
      ├─ (4) revisor-replica-rmc
      │        Roda validate_against_facts.py (cada CPF, CNJ, valor,
      │        data, IP, hash da réplica precisa estar em _facts.json;
      │        cada citação literal entre aspas precisa existir no
      │        texto do PDF). Checklist + 29 erros + scripts.
      │        Cobertura métrica explícita. Severidade graduada
      │        (CRÍTICO / MÉDIO / COSMÉTICO). Word Comments embutidos
      │        no .docx, sem relatório paralelo.
      │
      ├─ (5) Se AJUSTES NECESSÁRIOS, volta a (3) com feedback; máx 2 iterações.
      │
      └─ (6) Entrega:
              . .docx da réplica com Word Comments do revisor
              . Ficha de aprendizado pré-preenchida em
                vault/Aprendizado/ReplicasRMC/YYYY-MM-DD-cliente-processo.md
```

## Orquestração — instruções precisas

### Etapa 0 — Normalização da entrada

1. Verificar se a pasta contém PDFs já fatiados (arquivos separados tipo `01-inicial.pdf`, `02-contestacao.pdf`) ou um PDF consolidado.
2. Se consolidado: invocar a skill `fatiar-processo` primeiro.
3. Confirmar existência mínima: inicial + contestação. Se faltar qualquer, interromper e reportar.

### Etapa 0.5 — Extração determinística de fatos (`_facts.json`)

Antes de qualquer subagent rodar, executar o extractor determinístico:

```bash
python ~/.claude/skills/replica-rmc/scripts/extract_facts.py "{{PASTA}}"
```

Saída obrigatória: `{{PASTA}}/_facts.json` com:

1. CPFs, CNPJs, CNJs, OABs, datas, valores R$, IPs, hashes, e-mails, telefones, CEPs (cada item com arquivo, página e contexto).
2. Bancos canônicos mencionados (BMG, Santander, Bradesco, Pan, Daycoval, Olé, Parati, Safra, Mercantil, etc.).
3. Marcadores temáticos (HISCON, HISCRE, CCB, TED, fatura, RMC, RCC, ICP-Brasil, Clicksign, biometria, IN 28/2008, Resolução CNJ 159, litigância predatória, etc.) com mapa de páginas por arquivo.
4. Headers em caixa alta (candidatos a títulos de seção da contestação).

Esse arquivo é fonte de verdade pontual para a etapa 1 (analisador) e para a validação final na etapa 4 (revisor). Sem ele, o pipeline para com erro.

### Etapa 1 — Análise

Invocar o subagent `analisador-processo-rmc` com prompt:

> "Analise esta pasta de processo RMC/RCC: {{PASTA}}. {{PASTA}}/_facts.json já está disponível como fonte de verdade pontual. Extraia dados estruturados conforme template em references/schema_caso.json, ancorando todo dado pontual (CPF, CNJ, valor, data, IP, hash) em entrada do _facts.json e preenchendo _meta.fontes_facts com referências. Trecho literal OBRIGATÓRIO em cada preliminar e tese do banco (ler somente as páginas marcadas como 'contestacao' nos marcadores). Sinalize bloqueadores em campo próprio. Devolva apenas JSON válido."

Salvar em `{{PASTA}}/_analise.json`.

### Etapa 1.5 — Checagem de bloqueadores

Ler `_analise.json:bloqueadores`. Se houver entrada com `criticidade = ALTA`:

1. NÃO avançar para etapa 2.
2. Apresentar ao usuário a lista de bloqueadores com `acao_recomendada` de cada um.
3. Aguardar instrução explícita do usuário (resolver, ignorar com risco, abortar).

### Etapa 2 — Consulta ao vault e contrato de rebate

Invocar o subagent `consultor-vault-rmc` com prompt:

> "Dado {{PASTA}}/_analise.json, leia o vault em `$OBSIDIAN_VAULT_RMC/Modelos/ReplicasRMC/`. Aplique as 16 regras de adaptação. Gere DOIS arquivos: _plano.json (plano editorial) e _contrato_rebate.json (cobertura 100% das teses do banco com seção, fundamentos, criticidade e min_paragrafos)."

Salvar em `{{PASTA}}/_plano.json` e `{{PASTA}}/_contrato_rebate.json`.

### Etapa 3 — Redação

Invocar o subagent `redator-replica-rmc` com prompt:

> "Gere a réplica .docx baseada em _analise.json + _plano.json + _contrato_rebate.json em {{PASTA}}. Salve em {{PASTA}}/Réplica - {{CNJ-resumido}} - {{NOME_AUTOR}}.docx. Estrutura espelhada à contestação (preliminares antes do mérito). Densidade dos parágrafos do modelo do escritório. ZERO travessão (—) ou hífen (-) como aposto. Listas em a), b), c) ou i, ii, iii. Autovalidação obrigatória dos 11 itens antes de devolver."

### Etapa 4 — Revisão

Invocar o subagent `revisor-replica-rmc` com prompt:

> "Valide {{PASTA}}/Réplica*.docx. Antes de qualquer outra checagem, rodar `validate_against_facts.py --replica {{PASTA}}/Réplica*.docx --facts {{PASTA}}/_facts.json --pasta {{PASTA}}` para verificar que cada CPF, CNJ, valor R$, data, IP, hash da réplica está ancorado em _facts.json e cada citação literal entre aspas existe nos PDFs do processo. Itens não-ancorados de tipo CPF/CNPJ/valor/IP/hash/citação_literal são CRÍTICOS; CNJ/data não-ancorados são MÉDIOS. Em seguida: cobertura 100% do _contrato_rebate.json, severidade graduada nos achados, Word Comments embutidos no .docx (não gerar relatório paralelo), resumo no chat com cobertura métrica + estatísticas da validação contra facts + classificação APTO / APTO COM RESSALVAS / AJUSTES NECESSÁRIOS."

### Etapa 5 — Iteração

Se classificação AJUSTES NECESSÁRIOS, salvar `_ajustes_v<N>.md` e re-invocar o redator com esse arquivo como feedback. Máximo **2 iterações**. Após 2, entregar com classificação AJUSTES RESIDUAIS e alerta no final da resposta.

### Etapa 6 — Ficha de aprendizado

Criar ficha em `$OBSIDIAN_VAULT_RMC/Aprendizado/ReplicasRMC/YYYY-MM-DD-<slug-cliente>-<slug-comarca>.md` usando o template `_template.md` do vault, pré-preenchida com os metadados do caso e os padrões detectados pelo revisor.

## Entrega ao usuário — formato fixo

No final, responder ao usuário com mensagem curta neste formato exato:

```
Réplica gerada.

Arquivo: {{PATH_DOCX}}
Ficha: {{PATH_FICHA}}

Classificação: {{APTO | APTO COM RESSALVAS | AJUSTES APLICADOS | AJUSTES RESIDUAIS}}
Cobertura de teses do banco: {{N}}/{{N}} (100%)
Pontos de atenção: {{LISTA_CURTA}}
```

O `.docx` da réplica já vem com Word Comments do revisor embutidos no parágrafo problemático (apenas CRÍTICOS e MÉDIOS, sem poluir com COSMÉTICOS).

Nada mais. Sem resumo do que foi feito, sem recap, o usuário abre o `.docx`, revisa e protocola. NÃO usar travessão como aposto na resposta.

## Configuração

A skill espera duas variáveis de ambiente (ou caminhos hardcoded equivalentes no
seu fork):

| Variável                | Default                         | Para quê                                        |
|-------------------------|---------------------------------|-------------------------------------------------|
| `OBSIDIAN_VAULT_RMC`    | `~/Obsidian/`                   | raiz do vault Obsidian com `Modelos/ReplicasRMC/` e `Aprendizado/ReplicasRMC/` |
| `CLAUDE_HOME`           | `~/.claude/`                    | onde estão `skills/replica-rmc/scripts/*.py`    |

Antes de usar, popule `$OBSIDIAN_VAULT_RMC/Modelos/ReplicasRMC/` com os arquivos descritos
em "Arquivos de referência no vault" abaixo. O repositório fornece a estrutura de skill +
subagents + scripts; o conteúdo do vault é específico do seu escritório (modelos `.docx`,
teses modulares, regras de adaptação) e fica fora deste repo.

## Regras inegociáveis (do vault `Modelos/ReplicasRMC/`)

1. **Cidade do fecho** = comarca real do processo, NUNCA "Manaus/AM" automático. Erro 22.
2. **Cambria obrigatório**. Erro 19.
3. **Sem imagens**. Erro 20.
4. **Listas com a), b), c) ou i, ii, iii — NUNCA traços**. Erro 21.
5. **"Declaração de inexistência"**, NUNCA "anulação". Erro 6.
6. **IP**: checar RFC 1918 antes de chamar de privado. Regra 16.
7. **TED**: cruzar com conta INSS. Regra 4.
8. **2ª via massiva**: inserir Bloco A. Regra 2.
9. **BMG pré-09/2023**: inserir Bloco C (confissão do próprio banco). Regra 7.
10. **RMC + RCC gêmeos**: sempre verificar HISCON. Regra 1.
11. **Maués**: cautela de tom (alerta Juiz Anderson). Regra 13.

## Arquivos de referência no vault

O subagent `consultor-vault-rmc` deve ler (não duplicar aqui):

1. `Modelos/ReplicasRMC/_MOC.md` — árvore de decisão.
2. `Modelos/ReplicasRMC/manual-consolidado.md` — panorama geral.
3. `Modelos/ReplicasRMC/estrutura-padrao.md` — 9 blocos + 15 sub-seções.
4. `Modelos/ReplicasRMC/configuracoes-visuais.md` — Cambria, margens.
5. `Modelos/ReplicasRMC/erros-herdados.md` — 29 armadilhas.
6. `Modelos/ReplicasRMC/checklist-protocolo.md` — 7 blocos de validação.
7. `Modelos/ReplicasRMC/regras-de-adaptacao.md` — 16 regras + blocos A/B/C.
8. `Modelos/ReplicasRMC/modelos-por-estado/<uf>/_index.md` — matriz de escolha.
9. `Modelos/ReplicasRMC/teses-modulares/{nossas,impugnacao}/*.md` — teses.
10. `Aprendizado/ReplicasRMC/*.md` — aprendizado cumulativo (paradigmas).

## Scripts auxiliares

Ver `scripts/` desta skill. Todos Python 3, dependências: `pymupdf`, `python-docx`.

**Camada determinística (NOVA — fundação do pipeline):**

1. `extract_facts.py` — varre PDFs com regex calibradas e gera `_facts.json` (CPFs, CNJs, OABs, datas, valores, IPs, hashes, bancos, marcadores temáticos). Roda na etapa 0.5, antes de qualquer subagent. Saída é fonte de verdade pontual para todo o pipeline.
2. `validate_against_facts.py` — checa cada CPF, CNJ, valor, data, IP, hash e citação literal da réplica gerada contra `_facts.json` e contra o texto do PDF. Roda na etapa 4 (revisor) como primeira validação.

**Extração e fatiamento:**

3. `extract_processo.py` para extração estruturada de PDF processual (texto narrativo de páginas-alvo).

**Checks específicos (mantidos):**

4. `check_ip_rfc1918.py` para validação de IP contra blocos privados.
5. `check_ted_conta_inss.py` para cruzamento conta INSS × conta TED.
6. `detect_2via_massiva.py` para detectar postagem concentrada em faturas.
7. `check_cartao_gemeo.py` para cruzar número do cartão × HISCON.
8. `check_bmg_pre_09_2023.py` para flag de BMG pré-setembro/2023.
9. `check_refin_maquiador_bmg.py` para detectar "crédito de refin" sem queda de saldo.
10. `check_ancora_contestacao.py` para validar âncora de cada afirmação da réplica.

**Geração e layout:**

11. `gerar_tabela_onerosidade.py` para os 6 valores adaptativos da tabela do mérito.
12. `gerar_docx.py` para montagem final .docx Cambria.
13. `forcar_cambria.py` para forçar Cambria em .docx existente.
14. `aplicar_layout_modelo.py` para aplicar timbre + estilos + alinhamentos do modelo do vault.

## O que esta skill NÃO faz

1. Não redige inicial, apelação ou cumprimento.
2. Não negocia acordo.
3. Não analisa HISCON isoladamente (usar skill `analise-cadeias-hiscon`).
4. Não fatia PDF sozinha (usa skill `fatiar-processo`).

## Retomada em nova sessão

Se a skill for interrompida no meio (ex: contexto acaba), retomar pelo JSON salvo:

1. Se NÃO existir `_facts.json`: começar da etapa 0.5 (rodar `extract_facts.py`).
2. Se existir `_facts.json` mas não `_analise.json`: começar da etapa 1.
3. Se existir `_analise.json` e não `_plano.json`: começar da etapa 1.5 (checagem de bloqueadores) e seguir para etapa 2.
4. Se existir `_plano.json` mas não `_contrato_rebate.json`: começar da etapa 2 com prompt parcial pedindo só o contrato.
5. Se existir os três JSONs (analise, plano, contrato_rebate) e não `.docx`: começar da etapa 3.
6. Se existir `.docx` sem revisão: começar da etapa 4.

## Referências cruzadas

1. Skill `fatiar-processo` — pré-requisito se PDF consolidado.
2. Skill `conferencia-processual` — usada internamente pelo revisor.
3. Skill `analise-cadeias-hiscon` — NÃO é chamada aqui; usar em triagem antes da inicial.
