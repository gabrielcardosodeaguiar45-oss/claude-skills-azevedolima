---
name: inicial-nao-contratado
description: Gera petição inicial em ações declaratórias de inexistência de relação jurídica c/c repetição do indébito em dobro e danos morais por EMPRÉSTIMO CONSIGNADO NÃO CONTRATADO. Cobre BA Federal (JEF Salvador/Gabriel), AM Estadual (TJAM/Patrick), AL Federal (JEF Tiago), AL Estadual (TJAL Tiago) e MG Estadual (TJMG/Alexandre) com 10 templates parametrizados no vault. Use quando o usuário pedir para gerar inicial de empréstimo não contratado, processar pasta de cliente APP-NÃO-CONTRATADO, fazer petição inicial contra banco (e INSS no caso Federal) por descontos não autorizados em benefício previdenciário, ou mencionar HISCON com contratos fraudulentos. Sistema de perfis permite adicionar PE/SE/ES novas em ~30 minutos seguindo GUIA_NOVA_UF.md.
---

# Skill: inicial-nao-contratado

Geração automatizada de **petições iniciais** em ações declaratórias de inexistência de relação jurídica c/c repetição do indébito em dobro e danos morais, por **empréstimo consignado não contratado** (descontos no benefício previdenciário sem autorização do segurado). Escritório De Azevedo Lima & Rebonatto.

## INSTRUÇÕES OPERACIONAIS (uso da skill)

Quando o usuário invocar `/inicial-nao-contratado` ou pedir para gerar uma inicial:

**1. Identificar o perfil de jurisdição** (UF + foro):

| O que o usuário diz | Perfil a usar |
|---|---|
| BA / Salvador / JEF Federal Bahia | `BA_FEDERAL` |
| AM / Manaus / Maués / Boa Vista do Ramos / TJAM | `AM_ESTADUAL` |
| AL / Arapiraca / Maceió / JEF AL (≤ 60 SM = R$ 91.080) | `AL_FEDERAL` |
| AL Estadual / TJAL (> 60 SM ou sorteio) | `AL_ESTADUAL` |
| MG / Ipatinga / Uberlândia / Belo Horizonte / TJMG | `MG_ESTADUAL` |

**2. Localizar a pasta do cliente** (em `C:\Users\gabri\OneDrive\Área de Trabalho\APP - NÃO CONTRATADO\<cliente>` ou subpasta de banco)

**3. Ler procuração via OCR** (texto-camada → easyocr → multimodal Read se PDF escaneado) para extrair número(s) de contrato. **REGRA CRÍTICA §9-quater**: nunca pegar todos os contratos do banco; se OCR falhar, pedir números explícitos ao usuário.

**4. Ler RG + comprovante** via OCR multimodal — extrair CPF, RG, data nascimento (≥60 = idoso → prioridade), endereço, estado civil. Se RG ilegível, anotar como pendente; **nunca** escrever `[A CONFIRMAR]` sem antes tentar OCR.

**5. Invocar pipeline genérico:**

```python
from _pipeline_generico import gerar_inicial_padrao

res = gerar_inicial_padrao(
    perfil_chave='AL_FEDERAL',  # ou BA_FEDERAL / AM_ESTADUAL / AL_ESTADUAL
    pasta_cliente=r'...',
    autora={'nome': ..., 'cpf': ..., 'data_nascimento': datetime(...), ...},
    comarca='Arapiraca',
    numeros_contrato_explicitos=['xxxxxxxxxx'],
    output_path=r'.../INICIAL_<cliente>.docx',
)
```

A skill aplica AUTOMATICAMENTE:
- Procuração-fonte-única (`ProcuracaoSemFiltroError` se sem filtro)
- Fontes Segoe UI Bold no autor/banco/INSS via rStyle 2TtuloChar
- Cabeçalho em Segoe UI Bold inline (sem caps)
- Conjugação f/m automática (nacionalidade → inscrita/inscrito + domiciliada/domiciliado)
- Omissão limpa de RG inválido / igual ao CPF / vazio / `[A CONFIRMAR]`
- **Endereço composto** matriz Joaçaba/SC + unidade de apoio na UF do cliente (`montar_endereco_escritorio_completo` + `inserir_unidade_apoio_se_faltando`)
- Bloco fático sem mencionar depósito (default conservador AL)
- Intro fática com **BANCO + CONTRATO Nº em Cambria Bold CAPS** (não Segoe UI)
- Pedido declaratório com escolha empréstimo vs refinanciamento
- **Prioridade idoso** só se autor ≥ 60 anos:
  - cabeçalho em Cambria 11pt + alinhamento direita + recuo 4cm
  - pedido como item I da lista numerada em Cambria Bold
- Grifo amarelo em todas as alterações
- Validação template (`validar_template.py`) se template novo

**6. Reportar para o usuário:**
- Caminho do DOCX gerado
- N de contratos detectados
- Banco-réu identificado
- Modificações + residuais
- Alertas (pendências de leitura ocular, divergências doc vs HISCRE, etc.)

## Estrutura de arquivos da skill

```
~/.claude/skills/inicial-nao-contratado/
├── SKILL.md                            ← este arquivo
├── GUIA_NOVA_UF.md                     ← passo a passo para adicionar PE/MG/SE/ES
└── references/
    ├── _pipeline_generico.py           ← wrapper de alto nível (use este)
    ├── perfis_juridicos.py             ← PERFIS = {'BA_FEDERAL', 'AM_ESTADUAL', 'AL_FEDERAL', 'AL_ESTADUAL', 'MG_ESTADUAL'}
    ├── helpers_redacao.py              ← regras de fonte/redação canônica (compartilhado) — inclui montar_endereco_escritorio_completo, inserir_unidade_apoio_se_faltando, inserir_prioridade_idoso_se_faltando, inserir_pedido_prioridade_idoso_se_faltando
    ├── extrator_procuracao.py          ← OCR de procurações (text-layer + easyocr)
    ├── extrator_hiscon.py              ← parser HISCON com FIM DE DESCONTO + fuzzy + auditoria
    ├── extrator_hiscre.py              ← parser HISCRE
    ├── extrator_calculo.py             ← parser cálculo jurídico
    ├── escritorios.py                  ← procuradores + OABs + endereços + decidir_foro_al
    ├── bancos_canonicos.py             ← CNPJs/endereços de bancos
    ├── helpers_docx.py                 ← run-aware substituição com grifo amarelo
    ├── adaptador_am.py                 ← convenção placeholders AM + classificar_menor
    ├── auditor_dano_moral.py           ← regra dano moral (1 contrato = 15k; 2+ = 5k×N)
    ├── verificador_dados_pessoais.py   ← doc físico vs HISCRE
    ├── seletor_template.py             ← decide entre base/multiplos/refin (BA)
    ├── validar_template.py             ← checklist automático para template novo
    ├── _run_caso_padrao.py             ← TEMPLATE de runner (copiar pra cada cliente)
    ├── _run_demos_ficticias.py         ← gera 9 demos para teste
    ├── _pipeline_caso.py               ← BA Federal (chamado pelo genérico)
    ├── _pipeline_caso_am.py            ← AM Estadual
    └── _pipeline_caso_al.py            ← AL Federal/Estadual
```

Templates `.docx` ficam em
`~/OneDrive/Documentos/Obsidian Vault/Modelos/IniciaisNaoContratado/_templates/`
(10 templates ativos: BA × 3, AM × 2, AL × 4, MG × 1).

## TODOs conhecidos (pendentes de validação prática)

1. **BA sem PDF de cálculo** cai com `R$ 0,00` no valor da causa. Aplicar
   fallback "soma_dobros + dano_moral" (igual ao AL faz).

2. **AM com 2+ contratos do MESMO banco**: o pipeline AM ainda não duplica
   bloco fático. Replicar lógica do AL (`_preencher_bloco_fatico` caminho B
   1banco×N contratos) quando aparecer caso real.

## Regras críticas (não esquecer)

### 1. Polo passivo VARIA conforme jurisdição

| Jurisdição | Polo passivo | Procurador | OAB |
|---|---|---|---|
| **BA — JEF (Federal)** | Banco + **INSS** (TNU TEMA 183 II) | Dr. Gabriel Cardoso de Aguiar | OAB/BA 88973 |
| **AM — TJAM Estadual rito comum** | **Apenas o banco** (sem INSS) | Dr. Patrick Willian da Silva (sempre) | OAB/AM A2638 |
| **AL — JEF (Federal, ≤60 SM)** | Banco + INSS | Dr. Tiago de Azevedo Lima (transição → Alexandre) | OAB/AL 20906A |
| **AL — TJAL Estadual (>60 SM ou sorteio)** | Apenas o banco | Dr. Tiago de Azevedo Lima (transição → Alexandre) | OAB/AL 20906A |
| **MG — TJMG Estadual rito comum** | Apenas o banco | Dr. Alexandre Raizel de Meira | OAB/MG 230436 |

> **REGRA OPERACIONAL AM:** mesmo quando a notificação extrajudicial é assinada por outro procurador do escritório (Eduardo, Gabriel ou Tiago — que constam na procuração), a **inicial AM é sempre protocolada pelo Patrick** porque o sistema PJe/Projudi do TJAM é acessado por ele localmente. Os demais procuradores ficam apenas no instrumento de procuração anexo.

> **Atenção:** quando a jurisdição é Estadual (AM), **NÃO incluir o INSS no polo passivo** nem invocar a fundamentação federal (TNU TEMA 183, legitimidade do INSS, Justiça Federal competente, etc.). Isso já está pré-removido do template `inicial-jeam-*.docx` — não precisa mexer.

**Como decidir a jurisdição:** depende do domicílio do autor + decisão estratégica do escritório. Se o autor reside em comarca AM (Manaus, Maués, Boa Vista do Ramos, Caapiranga, etc.), o template `jeam` é o padrão. Se BA (Salvador, Camaçari, Mata de São João, etc.), `jfba`.

### 2. Renda da parte autora — do extrato INSS ou da base de cálculo do HISCON

`{{valor_renda_liquida}}` é o valor LÍQUIDO do benefício. Fontes possíveis:
- Extrato INSS (preferencial, se anexado pelo cliente)
- HISCON p.2 — campo `BASE DE CÁLCULO` (atenção: é a renda BRUTA — usar se não tiver extrato)
- KIT — declaração de hipossuficiência ou autodeclaração de renda

Se NÃO houver fonte identificável: **NÃO inventar valor padrão**: alertar no relatório paralelo "RENDA NÃO IDENTIFICADA — preencher manualmente" e deixar `[A CONFIRMAR]` no DOCX.

### 3. Cálculo do dano moral — regra fixa do escritório

| Cenário | Valor pleiteado |
|---|---|
| 1 contrato isolado | **R$ 15.000,00** |
| 2+ contratos do mesmo banco | **R$ 5.000,00 × N contratos** |
| Refinanciamento ATIVO | **R$ 15.000,00 + R$ 5.000,00 (dano temporal adicional)** |

### 4. Auditoria do dano moral vs PDF de cálculo

A skill SEMPRE compara o valor calculado pela regra acima com o valor "DANOS MORAIS" extraído do PDF de cálculo:
- BATER: usa o valor calculado, sem alerta.
- DIVERGIR: usa o valor da regra, mas alerta no relatório paralelo:
  > ⚠ Cálculo PDF traz R$ {valor_pdf}; regra do escritório para {N} contratos seria R$ {valor_regra}. CONFERIR antes do protocolo.

### 5. Valor da causa = "Total Geral" do PDF de cálculo

NÃO recalcular. O PDF de cálculo já vem PRONTO do escritório (formato Cálculo Jurídico). Extrair o "Total Geral" da p.2 e usar como `{{valor_causa}}`.

Se o cálculo NÃO bater com a regra do dano moral (ver § 4), alertar mas usar o valor do PDF mesmo (porque é o valor que vai instruir o pedido).

### 6. Bancos canônicos — fonte única de CNPJ + endereço

Toda referência a banco-réu vem do `bancos_canonicos.py` (espelho do `Modelos/IniciaisNaoContratado/bancos-canonicos.md`). 70+ bancos catalogados em 4 jurisdições (Matriz / AL / AM / BA).

Regra de seleção do endereço:
- DEFAULT = matriz (qualquer estado)
- EXCEÇÃO = se opta pelo foro do domicílio do réu (ex.: Maceió/AL), usar a filial do estado correspondente

### 7. Documentos do cliente — estrutura padrão

```
APP - NÃO CONTRATADO/
└── <CLIENTE> - <Procurador>/
    ├── 1. KIT/                                ← KIT COMPLETO (escaneado, OCR easyocr)
    │   ├── KIT COMPLETO.pdf                   ← contém RG/CPF/comp.residência/etc.
    │   ├── AUTODECLARAÇÃO DE RESIDÊNCIA.pdf
    │   ├── TERMO DE CONSENTIMENTO.pdf
    │   └── CONTRATO DE PRESTAÇÃO DE SERVIÇOS.pdf
    └── BANCO XXX/<sub-tese>/                  ← UMA pasta por BANCO
        ├── 2 - PROCURAÇÃO XXX <Nº CONTRATO>.pdf  ← N procurações = N contratos
        ├── 3 - RG.pdf
        ├── 4 - DECLARAÇÃO DE HIPOSSUFICIÊNCIA.pdf
        ├── 5 - DECLARAÇÃO DE BENS MÓVEIS E IMÓVEIS.pdf
        ├── 6 - DECLARAÇÃO DE ISENÇÃO DO IMPOSTO DE RENDA.pdf
        ├── 7 - COMPROVANTE DE RESIDÊNCIA.pdf
        ├── 8 - HISTÓRICO DE EMPRÉSTIMO.pdf    ← HISCON (mesmo de todos os bancos)
        ├── 9 - HISTÓRICO DE CRÉDITO.pdf       ← HISCRE
        └── 10 - CÁLCULO.pdf (ou 9- CÁLCULO)   ← cálculo PRONTO, específico por banco
```

**Sub-tese** = `1 AVERBAÇÃO NOVA INATIVO`, `1 REFINANCIAMENTO INATIVO`, `2 AVERBAÇÃO NOVA INATIVO`, etc. Combinação de:
- Numeração da procuração (1, 2, 3...)
- Origem da operação (`AVERBAÇÃO NOVA` / `REFINANCIAMENTO` / `PORTABILIDADE`)
- Status (`INATIVO` = excluído/encerrado / `ATIVO` = em curso)

### 8. Pasta KIT — usar APENAS para qualificação do autor

A pasta `1. KIT/` (ou variantes) tem documentos pessoais (RG, comp. residência, autodeclaração). É a **fonte primária da qualificação**. Os documentos da pasta de cada banco são repetições/versões + procurações específicas + HISCON + cálculo.

### 9. Auditoria automática pós-geração

Após gerar o DOCX, rodar `auditor.auditar_inicial_gerada()` que detecta:
- Placeholders residuais `{{...}}` não preenchidos
- Valores R$ XXX,XX que parecem caso-específico (verificar contra HISCON+cálculo)
- CNPJs/CPFs/contas/CEPs fora da lista esperada
- Datas fora de jurisprudência

### 9-bis. **OBRIGATÓRIO: hierarquia de fontes para dados pessoais + verificação cruzada**

Para os campos **CPF, RG, nome, data de nascimento, nome da mãe, NB**:

**Hierarquia de fontes (em ordem de prioridade):**

1. **PRIMÁRIA: documento pessoal físico** — RG, CPF, CNH escaneado no KIT do cliente (pasta `1. KIT/` ou `KIT/`). Esta é a fonte que o procurador apresentaria em juízo.
2. **SUBSIDIÁRIA: HISCRE (Histórico de Créditos do INSS)** — usado quando o documento físico não está legível ou faltou. Por ser oficial do INSS, é confiável mas não substitui o documento.
3. **VERIFICAÇÃO CRUZADA OBRIGATÓRIA: comparar SEMPRE entre as fontes** — para detectar:
   - Documento pessoal de OUTRA PESSOA na pasta (ex.: cônjuge, dependente, terceiro)
   - OCR mal-feito do KIT (manuscrito difícil)
   - Divergência entre nome no doc e no HISCRE (caso de homônimo, mudança de nome por casamento, etc.)

**Implementação técnica:**

```python
def verificar_dados_pessoais(autora_do_doc, hiscre):
    """Compara dados extraídos do documento físico (autora_do_doc) com o HISCRE.
    Retorna lista de divergências."""
    divergencias = []
    for campo in ['cpf', 'nome', 'data_nascimento', 'nome_mae']:
        v_doc = autora_do_doc.get(campo)
        v_hiscre = hiscre.get(campo)
        if v_doc and v_hiscre and v_doc != v_hiscre:
            divergencias.append({
                'campo': campo,
                'doc': v_doc,
                'hiscre': v_hiscre,
                'severidade': 'CRÍTICA' if campo in ['cpf', 'nome'] else 'ATENÇÃO',
            })
    return divergencias
```

**No relatório paralelo:** se houver QUALQUER divergência, gerar seção destacada "🚨 DIVERGÊNCIAS DOC vs HISCRE":
- Listar campo, valor do doc, valor do HISCRE
- CRÍTICA → "REVISAR ANTES DE PROTOCOLAR — pode ser documento de outra pessoa"
- ATENÇÃO → "CONFERIR — pode ser homônimo, mudança de nome ou OCR errado"

**Regra de qual valor usar:**
- Se AUTORA preenchida (lida do doc) → usar AUTORA (mesmo se divergir)
- Se AUTORA vazia → usar HISCRE com alerta "Dado extraído do HISCRE (subsidiário). Verifique RG físico do cliente."
- Se ambos vazios → erro fatal: "REVISAR — KIT/HISCRE não fornecem CPF/RG/nome"

### 9-ter. **OBRIGATÓRIO: cruzar procurações com HISCON e usar coluna LITERAL FIM DE DESCONTO**

Dois bugs históricos que NÃO PODEM se repetir (caso paradigma: GEORGE/FACTA, 07/05/2026):

**(a) Filtro de contratos por procuração — fuzzy match e auditoria cruzada**

O filtro do pipeline BA pega o número de contrato a partir do **nome do arquivo** das procurações (`2 - PROCURAÇÃO FACTA 0047032901.pdf` → `0047032901`). Esse nome pode ter typo. No caso GEORGE/FACTA, a procuração `2 - PROCURAÇÃO FACTA 0047633052.pdf` deveria ser `0047033052` (1 dígito errado: `63` vs `03`) — e o pipeline silenciosamente perdia o terceiro contrato.

Defesas obrigatórias (já implementadas em `extrator_hiscon.py`):

1. `filtrar_contratos_por_numero(..., fuzzy_dist=1)` — admite até **1 dígito** de diferença para casar com contrato do mesmo tamanho. Match fuzzy é flagado com `_match_fuzzy` no dict de saída.
2. `auditar_procuracoes_vs_hiscon(contratos_hiscon, numeros_procuracao, banco_codigo)` — cruza:
   - números casados EXATOS;
   - números casados FUZZY (gera alerta);
   - números no HISCON do banco que NÃO foram referidos por nenhuma procuração, classificados em **suspeitos** (data de inclusão a ≤31 dias dos casados ou prefixo idêntico — alta probabilidade de ser irmão esquecido) vs **informativos** (outros contratos do banco em outros períodos);
   - números nas procurações que NÃO estão no HISCON do banco (alerta crítico).

**REGRA OPERACIONAL DE TOLERÂNCIA (Gabriel, 07/05/2026):**

| Procurações com fuzzy match na pasta | Comportamento da skill |
|---|---|
| 0 | Segue silencioso |
| **1** | **Segue + alerta ⚠ ATENÇÃO** (1 typo de 1 dígito é tolerável; provavelmente o procurador renomeou errado) |
| **2 ou mais** | **Segue + alerta 🚨 CRÍTICO**: pode indicar erro sistemático (lote inteiro com typo, mistura com outro cliente, OCR ruim na geração das procurações). NÃO PROTOCOLAR sem revisar TODAS as procurações |

A skill **NUNCA pula contratos silenciosamente** — sempre que há divergência entre nome do arquivo e HISCON, gera alerta visível no relatório paralelo + console. Os alertas vão **na seção de pendências**, em ordem de criticidade. O procurador SEMPRE confere.

**(b) Competência FIM DE DESCONTO — usar a coluna literal do HISCON, não calcular**

O HISCON traz duas colunas que o parser do `analise-cadeias-hiscon` antigamente PULAVA: COMPETÊNCIA INÍCIO DE DESCONTO (col 5, ex.: `06/2021`) e COMPETÊNCIA FIM DE DESCONTO (col 6, ex.: `02/2024`). Antes, a skill estimava a competência fim como `data_exclusao − 1 mês`, o que dava resultado errado quando a exclusão acontecia no MESMO mês do último desconto (resultava em mês a menos).

Solução obrigatória: `analise-cadeias-hiscon/scripts/analisador.py` agora extrai `competencia_inicio_desconto` e `competencia_fim_desconto` direto da tabela. `extrator_hiscon.formatar_contrato_para_template` PRIORIZA esses campos; só cai para o cálculo via `data_exclusao − 1 mês` se a coluna vier vazia (HISCON antigo, antes da mudança da Dataprev).

| Fonte | Prioridade | Observação |
|---|---|---|
| `competencia_fim_desconto` (col 6 do HISCON) | **1ª — autoritativa** | string `'mm/yyyy'` |
| `data_exclusao − 1 mês` | 2ª (fallback) | quando a coluna 6 está vazia |
| `comp_inicio + qtd_parcelas − 1` | 3ª (contrato ATIVO sem exclusão) | só para Ativos |

### 9-quater. **OBRIGATÓRIO: a PROCURAÇÃO é a única fonte autoritativa dos contratos a impugnar**

Caso paradigma: EDMUNDA LIMA DOS SANTOS (07/05/2026). Pasta tinha:
- `2 - Procuração — N°1.pdf` (1 procuração, sem número no nome)
- HISCON com 2 contratos do BANCO BRADESCO

A skill pegou silenciosamente os 2 contratos do banco. Mas a procuração outorgava poderes apenas sobre **1 contrato** (`0123527065102`) — o segundo contrato do HISCON não estava autorizado. Isso resultou em uma inicial fora do escopo do mandato.

**Regra fundamental gravada (não pode ser violada):**

> A procuração é a **ÚNICA fonte autoritativa** do que o cliente nos autorizou a impugnar. NUNCA assumir contratos sem confirmação na procuração. NUNCA pegar "todos os contratos do banco" como fallback silencioso.

**Hierarquia obrigatória de extração** (em ordem de tentativa):

1. **Número no nome do arquivo da procuração** — ex.: `2 - PROCURAÇÃO FACTA 0047032901.pdf`. Pipeline lê via regex.
2. **Número no CONTEÚDO da procuração** (text-layer do PDF) — ex.: "ajuizar ação referente ao Contrato n° 0123527065102". Pipeline tenta `pymupdf.get_text()`.
3. **OCR via EasyOCR no PDF escaneado** — para procurações que vêm em scan sem text-layer. Roda em pt-BR com resolução até 2400px.
4. **`numeros_contrato_explicitos=[...]`** — parâmetro do chamador. Use quando o procurador leu manualmente e quer passar diretamente.

**Comportamento se TODAS as 4 fontes falharem:**

```python
raise ProcuracaoSemFiltroError(
    "🚨 IMPOSSÍVEL extrair números de contrato. AÇÃO: abrir o PDF "
    "manualmente e passar via numeros_contrato_explicitos=[...]. "
    "NUNCA pegamos 'todos os contratos do banco' como fallback."
)
```

A skill **PARA o pipeline** e o procurador precisa intervir. Isso evita gerar inicial com contratos não outorgados.

**Implementado nos 3 pipelines (atualizado 07/05/2026):**
- `extrator_procuracao.py` — extrator OCR (text-layer + EasyOCR fallback)
- `_pipeline_caso.py` (BA) — `ProcuracaoSemFiltroError`
- `_pipeline_caso_al.py` (AL) — `ProcuracaoSemFiltroError`
- `_pipeline_caso_am.py` (AM) — `ProcuracaoSemFiltroError` (caso paradigma adicional: FABIO/C6)

### 9-quinquies. **REDAÇÃO CANÔNICA: helpers_redacao.py compartilhado pelos 3 pipelines**

Para garantir que as MESMAS regras de formatação valem em BA/AM/AL, todos os pipelines importam de `helpers_redacao.py`:

| Função | O que faz |
|---|---|
| `make_run` | cria `<w:r>` com fonte/bold/grifo controlados; aceita `usar_rstyle_titulo` (apenas para nomes em destaque, NÃO usar em cabeçalho — gera caps automático) e `tamanho_pt` (sz em meio-pontos) |
| `substituir_qualificacao_autor` | reescreve qualificação com NOME (Segoe UI Bold via rStyle 2TtuloChar) + resto Cambria; conjugação f/m automática; omite estado_civil/RG vazios; recebe `end_escritorio` da `montar_endereco_escritorio_completo(uf)` |
| `substituir_polo_passivo` | reescreve polo passivo com NOMES (banco + INSS) em Segoe UI Bold + resto Cambria |
| `substituir_intro_contratos` | reescreve "tomou conhecimento dos descontos referentes a empréstimo(s)..." com BANCO e CONTRATO Nº em **Cambria Bold + CAPS** (regra fixa 07/05/2026 — substituiu Segoe UI Bold via rStyle); aplica `<w:highlight>` amarelo |
| `modalidade_extenso` | mapeia `tipo_origem` → 'empréstimo' / 'refinanciamento' / 'empréstimo (portabilidade)' |
| `preencher_pedidos_declaratorios` | reescreve "Declarar a inexistência do empréstimo/refinanciamento..." com escolha automática + dados reais; **duplica o parágrafo para N contratos** (1 pedido por contrato); detecta layout MG (sub-itens) vs BA/AM/AL e despacha para `_preencher_pedidos_formato_mg` quando necessário |
| `preencher_bloco_fatico_formato_mg` | preenche o bloco "Do contrato nº A:" do template MG com sub-itens por contrato |
| `remover_prioridade_pedidos` | remove o pedido de prioridade idoso quando autor não é idoso |
| `inserir_unidade_apoio_se_faltando` | padroniza endereço hardcoded dos templates BA/AM substituindo run-aware por `montar_endereco_escritorio_completo(uf)` (matriz Joaçaba/SC + unidade de apoio na UF do cliente). Idempotente: se o parágrafo já tem o endereço composto correto, não duplica |
| `inserir_prioridade_idoso_se_faltando` | quando autor é idoso, INSERE no cabeçalho o parágrafo "Prioridade de tramitação: art. 1.048 do Código de Processo Civil (Idoso)" em **Cambria 11pt + alinhamento à direita + recuo esquerdo de 4cm (ind=2268 twips)** + grifo amarelo |
| `inserir_pedido_prioridade_idoso_se_faltando` | quando autor é idoso, INSERE como item I da lista numerada de pedidos o pleito "A prioridade na tramitação..." em **Cambria Bold + grifo amarelo**, herdando o `pPr` (pStyle=5Listaalfabtica) do primeiro item da lista para entrar na renumeração automática |

**Regra de fontes — NUNCA violar:**

| Tipo de conteúdo | Fonte/estilo |
|---|---|
| Cabeçalho/endereçamento ('Ao Juízo...') | **Segoe UI Bold INLINE** (NÃO usar rStyle 2TtuloChar — tem caps automático) |
| Nome do AUTOR (qualificação) | **Segoe UI Bold via rStyle 2TtuloChar** (caps + bold do estilo do template) |
| Nome do BANCO no POLO PASSIVO | **Segoe UI Bold via rStyle 2TtuloChar** |
| Nome do INSS (Federal) no polo passivo | **Segoe UI Bold via rStyle 2TtuloChar** |
| BANCO + CONTRATO Nº na INTRO FÁTICA ("tomou conhecimento dos descontos…") | **Cambria Bold + CAPS** (regra fixa 07/05/2026 — substituiu Segoe UI rStyle) |
| Cabeçalho "Prioridade de tramitação: art. 1.048…" (idoso) | **Cambria 11pt + alinh. direita + recuo esquerdo 4cm (ind=2268 twips)** + grifo amarelo |
| Pedido "A prioridade na tramitação…" (idoso) | **Cambria Bold + pStyle 5Listaalfabtica** (entra na numeração romana I) + grifo amarelo |
| Resto da qualificação/polo passivo/intro | **Cambria** |
| Toda alteração da skill | **highlight amarelo** |

### 9-sexies. **REGRAS CANÔNICAS DE ENDEREÇO E PRIORIDADE IDOSO (gravadas 07/05/2026)**

Quatro regras fixas do escritório, propagadas por TODOS os pipelines (BA + AM + AL + MG) via `helpers_redacao.py`. Aplicadas automaticamente — não requerem configuração por caso.

**(1) Endereço do escritório — matriz Joaçaba/SC SEMPRE primeiro + unidade de apoio na UF do cliente**

Toda inicial deve trazer no parágrafo de qualificação do autor:

> "…com escritório profissional em **Rua Frei Rogério, 541, Centro, Joaçaba/SC, CEP 89600-000, e unidade de apoio em [endereço completo da filial da UF do cliente]**, local onde recebem avisos e intimações, vem…"

A função `escritorios.montar_endereco_escritorio_completo(uf)` retorna a string composta correta. Mapa de filiais por UF (`FILIAL_APOIO_POR_UF` em `escritorios.py`):

| UF do cliente | Filial de apoio | Endereço |
|---|---|---|
| BA / ES | Salvador/BA | Rua Portugal, 5, Ed. Status, Comércio, CEP 40015-903 |
| AM | Maués/AM | Travessa Michiles, S/N, Centro, CEP 69190-000 |
| AL / SE | Arapiraca/AL | Rua Nossa Senhora da Salete, 597, Sala 04, Itapuã, CEP 57314-175 |
| MG | Uberlândia/MG | Av. Floriano Peixoto, 615, Ed. Floriano Center, Loja 07, Térreo, Centro, CEP 38400-102 |
| SC | (nenhuma — é a matriz) | só matriz |

**Implementação:**
- Pipeline AL (e MG via `uf_override='MG'`): chama `montar_endereco_escritorio_completo(uf)` direto em `_substituir_qualificacao` antes de `substituir_qualificacao_autor`.
- Pipelines BA + AM: chamam `inserir_unidade_apoio_se_faltando(doc, uf)` ao final do `gerar_inicial`. O helper detecta o trecho hardcoded do template (3 padrões cobertos) e substitui run-aware preservando os placeholders restantes do parágrafo.
- Caso especial AM com REPRESENTANTE LEGAL: o pipeline já constrói o parágrafo de qualificação do zero usando `montar_endereco_escritorio_completo('AM')`.

**(2) Cabeçalho de prioridade — Cambria 11pt + alinhamento à direita + recuo esquerdo de 4cm**

Quando o autor é idoso (`eh_idoso=True`), inserir LOGO ABAIXO do cabeçalho "Ao Juízo…" o parágrafo:

> "Prioridade de tramitação: art. 1.048 do Código de Processo Civil (Idoso)."

**Formatação OOXML obrigatória** (não negociável):

```xml
<w:p>
  <w:pPr>
    <w:ind w:left="2268"/>          <!-- 4cm = 2268 twips -->
    <w:jc w:val="right"/>           <!-- alinhamento DIREITA -->
  </w:pPr>
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Cambria" w:hAnsi="Cambria"/>
      <w:sz w:val="22"/>            <!-- sz em meio-pontos: 22 = 11pt -->
      <w:szCs w:val="22"/>
      <w:highlight w:val="yellow"/>
    </w:rPr>
    <w:t xml:space="preserve">Prioridade de tramitação: art. 1.048 do Código de Processo Civil (Idoso).</w:t>
  </w:r>
</w:p>
```

Implementado em `inserir_prioridade_idoso_se_faltando(doc, eh_idoso, grifo)`. Idempotente — se o parágrafo já existe, não duplica.

**(3) BANCO + CONTRATO Nº na intro fática — Cambria Bold + CAPS (NÃO mais Segoe UI)**

A intro do bloco fático ("Nessa oportunidade, após informações, tomou conhecimento dos descontos referentes a empréstimo que não contratou junto ao **BANCO X**, **CONTRATO Nº 1234567**:") deve sair em:

- `<w:rFonts w:ascii="Cambria"/>` (não Segoe UI)
- `<w:b/><w:bCs/>` (BOLD)
- Texto em CAIXA ALTA (chamada `.upper()` no helper)
- `<w:highlight w:val="yellow"/>`
- **NÃO** usar `<w:rStyle w:val="2TtuloChar"/>` (que é Segoe UI Bold com caps automático do estilo)

Helper: `substituir_intro_contratos(p_elem, nome_banco, numeros, grifo)`. Funciona idêntico para 1, 2 ou N contratos (ajusta singular/plural e usa "e" para o último item).

**(4) Pedido de prioridade — em BOLD, herdando pStyle do primeiro item da lista numerada**

Quando o autor é idoso, INSERIR como item I da lista numerada de pedidos:

> "**A prioridade na tramitação, tendo em vista que a parte autora é pessoa idosa, nos termos do art. 1.048, inciso I, do Código de Processo Civil;**"

**Estratégia técnica:**
1. Localizar o primeiro parágrafo da lista após "DOS PEDIDOS" cujo `pStyle` contenha "Lista" (pStyle padrão: `5Listaalfabtica`).
2. `deepcopy` desse `pPr` (preserva numeração romana automática I, II, III).
3. Inserir o novo parágrafo ANTES dele (vira o novo item I; Word renumera automaticamente).
4. Texto em **`<w:b/><w:bCs/>` Cambria + grifo amarelo**.

Implementado em `inserir_pedido_prioridade_idoso_se_faltando(doc, eh_idoso, grifo)`. Idempotente.

**Casos paradigma das 4 regras:** JOSE DELI JORGE PEREIRA (3 bancos MG: DAYCOVAL, PARANÁ, SENFA), JOÃO PEDRO DA SILVA (PARANÁ MG), JOSÉ JESUS DA COSTA (PAN MG × 2 processos) — todos validados em 07/05/2026 com 4/4 ajustes presentes.

### 10. **OBRIGATÓRIO: grifar (highlight amarelo) TODAS as alterações da skill**

Toda substituição de placeholder e todo conteúdo INJETADO pela skill no DOCX gerado **DEVE** receber `<w:highlight w:val="yellow"/>`. Isso permite ao procurador a revisão visual rápida das alterações.

Áreas grifadas:
- Substituição de placeholders comuns (qualificação autor, banco-réu, benefício, valores, datas)
- Conteúdo gerado para blocos repetíveis (síntese fática por contrato + DECLARAR por contrato)
- Listas montadas pela skill (`{{contratos_lista_breve}}`)
- Resultado da remoção do marcador `{{SE_IDOSO}}` (quando autor é idoso, o texto restante fica grifado)

NÃO grifar:
- Texto fixo do template (toda a fundamentação jurídica, preliminares, jurisprudência)
- Nome/OAB do procurador (fixo)

**SEMPRE grifar (mesmo que pareça "fixo"):**
- Endereço do escritório (matriz + unidade de apoio): a skill **substitui** o trecho hardcoded do template via `inserir_unidade_apoio_se_faltando(doc, uf)` para deixar dinâmico por UF do cliente; como é alteração da skill, recebe grifo amarelo.
- Cabeçalho de prioridade idoso: inserido pela skill quando `eh_idoso=True`.
- Pedido de prioridade idoso: idem.

Implementação técnica: o helper `substituir_in_run(p, mapa, grifo=True)` aplica o highlight automaticamente nos caracteres SUBSTITUÍDOS (não nos preexistentes). Para runs criados manualmente (ex.: polo passivo com 5 runs separados, blocos repetíveis duplicados), aplicar `<w:highlight w:val="yellow"/>` no rPr antes de inserir no XML.

### 9-terdecies. **PLANILHA DE CÁLCULO DE INDÉBITO em EXCEL (gravado 13/05/2026)**

Junto com cada inicial AL/MG/AM/BA (consignado, RMC, RCC), a skill agora gera automaticamente uma **planilha Excel `CALCULO_<nome>.xlsx`** na mesma pasta do DOCX, com cálculo detalhado mensal dos descontos atualizados.

**Regime fixo** (conforme pedido nas iniciais do escritório):
* **Correção monetária:** INPC (responsabilidade civil — STJ Tema 905)
* **Juros de mora:** 1% a.m. simples (juros legais — art. 406 CC c/c CTN)
* **Dobro:** art. 42, p. único, CDC
* **Dano moral:** R\$ 15.000 (1 contrato) ou R\$ 5.000 × N contratos (2+)

**Estrutura da planilha:**

* **Aba `RESUMO`** — uma linha por contrato com totais (descontado, corrigido+juros, em dobro), linha SUBTOTAL com soma, linha DANO MORAL e linha **TOTAL GERAL DA AÇÃO** (subtotal em dobro + dano moral).
* **Aba por contrato** — tabela mensal de cada parcela descontada com: competência, valor original, fator INPC, valor corrigido, meses para juros, juros 1% a.m., total simples e total em dobro.

**Arquivos da implementação:**

| Arquivo | Conteúdo |
|---|---|
| `skills/_common/dados/inpc_bcb_serie188.json` | Tabela INPC mensal oficial BCB (jan/2017 em diante). Atualizar periodicamente via API BCB. |
| `skills/_common/indices_oficiais.py` | `inpc_acumulado_entre()`, `corrigir_inpc()`, `juros_simples_mes()` |
| `skills/_common/calculadora_indebito.py` | `calcular_contrato()`, `calcular_dano_moral()`, `gerar_excel_indebito()` |
| `_pipeline_caso_al.py` linha 1149 | Hook após `doc.save()` que chama `gerar_excel_indebito()` |

**Não se aplica a:** skill `inicial-bradesco` (Patrick AM — Bradesco encargos/tarifas/capitalização/PE tem regime próprio, cálculo é feito por outra rota).

**Atualização periódica do INPC:**

```bash
curl -sL "https://api.bcb.gov.br/dados/serie/bcdata.sgs.188/dados?formato=json&dataInicial=01/01/2017&dataFinal=31/12/2026" \\
     -o skills/_common/dados/inpc_bcb_serie188.json
```

### 9-undecies. **REGRA DE CIDADE FIXA AL → SEMPRE JEF FEDERAL (gravado 13/05/2026)**

Decisão operacional do escritório: clientes residentes em **Viçosa/AL**, **São Sebastião/AL** ou **Traipu/AL** **sempre ajuízam no JEF Federal**, independente do valor da causa. Quando o valor excede 60 SM (R\$ 91.080), inclui-se pedido expresso de **renúncia ao excedente** (Art. 17, § 4º, Lei 10.259/01).

**Implementação:** `escritorios.cidade_forca_foro_federal(cidade)` retorna True para essas 3 cidades (com normalização Unicode tolerante a acento/maiúsculas). A função `decidir_foro_al(valor, forcar, cidade_autor)` aplica a hierarquia:

1. `forcar` (override manual via `perfil_chave='AL_FEDERAL'` ou `'AL_ESTADUAL'`) — sempre vence
2. `cidade_autor` em `CIDADES_AL_SEMPRE_FEDERAL` — JEF Federal com renúncia se > 60 SM
3. Valor da causa ≤ 60 SM → Federal; > 60 SM → Estadual

Quando a regra de cidade impõe Federal mas o valor excede 60 SM, retorna `renuncia_ao_excedente=True` e o pipeline acrescenta alerta na inicial: *"INICIAL DEVE CONTER PEDIDO EXPRESSO DE RENÚNCIA AO EXCEDENTE (Art. 17, § 4º, Lei 10.259/01)"*.

**Para usuário:** ao gerar inicial, passar `perfil_chave='AL_FEDERAL'` para clientes dessas 3 cidades — independente do valor. Se passar `AL_ESTADUAL`, o `forcar` vence (você se responsabiliza pela decisão).

### 9-duodecies. **BLOCO FÁTICO MÚLTIPLOS CONTRATOS: cabeçalho numerado + sub-itens (gravado 13/05/2026, ajuste fino noite 13/05/2026)**

Caso paradigma: ANAIZA PENSAO ITAU (10 contratos a–j).

Mudança no layout do bloco fático quando há ≥2 contratos do mesmo banco:

**Antes (até 12/05/2026):**
```
a) No que diz respeito ao referido empréstimo, cumpre informar que a primeira
   parcela descontada... contrato n° 622902175, cuja operação foi realizada...
b) No que diz respeito ao referido empréstimo, cumpre informar que a primeira
   parcela descontada... contrato n° 626302197, cuja operação foi realizada...
```

Repetição do "No que diz respeito ao referido empréstimo, cumpre informar que" em CADA bloco gerava texto pesado e redundante.

**Agora (13/05/2026):**
```
4. No que diz respeito ao referido empréstimo, cumpre informar:           ← NUMERADO (4.)
   a) o contrato de nº 622902175: a primeira parcela descontada...        ← BOLD em "a) o contrato de nº 622902175:"
   b) o contrato de nº 626302197: a primeira parcela descontada...        ← BOLD em "b) o contrato de nº 626302197:"
   ...
```

Estrutura:
- **Cabeçalho NUMERADO** ("4. No que diz respeito ao referido empréstimo, cumpre informar:") — mantém o `numPr` original do parágrafo template, continuando a numeração da lista da inicial (1./2./3./4.).
- **N sub-itens SEM numeração** mas com `[letra]) o contrato de nº NNN:` em **NEGRITO** — destaca visualmente cada contrato.

**Implementação em `_pipeline_caso_al.py:_preencher_bloco_fatico` (caminho B):**

1. **Cabeçalho criado ANTES do loop de remoção de `numPr`** (senão herda elementos sem numPr):
   - `deepcopy(elem_template)` preservando `pPr` completo (com `numPr` → ganha "4." automático)
   - Limpa só os `<w:r>` (runs) do deepcopy
   - Adiciona novo run com texto fixo "No que diz respeito ao referido empréstimo, cumpre informar:"
   - Insere ANTES de `elem_template`

2. **Loop de remoção de `numPr`/`pStyle` de lista APENAS nos sub-itens** (elementos = cópias). O cabeçalho criado acima fica fora do loop e preserva sua numeração.

3. **Cada sub-item:**
   - Substitui "No que diz respeito ao referido empréstimo, cumpre informar que a primeira parcela" → "[letra]) o contrato de nº [NUM]: a primeira parcela"
   - Remove "contrato n° xxxxxxx, " do meio (número já apareceu no início, evita duplicidade)
   - Após todas as substituições, chama `_aplicar_bold_inicio(elem, "[letra]) o contrato de nº [NUM]:")` — função interna que quebra o primeiro `<w:r>` em 2: um run BOLD (prefixo) + um run normal (resto), preservando fonte/grifo.

Para N=1 (1 só contrato) NÃO se aplica — o parágrafo singular fica como está.

### 9-septies. **TEMPLATES AL/MG: literais piloto + xxxxx no bloco fático (gravado 12/05/2026)**

Caso paradigma: ANAIZA / ANTONIO / CICERO (AL_FEDERAL e AL_ESTADUAL, 12/05/2026).

Dois bugs simultâneos que rebentam iniciais AL/MG silenciosamente — gravados aqui para nunca mais voltar:

**(1) Templates AL (`inicial-jfal-1banco`, `inicial-jfal-2bancos`, `inicial-jeal-1banco`, `inicial-jeal-2bancos`) e MG (`inicial-jemg-1banco`) NÃO podem ter placeholders `{{nome_autor}}`/`{{banco_reu_nome}}`/etc.**

O pipeline `_pipeline_caso_al.py` faz substituições **TARGETED no DOCX usando string matching dos textos literais do caso piloto** (FULANO DE TAL, BANCO BRADESCO, NB 149.139.433-9, etc.). Templates parametrizados com `{{...}}` quebram o pipeline porque os padrões regex/contains não encontram o que esperam.

Se você (ou alguém) parametrizar um template AL/MG no vault, o pipeline gera DOCX com placeholders intactos e qualificação/polo passivo/intro vazios. **Sempre manter os templates AL/MG na versão LITERAL do caso piloto** — o pipeline reescreve em cima dos literais.

**Onde estão os backups da versão literal correta:**

```
C:\Users\gabri\OneDrive\Documentos\Obsidian Vault\Modelos\IniciaisNaoContratado\_templates\
├── inicial-jfal-1banco.docx                          ← USAR
├── inicial-jfal-1banco.docx.bak_pre_parametrizacao   ← backup literal seguro
├── inicial-jfal-1banco.docx.bak_pre_pente_fino       ← versão {{}} ruim (não usar)
├── inicial-jfal-1banco.docx.parametrizado_<DATA>     ← snapshot quando deu errado
```

Se aparecer `{{placeholders}}` em DOCX gerado, restaurar template do `.bak_pre_parametrizacao` e regerar.

**(2) Bloco fático "No que diz respeito ao referido empréstimo..." deve estar em formato xxxxxxxx (todos os templates AL/MG, NÃO LITERAL do piloto).**

Caso paradigma do bug: `inicial-jeal-1banco.docx` saiu com dados literais do piloto BANCO PAN/contrato 3880089838/competência 01/06/2024/parcela R\$ 49,00 no bloco fático em vez de `xxxxxxxx, xx parcelas, R$ xxx,xx`. Resultado: pipeline não substitui (não acha xxxxx pra trocar) e o DOCX fica com dados de OUTRO caso. O `_patch_templates_estadual.py` corrige.

O parágrafo correto é:

> "No que diz respeito ao referido empréstimo, cumpre informar que a primeira parcela descontada do benefício da parte autora foi na competência **xxxxxxxx**, de um total de **xx parcelas**, no valor de **R\$ xxx,xx** (valor por extenso), relativas a um empréstimo consignado no valor de **R\$ xxx,xx** (valor por extenso), contrato n° **xxxxxxx**, cuja operação foi realizada pelo **banco xxxxx**, ora requerido."

### 9-octies. **DUPLICAÇÃO AUTOMÁTICA DO BLOCO FÁTICO PARA 1banco × N contratos (gravado 12/05/2026)**

Caso paradigma: ANAIZA APOSENTADORIA ITAU (6 contratos), ANAIZA PENSAO ITAU (10 contratos), ANTONIO BRADESCO (4 contratos).

Template `inicial-jfal-1banco.docx` / `inicial-jeal-1banco.docx` / `inicial-jemg-1banco.docx` traz **um único bloco fático genérico**. Quando há ≥2 contratos do MESMO banco (caso comum: refin/refin/refin no Itaú; cobranças Bradesco) o pipeline `_pipeline_caso_al.py:_preencher_bloco_fatico` agora **duplica o parágrafo singular N vezes** automaticamente:

1. Localiza o parágrafo "No que diz respeito ao referido empréstimo..." (ou plural)
2. Faz `deepcopy` do `<w:p>` N-1 vezes, inserindo logo após o original
3. Remove `numPr` (lista numerada do pPr) das cópias — senão sai "5. a) ... 6. b) ..."
4. Remove `pStyle` de lista (que faz indentação automática)
5. Prefixa cada parágrafo com "a) ", "b) ", "c) "... até "z)" (fallback "aa)" para >26)
6. Para cada cópia, substitui xxxxx pelos dados do contrato correspondente

Resultado:

> a) No que diz respeito ao referido empréstimo... contrato n° 626102379...
> b) No que diz respeito ao referido empréstimo... contrato n° 628458426...
> c) No que diz respeito ao referido empréstimo... contrato n° 631048329...

Esse mecanismo é o "Caminho B" no `_preencher_bloco_fatico`. O "Caminho A" (sub-blocos "Do contrato sob n° xxxxxxxx") fica para templates `2bancos` que tenham essa estrutura.

### 9-nonies. **INTRO FÁTICA MULTI-BANCO + BLOCO FÁTICO POR BANCO: helpers em `helpers_redacao` (gravado 12/05/2026)**

Caso paradigma: CICERO/Bradesco+Mercantil (3 contratos em 2 bancos).

Quando há **litisconsórcio passivo** (2+ bancos diferentes em uma só inicial — ex.: cadeia de portabilidade Bradesco↔Mercantil), a intro fática agrupa contratos por banco:

> "Nessa oportunidade, após informações, tomou conhecimento dos descontos referentes a empréstimos que não contratou junto ao **BANCO BRADESCO S.A., CONTRATOS Nº 0123471622742 E 0123471622766**, e ao **BANCO MERCANTIL DO BRASIL S.A., CONTRATO Nº 016178952**:"

E cada bloco fático a)/b)/c) menciona o banco real do contrato em "cuja operação foi realizada pelo BANCO X, ora requerido" — não o banco principal.

**Helper compartilhado:** `aplicar_intro_fatica(p_elem, contratos_fmt, fallback_banco_nome, grifo=True)` em `helpers_redacao.py`. Decide automaticamente:
- 1 banco → chama `substituir_intro_contratos` clássico
- 2+ bancos → chama `substituir_intro_contratos_multi_banco` (lista de grupos)

Usado pelos **3 pipelines (BA + AM + AL/MG)** — chamadas únicas refatoradas em 12/05/2026.

**Cuidado com formatar_contrato_para_template:** após formatação, o nome do banco vem no campo `'banco'`, não `'banco_nome'`. Os helpers tratam ambos (fallback `c.get('banco_nome') or c.get('banco') or fallback_banco_nome`).

**Formato MG / AL-2bancos com sub-itens "Do contrato nº..."**: a função `preencher_bloco_fatico_formato_mg` também detecta multi-banco e, para cada sub-item, identifica o banco real do contrato. Quando todos os contratos são do mesmo banco, mantém o `nome_banco` único passado de fora (compatibilidade com o piloto MG original).

### 9-decies-bis. **BANCOS_CANONICOS: tolerância a espaços inseridos pelo parser HISCON (gravado 13/05/2026)**

Caso paradigma: MARCIA AGIBANK ("AGIBAN K FINANC EIRA S A"), GEDALVA PENSAO SANTANDER ("SANTA NDER"), JOSEFA APOSENTADORIA INTER ("BANCO INTER SA"), JOSEFA PENSAO BRADESCO ("BANCO BRADE SCO SA") — 13/05/2026.

O parser HISCON da `kit-juridico` insere espaços ALEATÓRIOS no meio de palavras quando há pequenos gaps no PDF entre letras. Resulta em nomes de banco como:

- `SANTA NDER` (deveria ser SANTANDER)
- `BANCO BRADE SCO SA` (BRADESCO)
- `BANCO BRADE SCO FINANC IAMENT OS SA` (BRADESCO FINANCIAMENTOS)
- `AGIBAN K FINANC EIRA S A` (AGIBANK FINANCEIRA)
- `BANCO MERCA NTIL DO BRASIL SA` (MERCANTIL DO BRASIL)
- `QI SOCIED ADE DE CREDIT O DIRETO` (QI SOCIEDADE DE CREDITO DIRETO)

**Solução aplicada em `bancos_canonicos.py:resolver_banco`** (13/05/2026):
1. **Tentativa 2a:** substring match com nome original (já existia)
2. **Tentativa 2b (NOVA):** substring match comparando **AMBOS sem espaços** (`re.sub(r'\s+', '', ...)`). Resolve todos os casos acima sem precisar cadastrar dezenas de variantes.

Antes de assumir que falta cadastro de banco, conferir se é só o problema do parser HISCON — o resolver agora tolera isso automaticamente.

**Aliases adicionados em 13/05/2026:**
- `BANCO SANTANDER`, `BANCO SANTANDER (BRASIL)`, `SANTANDER`, `SANTANDER FINANCIAMENTOS`, `SANTANDER FINANCIAMENTO`, `BANCO SANTANDER FINANCIAMENTO` → `santander`
- `BANCO INTER`, `BANCO INTER S A`, `BANCO INTER SA`, `INTER` → `inter`
- `BANCO INBURSA`, `INBURSA` → `inbursa`

### 9-decies. **ROTEAMENTO FEDERAL/ESTADUAL POR VALOR DA CAUSA — AL (gravado 12/05/2026)**

Caso paradigma: ANAIZA PENSAO ITAU (R\$ 189.154,40), ANTONIO BRADESCO (R\$ 136.336,64).

Em AL, o foro NÃO é decidido pelo procurador — é decidido pelo **valor da causa**:

| Valor da causa | Foro | Perfil | Polo passivo |
|---:|---|---|---|
| ≤ R\$ 91.080,00 (60 SM × R\$ 1.518) | JEF Federal | `AL_FEDERAL` | Banco + INSS |
| > R\$ 91.080,00 | TJAL Estadual | `AL_ESTADUAL` | Apenas banco (SEM INSS) |

**Antes de gerar a inicial AL**, calcule o valor da causa estimado e escolha o perfil:

- Pelo PDF de Cálculo: pega o "Total Geral" da p.2
- Sem PDF: estimativa = soma dos dobros + dano moral. Dobros = soma de `valor_parcela × qtd_parcelas × 2` para cada contrato. Dano moral = R\$ 15k (1 contrato) ou R\$ 5k × N (2+) ou R\$ 20k (refin ativo).

A função `decidir_foro_al(valor_causa)` em `escritorios.py` automatiza, mas você precisa passar `perfil_chave='AL_FEDERAL'` ou `'AL_ESTADUAL'` ao chamar `gerar_inicial_padrao`. Se passar errado, o pipeline aplica o template errado (sem ajustar polo passivo nem cabeçalho).

**Recomendação operacional:** ao gerar iniciais em lote, fazer DUAS passadas — primeira em `AL_FEDERAL` para ver os valores; segunda re-gera as que estouraram o teto em `AL_ESTADUAL`.

## Catálogo de cenários × templates

### BA — Federal (JEF Salvador) — procurador Gabriel

| Cenário | Template | Caso paradigma |
|---|---|---|
| 1 contrato + Averbação Nova + Inativo | `inicial-jfba-base.docx` | Roque Custódio × Daycoval (1 contrato encerrado em 02/2023) |
| N contratos do MESMO banco + Averbação Nova + Inativo | `inicial-jfba-multiplos-avn-inativo.docx` | George Souza × Itaú/Facta (vários contratos) |
| 1 ou N contratos + Refinanciamento + Ativo | `inicial-jfba-refin-ativo.docx` | (modelo do escritório) |

### AM — Estadual (JE Manaus / Maués / Boa Vista do Ramos / etc.) — procurador Patrick

| Cenário | Template | Caso paradigma |
|---|---|---|
| 1 contrato (AVN ou inativo) — sem INSS | `inicial-jeam-base.docx` | (sem caso ainda; modelo de Patrick) |
| Refinanciamento (com bloco "troco") — sem INSS | `inicial-jeam-refin.docx` | (sem caso ainda; modelo de Patrick) |
| N contratos do mesmo banco (AVN) | (criar `inicial-jeam-multiplos-avn-inativo.docx` quando aparecer) | — |

### MG — Estadual (TJMG, comarca do domicílio do autor) — procurador Alexandre

| Cenário | Template | Caso paradigma |
|---|---|---|
| 1 banco, 1+ contratos (sem INSS) | `inicial-jemg-1banco.docx` | JOSE DELI / DAYCOVAL, JOÃO PEDRO / PARANÁ, JOSÉ JESUS / PAN |
| 2+ bancos | (criar `inicial-jemg-2bancos.docx` quando aparecer) | — |

### Particularidades dos templates MG

- **Sem INSS** no polo passivo (rito comum estadual)
- **Cabeçalho:** "AO JUÍZO DE DIREITO DA __ª VARA CÍVEL DA COMARCA DE {{cidade_subsecao}}/MG" (regex `/[A-Z]{2}` aceita qualquer UF para o pipeline AL re-uso com `uf_override='MG'`)
- **Bloco fático com sub-itens "Do contrato nº A:":** preenchimento via `preencher_bloco_fatico_formato_mg(doc, contratos, banco, grifo)` quando o template traz placeholder `Do contrato nº A:`/`Do contrato nº B:`/etc.
- **Pedidos com sub-itens por contrato:** `_preencher_pedidos_formato_mg` lida com lista a)/b)/c) por contrato (ao invés de N pedidos consecutivos)
- **Pipeline reaproveitado:** o perfil `MG_ESTADUAL` despacha para `_pipeline_caso_al.py` passando `uf_override='MG'`. Decisões automatizadas: subseção, OABs, polo passivo (sem INSS), endereço composto matriz SC + apoio Uberlândia/MG.

### Particularidades dos templates AM

- **Sem INSS** no polo passivo (todo o bloco "INSTITUTO NACIONAL DO SEGURO SOCIAL — INSS" + "TNU TEMA 183" + "Legitimidade passiva do INSS" foi REMOVIDO)
- **Foro estadual:** "Ao Juízo da ___ Vara Cível da Comarca de {{competencia}}/AM"
- **Pedido de honorários cumulação STJ REsp 2.168.312/PR (Info 875)** — pleito de 20% sobre soma de capítulos autônomos (declaração + restituição + dano moral)
- **Naming convention diferente:** `{{nome_completo}}` no lugar de `{{nome_autor}}`, `{{quali_banco}}` consolida toda a qualificação do banco em 1 placeholder
- **`{{quali_banco}}` é UM único placeholder** que recebe a string completa montada pela skill: `"BANCO X, descrição PJ, inscrito no CNPJ sob o nº..., com endereço..."`
- **Pós-processamento de runs:** o nome do banco em `{{quali_banco}}` sai em **Segoe UI Bold** (separador `¤¤¤` quebra o run em 2). O `{{nome_completo}}` do autor mantém o `rStyle=2TtuloChar` do template (Segoe UI Bold).

### Autor MENOR de idade — REPRESENTAÇÃO vs ASSISTÊNCIA (CC arts. 3º, 4º, 1.690)

Regra do Código Civil aplicada automaticamente pelo `adaptador_am.classificar_menor`:

| Idade | Classe | Tratamento processual |
|---|---|---|
| < 16 anos | menor **impúbere** | **REPRESENTADA/O** pelo genitor |
| 16 a < 18 anos | menor **púbere** | **ASSISTIDA/O** pelo genitor |
| ≥ 18 anos | maior | qualificação normal sem representante |

Quando o caso tem `representante_legal != None`, o pipeline AM **REESCREVE** o parágrafo de qualificação inteiro (substituindo todos os placeholders desse parágrafo) com a estrutura:

```
NOME AUTORA (Segoe UI Bold + amarelo), brasileira, menor impúbere/púbere, beneficiária,
inscrita no CPF sob o nº XXX.XXX.XXX-XX, neste ato representada/assistida por sua
genitora NOME MÃE (Segoe UI Bold + amarelo), brasileira, solteira, beneficiária do INSS,
inscrita no CPF sob o nº YYY.YYY.YYY-YY, Cédula de Identidade nº Z.ZZZ.ZZZ-Z, órgão
expedidor SSP/AM, residente e domiciliada na [endereço da menor]...
```

Nota: o RG da MENOR não aparece nessa qualificação (criança pode não ter RG); aparece apenas o RG da MÃE/PAI representante. Se a menor já tem RG e você quer incluí-lo, ajustar `montar_qualificacao_menor` em `adaptador_am.py`.

Caso paradigma testado: PAOLA MAITÊ RODRIGUES DE CASTRO (5 anos, impúbere, REPRESENTADA pela mãe NAYEZA BRAGA RODRIGUES) — caso `PAOLA_C6` em `_run_am_clientes.py`.

## Pipeline completo

```
ENTRADA: caminho da pasta de UM banco (ex.: "GEORGE/BANCO ITAÚ/2 AVERBAÇÃO NOVA INATIVO/")
   │
[1] Identificar banco a partir do nome da pasta-mãe (ex.: "BANCO ITAÚ" → ITAÚ CONSIGNADO)
[2] Listar procurações 2-PROCURAÇÃO XXX → extrair números de contrato (do nome do arquivo)
[3] Ler HISCON (p.1 = autor+benefício; p.3+ = contratos)
[4] Filtrar contratos do HISCON pelos números nas procurações
[5] Determinar cenário:
        N == 1 + AVN + INATIVO → template `base`
        N >= 2 + AVN + INATIVO → template `multiplos`
        REFINANCIAMENTO + ATIVO → template `refin-ativo`
[6] Ler PDF de Cálculo → extrair "Total Geral" = VC + "DANOS MORAIS" pleiteado
[7] Ler KIT (OCR easyocr) → extrair CPF/RG/endereço/estado civil/profissão/idade
[8] Decidir prioridade idoso (data nasc. no Cálculo) e dano moral (regra § 3)
[9] Auditar dano moral pleiteado no PDF vs regra (§ 4)
[10] Aplicar template:
        - Substituir placeholders comuns (autor, banco-réu, benefício, etc.)
        - Para template `multiplos`: DUPLICAR bloco repetível p18 (síntese fática) e p231 (DECLARAR) N vezes
        - Substituir placeholders por contrato em cada cópia
[11] Pós-fix XML para placeholders com encoding (remuneração, etc.)
[12] Auditar DOCX gerado (placeholders residuais, valores fora do esperado)
[13] Gerar relatório paralelo .docx com pendências
[14] Retornar caminhos dos 2 arquivos gerados
```

## Regra de seleção do template

```python
def selecionar_template(contratos_questionados):
    """contratos_questionados: lista de dicts do HISCON
    Cada dict tem: numero, banco, origem, status, ...
    """
    n = len(contratos_questionados)
    
    # REFINANCIAMENTO ATIVO tem prioridade sobre o critério N×AVN
    tem_refin_ativo = any(
        ('Refinanciamento' in c['origem'] or 'Refinan' in c['origem'])
        and c['status'] == 'Ativo'
        for c in contratos_questionados
    )
    if tem_refin_ativo:
        return 'inicial-jfba-refin-ativo.docx'
    
    if n == 1:
        return 'inicial-jfba-base.docx'
    return 'inicial-jfba-multiplos-avn-inativo.docx'
```

## Cálculo do dano moral

```python
def calcular_dano_moral(contratos, eh_refin_ativo=False):
    n = len(contratos)
    if eh_refin_ativo:
        return {'moral': 15000.00, 'temporal': 5000.00, 'total': 20000.00}
    if n == 1:
        return {'moral': 15000.00, 'temporal': 0, 'total': 15000.00}
    return {'moral': 5000.00 * n, 'temporal': 0, 'total': 5000.00 * n}
```

## Hierarquia de fontes

| Campo | Fonte 1 | Fonte 2 | Fonte 3 |
|---|---|---|---|
| `nome_autor` | KIT (OCR) | HISCON p.1 | manual |
| `cpf_autor` | KIT (OCR) | manual | — |
| `rg_autor` + `orgao_expedidor_autor` | KIT (OCR) | manual | — |
| `nacionalidade` | KIT (OCR) | default "brasileiro/a" | — |
| `estado_civil` | KIT (OCR) | manual | — |
| `profissao` | KIT (OCR) | inferido do tipo de benefício | manual |
| `logradouro_autor`/`numero_autor`/`bairro_autor`/`cidade_autor`/`uf_autor`/`cep_autor` | KIT (autodeclaração de residência) | KIT (comp. residência) | manual |
| `tipo_beneficio`, `nb_beneficio` | HISCON p.1 | — | — |
| `banco_pagador`, `agencia_pagador`, `conta_pagador` | HISCON p.1 | — | — |
| `valor_renda_liquida` | extrato INSS | HISCON p.2 (BASE DE CÁLCULO) | KIT (autodeclaração de renda) |
| `contratos[*]` (numero, banco, valor_emprestado, qtd_parcelas, valor_parcela, data_inclusao, competencia_inicio, competencia_fim) | HISCON p.3+ tabela | — | — |
| `valor_causa` | PDF Cálculo p.2 ("Total Geral") | — | — |
| `dano_moral_pleiteado_pdf` (auditoria) | PDF Cálculo p.3+ | — | — |
| `idade` (idoso?) | data nascimento no PDF Cálculo p.1 | KIT RG (OCR) | manual |
| `banco_reu_*` (CNPJ, endereço) | `bancos_canonicos.py` | manual | — |
| `cidade_subsecao`, `uf_subsecao` | regra (subseção do domicílio do autor) | manual | — |

## Pendências conhecidas

- **Tesseract OCR pt-BR** ainda não está instalado nesta máquina; usar **easyocr** como padrão (igual no `inicial-bradesco`)
- **Template `inicial-jemg-2bancos.docx`** ainda não existe — quando aparecer caso MG com 2+ bancos, criar (modelo: copiar `inicial-jeal-2bancos.docx` adaptando cabeçalho/foro)
- **Cadeia multi-banco** (ex.: contrato Itaú→Pan→Agibank) não tem template ainda — para começar, gerar 1 inicial por banco mesmo dentro de cadeia (decisão futura)
- **Dicionário de tipos de benefício** (`{{tipo_beneficio}}` por extenso): aposentadoria por invalidez previdenciária / idade / tempo de contribuição / pensão por morte / etc. Construir incrementalmente conforme aparecem casos
- **AL 2bancos** (`inicial-jfal-2bancos.docx`, `inicial-jeal-2bancos.docx`): bloco fático ainda tem `xxxxxxxx`/`xxx,xx` — precisa simplificar igual ao 1banco (TODO § 1 lá em cima)
- **BA sem PDF de cálculo** cai com `R$ 0,00` no valor da causa — aplicar fallback "soma_dobros + dano_moral" (TODO § 2 lá em cima)

## Casos paradigma

| Cliente | UF / Comarca | Banco(s) × Contrato(s) | Template | Status |
|---|---|---|---|---|
| GEORGE DA SILVA SOUZA | BA / Salvador | ITAÚ × 4, FACTA × 3, AGIBANK × 2 (REFIN), PAN × 2 | multiplos (3) + refin-ativo (1) | em desenvolvimento |
| ROQUE CUSTODIO DA SILVA | BA / Salvador | DAYCOVAL × 1 | base | template-base já existe |
| FABIO MARINHO DE OLIVEIRA | AM / Maués | C6 × 1 (após filtro) | jeam-base | OK — caso paradigma `ProcuracaoSemFiltroError` (skill detectou que sem filtro pegaria 7 contratos errados) |
| EDMUNDA LIMA DOS SANTOS | AL / Arapiraca | BRADESCO × 1 (autorizado) | jfal-1banco | OK — caso paradigma da regra "procuração é única fonte autoritativa" |
| **JOSE DELI JORGE PEREIRA** | **MG / Janaúba** | **DAYCOVAL × 1, PARANÁ × 1, SENFA × 1 (3 ações separadas)** | **jemg-1banco × 3** | **OK 07/05/2026 — validou 4 ajustes canônicos (endereço composto + prioridade idoso)** |
| **JOÃO PEDRO DA SILVA** | **MG / Ipatinga** | **PARANÁ × 1 (39008309792-000)** | **jemg-1banco** | **OK 07/05/2026 — validou fuzzy de procuração truncada (ZapSign cortou número de 11 para 6 dígitos)** |
| **JOSÉ JESUS DA COSTA** | **MG / Uberlândia** | **PAN × 2 (319748353-4 + 344008857-7, 2 ações separadas)** | **jemg-1banco × 2** | **OK 07/05/2026 — validou auditoria cruzada (cada inicial alerta sobre o contrato do "outro processo")** |
| **ANAIZA MARIA DA CONCEIÇÃO** | **AL / Arapiraca** | **2 benefícios × 7 bancos × 30 contratos (5 ações CONSIGNADO)** | **jfal-1banco + jeal-1banco** | **OK 12/05/2026 — validou duplicação automática do bloco fático com prefixos a)/b)/c).../j) para até 10 contratos do mesmo banco; roteamento Federal→Estadual quando valor > 60 SM (R$ 91.080)** |
| **ANTONIO JOSÉ BARBOSA** | **AL / Arapiraca** | **BRADESCO × 4 + ITAU × 1** | **jeal-1banco + jfal-1banco** | **OK 12/05/2026 — caso de portabilidade Bradesco↔Digio com contratos repetidos no HISCON** |
| **CICERO DOMINGOS DA SILVA** | **AL / Arapiraca** | **BRADESCO + MERCANTIL (3 contratos, cadeia inter-banco)** | **jeal-2bancos** | **OK 12/05/2026 — caso paradigma da regra "intro fática multi-banco" (§9-nonies). Helper `aplicar_intro_fatica` agrupa contratos por banco em "BANCO X, CONTRATOS Y, e ao BANCO Z, CONTRATO W"; blocos a/b/c identificam o banco real de cada contrato** |

> Para o status do batch corrente, ver `Modelos/IniciaisNaoContratado/_checkpoint-sessao.md` (a criar).

## Notas de operação adicionais

### Bradesco como banco-PAGADOR vs banco-RÉU

O Bradesco aparece em DOIS papéis possíveis:
1. **Pagador** do benefício (banco onde o INSS deposita) — default
2. **Réu** (banco que fez o empréstimo fraudulento)

Se ambos forem o mesmo banco, aplica-se TNU TEMA 183 inciso I (INSS NÃO responde subsidiariamente). A skill detecta isso e ALERTA no relatório paralelo, mas mantém INSS no polo passivo (deixar a decisão para o procurador).

### Sub-pastas do KIT — duplicação esperada

Pode haver `KIT/1 AVERBAÇÃO NOVA INATIVO/` com cópias de procurações que TAMBÉM estão em `BANCO XXX/2 AVERBAÇÃO NOVA INATIVO/`. **Ignorar a pasta KIT/...** (regra similar ao `inicial-bradesco`) — usar APENAS as pastas `BANCO XXX/`.
