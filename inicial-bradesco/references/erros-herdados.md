# Erros Herdados — Iniciais Bradesco

Catálogo dos bugs reais detectados nas iterações com casos paradigma
(José Sebastião, Maria Joana, Elinaldo, Terezinha Brandão da Rocha).
Cada erro tem causa-raiz e trava aplicada.

> **Princípio**: nunca consertar um sintoma sem entender a causa-raiz.
> Se um erro recorrer apesar da trava, abrir um item novo aqui.

---

## E01 — Cambria não aplica (fonte sai Sitka Text / Calibri)

**Sintoma**: Word abre o .docx e o texto sai em Sitka Text ou Calibri,
mesmo após substituições.

**Causa-raiz**: a fonte é definida em **três** lugares no `.docx`:
1. `word/theme/theme1.xml` (majorFont / minorFont)
2. `word/styles.xml` (rPrDefault + estilos custom do escritório)
3. inline em cada `<w:rFonts>` dos runs

Trocar só um não resolve.

**Trava**: `helpers_docx.forcar_cambria_global(buf)` aplica nos três níveis +
substitui Sitka/Calibri inline em todos os XMLs.

**Verificação**: depois de salvar, abrir XML e procurar `Sitka Text` ou
`Calibri` (com aspas). Não deve haver ocorrência.

---

## E02 — Segoe UI Bold vaza para campos que não são o nome

**Sintoma**: na qualificação, "brasileira, viúva, aposentada" sai em
Segoe UI Bold (deveria ser apenas o nome).

**Causa-raiz**: o Word herda o `rStyle="2TtuloChar"` (Segoe UI Bold) do
parágrafo de origem para o run inteiro. Quando reescrevíamos com 1 só
run, todo mundo herdava o destaque.

**Trava**: `helpers_docx.remove_caps_destaque(rpr)` apaga `<w:caps/>` e
`<w:rStyle w:val="2TtuloChar"/>` para placeholders que **não** estão em
`DESTAQUE_NOME = {nome_completo, nome_terceiro}`.

Para qualificação inteira preservar o destaque só no nome, usar
`set_paragrafo_2runs(p, nome, rpr_destaque, resto, rpr_neutro)`.

---

## E03 — Valores hardcoded sobrevivem (R$ 632, R$ 316, R$ 37,02)

**Sintoma**: documento gerado para o cliente A continha R$ 632,00 que
era do cliente B (template tinha valor literal).

**Causa-raiz**: o template original do escritório veio com valores fixos
em vários parágrafos, fora dos placeholders `{{xxx}}`. A simples
substituição de placeholders não enxergou esses casos.

**Trava**:
1. Pré-processamento: `substituir_in_run(p, mapa_padroes_literais)` para
   trechos como `R$ 632,00`, `1.250,00`, datas hardcoded, etc.
2. Pós-processamento: `auditor.auditar_docx()` faz varredura final e
   alerta se sobrou qualquer valor R$ não declarado em
   `dados_caso['valores_legitimos']`.

**Lição**: SEMPRE auditar com `auditor.py` antes de entregar.

---

## E04 — Variantes de rubrica não substituídas

**Sintoma**: na seção "Fatos" aparece `ENCARGO LIM CRED` mas no pedido
final aparece `CRED MORA PESS` (mistura de teses).

**Causa-raiz**: o template tem 5 variantes da mesma rubrica em pontos
diferentes:
- Title Case curta: "Mora Cred Pess"
- Title Case completa: "Mora Crédito Pessoal"
- CAPS curta: "MORA CRED PESS" (jurisprudência)
- CAPS completa: "MORA CRÉDITO PESSOAL" (subtítulo)
- Versão abreviada: "MORA CREDITO PESSOAL" (sem acento)

A skill antiga substituía só uma variante.

**Trava**: 4 placeholders distintos no template, conforme
`catalogo_teses.md § 6`:
- `{{rubrica_curta}}`
- `{{rubrica_curta_caps}}`
- `{{rubrica_completa}}`
- `{{rubrica_completa_caps}}`

E todos vão a `RUBRICA_FORMATADA` (caps + bold + italic + underline + amarelo).

---

## E05 — Renda mensal hardcoded (R$ 1.518,00 num caso de Terezinha)

**Sintoma**: cliente Terezinha recebe R$ 1.212,17 mas saiu R$ 1.518,00.

**Causa-raiz**: alguma versão antiga do template tinha um valor exemplar
e ele foi promovido para o gerador.

**Trava (regra crítica)**: `extrator_documentos.extrair_renda_real()`
não tem fallback hardcoded. Se não achar crédito de salário/INSS no
extrato, retorna `None` e a skill marca como pendência manual com o
texto `[A CONFIRMAR]`. NUNCA usar valor padrão.

> "Não pode, tem que colocar o valor real" — usuário, sessão Terezinha.

---

## E06 — APLIC.INVEST com saldo líquido negativo

**Sintoma**: pedi devolução em dobro de R$ 30.000 aplicado, mas o cliente
já tinha resgatado R$ 27.749. Pedido foi gerado por inteiro, sem alerta.

**Causa-raiz**: faltava auditar o extrato comparando aplicações vs
resgates. O template assumia que toda APLIC era "perda" definitiva.

**Trava**: `extrator_documentos.auditoria_aplic_invest()` calcula:
```
saldo_liquido = sum(APLICAÇÕES) − sum(RESGATES)
```

Se `saldo_liquido < 0`, **trava a geração** e apresenta 3 opções
(estrita / conservadora / intermediária) ao operador. Decisão é humana.

---

## E07 — PG ELETRON com 2 réus em Segoe UI Bold

**Sintoma**: no parágrafo de qualificação dos réus, "BANCO BRADESCO" e
"ASPECIR" saíam em Segoe UI Bold, **mas também todo o resto** ("CNPJ X,
inscrita..., neste ato representada...").

**Causa-raiz**: mesma raiz de E02, mas agora em parágrafo com 2 réus.
A solução de 2-runs não dá conta — precisa de 5 runs:
- Run 1: nome do banco (destaque)
- Run 2: ", inscrita no CNPJ ..." (neutro)
- Run 3: "; e " (neutro)
- Run 4: nome do terceiro (destaque)
- Run 5: ", inscrita no CNPJ ..., com endereço..." (neutro)

**Trava**: `set_paragrafo_2runs` foi generalizado para N runs. O gerador
da inicial PG ELETRON monta a estrutura explicitamente.

---

## E08 — Pasta KIT lida indevidamente

**Sintoma**: skill leu RG do filho do cliente (que estava na pasta KIT
como contato de emergência) ao invés do RG do cliente.

**Causa-raiz**: `os.listdir` recursivo enxergou tudo.

**Trava**: `classificador.PASTAS_IGNORAR = {KIT, 0. KIT, 0_KIT, 0. Kit}`
e `listar_documentos()` salta esses diretórios.

---

## E09 — Estilo `font-claude-respon` vazado de chat

**Sintoma**: aparecia `style="font-claude-respon"` ou similar em alguns
parágrafos do .docx final.

**Causa-raiz**: copiar/colar de janela de chat trouxe estilo proprietário
da claude.ai. Acumulou nos templates antigos.

**Trava**: substituição cega de `font-claude-respon` → `1Pargrafo` no
pipeline `forcar_cambria_global`. Lista de estilos custom em
`helpers_docx.ESTILOS_CUSTOM`.

---

## E10 — Mora vs Mora+Encargo tratados como 2 teses

**Sintoma**: caso com Mora + Encargo cobrava dano moral 2× R$ 5.000
(combinada) ao invés de R$ 15.000 (1 tese).

**Causa-raiz**: o IRDR 0004464-79.2023.8.04.0000 do TJAM consolidou que
mora e encargo de limite de crédito são **uma só tese**.

**Trava**: `classificador.RUBRICA_PARA_TESE` mapeia ambas para `MORA`.
Quando ambas presentes, vai para `inicial-mora-encargo.docx` com placeholders
separados, mas **dano moral fixo R$ 15.000**.

---

## E11 — Nome do autor em CAPS vazado para outro caso

**Sintoma**: no .docx do cliente A apareceu o nome do cliente B em
CAIXA ALTA num parágrafo qualquer.

**Causa-raiz**: o template foi copiado a partir de um caso anterior
com algum nome literal embutido.

**Trava**: `auditor.auditar_docx()` lê todos os trechos em CAIXA ALTA
de 8+ letras e compara com a whitelist (`PADROES_OK_NOME`). Se sobrar
algum nome inesperado, alerta.

---

## E12 — CNPJ desconhecido sobrevive

**Sintoma**: PG ELETRON com terceiro X mas no .docx aparece CNPJ do Y.

**Causa-raiz**: template anterior tinha CNPJ literal.

**Trava**: `auditor.CNPJS_CONHECIDOS` lista entidades fixas (Bradesco,
escritório). Qualquer CNPJ fora dessa lista que **não esteja** em
`dados_caso['cnpjs_legitimos']` (passados explicitamente pelo gerador)
gera alerta.

---

## E13 — Datas suspeitas

**Sintoma**: datas no documento não correspondiam às datas reais dos
descontos detectados na tabela.

**Causa-raiz**: trechos hardcoded "DD/MM/AAAA" fora do conjunto de
descontos legítimos.

**Trava**: `auditor.auditar_docx()` compara todas as datas DD/MM/AAAA
do documento contra `dados_caso['datas_legitimas']` (extraídas do
`parsear_tabela_descontos`). Sobras geram alerta.

---

## E14 — Cambria forçada nos títulos/subtítulos (sobrescreve Segoe UI)

**Sintoma**: o modelo do escritório usa **Segoe UI nos títulos** ("2. Título"),
**Segoe UI Semibold nos subtítulos** ("3. Subtítulo", "3.1 Subtítulo
intermediário") e **Franklin Gothic Book** em "3.1 Subtítulo secundário".
Após a geração, esses textos saíram em Cambria, descaracterizando a tipografia
do escritório.

**Causa-raiz**: `helpers_docx.forcar_cambria_global` aplicava Cambria em TODOS
os estilos custom da lista `ESTILOS_CUSTOM`, sem distinguir corpo de título.
Também trocava `majorFont` do `theme1.xml` (usado por títulos) por Cambria.

**Trava**:
1. Lista dividida em duas: `ESTILOS_CORPO` (forçam Cambria) e
   `ESTILOS_TITULO_PRESERVAR` (nunca tocar).
2. `forcar_cambria_global` agora altera APENAS `<a:minorFont>` no theme
   (corpo), não `<a:majorFont>` (títulos).
3. O loop sobre `ESTILOS_CORPO` pula qualquer estilo presente em
   `ESTILOS_TITULO_PRESERVAR`.
4. As substituições cegas `Sitka Text → Cambria` e `"Calibri" → "Cambria"`
   continuam (não afetam Segoe UI nem Franklin Gothic).

> "Eu percebi que tu colocou os títulos e subtítulos em cambria. Mas tu não
> pode fazer isso, deve manter as fontes do modelo. Somente o corpo é
> cambria." — usuário, sessão TESTE 1, caso Sotero.

---

## E15 — Bloco de qualificação fica cru porque o template foi uniformizado para `{{NOME_COMPLETO}}` (UPPERCASE)

**Sintoma**: 11 iniciais Bradesco em `0. TESTE 1` saíram com nome, nacionalidade, profissão, CPF, RG, endereço completo na forma `{{NOME_COMPLETO}}, {{nacionalidade}}, ...` em vez dos dados do cliente. Tudo o que vinha **antes** desse bloco (rubrica, conta, datas, valores, comarca, renda) foi resolvido normalmente; o bloco de qualificação inteiro permaneceu cru.

**Causa-raiz**: o usuário **uniformizou os templates** (`Modelos/IniciaisBradesco/_templates/`) para padronizar `{{NOME_COMPLETO}}` em UPPERCASE. O `_pipeline_caso.montar_dados_padrao` continuou produzindo o dict com a chave `'nome_completo'` em lowercase. Em `helpers_docx.processar_paragrafo`, o lookup era **case-sensitive**:

```python
if nome not in dados:
    break  # <-- aborta o parágrafo INTEIRO!
```

Como `'NOME_COMPLETO' not in {'nome_completo': ...}`, o `break` matava a varredura do parágrafo no PRIMEIRO placeholder não encontrado. Os demais placeholders do mesmo parágrafo (que viriam depois) ficaram crus em cascata.

**Trava** (2026-05-10):
1. **Lookup case-insensitive** em `processar_paragrafo`: `dados_ci = {k.lower(): (k, v) for k, v in dados.items()}`. `{{NOME_COMPLETO}}` agora casa com `'nome_completo'` e vice-versa.
2. **Skip-on-unknown não aborta o parágrafo**: placeholder desconhecido é mascarado com sentinel ASCII (`PHL...PHR`) que não casa com `\{\{...\}\}`, restaurado para `{{xxx}}` no fim do loop. A varredura segue procurando o próximo placeholder no mesmo parágrafo.
3. **`aplicar_template(strict=True)` por padrão**: se sobrar qualquer `{{...}}` no docx final, levanta `PlaceholdersResiduaisError` E renomeia o arquivo para `*_FALHOU_PLACEHOLDERS.docx` para que ninguém protocole por engano. Mantém modo legado `strict=False` para chamadores que querem tratar manualmente.
4. **Pós-processamento `pos_processar_documento(root)`** rodando após `processar_paragrafo`, run-aware (NÃO mexe no rPr de nenhum run): (a) remove o órfão `Cédula de Identidade nº ` (texto-fixo do template) quando `{{rg}}` e `{{orgao_expedidor_prefixo}}` foram OPCIONAIS omitidos; (b) dedupica runs adjacentes com mesmo texto separados por `; ` — resolve o caso `ENC LIM CRÉDITO; ENC LIM CRÉDITO; ENC LIM CRÉDITO; MORA CRED PESS` do template MoraEncargo; (c) limpeza fina de pontuação (vírgulas duplas, espaço pós-aspas).
5. **Regressão coberta**: `tests/test_placeholders_residuais.py` com 7 cenários (case mismatch, skip-on-unknown, raise, strict=False, qualificação completa, orfão-cédula-removido, dedup-rubrica).

**Verificação**: rodar `python tests/test_placeholders_residuais.py`. Devem passar todos.

**Princípio adicional reforçado**: o motor preserva apenas o NOME COMPLETO em Segoe UI Bold (rStyle `2TtuloChar` herdado do parágrafo). Todo o resto da qualificação (nacionalidade, estado civil, profissão, CPF, RG, endereço) sai em **Cambria normal** com realce amarelo (indicador visual de campo preenchido). Quando OPCIONAIS estão vazios, são omitidos limpamente — **nunca** se substitui por "[CONFIRMAR X]" no corpo da inicial; isso vai para o relatório paralelo.

> "Faz uma revisão nessas iniciais. Por que eu encontrei elas com placeholders e não com os dados do cliente? Corrija tudo e corrija a skill para nunca mais fazer isso novamente. Isso é um erro crasso e não deve acontecer de novo." — usuário, sessão TESTE 1, 10/05/2026.

> "Novamente toda qualificação do autor ficou SEGOE UI e só o nome do autor deve ficar nessa fonte. […] Se não tem a informação, remova e consigne no relatório. Se o autor(a) não é idoso, deve tirar o I." — usuário, mesma sessão, complementando E15.

---

## E16 — Contagem de lançamentos parece errada porque o PDF do extrato está duplicado

**Sintoma**: usuário faz `Ctrl+F` no PDF do extrato e vê **47** ocorrências de "MORA"; a inicial reporta apenas **24**. À primeira vista parece bug do parser (subdimensionando 50%). Não é.

**Causa-raiz**: clientes baixam o extrato Bradesco várias vezes seguidas (segundos/minutos de diferença) pelo app e enviam todas as cópias juntas em um PDF único. Cada lançamento aparece N vezes (uma por download), inflando o contador do `Ctrl+F`.

**Caso paradigma — ANA CAROLINE SEIXAS DE SOUZA (10/05/2026)**:
- PDF de 26 páginas, 47 hits brutos de "MORA CREDITO PESSOAL"
- Estrutura: extrato Jan-Dez/2020 baixado às 11h19 (pgs 1-9) **+ baixado de novo às 11h21 (pgs 10-18)** + 2019 (pgs 19-22) + 2021 (pgs 23-24) + 2026 (pgs 25-26)
- 23 lançamentos únicos do 2020 × 2 cópias = 46 hits + 1 lançamento isolado de 2021 = 47 hits brutos
- Após dedup por `(data, contrato, valor)`: **24 lançamentos únicos** = R$ 3.554,71
- Conferência: 23 + 1 = 24 ✓

**Trava** (2026-05-10):
1. **Hierarquia obrigatória de fontes** (vide SKILL.md §5-septies):
   - Se EXISTE planilha (xlsx/csv) na pasta → usar a planilha + auditar contra extrato
   - Se NÃO existe → GERAR planilha Excel com 4 abas (Resumo / Únicos / Auditoria Duplicação / Auditoria Crua) salva na pasta
   - Se PDF é scan/foto → OCR (Tesseract) ou leitura visual nativa, NUNCA "estimar"
2. **Detecção de duplicação no PDF**: para cada página, ler cabeçalho `Data: DD/MM/AAAA - HHhMM` + `Movimentação entre: ... e ...`. Agrupar páginas por (período, hora_geracao). Se múltiplos grupos cobrem o MESMO período → duplicação confirmada.
3. **Dedup por chave** `(data, contrato, valor)`. Manter o primeiro, descartar duplicatas, REGISTRAR na aba "Auditoria Duplicação" para auditoria humana.
4. **A planilha Excel é entregável obrigatório** quando não vier do cliente. Tem que reconciliar matematicamente os 47 hits brutos com os 24 únicos (verde/vermelho na aba "Auditoria Crua") — é a prova de que a contagem está certa.

**Verificação manual**: usuário pode abrir a planilha gerada e fazer Ctrl+F na coluna "Status": tem que bater `47 = ÚNICA + DUPLICATA (descartada)`.

> "Eu dei um CTRL + F e pesquisei pela palavra 'mora' e vi 47 lançamentos. Por que tu informou 24?" — usuário, sessão TESTE 1, 10/05/2026.

> "Se tem tabela, deve seguir a tabela e fazer a auditoria no extrato bancário; se não tem tabela, você deve fazê-la em Excel; se tiver em imagem/PDF difícil de ler, deve usar Tesseract ou OCR até encontrar todos os descontos." — usuário, mesma sessão.

---

## E17 — Pasta com 2 procurações gera só 1 inicial e deixa a outra procuração orfã

**Sintoma**: a pasta de uma tese (ex.: `<CLIENTE>/ENCARGOS/`) tem 2 (ou mais) procurações `2 - PROCURAÇÃO BRADESCO ...pdf` mas a skill gerou apenas UMA inicial cobrindo a primeira. A segunda procuração fica sem peça correspondente — o cliente assinou para 2 teses e o escritório só ajuíza 1.

**Causa-raiz**: o pipeline anterior selecionava o template (mora / encargo / tarifas) baseado apenas no nome da SUBPASTA (ex.: "ENCARGOS" → `inicial-mora-encargo.docx`), sem antes contar quantas procurações existiam na pasta. Quando havia mais de uma, ele rodava o template singular para a primeira/principal e ignorava as demais.

**Caso paradigma — LUIZ PIRES (10/05/2026)**:
- Subpasta `ENCARGOS/` continha:
  - `2 - PROCURAÇÃO BRADESCO ENCARGOS LIMITE DE CRED.pdf` (família MORA)
  - `2 - PROCURAÇÃO BRADESCO SERVIÇO CARTÃO PROTEGIDO.pdf` (família TARIFAS)
- Sessão anterior gerou apenas `INICIAL_Encargo_LUIZ_v3.docx` cobrindo só ENCARGOS LIMITE.
- A procuração de SERVIÇO CARTÃO PROTEGIDO ficou orfã (24 lançamentos, R$ 239,76).
- Correção: `INICIAL_Combinada_LUIZ_v3.docx` com 2 núcleos (54 + 24 = 78 lançamentos, R$ 421,79).

**Trava** (2026-05-10):
1. **Antes de invocar qualquer runner singular** (`inicial-mora`, `inicial-encargo`, `inicial-tarifas`, `inicial-mora-encargo`), o pipeline DEVE listar `2 - PROCURAÇÃO BRADESCO *.pdf` na pasta.
2. Se `count > 1` → roteamento OBRIGATÓRIO para `_combinada_helper.gerar_combinada()` mapeando cada procuração para uma `tese`.
3. Identificação de família por nome do arquivo:
   - `MORA CRED PESS` / `ENCARGOS LIMITE DE CRED` → **MORA**
   - `TARIFA BANCÁRIA *` / `SERVIÇO CARTÃO PROTEGIDO` → **TARIFAS**
   - `TÍTULO DE CAPITALIZAÇÃO` → **TITULO**
   - `APLIC.INVEST FÁCIL` → **APLIC**
   - `PG ELETRON` / `PAGAMENTO ELETRÔNICO` → **PG_ELETRON** (não combina, sempre separada por terceiro réu)
4. Nome do arquivo final tem que conter "Combinada" (não "Encargo" ou "Mora" sozinhos), para sinalizar visualmente.
5. Planilha Excel gerada deve ter no mínimo: **Resumo** | **<RUBRICA 1>** | **<RUBRICA 2>** | **Combinado Cronológico** (com cor por família).
6. Dano moral: 1 tese isolada = R$ 15.000; **2+ teses combinadas = R$ 5.000 por tese**.

**Bug colateral corrigido junto** (`_combinada_helper.gerar_combinada`):
- Antes: chamava `aplicar_template(strict=True default)` e quebrava porque o template inicial-combinada tem placeholders de seção (`{{INICIO_BLOCO_X}}`, `{{FIM_BLOCO_X}}`, `{{BLOCO_PEDIDO_X}}`, `{{__DELETE__}}`, `{{nucleos_faticos}}`) que são processados depois via python-docx.
- Agora: helper chama `aplicar_template(..., strict=False)` e faz sua PRÓPRIA verificação final de residuais ao final do pós-processamento.
- Helper também não populava `{{rubrica_mora}}`, `{{rubrica_encargo}}` e variantes (caps/canonica) usadas na seção IRDR. Agora deriva esses valores de `teses[familia=='MORA']` automaticamente.

> "Tem quantas procurações? […] Adivinhe o erro que você cometeu." — usuário, sessão TESTE 1, 10/05/2026.

> "1. Faça e corrija isso na skill" — usuário, mesma sessão.

## Resumo de princípios

1. **Renda real do extrato** — sem fallback hardcoded.
2. **Auditoria pós-geração obrigatória** — `auditor.auditar_docx()`.
3. **Pasta KIT é off-limits** — sempre.
4. **Hierarquia de fontes** — notificação > procuração > RG > declaração > comprovante > extrato.
5. **Cambria forçada nos 3 níveis** — theme + styles + inline.
6. **Destaque Segoe UI** apenas em `nome_completo` e `nome_terceiro`.
7. **Mora+Encargo = 1 tese**, IRDR 0004464.
8. **APLIC negativo trava a geração** até decisão humana.
9. **PG ELETRON é sempre uma inicial por terceiro** — não combina.
10. **Combinação só com critérios objetivos** — comarca pequena ou valor ≤ R$ 400.
11. **Lookup de placeholder é case-insensitive e fail-fast** — qualquer `{{...}}` residual no docx final aborta a geração (E15).
12. **Hierarquia de fontes para lançamentos**: tabela cliente > planilha gerada por nós > OCR. Sempre dedupar PDF duplicado por (data, contrato, valor) e gerar planilha Excel com aba de auditoria (E16).
13. **Toda modificação em peça é grifada em amarelo** — sem exceção. O `processar_paragrafo` já faz isso para placeholders substituídos via `add_highlight()`. Para edições posteriores (pós-processamento, pente-fino, correções manuais), o run modificado também tem que receber `<w:highlight w:val="yellow"/>`. É a forma como o operador identifica visualmente o que a skill mexeu vs o que veio do template original. Se a edição NÃO for grifada, o operador não consegue auditar a peça antes do protocolo.
14. **Pasta com >1 procuração = combinada obrigatória** (E17). Antes de invocar qualquer runner singular, listar `2 - PROCURAÇÃO BRADESCO *.pdf` na pasta. Se >1 → `_combinada_helper.gerar_combinada()` com 1 tese por procuração. Nome do arquivo final contém "Combinada".
