# Regras de Detecção e Split por Benefício INSS

Quando o cliente recebe mais de um benefício do INSS (ex: aposentadoria + pensão por morte), os contratos consignados estão averbados em benefícios diferentes. A skill DEVE separar a organização por benefício.

## Identificando os benefícios

### No HISCON (Histórico de Empréstimo)

Cada PDF de HISCON refere-se a UM benefício. A primeira página traz:

```
HISTÓRICO DE EMPRÉSTIMO CONSIGNADO
[NOME DO TITULAR]
Benefício
[ESPÉCIE DO BENEFÍCIO]
Nº Benefício: 041.645.683-9
```

Quando o cliente tem 2+ benefícios, há 2+ PDFs de HISCON. A skill deve identificar todos via regex sobre o text-layer.

**Padrões de regex:**
```
NB:                regex r"N[ºo°]\s*Benefício:\s*([\d\.\-]+)"
Espécie:           regex r"Benefício\s*\n([A-ZÇÃÉÔ\s]+)\s*\nN[ºo°]\s*Benefício:"
Titular:           regex r"HISTÓRICO DE\s*\nEMPRÉSTIMO CONSIGNADO\s*\n([A-ZÇÃÉ\s]+)\s*\nBenefício"
```

### No HISCRE (Histórico de Pagamento)

Pode conter dados de 1 ou mais benefícios. Cada bloco começa com:

```
NB: 134.412.590-2
Espécie: 41 - APOSENTADORIA POR IDADE
```

A skill deve detectar transições e cortar em PDFs separados (1 por NB).

## Espécies de benefício comuns

| Cód | Sigla | Descrição | Pasta sugerida |
|---|---|---|---|
| 21 | B21 | Pensão por morte previdenciária | `PENSÃO/` |
| 32 | B32 | Aposentadoria por incapacidade permanente | `APOSENTADORIA POR INCAPACIDADE/` |
| 41 | B41 | Aposentadoria por idade | `APOSENTADORIA/` |
| 42 | B42 | Aposentadoria por tempo de contribuição | `APOSENTADORIA POR TEMPO DE CONTRIBUIÇÃO/` |
| 31 | B31 | Auxílio por incapacidade temporária | `AUXÍLIO-DOENÇA/` |
| 87 | B87 | Amparo Social ao Idoso (BPC-LOAS) | `BPC/` |
| 88 | B88 | Amparo Social ao PCD (BPC-LOAS) | `BPC/` |
| 91 | B91 | Auxílio-acidente | `AUXÍLIO-ACIDENTE/` |
| 25 | B25 | Auxílio-reclusão | `AUXÍLIO-RECLUSÃO/` |

A skill deve normalizar nomes de pasta: tudo maiúsculo, sem acento problemático em filesystem (pode usar acentos pois NTFS suporta), substituir caracteres ilegais por espaço.

## Layout de pastas

### Caso 1: Cliente com UM benefício
Não cria nível BENEFÍCIO. Pastas de ação ficam direto na raiz:

```
[Cliente]/
├── 0. Kit/
├── BANCO ITAU CONSIGNADO/
├── BANCO BMG - RMC-RCC/
└── Pendências.xlsx
```

### Caso 2: Cliente com MAIS DE UM benefício
Cria nível BENEFÍCIO entre raiz e pastas de ação:

```
[Cliente]/
├── 0. Kit/
├── PENSÃO/
│   ├── BANCO ITAU CONSIGNADO/
│   ├── BANCO C6 CONSIGNADO/
│   └── CAIXA - RMC-RCC/
├── APOSENTADORIA/
│   ├── BANCO ITAU CONSIGNADO/
│   ├── BANCO C6 CONSIGNADO/
│   ├── BANCO PAN/
│   └── BANCO BMG - RMC-RCC/
└── Pendências.xlsx
```

`0. Kit/` fica sempre na raiz (compartilhado). `Pendências.xlsx` também.

### Detecção do número de benefícios

A skill conta os HISCON únicos pelo NB. Se >1, ativa o layout com nível benefício.

Caso o usuário forneça apenas 1 HISCON mas a procuração mencionar contratos de bancos não localizáveis nele, a skill registra pendência: "Possível ausência de extrato de outro benefício".

## Cruzamento procurações × benefícios

Cada contrato listado na procuração deve ser localizado em UM dos extratos. A skill faz:

```python
for procuracao in procuracoes:
    contrato = procuracao.contrato
    achado_em = []
    for extrato in extratos:
        if extrato.contem(contrato):
            achado_em.append(extrato.beneficio)
    if len(achado_em) == 0:
        registrar_pendencia(f"Contrato {contrato} não localizado em nenhum extrato")
    elif len(achado_em) > 1:
        registrar_pendencia(f"Contrato {contrato} aparece em múltiplos extratos: {achado_em}")
    else:
        atribuir_beneficio(procuracao, achado_em[0])
```

Tolerância de leitura: o número da procuração pode vir com 1 dígito errado por OCR. A skill deve fazer match aproximado (Levenshtein ≤ 1) e marcar com pendência leve.

## Replicação de documentos comuns

Documentos da parte (RG, comprovante, declaração de hipossuficiência) são duplicados em CADA pasta de ação dentro de CADA benefício. Histórico de empréstimo (HISCON) e histórico de pagamento (HISCRE) são DUPLICADOS apenas na versão correta do benefício correspondente — nunca cruzar (não colocar HISCON da pensão na pasta de aposentadoria).
