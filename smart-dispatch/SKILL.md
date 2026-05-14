---
name: smart-dispatch
description: Roteamento inteligente de modelo por tipo de tarefa para economizar tokens
user_invocable: true
---

# Smart Dispatch — Roteamento de Modelos

Analise a tarefa solicitada e recomende o modelo ideal. Use esta tabela:

## Opus (tarefas complexas)
- Planejamento arquitetural e decisões de design
- Raciocínio jurídico complexo (análise de teses, fundamentação)
- Análise de múltiplos documentos com cruzamento de dados
- Elaboração de peças processuais completas
- Debugging complexo com múltiplas variáveis

## Sonnet (tarefas intermediárias)
- Implementação de lógica de negócio
- Conferência processual padrão
- Geração de relatórios e pareceres
- Edição e revisão de documentos existentes
- Integração com APIs e serviços

## Haiku (tarefas simples)
- Formatação e estilização de documentos
- Geração de templates/boilerplate
- Renomeação e organização de arquivos
- Extração simples de dados de PDFs
- Conversão entre formatos (PDF→DOCX, etc.)

## Como usar
Ao receber uma tarefa, informe ao usuário:
1. Qual modelo é recomendado e por quê
2. Se a tarefa pode ser paralelizada entre modelos
3. Estimativa de economia vs usar Opus para tudo

## Exemplo de dispatch paralelo
Para "Analisar 10 contratos e gerar relatório":
- **Haiku**: Extrair dados de cada PDF (paralelo, 10x)
- **Sonnet**: Cruzar dados e identificar padrões
- **Opus**: Gerar análise jurídica final com fundamentação
