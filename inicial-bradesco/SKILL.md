---
name: inicial-bradesco
description: Gera petição inicial contra o BANCO BRADESCO S.A. em ações declaratórias de inexistência de relação jurídica c/c repetição do indébito e danos morais. Cobre 5 famílias de tese (Tarifas, Mora+Encargo, Aplic.Invest, Título de Capitalização, PG ELETRON com terceiro), com 6 templates no vault Obsidian e seleção automática conforme as cobranças detectadas no extrato Bradesco. Use quando o usuário pedir para gerar inicial Bradesco, processar pasta de cliente Bradesco, fazer petição inicial bancária Bradesco, ou disser "faz a inicial do/da [nome do cliente]".
---

# Skill: inicial-bradesco

Geração automatizada de **petições iniciais contra o Banco Bradesco** em ações declaratórias de inexistência de relação jurídica c/c repetição do indébito em dobro e danos morais. Atende ao escritório De Azevedo Lima & Rebonatto (Maués/AM).

## Regras críticas (não esquecer)

### 1. Renda da parte autora — SEMPRE do extrato real

**NUNCA hardcode.** A renda mensal usada no parágrafo da Justiça Gratuita (`{{valor_remuneração}}` e `{{valor_remuneração_extenso}}`) é EXTRAÍDA do **extrato bancário Bradesco** do próprio cliente, no último crédito identificado das rubricas:

- `INSS`
- `CREDITO DE SALARIO`
- `TRANSF SALDO C/SAL P/CC` (típico de servidor público que recebe via conta-salário)
- `BENEFICIO PREVIDENCIARIO`
- `PAGTO BENEFICIO INSS`
- `APOSENTADORIA`
- `PENSAO`

Se NÃO houver crédito identificável no extrato, **NÃO inventar valor padrão**: alertar no relatório paralelo "RENDA NÃO IDENTIFICADA NO EXTRATO — preencher manualmente" e deixar `[A CONFIRMAR]` no DOCX.

### 2. Ementa (QUESTÃO/RATIO/SOLUÇÃO) — TEXTO LITERAL DO MODELO

A QUESTÃO/RATIO/SOLUÇÃO de cada template é **literal do modelo do escritório**. NUNCA reescrever ou parafrasear; apenas substituir placeholders dinâmicos (rubricas, ordinais) quando aplicável.

### 3. Valores monetários — SEMPRE da tabela ou do extrato

Os valores `{{total_descontos}}`, `{{dobro_descontos}}`, `{{valor_causa}}` são **calculados a partir das tabelas (PDF 7) ou do parsing direto do extrato**. NUNCA usar o "TOTAL: R$ X" impresso no rodapé da tabela como valor de uma tese isolada — esse total agrega todas as cobranças de todos os terceiros.

### 4. Documentos do cliente — SEMPRE fora da pasta KIT

Pasta `KIT/`, `0. Kit/` ou variantes é **ignorada por padrão**. Ler apenas documentos da pasta principal. Exceção: se NENHUMA outra fonte trouxer a qualificação (ex.: caso Elinaldo — sem notificação extrajudicial), pode usar o KIT como fallback **com alerta explícito no relatório paralelo**.

### 5-bis. Tipografia do modelo — preservar fontes dos TÍTULOS

**REGRA CRÍTICA**: o modelo do escritório usa Cambria APENAS no corpo. Os
**títulos e subtítulos** preservam suas fontes próprias do template (Segoe UI,
Segoe UI Semibold, Franklin Gothic Book). NÃO sobrescrever.

| Estilo (styleId) | Fonte original | Categoria |
|---|---|---|
| `2Ttulo`, `2TtuloChar` | **Segoe UI** | TÍTULO — preservar |
| `3Subttulo`, `3SubttuloChar` | **Segoe UI Semibold** | SUBTÍTULO — preservar |
| `31Subttulointermedirio`, `31SubttulointermedirioChar` | **Segoe UI Semibold** | SUBTÍTULO — preservar |
| `31Subttulosecundrio` | **Franklin Gothic Book** | SUBTÍTULO — preservar |
| `1Pargrafo`, `4Citao`, `5Listaalfabtica`, `CORPOHOMERO`, `PargrafodaLista`, `Estilo1` (+ Char) | Cambria | CORPO — forçar |
| `Normal` | Cambria | CORPO — forçar |

`helpers_docx.py` mantém duas listas separadas:
- `ESTILOS_CORPO` → recebem Cambria via `forcar_cambria_global`
- `ESTILOS_TITULO_PRESERVAR` → nunca tocar

`forcar_cambria_global` também NÃO mexe em `<a:majorFont>` do `theme1.xml`
(usado pelos títulos), apenas em `<a:minorFont>` (usado pelo corpo).

### 5-bis-2. Extratos como PDF imagem (scan/foto) — OCR automático

**REGRA CRÍTICA**: extratos Bradesco frequentemente vêm como PDF de imagem (digitalizados, fotografados pelo cliente). `page.get_text()` retorna vazio nesses casos e silenciosamente perde lançamentos.

A skill agora usa `_ler_texto_pdf()` em `extrator_documentos.py` para todas as extrações:

1. **Tenta text-layer** primeiro (rápido)
2. **Se a página não tem texto** (≤50 chars), aplica OCR easyOCR
3. **Detecta landscape** (largura > altura × 1.2) e roda 270° antes do OCR
4. **Cacheia resultado** por path para evitar reprocessar o mesmo PDF

Funções afetadas (todas usam `_ler_texto_pdf` internamente):
- `extrair_renda_real(extrato_path)` — Justiça Gratuita
- `extrair_conta_agencia(extrato_path)` — qualificação da conta
- `parsear_lancamentos_extrato(extrato_path, rubrica)` — auditoria
- `parsear_tabela_descontos(tabela_path, filtro_rubrica)` — base da tese

Para detectar antecipadamente:

```python
from extrator_documentos import detectar_pdf_imagem

if detectar_pdf_imagem(extrato_path):
    print('Extrato é imagem; OCR vai rodar (~30s/página)')
```

Limitações do OCR:
- 5-15s por página em PDF imagem
- Pode confundir 0/O, 1/I, valores R$ com pontuação ruim
- Se severidade da auditoria tabela↔extrato vier `CRITICO`, sempre revisar manual

### 5-quater. Tabela do NotebookLM incompleta — auto-completa via extrato digital

**REGRA CRÍTICA**: Para teses TARIFAS, sempre que houver na pasta do cliente um extrato digital com text-layer (geralmente em `0. Kit/EXTRATO - <NOME>.pdf` baixado do app Bradesco), a skill **DEVE** rodar `auditor_tarifas_completo.auditar_e_completar_tarifas()` ANTES de montar a tese.

A tabela XLSX gerada pelo NotebookLM com frequência ignora rubricas adjacentes que também envolvem TARIFA: VR.PARCIAL CESTA (parcelas), TARIFA EMISSÃO EXTRATO, etc. Procuração genérica de TARIFA BANCÁRIA cobre TODAS — não impugnar apenas a CESTA cheia significa subdimensionar a inicial em 50-100%.

**Caso paradigma — CELIA RODRIGUES DA SILVA (09/05/2026)**:
- Tabela do NotebookLM: 32 lançamentos / R$ 1.324,02 (só CESTA cheia)
- Extrato digital parseado posicionalmente: **112 lançamentos / R$ 2.434,35** (CESTA + VR.PARCIAL + EMISSÃO EXTRATO)
- Diferença: **80 lançamentos perdidos** se usasse só a tabela

**Como invocar:**

```python
from auditor_tarifas_completo import auditar_e_completar_tarifas, lancamentos_para_tese

audit = auditar_e_completar_tarifas(
    pasta_cliente=PASTA_CLIENTE,                # raiz do cliente (onde está '0. Kit/')
    tabela_xlsx_path=TABELA_NOTEBOOKLM,         # XLSX original (opcional, p/ comparar)
    cliente_nome='CELIA RODRIGUES DA SILVA',
    conta_label='Agência: 3706 | Conta: 16649-9',
    procuracao_label='TARIFA BANCÁRIA - CESTA B.EXPRESSO',
    gerar_planilha_v2=True,                     # cria '<...> - v2.xlsx' substituta
)

# audit['severidade'] ∈ {'OK', 'INCOMPLETO', 'CRITICO'}
# audit['lancamentos'] = lista completa do extrato (todos com 'TARIFA')
# audit['planilha_v2_path'] = path da planilha gerada (substitui a do NotebookLM)
# audit['recomendacao'] = texto humano para o relatório paralelo

LANCAMENTOS = lancamentos_para_tese(audit['lancamentos'])
tese = {'rubrica': 'TARIFA BANCÁRIA - CESTA B.EXPRESSO', 'lancamentos': LANCAMENTOS}
```

**O que a rotina faz por baixo dos panos:**

1. Procura extrato digital com text-layer (em `0. Kit/`, raiz do cliente, etc.) via `parser_extrato_posicional.encontrar_extrato_digital_no_kit`
2. Faz parsing posicional preciso (estrutura DATA/RUBRICA/DOCTO/VALOR/SALDO) via `parser_extrato_posicional.parsear_extrato_digital` — superior ao OCR para extratos digitais
3. Filtra TODOS os lançamentos com `TARIFA` na descrição (não só CESTA)
4. Lê a tabela do NotebookLM (se fornecida) e compara
5. Se a tabela está incompleta (>5 lançamentos a mais no extrato OU divergência >R$ 50), gera planilha XLSX v2 com todas as categorias separadas (CESTA / VR.PARCIAL / EMISSÃO EXTRATO) na pasta do cliente
6. Retorna lançamentos + relatório textual para anexar ao `_RELATORIO_PENDENCIAS_*.docx`

**Bug do template "R$ R$" duplicado** — após `aplicar_template`, sempre rodar pós-fix:

```python
import re
from docx import Document
d = Document(DOCX_OUT)
for p in d.paragraphs:
    if re.search(r'R\$\s*R\$', p.text):
        full = ''.join(r.text for r in p.runs)
        novo = re.sub(r'R\$\s*R\$', 'R$', full)
        p.runs[0].text = novo
        for r in p.runs[1:]: r.text = ''
d.save(DOCX_OUT)
```

(O bug está no template — `R$ {{total_descontos}}` + placeholder já formatado com "R$" → `R$ R$ X,YY`. Editar o template no vault removendo o `R$ ` antes de cada placeholder monetário resolve permanente.)

### 5-quinquies. Renda não identificada — REMOVER parágrafo da Justiça Gratuita

**REGRA**: quando `extrair_renda_real()` retornar `None` (nenhum crédito INSS/SALARIO/etc. ≥ R$ 500 nos extratos), **NÃO** deixar `[A CONFIRMAR]` no DOCX nem renda zerada — **REMOVER os parágrafos** da Justiça Gratuita.

Parágrafos a remover (2 normalmente):
1. "Frisa-se que a parte autora recebe ... no valor líquido de apenas R$ ... conforme se comprova pelo extrato anexo, restando cristalina a sua fragilidade econômica."
2. "Para fazer frente às despesas fixas com alimentação, vestuário ... pugna, expressamente, pelo beneplácito da gratuidade de justiça..."

Função: `remover_paragrafo_renda(docx_path)` no batch script.

Adicionar alerta no relatório paralelo: "RENDA não detectada — parágrafo da Justiça Gratuita REMOVIDO. Reavaliar se é caso de pedir gratuidade (adicionar parágrafo manual com renda real do cliente) ou prosseguir sem."

### 5-sexies. Conta sem número — ALERTA CRÍTICO 🛑

**REGRA**: quando `extrair_conta_agencia()` retornar dict sem `conta` (só `agencia`), gerar alerta CRÍTICO em vermelho no relatório paralelo. Sem número de conta, a inicial NÃO PODE ser protocolada.

Causas comuns:
- Iteração de extratos parou no primeiro que tinha só agência (preferir os que têm `agencia` E `conta`)
- Cabeçalho do extrato com formato diferente (regex `Conta[:\s]*([\d-]+)` não pega)
- Extrato escaneado sem text-layer (cair em OCR — impreciso)

Boas práticas:
1. Em `extrair_conta_e_renda(extratos_paths)`: prefirir extrato com agência+conta. Só fallback para "só agência" se NENHUM tiver ambos.
2. Marcar `alertas_critico` no relatório com cor vermelha: "CONTA/AGÊNCIA faltando — extraído apenas agencia=X / conta=. Sem o número da conta, a inicial NÃO PODE ser protocolada."

### 5-ter. Auditoria tabela ↔ extrato — SEMPRE rodar antes de montar tese

**REGRA CRÍTICA**: a tabela de descontos gerada pelo NotebookLM tem apresentado erros recorrentes (rubricas faltantes, valores trocados, lançamentos perdidos). NUNCA usar a tabela como única fonte sem auditoria.

Use `extrator_documentos.obter_lancamentos_auditados(tabela_path, extrato_path, rubrica)`. Ela:

1. Parseia a TABELA filtrando por rubrica
2. Parseia o EXTRATO direto filtrando pela mesma rubrica
3. Compara contagem + soma + datas
4. Retorna `lancamentos` da fonte mais confiável + `relatorio` com divergências

Política de seleção:
- **paridade** (tabela = extrato) → usa tabela (visualmente já formatada)
- **extrato > tabela** em quantidade → usa extrato (tabela incompleta)
- **tabela > extrato** → usa tabela mas alerta CRÍTICO para revisão manual (parser do extrato pode ter falhado)

Sempre incluir `relatorio` no relatório paralelo da inicial. Se severidade for `CRITICO`, NÃO entregar para o cliente sem revisão manual da fonte.

```python
from extrator_documentos import obter_lancamentos_auditados

audit = obter_lancamentos_auditados(
    tabela_path='/.../7- TABELA - DESCONTOS.pdf',
    extrato_path='/.../EXTRATO BRADESCO.pdf',
    rubrica='MORA CRED PESS'
)
if audit['severidade'] == 'CRITICO':
    print(audit['relatorio'])  # ler antes de prosseguir
tese = {'rubrica': 'MORA CRED PESS', 'lancamentos': audit['lancamentos']}
```

### 5-septies. Fonte dos lançamentos — HIERARQUIA OBRIGATÓRIA + auditar duplicação

**REGRA CRÍTICA** (caso ANA CAROLINE 10/05/2026 — usuário viu 47 hits no Ctrl+F mas a inicial reportou 24): a contagem de lançamentos NUNCA pode ser feita "no olho". A skill deve seguir esta hierarquia rígida E sempre auditar duplicação no PDF.

**Hierarquia de fontes (em ordem de preferência):**

1. **EXISTE planilha (xlsx/csv) na pasta do cliente** → USAR a planilha como fonte primária E rodar auditoria cruzada com o extrato (`obter_lancamentos_auditados`). Diferenças >5 lançamentos OU >R$ 50 → severidade CRITICO no relatório.
2. **NÃO existe planilha** → GERAR uma em Excel a partir do extrato, salvar na pasta do cliente como `TABELA_<RUBRICA>_<NOME>_v<N>.xlsx`. O usuário converte para PDF depois se quiser. A planilha deve ter no mínimo 4 abas:
   - **Resumo**: cliente, agência, conta, rubrica, contagem, soma, dobro, período
   - **Lançamentos Únicos**: tabela final ordenada por data (data, contrato, rubrica, valor, página origem, hora geração)
   - **Auditoria Duplicação**: linhas descartadas como duplicatas
   - **Auditoria Crua**: TODAS as ocorrências brutas com flag ÚNICA/DUPLICATA (verde/vermelho)
3. **PDF sem text-layer (scan/foto)** → OCR via Tesseract OU leitura visual nativa (PyMuPDF render → Read visual). NUNCA confiar em "achei só X lançamentos" sem ter parseado todas as páginas. Se mesmo o OCR falhar, abrir alerta CRÍTICO no relatório paralelo e exigir revisão manual.

**Auditoria de duplicação OBRIGATÓRIA** (causa-raiz do mal-entendido ANA CAROLINE):

Clientes frequentemente baixam o extrato Bradesco várias vezes seguidas (segundos/minutos de diferença) e mandam todos juntos. O resultado é UM PDF com o mesmo período repetido várias vezes. Sintoma: `Ctrl+F "MORA"` retorna o dobro/triplo do que a tabela real tem.

Detecção:
- Para cada página do PDF, extrair o cabeçalho `Data: DD/MM/AAAA - HHhMM` E `Movimentação entre: DD/MM/AAAA e DD/MM/AAAA`
- Agrupar páginas por (período, hora_geracao) — cada grupo = um download independente do extrato
- Se múltiplos grupos cobrirem o MESMO período → detectar duplicação
- Deduplicar lançamentos por chave `(data, contrato, valor)` — manter o primeiro, descartar os demais
- Registrar na aba "Auditoria Duplicação" da planilha o que foi descartado e de qual versão veio

**Caso paradigma ANA CAROLINE (10/05/2026)**:
- PDF tinha 26 páginas, 47 hits brutos de "MORA CREDITO PESSOAL"
- Estrutura: Jan-Dez/2020 baixado às 11h19 (pgs 1-9) **+ baixado de novo às 11h21 (pgs 10-18)** + 2019 (pgs 19-22) + 2021 (pgs 23-24) + 2026 (pgs 25-26)
- Após dedup por (data, contrato, valor): **24 lançamentos únicos** = R$ 3.554,71
- Conferência: 23 únicos × 2 versões + 1 (de 2021) = 47 hits ✓

**Por que isso é crítico**: o usuário SEMPRE vai conferir com Ctrl+F. Se a skill reportar 24 mas o Ctrl+F mostrar 47, a confiança quebra. A planilha Excel com a aba "Auditoria Crua" (verde = único, vermelho = duplicata) é a prova matemática que reconcilia os dois números.

```python
from auditor_tarifas_completo import gerar_planilha_lancamentos

audit = gerar_planilha_lancamentos(
    extrato_pdf=PASTA_CLIENTE / 'EXTRATOS.pdf',
    rubrica='MORA CREDITO PESSOAL',
    saida_xlsx=PASTA_CLIENTE / f'TABELA_MORA_{NOME_CURTO}_v3.xlsx',
)
# audit['unicos'] = lista para usar na tese
# audit['duplicatas'] = lista descartada
# audit['relatorio'] = texto p/ relatório paralelo
```

### 5-novies. Pasta com >1 procuração = INICIAL-COMBINADA obrigatória

**REGRA CRÍTICA** (caso LUIZ PIRES 10/05/2026 — usuário detectou que a inicial cobria só 1 das 2 procurações da pasta): **toda subpasta de tese que contém mais de uma procuração `2 - PROCURAÇÃO BRADESCO ...pdf` exige uma `inicial-combinada.docx`**, não múltiplas iniciais separadas e nem **uma só inicial cobrindo apenas 1 das procurações**.

Antes de chamar qualquer runner singular (`inicial-mora`, `inicial-encargo`, `inicial-tarifas`, `inicial-mora-encargo`), o pipeline DEVE:

1. Listar `2 - PROCURAÇÃO BRADESCO *.pdf` na pasta da tese.
2. Se `count > 1` → usar `_combinada_helper.gerar_combinada()` mapeando cada procuração para uma `tese` no array.
3. Identificar a família de cada procuração pelo nome do arquivo:
   - `MORA CRED PESS` / `ENCARGOS LIMITE DE CRED` → família **MORA**
   - `TARIFA BANCÁRIA *` / `SERVIÇO CARTÃO PROTEGIDO` (seguro de cartão) → família **TARIFAS**
   - `TÍTULO DE CAPITALIZAÇÃO` / `CARTÃO PROTEGIDO` (quando = título) → família **TITULO**
   - `APLIC.INVEST FÁCIL` → família **APLIC**
   - `PG ELETRON` / `PAGAMENTO ELETRÔNICO` → família **PG_ELETRON** (não combina — vai em `inicial-pg-eletron` separada por terceiro réu)
4. Buscar lançamentos de cada rubrica no extrato (`6 - EXTRATO BANCÁRIO.pdf`) ou na planilha do cliente (`Tabela de Descontos por Procuracao - <NOME>.xlsx`).
5. Gerar `INICIAL_Combinada_<CLIENTE>_v<N>.docx` (nome contém "Combinada", não "Encargo" ou "Mora" sozinhos).
6. Gerar planilha Excel `TABELA_Combinada_<CLIENTE>_v<N>.xlsx` com no mínimo 4 abas: **Resumo** (totais por rubrica + valor causa) | **<RUBRICA 1>** | **<RUBRICA 2>** | **Combinado Cronológico** (intercaladas, com cor por família).
7. Calcular dano moral conforme §9: 1 tese isolada = R$ 15.000; **2+ teses combinadas = R$ 5.000 por tese** (caso LUIZ PIRES = R$ 10.000).

**Caso paradigma LUIZ PIRES (10/05/2026)**:
- Subpasta `LUIZ PIRES - Ruth - TARIFA/ENCARGOS/` tinha 2 procurações: `ENCARGOS LIMITE DE CRED` + `SERVIÇO CARTÃO PROTEGIDO`.
- Sessão anterior gerou apenas `INICIAL_Encargo_LUIZ_v3.docx` cobrindo só ENCARGOS — deixou a procuração de cartão protegido orfã (erro grave: ação proposta apenas sobre 1 das 2 rubricas para as quais o cliente assinou procuração).
- Correção: `INICIAL_Combinada_LUIZ_v3.docx` com 2 núcleos fáticos (TARIFAS + MORA), 78 lançamentos totais (54 ENCARGOS + 24 CARTÃO), R$ 421,79 + dobro R$ 843,58 + dano moral R$ 10.000 = VC R$ 10.843,58.

**Anti-padrão comprovado**: nunca olhar SÓ os arquivos de tese específica (`6 - EXTRATO`, `7 - TABELA`) sem antes listar quantas procurações existem na pasta. A pasta é a unidade de combinação, não o template.

**Bug do `gerar_combinada` corrigido na mesma data**:
- O helper chama `aplicar_template` que com `strict=True` quebrava porque o template inicial-combinada usa placeholders de seção (`{{INICIO_BLOCO_X}}`, `{{FIM_BLOCO_X}}`, `{{BLOCO_PEDIDO_X}}`, `{{__DELETE__}}`, `{{nucleos_faticos}}`) processados depois via python-docx. Solução: helper agora chama `aplicar_template(..., strict=False)` e faz sua PRÓPRIA verificação final de residuais ao terminar todo o pós-processamento.
- O helper também não populava `{{rubrica_mora}}`, `{{rubrica_encargo}}` e variantes (`_caps`, `_canonica`, `_canonica_caps`) usadas na seção IRDR. Solução: agora deriva esses valores das `teses[familia=='MORA']` automaticamente.

### 5-octies. Toda modificação na peça é GRIFADA EM AMARELO — sem exceção

**REGRA**: qualquer texto que a skill ou um pós-processador (incluindo correções manuais de pente-fino) inserir, alterar ou substituir em um DOCX **deve** receber `<w:highlight w:val="yellow"/>` no `rPr` do run resultante.

Esse grifo é o **mecanismo único de auditoria visual** do operador antes do protocolo: o que está grifado em amarelo foi tocado pela skill; o que está sem grifo é texto-fixo do template. Sem essa convenção, não há como saber rapidamente se um campo foi preenchido corretamente, esquecido ou corrompido.

Implementação:
- O `helpers_docx.processar_paragrafo` já aplica `add_highlight()` em todo run substituído (campo `True` na 3ª flag de `plain_chars`).
- Pós-processamento (`pos_processar_documento`, scripts de correção, edições manuais) **deve** preservar ou re-aplicar o grifo. Nunca remover o highlight de um run que veio modificado.
- Para edições NOVAS feitas fora do `processar_paragrafo`: o run alterado deve receber `add_highlight(rpr)` antes de ser salvo.

> "Outra configuração importante que você não pode esquecer é, todas as modificações que você fizer em qualquer peça, deve grifar em amarelo para indicar o que modificou." — usuário, sessão TESTE 1, 10/05/2026.

### 6. Auditoria automática pós-geração — SEMPRE rodar

Após gerar o DOCX, rodar `auditor.auditar_inicial_gerada()` que detecta:

- Valores `R$ XXX,XX` que parecem caso-específico (verificar contra a tabela)
- Datas `dd/mm/yyyy` fora de jurisprudência
- CPFs/CNPJs/contas/CEPs que não estão na lista esperada
- Nomes próprios em CAIXA ALTA suspeitos

Filtros automáticos (não alertar):
- Endereço matriz Joaçaba/SC: `89600-000`, `Frei Rogério`, `Joaçaba`
- Endereço unidade Maués/AM: `69.195-000`, `69195-000`, `69190-000`, `Travessa Michiles`
- Endereço Bradesco: `60.746.948`, `06029-900`, `Cidade de Deus`, `Vila Yara`, `Osasco`
- Multa diária padrão `R$ 500,00`
- Datas de IRDR/jurisprudência (`13/09/2025`, `0005053-71.2023.8.04.0000`, `0004464-79.2023.8.04.0000`)

### 7. Endereço composto do escritório — matriz Joaçaba/SC + unidade de apoio da UF

Os 6 templates Bradesco do vault têm hardcoded apenas a unidade de apoio em
Maués/AM (`"com unidade na Rua Travessa Michiles, ..."`). O pipeline
substitui esse trecho automaticamente pelo formato canônico do escritório:

> "com escritório na Rua Frei Rogério, 541, Centro, Joaçaba/SC, CEP 89600-000, e unidade de apoio em Travessa Michiles, s/n, Centro, Maués/AM, CEP 69195-000"

A função `helpers_docx.inserir_endereco_composto_se_faltando(root, uf)` é
chamada dentro de `aplicar_template` (após `pos_processar_documento`).
Lê a UF do caso de `dados['uf']` (default `'AM'`) e usa
`skills/_common/escritorios_cadastro.py:montar_endereco_escritorio_completo`
como fonte única de verdade compartilhada com `notificacao-extrajudicial` e
`inicial-nao-contratado`.

**Comportamento por UF:**

| `dados['uf']` | Saída |
|---|---|
| `AM` (caso atual padrão) | Matriz Joaçaba/SC + unidade de apoio em Maués/AM |
| `SE` (Bradesco vai entrar) | Matriz Joaçaba/SC + unidade de apoio em Arapiraca/AL (Tiago cobre SE via Arapiraca) |
| `AL` | Matriz Joaçaba/SC + unidade de apoio em Arapiraca/AL |
| `BA`, `ES`, `MG`, `SC`, qualquer outra | **Só** a matriz Joaçaba/SC. **Nunca placeholder visível.** |

**Regra inviolável (2026-05-11):** se a UF não tem unidade de apoio
CONFIRMADA no cadastro central, a peça sai com SÓ a matriz. Jamais aparece
`[A CONFIRMAR]` em nenhuma parte do DOCX. A salvaguarda
`_eh_placeholder` em `escritorios_cadastro.py` filtra qualquer entrada que
contenha marcador entre colchetes, "CONFIRMAR", "PENDENTE" ou "TODO".

Idempotente: se o parágrafo já contém "Frei Rogério" (já foi processado em
rodada anterior ou veio editado), a função não toca.

## Catálogo de teses

| Código | Rubricas no extrato | Template | Réu(s) |
|---|---|---|---|
| `TARIFAS` | TARIFA BANCARIA CESTA *, VR.PARCIAL CESTA *, CARTAO CREDITO ANUIDADE, demais tarifárias | `inicial-tarifas.docx` | Bradesco |
| `MORA` | MORA CRED PESS / CRED MORA PESS, ENC LIM CRED, ENCARGO (ambos contam como 1 só tese) | `inicial-mora.docx` (1 só, mora ou encargo) ou `inicial-mora-encargo.docx` (ambos) | Bradesco |
| `APLIC` | APLIC.INVEST FACIL | `inicial-aplic-invest.docx` | Bradesco |
| `TITULO` | TITULO DE CAPITALIZACAO | (a criar — usar `inicial-combinada.docx` por enquanto) | Bradesco |
| `PG_ELETRON` | PAGTO ELETRON COBRANCA \<NOME DO TERCEIRO\> | `inicial-pg-eletron.docx` | Bradesco + Terceiro Beneficiário |

## Pipeline completo

```
ENTRADA: caminho da pasta do cliente
    │
    ▼
[1] Coletar documentos (Glob, exclui KIT/)
    │
    ▼
[2] Classificar arquivos (heurística por nome + conteúdo)
        Tabelas: 7 - TABELA *.pdf (uma por tese ou consolidada)
        Notificação: 8 - NOTIFICACAO*.pdf
        Extrato: 6 - EXTRATO*.pdf / 6 - EXTRATOS*.pdf
        Comprovante residência: 5 - COMPROVANTE*.pdf
        Declaração domicílio: 5.1 - DECLARACAO DOMICILIO*.pdf
        RG: 3 - RG.pdf (geralmente PDF escaneado, OCR pendente)
    │
    ▼
[3] Detectar teses ativas
        Pelas tabelas presentes na pasta principal (excluindo KIT/)
        Mapeamento via classificador.classificar_tese(arquivo + rubricas)
    │
    ▼
[4] Decidir template
        Vide § "Regra de seleção do template"
    │
    ▼
[5] Extrair qualificação do autor
        FONTE PRIMÁRIA: notificação extrajudicial (texto-camada extraível)
        FALLBACK 1: declaração de domicílio (5.1)
        FALLBACK 2: comprovante de residência (5) — apenas se titular = autor
        FALLBACK 3 (raro): KIT/ — alerta explícito no relatório
    │
    ▼
[6] Extrair conta + agência (1ª página do extrato)
    │
    ▼
[7] Extrair RENDA REAL do extrato (regra crítica § 1)
        Buscar último crédito INSS/SALARIO/TRANSF SALDO C/SAL/etc.
        Filtrar valores ≥ R$ 500
        Pegar o mais RECENTE
        Se não houver: ALERTAR e deixar [A CONFIRMAR]
    │
    ▼
[8] Para cada tese ativa, extrair dados da tabela
        Filtrar lançamentos da rubrica daquela tese
        Calcular: total simples, dobro, número, período (início/fim)
        Auditoria contra extrato: confirmar que tabela bate com extrato
    │
    ▼
[9] Calcular dano moral e valor da causa
        1 tese isolada → R$ 15.000 dano moral
        2+ teses combinadas → R$ 5.000 × N
        Valor causa = soma_dobros + dano_moral_total
    │
    ▼
[10] Verificar idade (prioridade idoso)
        RG via OCR (se Tesseract disponível)
        OU notificação chama "pessoa idosa" → assumir idoso + alerta
        OU dado faltando → assumir não idoso + alerta
    │
    ▼
[11] Para PG ELETRON: extrair dados do TERCEIRO
        FONTE PRIMÁRIA: notificação extrajudicial (lista nome, CNPJ, endereço)
        FALLBACK: dicionário canônico (banco de dados a construir)
        FALLBACK MANUAL: Receita Federal / Google
        Se faltar: ALERTAR e deixar placeholders
    │
    ▼
[12] Aplicar template
        Copiar template do Obsidian para pasta do cliente
        Aplicar substituições run-aware preservando rPr de origem
        Para PG ELETRON: 5 runs em p14 (qualif réus) — Bradesco e Terceiro em rStyle 2TtuloChar
        Aplicar formatação de RUBRICA: caps + bold + italic + underline + amarelo
        Aplicar grifo amarelo nos demais campos modificados
        Omitir limpamente OPCIONAIS vazios (estado_civil, profissão, RG, etc.)
    │
    ▼
[13] AUDITORIA PÓS-GERAÇÃO (regra crítica § 5)
        helpers.auditar_inicial_gerada(path) → list de achados
    │
    ▼
[14] Gerar relatório paralelo
        _RELATORIO_pendencias_<TESE>_<NOME>.docx
        Seções: Resumo, Pendências, Divergências resolvidas, Auditoria automática, Confirmações manuais, Checklist
    │
    ▼
[15] Retornar caminhos dos 2 arquivos gerados
```

## Regras de seleção do template

```python
def selecionar_template(teses_ativas, eh_pg_eletron, comarca):
    if eh_pg_eletron:
        # 1 inicial por terceiro, sempre
        return 'inicial-pg-eletron.docx'

    if len(teses_ativas) == 1:
        tese = teses_ativas[0]
        if tese == 'TARIFAS': return 'inicial-tarifas.docx'
        if tese == 'MORA':
            # Verifica se tem só Mora, só Encargo, ou ambos
            if rubricas_inclui_mora and rubricas_inclui_encargo:
                return 'inicial-mora-encargo.docx'
            else:
                return 'inicial-mora.docx'
        if tese == 'APLIC': return 'inicial-aplic-invest.docx'
        if tese == 'TITULO': return 'inicial-combinada.docx'  # template próprio pendente

    # 2+ teses
    if deve_combinar(teses_ativas, comarca):
        return 'inicial-combinada.docx'
    else:
        # Não cumpre critério de combinação — gerar 1 inicial por tese
        return [selecionar_template([t], False, comarca) for t in teses_ativas]


def deve_combinar(teses_ativas, comarca):
    COMARCAS_QUE_JUNTAM = {'Caapiranga', 'Presidente Figueiredo', 'Manacapuru'}
    LIMITE_VALOR_BAIXO = 400.00  # dobro

    if comarca in COMARCAS_QUE_JUNTAM:
        return True
    if any(t.dobro <= LIMITE_VALOR_BAIXO for t in teses_ativas):
        return True
    if sum(t.dobro for t in teses_ativas) <= LIMITE_VALOR_BAIXO:
        return True
    return False
```

## Cálculo do dano moral e valor da causa

| Cenário | Valor do dano moral total |
|---|---|
| 1 tese isolada (Tarifas, Mora, Mora+Encargo, Aplic, Título, PG ELETRON) | **R$ 15.000,00** |
| 2+ teses combinadas | **R$ 5.000,00 × N teses** |

Mora + Encargo = **1 só tese** (segue IRDR 0004464 do TJ-AM).

```
valor_causa = soma_dos_dobros_das_teses + dano_moral_total
```

## Hierarquia de fontes (ver § 5)

| Campo | Fonte 1 | Fonte 2 | Fonte 3 |
|---|---|---|---|
| `nome_completo` | Notificação extrajudicial | KIT (ressalva) | RG OCR |
| `cpf` | Notificação | KIT (ressalva) | RG OCR |
| `rg` + `orgao_expedidor` | Notificação | KIT (ressalva) | RG físico |
| `nacionalidade` | Notificação | default "brasileiro/a" | — |
| `estado_civil` | Notificação | KIT | manual |
| `profissao` | Notificação | KIT | manual ("aposentado" se INSS) |
| `logradouro/numero/bairro/cidade/cep/uf` | Declaração de Domicílio | Notificação | Comprovante residência (se titular = autor) |
| `agencia` / `conta` | Extrato Bradesco (1ª página) | — | — |
| `valor_remuneração` | **Extrato Bradesco — último crédito INSS/SALARIO/etc.** (regra § 1) | — | — |
| `competência` | Notificação ou cidade do autor | manual | — |
| Para PG ELETRON: `nome_terceiro`, `cnpj_terceiro`, `endereco_terceiro` | Notificação extrajudicial (preferencial) | Receita Federal / Google | manual |

## Formatação visual obrigatória

### Cambria global

`theme1.xml` com majorFont+minorFont = Cambria. `rPrDefault` em styles.xml com `<w:rFonts w:ascii="Cambria" w:hAnsi="Cambria" w:cs="Cambria"/>`. Estilos custom (1Pargrafo, CORPOHOMERO, 5Listaalfabtica, PargrafodaLista) também forçados para Cambria.

### Destaque do nome em Segoe UI Bold (rStyle 2TtuloChar)

- Qualificação do autor (parágrafo `{{nome_completo}}`): nome em **Segoe UI Bold via rStyle 2TtuloChar**, resto em Cambria neutro
- PG ELETRON, qualificação dos réus: 5 runs separados onde **BANCO BRADESCO S.A.** e **{{nome_terceiro}}** ficam em rStyle 2TtuloChar; resto em Cambria neutro

A função de geração precisa criar 2 ou 5 runs (não 1 só), preservando o rPr correto em cada trecho.

### Grifo amarelo

Todo campo modificado pela skill ganha `<w:highlight w:val="yellow"/>`. Inclui placeholders preenchidos, datas, valores, números, etc.

### Rubricas — formatação especial

CAIXA ALTA + **bold + italic + sublinhado + amarelo** simultaneamente. Aplica em:

- Núcleos fáticos (`{{rubrica_curta_caps}}`, `{{titulo}}` etc.)
- Subtítulo do bloco doutrinário ("Não contratação e cobrança indevida de '...'")
- Bloco de pedido por tese (declaratório cita a rubrica)
- Citações de jurisprudência da rubrica

```python
RUBRICA_FORMATADA = {
    'titulo',                  # template tarifas (junção de TODAS as rubricas)
    'rubrica_curta',           # mora.docx Title Case
    'rubrica_curta_caps',      # CAPS - tarifas/mora/aplic/pgeletron
    'rubrica_completa',        # mora.docx Title Case
    'rubrica_completa_caps',   # mora.docx CAPS
}

def add_rubrica_formato(rpr_elem):
    etree.SubElement(rpr_elem, 'b'); etree.SubElement(rpr_elem, 'bCs')
    etree.SubElement(rpr_elem, 'i'); etree.SubElement(rpr_elem, 'iCs')
    u = etree.SubElement(rpr_elem, 'u'); u.set('val', 'single')
    h = etree.SubElement(rpr_elem, 'highlight'); h.set('val', 'yellow')
```

### Ordinais dos núcleos fáticos (combinada)

"Primeiro/Segundo/Terceiro/Quarto núcleo fático" → **negrito** (sem amarelo, sem caps).

### Pedidos

Cabeçalho do bloco da tese: estilo `5. Lista alfabética` (numeração corrida).

Itens internos da tese: estilo `List Paragraph` com indent left=2268 (~4cm) + prefixos literais "a) ", "b) ", "b.1) ", "c) ".

## Variantes de rubrica (placeholders dinâmicos)

Para o template `inicial-mora.docx` (compartilhado entre Mora e Encargo isolados), 4 placeholders:

| Placeholder | Mora | Encargo |
|---|---|---|
| `{{rubrica_curta}}` (Title) | "Mora Cred Pess" | "Enc. Lim. Crédito" |
| `{{rubrica_curta_caps}}` (CAPS) | "MORA CRED PESS" | "ENC LIM CRÉDITO" |
| `{{rubrica_completa}}` (Title) | "Crédito Mora Pessoal" | "Encargos Limite de Crédito" |
| `{{rubrica_completa_caps}}` (CAPS) | "MORA CREDITO PESSOAL" | "ENCARGOS LIMITE DE CRÉDITO" |

Para `inicial-tarifas.docx`: o `{{titulo}}` deve listar **TODAS as rubricas distintas** detectadas na tabela do caso, separadas por " / ", em CAIXA ALTA com normalização de acentos (TARIFA BANCARIA → TARIFA BANCÁRIA).

Para `inicial-pg-eletron.docx`: `{{rubrica_curta_caps}}` traz a rubrica completa do extrato (ex.: "PAGTO ELETRON COBRANCA ASPECIR").

## Normalização de acentos das rubricas

```python
NORMALIZACOES = {
    'TARIFA BANCARIA':         'TARIFA BANCÁRIA',
    'TITULO DE CAPITALIZACAO': 'TÍTULO DE CAPITALIZAÇÃO',
    'MORA CREDITO PESSOAL':    'MORA CRÉDITO PESSOAL',
    'ENCARGOS LIMITE DE CRED': 'ENCARGOS LIMITE DE CRÉDITO',
    'CARTAO CREDITO ANUIDADE': 'CARTÃO CRÉDITO ANUIDADE',
    'APLIC INVEST FACIL':      'APLIC.INVEST FÁCIL',
}
```

## Casos especiais

### APLIC.INVEST — auditoria de aplicações vs resgates + estratégia padrão (b)

Tese complicada. APLIC.INVEST FACIL é APLICAÇÃO automática (débito), e RESGATE INVEST FACIL é o retorno do dinheiro (crédito). Antes de gerar, rodar auditoria:

```python
def auditoria_aplic_invest(extrato_path):
    aplicacoes = soma de todos APLIC.INVEST FACIL no extrato
    resgates   = soma de todos RESGATE INVEST FACIL no extrato
    saldo_liquido = aplicacoes - resgates
    janela_media = média de dias entre cada APLIC e o(s) RESGATE(s) correspondente(s)
    if saldo_liquido <= 0 OR janela_media <= 5:
        # Cliente recebeu de volta praticamente tudo em janela curta
        # → adotar estratégia (b) PADRÃO (vide § "Estratégia (b) padrão")
```

**Estratégia (b) PADRÃO confirmada pelo procurador (06/05/2026, caso DENIVAL CARVALHO BATISTA)**:

Quando a auditoria detectar **ciclo aplica-resgate em D+1 a D+3** na maioria dos meses (saldo líquido ≈ zero, janela curta), a tese a aplicar é **estratégia (b) — só dano moral fundamentado nas RETENÇÕES recorrentes**, sem repetição em dobro. Razão: cada aplicação automática mensal sem autorização expressa configura prática abusiva autônoma (art. 39 VI CDC), mesmo que devolvida em D+1; o dano moral decorre da privação reiterada da autodeterminação do consumidor sobre a renda alimentar (não da perda patrimonial líquida, que inexiste).

Pleito típico (b):
- (a) declarar inexistência da relação de aplicação automática
- (b) obrigação de não fazer (cessar) com multa diária R$ 500
- (c) dano moral R$ 15.000
- VC = R$ 15.000 (cabe folgadamente no JEC, ~10 SM)

**Pós-processamento OBRIGATÓRIO do template `inicial-aplic-invest.docx` para estratégia (b)**:

O template padrão pleiteia repetição em dobro do bruto aplicado, gerando contradição com a estratégia (b). Antes de salvar o DOCX, é necessário:

1. **REMOVER 7 parágrafos** do bloco "Repetição do indébito" + pedido subsidiário:
   - Subtítulo "Repetição do indébito"
   - "Caso se verifique a existência de valores indevidamente aplicados..."
   - "Art. 42. Na cobrança de débitos..."
   - "Parágrafo único. O consumidor cobrado em quantia indevida..."
   - "Assinala-se que a restituição em dobro se faz necessária como penalidade..."
   - "Dessarte, deve a requerida ser condenada a restituir em dobro..."
   - Pedido (b) "Havendo a retenção dos valores a título de investimento indevido..."

2. **REESCREVER o parágrafo doutrinário** que inicia com "Além disso, havendo lançamentos, cobranças ou perdas vinculadas..." (faz referência à repetição em dobro). Substituir pelo texto:
   > "A cobrança indevida não decorre de engano justificável, mas de modelo operacional estruturado para funcionar sem contratação inequívoca, configurando ato ilícito reiterado durante todo o período em que a renda alimentar da parte autora ficou indisponível para uso imediato."

3. **INSERIR parágrafo do caso concreto** após "Alegar que os valores permaneciam disponíveis e não geraram saldo negativo...":
   > "No caso concreto, o extrato bancário registra N (...) ocorrências mensais de aplicação automática entre DATA_INICIO e DATA_FIM. Em todos os meses, o valor da aposentadoria do INSS, recebido em conta-salário, foi automaticamente subtraído pelo banco réu sob a rubrica APLIC.INVEST FACIL, restando indisponível ao consumidor pelo prazo de X (...) a Y (...) dias até o resgate manual. Embora os valores tenham sido restituídos via RESGATE INVEST FACIL ao longo do período, o cerne do dano moral não reside na perda patrimonial líquida — inexistente —, mas na privação reiterada da autodeterminação do consumidor sobre sua própria renda alimentar, mês após mês, durante T (...) anos consecutivos. Cada retenção mensal configura, autonomamente, prática abusiva vedada pelo art. 39, inciso VI, do Código de Defesa do Consumidor, sendo a recorrência sistêmica o fato gerador do abalo extrapatrimonial."

4. **OVERRIDE de placeholders** para `valor_causa = R$ 15.000,00` e `valor_causa_extenso = "quinze mil reais"`.

5. **Pendência crítica #1 do relatório paralelo**: AUDITORIA APLIC vs RESGATE — anexar ou descrever a tabela mês-a-mês (aplicação→resgate→janela) para o procurador validar antes do protocolo.

Implementação automatizada via script `_run_<cliente>_carvalho.py` no diretório `references/` (ver caso DENIVAL como template). O script chama `aplicar_template` normalmente e depois pós-processa o DOCX via python-docx para remover/inserir parágrafos.

**Quando NÃO aplicar (b)** — exceções que reabrem (a) estrita ou (c) intermediária:
- (a) estrita: cliente realmente PERDEU dinheiro (saldo líquido positivo, valores não foram resgatados). Pleitear bruto em dobro. Cabível só quando o juízo competente é vara cível comum (sem teto JEC) ou quando o procurador opta pela renúncia ao excedente.
- (c) intermediária: há um PICO ISOLADO de retenção (ex: aplicação grande oriunda de empréstimo pessoal/PIX que demorou >7 dias para resgate integral). Pleitear repetição em dobro APENAS do pico, mantendo dano moral pela recorrência. Caso paradigma testado mas DESCARTADO pelo procurador no DENIVAL — preserva a estratégia mas alerta que a (b) é mais simples e tem maior probabilidade de procedência.

**Teto JEC sempre conferir**: 40 SM (SM-2025 R$ 1.518 → R$ 60.720). Estratégia (a) com bruto alto (ex: caso ELINALDO histórico R$ 159k) estoura facilmente. Memória `feedback_teto_jec_40sm.md` detalha as 3 opções para resolução (renúncia, vara cível, fracionamento).

### PG ELETRON — particularidades

- **Sempre 2 réus**: BANCO BRADESCO + TERCEIRO BENEFICIÁRIO
- **1 inicial por terceiro** (jamais cumular num só processo)
- **Item de pedido fixo**: ofícios ao MP Estadual e BACEN/ASPAR (intimidação processual)
- **Responsabilidade SOLIDÁRIA** (CDC arts. 7º p.ún., 14, 25 § 1º + Súmula 479 STJ)
- Pedidos pedem "Condenar **solidariamente** os Réus..."
- Geladeira (R$ XXX como PAGTO ELETRON COBRANCA GELADEIRA): provavelmente compra parcelada real, não tese — alertar antes

### Lançamento isolado (1 só)

Se uma tese tem APENAS 1 lançamento (ex.: ODONTOPREV da Terezinha — R$ 499 em 29/08/2022 único), alertar:
- Pode ser cobrança avulsa em vez de plano recorrente
- Confirmar com cliente se foi de fato indevido ou houve adesão pontual

## Pendências

- **Tesseract OCR pt-BR** ainda não está instalado nesta máquina; quando estiver, ativar leitura do RG (3 - RG.pdf) para extrair estado_civil, data_nascimento, idade
- **Bloco doutrinário do APLIC.INVEST** está parcial (só 2 subseções: serviço não solicitado + abusividade aplicações automáticas) — usuário pode complementar
- **Banco de dados de terceiros (PG ELETRON)** ainda manual; ir construindo conforme casos novos aparecem (ASPECIR PREVIDÊNCIA, MBM, ODONTOPREV já mapeados)
- **Comarcas que adotam combinação** confirmadas: Caapiranga, Presidente Figueiredo, Manacapuru — outras a confirmar com escritório

## Casos paradigma testados

| Cliente | Pasta | Tese(s) | Template | Resultado |
|---|---|---|---|---|
| José Sebastião dos Santos Silva (caso removido) | TARIFAS/ | 1 (Tarifas) | inicial-tarifas | OK |
| Maria Joana da Silva Soares (removida) | (root) | 3 (Tarifas + Mora + Título) | inicial-combinada | OK |
| Elinaldo Cunha dos Santos (removido) | (root) | 1 (Aplic.Invest) | inicial-aplic-invest | OK |
| Terezinha Brandão da Rocha | PGTO ELETRÔNICO DE COBRANÇA/ASPECIR | 1 (PG Eletron - Aspecir) | inicial-pg-eletron | OK |
| Terezinha Brandão da Rocha | PGTO ELETRÔNICO DE COBRANÇA/MBM | 1 (PG Eletron - MBM) | inicial-pg-eletron | OK |
| Terezinha Brandão da Rocha | PGTO ELETRÔNICO DE COBRANÇA/PLANO ODONTOLÓGICO | 1 (PG Eletron - ODONTOPREV) | inicial-pg-eletron | OK |
| Midia de Almeida (06/05/2026) | PGTO ELETRÔNICO DE COBRANÇA | 1 (PG Eletron - Bradesco Vida e Prev., 3 lançamentos anuais 12/2023, 12/2024, 12/2025) | inicial-pg-eletron | OK — autora idosa, KIT ignorado, extrato Bradesco escaneado renderizado via pymupdf get_pixmap |

> Para o status do batch corrente `APP-BRADESCO\0. TESTE 1` (clientes processados vs pendentes), ver `~/Documentos/Obsidian Vault/Modelos/IniciaisBradesco/_checkpoint-sessao.md`.

## Cadência de atualização do checkpoint do vault

**Não** atualizar `_checkpoint-sessao.md` a cada cliente processado. Atualizar caso a caso adiciona overhead pesado de leitura/edição do vault entre os clientes e atrasa o batch (feedback do usuário em 06/05/2026).

Atualizar APENAS nestes momentos:

1. **Fechamento do batch** — quando todos os clientes da pasta foram processados (ou quando o usuário interromper o batch). Consolidar em UMA edição todos os clientes desde o último checkpoint, com seções de caso paradigma agrupadas.
2. **A cada ~3–5 clientes processados em batches grandes** (10+ clientes), como ponto de salvaguarda intermediário caso a sessão caia.
3. **Quando o usuário pedir explicitamente** (`atualiza o checkpoint`).
4. **Quando descobrir aprendizado estrutural novo** (ex.: erro novo da skill, padrão jurisprudencial inédito) — esse tipo de aprendizado vale checkpoint imediato porque alimenta a próxima sessão e a memória global.

Durante o processamento dos clientes, manter apenas resumo curto em texto na resposta ao usuário (cliente, tese, valor da causa, status). O detalhamento do caso paradigma (qualificação completa, pendências, raciocínio jurídico) entra no relatório paralelo `_RELATORIO_PENDENCIAS_*.docx` da própria pasta do cliente, não no checkpoint do vault.

Quando o checkpoint for atualizado em lote, agrupar por dia (`## Casos paradigma — DD/MM/YYYY`) e listar cada cliente como subseção `### NOME` com 3–5 linhas (não as 15+ linhas que cada caso tem hoje). Aprendizados estruturais vão em seção própria `## Aprendizados desta sessão` no fim.

## Notas de operação adicionais (lições aprendidas)

### Extratos Bradesco escaneados (sem text-layer)

Extratos baixados de algumas agências vêm como PDF de imagens (sem camada
de texto). `pymupdf doc[i].get_text()` retorna string vazia. Para extrair
conta/agência e renda real, **SEMPRE usar o helper** `render_paginas_pdf`
(em `_pipeline_caso.py`), nunca chamar `get_pixmap(dpi=...)` direto:

```python
from references._pipeline_caso import render_paginas_pdf
import fitz
doc = fitz.open(extrato_path)
n = len(doc)
paginas = sorted({1, 2, n-2, n-1, n})  # 1-indexed, sem repetir, sem inválidos
render_paginas_pdf(extrato_path, paginas, '_tmp_pages')  # PNGs ≤ 1800px
# então usar a leitura visual nativa do Claude (Read PNG)
```

**REGRA CRÍTICA — limite de 2000px do Claude.** Em sessões com várias
imagens, o Claude rejeita qualquer PNG cuja maior dimensão passe de 2000px
("An image in the conversation exceeds the dimension limit for many-image
requests"). DPI 180 em A4 vertical gera ~2104px e estoura o limite. Por
isso o helper `render_paginas_pdf` agora clampa a maior dimensão em
`max_dim=1800` (200px de margem) automaticamente, calculando o zoom a
partir de `page.rect`. NUNCA chamar `doc[i].get_pixmap(dpi=180)` direto —
sempre passar pelo helper, ou replicar a lógica de clamp via
`fitz.Matrix(zoom, zoom)` com `zoom = min(dpi/72, max_dim/max(w_pts, h_pts))`.

`pdftoppm` NÃO está disponível na máquina do escritório — não confiar nele.
A primeira página costuma trazer Agência/Conta/Nome no cabeçalho; a
ÚLTIMA página tem os créditos INSS mais recentes (aplicar a regra § 1).
Limpar a pasta `_tmp_pages/` ao final.

### Cobrança ANUAL — padrão típico de seguro/previdência

Quando a tabela traz APENAS 1 lançamento por ano (ex.: 27/12/2023,
02/12/2024, 01/12/2025) é cobrança anual de seguro de vida ou produto
previdenciário — apólice anual. NÃO é sinal de erro de extração; é o modus
operandi do produto. Sinalizar no relatório paralelo para o procurador
confirmar com o cliente: nunca recebeu apólice, nunca renovou, nunca
recebeu proposta. Esse é o ponto que o banco mais explora em contestação.

### INSS líquido vs renda bruta

Quando o crédito INSS no extrato vem com valor muito reduzido (R$ 800–950),
provavelmente já está líquido após consignações descontadas pelo próprio
INSS. A renda BRUTA do benefício é maior. Adotar o valor do extrato como
`valor_remuneração` (regra § 1) mas SINALIZAR no relatório paralelo para o
procurador conferir HISCON e ajustar se necessário (pode mudar a tese de
hipossuficiência ou reforçar o impacto do dano moral).

## Erros recorrentes a evitar

1. **Hardcode de renda** — bug detectado e corrigido. Sempre extrair do extrato.
2. **Hardcode de valor de descontos** — bug detectado nos templates (R$ 632, R$ 316, R$ 37,02, R$ 961,01). Corrigido. Sempre auditar pós-geração.
3. **Confundir TOTAL agregado da tabela** com total da tese isolada — TOTAL no rodapé da tabela soma TODAS as cobranças; para 1 tese isolada, somar APENAS os lançamentos daquela rubrica.
4. **Tudo em Segoe UI Bold na qualificação** — bug detectado e corrigido. Usar 2 (ou 5) runs separados.
5. **Rubrica sem formatação completa** — só amarelo é insuficiente. Aplicar caps + bold + italic + underline + amarelo.
6. **{{titulo}} com 1 só rubrica quando há múltiplas** — bug detectado. Listar TODAS separadas por " / ".
7. **Variantes de rubrica não capturadas** — bug detectado (CAPS sem ponto, ordem invertida). Mapear todas as 4 variantes (curta/completa × normal/CAPS).
8. **APLIC.INVEST somando aplicações sem subtrair resgates** — alerta crítico, pode gerar valor 100x maior do que o prejuízo real.
9. **PG ELETRON cumulando vários terceiros num processo** — proibido, 1 inicial por terceiro.
10. **`get_pixmap(dpi=180)` direto em A4 → estouro do limite de 2000px do Claude** — DPI 180 em página A4 vertical gera ~2104px e o Claude rejeita a imagem com "An image in the conversation exceeds the dimension limit for many-image requests". Sempre usar o helper `render_paginas_pdf` (que clampa a maior dimensão em 1800px via `fitz.Matrix(zoom, zoom)` com `zoom = min(dpi/72, max_dim/max(w_pts, h_pts))`).
11. **`Read` direto em PDF > 30MB → erro "Request too large (max 32MB)"** — RGs e extratos escaneados em alta resolução podem passar de 32MB e o tool `Read` rejeita o arquivo inteiro. Antes de ler PDF, conferir tamanho via `os.path.getsize(p)`. Se ≥ 30 MB, NUNCA usar `Read` direto — renderizar página a página com `render_paginas_pdf` (clampado em 1800px) e ler os PNGs gerados, OU extrair só o texto via `fitz.open(p)[i].get_text()` quando há text-layer. Helper canônico: `ler_pdf_seguro(path)` em `_pipeline_caso.py` (escolhe o caminho automaticamente).
12. **`Read` paralelo de múltiplos PDFs do mesmo cliente OU acúmulo de contexto em batch grande → erro "Prompt is too long"** — disparar 3+ `Read` de PDFs do cliente no mesmo turno (notificação + RG + extrato + tabela) infla a request acima do limite de tokens de entrada do modelo, mesmo quando cada PDF tem só algumas centenas de KB. O efeito agrava em batches com 4+ clientes processados em sequência: o contexto principal acumula PDFs já lidos + DOCX gerados + relatórios, e a próxima request começa apertada antes mesmo do `Read`. **Regras**: (a) ler PDFs do cliente em SÉRIE — um `Read` por turno, nunca 3+ em paralelo; (b) para batches com 5+ clientes, despachar UM SUBAGENTE por cliente (Agent tool) que recebe só o caminho da pasta e devolve `{caminho_inicial.docx, caminho_relatorio.docx, resumo}`, mantendo o contexto principal limpo; (c) checar tamanho via `os.path.getsize(p)` antes do `Read` — paralelo só quando soma estimada < 8 MB. Aconteceu na sessão de 06/05/2026 ao processar a 4ª–5ª cliente do batch `0. TESTE 1` (RAIMUNDA RODRIGUES) lendo notificação + RG + extrato em paralelo. Helper canônico: `ler_docs_cliente_seguro(paths)` em `_pipeline_caso.py` (que serializa automaticamente quando a soma estimada estoura).

## Estrutura física

```
~/.claude/skills/inicial-bradesco/
├── SKILL.md                    # esta documentação
├── README.md                   # visão geral
├── references/
│   ├── helpers_docx.py         # substituição run-aware preservando rPr + Cambria + grifos + formatação rubrica
│   ├── extrator_documentos.py  # parsers PDF (notificação, tabela, extrato — incluindo extrair_renda_real)
│   ├── classificador.py        # detecta teses ativas pelas tabelas/rubricas
│   ├── auditor.py              # auditoria pós-geração de valores hardcoded
│   ├── extenso.py              # wrapper num2words pt-BR
│   └── catalogo_teses.md       # mapa canônico tese → rubrica → template
└── tests/
    └── (futuras fixtures)

~/Documentos/Obsidian Vault/Modelos/IniciaisBradesco/
├── _MOC.md                     # mapa de conteúdo
├── estrutura-padrao.md         # esqueleto comum dos templates
├── regras-de-adaptacao.md      # já existe (atualizar)
├── erros-herdados.md           # bugs detectados e correções
├── checklist-protocolo.md      # conferência pré-protocolo
├── _templates/                 # 6 templates (já existe)
└── teses/
    ├── tarifas.md
    ├── mora-encargo.md
    ├── aplic-invest.md
    ├── titulo-capitalizacao.md
    └── pg-eletron.md

# Pasta de cliente (típica)
.../Clientes/<NomeCliente>/
├── KIT/                        # ignorada
├── 3 - RG.pdf
├── 5 - COMPROVANTE DE RESIDÊNCIA.pdf
├── 5.1 - DECLARAÇÃO DE DOMICÍLIO.pdf
├── 6 - EXTRATOS.pdf
├── 7 - TABELA <RUBRICA>.pdf    # 1 ou mais
├── 8 - NOTIFICAÇÃO.pdf
├── INICIAL_<TESE>_<NOME>.docx              # gerado
└── _RELATORIO_pendencias_<TESE>.docx       # gerado
```

## Pré-requisitos

- Python 3.10+ com `pymupdf` (`pip install pymupdf`), `python-docx` (`pip install python-docx`), `lxml` (`pip install lxml`), `num2words` (`pip install num2words`)
- Vault Obsidian em `~/Documentos/Obsidian Vault/Modelos/IniciaisBradesco/_templates/` com os 6 DOCX
- (opcional) Tesseract OCR + pacote pt-BR para extração de RG escaneado

## Como invocar

Em qualquer chat do Claude Code:

```
Faz a inicial do <NOME DO CLIENTE> que está na pasta <PATH>
```

ou

```
/inicial-bradesco <PATH>
```

O Claude lê esta SKILL.md, segue o pipeline, gera DOCX + relatório paralelo na pasta do cliente.

## Limites (não use para)

- RMC/RCC com vício de consentimento → existe outra skill: `replica-rmc`
- Réplicas à contestação → existe outra skill: `replica-nao-contratado`
- Apelações → outra skill
- Casos onde o cliente reconhece a contratação (cenário diverso)
