---
tipo: documentação
tags: [planilha, calculo-indebito, rmc, rcc, nao-contratado]
---

# Planilhas Modelo — Cálculo de Indébito

Referência canônica das planilhas geradas pelas skills do escritório.
Os arquivos `.xlsx` nesta pasta são **modelos com dados fictícios** —
nenhuma informação de cliente real. Servem como espelho visual do formato.

## Arquivos

| Arquivo | Origem (script) | Skill que consome |
|---|---|---|
| `CALCULO_INDEBITO_NC_MODELO.xlsx` | [`_common/calculadora_indebito.py`](../calculadora_indebito.py) → `gerar_excel_indebito()` | `kit-juridico` (Fase F) e `inicial-nao-contratado` (lê o TOTAL GERAL para o valor da causa) |
| `CALCULO_RMC_MODELO.xlsx` | [`inicial-rmc-rcc/references/_pipeline_caso.py`](../../inicial-rmc-rcc/references/_pipeline_caso.py) → `gerar_planilha()` | `inicial-rmc-rcc` (parte do `renderizar_caso`) |
| `CALCULO_RCC_MODELO.xlsx` | mesmo `gerar_planilha()` (tese RCC) | `inicial-rmc-rcc` |

## Regime de cálculo (regras canônicas)

Aplicado em **todas** as planilhas, NC + RMC + RCC:

1. **Correção monetária:** INPC mensal (índices oficiais em
   `_common/indices_oficiais.py`). Fator INPC = (índice da apuração) ÷
   (índice da competência do desconto).
2. **Juros de mora:** 1% a.m. simples (art. 406 CC + art. 161 §1º CTN),
   contados desde cada desconto indevido.
3. **Restituição em dobro:** art. 42, parágrafo único, CDC. Total simples
   × 2.
4. **Dano moral (NC):**
   - 1 contrato impugnado: **R$ 15.000,00** (regra escritório AL/AM)
   - 2+ contratos no mesmo banco/benefício: **R$ 5.000,00 × N**
5. **Dano moral (RMC/RCC):** R$ 10.000,00 fixo + dano temporal R$ 5.000,00
   (regra IRDR Tema 5 TJAM + jurisprudência consolidada).
6. **Prescrição quinquenal:** descontos de mais de 5 anos contados da
   data de apuração são excluídos do `valor_dobro` (mas continuam
   listados na planilha com flag visual).

## Estrutura

### CALCULO_INDEBITO_NC (Não Contratado)

Aba única `RESUMO` com:

```
CÁLCULO DE INDÉBITO — <NOME DO CLIENTE>
Data de apuração: dd/mm/aaaa

CONTRATO 1 — <BANCO> nº <NÚMERO>     Situação: Ativo/Excluído
Parcela: R$ XX,XX           Total contratado: R$ X.XXX,XX
+------------+----------------+------------+----------------+...
| Competência | Valor original | Fator INPC | Valor corrigido| Meses (juros) | Juros 1% a.m. | Total simples | Total em dobro |
+------------+----------------+------------+----------------+...
| 01/2024    | R$ 100,00      | 1,0345     | R$ 103,45      | 28            | R$ 28,97      | R$ 132,42     | R$ 264,84      |
| ...        | ...            | ...        | ...            | ...           | ...           | ...           | ...            |
+------------+----------------+------------+----------------+...
SUBTOTAL CONTRATO 1: R$ X.XXX,XX (dobro)

CONTRATO 2 — ...
SUBTOTAL CONTRATO 2: R$ X.XXX,XX

SUBTOTAL GERAL (todos os contratos em dobro): R$ XX.XXX,XX
DANO MORAL (regra 15k×1 ou 5k×N):              R$ 15.000,00
TOTAL GERAL DA AÇÃO:                            R$ XX.XXX,XX
```

> **Nota:** a skill `inicial-nao-contratado` (perfis AL/AM) lê o
> `TOTAL GERAL` para usar como valor da causa. A leitura é feita por
> `calculadora_indebito.localizar_excel_indebito(pasta_acao)` +
> `ler_total_geral_xlsx(path)`.

### CALCULO_RMC / CALCULO_RCC

Mesma estrutura geral, mas com 1 só contrato (cada RMC/RCC vira 1
inicial separada). Adiciona coluna `Prescrição?` (Sim/Não) e linha
extra `Dano temporal` (R$ 5.000,00).

Cabeçalho:
```
CÁLCULO DE INDÉBITO — <NOME> — <TESE: RMC ou RCC>
Banco-réu: <BANCO> — CNPJ <CNPJ>
Contrato: nº <NÚMERO>
Data de inclusão: dd/mm/aaaa
Base de cálculo do benefício: R$ X.XXX,XX
Total comprometido: R$ XXX,XX
Valor líquido (base - comprometido): R$ X.XXX,XX
```

Bloco mensal igual ao NC. Subtotais:

```
SUBTOTAL DOBRO (descontos não prescritos × 2): R$ X.XXX,XX
DANO MORAL:                                     R$ 10.000,00
DANO TEMPORAL:                                  R$  5.000,00
VALOR DA CAUSA:                                 R$ XX.XXX,XX
```

## Como regenerar os modelos

Script único (Python):

```python
# Para NC:
from _common.calculadora_indebito import gerar_excel_indebito
gerar_excel_indebito(contratos, 'NOME', 'saida.xlsx')

# Para RMC/RCC:
from inicial_rmc_rcc.references._pipeline_caso import gerar_planilha, calcular_valores
calcular_valores(caso)          # antes
gerar_planilha(caso, 'saida.xlsx')
```

Veja `_gerar_modelos.py` (não incluído no repo — está em
`C:\Users\gabri\OneDrive\Área de Trabalho\CLAUDE\`) para o snippet
completo com os dados fictícios usados aqui.

## Paradigmas e casos de teste

- **BENEDITA WALKYRIA REIS BARBOSA** (RMC BMG AM, 2026-05-13) — primeiro
  caso RMC validado contra escritório.
- **MARIA AZEVEDO PARINTINS** (RMC PAN 756931620-6, AM, 2026-05-14) —
  primeiro caso RMC com pluralização de período ("3 anos e 11 meses").

Veja também os feedbacks em memory/ relacionados:

- `feedback_rmc_rcc_cambria_quadro.md`
- `feedback_rubricas_hiscre.md`
- `project_iniciais_rmc_rcc.md`
