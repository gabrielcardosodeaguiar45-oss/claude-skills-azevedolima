# Taxonomia dos modelos de apelação — Banco/Consignado

**Atualizado em:** 2026-04-21.
**Fonte:** `C:\Users\gabri\OneDrive\Área de Trabalho\CLAUDE\3. Correções\Modelo - Apelações`.

Existem **11 modelos** no acervo do escritório. Dividem-se em dois grandes cenários de recurso, com matriz de variação por comarca, tipo de contrato e desfecho da sentença.

## Cenário A — Apelação de MAJORAÇÃO de dano moral

O autor venceu em 1ª instância, mas o valor arbitrado é baixo. Recorre pedindo majoração. O banco também costuma recorrer (recursos cruzados). Variação por percentual de honorários fixado na sentença (10%, <10% ou >10%), comarca e se a sentença desviou para "cartão" indevidamente.

| # | Comarca | Honorários | Particularidade | Arquivo |
|---|---|---|---|---|
| 1 | Boa Vista do Ramos | < 10% | Um contrato | `Apelação - Dano moral majoração, um contrato, inferior a 10% (boa vista do ramos).docx` |
| 2 | Maués | < 10% | Um contrato | `Apelação - Dano moral majoração, um contrato, inferior a 10% (maués).docx` |
| 3 | Boa Vista do Ramos | > 10% | Um contrato | `Apelação - Dano moral majoração, um contrato, superior a 10%  (boa vista do ramos).docx` |
| 4 | Maués | > 10% | Um contrato + julgou como CARTÃO (desvio) | `Apelação - Dano moral majoração, um contrato, superior a 10% + julgou com CARTÃO (maués).docx` |
| 5 | Maués | = 10% | Um contrato (versão NOVO) | `Apelação - dano moral majoração, um contrato, 10% (maués) NOVO.docx` |
| 6 | Maués | = 10% | Um contrato | `Apelação - dano moral majoração, um contrato, 10% (maués).docx` |

## Cenário B — Apelação de IMPROCEDÊNCIA

O autor perdeu em 1ª instância. Recorre pedindo reforma (procedência) ou, subsidiariamente, cassação da sentença. Variação por forma do contrato (físico vs digital), existência de perícia e se a sentença desviou para "cartão".

| # | Comarca | Contrato | Perícia | Desvio cartão | Arquivo |
|---|---|---|---|---|---|
| 7 | Maués | Digital | Não | Não | `Apelação - Improcedencia - digital, sem pericia  (maués).docx` |
| 8 | Boa Vista do Ramos | Digital | Não | Não | `Apelação - Improcedencia - digital, sem pericia (boa vista do ramos).docx` |
| 9 | Boa Vista do Ramos | Físico | Não | Não | `Apelação - Improcedencia - fisico, sem pericia (boa vista do ramos).docx` |
| 10 | Maués | Digital | Não | **Sim** | `Apelação AM - Improcedencia - contrato DIGITAL, sem pericia, julgado como cartão (Maués).docx` |
| 11 | Maués | Físico | Não | **Sim** | `Apelação AM - Improcedencia - contrato FISICO, sem pericia, julgado como cartão (Maués).docx` |

## Árvore de decisão para seleção de modelo (a preencher após estudo)

```
Autor ganhou 1ª instância?
├── SIM → Cenário A (majoração)
│   ├── Sentença julgou como cartão? → Modelo #4
│   ├── Honorários < 10%? → Modelos #1 (BVR) ou #2 (Maués)
│   ├── Honorários = 10%? → Modelos #5/#6 (Maués)
│   └── Honorários > 10%? → Modelos #3 (BVR) ou #4 (Maués)
└── NÃO → Cenário B (improcedência)
    ├── Contrato digital?
    │   ├── Julgou como cartão? → Modelo #10 (Maués)
    │   └── Não desviou? → Modelo #7 (Maués) ou #8 (BVR)
    └── Contrato físico?
        ├── Julgou como cartão? → Modelo #11 (Maués)
        └── Não desviou? → Modelo #9 (BVR)
```

**Lacunas identificadas (a confirmar):**
- Não há modelo de majoração para BVR com honorários = 10%.
- Não há modelo de improcedência com perícia realizada.
- Não há modelo para outras comarcas (Parintins, Manacapuru etc.).
- Não há modelo para situação em que apenas o banco recorre (contrarrazões são outra skill).

## Próximos passos de estudo

1. Extrair configurações técnicas de cada .docx (margens, fontes, estilos, cabeçalho, rodapé).
2. Extrair estrutura textual (seções, parágrafos, fórmulas).
3. Extrair teses jurídicas por cenário.
4. Catalogar imagens/prints embutidos.
5. Identificar placeholders (campos variáveis).
6. Listar jurisprudência fixa (sempre citada) vs variável.
7. Gravar assinaturas e OABs de cada modelo.
8. Comparar pares (Maués vs BVR; < 10% vs = 10% vs > 10%; físico vs digital) para extrair deltas.
