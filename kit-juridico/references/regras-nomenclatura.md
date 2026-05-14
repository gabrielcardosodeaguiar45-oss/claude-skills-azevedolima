# Regras de Nomenclatura de Documentos (v2.2 — 2026-05-11)

Numeração canônica única. Nunca improvisar fora deste padrão.

## Convenção de separadores (v2.2)

A partir de 2026-05-11 a skill usa três caracteres distintos como separadores,
e cada um tem função fixa:

| Caractere | Uso |
|---|---|
| `.` ponto (U+002E) | Sempre depois do número de ordem: `2. ...`, `3. ...`, `3.1 ...`, `5.1 ...` |
| `–` travessão / en-dash (U+2013) | Entre campos da procuração: `2. Procuração – Banco – Contrato N.pdf` |
| `-` hífen comum (U+002D) | Entre o número ordinal e o descritor do subdocumento (3.1, 3.2, 3.3, 5.1, 5.2): `3.1 - RG e CPF do rogado.pdf`; e dentro do descritor antes do nome próprio: `3.1 - RG e CPF do rogado - SANTANA DE SOUZA SERVALHO.pdf` |

Antes da v2.2 a skill usava `-` (hífen) tanto após o número (`2- ...`) quanto
entre campos da procuração. O Mac (paradigma de 5 clientes do Elizio, 2026-05-11)
migrou para o esquema atual e o pipeline.py já gera neste formato. Pastas
organizadas em versão antiga devem ser renormalizadas em caso de retomada.

## Estrutura completa de uma pasta de ação

```
0. Kit/                                                       (sempre criada)
[BENEFÍCIO]/                                                  (apenas se houver mais de 1 NB)
└── [PASTA DE AÇÃO]/                                          (1 banco ou bancos com cadeia)
    ├── 2. Procuração – [Banco] – Contrato [Nº].pdf
    ├── 3. RG e CPF.pdf                                       (parte autora / rogante)
    ├── 3.1 - RG e CPF do rogado - [Nome Completo].pdf        (se há rogo)
    ├── 3.2 - RG e CPF da testemunha 1 - [Nome Completo].pdf
    ├── 3.3 - RG e CPF da testemunha 2 - [Nome Completo].pdf
    ├── 4. Declaração de hipossuficiência.pdf
    ├── 5. Comprovante de residência.pdf
    ├── 5.1 - Declaração de domicílio.pdf                     (se aplicável)
    ├── 5.2 - RG do declarante terceiro.pdf
    ├── 6. Histórico de empréstimo [BENEFÍCIO] (grifado).pdf
    ├── 7. Histórico de créditos [BENEFÍCIO].pdf
    ├── 8. Extrato bancário.pdf                               (opcional)
    └── ESTUDO DE CADEIA - [Banco].docx
```

## 1. Procuração

Formato com travessão entre campos:
```
2. Procuração – [Banco] – Contrato [Número].pdf
```

Quando a procuração é específica de RMC/RCC (cartão consignado), incluir tipo
entre o banco e o contrato:
```
2. Procuração – [Banco] – RMC-RCC – Contrato [Número].pdf
```

Cada procuração é um PDF separado, mesmo que haja várias do mesmo banco.
Todas ficam na pasta da ação correspondente. **A procuração contém SOMENTE
a procuração** — nunca misturar com outros documentos.

Quando não for possível identificar banco ou contrato:
```
2. Procuração 1.pdf
2. Procuração 2.pdf
```

## 2. Documentos pessoais

### RG + CPF (parte autora — padrão)
```
3. RG e CPF.pdf
```

RG e CPF unificados em um único PDF. Quando o cliente tem só CNH:
```
3. CNH.pdf
```

**CIN moderna (Carteira de Identidade Nacional):** o documento tem duas faces
distintas. A frente traz foto + nome + RG/CPF; o verso traz filiação, órgão
expedidor, local e data de emissão. **As duas faces devem ficar juntas no
mesmo PDF** (`3. RG e CPF.pdf`). Cuidado especial: o verso mostra a
**filiação do próprio titular** — não confundir com CIN de outra pessoa
(o nome dos pais não é o nome do dono do documento).

### Assinatura a rogo

Quando o outorgante não pode assinar (analfabeto / impossibilitado), há rogo
+ 2 testemunhas. Cada pessoa tem seu próprio PDF, com o nome completo no
final:

```
3. RG e CPF.pdf                                              (parte autora / rogante)
3.1 - RG e CPF do rogado - [Nome Completo].pdf
3.2 - RG e CPF da testemunha 1 - [Nome Completo].pdf
3.3 - RG e CPF da testemunha 2 - [Nome Completo].pdf
```

**`[Nome Completo]` é extraído do RG/CNH da pessoa**, com todos os sobrenomes.
Não usar apelido nem primeiro nome só. Exemplos corretos:
- `3.1 - RG e CPF do rogado - SANTANA DE SOUZA SERVALHO.pdf`
- `3.2 - RG e CPF da testemunha 1 - FRANCISCA SERVALHO PINHEIRO.pdf`

Errado:
- `3.1 - RG e CPF do rogado - Santana.pdf` (faltam sobrenomes)
- `3.2 - RG e CPF da testemunha 1.pdf` (falta nome)
- `3.1 - DOC ROGADO.pdf` (placeholder antigo do pipeline; deve ser renomeado)

Cada pessoa tem PDF próprio. Nunca juntar documentos de pessoas diferentes
em um único arquivo.

**Implementação:** o `pipeline.py` cria os arquivos com nome genérico
(sem `- NOME`). O passo seguinte (Fase 5 manual ou Fase 11 automática quando
o nome já foi extraído) **deve renomear** acrescentando o sufixo
` - NOME COMPLETO`. Ver `regras-imagens.md` para o procedimento de extração.

## 3. Declaração de hipossuficiência

```
4. Declaração de hipossuficiência.pdf
```

Contém EXCLUSIVAMENTE a declaração assinada. Nunca incluir contratos, RG,
comprovantes, procurações.

## 4. Comprovante de residência

```
5. Comprovante de residência.pdf
```

Se o comprovante estiver em nome de terceiro (parente, cônjuge, anfitrião),
acrescentar declaração de domicílio + RG do declarante:

```
5. Comprovante de residência.pdf                             (em nome do terceiro)
5.1 - Declaração de domicílio.pdf                            (declaração assinada do terceiro)
5.2 - RG do declarante terceiro.pdf                          (RG da pessoa que declara)
```

> **Nota terminológica:** até v2.1 o documento de 5.1 chamava-se
> "Declaração de residência de terceiro". A v2.2 padronizou para
> "Declaração de domicílio" (terminologia do CC art. 70). O conteúdo é o
> mesmo: declaração assinada por terceiro confirmando que o cliente reside
> no endereço do comprovante.

## 5. Histórico de empréstimo (HISCON do INSS)

Documento emitido pelo Meu INSS / INSS listando contratos de consignado
averbados em um benefício específico.

```
6. Histórico de empréstimo [BENEFÍCIO] (grifado).pdf
```

`[BENEFÍCIO]` é a espécie do benefício, em maiúsculas: `PENSÃO`,
`APOSENTADORIA`, `AUXÍLIO`, `BPC`, etc.

Quando há um único benefício, omitir o sufixo:
```
6. Histórico de empréstimo (grifado).pdf
```

O sufixo `(grifado)` indica que o PDF tem highlights coloridos sobre os
contratos relevantes daquela ação. Se a versão grifada não foi gerada
(ex.: extrato sem texto extraível), nomear:
```
6. Histórico de empréstimo [BENEFÍCIO].pdf
```

## 6. Histórico de créditos (HISCRE)

Documento emitido pelo INSS listando os créditos do benefício mês a mês.

```
7. Histórico de créditos [BENEFÍCIO].pdf
```

Quando há um único benefício, omitir o sufixo:
```
7. Histórico de créditos.pdf
```

> **Nota terminológica:** até v2.1 chamava-se "Histórico de pagamento". A v2.2
> migrou para "Histórico de créditos" — sigla HISCRE = Histórico de
> Crédito do INSS, terminologia oficial.

## 7. Extrato bancário (opcional)

Movimentação financeira da conta corrente do cliente — apenas quando
relevante para a ação (ex.: ações Bradesco onde se pleiteia restituição de
cobranças indevidas).

```
8. Extrato bancário.pdf
```

**ATENÇÃO — não confundir:**
- `6. Histórico de empréstimo` = HISCON do INSS (Meu INSS)
- `7. Histórico de créditos` = HISCRE do INSS
- `8. Extrato bancário` = extrato de conta corrente do banco do cliente

Se o documento veio de um banco específico e mostra movimentação de conta,
descontos, parcelas debitadas, saldos → é extrato bancário (item 8), não
histórico do INSS.

## 8. Estudo de cadeia (gerado pela skill)

```
ESTUDO DE CADEIA - [Banco].docx
```

Quando a pasta agrupa bancos por cadeia inter-banco (portabilidade entre bancos):
```
ESTUDO DE CADEIA - [Banco A] + [Banco B].docx
```

Documento gerado automaticamente após a detecção de cadeias. Contém: diagrama
da cadeia, tabela de contratos, valores, datas, motivos de exclusão,
fundamentação narrativa.

## 9. Notificação extrajudicial (gerada pela skill irmã)

Gravada pela skill `notificacao-extrajudicial` em subpasta `notificacao/`
dentro da pasta da ação:

```
notificacao/Notificação Extrajudicial - [Banco] - [TESE].docx
```

Mantém hífen comum entre campos (não travessão) por compatibilidade com os
templates DOCX da skill irmã.

## 10. Contrato de prestação de serviços

```
Contrato de prestação de serviços advocatícios.pdf
```

NÃO integra o kit processual. Mantém na pasta `0. Kit/` apenas. Nunca colocar
nas pastas de ação.

## 11. Termos e fotos auxiliares (pasta `0. Kit/`)

```
Termo de atendimento e consentimento LGPD.pdf
KIT - assinado.pdf                                           (kit completo assinado)
KIT - modelo em branco.docx                                  (modelo editável Word, sem assinatura)
KIT - modelo em branco.pdf                                   (modelo PDF sem assinatura)
Foto de cautela - assinatura 1.jpg
Foto de cautela - assinatura 2.jpg
Vídeo do cliente.mp4
Senha INSS.txt                                               (ou .jpg se foi foto)
Senha gov.br.txt
```

## Regras gerais

- Numeração 0/2/3/4/5/6/7/8 é fixa e canônica.
- A posição "1" não é usada (reservada historicamente, mantida para compatibilidade).
- Sufixos decimais (3.1, 3.2, 3.3, 5.1, 5.2) são para variantes do mesmo grupo.
- **Separador após o número:** SEMPRE ponto seguido de espaço (`2. `, `3. `, `3.1 `, `5.1 `). Nunca mais hífen colado (`2-`).
- **Separador entre campos da procuração:** SEMPRE travessão `–` (U+2013) com espaços (` – `). Nunca hífen comum nem barra.
- **Separador entre descritor e nome próprio:** hífen comum `-` com espaços (` - `).
- Caracteres permitidos no nome: letras, números, espaços, ponto, hífen, travessão, parênteses, vírgulas, ponto-e-vírgula.
- Caracteres proibidos: barra `/`, contrabarra `\`, asterisco `*`, dois-pontos `:`, aspas, `<`, `>`, `?`, `|`.
- Acentos são permitidos.
- Ordem do banco no nome da procuração: usar nome humano amigável (`Banco Itaú Consignado`, `Caixa Econômica Federal`, `Banco BMG`), não o nome jurídico completo (`BANCO BMG S.A.`).
