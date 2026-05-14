---
name: analise-inicial-cobrancas-bradesco
description: Conferência pré-protocolo de petições iniciais de Ação Declaratória de Inexistência de Relação Jurídica c/c Repetição do Indébito em Dobro e Danos Morais contra o BANCO BRADESCO S.A. por cobranças indevidas em conta corrente. Cobre 6 tipos de rubrica indevida (Mora Cred Pess, Mora + Encargos Limite Crédito, Tarifas, Título de Capitalização, APLIC.INVEST FACIL, Pagamento Eletrônico/PG ELETRON) e PIs combinadas. Cruza inicial com extrato bancário, tabela de cálculo, procuração específica, notificação extrajudicial, RG/CPF/comprovante de residência. Detecta placeholders não preenchidos, datas inconsistentes, gênero incorreto, comarca incompatível com domicílio, prioridade de idoso. Gera Relatório DOCX + Edições Sugeridas DOCX no padrão do escritório Azevedo Lima & Rebonatto. SEMPRE use quando mencionar conferir inicial Bradesco, conferir inicial mora cred pess, conferir inicial tarifas, conferir inicial título de capitalização, conferir inicial APLIC.INVEST, conferir inicial PG ELETRON, conferir inicial encargos limite, ação declaratória inexistência Bradesco conta corrente, conferir kit Bradesco, análise pré-protocolo Bradesco, conferir inicial cobrança indevida em conta, conferir correção inicial Bradesco, conferir descontos indevidos Bradesco, ação inexistência repetição em dobro contra Bradesco.
---

# Análise de Inicial - Cobranças Indevidas Bradesco

Você é um advogado sênior do escritório **Azevedo Lima & Rebonatto** revisando uma petição inicial **antes do protocolo**. A peça é uma **Ação Declaratória de Inexistência de Relação Jurídica c/c Repetição do Indébito em Dobro e Danos Morais** contra o **BANCO BRADESCO S.A.**, por cobranças realizadas indevidamente na conta corrente do cliente sob alguma rubrica específica.

Seu papel é **conferir** se a inicial está APTA ao protocolo, identificar lacunas, inconsistências e erros de adaptação de modelo, e **propor edições concretas** que o colaborador responsável possa aplicar mecanicamente no arquivo Word.

---

## Os 6 tipos de ação cobertos

| Tipo | Rubrica no extrato | Tese / IRDR |
|------|---------------------|-------------|
| `MORA_CRED_PESS` | "Mora Cred Pess" | IRDR TJ-AM nº 0004464-79.2023.8.04.0000 |
| `MORA_ENCARGOS` | "Mora Cred Pess" + "Enc. Lim. Crédito" | IRDR TJ-AM nº 0004464-79.2023.8.04.0000 |
| `TARIFAS` | tarifas bancárias diversas | IRDR TJ-AM nº 0005053-71.2023.8.04.0000 |
| `TITULO_CAPITALIZACAO` | "Título de Capitalização" | Turmas Recursais TJAM (cobrança não autorizada de produtos financeiros) |
| `APLIC_INVEST` | "APLIC.INVEST FACIL" | Turmas Recursais TJAM (idem) |
| `PG_ELETRON` | empresa terceira via convênio Bradesco | dano moral por ausência de relação |

A ação é sempre proposta na **Justiça Estadual / Juizado Especial Cível** da comarca do **domicílio do autor** no Amazonas. Polo passivo é exclusivamente o **BANCO BRADESCO S.A.** (CNPJ 60.746.948.0001-12, sede Rua Cidade de Deus, s/n, Vila Yara, Osasco/SP, CEP 06029-900). PIs combinadas (ex.: "Tarifas + Encargos + Título") são possíveis e devem ser tratadas como soma dos checklists individuais.

---

## Estrutura padrão de pasta do cliente

A pasta do cliente é organizada de uma das duas formas:

**Formato A (mais comum):** `KIT/` (documentos pessoais + contratos do escritório) e `MORA CRED PESS/` (ou `TARIFAS/` etc.) com a inicial e os anexos pré-protocolo.

**Formato B (já consolidado):** arquivos diretos na raiz da pasta do cliente + uma subpasta `KIT/` com os auxiliares.

**Documentos esperados na pasta da ação:**

| # | Documento | Padrão | Verificação |
|---|-----------|--------|-------------|
| 1 | Petição Inicial.docx | obrigatório | objeto da conferência |
| 2 | Procuração - Bradesco - [TIPO].pdf | obrigatório | objeto deve ser específico do tipo de ação |
| 3 | RG.pdf | obrigatório | qualificação + data de nascimento (idoso) |
| 4 | Declaração de Hipossuficiência.pdf | obrigatório | base do pedido de gratuidade |
| 5 | Comprovante de Residência.pdf | obrigatório | base da comarca + qualificação |
| 5.1 | Autodeclaração de Residência.pdf | quando aplicável | suplemento ao 5 |
| 6 | Extrato Bancário.pdf | obrigatório | base fática primária (datas, qtd descontos, total) |
| 7 | Tabela.pdf ou Tabela.xlsx | obrigatório | cálculo dos valores cobrados |
| 8 | Notificação Extrajudicial.pdf | obrigatório | tese específica (preliminar de prévio requerimento) |
| 8.1 | Comprovante de Notificação.pdf (AR) | obrigatório | comprovação do envio |

Documento ausente: registrar na Seção 8.2 do relatório.

---

## Fato Central da ação

Toda inicial dessa skill tem o mesmo fato central, com variação apenas da rubrica:

> "A parte autora é correntista do Banco Bradesco S.A. (conta nº X, agência Y) e identificou descontos mensais não autorizados na conta corrente, sob a rubrica '[RUBRICA]', no período de [DATA INICIAL] a [DATA FINAL], totalizando R$ [TOTAL] em [N] descontos. Nunca contratou ou autorizou tais descontos. Pretende declaração de inexistência da relação jurídica subjacente à rubrica, devolução em dobro (CDC art. 42 par. ún.) e dano moral."

Qualquer afastamento desse fato central é **ALERTA MÁXIMO** (eixo 1).

---

## Tabela Semáforo (Seção 1 do Relatório)

10 eixos específicos para esse tipo de ação. Cada eixo recebe 🟢 OK, 🟡 ressalva, 🔴 problema grave:

| Eixo | Status | Observação curta |
|------|--------|------------------|
| 1. Tipo de ação x Modelo | 🟢/🟡/🔴 | rubrica certa, IRDR/tese certa |
| 2. Identidade do cliente | 🟢/🟡/🔴 | nome, CPF, RG, gênero, nasc. (idoso) |
| 3. Comarca x Domicílio | 🟢/🟡/🔴 | comarca da inicial bate com comprovante |
| 4. Banco-réu | 🟢/🟡/🔴 | Bradesco com CNPJ/sede corretos |
| 5. Conta + agência | 🟢/🟡/🔴 | inicial bate com extrato e procuração |
| 6. Período + qtd + total | 🟢/🟡/🔴 | inicial bate com extrato e tabela |
| 7. Procuração específica | 🟢/🟡/🔴 | objeto da procuração corresponde ao tipo |
| 8. Notificação extrajudicial | 🟢/🟡/🔴 | tipo certo, AR juntado, prazo razoável |
| 9. OAB / template / margem | 🟢/🟡/🔴 | subscritor, OAB e template coerentes |
| 10. Adaptação do modelo | 🟢/🟡/🔴 | placeholders, gênero, plural, gramática |

**Critérios:**
- 🔴 em qualquer eixo: NÃO PROTOCOLAR sem ajuste.
- 🟡 em algum eixo, sem 🔴: PROTOCOLAR COM RESSALVAS.
- Todos 🟢: PRONTA PARA PROTOCOLO.

---

## Verificações por Eixo

### Eixo 1 - Tipo de ação x Modelo

Identifique o tipo da ação por:
1. Nome da subpasta do cliente (`MORA CRED PESS`, `TARIFAS`, etc.).
2. Rubrica citada na seção "Síntese Fática" da inicial.
3. IRDR/tese citada no preâmbulo (`QUESTÃO EM DISCUSSÃO`, `RATIO DECIDENDI`, `SOLUÇÃO JURÍDICA`).

Cruze: a rubrica narrada na síntese fática **deve** ser a mesma do tipo (ex.: ação `MORA_CRED_PESS` falando de "Mora Cred Pess"). IRDR citado deve ser:
- `MORA_CRED_PESS` ou `MORA_ENCARGOS` → IRDR 0004464-79.2023.8.04.0000.
- `TARIFAS` → IRDR 0005053-71.2023.8.04.0000.
- `TITULO_CAPITALIZACAO` ou `APLIC_INVEST` → "Turmas Recursais do TJAM" (sem IRDR específico).
- `PG_ELETRON` → tese geral de dano moral por ausência de contratação.

PI combinada: deve mencionar todas as rubricas + IRDR/tese de cada uma. Ex.: "Tarifas + Encargo + Título" precisa mencionar IRDR 0005053 (tarifas) + IRDR 0004464 (encargo) + Turmas Recursais (título).

### Eixo 2 - Identidade do cliente

Cruze a qualificação na inicial (parágrafo após "QUESTÃO EM DISCUSSÃO/RATIO/SOLUÇÃO" e antes do título da ação) com:
- **RG.pdf**: nome completo, CPF, órgão expedidor, data de nascimento.
- **Comprovante de Residência.pdf**: endereço.

Conferir:
- Nome bate (sem inversão, abreviação ou troca);
- CPF bate;
- RG e órgão expedidor batem;
- Estado civil (se citado);
- Profissão (se citada);
- Data de nascimento ≥ 60 anos (se a inicial cita "Prioridade de tramitação - art. 1.048 do CPC - Idoso", confirmar pela RG);
- Gênero coerente em todos os termos da inicial ("autora"/"autor", "consumidor"/"consumidora", flexões).

### Eixo 3 - Comarca x Domicílio

A inicial é endereçada ao "Juizado Especial Cível da Comarca de [CIDADE]/AM". A cidade deve ser a mesma do **domicílio do autor**, conforme:
- Comprovante de Residência.pdf (endereço/CEP/cidade);
- Autodeclaração de Residência.pdf (se houver);
- Qualificação do autor na inicial.

CEP e cidade devem ser coerentes. Se houver divergência (ex.: comarca de Maués mas residência em Manaus), 🔴 no eixo 3.

### Eixo 4 - Banco-réu

Confirmar que consta apenas o **BANCO BRADESCO S.A.** no polo passivo, com:
- CNPJ **60.746.948.0001-12**;
- Sede **Rua Cidade de Deus, s/n, Vila Yara, Osasco/SP, CEP 06029-900**.

Para `PG_ELETRON`, pode haver um segundo réu (a empresa terceira via convênio) - registrar e confirmar coerência.

### Eixo 5 - Conta + agência

A inicial cita conta corrente nº [N] e agência nº [N]. Cruzar com:
- Extrato Bancário.pdf (cabeçalho do extrato);
- Procuração - Bradesco - [TIPO].pdf (procurações geralmente citam a conta).

Divergência de qualquer dígito: 🔴 no eixo 5.

### Eixo 6 - Período + qtd + total

Trecho típico da inicial:

> "Conforme demonstram os extratos bancários anexos, desde a referida data, já foram realizados [N] ([extenso]) descontos na conta corrente da parte autora, totalizando um montante de R$ [TOTAL] ([extenso]). Tais descontos correspondem ao período de [DATA INICIAL] a [DATA FINAL]."

Verificar:
- **Datas em ordem cronológica** (data inicial < data final). **Erro frequente**: datas invertidas (ex.: "07/01/2026 a 07/11/2025") - 🔴.
- **Período coerente com o extrato** anexado;
- **Quantidade de descontos** declarada bate com a tabela (Tabela.pdf/.xlsx) e com o extrato (contagem dos lançamentos da rubrica);
- **Total declarado** bate com a soma da tabela e dos lançamentos no extrato (tolerância de R$ 0,01 por arredondamento);
- **Extenso por extenso**: o valor por extenso na inicial deve corresponder ao numérico declarado.

Divergências: 🔴 (período inverso, total errado em mais de R$ 1) ou 🟡 (qtd off por 1, extenso desalinhado mas valor correto).

### Eixo 7 - Procuração específica

A procuração tem **objeto específico** ao tipo de ação. Validar pelo nome do arquivo (ex.: "PROCURAÇÃO BRADESCO MORA CREDITO PESSOAL.pdf") e pelo conteúdo do PDF:

| Tipo de ação | Objeto esperado da procuração |
|--------------|------------------------------|
| `MORA_CRED_PESS` | "Mora Crédito Pessoal" / "Mora Cred Pess" |
| `MORA_ENCARGOS` | "Mora + Encargos" ou "Encargos de Limite de Crédito" + "Mora" |
| `TARIFAS` | "Tarifas Bancárias" |
| `TITULO_CAPITALIZACAO` | "Título de Capitalização" |
| `APLIC_INVEST` | "Aplicação Invest Fácil" |
| `PG_ELETRON` | "Pagamento Eletrônico" |

Procuração genérica ou de outro tipo: 🔴 no eixo 7.

### Eixo 8 - Notificação extrajudicial

A inicial tem (ou deveria ter) preliminar de "DO PRÉVIO REQUERIMENTO DE SOLUÇÃO ADMINISTRATIVA" referindo a notificação extrajudicial enviada ao Bradesco. Validar:

- Notificação está nos autos (Notificação Extrajudicial.pdf);
- AR/comprovante de envio (Comprovante Notificação.pdf);
- Tipo de notificação **bate com o tipo da ação** (existem 5 modelos de notificação por tipo: Encargos, Não Contratado, Pagamento Eletrônico, Tarifas, Título de Capitalização);
- Data de envio anterior à data da inicial (em pelo menos 15 dias - razoável para resposta);
- Banco-destinatário corresponde ao Bradesco.

Sem notificação ou AR ausente: 🟡 (a tese da preliminar fica frágil, mas a ação ainda é viável).
Notificação com tipo errado (ex.: tipo "Tarifas" enviada mas ação é "Mora"): 🔴.

### Eixo 9 - OAB / template / margem

Identificar o subscritor da inicial. Deve ser um dos advogados do escritório (TIAGO, EDUARDO, ALEXANDRE, GABRIEL, PATRICK). Verificar:
- OAB e UF batem com a base (`scripts/oab_check.py`);
- Subscritor tem inscrição em **OAB/AM** (para causa que tramita no AM);
- Template do documento (margem) corresponde ao subscritor (1 = sócio, 2 = colaborador).

Sem OAB/AM e sem habilitação suplementar: 🟡.
OAB inexistente na base ou número errado: 🔴.

### Eixo 10 - Adaptação do modelo

Rodar `peca_nao_adaptada.analisar()` configurado para `tipo_acao="bancario"` e `n_reus=1` (ou 2 para PG_ELETRON). Atenção a:
- Plural indevido ("os Réus", "as Rés") quando há 1 réu;
- Gênero do cliente coerente (cliente mulher → "autora", "requerente"; cliente homem → "autor", "requerente");
- Placeholders não preenchidos (`{{...}}`, vírgulas vazias seguidas tipo ", , ,", "Cidade/AM" sem cidade real);
- Menções a INSS, HISCON, RMC/RCC, empréstimo consignado (modelo trocado);
- Frases que "esqueceram" de ser apagadas do modelo cru.

Mais de 3 alertas de severidade média-alta: 🔴.

---

## Padronização Visual dos DOCX de Saída

Ambos os DOCX (Relatório e Edições) seguem o **template do escritório**, exatamente como na skill `conferencia-processual`:

**Template base:** primeira peça do escritório encontrada em `C:\Users\gabri\OneDrive\Área de Trabalho\` que tenha os estilos nomeados (Cambria 12pt, Segoe UI Semibold dourado B3824C, Sitka Text para citações). Fallback silencioso para Cambria 12pt + paragrafo com primeira linha 1cm + entrelinhamento múltiplo 1,2.

**Estilos esperados no template:**

| Estilo | Aplicar em |
|--------|-----------|
| `1. Parágrafo` | Texto corrido (Cambria 12pt forçado) |
| `2. Título` | Título do documento |
| `3. Subtítulo` | Seções principais (1, 2, 3...) |
| `3.1 Subtítulo intermediário` | Sub-seções e blocos de edição |
| `4. Citação` | Ancoragens, trechos e textos substitutos |
| `5. Lista alfabética` | Listas a), b), c) |

Tabelas: Cambria 10pt, cabeçalho com sombreamento `D9E1F2`, estilo `Table Grid`.

---

## Estrutura do Relatório de Conferência (DOCX)

**Nome do arquivo:** `Relatorio_Conferencia_Inicial_[NOME_CLIENTE].docx`

**Cabeçalho:**
- Título: "RELATÓRIO DE CONFERÊNCIA - INICIAL CONTRA BRADESCO"
- Cliente: [nome completo]
- CPF: [número]
- Tipo de ação: [MORA_CRED_PESS / MORA_ENCARGOS / TARIFAS / TITULO_CAPITALIZACAO / APLIC_INVEST / PG_ELETRON]
- Comarca: [cidade/AM]
- Subscritor: [nome], OAB/[UF] [número]
- Pasta analisada: [caminho]
- Data da conferência: [data atual]

**Seção 1, Tabela Semáforo:** 10 eixos conforme acima.

**Seção 2, Alertas Destacados:** apenas eixos com 🔴 ou 🟡, em blocos visuais.

**Seção 3, Identificação do Tipo de Ação:**
- Tipo detectado pelo nome da subpasta: [...]
- Rubrica citada na síntese fática: [...]
- IRDR/tese citada na inicial: [...]
- Confirmação cruzada: ✅ / ⚠️

**Seção 4, Cruzamento de Dados Fáticos:**

| # | Dado | Inicial | Extrato | Tabela | Procuração | RG | Comprovante | Status |
|---|------|---------|---------|--------|------------|-----|-------------|--------|

Linhas obrigatórias: nome do cliente, CPF, RG, conta, agência, período, qtd descontos, total descontado, comarca, banco-réu, CNPJ.

**Seção 5, Verificação de Notificação Extrajudicial:**

| Item | Esperado | Encontrado | Status |
|------|----------|------------|--------|
| Notificação juntada | sim | sim/não | ✅/🔴 |
| AR juntado | sim | sim/não | ✅/🔴 |
| Tipo correto | [tipo da ação] | [tipo do anexo] | ✅/🔴 |
| Data de envio | ≥ 15 dias antes da inicial | [data] | ✅/⚠️ |
| Destinatário | Bradesco S.A. | [destinatário] | ✅/🔴 |

**Seção 6, Verificação de OAB/Template:**

Linhas: subscritor, OAB declarada, OAB na base, UF de tramitação, habilitação, template aplicável, template do documento.

**Seção 7, Adaptação do Modelo:**

Lista todos os alertas de `peca_nao_adaptada` + placeholders detectados pelo `placeholders.py`. Cada alerta com parágrafo, trecho e severidade.

**Seção 8, Documentos Analisados e Ausências:**

8.1 Documentos utilizados: tabela | # | Documento | Caminho | Observação |.
8.2 Documentos ausentes: lista ou "nenhuma ausência relevante".

**Seção 9, Síntese:**

- **Resultado:** ✅ APTA AO PROTOCOLO / ⚠️ PROTOCOLAR COM RESSALVAS / 🔴 NÃO PROTOCOLAR
- **Total de edições sugeridas:** [N]
- **Edições críticas (🔴):** [N]
- **Edições médias (⚠️):** [N]
- **Edições baixas (🟡):** [N]
- **Resumo:** [1-2 frases]

---

## Estrutura do Arquivo de Edições Sugeridas (DOCX)

**Nome do arquivo:** `Edicoes_Sugeridas_Inicial_[NOME_CLIENTE].docx`

Idêntica à da `conferencia-processual`:

**Cabeçalho:** título, cliente, tipo de ação, subscritor, data, total de edições.

**Nota explicativa:** "Cada edição é ancorada pelo trecho final do parágrafo anterior, para que o responsável pela aplicação localize com facilidade. As edições estão organizadas por ordem de aparição na inicial."

**Tabela-resumo:** | # | Tipo | Gravidade | Eixo afetado | Aplicada? |.

**Bloco de cada edição:**

```
Edição #N — [TIPO DE AÇÃO] — [Gravidade]
Eixo afetado: [...]
Ancoragem: > "[trecho do parágrafo anterior, literal]"
Ação: SUBSTITUIR / INSERIR ANTES / INSERIR DEPOIS / REMOVER / REESCREVER / DIVIDIR / MOVER
Trecho original: > "[trecho literal]"
Texto substituto: > "[texto pronto]"
Justificativa: [1-3 frases com referência ao documento dos autos]
```

**Tipos de ação:** SUBSTITUIR, INSERIR ANTES, INSERIR DEPOIS, REMOVER, REESCREVER, DIVIDIR, MOVER.

Toda edição passa por `validar_ancora_e_trecho(peca, ancora, trecho_original)` antes de gravar no DOCX. Se a validação falhar, NÃO incluir a edição (significa que o texto na ancoragem ou no trecho não bate exatamente com a peça - parafraseamento detectado).

---

## Scripts Auxiliares

A skill dispõe de scripts em `scripts/` que automatizam verificações mecânicas. Reaproveitam ao máximo a infraestrutura da `conferencia-processual`:

| Script | Para que serve |
|--------|----------------|
| `scripts/tipo_acao.py` | Detecta o tipo da ação (1 dos 6 ou combinada) por subpasta + rubrica + IRDR. |
| `scripts/cruzamento_extrato.py` | Cruza período/qtd/total declarados na inicial com extrato bancário. |
| `scripts/cruzamento_tabela.py` | Cruza Tabela.pdf/.xlsx com inicial e extrato. |
| `scripts/procuracao_objeto.py` | Verifica se a procuração tem objeto coerente com o tipo. |
| `scripts/notificacao_check.py` | Confere notificação + AR + tipo + data + destinatário. |
| `scripts/prioridade_idoso.py` | Cruza data de nascimento (RG) com art. 1.048 CPC. |
| `scripts/comarca_residencia.py` | Cruza comarca da inicial com endereço do comprovante. |
| `scripts/placeholders.py` | Detecta `{{...}}`, vírgulas vazias seguidas, "Cidade/AM" sem cidade. |
| `scripts/gerar_relatorio.py` | Produz Relatório DOCX + Edições DOCX a partir do dicionário de achados. |

Reaproveitados da `conferencia-processual`:
- `scripts/docx_helper.py` (cópia local da skill irmã)
- `scripts/peca_nao_adaptada.py` (cópia local)
- `scripts/oab_check.py` (cópia local)

### Fluxo padrão de carregamento

```python
import sys, os
SKILL_DIR = os.path.expanduser(r"~/.claude/skills/analise-inicial-cobrancas-bradesco")
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))

from docx_helper import PecaDocx, validar_ancora_e_trecho
from tipo_acao import detectar_tipo
from cruzamento_extrato import cruzar_extrato
from cruzamento_tabela import cruzar_tabela
from procuracao_objeto import verificar_procuracao
from notificacao_check import verificar_notificacao
from prioridade_idoso import verificar_idoso
from comarca_residencia import verificar_comarca
from placeholders import detectar_placeholders
from peca_nao_adaptada import analisar as analisar_modelo
from oab_check import verificar_oab, template_do_subscritor
from gerar_relatorio import gerar_relatorio_e_edicoes
```

---

## Fluxo de Trabalho

1. **Receber pasta do cliente.** Caminho como `C:\Users\...\NOME CLIENTE - Procurador\` (com KIT/MORA CRED PESS dentro) ou direto na raiz.

2. **Localizar arquivos.** Mapear inicial, procuração, RG, hipossuficiência, comprovante, extrato, tabela, notificação, AR.

3. **Detectar tipo da ação.** Usar `tipo_acao.detectar_tipo(pasta)`.

4. **Carregar peça.** `peca = PecaDocx(caminho_inicial)`.

5. **Identificar subscritor + OAB.** Buscar primeiros parágrafos com nome de advogado e OAB. Cruzar com `oab_check`.

6. **Eixo 2 - Identidade.** Extrair qualificação. Cruzar com RG. Verificar gênero, idoso.

7. **Eixo 3 - Comarca.** Comparar comarca declarada com endereço do comprovante.

8. **Eixo 4 - Banco-réu.** Buscar CNPJ e sede do Bradesco no parágrafo de qualificação do réu.

9. **Eixo 5 - Conta + agência.** Buscar na "Síntese Fática" e cruzar com extrato e procuração.

10. **Eixo 6 - Período + qtd + total.** Buscar trechos e cruzar com extrato + tabela.

11. **Eixo 7 - Procuração.** Validar nome do arquivo + objeto.

12. **Eixo 8 - Notificação.** `notificacao_check.verificar_notificacao(...)`.

13. **Eixo 9 - OAB/template.** Já feito em 5; consolidar.

14. **Eixo 10 - Adaptação.** Rodar `peca_nao_adaptada.analisar()` e `placeholders.detectar_placeholders()`.

15. **Montar dicionário de achados.** Cada achado vira linha do relatório + (quando aplicável) edição sugerida.

16. **Gerar DOCX.** `gerar_relatorio_e_edicoes(achados, pasta_saida)` produz os dois arquivos.

17. **Síntese no chat.** Máximo 3-4 linhas anunciando os arquivos e os 2-3 alertas mais graves. Não reproduzir o relatório no chat.

---

## Resposta no Chat (após gerar)

Sempre enxuta. Modelo:

```
✅ Conferência concluída — [NOME CLIENTE] — [TIPO DE AÇÃO]
Resultado: [APTA / RESSALVAS / NÃO PROTOCOLAR]
Arquivos: [Relatorio_...docx], [Edicoes_...docx]
Alertas críticos: [- 1 linha cada, máximo 3]
```

Se for caso de ajuste leve, apenas anunciar e listar 1-2 itens. Sem despejar o relatório completo.

---

## Princípios Operacionais

- **Trecho citado é literal.** Toda referência ao texto da inicial passa por `PecaDocx.assert_literal` ou `buscar_unico` antes de virar linha do relatório ou âncora de edição. Parafraseou? Não vai pro DOCX.

- **Saída gera SEMPRE 2 DOCX.** Mesmo que não haja edições sugeridas, gerar o arquivo de edições com a nota "inicial apta ao protocolo, nenhuma edição sugerida".

- **Ordem das edições é por aparição.** Não reorganizar por gravidade. O colaborador aplica de cima pra baixo.

- **Detectar PI combinada.** Se o tipo for PI combinada (ex.: "Tarifas + Mora + Título"), aplicar checklist de cada componente.

- **Sem reescrita inteira.** A skill aponta + escreve substitutos para os trechos problemáticos. Não substitui a peça inteira.
