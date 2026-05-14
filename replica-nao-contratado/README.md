# replica-nao-contratado

Skill para gerar **réplica à contestação** em ações de empréstimo consignado **NÃO CONTRATADO** (cliente nega ter celebrado o contrato — fraude absoluta).

## Como usar

Em qualquer chat do Claude Code:

```
/replica-nao-contratado <caminho da pasta com PDF do processo>
```

ou simplesmente:

```
Faz a réplica desse processo de não contratado: <caminho>
```

O Claude lê a SKILL.md, segue o fluxo, e gera um `REPLICA_<BANCO>_<NOME>.docx` na mesma pasta.

## Pré-requisitos

1. **Vault Obsidian populado** em `~/Documentos/Obsidian Vault/Modelos/ReplicasNaoContratado/` com os 60 pilotos modulares
2. **Python 3** com `pymupdf` e `python-docx`
3. **Pasta com PDF do processo** consolidado (eproc/PJe/TJ)

## Estrutura

```
replica-nao-contratado/
├── SKILL.md                ← orquestração principal (Claude lê isso primeiro)
├── README.md               ← este arquivo
├── references/
│   └── helpers.py          ← funções utilitárias para gerar DOCX
└── scripts/
    (vazio — o Claude cria scripts ad hoc por caso, usando os helpers)
```

## Filosofia

A skill **não tem subagents** nem **scripts pré-compilados** porque cada caso é único. Em vez disso:

1. SKILL.md orienta o Claude a ler o PDF, identificar o caso e mapear teses contra o catálogo do vault
2. O Claude escreve um script Python ad hoc por caso (usando os helpers)
3. Roda o script, gera o DOCX
4. Entrega na pasta do processo

Os 3 scripts em `~/OneDrive/Área de Trabalho/CLAUDE/replicas-nao-contratado/_redigir-replica-*.py` servem como **modelos de referência** — estudar antes de gerar nova réplica para entender o padrão.

## Regras críticas

1. **Grifo amarelo** apenas em modificações (Camadas 2 e 3). Núcleo doutrinário (Camada 1) sem destaque.
2. **TED para conta divergente:** conferir HISCRE antes de argumentar fraude. Se não puder, ALERTAR.
3. **Teses sem piloto:** marcar com `[TESE A SER DESENVOLVIDA]` em amarelo, deixar espaço em branco.
4. **Cambria 12pt**, sem travessão como aposto, sem imagens embutidas (apenas placeholders textuais).

## Não use para

- RMC/RCC com vício de consentimento (existe outra skill)
- Apelações, iniciais ou cumprimento
- Casos onde o cliente reconhece ter contratado
