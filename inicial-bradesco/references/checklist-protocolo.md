# Checklist Pré-Protocolo — Iniciais Bradesco

Verificações obrigatórias **antes** de entregar a inicial para o operador
humano protocolar. Cada item tem regra clara de aprovação.

---

## A) Identificação do autor

- [ ] Nome completo bate com a notificação extrajudicial
- [ ] CPF formatado `XXX.XXX.XXX-XX` e idêntico em todos os documentos
- [ ] RG / órgão expedidor consistentes (ou omitidos limpamente)
- [ ] Estado civil e profissão extraídos da notificação (ou omitidos limpamente, sem `,, ,,`)
- [ ] Endereço veio da fonte preferencial (declaração de domicílio > comprovante > notificação)
- [ ] Comarca de competência condiz com o endereço

## B) Conta bancária

- [ ] Agência e conta extraídas do extrato Bradesco real (não hardcoded)
- [ ] Cidade da filial casa com a agência
- [ ] Valor de remuneração mensal vem de `extrair_renda_real()` do extrato
  - se `None`, está marcado `[A CONFIRMAR]` na inicial e listado em pendências

## C) Tese e template

- [ ] Tese detectada por `classificador.detectar_teses_ativas()` confere com a pasta
- [ ] Template selecionado por `selecionar_template()` é o correto
- [ ] Mora + Encargo: tratada como 1 só tese (IRDR 0004464)
- [ ] PG ELETRON: 1 inicial por terceiro (não combinou)
- [ ] Combinação de teses observa critério (comarca pequena ou ≤ R$ 400)

## D) Valores e dano moral

- [ ] Total dos descontos = soma dos valores em `parsear_tabela_descontos`
- [ ] Dobro = total × 2
- [ ] Dano moral aplicado:
  - 1 tese isolada → R$ 15.000
  - 2+ teses combinadas → R$ 5.000 × N
  - PG ELETRON → R$ 15.000 fixo
- [ ] Valor da causa = dobro + dano moral
- [ ] Extensos batem com os valores numéricos (`num2words` aplicado em todos)

## E) APLIC.INVEST FÁCIL (se aplicável)

- [ ] `auditoria_aplic_invest()` rodou no extrato
- [ ] Saldo líquido **não** é negativo (ou foi confirmada a tese pelo operador)
- [ ] Pedido reflete a tese escolhida (estrita / conservadora / intermediária)

## F) PG ELETRON (se aplicável)

- [ ] Nome, CNPJ e endereço do terceiro extraídos da notificação
- [ ] CDC arts. 7º p.ún., 14, 25 §1º citados na fundamentação
- [ ] Súmula 479 STJ presente
- [ ] Litisconsórcio passivo Bradesco + Terceiro está claro no cabeçalho
- [ ] Apenas o nome do banco e o nome do terceiro estão em destaque (Segoe UI Bold)

## G) Formatação visual

- [ ] Fonte Cambria em todo o documento (testar abrir e selecionar texto)
- [ ] Rubricas em CAPS + negrito + itálico + sublinhado + amarelo
- [ ] Nome do autor em CAIXA ALTA com Segoe UI Bold (rStyle 2TtuloChar)
- [ ] Nenhum trecho em Sitka Text, Calibri, ou `font-claude-respon`
- [ ] Margens, espaçamento, recuo conforme template (não foram alterados)

## H) Auditoria pós-geração (`auditor.py`)

- [ ] `auditar_docx()` rodou e retornou severidade `OK` ou `ATENCAO` justificada
- [ ] `placeholders_residuais` = vazio
- [ ] `cpfs_suspeitos` = vazio
- [ ] `cnpjs_suspeitos` = vazio (ou todos verificados)
- [ ] `valores_suspeitos` = vazio (ou todos justificados)
- [ ] `datas_suspeitas` = vazio
- [ ] `nomes_vazados` = vazio

## I) IRDR e fundamentação

- [ ] Tarifas: IRDR 0005053-71.2023.8.04.0000 citado
- [ ] Mora/Encargo: IRDR 0004464-79.2023.8.04.0000 citado
- [ ] CDC e Código Civil corretamente referenciados
- [ ] Súmula 479 STJ (PG ELETRON / fato do serviço)
- [ ] Tema 1.061 STJ se houver discussão sobre prescrição
- [ ] EAResp 1.280.825/RJ (prescrição consumerista)

## J) Pedidos

- [ ] Declaratória de inexistência da relação jurídica
- [ ] Repetição do indébito EM DOBRO (CDC art. 42 p.ún.)
- [ ] Dano moral
- [ ] Tutela de urgência (se aplicável: para cessar cobranças)
- [ ] Inversão do ônus da prova (CDC art. 6º, VIII)
- [ ] Justiça gratuita
- [ ] Prioridade idoso (≥ 60 anos) com art. 1.048 CPC
- [ ] Prova: oitiva, documental, perícia se aplicável
- [ ] Citação do(s) réu(s) com endereço completo

## K) Pasta KIT (regra crítica)

- [ ] Nenhum documento dentro de `KIT/` foi lido na geração

---

## Severidade

- **OK** → liberada para revisão final humana
- **ATENCAO** → pelo menos 1 alerta amarelo; revisar antes de protocolar
- **CRITICO** → bloqueado; corrigir antes de qualquer entrega

---

## Output esperado

Arquivo .docx no caminho da pasta do cliente com nome no padrão:

```
INICIAL_<TESE>_<NOME_CLIENTE>_v<N>.docx
```

Exemplos reais já catalogados:
- `INICIAL_Tarifas_JOSE_SEBASTIAO_v1.docx`
- `INICIAL_MoraEncargo_MARIA_JOANA_v1.docx`
- `INICIAL_AplicInvest_ELINALDO_v1.docx`
- `INICIAL_PgEletron_ASPECIR_TEREZINHA_v1.docx`
- `INICIAL_PgEletron_MBM_TEREZINHA_v1.docx`
- `INICIAL_PgEletron_ODONTOPREV_TEREZINHA_v1.docx`
