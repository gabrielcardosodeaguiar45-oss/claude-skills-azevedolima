---
name: wiki-lint
description: Auditoria automática do vault Obsidian para detectar inconsistências antes que se acumulem. Roda 5 verificações (wikilinks quebrados, tags fora do vocabulário canônico, páginas órfãs sem incoming link, conceitos órfãos como precedentes citados sem ficha própria, e divergências de data em precedentes citados em múltiplos arquivos). Gera relatório em `_lint/lint-YYYY-MM-DD.md` no próprio vault, com wikilinks clicáveis para correção dentro do Obsidian. SEMPRE use quando o usuário mencionar: lint do vault, auditar vault, verificar consistência do vault, wikilinks quebrados, páginas órfãs, tags inválidas, divergências em precedentes, conferir fichas do vault, sanity check do vault, vault sujo, vault inconsistente, manutenção do vault, limpeza do vault, conferir Obsidian, validar Obsidian.
---

# Skill: wiki-lint

Implementação do conceito de "lint" da [LLM Wiki do Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) adaptada ao vault de advocacia. Detecta inconsistências silenciosas que se acumulam sem monitoramento.

## O que a skill faz

Roda cinco verificações no vault Obsidian:

1. **Wikilinks quebrados**. Encontra `[[X]]` apontando para arquivo inexistente. Considera basename, caminho relativo e aliases do frontmatter na resolução.
2. **Tags fora do vocabulário canônico**. Compara todas as tags (frontmatter + inline) com `_tags.md`. Sinaliza tags não cadastradas (ex.: `#bancário` quando o canônico é `#bancario`).
3. **Páginas órfãs**. Arquivos sem nenhum incoming wikilink. Exclui arquivos estruturais (`_index`, `_MOC`, `MOC-*`, `_template`, `_tags`, `Home`, `_checkpoint*`) e arquivos abaixo de 200 caracteres (stubs/placeholders).
4. **Conceitos órfãos**. Precedentes padronizados (Tema, EAREsp, EREsp, REsp, Súmula, ADI, IRDR) citados em ≥2 arquivos sem ficha consolidada em `Precedentes/`. Sugere criação da ficha.
5. **Divergências em precedentes**. Mesmo precedente referenciado com datas diferentes em arquivos distintos (ex.: EAREsp 1280825 com "30/03/2021" em uma ficha e "30/03/2022" em outra).

## Uso

```bash
python ~/.claude/skills/wiki-lint/scripts/wiki_lint.py "C:/Users/gabri/OneDrive/Documentos/Obsidian Vault"
```

Argumentos opcionais:

- `--saida <arquivo.md>` — caminho explícito do relatório (default: `<vault>/_lint/lint-YYYY-MM-DD.md`)
- `--orfa-min-tamanho <chars>` — limiar mínimo para considerar arquivo como órfão real (default: 200)

Sem dependências externas: usa apenas stdlib (re, pathlib, collections).

## Regras de uso pela Claude

1. **Rodar antes de iniciar trabalho de fôlego no vault** (ex.: criar nova área, refatorar taxonomia, ingerir lote de precedentes). O relatório aponta dívida acumulada que vale resolver antes de adicionar mais conteúdo.
2. **Após o lint, abrir o relatório no Obsidian** (não só ler o stdout). Os wikilinks no relatório são clicáveis e levam direto ao arquivo problemático.
3. **Cadência sugerida**: rodar semanalmente (segunda de manhã, junto com a rotina de prazos). Ou quando o usuário mencionar sintomas de inconsistência ("não acho aquela tese", "citei o precedente errado").
4. **Não corrigir automaticamente**. A skill apenas detecta. Cada categoria pede julgamento humano: tag fora do vocabulário pode ser typo (corrigir) OU candidata a entrar no vocabulário (atualizar `_tags.md`).
5. **Ao corrigir wikilinks quebrados**, verificar se o destino existia e foi renomeado vs. nunca existiu. Renomeação: ajustar todos os incoming. Inexistente: criar a ficha ou remover a referência.
6. **Conceitos órfãos têm prioridade alta**: cada precedente citado ≥3x sem ficha é dívida que pesa nas peças (re-pesquisa de zero, citações inconsistentes). Criar ficha em `Precedentes/` consolidando.
7. **Páginas órfãs nem sempre são lixo**: pode ser ficha boa esquecida do MOC. Antes de deletar, ver se faz sentido linkar do MOC da área.

## Exemplo de saída

```markdown
# Wiki Lint — 2026-04-30

| Categoria | Total |
|---|---:|
| Wikilinks quebrados | 3 |
| Tags fora do vocabulário | 5 |
| Páginas órfãs | 12 |
| Conceitos órfãos | 4 |
| Divergências em precedentes | 2 |

## 1. Wikilinks quebrados

**[[Teses/rmc-irdr-tema5-tjam]]** cita destinos inexistentes:
1. `[[Tema 5 TJAM]]`

## 4. Conceitos órfãos

### EAREsp 1280825

Citado em 5 arquivo(s):
1. [[Teses/prescricao-consignado]] (data citada: 30/03/2021)
2. [[Modelos/ReplicasRMC/_MOC]] (data citada: 30/03/2021)
...

> Sugestão: criar `Precedentes/earesp-1280825.md` consolidando.

## 5. Divergências em precedentes

### EAREsp 1280825

Datas distintas encontradas: 30/03/2021, 30/03/2022
1. [[Teses/prescricao-consignado]] → **30/03/2021**
2. [[Aprendizado/X]] → **30/03/2022**
```

## Limitações conhecidas

1. **Precedentes em formato livre não são detectados**. Captura apenas padrões `Tema NNN`, `EAREsp NNN`, `REsp NNN`, `Súmula NNN STF/STJ/TST`, `ADI NNN`, `IRDR NNN`. Casos como "Súmula Vinculante 47" ou "AgInt no AREsp" não entram (extender padrões em `PRECEDENTE_PATTERNS` do script).
2. **Aliases do frontmatter são lidos para resolução de wikilinks**, mas apenas se a tag estiver bem formada (`aliases: [a, b]` ou `aliases:\n  - a\n  - b`).
3. **Não detecta contradições semânticas**. Se duas fichas dizem coisas opostas sobre o mesmo precedente sem divergência de data, a skill não pega — isso pede leitura humana.
4. **Tags em texto corrido fora de frontmatter** podem ser falsos positivos se o autor escreveu, p. ex., `o#1` (não é tag, é "número um"). A regex pede `#` precedido de espaço/início e seguido de letra; mas casos como `\#literal` não são tratados.

## Ver também

- Skill `obsidian-markdown` — sintaxe Obsidian completa (caso de criar fichas novas a partir do relatório)
- Memória `reference_autoresearch.md` — origem do conceito (Karpathy)
- Memória `feedback_rag_processos.md` — por que descartamos RAG vetorial e mantemos a wiki como fonte canônica
