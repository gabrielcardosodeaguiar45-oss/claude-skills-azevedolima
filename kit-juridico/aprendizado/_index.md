# Aprendizado de Manuscritos — Índice

Conhecimento acumulado para leitura de procurações manuscritas, com
cross-check no HISCON e correções supervisionadas.

## Arquivos

- `padroes-bancos.md` — heurísticas estáveis por banco (formato de número, faixas comuns, dígito verificador)
- `correcoes.md` — log datado de TODAS as correções (toda correção é registrada, sem threshold)
- `manuscritos-conhecidos.md` — galeria curada de pares (crop, valor real) com observações
- `captadores/<nome-slug>.md` — ficha por captador/operador (caligrafia, padrões de erro, clientes típicos)
- `exemplos/<id>.png` — crops de manuscritos reais usados como referência (anexados pelas correções)

## Regra de uso

Antes de processar procurações manuscritas:
1. Ler `padroes-bancos.md` (formato esperado por banco)
2. Identificar o captador (pelo nome do PDF, contrato de honorários ou rótulo informado pelo usuário)
3. Se houver ficha em `captadores/<slug>.md`, ler antes de extrair (descontar os erros conhecidos)

Após cada correção do usuário:
1. Registrar em `correcoes.md` (log)
2. Se aplicável, atualizar `captadores/<slug>.md` (padrão recorrente)
3. Se aplicável, atualizar `padroes-bancos.md` (regra estável)
4. Salvar crop em `exemplos/` quando o caso for didático

## Política de Não-Generalização Prematura

Toda correção entra no log. Mas **regras estáveis** em `padroes-bancos.md` ou `captadores/*.md` exigem evidência observada — descreva no texto a base
("3 correções no mesmo captador onde '0' é confundido com '1' fechado")
em vez de afirmar como verdade absoluta.
