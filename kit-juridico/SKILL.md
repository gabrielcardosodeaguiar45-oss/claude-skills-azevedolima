---
name: kit-juridico
description: |
  Organização automatizada de kits documentais jurídicos para escritórios de advocacia, com detecção de múltiplos benefícios INSS, parser de extrato HISCON, detecção de cadeias de fraude (refinanciamento, portabilidade, consolidação, fracionamento), grifo colorido por cadeia e geração de ESTUDO de cadeia em DOCX. Recebe pasta com documentos brutos (PDFs, imagens, Word) de um ou mais clientes e organiza em estrutura BENEFÍCIO/BANCO/ com numeração canônica, validação documental e Pendências.xlsx. Suporta processamento em lote.
  SEMPRE use esta skill quando o usuário mencionar: kit jurídico, organizar documentos de cliente, separar kit, montar pasta de ação, organizar pasta AL/AM/SC, RMC, RCC, empréstimo consignado, empréstimo não contratado, organizar procurações, organizar Bradesco, kit processual, montar kit de processo, processar kits em lote, cadeia de empréstimos, refinanciamento sucessivo.
---

# Kit Jurídico — Organização Documental Automatizada com Detecção de Cadeias

Esta skill recebe uma pasta com documentos brutos de cliente(s) e produz uma estrutura organizada, validada, com extratos grifados por cadeia e ESTUDO em DOCX por banco. O objetivo é **uma ação por cliente, por banco, por benefício** — agrupando bancos APENAS quando há cadeia inter-banco (portabilidade), conforme regras em `references/regras-cadeias.md`.

## Pré-requisitos

```bash
pip install pymupdf python-docx Pillow img2pdf openpyxl opencv-python --break-system-packages
```

## Regra de Escopo — Trabalhar APENAS na pasta selecionada

**REGRA ABSOLUTA E INVIOLÁVEL:** O processamento deve ser feito **exclusivamente dentro da pasta que o usuário selecionou**. Essa é a ÚNICA pasta com a qual você deve interagir.

- A pasta selecionada é o universo de trabalho. Tudo acontece dentro dela.
- NUNCA use `find`, `ls`, `locate` para buscar fora da pasta selecionada.
- NUNCA navegue para diretórios pai, irmãos ou qualquer caminho fora dela.
- NUNCA presuma que existem outros kits em outros locais do computador.
- Se a pasta não contém os documentos esperados, informe e peça que selecione a pasta correta — não saia procurando.
- Use SEMPRE caminhos relativos à pasta selecionada ao listar arquivos.

## Regra de Integridade — NUNCA excluir documentos

**REGRA ABSOLUTA E INVIOLÁVEL:** Nenhum arquivo pode ser excluído, removido, apagado ou deletado da pasta de trabalho. As únicas operações permitidas são **mover** (dentro da mesma pasta de cliente) e **copiar** (replicar documentos comuns nas subpastas de banco).

- NUNCA use `rm`, `del`, `unlink`, `shutil.remove`, `os.remove`, `Path.unlink()`, etc.
- NUNCA exclua arquivos "temporários", "duplicados" ou "desnecessários".
- Documentos não classificados, modelos em branco, fotos de cautela, vídeos, senhas → tudo vai para `0. Kit/`, nunca é excluído.
- Imagens originais, após convertidas em PDF, são MOVIDAS para `0. Kit/` — nunca excluídas.
- Os scripts auxiliares também respeitam essa regra: nenhum script contém lógica de exclusão.

## Estrutura final esperada

### Cliente com UM benefício INSS

```
[Cliente]/
├── 0. Kit/                              (sempre criada — auxiliares, modelos, mídia)
├── BANCO ITAÚ CONSIGNADO/               (1 banco = 1 ação)
│   ├── 2. Procuração – Banco Itaú Consignado – Contrato N.pdf
│   ├── 3. RG e CPF.pdf
│   ├── 4. Declaração de hipossuficiência.pdf
│   ├── 5. Comprovante de residência.pdf
│   ├── 6. Histórico de empréstimo (grifado).pdf
│   ├── 7. Histórico de créditos.pdf
│   ├── ESTUDO DE CADEIA - BANCO ITAÚ CONSIGNADO.docx
│   └── CALCULO_INDEBITO.xlsx            (planilha gerada com INPC + juros 1% + dobro + dano moral)
├── BANCO BMG - RMC-RCC/                 (cartão consignado — NÃO tem CALCULO_INDEBITO.xlsx)
└── Pendências.xlsx
```

> **CALCULO_INDEBITO.xlsx (gravado 13/05/2026):** gerado automaticamente para cada pasta de ação CONSIGNADO (não para RMC/RCC). Usa `skills/_common/calculadora_indebito.py` com regime fixo: correção INPC, juros 1% a.m. simples, dobro art. 42 CDC, dano moral R\$ 15k (1 contrato) ou R\$ 5k×N (2+). A skill `inicial-nao-contratado` lê esse Excel para usar o TOTAL GERAL como valor da causa.

> **Separadores (v2.2):** ponto após o número (`2. `, `3. `), travessão `–` entre campos da procuração (Banco – Contrato), hífen comum `-` entre descritor e nome de subdocumento (`3.1 - RG e CPF do rogado - NOME COMPLETO.pdf`). Regras completas em [`references/regras-nomenclatura.md`](references/regras-nomenclatura.md).

### Cliente com DOIS ou mais benefícios INSS (v2.4, paradigma Guilherme 2026-05-14)

Estrutura `<CLIENTE>/<BENEFÍCIO>/<TESE>/<BANCO>/[Contrato XXX/]`:

```
[Cliente]/
├── 0. Kit/
├── APOSENTADORIA/                       (NB principal — maiúsculas)
│   ├── Não contratado/
│   │   ├── BANCO BRADESCO/              (1 contrato → docs direto, sem subpasta)
│   │   │   ├── 2. Procuração – Bradesco – Contrato N.pdf
│   │   │   ├── 3. RG e CPF.pdf
│   │   │   ├── 4. Declaração de hipossuficiência.pdf
│   │   │   ├── 5. Comprovante de residência.pdf
│   │   │   ├── 6. Histórico de empréstimo - Extrato de Empréstimo - Aposentadoria.pdf
│   │   │   ├── 7. Histórico de créditos.pdf
│   │   │   └── notificacao/
│   │   └── BANCO DO BRASIL/             (3 contratos → subpastas Contrato XXX/)
│   │       ├── Contrato 114180212/
│   │       ├── Contrato 159730415/
│   │       ├── Contrato 185401944/
│   │       └── notificacao/
│   ├── RMC/BANCO PAN/                   (1 contrato → docs direto)
│   └── RCC/BANCO PAN/
└── PENSÃO/                              (segundo NB)
    └── Não contratado/
        ├── BANCO DO BRASIL/             (185402234)
        └── BANCO ITAU/
```

**Regras críticas para múltiplos benefícios:**

1. Cada contrato pertence a UM benefício, identificado pelo HISCON respectivo. Em `_estado_cliente.json`, o campo `contratos[i].beneficio_pasta` deve ser `APOSENTADORIA` ou `PENSAO` (sem til, para alinhar com o filtro da skill `notificacao-extrajudicial`).
2. **HISCON por benefício**: dentro de cada pasta-banco, deixe SÓ o HISCON do benefício correspondente (não duplicar os dois). Em `APOSENTADORIA/.../BANCO X/` → só `6. Histórico de empréstimo - Extrato de Empréstimo - Aposentadoria.pdf`.
3. HISCRE vem único do INSS cobrindo ambos os NBs — replicar nas duas árvores.
4. `pastas_acao[i].path_relativo` no formato `BENEFÍCIO/TESE/BANCO` (3 níveis).
5. Colapso de `Contrato XXX/`: aplicar SÓ se banco tem 2+ contratos no mesmo benefício; com 1 contrato, deixar docs direto na pasta do banco.
6. Pasta `notificacao/` SEM subpasta de banco interna quando há 1 só banco em cada pasta-de-ação (regra escritório 2026-05-14).

### Cliente com UM benefício INSS (formato simplificado)

Quando há apenas um benefício, omitir o nível BENEFÍCIO (estrutura plana TESE/BANCO):

```
[Cliente]/
├── 0. Kit/
├── Não contratado/BANCO X/
├── RMC/BANCO X/
└── RCC/BANCO X/
```

### Cliente com cadeia inter-banco (portabilidade)

Pasta combinada quando há cadeia atravessando bancos:

```
APOSENTADORIA/
├── BANCO ITAÚ CONSIGNADO + BANCO BMG/   (cadeia de portabilidade)
│   └── ESTUDO DE CADEIA - BANCO ITAÚ CONSIGNADO + BANCO BMG.docx
└── BANCO ITAÚ CONSIGNADO/               (contratos isolados sem cadeia inter-banco)
```

## Detecção de modo

Antes de processar, identifique:

**Individual:** pasta com documentos brutos de UM cliente.
**Lote:** pasta-mãe com subpastas (cada uma é um cliente). Processe um por um.
**Organização Parcial:** pasta já tem subpastas com numeração canônica. Analise antes de refazer; corrija apenas o que estiver errado.

Como detectar:
1. Liste o conteúdo da pasta indicada.
2. Se contém subpastas que por sua vez contêm arquivos → modo lote.
3. Se contém diretamente documentos → modo individual.
4. Se contém subpastas como `0. Kit`, `[BENEFÍCIO]/`, `BANCO X/` → modo organização parcial.
5. Em caso de dúvida, pergunte ao usuário.

## Fluxo de Trabalho (12 fases)

Execute estas fases em ordem. Use os scripts em `scripts/` para tarefas determinísticas. Use sua leitura visual (Read tool) para tarefas que exigem interpretação (assinatura, texto rotacionado, classificação ambígua).

### Fase 1: Inventário e Detecção de Modo

```python
from scripts.pipeline import fase_a_inventario
inv = fase_a_inventario("/caminho/pasta-cliente")
```

Lista todos os arquivos com extensão, tamanho, número de páginas e se tem text-layer. Decida o modo (Individual / Lote / Parcial).

### Fase 2: Identificação do KIT Assinado e Separação de Modelos

Aplique a regra de assinatura (física ou digital). Detalhes em `references/regras-validacao.md` (seção 2).

- Documentos sem assinatura → MOVER para `0. Kit/` (nunca excluir).
- Documentos Word `.doc/.docx` → quase sempre são modelos editáveis → vão para `0. Kit/`.
- KIT compactado em PDF assinado → fonte da Fase 5 (separação por documento).

**Distinção KIT em branco × Processo escaneado (v2.3, paradigma Guilherme 2026-05-14):**

Quando há 2+ PDFs candidatos a "kit do cliente" em `0. Kit/` (típico: `KIT <NOME>.pdf` gerado em Word para impressão E `Processo <NOME>.pdf` escaneado com tudo assinado), USE `scripts/pdf_utils.py:score_kit_assinado(path)` para decidir qual é a fonte autoritativa:

```python
from scripts.pdf_utils import score_kit_assinado, escolher_kit_assinado

# Cada candidato recebe score -100..+100
info = score_kit_assinado(path)
# info['classificacao']: 'ASSINADO' | 'MODELO' | 'AMBIGUO'

# Ou: passar lista de candidatos e receber o vencedor
resultado = escolher_kit_assinado([kit_em_branco_path, processo_path])
# resultado['escolhido'] = caminho do kit assinado
# resultado['descartados'] = outros (intactos, só não usados como fonte)
```

Sinais que indicam **kit ASSINADO**:
- `producer` em `{intsig.com pdf producer, Adobe Scan, CamScanner, ScannerPro, Office Lens}` (apps de scanner)
- Text-layer vazio ou < 100 chars (PDF imagem puro)
- ≥ 1 imagem raster na primeira página
- Tamanho > 3 MB
- Nome começa com "Processo"

Sinais que indicam **kit MODELO** (em branco para o cliente assinar):
- `producer` em `{Microsoft® Word, LibreOffice, OpenOffice, WPS Writer}`
- Text-layer abundante (> 500 chars) + zero imagens raster
- Tamanho < 1 MB
- Nome começa só com "KIT" sem "assinado"/"completo"

Em `pipeline.py:_sugerir_tipo_pdf`, qualquer PDF com "kit" ou "processo" no nome passa por essa heurística antes do match por keyword. Em `fase_b_classificar_pdfs`, quando há múltiplos `KIT_ASSINADO` na mesma pasta, o de menor score é REBAIXADO a `KIT_MODELO` (intacto fisicamente, apenas não é fonte de extração).

**Sub-documentos a extrair do Processo escaneado** (paradigma Guilherme):
- Procurações específicas por banco/contrato (uma por página)
- Declaração de hipossuficiência (uma única, replicada nas pastas-banco)
- Declaração LGPD / consentimento (única)
- RG/CPF do cliente, da rogada (se a rogo) e das testemunhas

NUNCA pegar essas peças do KIT em branco — sairão sem assinatura e atrapalham o protocolo.

Para verificar assinatura visual quando o score for ambíguo:
1. Renderize cada página em imagem (`scripts/pdf_utils.py:render_page`).
2. Use Read tool para análise visual procurando: traços manuscritos, rubricas, impressão digital, selos de certificado digital (ICP-Brasil, DocuSign, ClickSign, ZapSign, D4Sign, Adobe Sign).
3. Se não tiver nenhum tipo de assinatura → modelo → MOVER para `0. Kit/`.

### Fase 3: Identificação dos Tipos de Ação

A skill cobre múltiplos tipos:
- Empréstimo consignado não contratado
- RMC (Reserva de Margem Consignável)
- RCC (Reserva de Cartão Consignado)
- Refinanciamento
- Empréstimo consignado genérico
- Bradesco — Tarifas, Mora, Mora+Encargo, Aplic.Invest, PG ELETRON, Título de Capitalização

A classificação parte SEMPRE da procuração — o documento-mestre. Detalhes em `references/regras-validacao.md` (seções 7 e 8).

**Validação do número do contrato (v2.4, paradigma Guilherme 2026-05-14):**

O número que vai como contrato no JSON precisa ser EXTRAÍDO DA PROCURAÇÃO ASSINADA específica, NUNCA presumido pelo RG, CPF ou outros identificadores. O kit-juridico antigo às vezes confundia o RG do cliente com número de contrato (caso paradigma: Guilherme PAN RMC ficou como "1897431-7" no JSON, que era o RG do cliente — o número real era "0229014603105"). Antes de gravar `contratos[i].contrato` no JSON:

1. Conferir que o número aparece literalmente na procuração específica.
2. Validar cruzando com HISCON ou HISCRE quando aplicável (cartões RMC/RCC podem não aparecer no HISCON tradicional, mas a procuração é fonte autoritativa).
3. Em caso de ambiguidade, marcar `contratos_impugnar_origem = "sugestao_automatica"` para forçar revisão humana antes de gerar inicial.

Heurísticas que NÃO devem ser fonte primária do número de contrato:
- RG do cliente (formato XXXXXXX-X)
- CPF do cliente
- NB do benefício (formato XXX.XXX.XXX-X)
- Identificadores internos do banco que aparecem em telas/extratos sem o rótulo "Contrato"

### Fase 4: Processamento de Imagens

Para cada imagem (JPG, PNG, HEIC, etc.), aplique:
1. **Análise** — Identifique TODOS os documentos/elementos (uma imagem pode conter múltiplos: RG + senha; RG + CPF; etc.). Detalhes em `references/regras-imagens.md`.
2. **Recorte e centralização** — Use `scripts/process_images.py` para auto-detectar bordas via OpenCV. Ajuste manualmente quando o auto-detect falhar.
3. **Conversão para PDF** — Cada documento vira um PDF separado.
4. **Dados sensíveis** (senhas INSS, gov.br, banco) — separar e SALVAR em `0. Kit/`, nunca em pastas de ação.
5. **Fotos de cautela** (cliente assinando) — não recortar, mantém no `0. Kit/`.

```python
from scripts.process_images import crop_and_save_as_pdf, process_batch
process_batch("pasta_imagens", "pasta_pdfs_output")
```

### Fase 5: Separação do KIT (PDF compactado) em Documentos Individuais

Se houver KIT compactado assinado (PDF único com vários documentos):
1. Renderize cada página em imagem.
2. Identifique visualmente onde um documento termina e outro começa.
3. Use `scripts/pdf_utils.py:extract_pages` para fatiar.
4. Nomeie conforme `references/regras-nomenclatura.md`.

### Fase 5.5: Preparar leitura de manuscritos (se aplicável)

Antes de extrair banco/contrato de procurações manuscritas, **carregue o
módulo de aprendizado**:

1. Ler `aprendizado/_index.md` (entender a estrutura)
2. Ler `aprendizado/padroes-bancos.md` (formato esperado por banco)
3. **Identificar o captador** do kit (nome no PDF, contrato escritório, ou
   rótulo do usuário). Se houver ficha em `aprendizado/captadores/<slug>.md`,
   ler antes de extrair (descontar erros conhecidos da caligrafia daquele
   captador).
4. Aplicar `references/regras-manuscritos.md` para o workflow completo
   (1ª tentativa → cross-check HISCON → retry → solicitar usuário).

### Fase 6: Extrair Banco/Tipo/Contrato das Procurações

```python
from scripts.pipeline import fase_c_preparar_procuracoes
manifesto = fase_c_preparar_procuracoes(
    pdf_procuracoes="caminho/2- Procurações N22.pdf",
    pasta_trabalho="pasta-cliente"
)
# Gera crops_pag_NN.png em pasta-cliente/_proc_crops/
```

Para CADA crop, use Read tool para extrair:
- Banco (do parágrafo "PODERES ESPECIAIS: em face do BANCO X")
- Tipo (consignado vs RMC/RCC — verifique se há texto "em virtude do desconto de cartão de crédito RMC/RCC")
- Número do contrato

Em caso de dúvida em algum dígito, use:
```python
from scripts.pipeline import fase_c_revalidar_pagina
fase_c_revalidar_pagina(pdf_procuracoes, pag_num, pasta_trabalho)
# Gera linha_pag_NN.png com super-zoom só da linha do contrato
```

### Fase 7: Parser de Extratos HISCON

```python
from scripts.pipeline import fase_d_parsear_extratos
extratos = fase_d_parsear_extratos([
    "caminho/EXTRATO PENSAO.pdf",
    "caminho/EXTRATO APOSENTADORIA.pdf",
])
```

Cada extrato é parseado em `{beneficio: {...}, contratos: [...]}`. Se o extrato for sem text-layer (raro), o parser retorna `is_ocr_required=True` — você precisará rodar OCR (visual via Claude ou easyocr) antes.

### Fase 8: Detecção de Múltiplos Benefícios

Se há mais de um NB único nos extratos parseados, a estrutura final terá nível BENEFÍCIO. Detalhes em `references/regras-beneficios.md`.

### Fase 9: Cruzamento Procurações × Extratos

Use `fase_i_cruzar_procuracoes_hiscon` para classificar cada procuração:

```python
from scripts.pipeline import fase_i_cruzar_procuracoes_hiscon
resultado = fase_i_cruzar_procuracoes_hiscon(procuracoes, extratos)

# resultado["exatos"]:        match exato no HISCON → confiança 100%
# resultado["aproximados"]:   Lev ≤ 2 → SUGERIR e PEDIR confirmação ao usuário
# resultado["nao_localizados"]: pendência crítica (ver regras-manuscritos.md)
```

Para cada **aproximado**, mostrar ao usuário:
```
Procuração pag 4 diz "31203991.43" — não bate exato com nenhum HISCON.
Candidato mais próximo: 31103991143 (Lev=2, Bradesco, pensão).
Confirmar ou corrigir?
```

Para cada **não localizado**:
- Aplicar técnicas de retry (ver `references/regras-manuscritos.md` Fase 3)
- Se ainda não achar, marcar pendência crítica e pedir leitura ao usuário

Quando usuário corrigir, **registrar via**:

```python
from scripts.pipeline import fase_j_registrar_correcao
fase_j_registrar_correcao(
    cliente="ALICE DA CONCEIÇÃO DOS SANTOS",
    captador="Marcio Teixeira",
    pagina=4,
    banco="Bradesco",
    valor_lido="31203991.43",
    valor_correto="311039911-43",
    origem="usuario",
    observacao="O '0' depois do '31' parecia bola, era '1' fechado.",
)
```

Toda correção é registrada em `aprendizado/correcoes.md`. Se o padrão é
recorrente no captador (≥3 correções similares), atualizar
`aprendizado/captadores/<slug>.md` na seção "Padrões de erro".

### Fase 10: Detecção de Cadeias

```python
from scripts.pipeline import fase_e_detectar_cadeias
cadeias = fase_e_detectar_cadeias(extratos)
# Retorna {beneficio_pasta: [componentes_conectados]}
```

Cada componente pode ser:
- `ISOLADO` (1 contrato)
- `REFIN_DIRETO` (1→1)
- `CONSOLIDACAO` (N→1)
- `FRACIONAMENTO` (1→N)
- `PORTABILIDADE_INTER_BANCO` (atravessa bancos)
- `SUBSTITUICAO_BANCO` (caso especial RMC/RCC)
- `CADEIA_RECURSIVA` (refins sucessivos)

Detalhes em `references/regras-cadeias.md`.

### Fase 11: Montar Estrutura Final

```python
from scripts.pipeline import fase_f_montar_estrutura
relatorio = fase_f_montar_estrutura(
    pasta_cliente="pasta-cliente",
    pdf_procuracoes_origem="...pdf",
    procuracoes_extraidas=[...],   # da Fase 6
    extratos_parseados=extratos,    # da Fase 7
    cadeias_por_beneficio=cadeias,  # da Fase 10
    docs_comuns={
        "RG_CPF": "...pdf",
        "DECLARACAO_HIPOSSUFICIENCIA": "...pdf",
        "COMPROVANTE_RESIDENCIA": "...pdf",
        "HISCRE": "...pdf",          # ou HISCRE_PENSAO/HISCRE_APOSENTADORIA
    },
    cliente_nome="ANAIZA MARIA DA CONCEIÇÃO",
)
```

Esta fase:
1. Cria pastas BENEFÍCIO/BANCO/ ou BANCO/ (conforme houver multi-benefício)
2. Fatia cada procuração no PDF original e salva no formato canônico
3. Replica documentos comuns em cada pasta
4. Grifa o extrato relevante com cores por cadeia
5. Gera ESTUDO DE CADEIA - [Banco].docx em cada pasta

### Fase 11.5: Consolidar arquivos residuais no `0. Kit/`

Após criar todas as pastas de banco e replicar documentos, mova os
arquivos ORIGINAIS que sobraram na raiz (PDF compactado original,
extratos, vídeos, fotos, kit assinado etc.) para `0. Kit/`.

```python
from scripts.pipeline import fase_h_consolidar_kit
fase_h_consolidar_kit(
    pasta_cliente="...",
    arquivos_originais_para_mover=[
        "...PDF originais que estavam na raiz...",
    ],
    extras_para_mover=[
        "...vídeos .mp4...",
    ],
)
```

A função também:
- Renomeia `KIT/` → `0. Kit/` se existir o nome antigo (pra ficar no topo da listagem)
- Mescla conteúdo se ambos existirem
- Não sobrescreve arquivos que já estão no `0. Kit/`

**Regra geral**: nada se perde. Tudo que não foi distribuído pra pastas
de banco vai pro `0. Kit/`. Originais que foram REPLICADOS nas pastas de
banco também vão pro `0. Kit/` (a cópia está nas pastas; o original fica
preservado no kit).

### Fase 12: Validação e Pendências

Execute todas as verificações de `references/regras-validacao.md`:
- Identidade documental (nome / CPF / endereço)
- Assinatura presente onde exigido
- Comprovante de residência autêntico e dentro do prazo
- Declaração de residência de terceiro completa
- Documentos obrigatórios presentes
- Integridade (1 documento por arquivo)
- Cruzamento procuração × histórico (já feito na Fase 9)
- Classificação correta da ação

Acumule pendências em uma lista de dicts. Gere XLSX **apenas se houver
alertas** (a função retorna None se a lista estiver vazia, sem criar o
arquivo):

```python
from scripts.pipeline import fase_g_gerar_pendencias
fase_g_gerar_pendencias(pasta_cliente, alertas)  # só cria se alertas != []
```

### Fase 12.5: Salvar dossiê do cliente (`_estado_cliente.json`)

Ao final do pipeline, salve o **dossiê único do cliente** que vai
servir de insumo para as próximas skills do escritório (notificação
extrajudicial, petição inicial). Veja schema completo em
`references/regras-estado-cliente.md`.

```python
from scripts.pipeline import fase_k_salvar_estado_cliente
fase_k_salvar_estado_cliente(
    pasta_cliente=PASTA,
    cliente_nome="ANAIZA MARIA DA CONCEIÇÃO",
    extratos_parseados=extratos,
    procuracoes_extraidas=procuracoes,
    cadeias_por_beneficio=cadeias,
    relatorio_montagem=relatorio,
    captador={"nome": "Marcio Teixeira", "slug": "marcio-teixeira",
              "estado_origem_cliente": "BA"},
    advogado={"nome": "...", "oab": "...", "uf_atuacao": "...", ...},
    alertas=alertas,
)
```

A skill PRESERVA campos de outras skills (`notificacoes_extrajudiciais`,
`iniciais`, `anotacoes_livres`) — só atualiza o que ela mesma produz.
A skill `notificacao-extrajudicial` lerá esse JSON e gravará suas próprias
entradas; a `inicial-nao-contratado`/`inicial-bradesco` o mesmo.

## Modo Lote

Para cada subpasta de cliente, execute as Fases 1–12 individualmente. Após processar todos:

```python
from scripts.gerar_relatorio_lote import gerar_relatorio_consolidado
gerar_relatorio_consolidado(pasta_mae, dados_de_cada_cliente)
```

## Validação Final (checklist)

Antes de finalizar, confirme:
- [ ] Nenhum documento misturado com outro
- [ ] RG + CPF unidos em PDF único (quando aplicável)
- [ ] Documentos de pessoas diferentes em arquivos separados (rogado, testemunhas)
- [ ] Procurações como PDFs separados na pasta da ação correta
- [ ] Estrutura BENEFÍCIO/BANCO/ correta (ou BANCO/ se 1 só benefício)
- [ ] Procurações contêm APENAS procuração
- [ ] Declaração de hipossuficiência contém APENAS a declaração
- [ ] Documentos organizados foram MOVIDOS (não excluídos) do material bruto
- [ ] Pendências.xlsx gerado
- [ ] Pasta `0. Kit/` contém os residuais (modelos, mídia, senhas, contrato escritório, LGPD)
- [ ] NENHUM arquivo foi excluído da pasta de trabalho
- [ ] Processamento ocorreu APENAS dentro da pasta selecionada
- [ ] Cadeias detectadas estão grifadas no extrato com cores diferentes
- [ ] ESTUDO.docx gerado em cada pasta de banco
- [ ] Procurações com contrato não localizado têm pendência registrada

## Dicas para o Claude (LLM)

1. **OCR/Vision para procurações rotacionadas**: o `proc_extractor.py` aplica `prerotate(270)` automaticamente. Se a leitura visual ainda mostrar texto rotacionado, peça pra rodar com `rotation=90` ou `rotation=180`.
2. **Números de contrato com 1 dígito errado**: matching aproximado contra extrato. Se a procuração diz `15007985` e o extrato tem `15007989`, é provavelmente OCR — revalide com `fase_c_revalidar_pagina`.
3. **HISCON com layout incomum**: o parser regex pode falhar parcialmente em alguns formatos novos. Se um contrato esperado não aparece no resultado, abra o PDF, verifique manualmente, e adicione regra no `hiscon_parser.py`.
4. **Substituição imediata RMC/RCC**: padrão suspeito mas não é "refin oficial". O detector marca como `SUBSTITUICAO_BANCO` e o ESTUDO inclui observação narrativa.
5. **Lote grande (50+ clientes)**: processe um por um, registre erros por cliente sem interromper o lote, e produza relatório consolidado no fim.
