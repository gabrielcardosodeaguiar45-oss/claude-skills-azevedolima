# Changelog — kit-juridico

## v2.2 — 2026-05-11 (atual)

### Padronização de nomes de arquivos

Aplicada após processamento de 5 clientes do Elizio (caso paradigma — 5 pastas com PDFs misturados detectados manualmente). Mudanças no naming dos PDFs gerados pelo pipeline:

- **Após número: PONTO (não hífen)**: `2.` em vez de `2-`. Inclui:
  - `2. Procuração …`
  - `3. RG e CPF.pdf`
  - `4. Declaração de hipossuficiência.pdf`
  - `5. Comprovante de residência.pdf`
  - `6. Histórico de empréstimo.pdf`
  - `7. Histórico de pagamento.pdf`
- **Entre campos do nome do arquivo: TRAVESSÃO (`–`)** em vez de hífen ASCII (`-`).
  - Antes: `2- Procuração - Banco BMG - Contrato 15076520.pdf`
  - Depois: `2. Procuração – Banco BMG – Contrato 15076520.pdf`
- **Subdocumentos por pessoa: separador `<espaço>-<espaço>` + nome completo** ao fim:
  - `3.1 - RG e CPF do rogado - NOME COMPLETO.pdf`
  - `3.2 - RG e CPF da testemunha 1 - NOME COMPLETO.pdf`
  - `3.3 - RG e CPF da testemunha 2 - NOME COMPLETO.pdf`
  - `5.1 - Declaração de domicílio - NOME DO DECLARANTE.pdf`
  - `5.2 - RG do declarante terceiro - NOME.pdf`

A função `_nome_doc_comum(tipo, nome_pessoa='')` agora aceita o nome opcional. Quando o caller não souber o nome (caso atual do pipeline), o nome é omitido — backward-compatible.

### Próximos passos
- Caller (`fase_f_montar_estrutura`) precisa receber os nomes do rogado/testemunhas e propagar para `_nome_doc_comum`. Hoje os nomes ficam genéricos quando o pipeline não tem essa info.

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
