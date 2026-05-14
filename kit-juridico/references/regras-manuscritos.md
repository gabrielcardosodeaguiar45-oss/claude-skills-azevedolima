# Regras de Leitura de Procurações Manuscritas

Workflow para extrair banco/contrato de procurações com campos manuscritos
e validar contra HISCON (quando disponível).

## Antes de ler — preparação

1. **Ler `aprendizado/_index.md`** para conhecer os arquivos de aprendizado
2. **Identificar o captador** (pelo nome do PDF, contrato escritório, ou rótulo do usuário)
3. **Se houver ficha** em `aprendizado/captadores/<slug>.md`, ler antes de extrair
4. **Ler `aprendizado/padroes-bancos.md`** para conhecer formato esperado por banco

## Workflow de extração e validação

### Fase 1: Extração inicial (1ª tentativa)

Para cada página de procuração:
1. Renderizar com `proc_extractor.preparar_crops` (rotação 270°, crop 0.30-0.80)
2. Ler o crop visualmente para identificar:
   - Banco (texto manuscrito após "em face do BANCO" ou "BANCO")
   - Contrato (manuscrito após "Contrato nº")
   - Tipo (consignado vs RMC/RCC, pelo texto "em virtude de descontos do cartão de crédito")
3. **Normalizar** o número extraído:
   - Remover pontos, espaços, hífens (manter só dígitos)
   - Validar comprimento contra `padroes-bancos.md` (ex: Itaú = 9 dígitos)
4. Anotar a 1ª tentativa com **confiança baixa** (manuscrito é ambíguo)

### Fase 2: Cross-check com HISCON

**Se HISCON está disponível e parseado:**

Para cada procuração extraída:

```
Procuração diz: BANCO ITAU CONSIGNADO, contrato "631248310"
HISCON contém:  31 contratos no total

1. Match EXATO em todos os contratos do mesmo banco no HISCON?
   → SIM (achou): valida procuração, confiança 100%
   → NÃO: vai pra match aproximado
2. Match APROXIMADO (Levenshtein ≤ 2 dígitos)?
   → SIM e há 1 candidato único: SUGERIR correção, perguntar usuário
   → SIM e há múltiplos: marcar pendência, listar candidatos
   → NÃO: vai pra retry
3. Retry: aplicar técnicas de melhoria (Fase 3)
```

### Fase 3: Retry com técnicas de melhoria visual

Quando o match falha, em ordem:

#### 3.1. Crop super-zoom (5x-7x) + crop estreito da linha

```python
crop_linha_contrato(pdf, pag, output, zoom=5.0, y_ini=0.46, y_fim=0.55)
```

Pegar SÓ a linha onde está "Contrato nº NNNNN".

#### 3.2. Pré-processamento da imagem

- Aumentar contraste (PIL.ImageEnhance.Contrast)
- Binarização (threshold adaptativo via OpenCV)
- Sharpen (PIL.ImageFilter.SHARPEN ou unsharp mask)

#### 3.3. Comparação cruzada

Ao invés de extrair "do zero", comparar visualmente o manuscrito com a
LISTA RESTRITA de contratos do HISCON (filtrada por banco):

```
Pergunta: "Qual destes 7 contratos do Banco Itaú no HISCON da Marinete
combina com o que está escrito na procuração?"
- 649667381
- 653826378
- 639548569
- 634848576
- 631048329
- 628458426
- 626102379
```

Comparação visual de N candidatos é geralmente mais fácil que extração cega.

#### 3.4. Dedução por contexto

Se o cliente tem N contratos no HISCON daquele banco e já identifiquei
N-1, o último deve ser o que sobrou:

```
HISCON Itaú = {A, B, C, D, E, F, G}  (7 contratos)
Procurações Itaú já mapeadas: {A, B, C, D, E, F}
A 7ª procuração só pode ser G → confirmar visualmente.
```

### Fase 4: Falha total → solicitar ao usuário

Se nenhuma técnica funcionou:
1. Marcar a procuração com nome genérico:
   `2- Procuração - Banco <X> - REVISAR - Pag <N>.pdf`
2. Adicionar pendência crítica:
   ```
   Categoria: Procuração / Verificação cruzada
   Pendência: Manuscrito ilegível e não localizado no HISCON
   Observação: Pag N. Banco aparente: X. Tentei ler "ABC123" mas não bate.
                Solicitar ao usuário leitura ou nova procuração.
   ```
3. **Pedir explicitamente** ao usuário (no chat) a leitura correta

## Caso especial — SEM HISCON

Quando o cliente não trouxe extrato:

1. Fazer extração 1ª passada normalmente
2. Marcar TODAS as procurações com tag `VALIDAÇÃO_PENDENTE_HISCON`
3. Gerar Pendência crítica: "HISCON ausente — solicitar ao cliente"
4. Quando HISCON chegar (segunda etapa), executar Fase 2 retroativamente

## Caso especial — Procuração com contrato NÃO existente no HISCON

Pode acontecer: o cliente assinou procuração com banco/contrato que NÃO
aparece no HISCON. Possibilidades:

1. **Procuração escrita errada** (banco ou número equivocado pelo escrivão)
2. **Contrato realmente inexistente** (cliente foi ludibriado ou houve erro de cadastro)
3. **Banco diferente do declarado** (ex: procuração diz "Bradesco" mas o contrato real está com "Bradesco Financiamentos" código 394)

Nesses casos:
- Marcar como **pendência crítica**: "Procuração com contrato não localizado no HISCON — verificar com cliente; pode estar inválida"
- Não criar pasta de banco para esse contrato (ou criar pasta com sufixo `_REVISAR`)
- Documentar no relatório de pendências para decisão do advogado

## Registro de aprendizado

Após cada correção do usuário (manual ou via cross-check):

1. **Sempre** adicionar entrada em `aprendizado/correcoes.md`:
   - Data, cliente, captador, página, banco
   - Eu li `X` / Correto é `Y`
   - Origem da correção (HISCON exato / Lev≤2 / usuário)
   - Observação opcional sobre o padrão

2. Se identificar **padrão repetido no mesmo captador** (ex: "0" parece "1" fechado em 3+ correções):
   - Atualizar `aprendizado/captadores/<slug>.md` na seção "Padrões de erro recorrentes"

3. Se identificar **regra estável por banco** (ex: contratos Itaú novos sempre começam com 6):
   - Atualizar `aprendizado/padroes-bancos.md`

4. Se o crop é **didático** (ilustra bem um erro comum):
   - Salvar em `aprendizado/exemplos/<id>.png`
   - Linkar em `aprendizado/manuscritos-conhecidos.md`

## Heurísticas de leitura

### Erros visuais comuns em números manuscritos

Antes de afirmar `X`, considere se pode ser:

| Lido como | Pode ser | Quando duvidar |
|-----------|----------|----------------|
| 0 | 6 | curva fechada inferior |
| 0 | 9 | curva com pequena saída superior |
| 0 | 1 fechado | bola pequena (típico de algumas caligrafias) |
| 1 | 7 | quando tem traço médio na haste |
| 1 | l (letra) | em isolamento |
| 4 | 9 | quando o "4" não tem haste superior |
| 3 | 8 | curvas duplas |
| 5 | 6 | quando o "5" tem barriga grande |
| 5 | S | em letra cursiva |

### Comprimento do número

Se o número extraído tem comprimento DIFERENTE do esperado pelo banco
(ver `padroes-bancos.md`):
- Faltam dígitos: provavelmente o crop cortou parte do número (rever zoom)
- Sobram dígitos: pode ter capturado dígito da linha vizinha (ex: data, CEP)

### Pontuação arbitrária

Manuscrito frequentemente coloca pontos onde não deveria
(`315833.3299` → real `3158333299`). **Sempre** normalizar removendo
pontuação antes do match com HISCON.
