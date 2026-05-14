# replica-rmc

Skill autônoma do escritório **Azevedo Lima & Rebonatto** para gerar réplica à contestação em ações de RMC/RCC (Reserva de Margem Consignável / Cartão Consignado), cobrindo AM/AL/BA/MG.

## Por que existe

Gabriel (advogado, OAB/SC 76040) queria um fluxo onde "joga o processo e a réplica sai pronta, conforme o modelo do escritório". A skill faz exatamente isso: recebe uma pasta de processo, aciona 4 subagentes especializados, navega o vault Obsidian `Modelos/ReplicasRMC/` e entrega:

1. `.docx` da réplica em Cambria;
2. relatório de conferência paralelo (.docx);
3. ficha de aprendizado pré-preenchida no vault.

Escopo restrito: somente réplica RMC/RCC. Apelação, inicial e cumprimento têm skills próprias.

## Arquitetura

```
/replica-rmc <pasta>
      │
      ├─ (0) fatiar-processo  (se PDF consolidado)
      │
      ├─ (1) analisador-processo-rmc    → _analise.json
      │
      ├─ (2) consultor-vault-rmc        → _plano.json
      │
      ├─ (3) redator-replica-rmc        → Replica - <CNJ> - <NOME>.docx
      │
      ├─ (4) revisor-replica-rmc        → Relatorio_Conferencia_<CNJ>.docx
      │
      ├─ (5) iteracao (max 2) se AJUSTES
      │
      └─ (6) ficha de aprendizado em Aprendizado/ReplicasRMC/
```

Cada subagente tem contexto isolado e roda em paralelo ou em sequência conforme dependência. Os dados intermediários (`_analise.json`, `_plano.json`) ficam na própria pasta do processo — permite retomada em nova sessão se algo interromper.

## Estrutura

```
~/.claude/skills/replica-rmc/
├─ SKILL.md                              ← carta de missão da skill
├─ README.md                             ← este arquivo
├─ references/
│  ├─ schema_caso.json                   ← schema do _analise.json
│  └─ schema_plano.json                  ← schema do _plano.json
└─ scripts/
   ├─ fatiar_processo.py                 ← wrapper de fatiamento
   ├─ extract_processo.py                ← PyMuPDF → texto estruturado
   ├─ check_ip_rfc1918.py                ← Regra 16
   ├─ check_ted_conta_inss.py            ← Regra 4 / Bloco B
   ├─ detect_2via_massiva.py             ← Regra 2 / Bloco A
   ├─ check_cartao_gemeo.py              ← Regra 10 (Santander)
   ├─ check_bmg_pre_09_2023.py           ← Regra 7 / Bloco C
   ├─ check_refin_maquiador_bmg.py       ← Regra 9
   ├─ gerar_docx.py                      ← montagem .docx
   ├─ forcar_cambria.py                  ← força Cambria em todos os runs
   └─ gerar_relatorio_conferencia.py     ← .docx do revisor

~/.claude/agents/
├─ analisador-processo-rmc.md
├─ consultor-vault-rmc.md
├─ redator-replica-rmc.md
└─ revisor-replica-rmc.md

~/.claude/commands/
└─ replica-rmc.md                        ← slash command /replica-rmc
```

## Entrada esperada

Caminho de pasta que contenha **PDF consolidado** do processo ou pasta **já fatiada** com ao menos inicial + contestação.

```
/replica-rmc C:\Users\gabri\OneDrive\Documentos\Processos\Maria Silva\0600700-28.2025.8.04.0100
```

## Saída ao usuário

Mensagem curta padronizada:

```
Réplica gerada.

Arquivo:    C:\...\Replica - 0600700-28 - MARIA SILVA.docx
Relatório:  C:\...\Relatorio_Conferencia_0600700-28.docx
Ficha:      ...\Obsidian Vault\Aprendizado\ReplicasRMC\2026-04-22-maria-silva-maues.md

Classificação: APTO | AJUSTES APLICADOS | AJUSTES RESIDUAIS
Pontos de atenção: <lista curta>
```

Sem recap. Gabriel abre o `.docx`, revisa, protocola.

## Dependências

Python 3 com:

```
pip install pymupdf python-docx
```

Vault Obsidian em `C:\Users\gabri\OneDrive\Documentos\Obsidian Vault\Modelos\ReplicasRMC\`. O consultor-vault-rmc navega essa árvore para selecionar modelo-base e teses modulares.

## Regras inegociáveis

São 11 regras absolutas dentro da skill (detalhadas em `SKILL.md`):

1. Cidade do fecho = comarca real. Nunca "Manaus/AM" automático. Erro 22.
2. Cambria obrigatório. Erro 19.
3. Sem imagens. Erro 20.
4. Listas em a)/b)/c) ou i/ii/iii. Nunca traços. Erro 21.
5. "Declaração de inexistência". Nunca "anulação". Erro 6.
6. IP: checar RFC 1918 antes de chamar de privado. Regra 16.
7. TED: cruzar com conta INSS. Regra 4.
8. 2ª via massiva: inserir Bloco A. Regra 2.
9. BMG pré-09/2023: inserir Bloco C. Regra 7.
10. RMC + RCC gêmeos: sempre verificar HISCON. Regra 1.
11. Maués: cautela Juiz Anderson. Regra 13.

## Retomada em nova sessão

Se a skill for interrompida, retoma pelos JSON salvos:

1. Existe `_analise.json` e não `_plano.json` → retoma em (2).
2. Existe `_plano.json` e não `.docx` → retoma em (3).
3. Existe `.docx` sem relatório → retoma em (4).

## Cobertura atual

Três casos paradigmas catalogados no vault (Fase 3):

1. ALUIZIO — Santander — Caapiranga/AM (cartão gêmeo)
2. ANNA CLARICE — BMG — Boa Vista do Ramos/AM (BMG pré-09/2023)
3. ANTONIO MARCOS — BMG — Maués/AM (refin maquiador, BPC/LOAS)

Das 16 regras de adaptação: 3 transversais (3 em 3 casos), 3 recorrentes (2 em 3), 5 específicas (1 em 3), 5 editoriais.

## Referências cruzadas

Skill `fatiar-processo` — pré-requisito se PDF consolidado.
Skill `conferencia-processual` — usada internamente pelo revisor.
Skill `analise-cadeias-hiscon` — não é chamada aqui; usar em triagem antes da inicial.

## O que esta skill NÃO faz

Não redige inicial, apelação ou cumprimento. Não negocia acordo. Não analisa HISCON isoladamente. Não fatia PDF sozinha (delega para skill específica).

## Histórico

Criada em 2026-04-22 após consolidação dos 3 casos paradigma em 3 fases de análise no vault.
