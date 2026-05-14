# Regras de Validação Documental

Este arquivo contém todas as verificações obrigatórias que devem ser realizadas antes de finalizar a organização do kit.

## Índice

1. [Verificação de Identidade Documental](#1-verificação-de-identidade-documental)
2. [Verificação de Assinatura](#2-verificação-de-assinatura)
3. [Verificação do Comprovante de Residência](#3-verificação-do-comprovante-de-residência)
4. [Declaração de Residência de Terceiro](#4-declaração-de-residência-de-terceiro)
5. [Documentos Obrigatórios Ausentes](#5-documentos-obrigatórios-ausentes)
6. [Validação de Integridade dos Documentos](#6-validação-de-integridade-dos-documentos)
7. [Verificação Cruzada — Procuração x Histórico de Crédito/Empréstimo](#7-verificação-cruzada--procuração-x-histórico-de-créditoempréstimo)
8. [Verificação de Classificação de Ação](#8-verificação-de-classificação-de-ação)

---

## 1. Verificação de Identidade Documental

Verificar correspondência entre:
- Nome do outorgante na procuração
- Nome nos documentos pessoais da parte autora
- Nome nos documentos assinados pelo cliente
- CPF na procuração vs. CPF no documento pessoal
- Endereço na procuração vs. comprovante de residência (quando possível)

**Exceções:** A verificação de correspondência NÃO se aplica a:
- Rogado
- Testemunhas
- Proprietário do imóvel (terceiro)

Esses nomes podem divergir do nome da parte autora sem gerar pendência.

**Se houver divergência:** Registrar na Planilha de Pendências. Divergências de CPF ou endereço na procuração são **pendências críticas**, pois podem exigir que a procuração seja refeita.

---

## 2. Verificação de Assinatura

### Método de verificação — Análise visual obrigatória
A verificação de assinatura deve ser feita por **análise visual das páginas convertidas em imagem** (usando `pdftoppm` ou similar). Não basta verificar o texto extraído do PDF — documentos escaneados frequentemente não possuem texto extraível.

A assinatura pode ser de dois tipos:
- **Assinatura física (manuscrita):** Procure por traços manuscritos, rubricas, campos preenchidos à mão e impressões digitais.
- **Assinatura digital (eletrônica):** Procure por selos de certificado digital, carimbos de assinatura eletrônica (ICP-Brasil, DocuSign, ClickSign, ZapSign, D4Sign, Adobe Sign), metadados de assinatura no PDF, ou texto indicando que o documento foi assinado digitalmente.

Ambos os tipos são válidos e conferem validade ao documento.

### Documentos que DEVEM estar assinados
Todos os documentos que exigem assinatura do cliente devem estar devidamente assinados (física ou digitalmente). Se algum não estiver, registrar pendência. Documentos sem nenhum tipo de assinatura que deveriam tê-la são **modelos/editáveis** e devem ser MOVIDOS para a pasta `0. Kit` (nunca excluídos), nunca colocados nas pastas de ação.

### Documentos que NÃO devem conter assinatura do cliente
- Histórico de crédito
- Contrato de empréstimo (documento fornecido pelo banco)

A ausência de assinatura nesses documentos NÃO é pendência. Porém, se esses documentos apresentarem assinatura atribuída ao cliente, registrar na Planilha de Pendências — pode indicar inconsistência documental.

---

## 3. Verificação do Comprovante de Residência

### Autenticidade
Analisar visualmente o documento verificando:
- Incoerência de fontes ou formatação
- Cortes, sobreposições ou áreas borradas
- Desalinhamento de textos
- Datas inconsistentes
- Ausência de elementos comuns (logotipo da concessionária, padrão gráfico, layout típico da fatura)
- Sinais de edição digital

**Se houver indícios de falsificação:** NÃO descartar o documento. Registrar na Planilha de Pendências:
- Categoria: Comprovante de residência
- Pendência: Possível falsificação ou indícios de adulteração documental
- Observação: Descrever os elementos que geraram a suspeita

---

## 4. Declaração de Residência de Terceiro

Quando o comprovante for substituído por declaração de terceiro, verificar:

1. Existe documento de identificação do declarante (RG ou equivalente)?
2. O nome no documento de identificação corresponde ao nome na declaração?
3. A declaração está devidamente assinada?
4. O documento de identificação está legível?

**Se qualquer verificação falhar:** Registrar na Planilha de Pendências:
- Categoria: Declaração de residência
- Pendência: Declarante sem documento de identificação ou divergência de nome
- Observação: Descrever a inconsistência encontrada

### Verificação de possível falsificação da declaração
Mesmos critérios do comprovante de residência (seção 3 acima).

### Regra de ausência
Se existir declaração de residência de terceiro mas NÃO houver RG do declarante:
- Documento faltante: RG do declarante da residência
- Observação: Necessário para validar declaração

### Validação final obrigatória
Antes de finalizar, verificar:
- Nome do declarante na declaração corresponde ao nome do RG apresentado
- Declaração está assinada
- RG do declarante está legível

---

## 5. Documentos Obrigatórios Ausentes

Qualquer ausência de documento que, pela estrutura do kit, deveria constar, é pendência obrigatória.

Documentos tipicamente obrigatórios (variam por tipo de ação):
- Procuração
- Documentos pessoais (RG/CPF ou CNH)
- Declaração de hipossuficiência
- Comprovante de residência
- Histórico de empréstimos (quando aplicável)
- Histórico de créditos (quando aplicável)

---

## 6. Validação de Integridade dos Documentos

Verificar que:
- Nenhum documento está misturado com outro em um mesmo PDF
- Procurações contêm APENAS procurações
- Procurações estão como PDFs separados na subpasta do banco correspondente
- Estrutura de 3 níveis está correta (Tipo de ação → Banco → Documentos)
- Declaração de hipossuficiência contém APENAS a declaração
- Documentos de pessoas diferentes não estão no mesmo arquivo
- Todas as imagens foram convertidas para PDF
- Documentos organizados não estão duplicados fora das pastas de ação

### 6.1 Armadilha de KIT compactado mal fatiado — conferir conteúdo página a página

Quando o material chega como um KIT compactado (PDF único, todas as páginas
do kit em ordem assinada) e o fatiamento é feito por inferência de bordas
visuais, **é frequente que páginas terminem na pasta errada**. Casos reais
encontrados em batch (5 clientes do captador Elizio, 2026-05-11):

| Cliente | Erro detectado |
|---|---|
| ADALTO | `3. RG e CPF.pdf` continha CPF de Santana (rogada) e CIN de Francisca (testemunha) |
| ADALTO | `4. Declaração de hipossuficiência.pdf` tinha o Contrato de Honorários colado na pg1 |
| ALBERTO | `3. RG e CPF.pdf` continha Declaração de Residência e CPF de testemunha (nada do Alberto) |
| ALBERTO | `4. Declaração de hipossuficiência.pdf` tinha Contrato de Honorários na pg1 |
| ALDENICE | Pasta praticamente vazia — faltavam procuração, hipossuficiência, comprovante, declaração de domicílio e 3.1/3.2/3.3 |

**Procedimento obrigatório após o fatiamento automático:**

1. Abrir cada PDF numerado (`3. RG e CPF.pdf`, `4. Declaração...`, `5. Comprovante...`) e confirmar visualmente que o conteúdo corresponde ao nome do arquivo. Não basta o pipeline ter rodado sem erro.
2. Conferir especificamente os limites entre documentos: a primeira página de cada PDF deve ser do documento certo (não o "rabo" do documento anterior).
3. Quando o cliente tem **assinatura a rogo**, validar que todos os 3 PDFs auxiliares (3.1, 3.2, 3.3) existem e estão nomeados com o NOME COMPLETO certo — confundir rogado com testemunha 1 é erro comum.
4. Se o agente fatiou pelos marcadores do KIT mas faltam PDFs esperados, abrir o KIT compactado original e mapear página por página. Pasta vazia ou minúscula é sinal de fatiamento que falhou silenciosamente.
5. Registrar como pendência crítica qualquer PDF cujo conteúdo não corresponda ao nome, mesmo se foi gerado pelo pipeline.

---

## 7. Verificação Cruzada — Procuração x Histórico de Crédito/Empréstimo

Esta verificação é **obrigatória** e serve para confirmar a viabilidade da ação judicial.

### Procedimento
Para cada procuração:
1. Extraia o(s) número(s) de contrato mencionado(s) na procuração.
2. Localize cada número de contrato no histórico de crédito e/ou histórico de empréstimo do cliente.
3. Verifique se o contrato existe e se o tipo corresponde ao que a procuração indica.

### Pendências a registrar

**Contrato não localizado:**
- Categoria: Procuração / Verificação cruzada
- Pendência: Contrato não localizado no histórico
- Observação: "Contrato [número] mencionado na procuração do [Banco] não foi encontrado no histórico de crédito/empréstimo. Ação pode ser inviabilizada."

**Número do contrato incorreto (possível erro de digitação):**
- Categoria: Procuração / Verificação cruzada
- Pendência: Possível erro no número do contrato
- Observação: "Contrato [número na procuração] não encontrado no histórico, mas existe contrato similar [número no histórico] do mesmo banco. Verificar se houve erro de digitação na procuração."

**Divergência de tipo:**
- Categoria: Procuração / Verificação cruzada
- Pendência: Divergência entre procuração e histórico
- Observação: "Procuração classifica contrato [número] como [tipo na procuração], mas o histórico indica que se trata de [tipo no histórico]."

**Dados pessoais incorretos na procuração:**
Verificar se os dados do cliente na procuração correspondem aos documentos pessoais (RG, CPF, CNH). Conferir:
- CPF do outorgante na procuração vs. CPF no documento pessoal
- Nome completo do outorgante vs. nome no documento pessoal
- Endereço na procuração vs. comprovante de residência (quando possível verificar)

Se houver divergência:
- Categoria: Procuração / Dados pessoais
- Pendência: Dados incorretos na procuração
- Observação: "[Dado] na procuração ([valor na procuração]) diverge do documento pessoal ([valor no documento]). Procuração pode precisar ser refeita."

---

## 8. Verificação de Classificação de Ação

Após a organização, verificar que a classificação de cada pasta de ação está correta:

- Pastas classificadas como **RMC** devem conter procurações que mencionem expressamente "RMC" ou "Reserva de Margem Consignável"
- Pastas classificadas como **RCC** devem conter procurações que mencionem expressamente "RCC" ou "Reserva de Cartão de Crédito Consignado"
- Se uma pasta foi classificada como RMC/RCC mas a procuração não contém esses termos expressamente, **reclassificar** conforme o texto real da procuração

**Se houver reclassificação:** Registrar na Planilha de Pendências:
- Categoria: Classificação de ação
- Pendência: Ação reclassificada
- Observação: "Pasta originalmente classificada como [tipo antigo], reclassificada para [tipo novo] conforme texto da procuração."

---

## Formato da Planilha de Pendências

Cada pendência deve conter:

| Coluna | Descrição |
|--------|-----------|
| Categoria | Tipo do documento (ex: Procuração, Comprovante de residência, Verificação cruzada) |
| Pendência | Descrição da pendência |
| Observação | Detalhamento da inconsistência |
| Status | "Pendente" (padrão) |
