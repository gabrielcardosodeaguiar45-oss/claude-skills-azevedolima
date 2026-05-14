# Catálogo Canônico de Teses — Iniciais Bradesco

Mapa de cada **rubrica** do extrato → **tese jurídica** → **template** no vault.
Referência única para a skill `inicial-bradesco`. Tudo aqui passa por
`classificador.py` antes de virar template.

---

## 1. Tabela mestra (rubrica → tese → template)

| Rubrica no extrato | Padrão "7 - TABELA" | Tese | Template |
|---|---|---|---|
| `TARIFA BANCARIA` | `7 - TABELA TARIFA*.pdf` | TARIFAS | `inicial-tarifas.docx` |
| `CESTA B.EXPRESSO` | `7 - TABELA CESTA*.pdf` | TARIFAS | `inicial-tarifas.docx` |
| `CARTAO CREDITO ANUIDADE` | `7 - TABELA CARTÃO CRÉDITO ANUIDADE.pdf` | TARIFAS | `inicial-tarifas.docx` |
| `MORA CRED PESS` (isolada) | `7 - TABELA MORA.pdf` | MORA | `inicial-mora.docx` |
| `ENC LIM CRED` (isolada) | `7 - TABELA ENCARGO.pdf` | MORA | `inicial-mora.docx` |
| `MORA CRED PESS` + `ENC LIM CRED` (juntas) | `7 - TABELA MORA E ENCARGO.pdf` (ou 2 PDFs) | MORA (1 só tese p/ IRDR 0004464) | `inicial-mora-encargo.docx` |
| `APLIC.INVEST FACIL` | `7 - TABELA APLIC*.pdf` | APLIC | `inicial-aplic-invest.docx` |
| `TITULO DE CAPITALIZACAO` | `7 - TABELA TÍTULO DE CAPITALIZAÇÃO*.pdf` | TITULO | `inicial-combinada.docx` (placeholder) |
| `PAGTO ELETRON COBRANCA <X>` | `7 - TABELA PG ELETRON*.pdf` | PG_ELETRON | `inicial-pg-eletron.docx` |

---

## 2. Mora vs Mora + Encargo (regra crítica)

A IRDR **0004464-79.2023.8.04.0000** (TJAM) consolidou que **mora e encargo
de limite de crédito constituem 1 só tese**. Por isso:

| Cenário | Template | Placeholders |
|---|---|---|
| Apenas `MORA CRED PESS` | `inicial-mora.docx` | usa `rubrica_curta = "Mora Cred Pess"` (Title Case) e `rubrica_curta_caps = "MORA CRED PESS"` |
| Apenas `ENC LIM CRED` | `inicial-mora.docx` | usa `rubrica_curta = "Enc. Lim. Crédito"` e `rubrica_curta_caps = "ENC LIM CRED"` |
| Ambas | `inicial-mora-encargo.docx` | usa duas rubricas separadas no fluxo dos fatos, mas trata como 1 só tese no pedido |

> Em qualquer caso, citar IRDR 0004464.

---

## 3. Combinação de teses (≥ 2 teses ativas)

```
deve_combinar(teses, comarca, valores) = True  se:
   • comarca ∈ {Caapiranga, Presidente Figueiredo, Manacapuru}
   • OU dobro de qualquer tese ≤ R$ 400,00
   • OU soma dos dobros ≤ R$ 400,00
```

| Resultado | Template |
|---|---|
| Combinar | `inicial-combinada.docx` (1 só processo) |
| Não combinar | gera N iniciais (1 por tese) usando os respectivos templates isolados |

---

## 4. PG ELETRON — particularidades

Sempre **1 inicial por terceiro réu** (não combina mesmo com várias rubricas).
Litisconsórcio passivo: Bradesco + Terceiro (`{{nome_terceiro}}`,
`{{cnpj_terceiro}}`, etc.). Solidariedade pelo CDC (arts. 7º p.ún., 14, 25 §1º).

Exemplos catalogados (Terezinha Brandão da Rocha):

| Terceiro | CNPJ | Rubrica PG ELETRON |
|---|---|---|
| ASPECIR PREVIDÊNCIA | 33.067.626/0001-83 | `PAGTO ELETRON COBRANCA ASPECIR` |
| MBM PREVIDÊNCIA COMPLEMENTAR | 92.892.256/0001-79 | `PAGTO ELETRON COBRANCA MBM PREV. COMP.` |
| ODONTOPREV | 58.119.199/0001-51 | `PAGTO ELETRON COBRANCA PLANO ODONTOLÓGICO` |

---

## 5. APLIC.INVEST FÁCIL — auditoria obrigatória

Antes de gerar a inicial, rodar `auditoria_aplic_invest()` no extrato:

```
saldo_liquido = sum(APLICAÇÕES) − sum(RESGATES)
```

Se `saldo_liquido < 0`, **alerta vermelho**: cliente recebeu mais do que aplicou.
Apresentar ao usuário 3 opções de tese:

1. **Estrita**: pedir a devolução de tudo que foi APLICADO (mais agressiva, vulnerável a alegação de enriquecimento ilícito)
2. **Conservadora**: pedir apenas a parcela líquida retida (saldo positivo)
3. **Intermediária**: pedir aplicações com compensação dos resgates documentada

Decisão é do operador humano. NUNCA gerar a inicial nessa hipótese sem aprovação.

---

## 6. Variantes de placeholder de rubrica

Cada template usa um conjunto específico:

### `inicial-tarifas.docx`
- `{{titulo}}` — junção de **TODAS as rubricas de tarifa** detectadas (ex.: "TARIFA BANCÁRIA, CESTA B.EXPRESSO, CARTÃO CRÉDITO ANUIDADE")

### `inicial-mora.docx`
- `{{rubrica_completa}}` — Title Case (subtítulo): "Mora Crédito Pessoal" ou "Encargos Limite de Crédito"
- `{{rubrica_completa_caps}}` — CAPS para citação na jurisprudência
- `{{rubrica_curta}}` — Title Case: "Mora Cred Pess" ou "Enc. Lim. Crédito"
- `{{rubrica_curta_caps}}` — CAPS: "MORA CRED PESS" ou "ENC LIM CRED"

### `inicial-mora-encargo.docx`
- Os 4 acima, mas pareados (uma instância para cada rubrica)

### `inicial-aplic-invest.docx`
- `{{rubrica_curta_caps}}` — sempre `"APLIC.INVEST FÁCIL"`

### `inicial-combinada.docx`
- `{{titulo_combinado}}` — junção das teses (ex.: "Tarifa Bancária + Mora Cred Pess + Aplic.Invest Fácil")
- `{{lista_pedidos}}` — gerada dinamicamente conforme `ROTULOS_PEDIDO[tese]`

### `inicial-pg-eletron.docx`
- `{{nome_terceiro}}` — nome em CAIXA ALTA (estilo Segoe UI Bold via rStyle 2TtuloChar)
- `{{cnpj_terceiro}}`, `{{logradouro_terceiro}}`, `{{numero_terceiro}}`,
  `{{bairro_terceiro}}`, `{{cidade_terceiro}}`, `{{uf_terceiro}}`, `{{cep_terceiro}}`
- `{{rubrica_curta_caps}}` — CAPS: "PAGTO ELETRON COBRANCA <X>"

Todos os 4 vão à formatação de RUBRICA (caps + bold + italic + underline + amarelo) — ver `helpers_docx.RUBRICA_FORMATADA`.

---

## 7. Placeholders compartilhados (todos os templates)

### Identificação do autor

| Placeholder | Origem | Observação |
|---|---|---|
| `{{nome_completo}}` | Notificação extrajudicial / procuração | CAIXA ALTA, destaque Segoe UI Bold (rStyle 2TtuloChar) |
| `{{nacionalidade}}` | Notificação | "brasileira" / "brasileiro" |
| `{{estado_civil}}` | Notificação | omitir limpamente se vazio |
| `{{profissao}}` | Notificação | omitir limpamente se vazio |
| `{{cpf}}` | Notificação / RG | formato `XXX.XXX.XXX-XX` |
| `{{rg}}` | Notificação / RG | omitir limpamente se vazio |
| `{{orgao_expedidor_prefixo}}` | Notificação | ex.: ` SSP/AM` (com espaço inicial) |
| `{{logradouro}}`, `{{numero}}`, `{{bairro}}`, `{{cidade_de_residencia}}`, `{{uf}}`, `{{cep}}` | Declaração de domicílio (preferencial) ou notificação | dependem da fonte hierárquica |

### Foro e pessoais

| Placeholder | Origem | Observação |
|---|---|---|
| `{{competência}}` | Comarca de residência ou de Maués | usado no cabeçalho da inicial |
| `{{cidade_filial}}`, `{{uf_filial}}` | Mesma do extrato Bradesco da agência | "Maués"/"AM" para casos da comarca |
| `{{prioridade_cabecalho}}` | Idoso (≥ 60 anos) → "Prioridade de tramitação: art. 1.048 do CPC" | omitir se não aplicável |
| `{{pedido_prioridade}}` | mesmo critério | idem |

### Conta e renda

| Placeholder | Origem | Regra crítica |
|---|---|---|
| `{{agencia}}` | Extrato (`extrair_conta_agencia`) | NUNCA hardcoded |
| `{{conta}}` | Extrato (`extrair_conta_agencia`) | NUNCA hardcoded |
| `{{valor_remuneração}}` | `extrair_renda_real()` do extrato | **REGRA CRÍTICA: nunca hardcoded; sem fallback. Se vazio, deixar `[A CONFIRMAR]` e listar como pendência.** |
| `{{valor_remuneração_extenso}}` | `num2words` sobre o real | acompanha o anterior |

### Descontos / valores

Gerados por `extenso.montar_placeholders_monetarios()`. Inclui:
- `{{numero_desconto}}`, `{{desconto_extenso}}`
- `{{inicio_desconto}}`, `{{fim_desconto}}`
- `{{total_descontos}}`, `{{total_descontos_extenso}}`
- `{{dobro_descontos}}`, `{{dobro_descontos_extenso}}`
- `{{dano_moral_total}}`, `{{dano_moral_total_extenso}}`
- `{{valor_causa}}`, `{{valor_causa_extenso}}`

---

## 8. Dano moral — cálculo

| Cenário | Valor |
|---|---|
| 1 tese isolada | R$ 15.000,00 |
| 2+ teses combinadas (`inicial-combinada.docx`) | R$ 5.000,00 × N (N = nº de teses) |
| PG ELETRON (1 inicial por terceiro) | R$ 15.000,00 fixo |

---

## 9. Pastas a IGNORAR

A skill **NUNCA** lê documentos dentro de:
- `KIT/`, `0. KIT/`, `0_KIT/`, `0. Kit/` (qualquer caps)

Esta regra está em `classificador.PASTAS_IGNORAR` e é aplicada em
`listar_documentos()`. Justificativa: a pasta KIT contém documentos
de apoio operacional do escritório, não documentos do caso.

---

## 10. Hierarquia de fontes (anti-vazamento)

Quando há conflito, a fonte vence na ordem:

1. **Notificação extrajudicial** (assinada pelo cliente)
2. **Procuração específica**
3. **RG / CPF físico (legível)**
4. **Declaração de domicílio** (preferencial para endereço se comprovante for de terceiro)
5. **Comprovante de residência** (apenas se em nome do autor)
6. **Extrato Bancário Bradesco** (fonte EXCLUSIVA para conta/agência/renda)

NUNCA usar dados de outro caso, nem hardcoded.
