---
name: inicial-rmc-rcc
description: Gera petição inicial em ações ANULATÓRIAS de contrato de RMC (Reserva de Margem Consignável) ou RCC (Cartão de Crédito Consignado) por vício de consentimento — autora celebrou contrato achando que era empréstimo consignado normal. Cobre AM Estadual (TJAM/Patrick), AL/BA/MG (templates parametrizados por UF). Aplica as 5 regras canônicas do paradigma BENEDITA (2026-05-13): valor líquido HISCON, contagem só do contrato corrente, tabela Quadro Sumário centralizada, polo passivo 12pt, planilha XLSX aba única. Use quando o usuário pedir inicial de RMC, inicial de RCC, processar pasta de cliente RMC/RCC, ou fizer o pedido "faz a inicial de [cliente] do BMG/Pan/etc". NÃO usar para empréstimo NÃO CONTRATADO (use `inicial-nao-contratado`).
---

# Skill: inicial-rmc-rcc

Geração automatizada de **petições iniciais** em ações anulatórias de RMC/RCC (vício de consentimento — autora **celebrou** o contrato mas pensando ser empréstimo consignado tradicional). Escritório De Azevedo Lima & Rebonatto.

> **Distinção crítica**: esta skill é para casos em que a autora **assinou o contrato**, mas o banco vendeu como empréstimo consignado quando era cartão RMC/RCC. Para casos em que a autora **NÃO assinou** (fraude absoluta), use a skill `inicial-nao-contratado`.

## INSTRUÇÕES OPERACIONAIS

Quando o usuário invocar `/inicial-rmc-rcc` ou pedir uma inicial de RMC/RCC:

**1. Identificar o perfil de jurisdição (UF)**

| O que o usuário diz | Perfil |
|---|---|
| AM / Manaus / Maués / TJAM / Patrick | `AM` |
| AL / Arapiraca / Maceió / Tiago | `AL` |
| BA / Salvador / Dr. Edu / Gabriel | `BA` |
| MG / Uberlândia / Dr. Xande / Alexandre | `MG` |

**2. Identificar a tese**

| Tese | Quando usar |
|---|---|
| `RMC` | Reserva de Margem Consignável (desconto no contracheque/benefício) |
| `RCC` | Reserva de Cartão de Crédito Consignado (cobrança via fatura) |

**3. Identificar o banco-réu**

| Banco | Template |
|---|---|
| BMG | `*-BMG.docx` (tem parágrafo Forbes/Família Guimarães) |
| Demais (Pan, Bradesco, Itaú, Daycoval, Parati, Safra, etc.) | `*-Demais bancos.docx` |

**4. Localizar a pasta do cliente**

`C:\Users\gabri\OneDrive\Área de Trabalho\APP - RMC-RCC\<cliente>` ou subpasta de banco. Procurar:
- Procuração (extrair nome, CPF, endereço, número do contrato);
- RG/CPF (extrair data nascimento → idoso se ≥60, gênero via filiação ou contexto);
- HISCON do INSS (extrair benefício, NB, banco pagador, agência/conta, base de cálculo, total comprometido, e detalhamento mês-a-mês dos descontos do contrato);
- Comprovante de residência.

**5. Aplicar as 5 REGRAS CANÔNICAS (paradigma BENEDITA)**

> ⚠️ **FONTE AUTORITATIVA: HISCRE (Histórico de Créditos)**, **não HISCON**. O HISCRE mostra o valor LÍQUIDO recebido pela autora mês a mês e cada desconto pela rubrica (217 = RMC, 268 = RCC). É o documento oficial pra valor da causa.

> 🚫 **NÃO usar/exigir extrato bancário** (conta corrente da autora no banco pagador do benefício). O escritório **não trabalha com extrato bancário** em ações de RMC/RCC. A prova dos descontos vem do HISCRE (oficial do INSS), não da conta da autora. Não incluir em pendências.

> 🚫 **NUNCA presumir/estimar valores em RMC/RCC**. Diferente do NC (que tem valor de parcela fixo no HISCON e pode ser presumido pelo qtd × valor), o RMC/RCC tem cobrança **rotativa** que varia mês a mês conforme uso do cartão. Estimar valor seria **má-fé processual**. Se a rubrica 217 (RMC) ou 268 (RCC) está vazia no HISCRE → **PENDÊNCIA**, não gera inicial. Aguardar HISCRE com a rubrica preenchida. Esta é a diferença fundamental com a regra `permitir_contrato_virtual=True` da skill `inicial-nao-contratado` (que se aplica APENAS a NC).

| # | Regra | Implementação |
|---|---|---|
| 1 | **Valor líquido = campo "Valor Líquido" do HISCRE (competência mais recente)** | extraído por `extrair_descontos_hiscre()` |
| 2 | **Quantidade de descontos = TODAS as ocorrências da rubrica 217/268 no HISCRE** | `extrair_descontos_hiscre(pdf, rubrica="217")` |
| 3 | **Tabela Quadro Sumário centralizada (conteúdo)** | `centralizar_celulas_tabela_quadro_sumario()` |
| 4 | **Polo passivo em 12pt** | `aplicar_12pt_no_polo_passivo()` |
| 5 | **Planilha XLSX aba única + coluna prescrição** | `_pipeline_caso.gerar_planilha()` |

### Pré-condição: HISCRE deve estar COMPLETO (regra acrescentada 2026-05-13)

**Antes de tentar gerar a inicial**, validar o HISCRE com `verificador_hiscre.verificar_hiscre(pdf_path, rubrica_esperada)`. Se retornar `completo=False`, **NÃO gerar inicial** — gerar `RELATORIO_PENDENCIA_HISCRE_<cliente>.docx` com `gerar_relatorio_pendencia_hiscre(...)` e parar.

Critérios de incompletude:
- Período declarado no header < 5 anos (não cobre prescrição CDC)
- Gap entre Compet. Final declarada e primeiro pagamento efetivo > 6 meses (HISCRE baixado parcial)
- Rubrica esperada (217 RMC / 268 RCC) com 0 ocorrências
- Contrato a impugnar marcado como `_virtual: true` no `_estado_cliente.json` (sem rastro no HISCON)

Sem HISCRE completo, o cálculo do valor da causa fica fragilizado e o banco pode contestar a existência dos descontos. O ônus de baixar o HISCRE completo (via meu.inss.gov.br) é do operador antes de invocar a skill novamente.

### Detalhe sobre as Regras 1 e 2 (refinadas 2026-05-13)

**Tentativas anteriores** (rejeitadas pelo usuário):
- ❌ Calcular valor líquido como `base_HISCON − total_comprometido` → produzia aproximação, não o valor real
- ❌ Contar parcelas pelo HISCON com identificador explícito `<contrato><banco>...` → o HISCON é da modalidade de cartão (RMC/RCC), mas tem identificadores ambíguos (formato antigo NB) e cobre um período diferente

**Solução correta**: usar o HISCRE como fonte única.

```python
descontos = extrair_descontos_hiscre(
    pdf_hiscre_path=r"7. Histórico de créditos.pdf",
    rubrica="217",  # 217=RMC, 268=RCC
)
# devolve list[dict] com competencia, valor_liquido, valor_rubrica
# cronologico (mais recente primeiro)
```

Cada entrada: `{"competencia": "01/2026", "valor_liquido": 1056.94, "valor_rubrica": 69.86}`. O valor da rubrica é o desconto MENSAL exato (sem inferência). A `data_do_primeiro_desconto` da inicial deve ser a competência mais antiga visível no HISCRE.

Mais:
- Conjugação automática de gênero (`brasileira` → `inscrita`/`domiciliada`)
- Omissão limpa de campos ausentes (estado civil, RG inválido)
- Cabeçalho idoso em Cambria 11pt + direita + recuo 4cm
- Pedido idoso com texto canônico NC em Cambria Bold
- Endereço escritório (matriz + apoio) na qualificação
- `quali_banco` em 2 runs (Segoe UI Bold rStyle 2TtuloChar + Cambria) 12pt
- GRIFO AMARELO em TUDO que a skill substituir
- Limpeza de grifos legacy do template

**6. Invocar pipeline**

```python
import sys
sys.path.insert(0, r'C:/Users/gabri/.claude/skills/inicial-rmc-rcc/references')

from _pipeline_caso import renderizar_caso
from perfis_juridicos import perfil

caso = {
    "perfil": perfil("AM"),
    "tese": "RMC",
    "comarca": "Maués",
    "autora": {
        "nome": "BENEDITA WALKYRIA REIS BARBOSA",
        "nacionalidade": "brasileira",
        "estado_civil": "",      # vazio → omitido limpamente
        "profissao": "aposentada",
        "cpf": "343.084.662-53",
        "rg": "0469611-5",
        "orgao_expedidor": "SSP/AM",
        "logradouro": "Comunidade Menino Deus",
        "numero": "s/nº",
        "bairro": "Setor Parauari",
        "cidade": "Maués",
        "uf": "AM",
        "cep": "69.190-000",
        "eh_idoso": True,        # idade ≥ 60
    },
    "beneficio": {
        "tipo": "aposentadoria por invalidez previdenciária",
        "nb": "605.559.920-5",
        "banco_pagador": "BRADESCO S.A.",   # SEM prefixo "BANCO"
        "conta_agencia_conta": "agência 3706, conta corrente nº 0005524601",
        "base_calculo": 1621.00,
        "total_comprometido": 575.25,
    },
    "banco": {
        "nome": "BANCO BMG S/A",                  # texto que entra no run Segoe Bold
        "nome_curto": "BANCO BMG",                # para o relatório/planilha
        "cnpj": "61.186.680/0031-90",
        "resto_qualificacao": (
            ", pessoa jurídica de direito privado, inscrita no CNPJ/MF sob "
            "o nº 61.186.680/0031-90, com endereço na Rua Marcelio Dias, nº "
            "291, Centro, Manaus/AM, CEP 69.005-270"
        ),
    },
    "contrato": {
        "numero": "12257818",
        "data_inclusao": "04/02/2017",            # filtra descontos a partir daqui
        "data_primeiro_desconto": "02/2017",
        "descontos_hiscon": [
            # (competencia, valor) — cronologico recente -> antigo
            ("03/2026", 69.86), ("02/2026", 69.86), ...
        ],
    },
    "procurador_nome": "Patrick Willian da Silva",
    "procurador_oab": "OAB/AM A2638",
    "pendencias": [
        ("Estado civil", "Não consta — colher junto à cliente."),
        ("Extrato bancário Bradesco", "Pendente."),
    ],
}

resultado = renderizar_caso(caso, pasta_saida=r"C:/.../Templates Padronizados/Teste - 1/BANCO BMG - RMC-RCC")
# resultado = {'inicial': '...', 'planilha': '...', 'relatorio': '...'}
```

**7. Reportar ao usuário**

Listar os 3 arquivos gerados, valor da causa, número de parcelas (histórico vs prescrição), e qualquer pendência que ficou no relatório paralelo.

## Estrutura de arquivos

```
~/.claude/skills/inicial-rmc-rcc/
├── SKILL.md                          # este arquivo
└── references/
    ├── helpers_docx.py               # substituir_in_run (grifo amarelo run-aware) + primitivas
    ├── helpers_redacao.py            # 5 regras canônicas + conjugação + idoso + escritório
    ├── perfis_juridicos.py           # CONFIGURAÇÃO por UF (AM ativo; AL/BA/MG mapeados)
    ├── _gerar_templates.py           # Gera templates padronizados a partir dos originais
    └── _pipeline_caso.py             # Pipeline completo: inicial + planilha + relatório
```

Templates DOCX padronizados ficam em:
`~/OneDrive/Área de Trabalho/APP - RMC-RCC/Templates Padronizados/<UF>/`

Templates originais (do Patrick, Tiago, Edu, Xande) ficam em:
`~/OneDrive/Área de Trabalho/APP - RMC-RCC/Tese R{MC,CC}/`

## Como regenerar todos os templates (após mudança em alguma regra)

```bash
cd ~/.claude/skills/inicial-rmc-rcc/references
python _gerar_templates.py           # todas as UFs ativas
python _gerar_templates.py AM        # só AM
```

## Adicionar UF nova

1. Garantir que os templates originais estão em `APP - RMC-RCC/Tese R{MC,CC}/` com nome compatível.
2. Editar `perfis_juridicos.py` → adicionar entrada em `PERFIS` (já há `AL`, `BA`, `MG` mapeados).
3. Rodar `python _gerar_templates.py <UF>`.
4. Validar visualmente os templates gerados.

## REGRAS CRÍTICAS (não esquecer)

### 1. PROCURAÇÃO é a única fonte autoritativa do número do contrato

Se a procuração da cliente menciona "Contrato 12257818", impugnar APENAS esse contrato. NUNCA pegar "todos os contratos do banco" como fallback. Mesmo princípio da skill `inicial-nao-contratado`.

### 2. Valor LÍQUIDO ≠ base de cálculo

A "BASE DE CÁLCULO" do HISCON é a renda bruta. Para o **valor líquido** que aparece na inicial, calcular: `base - total comprometido`. Nunca colocar a base crua como valor líquido.

### 3. Descontos só do contrato CORRENTE

Quando o cartão RMC foi MIGRADO (contrato antigo excluído + contrato novo averbado), contar APENAS os descontos do contrato atual. Os descontos do contrato anterior (que aparece como "EXCLUÍDO" no HISCON) NÃO entram.

### 4. Banco-pagador SEM prefixo "Banco"

O template já contém `"junto ao Banco {{banco_que_recebe}}"`. Preencher `{{banco_que_recebe}}` com `"BRADESCO S.A."` (sem repetir "BANCO"), senão fica `"junto ao Banco BANCO BRADESCO S.A."`.

### 5. Idoso: cabeçalho em Cambria 11pt direita recuo 4cm; pedido em Cambria Bold

Texto canônico NC do pedido: *"A prioridade na tramitação, tendo em vista que a parte autora é pessoa idosa, nos termos do art. 1.048, inciso I, do Código de Processo Civil;"*

### 6. quali_banco em 2 runs separados, ambos 12pt

Nome do banco em **Segoe UI Bold via rStyle="2TtuloChar"**, resto em **Cambria**. Ambos com `w:sz val="24"` (= 12pt) e grifo amarelo.

### 7. Memória de cálculo XLSX em ABA ÚNICA

Para facilitar exportação PDF e juntada ao processo. NUNCA gerar planilha multi-aba.

## Paradigma e casos de teste

**BENEDITA WALKYRIA REIS BARBOSA** (BMG, contrato 12257818, AM, 2026-05-13) — caso paradigma. Pasta: `APP - RMC-RCC/Templates Padronizados/Teste - 1/BANCO BMG - RMC-RCC/`. Validações: idosa (72 anos), assinatura a rogo, estado civil ausente, valor líquido R$ 1.045,75, 104 parcelas históricas (02/2017 → 03/2026), 59 na prescrição, valor da causa R$ 22.242,40.

## TODOs conhecidos

1. **Assinatura a rogo** — template ainda não menciona art. 595 CC + rogado + 2 testemunhas. Adicionar quando aparecer caso 2.
2. **Parser HISCON automático** — atualmente os descontos são listados manualmente no `caso["contrato"]["descontos_hiscon"]`. Criar parser (espelhar `extrator_hiscon.py` do NC) que lê o PDF do HISCON e extrai automaticamente.
3. **Validador pós-geração** — auditor que conferiu o DOCX gerado contra checklist (12pt no polo, todos placeholders preenchidos, grifo amarelo aplicado, tabela centralizada, etc.).
