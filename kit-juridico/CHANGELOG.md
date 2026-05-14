# Changelog — kit-juridico

## v2.4 — 2026-05-14 (tarde)

### Estrutura por benefício + tese (paradigma Guilherme — múltiplos NBs)

Cliente com 2+ benefícios INSS (aposentadoria + pensão) ganha estrutura de **3 níveis**:

```
<CLIENTE>/<BENEFÍCIO>/<TESE>/<BANCO>/[Contrato XXX/]
```

Antes (v2.3): `<CLIENTE>/<BENEFÍCIO>/<BANCO>/` — sem nível de tese.
Agora: tese (`Não contratado / RMC / RCC / Bradesco`) é nível intermediário entre benefício e banco.

Regras associadas:
- Cada contrato pertence a UM benefício, mapeado pelo HISCON respectivo.
- `_estado_cliente.json`: `contratos[i].beneficio_pasta` deve ser `APOSENTADORIA` ou `PENSAO` (sem til); `pastas_acao[i].path_relativo` no formato `BENEFÍCIO/TESE/BANCO`.
- **HISCON por benefício**: em cada pasta-banco, manter apenas o HISCON do benefício respectivo (não duplicar aposentadoria+pensão).
- HISCRE: como vem único do INSS cobrindo ambos NBs, replicar nas duas árvores.
- Colapso de `Contrato XXX/` só quando banco tem 2+ contratos no mesmo benefício; com 1 só contrato, docs vão direto na pasta-banco.

Cliente com 1 só benefício mantém estrutura simplificada `<CLIENTE>/<TESE>/<BANCO>/`.

### Validação do número de contrato (não confundir com RG)

`pipeline.py` agora documenta que o número que vai como `contrato` no JSON precisa ser EXTRAÍDO LITERALMENTE da procuração assinada — nunca presumido pelo RG, CPF, NB ou identificador interno do banco.

Caso paradigma Guilherme: kit-juridico antigo gravou `1897431-7` (que era o RG) como contrato RMC PAN. Procuração assinada do contrato real era `0229014603105`. Inicial precisou ser regenerada após auditoria.

Heurísticas que **não** devem ser fonte do número de contrato:
- RG do cliente (XXXXXXX-X)
- CPF do cliente
- NB do benefício (XXX.XXX.XXX-X)
- Identificadores internos sem o rótulo "Contrato"

### Skill `notificacao-extrajudicial` adaptada para 3 níveis

Patches em `_run_notificacoes.py:agrupar_contratos_por_banco_tese`:
- Detecta benefício pelo primeiro segmento do path (caso seja `APOSENTADORIA / PENSÃO`).
- Banco é sempre o último segmento (não mais o segundo).
- Detecta tese RMC/RCC pelo segmento intermediário do path, não só pelo nome do banco (que antes era `BANCO X - RMC-RCC`).
- Normaliza acentos para comparar `PENSÃO` com `PENSAO`.

## v2.3 — 2026-05-14

### Distinção KIT em branco × Processo assinado por sinais físicos

Paradigma: Guilherme de Oliveira Lacerda. A pasta `0. Kit/` tinha **dois**
PDFs candidatos a "kit do cliente":

- `KIT GUILHERME DE OLIVEIRA LACERDA.pdf` — template em branco gerado em
  Word, sem assinatura (0.33 MB, 14 págs, producer `Microsoft® Word 2016`,
  text-layer abundante, zero imagens raster).
- `Processo Guilherme de Oliveira Lacerda.pdf` — kit COMPLETO assinado e
  escaneado via CamScanner (12.69 MB, 22 págs, producer
  `intsig.com pdf producer`, text-layer vazio, 6 imagens raster).

A heurística antiga (`["kit", "assinad"]`) classificava o template em
branco como `KIT_ASSINADO` só porque o nome continha "kit" — gerando kit
errado em todas as pastas-banco do cliente.

**Solução:** novo helper `score_kit_assinado(path)` em `pdf_utils.py` que
calcula score -100..+100 por sinais físicos (producer/creator de scanner
vs editor, text-layer, imagens raster, tamanho, nome). Score ≥50 →
ASSINADO; ≤-30 → MODELO; entre → AMBIGUO.

Integrado em `_sugerir_tipo_pdf`: para PDFs com "kit" ou "processo" no
nome, consulta `score_kit_assinado` antes do match por keyword. E em
`fase_b_classificar_pdfs`: quando há múltiplos `KIT_ASSINADO` na mesma
pasta, o de menor score é REBAIXADO a `KIT_MODELO` (intacto fisicamente,
apenas não usado como fonte).

Validação Guilherme:
- KIT em branco → score `-100`, classificação `MODELO`.
- Processo escaneado → score `+100`, classificação `ASSINADO`.

Nenhum arquivo é movido ou excluído. O PDF rebaixado permanece em
`0. Kit/`, apenas sai do fluxo de extração.

## v2.2 — 2026-05-11

### Padronização de nomenclatura (paradigma 5 clientes Elizio)

Mineração dos erros encontrados no batch de 5 clientes do captador Elizio
(ADALTO, ALBERTO, ALDENICE, ANDRE, ALEX) produziu três classes de ajuste.

**Separadores fixados em três caracteres distintos:**
- `.` (ponto) sempre depois do número de ordem: `2. `, `3. `, `3.1 `, `5.1 `
- `–` (travessão / en-dash U+2013) entre campos da procuração: `2. Procuração – Banco – Contrato N.pdf`
- `-` (hífen comum U+002D) entre descritor e nome próprio de subdocumento: `3.1 - RG e CPF do rogado - NOME COMPLETO.pdf`

Antes da v2.2 a skill usava hífen colado após o número (`2-`, `3-`, `3.1-`)
e hífen entre campos da procuração. O Mac (paradigma 2026-05-11) consolidou
o esquema atual e o pipeline.py já gera neste formato.

**Renomeações semânticas:**
- `7- Histórico de pagamento.pdf` → `7. Histórico de créditos.pdf`. Adere à terminologia INSS (HISCRE = Histórico de Crédito).
- `5.1- Declaração de residência de terceiro.pdf` → `5.1 - Declaração de domicílio.pdf`. Adere à terminologia CC art. 70. Conteúdo é o mesmo (declaração assinada por terceiro confirmando residência).

**Subdocumentos com NOME COMPLETO obrigatório:**
- 3.1, 3.2, 3.3 (rogado, testemunha 1, testemunha 2) e 5.2 (RG do declarante terceiro) devem terminar com ` - NOME COMPLETO` extraído do RG/CNH.
- O pipeline cria os arquivos com nome genérico (`3.1 - RG e CPF do rogado.pdf`); o agente renomeia após extrair o nome.

**Avisos novos adicionados às references:**
- `regras-imagens.md` §1.1 — armadilha CIN moderna: frente + verso são do MESMO titular; não confundir filiação no verso com CIN de outra pessoa (caso ADALTO/Francisca).
- `regras-validacao.md` §6.1 — armadilha KIT compactado mal fatiado: conferir conteúdo página a página depois do fatiamento (caso ADALTO/ALBERTO/ALDENICE — contratos de honorários e RGs de testemunhas trocados nos PDFs numerados).

**Skill irmã afetada:**
- `notificacao-extrajudicial`: deixou de hardcodar endereço Joaçaba/SC + Arapiraca/AL. Passa a usar `skills/_common/escritorios_cadastro.py:montar_endereco_escritorio_completo(uf_acao)`. AM agora usa Maués; BA/ES Salvador; MG Uberlândia.

---

## v2.1 — 2026-05-08

### `_estado_cliente.json` — dossiê compartilhado entre skills

Adicionada Fase 12.5: ao final do pipeline, salva dossiê JSON único na
raiz da pasta do cliente. Servirá de insumo para `notificacao-extrajudicial`
e `inicial-*` sem reextração.

**Novos arquivos:**
- `references/regras-estado-cliente.md` — schema v1.0 documentado

**Novas funções em `pipeline.py`:**
- `fase_k_salvar_estado_cliente(...)` — cria/atualiza JSON, preserva campos de outras skills
- `fase_k_carregar_estado_cliente(...)` — usado pelas skills downstream

---

## v2.0 — 2026-05-08

### Reescrita completa.

**Mudanças estruturais:**
- Layout `BENEFÍCIO/BANCO/` quando cliente tem >1 NB INSS (Anaiza paradigma)
- Numeração canônica unificada: 0. Kit, 2-, 3-, 3.1, 3.2, 3.3, 4-, 5-, 5.1, 5.2, 6-, 7-, 8-, ESTUDO.docx
- Pasta `0. Kit/` sempre criada e absorve TODOS os originais residuais
- Regra "1 banco = 1 ação" exceto quando há cadeia inter-banco (portabilidade), aí agrupa

**Capacidades novas:**
- Parser HISCON robusto com regex (suporta múltiplos benefícios)
- Detector de cadeias: REFIN_DIRETO 1→1, CONSOLIDAÇÃO N→1, FRACIONAMENTO 1→N, PORTABILIDADE_INTER_BANCO, SUBSTITUIÇÃO_BANCO (RMC/RCC), CADEIA_RECURSIVA
- Grafo de componentes conectados (cada componente = 1 pasta de ação)
- Grifo colorido por cadeia no extrato (paleta de 6 cores rotativa)
- ESTUDO DE CADEIA - Banco.docx por pasta (diagrama, tabelas, fundamentação)
- Cruzamento procuração × HISCON com Levenshtein (exato/aproximado/não localizado)
- Módulo de aprendizado de manuscritos (`aprendizado/captadores/`, `correcoes.md`, `padroes-bancos.md`)
- Pendências.xlsx só gera se houver alertas de fato
- Workaround do bug PyMuPDF + paths Unicode no Windows (stream em vez de filename)

**Tecnologia:**
- PyMuPDF 1.x (substitui PyPDF2)
- python-docx
- openpyxl
- OpenCV opcional (com fallback PIL) pra processamento de imagens

**Cobertura testada:**
- Cliente Anaiza (paradigma): 22 procurações, 2 benefícios, 7 cadeias detectadas
- Maria Celina: 2 procurações, 1 benefício, SUBSTITUIÇÃO_BANCO
- Marinete: 9 procurações, 2 benefícios, CONSOLIDAÇÃO 3→1 detectada
- Alice/Antonio/Lourdes (cenário "do zero"): 5/12/15 procurações manuscritas, fluxo SEM HISCON

**Próximos passos integrados:**
- `notificacao-extrajudicial` (skill irmã, em desenvolvimento) — gera notificação por banco
- `inicial-nao-contratado` / `inicial-bradesco` (skills existentes) — gera petição inicial

---

## v1.0 — versão legacy (preservada em `_legacy/`)

Skill original baseada em PyPDF2, sem detecção de cadeias, sem multi-benefício,
sem aprendizado de manuscritos. Mantida em `_legacy/` para referência.
