---
name: fatiar-processo
description: Fatia PDFs consolidados de processos judiciais eletrônicos em múltiplos PDFs menores, um por evento/movimentação/documento. Suporta TRÊS sistemas com detecção automática — (1) eproc/TRF4/TJSC via "PÁGINA DE SEPARAÇÃO" + "Evento N", (2) PJe TJAM via tríade "Data: + Movimentação: + Por:" na página de rosto, e (3) PJe TJBA via "Num. NNN - Pág. 1" + "Assinado eletronicamente por:". Gera uma pasta com um PDF por marcador, nomeado "<prefixo>NNN-TIPO-descricao.pdf" (Ev/Mov/Doc conforme sistema). SEMPRE use esta skill quando o usuário mencionar: fatiar processo, dividir PDF do processo, quebrar PDF em eventos, separar eventos do PDF, splittar PDF do eproc, separar por evento processual, organizar PDF do processo, dividir autos por evento, fatiar autos, quebrar autos, separar peças do PDF, PDF grande do processo, processo consolidado, PDF do eproc, PDF do PJe, processo do TRF4, processo do TJSC, processo do TJAM, processo do TJBA, processo consolidado PJE. O resultado permite ler apenas os eventos relevantes (sentença, contestação, recurso) sem carregar o PDF inteiro, economizando tokens e tempo. Útil SEMPRE que o usuário fornecer um PDF grande baixado integralmente do sistema judicial e for trabalhar com análise de peças específicas.
---

# Skill: fatiar-processo

Divide PDF consolidado de processo eletrônico em múltiplos PDFs menores, um por evento/movimentação/documento.

## Sistemas suportados

| Sistema     | Marcador detectado                                          | Prefixo arquivo |
|-------------|-------------------------------------------------------------|-----------------|
| eproc/TRF4  | "PÁGINA DE SEPARAÇÃO" + "Evento N"                          | `Ev`            |
| PJe TJAM    | tríade "Data:" + "Movimentação:" + "Por:" na mesma página   | `Mov`           |
| PJe TJBA    | "Num. NNNNN - Pág. 1" + "Assinado eletronicamente por:"     | `Doc`           |

A detecção é automática (varre as primeiras 15 páginas em busca de assinaturas únicas de cada sistema). Use `--sistema eproc|pje_tjam|pje_tjba` para forçar manualmente, se necessário.

## Uso

```bash
python ~/.claude/skills/fatiar-processo/scripts/fatiar.py "<caminho_pdf>" [--saida "<pasta>"] [--sistema eproc|pje_tjam|pje_tjba]
```

Por padrão a saída vai para uma subpasta `eventos` na mesma pasta do PDF.

## Regras de uso pela Claude

1. **Antes de ler um PDF grande de processo**, rodar esta skill primeiro. Depois trabalhar apenas com os PDFs fatiados relevantes.
2. **Nome dos arquivos gerados:**
   - eproc: `EvNNN-TIPODOC-descricao.pdf` (TIPODOC = sigla no rodapé: SENT1, INIC1, CONTES1)
   - PJe TJAM: `MovNNN-TIPO-DD/MM/AAAA - DESCRIÇÃO.pdf` (TIPO = INIC, CONTES, SENT, DESP, DEC, DJE, etc.)
   - PJe TJBA: `DocNNN-TIPO-DD/MM/AAAA - TIPO - ASSINANTE.pdf`
3. **eproc**: a primeira parte do PDF (antes da primeira página de separação) vira "Evento 001 - INICIAL E DOCUMENTOS".
4. **PJe TJAM**: cada movimentação processual gera um arquivo, mesmo as automáticas do sistema (`SISTEMA PROJUDI`). Filtra falsos positivos verificando se "Movimentação:" aparece na primeira metade da página (página de rosto, não anexo).
5. **PJe TJBA**: cada documento individual (com `Num. único`) vira um arquivo. Tipicamente gera mais arquivos que TJAM porque cada anexo tem seu próprio Num.

## Limitações

Não fatia documentos agrupados no mesmo evento (ex: Evento 1 com INIC1 + DOC2 + DOC3 ficarão juntos). Isso atende 90% dos casos; quando precisar fatiar mais fino, usar busca literal direto no PDF do evento.

Requer `pymupdf` (fatiamento com garbage collection real — evita inflate por recursos compartilhados do PDF consolidado). Instalar: `pip install pymupdf`.

## Salvaguarda anti-inflate

A skill aborta automaticamente se a soma dos PDFs fatiados exceder 2x o tamanho do original. Isso protege contra cenário em que o PDF tem Form XObjects/fontes pesadas compartilhadas que podem ser duplicadas em cada split. Se abortar, investigar antes de tentar de novo — nunca desativar a salvaguarda sem diagnóstico.
