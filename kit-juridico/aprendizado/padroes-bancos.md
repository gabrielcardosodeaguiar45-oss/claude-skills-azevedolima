# Padrões de Numeração de Contrato por Banco

Heurísticas estáveis para validar/sugerir leitura de números de contrato.
Atualizar quando uma correção evidenciar regra nova ou refutar regra existente.

## Banco Itaú Consignado (código 029)

- 9 dígitos (sem hífen, sem ponto)
- Geralmente começa com `5` ou `6` (refins recentes 2020+ tendem a `6`)
- Exemplos confirmados: `631248310`, `626702215`, `639348740`, `598992497`
- ATENÇÃO: contratos novos da Anaiza/Marinete começam com `63x` (refin 2021)

## Banco PAN (código 623)

- 9-10 dígitos, geralmente seguidos de `-X` (dígito verificador)
- Padrão: `NNNNNNNNN-N` (ex: `326994938-8`, `303117659-1`, `334910291-7`)
- Quando manuscrito, o `-X` final às vezes é separado em outra linha
- Em algumas pastas (sem hífen visível): `334924939.2`, `304987531.7`

## Caixa Econômica Federal (código 104) — RMC

- 15 dígitos seguidos, sem espaços nem hífens
- Padrão: `1NNNNNNNNNNNNNN` (ex: `104041645683901`)
- Os primeiros 3 dígitos `104` são código do banco (CAIXA)

## Banco BMG (código 318)

- Cartão consignado RMC: 7-8 dígitos (ex: `15021854`, `12140484`, `9985524`)
- Empréstimo consignado: 9 dígitos
- Note: contratos antigos podem ter 7 dígitos (`9985524`) e novos 8 (`15021854`)

## Banco C6 Consignado (código 626)

- 10 dígitos
- Exemplos: `9043454776`, `9043455094`, `9043455093`
- Início recorrente `90434xxxxx`

## Banco Bradesco (código 237 / 394 — Bradesco Financiamentos)

- Variável: 9 a 12 dígitos, pode ter ponto separador
- Em manuscritos vistos: `315833.3299`, `34985.654906`, `31203991.43`
- ATENÇÃO: bradesco financiamento usa código 394 (não 237)

## Banco Mercantil (código 389)

- 9 dígitos
- Exemplo: `017342690`
- Inicia com `0` em alguns casos

## Banco Daycoval (código 707)

- Cartão (RMC): 13-15 dígitos
- Exemplo: `53011624.0163`

## Banco Facta (código 326)

- 10 dígitos
- Exemplo: `0055245654`

## Banco Olé (código 169)

- 9 dígitos
- Exemplo: `240053319`

## Agibank (código 121)

- Cartão (RCC): 9 dígitos
- Exemplo: `350023871`
- Empréstimo consignado: 10 dígitos (`1513134296`, `1515917919`)

---

## Regras gerais de validação manuscrita

1. **Comparar comprimento** com o esperado por banco antes de validar.
2. **Confronto com HISCON** quando disponível: matching exato → match aproximado (Lev≤2) → fuzzy por banco.
3. **Erros de leitura comuns**:
   - `0` vs `6` vs `9` (curva fechada)
   - `1` vs `7` (traço com pé)
   - `4` vs `9` (idem)
   - `3` vs `8` (curva dupla)
   - `5` vs `6` vs `S` (especialmente em letra cursiva)
4. **Pontuação no manuscrito** (`.`, `-`) é frequentemente arbitrária e deve ser **removida** antes do match com HISCON (que usa o número limpo).
