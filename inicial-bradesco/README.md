# Skill `inicial-bradesco`

Gera petição inicial contra o **BANCO BRADESCO S.A.** (ações declaratórias
de inexistência de relação jurídica c/c repetição do indébito em dobro e
danos morais), a partir da pasta organizada do cliente.

Cobre 5 famílias de tese e 6 templates no vault Obsidian. Seleção
automática conforme as cobranças detectadas no extrato Bradesco.

## Estrutura da skill

```
inicial-bradesco/
├── SKILL.md                     # orquestração + regras críticas (load primário)
├── README.md                    # este arquivo
└── references/
    ├── helpers_docx.py          # manipulação DOCX (run-aware, Cambria global)
    ├── extrator_documentos.py   # parsers PDF (renda real, qualificação, audit APLIC)
    ├── classificador.py         # rubrica → tese, seleção de template
    ├── extenso.py               # num2words pt_BR + montagem de placeholders
    ├── auditor.py               # varredura pós-geração (placeholders, valores, CPFs)
    ├── catalogo_teses.md        # mapa canônico rubrica → tese → template
    ├── erros-herdados.md        # 13 bugs catalogados com causa-raiz e trava
    └── checklist-protocolo.md   # verificações obrigatórias pré-protocolo
```

Os 6 templates `.docx` ficam no vault em
`Modelos/IniciaisBradesco/_templates/` (versionados pelo escritório).

## Quando a skill ativa

Frases-gatilho:
* "gere inicial Bradesco para <cliente>"
* "processar pasta de <cliente> Bradesco"
* "fazer petição inicial bancária Bradesco"
* "tarifas/mora/encargo/aplic invest/pg eletron Bradesco"
* "inicial cobrança indevida Bradesco"

## Famílias de tese cobertas

| Tese | Rubrica típica | Template | IRDR/Súmula |
|---|---|---|---|
| TARIFAS | TARIFA BANCÁRIA, CESTA B.EXPRESSO, CARTÃO CRÉDITO ANUIDADE | `inicial-tarifas.docx` | IRDR 0005053-71.2023.8.04.0000 |
| MORA | MORA CRED PESS / ENC LIM CRED | `inicial-mora.docx` ou `inicial-mora-encargo.docx` | IRDR 0004464-79.2023.8.04.0000 |
| APLIC | APLIC.INVEST FÁCIL | `inicial-aplic-invest.docx` | CC art. 421 + Súmula 479 STJ |
| TITULO | TÍTULO DE CAPITALIZAÇÃO | `inicial-combinada.docx` (placeholder) | IRDR 0005053 |
| PG_ELETRON | PAGTO ELETRON COBRANCA \<X\> | `inicial-pg-eletron.docx` | CDC arts. 7/14/25 + Súmula 479 |

## Pipeline (15 passos)

1. Operador joga pasta do cliente
2. `listar_documentos()` lista PDFs da raiz (ignora `KIT/`)
3. `detectar_teses_ativas()` mapeia tabelas → teses
4. `extrair_qualificacao_da_notificacao()` lê dados do autor
5. `extrair_endereco_declaracao()` lê endereço (preferencial)
6. `extrair_conta_agencia()` lê conta/agência do extrato
7. `extrair_renda_real()` lê renda mensal (sem fallback)
8. Para APLIC: `auditoria_aplic_invest()` valida saldo líquido
9. Para PG ELETRON: extrai dados do terceiro
10. `selecionar_template()` escolhe DOCX
11. `parsear_tabela_descontos()` lê cobranças com filtro por rubrica
12. `montar_placeholders_monetarios()` calcula totais e dobros
13. `aplicar_template()` aplica substituições com formatação
14. `auditar_docx()` faz varredura final
15. Salva `INICIAL_<TESE>_<NOME>_v<N>.docx` + `_RELATORIO_pendencias_v<N>.docx`

## Regras críticas (sumário)

1. **Renda real do extrato** — `extrair_renda_real()` sem fallback hardcoded
2. **Pasta KIT é off-limits** — `PASTAS_IGNORAR` em `classificador.py`
3. **Cambria forçado nos 3 níveis** — theme + styles + inline
4. **Destaque Segoe UI Bold** apenas em `nome_completo` e `nome_terceiro`
5. **Mora+Encargo = 1 tese** (IRDR 0004464)
6. **APLIC negativo** trava geração até decisão humana
7. **PG ELETRON: 1 inicial por terceiro** — não combina
8. **Combinação só com critério objetivo** — comarcas {Caapiranga, Presidente Figueiredo, Manacapuru} ou dobro ≤ R$ 400
9. **Auditoria pós-geração obrigatória** — `auditor.auditar_docx()`
10. **Hierarquia de fontes** — notificação > procuração > RG > declaração > comprovante > extrato

Ver `references/erros-herdados.md` para o catálogo completo de bugs e
`references/checklist-protocolo.md` para a checagem pré-entrega.

## Casos paradigma testados

| Caso | Pasta | Tese | Template | Bugs detectados |
|---|---|---|---|---|
| José Sebastião dos Santos Silva | `JOSÉ SEBASTIÃO.../TARIFAS/` | 1 (tarifas) | `inicial-tarifas` | E01 (Cambria), E03 (hardcoded) |
| Maria Joana da Silva Soares | `MARIA JOANA.../` | 3 (tarifas+mora+título) | `inicial-combinada` | E04 (variantes rubrica) |
| Elinaldo | `ELINALDO.../` | 1 (aplic.invest) | `inicial-aplic-invest` | E06 (saldo negativo) |
| Terezinha Brandão da Rocha | `TEREZINHA.../PGTO ELETRÔNICO/` | 3 PG ELETRON × 3 terceiros | `inicial-pg-eletron` (3×) | E02, E05, E07, E12 |

## Dependências Python

```
python-docx
PyMuPDF (fitz)
lxml
num2words
```

## Ver também

* Skill irmã para verificação pós-protocolo: `analise-inicial-cobrancas-bradesco`
* Vault: `Modelos/IniciaisBradesco/_MOC.md` (mapa de conteúdo no Obsidian)
