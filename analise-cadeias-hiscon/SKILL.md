---
name: analise-cadeias-hiscon
description: Parseia o PDF do HISCON (Histórico de Empréstimo Consignado do INSS) e monta grafo das cadeias de refinanciamento, portabilidade, migração, consolidação (N→1) e fracionamento (1→N). Detecta indícios de irregularidade (anatocismo em refinanciamentos sucessivos, cadeias longas, bancos sem vínculo com o beneficiário, operações-ponte, consolidações e fracionamentos). Gera relatório DOCX com árvore visual de cada cadeia, tabela detalhada de contratos, campos ausentes marcados em amarelo, ligações de baixa confiança em vermelho e avisos de leitura. Padrão visual do escritório (Cambria, cor #B3824C). SEMPRE use quando o usuário mencionar: HISCON, cadeia de empréstimos, refinanciamento consignado, portabilidade INSS, operação-ponte, anatocismo consignado, triagem de cliente consignado, analisar extrato de empréstimo INSS, mapear refinanciamentos.
---

# Skill: analise-cadeias-hiscon

Lê o HISCON (PDF baixado do meu.inss) e produz relatório completo de cadeias de empréstimo consignado para triagem de cliente e elaboração de peças.

## O que a skill faz

1. **Parseia o PDF HISCON** extraindo todos os contratos (ativos, suspensos, excluídos, encerrados) com números, bancos, datas, valores, taxas, CET, motivo de exclusão.
2. **Monta grafo de cadeias** usando quatro critérios em ordem de confiança:
   - Ligação explícita via campo "Migrado do contrato XXX" (alta)
   - Match por valor de parcela idêntico em janela ±60 dias (alta)
   - Consolidação N→1 ou fracionamento 1→N por soma de parcelas (média)
   - Proximidade temporal com mesmo banco (baixa — sinalizada)
3. **Detecta red flags**: crescimento anormal do valor (anatocismo), cadeias longas (>5 contratos), bancos sem vínculo com o beneficiário, operações-ponte (<60 dias ativas), consolidações/fracionamentos suspeitos.
4. **Gera relatório DOCX** no padrão do escritório com: identificação do beneficiário, resumo executivo, indícios consolidados, avisos de leitura em caixas destacadas, uma seção por cadeia (árvore visual + tabela de contratos + red flags específicos), apêndice com contratos isolados, nota metodológica.
5. **Sinaliza limitações** explicitamente: campos ausentes no HISCON (amarelo), ligações de baixa confiança (vermelho), contratos órfãos sem sucessor (caixa vermelha no topo).

## Uso

```bash
python ~/.claude/skills/analise-cadeias-hiscon/scripts/analisar.py "<caminho_hiscon.pdf>" [--saida "<destino.docx>"]
```

Se `--saida` não for informado, o DOCX é gerado na mesma pasta do HISCON com nome `Analise_Cadeias_<nome_do_arquivo>.docx`.

Opcionalmente salvar também o JSON bruto para revisão:
```bash
python ~/.claude/skills/analise-cadeias-hiscon/scripts/analisar.py "<hiscon.pdf>" --json "<saida.json>"
```

## Regras de uso pela Claude

1. **Sempre rodar antes de analisar manualmente um HISCON**, mesmo para casos simples. O parser captura padrões (convergências 4→1, fracionamentos 1→N) que escapam à leitura visual.
2. **Antes de elaborar peça de empréstimo não contratado**, revisar a seção "Avisos de leitura" do DOCX gerado — os contratos órfãos sinalizados em vermelho são candidatos a investigação especial (podem ter saído para crédito fora do consignado, o que muda a tese).
3. **Nunca ignorar as ligações marcadas como "baixa confiança"** — elas foram pareadas apenas por proximidade de data e merecem validação manual antes de citação na peça.
4. **Campos em amarelo na tabela ("⚠ —")** indicam que o INSS não disponibilizou o dado (geralmente juros/CET em contratos anteriores a 2019). Não são erros do relatório; mencionar o PDF original do contrato se precisar desses valores para a peça.
5. **Para triagem rápida em entrevista**, usar o resumo executivo + caixa de red flags consolidados no topo do DOCX — em 30 segundos o advogado tem noção do volume de irregularidades e quantas cadeias merecem atenção.

## Saídas

O relatório DOCX contém:

- **Caixa amarela/vermelha no topo** com avisos de leitura (quando aplicável)
- **Seção 1**: Identificação do beneficiário (nome, benefício, banco pagador, margem)
- **Seção 2**: Resumo executivo (totais, cadeias, ligações por nível de confiança)
- **Seção 3**: Indícios consolidados (distribuição das red flags)
- **Seção 4**: Cadeias identificadas (uma subseção por cadeia multi-contrato)
  - Metadados (nº contratos, ativos, bancos, totais)
  - Árvore visual em fonte monoespaçada
  - Tabela detalhada de todos os contratos (12 colunas)
  - Red flags específicos da cadeia
- **Seção 5**: Contratos isolados (apêndice com contratos sem cadeia)
- **Seção 6**: Nota metodológica (explicação dos níveis de confiança)

## Dependências

`pip install pdfplumber python-docx` (ambos já instalados no ambiente do escritório).

## Limitações conhecidas

1. O HISCON do INSS às vezes corta nomes de bancos em quebras de linha. A skill normaliza via tabela FEBRABAN (código → nome oficial) para os principais bancos; se aparecer um banco novo não catalogado, o nome truncado pode passar — nesse caso, atualizar o dicionário `BANCOS_OFICIAIS` em `scripts/analisador.py`.
2. Contratos com portabilidade para crédito não-consignado saem do HISCON e ficam como "órfãos sem sucessor" — isso é esperado e sinalizado.
3. O algoritmo não detecta casos em que o banco mudou o valor da parcela em refinanciamento (match por parcela falha). Nesses casos, o pareamento cai no fallback por data (baixa confiança).

## Ver também

- Skill `anthropic-skills:cumprimento-consignado` — para elaborar cumprimento de sentença sobre RMC/RCC do INSS
- Skill `anthropic-skills:analise-cadeia-consignados` — versão mais ampla com análise por procuração e cálculo de prescrição
- Sistema web em `Projeto Claude/sitio-cadeias/` — interface de upload + visualização das cadeias no navegador para entrevista
