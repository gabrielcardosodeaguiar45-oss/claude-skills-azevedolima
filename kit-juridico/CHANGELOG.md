# Changelog — kit-juridico

## v2.2 — 2026-05-11 (atual)

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
