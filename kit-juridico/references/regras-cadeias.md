# Regras de Detecção e Organização de Cadeias

Este arquivo descreve como a skill detecta cadeias de fraude (refinanciamentos, portabilidades, consolidações, fracionamentos) a partir do extrato HISCON e como agrupa os contratos em pastas de ação.

## Conceitos

### Cadeia de contratos
Sequência de contratos onde um derivou do outro por uma operação financeira do banco — refinanciamento, portabilidade, consolidação, fracionamento. A detecção se baseia em três sinais combinados:

1. **Data de inclusão do novo coincide (± 1 dia) com data de exclusão do antigo**
2. **Origem do novo é "Averbação por Refinanciamento" / "Portabilidade"**
3. **Motivo de exclusão do antigo é "Exclusão por refinanciamento" / "Portabilidade"**
4. **Reforço opcional: valor de parcela igual ou consistente**

### Tipos de cadeia

#### Refin direto (1→1)
1 contrato excluído por refin → 1 contrato novo de refin no mesmo banco, mesma data, mesmo valor de parcela.

```
Contrato A (R$236,30, parcela)        Contrato B (R$236,30, parcela)
Inclusão: 08/07/2020                  Inclusão: 14/09/2021
Exclusão: 14/09/2021 (por refin)  →   Origem: Refin
Banco: Itaú                           Banco: Itaú
```

#### Consolidação (N→1)
N contratos excluídos no mesmo dia, todos por refin → 1 contrato novo de refin com valor de parcela = soma das parcelas excluídas (ou próximo).

```
A (R$50)  ─┐
B (R$30)  ─┼──→  D (R$120, refin)
C (R$40)  ─┘
Excluídos em 14/09/2021       Incluído em 14/09/2021
```

#### Fracionamento (1→N)
1 contrato excluído por refin → N contratos novos de refin no mesmo dia, valores de parcela somando ao do excluído.

```
                    ┌──→ B (R$50, refin)
A (R$120)  ────────┼──→ C (R$30, refin)
Excluído            └──→ D (R$40, refin)
14/09/2021          Incluídos em 14/09/2021
```

#### Portabilidade (entre bancos)
Contrato excluído por portabilidade no banco A → contrato novo no banco B com origem "portabilidade" e valor pago equivalente ao saldo devedor.

```
A (Itaú)                          B (BMG)
Inclusão: 08/07/2020             Inclusão: 14/09/2021
Exclusão: 14/09/2021 (port)  →   Origem: Portabilidade
Motivo: Portabilidade            Banco: BMG
```

Esta é a única cadeia que cruza bancos. As demais (refin, consolidação, fracionamento) ficam no mesmo banco.

#### Cadeia recursiva
Um contrato pode ser ao mesmo tempo "filho" de outro (chegou por refin) e "pai" de um terceiro (foi refinanciado depois). Cadeias podem ter 3+ contratos em série:

```
A → B → C → D     (4 níveis de refin sucessivos)
```

#### Substituição imediata (RMC/RCC)
Caso especial de cartão consignado. Contrato A excluído por "Exclusão Banco" + contrato B com "Averbação nova" no dia seguinte (± 1 dia), mesmo banco, mesmo valor de reserva. Não é refin oficial mas indica substituição administrativa do banco — anotar como cadeia tipo `SUBSTITUIÇÃO_BANCO`.

## Algoritmo de detecção

```
1. Para cada extrato (um por benefício), parsear todos os contratos.
2. Construir grafo:
   - Nodes = contratos
   - Edges = relações de cadeia (refin, port, consol, frac, subst)
3. Aplicar regras de matching:
   3.1. Listar todos contratos com motivo de exclusão = "refinanciamento" ou "portabilidade"
   3.2. Para cada um, buscar candidatos com origem = "Refin"/"Port" e data inclusão = data exclusão ± 1 dia
   3.3. Confirmar match por banco (intra-banco para refin, qualquer para port) e por valor (parcela ou saldo)
   3.4. Aplicar regras 1→1, N→1, 1→N
4. Encontrar componentes conectados do grafo.
5. Cada componente é um "cluster" = uma ação judicial.
```

## Regras de organização em pastas de ação

A unidade de organização **não é o banco**, mas o **componente conectado** do grafo de cadeias. Cada componente vira uma pasta de ação.

### Regras de nome da pasta

1. **Componente todo do mesmo banco**:
   ```
   [Banco]/
   ```
   Exemplo: `BANCO ITAU CONSIGNADO/`

2. **Componente envolve portabilidade entre bancos**:
   ```
   [Banco A] + [Banco B]/
   ```
   Exemplo: `BANCO ITAU + BANCO BMG/`

3. **RMC/RCC** (cartão consignado): adicionar sufixo:
   ```
   [Banco] - RMC-RCC/
   ```
   Exemplo: `BANCO BMG - RMC-RCC/`

### Contratos isolados (sem cadeia detectada)

Contratos sem cadeia (averbação nova isolada, sem refin posterior) são agrupados na pasta do banco onde estão. Se já existe pasta `[Banco]/` por causa de uma cadeia interna, os isolados vão na mesma pasta. Se não existe, criar `[Banco]/`.

**Cuidado**: contratos do mesmo banco podem aparecer em duas pastas — uma `[Banco]/` (com cadeia interna + isolados) e outra `[Banco] + [Banco_Y]/` (com cadeia inter-banco específica). Isso é intencional.

### Quando a procuração contém poderes especiais contra INSS

Se a procuração tem poderes especiais contra o INSS (típico de empréstimo não contratado), adicionar essa informação ao ESTUDO mas não alterar o layout de pastas — continua sendo organizado por banco/cadeia.

## Saída do detector

Após rodar o detector, a saída deve conter para cada componente:

```python
{
    "id": "C-01",
    "tipo": "CADEIA",  # ou "ISOLADO"
    "subtipo": "REFIN_DIRETO",  # ou "CONSOLIDACAO_N1", "FRACIONAMENTO_1N", "PORTABILIDADE_INTER_BANCO", "SUBSTITUICAO_BANCO"
    "bancos": ["BANCO ITAU CONSIGNADO"],  # 1 ou 2 bancos
    "beneficio": "PENSAO",
    "contratos": [
        {"contrato": "626702215", "papel": "ANCESTRAL", "ordem": 1, ...},
        {"contrato": "632948666", "papel": "ATUAL",     "ordem": 2, ...},
    ],
    "cor_grifo": (1.00, 0.95, 0.40),  # RGB 0-1
    "valor_parcela_referencia": "R$236,30",
    "data_refin_referencia": "14/09/2021",
}
```

## Paleta de cores para grifo (uma cor por cadeia dentro do mesmo extrato)

Em ordem de uso, ciclando se houver mais de 6 cadeias:

| ID | RGB (0-1) | Hex | Nome |
|---|---|---|---|
| 1 | (1.00, 0.95, 0.40) | FFF066 | Amarelo |
| 2 | (0.60, 1.00, 0.60) | 99FF99 | Verde claro |
| 3 | (1.00, 0.75, 0.40) | FFBF66 | Laranja claro |
| 4 | (1.00, 0.70, 0.85) | FFB3D9 | Rosa claro |
| 5 | (0.50, 0.85, 1.00) | 80D9FF | Azul claro |
| 6 | (0.85, 0.70, 1.00) | D9B3FF | Violeta claro |

Contratos sem cadeia (isolados) recebem cor neutra (1.0, 1.0, 0.5) = amarelo padrão suave.
