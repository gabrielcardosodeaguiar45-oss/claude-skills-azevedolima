---
name: notificacao-extrajudicial
description: Gera notificações extrajudiciais bancárias (RMC, RCC, consignado-não-contratado, Bradesco-encargos/tarifas/capitalização/pagamento-eletrônico) a partir de templates DOCX com placeholders canônicos. Suporta versão COM-escritório (logo Tiago/Eduardo) e SEM-escritório (Patrick/Gabriel/Alexandre, timbrado neutro).
license: Proprietary — De Azevedo Lima & Rebonatto
---

# Skill: notificacao-extrajudicial

Gera notificações extrajudiciais bancárias preenchidas a partir de templates DOCX com placeholders. O fluxo padrão é: **carregar `_estado_cliente.json`** → **selecionar tese** → **substituir placeholders** → **salvar DOCX final**.

## Teses suportadas (7)

| Slug | Subtítulo | Versões | Hipótese de uso |
|---|---|---|---|
| `consignado-nao-contratado` | "Empréstimo Não Contratado" | COM (Tiago AL) + SEM (Patrick AM) | Cliente descobriu desconto no INSS de empréstimo que jamais contratou |
| `rmc` | "Cartão de Crédito RMC" | COM (Tiago AL) + SEM (Patrick AM) | Cliente foi induzido a aderir a Reserva de Margem Consignável em vez de empréstimo |
| `rcc` | "Cartão de Crédito RCC" | COM (Tiago AL) + SEM (Patrick AM) | Cliente foi induzido a aderir a Reserva de Cartão Consignado |
| `bradesco-encargos` | "Descontos indevidos de encargos" | **SEM apenas** (Patrick AM) | Encargos "MORA CRED PESS" / "ENC LIM CRED" sem contrato — protocolada só no AM |
| `bradesco-tarifas` | "Descontos indevidos de tarifas" | **SEM apenas** (Patrick AM) | Tarifas bancárias sem contrato (IRDR 0005053-71 TJAM) — protocolada só no AM |
| `bradesco-capitalizacao` | "Descontos indevidos de título de capitalização" | **SEM apenas** (Patrick AM) | Título de capitalização não contratado — protocolada só no AM |
| `bradesco-pe` | "Descontos a título de Pagamento Eletrônico" | **SEM apenas** (Patrick AM) | "PAGTO ELETRON COBRANÇA *" — terceiros (EAGLE, ASPECIR, etc.) — protocolada só no AM |

> **Nota:** As 4 teses Bradesco (encargos, tarifas, capitalização, PE) só têm versão SEM-escritório porque essas pretensões são protocoladas exclusivamente pelo Patrick no AM. Não há demanda de versão COM-logo Tiago/Eduardo para essas teses.

## Dossiê de notificação (gravado 13/05/2026)

Toda notificação gerada pela `_run_notificacoes.py` agora sai dentro de uma **subpasta dedicada por banco** já com todos os documentos de instrução prontos para envio extrajudicial:

```
<pasta_acao>/notificacao/
└── BRADESCO/
    ├── Notificação Extrajudicial - BRADESCO - CONSIGNADO-NAO-CONTRATADO.docx
    ├── OAB TIAGO.pdf                              ← assinatura do procurador
    ├── 2- Procuração - Contrato 0123471622742.pdf ← procurações dos contratos do banco
    ├── 2- Procuração - Contrato 0123471622766.pdf
    ├── 2- Procuração - Contrato 016178952.pdf
    ├── 3- RG e CPF.pdf                            ← identidade do cliente
    ├── 6- Histórico de empréstimo (grifado).pdf   ← HISCON
    └── 7- Histórico de pagamento.pdf              ← HISCRE
```

> **REGRA OPERACIONAL (gravada 13/05/2026, Gabriel):** o dossiê extrajudicial NÃO inclui declaração de hipossuficiência nem comprovante de residência — esses ficam reservados para a inicial. A notificação extrajudicial só precisa demonstrar (a) identidade do notificante (RG/CPF), (b) outorga de poderes (procurações), (c) existência dos descontos (HISCON + HISCRE) e (d) qualificação do procurador (OAB).

**Cadastro de OAB** em `assets/oabs/` (PDFs das carteiras):
- `OAB TIAGO.pdf` — usado quando advogado.chave == 'tiago' (AL Federal/Estadual)
- `OAB PATRICK.pdf` — chave 'patrick' (AM Estadual)
- `OAB GABRIEL.pdf` — chave 'gabriel' (BA Federal)
- `OAB ALEXANDRE.pdf` — chave 'alexandre' (MG Estadual, SE)
- `OAB EDUARDO.pdf` — chave 'eduardo' (outras situações)

**Função `montar_dossie_notificacao`** em `_run_notificacoes.py`:
1. Copia a OAB do procurador (mapeada por `advogado.chave` → `OAB_PDF_POR_PROCURADOR`)
2. Filtra as procurações da pasta_acao pelos números dos contratos do banco (regex no nome do arquivo). Para litisconsórcio Bradesco + Mercantil, cada subpasta só leva as procurações relevantes ao seu banco.
3. Copia documentos pessoais e financeiros (RG, hipossuficiência, comp. residência, HISCON grifado, HISCRE) que estão na pasta_acao.

Validado em 13/05/2026: CICERO (Bradesco 9 docs anexos + Mercantil 7 docs anexos), bath completo de 14 clientes.

## Estrutura de arquivos

```
notificacao-extrajudicial/
├── SKILL.md                              ← este arquivo
├── assets/
│   ├── __BASE_com-escritorio__*.docx     ← bases originais Tiago/Eduardo (com logo)
│   ├── __BASE_sem-escritorio__*.docx     ← bases originais Patrick/Gabriel (timbrado neutro)
│   ├── template_<slug>__com-escritorio.docx   ← templates placeholderizados COM
│   └── template_<slug>__sem-escritorio.docx   ← templates placeholderizados SEM
├── scripts/
│   └── docx_replace.py                   ← substituir_em_docx, aplicar_timbrado_neutro
├── _test_consignado.py                   ← gera testes consignado-nao-contratado
├── _test_rmc.py                          ← gera testes RMC
├── _test_rcc.py                          ← gera testes RCC
└── _test_bradesco.py                     ← gera testes Bradesco (4 teses)
```

## Como adicionar conteúdo de cliente

Os templates esperam placeholders `{{VARIAVEL}}` em MAIÚSCULAS. Vocabulário canônico documentado em
`Modelos/Notificacoes/placeholders-canonicos.md` no vault. Resumo dos principais grupos:

**Cabeçalho:** `CIDADE_ASSINATURA`, `UF_ASSINATURA`, `DATA_EXTENSO`

**Cliente:** `CLIENTE_NOME`, `CLIENTE_NACIONALIDADE_GENERO`, `CLIENTE_ESTADO_CIVIL`, `CLIENTE_PROFISSAO`, `CLIENTE_CPF`, `CLIENTE_RG`, `CLIENTE_RG_ORGAO`, `CLIENTE_LOGRADOURO`, `CLIENTE_BAIRRO`, `CLIENTE_MUNICIPIO`, `CLIENTE_UF`, `CLIENTE_CEP`, `INSCRITO_A`, `DOMICILIADO_A`

**Banco:** `BANCO_NOME_QUALIFICADO`, `BANCO_CNPJ`, `BANCO_LOGRADOURO`, `BANCO_BAIRRO`, `BANCO_MUNICIPIO`, `BANCO_UF`, `BANCO_CEP`, `NOME_BANCO_CONTRATO`

**Advogado:** `ADVOGADO_NOME`, `ADVOGADO_NOME_MAIUSCULO`, `ADVOGADO_OAB_UF`, `SEU_SUA_ADVOGADO_A`, `ESCRITORIO_ENDERECO_COMPOSTO` (resolvido por UF de atuação via `skills/_common/escritorios_cadastro.py` → matriz Joaçaba/SC + unidade de apoio: AM→Maués, AL/SE→Arapiraca, BA/ES→Salvador, MG→Uberlândia; sem hardcoded em produção)

**Específicos por tese:**
1. **Consignado/RMC/RCC:** `CONTRATO_NUMEROS`, `CONTRATO_VALOR_EMPRESTIMO`, `CONTRATO_QTD_PARCELAS`, `CONTRATO_VALOR_PARCELA`, `CONTRATO_DATA_INCLUSAO`, `CONTRATO_DATA_PRIMEIRO_DESCONTO`
2. **Bradesco-Encargos/Tarifas/Capitalização/PE:** `RUBRICAS` (os placeholders `DATA_INICIAL`, `DATA_FINAL`, `NUMERO_DESCONTOS`, `VALOR_TOTAL` foram REMOVIDOS dos templates em 13/05/2026 — o parágrafo "Tais descontos vêm ocorrendo, em síntese, no período aproximado de..." foi excluído porque o procurador prefere demonstrar os descontos diretamente via tabela anexa, sem repetir período/total em texto corrido)
3. **Bradesco-PE (terceiros):** `TERCEIRO_NOME`, `TERCEIRO_CNPJ`, `TERCEIRO_LOGRADOURO`, `TERCEIRO_BAIRRO`, `TERCEIRO_MUNICIPIO`, `TERCEIRO_UF`, `TERCEIRO_CEP`

## API programática

```python
from scripts.docx_replace import substituir_em_docx, aplicar_timbrado_neutro

# Gerar notificação para um cliente
substituir_em_docx(
    'assets/template_rmc__com-escritorio.docx',
    {
        '{{CLIENTE_NOME}}': 'JOSÉ DA SILVA',
        '{{CLIENTE_CPF}}': '000.111.222-33',
        # ... resto dos placeholders
    },
    'output/notificacao_jose.docx'
)
```

## Helpers em `scripts/docx_replace.py`

| Função | Uso |
|---|---|
| `substituir_em_docx(input, mapa, output)` | Substitui todas as ocorrências de cada chave do `mapa` (dict) no DOCX. Faz LOOP — múltiplas ocorrências do mesmo placeholder no mesmo parágrafo são todas substituídas. Limpa parágrafos vazios excessivos. |
| `aplicar_timbrado_neutro(corpo, timbrado, output)` | Pega o corpo de um template e aplica headers/footers/imagens de outro. Usado para gerar SEM a partir de COM (e vice-versa). |
| `inserir_paragrafo_antes(doc, ancora, texto, herdar_estilo_de)` | Insere parágrafo antes de uma âncora textual, herdando estilo do parágrafo anterior. |
| `padronizar_fontes(doc, corpo='Cambria', destaque='Segoe UI')` | Heurística para normalizar fontes (use só quando o BASE não vier com fontes corretas). |
| `normalizar_tema_corpo(docx_path)` | Conserta documentos cujo corpo aponta para majorFont (Calibri) em vez de minorFont (Cambria). Substitui `asciiTheme="majorHAnsi"` → `"minorHAnsi"`. |

## Geração programática vs templates manuais

A skill distingue dois momentos:

1. **Bases originais** (`__BASE_*`) — modelos reais do escritório com cliente preenchido. Servem de molde visual mas nunca são editados.
2. **Templates placeholderizados** (`template_*`) — geração automática a partir das bases via `_test_*.py`, substituindo dados específicos por `{{PLACEHOLDERS}}`. **Não editar diretamente** — regenerar via script se mudar a base.

Os scripts `_test_*.py` rodam o pipeline completo:
- Lê o BASE
- Aplica placeholderização (substitui dados reais por placeholders)
- Gera template SEM via `aplicar_timbrado_neutro()` (se BASE for COM) ou template COM (se BASE for SEM)
- Gera teste com cliente fictício para validação visual
- Reporta placeholders pendentes (= bug se houver)

## Pipeline integrado — `_run_notificacoes.py`

Implementado em 2026-05-08. Processa em batch uma pasta de clientes. Para cada cliente:

1. Carrega `_estado_cliente.json` (gerado pela skill `kit-juridico`)
2. Localiza pasta KIT (variantes: `KIT`, `0. Kit`, `Kit`)
3. Localiza procuração (heurística em ordem de prioridade):
   1. PDF "Procuração*" no KIT
   2. PDF original referenciado em `_proc_crops/manifesto.json`
   3. PNG já recortado em `_proc_crops/crop_pag_01.png` (último recurso)
4. Extrai qualificação via `extrair_qualificacao.py`:
   - Tenta text-layer; se vazio, OCR com easyOCR + rotação automática (procurações vêm escaneadas em landscape)
   - Aplica regex restrito ao **bloco OUTORGANTE** (antes de OUTORGAD[OA]S) para evitar pegar dados dos advogados
   - Tolera erros de OCR ("vlúva" → "viúva", "RG/CPF" → distingue do CPF)
5. Para cada `pastas_acao` do JSON, agrupa contratos por `(banco_chave, tese)` aplicando filtros:
   - **Banco** extraído do path (`APOSENTADORIA\BANCO BMG - RMC-RCC` → BMG); suporta litisconsórcio (`BANCO X + BANCO Y`)
   - **Benefício**: contratos com `beneficio_pasta` igual ao prefixo do path (APOSENTADORIA/PENSAO)
   - **Tipo**:
     - Path contém "RMC-RCC" → só `tipo` em `(RMC, RCC)`; tese = `rmc` ou `rcc` (decidida por contrato). Mantém Ativos + Excluídos (mesmo a margem encerrada pode ter cobranças residuais).
     - Senão → só `tipo == CONSIGNADO`; tese = `consignado-nao-contratado`.
   - **Autoridade da procuração** (regra crítica do escritório): se a `pasta_acao` contém PDFs de procuração com número de contrato no nome do arquivo (padrão `Procuração - Banco X - Contrato N.pdf`), **só esses contratos entram** na notificação. Procurações são outorgadas individualmente por contrato — listar contratos não referidos é ultra vires.
     - Estratégia primária: regex no nome do arquivo (`Contrato\s+(?:nº)?\s*(\d{6,})`)
     - Fallback: procurar `ESTUDO DE CADEIA.docx` na pasta_acao e extrair os números do texto
     - Se nenhum número encontrado, NÃO infla com "todos do banco" — gera notificação com todos os contratos do JSON apenas se não há procurações com número.
   - **Filtro de situação** aplicado SOMENTE quando NÃO há procurações específicas: para CONSIGNADO, só Ativos. Quando há procurações, todas as situações entram (a procuração já decidiu impugnar).
   - **De-duplicação**: por número de contrato; preferindo `Ativo` sobre `Excluído`
6. Para cada `(banco, tese)` resolvido, busca cadastro de banco via `bancos.py`:
   - UF da ação determina filial usada (AL → filial Maceió, AM → filial Manaus, demais → matriz)
7. Monta `mapa` completo de placeholders e chama `substituir_em_docx()`
8. Salva em `<pasta_acao>/notificacao/Notificação Extrajudicial - <banco> - <tese>.docx`

**Filtros importantes (lições aprendidas):**

- **Sem filtro de benefício** → cliente com APOSENTADORIA + PENSAO ganhava notificações com contratos misturados (errado)
- **Sem filtro de tipo** → pasta "BANCO BMG - RMC-RCC" ganhava contratos consignados normais (errado)
- **Sem de-duplicação** → JSON da `kit-juridico` pode ter o mesmo contrato listado 2 vezes (ex: vindo de páginas diferentes do HISCON), inflando a lista de contratos na notificação

**Modo piloto (testar 1 cliente):**

```powershell
$env:NOTIF_FILTRO_CLIENTE = "ANAIZA"
python _run_notificacoes.py
```

**Cadastros usados:**

- `scripts/bancos.py` — 21 bancos com matriz + filiais AL/AM/MG quando relevantes
- Advogado por UF: AL → Tiago (template COM-escritório); AM → Patrick (template SEM-escritório)

**Limitação atual:** RG/órgão expedidor frequentemente não vêm da procuração (que tem só CPF). Os campos faltantes são substituídos por marcadores `[INDICAR XXX]` (ex: `[INDICAR RG]`) para revisão manual no DOCX final.

## Bugs conhecidos da `kit-juridico` (a corrigir lá)

Encontrados rodando o pipeline em 14 clientes (2026-05-08):

1. **Duplicação de contratos no JSON** — o mesmo contrato (mesmo número, banco, benefício) aparece 2 vezes em `contratos[]`. O orchestrator do `_run_notificacoes.py` faz de-duplicação por número (preferindo `Ativo` sobre `Excluído`), mas a fonte deveria ser limpa.
2. **Pastas com whitespace ruim** — `pastas_acao[].path_relativo` ocasionalmente vem com espaços dentro de palavras: `BANCO BRADESCO FINANC IAMENT OS`, `AGIBAN K`, `BANCO MERCA NTIL DO BRASIL`. O orchestrator trata via fuzzy matching (normaliza whitespace), mas a fonte deveria gerar nomes corretos.
3. **`cliente.*`** falta CPF, RG, endereço, profissão, estado civil, gênero — daí precisamos do OCR de procuração no `_run_notificacoes.py`. A `kit-juridico` deveria já popular esses campos no JSON quando processa procurações.

## Cadastros do vault

A skill consulta o vault Obsidian em `Modelos/Notificacoes/`:

| Arquivo | Conteúdo |
|---|---|
| `_MOC.md` | Map of Content da pasta de notificações |
| `placeholders-canonicos.md` | Vocabulário fechado de placeholders |
| `teses/<slug>.md` | Texto-fonte da tese + metadados (template_docx, placeholders obrigatórios) |
| `bancos/<slug>.md` | Cadastro de cada banco (CNPJ, endereços, filiais) — *em construção* |
| `terceiros-pagamento-eletronico/<slug>.md` | Cadastro de terceiros recebedores (EAGLE, ASPECIR, etc.) — *em construção* |

## Histórico

- 2026-05-11 — Endereço do escritório deixou de ser hardcoded (`Joaçaba/SC + Arapiraca/AL` cravado para qualquer UF). Agora é resolvido em runtime via `skills/_common/escritorios_cadastro.py:montar_endereco_escritorio_completo(uf_acao)`. AM passa a usar a unidade de Maués; BA/ES Salvador; MG Uberlândia; SE compartilha Arapiraca. Aplicado em batch de 5 clientes do captador Elizio (todos AM Patrick).
- 2026-05-08 — Skill remasterizada. 7 teses suportadas (consignado-nao-contratado + rmc + rcc + 4 Bradesco). Templates COM/SEM gerados automaticamente. Bug de substituição múltipla corrigido (`substituir_em_paragrafo` agora itera enquanto encontrar match).
