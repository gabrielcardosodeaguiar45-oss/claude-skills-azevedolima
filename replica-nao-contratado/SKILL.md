---
name: replica-nao-contratado
description: Gera réplica à contestação em ações de empréstimo consignado NÃO CONTRATADO (cliente nega ter celebrado o contrato — fraude absoluta). Usa o catálogo de 60+ pilotos modulares do vault Obsidian + verificações automáticas cruzadas (CCB×HISCON, hash idêntico, selfie reutilizada, TED para terceiro, divergência interna na contestação, cessão não notificada, RG com impossibilidade de assinar, etc.) + pipeline OCR híbrido (texto pymupdf + leitura visual nativa em peças críticas). Use quando o usuário pedir réplica de não contratado, réplica de empréstimo fraudulento, réplica bancária de fraude consignado, ou jogar pasta de processo de não contratado para análise. Tese central exigida: cliente NEGA ter contratado (não confunde com vício de consentimento de RMC/RCC). Cobre AL/AM/BA/ES/RS/SC.
---

# Skill — replica-nao-contratado

Orquestra a produção de **réplica à contestação** em ações declaratórias de inexistência de relação jurídica (fraude absoluta — cliente nega contratação), usando o catálogo de **60+ pilotos modulares** do vault Obsidian em `Modelos/ReplicasNaoContratado/`.

## Quando sou invocada

1. Usuário diz "faz a réplica desse processo de não contratado", "gera réplica do empréstimo fraudulento", "réplica bancária de fraude".
2. Usuário envia pasta de processo onde a tese é "não contratei" (não vício de consentimento).
3. Usuário diz `/replica-nao-contratado <pasta>`.

## Quando NÃO usar

1. Caso de RMC/RCC com vício de consentimento (cliente assinou achando que era empréstimo) → usar outras skills de RMC.
2. Caso de cumprimento, apelação ou inicial — esta skill só faz réplica.
3. Caso onde o cliente reconhece ter contratado mas alega abusividade → não é "não contratado".
4. **Réplica à contestação do INSS** — esta skill é EXCLUSIVA para banco. Réplica ao INSS é peça AUTÔNOMA, com template próprio em `Modelos/ReplicasNaoContratado/pecas-autonomas/replica-INSS-template.md`. Mesmo que o INSS esteja no polo passivo, NÃO rebater a contestação dele nesta réplica.

## Entrada obrigatória

Caminho para **pasta** contendo o PDF do processo (consolidado, baixado do PJe/eproc/TJ). Geralmente o nome do PDF tem o número CNJ.

## Sistema de 3 camadas dos pilotos

Cada piloto no vault `Modelos/ReplicasNaoContratado/teses-modulares/<categoria>/<nome>.md` tem:

- **Camada 1 — Núcleo doutrinário fixo** (~70-95% do texto): copy-paste LITERAL, NÃO mexer NUNCA
- **Camada 2 — Slots variáveis** (`{{CHAVES}}`): preencher com dados do caso
- **Camada 3 — Zonas de adaptação** (`[ZONA DE ADAPTAÇÃO]`): decisão estratégica caso a caso

> [!danger] PROIBIDO redigir argumentos próprios em substituição aos pilotos
> Para CADA tese a usar, é OBRIGATÓRIO abrir o piloto correspondente e transcrever o texto Camada 1 LITERALMENTE (incluindo citações jurisprudenciais), substituindo apenas slots e zonas. Reescrever do zero, ainda que pareça melhorar a redação, é violação grave da skill: perde-se a doutrina decantada do escritório e introduzem-se variações textuais não validadas. Erro detectado em caso anterior — reincidência inadmissível.

> [!danger] PROIBIDO cortar pilotos por decisão própria
> A skill insere todos os pilotos aplicáveis ao caso. A decisão de cortar/integrar pilotos redundantes é EDITORIAL HUMANA, feita pelo usuário no Word após a entrega. A skill nunca decide o que é "supérfluo".

## Fluxo autônomo — NÃO pedir confirmação ao usuário

```
/replica-nao-contratado <pasta>
      │
      ├─ (1) Localizar PDF na pasta
      │
      ├─ (1.5) FATIAR o PDF consolidado em fatias por arquivo (Arq:)
      │        - Usa `references/fatiar_pje_tjam.py` (PJe TJAM por padrão)
      │        - Cria pasta `_fatias/` ao lado do PDF
      │        - Cada fatia nomeada `NNN-movXXX-YY-tipo.pdf`
      │        - Permite ler peças isoladas (inicial, contestação, CCB, HISCRE, TED)
      │          sem carregar o PDF inteiro a cada extração
      │        - Para eproc/TRF4/TJSC ou PJe TJBA, chamar a skill `fatiar-processo`
      │          (que detecta o sistema automaticamente) antes de prosseguir
      │
      ├─ (1.6) [SE houver contratos DIGITAIS] EXECUTAR PERÍCIA DIGITAL
      │        - Importar `references/pipeline_pericia_digital.py`
      │        - Verificar cache em `_pericia/_pericia.json` (se existe, reusar)
      │        - Senão, executar `executar_pericia(...)` com:
      │            * lista de contratos digitais identificados
      │            * textos de CCB, trilha de auditoria, comprovante TED por contrato
      │            * caminho dos PDFs de cada CCB (para hash + metadados)
      │            * HISCRE por competência (banco do INSS na época do TED)
      │        - Salvar resultado em `_pericia/_pericia.json`
      │        - As 12 verificações A–L são executadas conforme
      │          `references/tabela-mestre-achado-piloto.md`
      │        - Verificações que exigem leitura visual (B validador ITI,
      │          H comparação de selfies) ficam como `risco: manual` no JSON
      │
      ├─ (2) Ler INICIAL e identificar:
      │        - Autor (nome, CPF, RG, idade, profissão, endereço, NB INSS)
      │        - Banco réu (nome, CNPJ, procurador)
      │        - Comarca, processo, juízo
      │        - >>> Procurador da autora (NOME COMPLETO + OAB) — capturar do rodapé da inicial
      │            para usar na ASSINATURA da réplica. NÃO usar lista fixa de 3 advogados.
      │        - Filial do escritório que atende (cidade) — usar na cidade da assinatura final
      │        - Notificação extrajudicial (AR digital/AR-Email) — capturar DATAS específicas
      │            (envio + entrega) se juntada
      │
      ├─ (3) Ler CONTESTAÇÃO (palavra "CONTESTAÇÃO" como cabeçalho de página
      │        ou "CONTES1" como tipo de evento) e extrair TODAS as teses arguidas
      │        pelo banco (literais — não parafrasear)
      │
      ├─ (4) Identificar contratos impugnados na inicial:
      │        - Número, valor, data, parcelas
      │        - Conta de depósito alegada
      │        - Cadeia de refinanciamentos (se houver)
      │        >>> Comparar com contratos JUNTADOS pelo banco na contestação:
      │            - Se algum contrato impugnado NÃO foi juntado pelo banco → tese da
      │              presunção art. 400 CPC + pedido individual de julgamento antecipado
      │
      ├─ (5) VERIFICAÇÕES CRUZADAS AUTOMÁTICAS (todas obrigatórias):
      │
      │   FÍSICAS:
      │   ────────
      │   a) Anotação "IMPOSSIBILIDADE DE ASSINAR" no RG × data dos contratos
      │      - Se RG anterior aos contratos: argumento devastador
      │
      │   b) Tipo de assinatura por contrato físico (via leitura visual):
      │      - CURSIVA + autor analfabeto/impossibilitado = nulidade DE PLANO
      │      - CURSIVA + caixa "A Rogo" NÃO marcada em pessoa que não pode assinar = nulidade
      │      - DIGITAL + caixa "A Rogo" marcada + duas testemunhas = perícia papiloscópica
      │      - DIGITAL sem rogo regular = pedido de nulidade
      │
      │   c) Declaração de residência (ou outras) em branco com assinatura solta
      │
      │   d) Cronologia anômala dos documentos físicos:
      │      - Comprovante de TED, CPF ou outros documentos emitidos APÓS data da CCB
      │      - Verificação cadastral feita após o contrato = sinal de fraude
      │
      │   e) Campo 14 da CCB vazio em contrato classificado como REFIN
      │      - Banco diz refin mas não declara qual contrato anterior
      │
      │   f) Campos cadastrais da CCB × documentos do autor:
      │      - Estado civil divergente
      │      - Endereço divergente
      │      - E-mail vazio em operação supostamente eletrônica
      │
      │   DIGITAIS:
      │   ─────────
      │   g) CCB × HISCON (impossibilidade temporal):
      │      - Se HISCON registra averbação ANTES da data de assinatura da CCB =
      │        impossibilidade material (não se averba contrato inexistente)
      │
      │   h) Hash idêntico entre contratos digitais:
      │      - Mesmo hash SHA-256 em arquivos de contratos distintos = mesmo PDF reutilizado
      │      - Comum em "Termo de Cadastro" / "Aviso de Privacidade" entre dois contratos
      │
      │   i) Reutilização de selfie entre contratos digitais (via leitura visual):
      │      - Comparar visualmente as selfies extraídas de cada contrato digital
      │      - Mesma roupa, mesmo fundo, mesma expressão = reutilização (não há prova de vida real por contrato)
      │
      │   j) Trilha de auditoria com status "Incompleto" em todos os passos
      │      (incluindo a etapa final "Proposta Paga")
      │
      │   k) SMS de formalização para telefone com DDD diferente da residência do autor
      │
      │   l) Identificação eletrônica (Certisign) por e-mail do próprio banco
      │      (ex.: safra@safra.com.br) — não por e-mail pessoal do consumidor
      │
      │   m) Originador/correspondente bancário em cidade distante da residência
      │
      │   FINANCEIRAS:
      │   ────────────
      │   n) TED para conta divergente (REGRA CRÍTICA HISCRE):
      │      - Capturar o comprovante de TED (DEMTRANSF, COMPTRANS) — se imagem, ler visualmente
      │      - Cruzar banco/agência/conta de DESTINO da TED com o banco do INSS
      │        registrado no HISCRE (Histórico de Créditos do INSS) na competência da TED
      │      - Se a conta da TED for DIFERENTE do banco onde o autor recebia o INSS:
      │          - Confirma fraude (TED para conta de terceiro)
      │          - Argumento devastador
      │      - Se HISCRE não disponível: ALERTAR explicitamente o usuário antes do protocolo
      │
      │   o) Divergência interna na contestação × documentos juntados pelo banco:
      │      - Comparar valores e número de parcelas afirmados no TEXTO da contestação
      │        com os mesmos campos no extrato financeiro / CCB juntada
      │      - Se contraditório: tese específica com tabela comparativa
      │
      │   p) Cessão de crédito não notificada (parcelas marcadas como "Cedida"
      │      no extrato financeiro do banco)
      │      - Tese art. 290 CC (cessão sem notificação ao devedor)
      │
      │   q) Contratos paralelos não impugnados com depósitos em contas divergentes
      │      - Mencionar como possível padrão de fraude maior, a apurar
      │
      ├─ (6) Mapear cada tese arguida pelo banco contra os pilotos do vault
      │        (ver tabela de mapeamento abaixo)
      │        Para teses sem piloto: marcar como "[TESE A SER DESENVOLVIDA]" em amarelo
      │
      ├─ (7) Calcular dano material — somente dos contratos com TED COMPROVADO
      │        (com fls./Num. específicos) pelo banco. Não incluir contratos sem TED na tabela:
      │        - Total descontado até a data
      │        - Total a ser descontado (parcelas restantes × valor)
      │        - Lucro do banco (total - liberado)
      │        - Percentual de lucro sobre o liberado
      │        - VALOR DO TED tirado do COMPROVANTE (não da contestação — banco pode escrever errado)
      │
      ├─ (8) Gerar DOCX combinando os pilotos LITERAIS:
      │        - Substitui slots {{CHAVES}} com dados reais
      │        - Resolve zonas [ZONA DE ADAPTAÇÃO] conforme contexto
      │        - GRIFA EM AMARELO tudo que foi modificado (Camadas 2 e 3)
      │        - Mantém SEM destaque o núcleo doutrinário (Camada 1)
      │        - Estrutura do mérito por contrato:
      │             - Sub-bloco DO CONTRATO FÍSICO (quando houver)
      │             - Sub-bloco DOS CONTRATOS DIGITAIS (quando houver)
      │             - Sub-sub-blocos individuais por contrato digital quando ≥2
      │        - Mapa visual da cadeia contratual quando houver refin/portabilidade/migração
      │        - Tabela inventário hashes SHA-256 quando ≥2 contratos digitais
      │        - Tabela lucro % real só dos contratos com TED comprovado
      │        - Pedidos finais INDIVIDUALIZADOS por contrato (não em bloco):
      │             - Nulidade dos com cursiva fraudulenta
      │             - Julgamento antecipado dos AUSENTES (art. 355 I + 400 CPC)
      │             - Perícia papiloscópica dos a rogo
      │             - Perícia grafotécnica dos físicos com cursiva impugnada
      │             - Perícia digital dos digitais
      │        - Cambria 12pt, citações 11pt itálico recuo 4cm
      │        - Margens 3cm sup./esq., 2cm inf./dir.
      │        - Espaçamento 1,5 linhas, justificado
      │        - ZERO travessão (—) ou hífen (-) como aposto
      │        - Listas com a), b), c) ou i, ii, iii — NUNCA traços
      │
      └─ (9) Salvar como REPLICA_<BANCO>_<NOME-AUTOR>.docx
              na MESMA pasta do PDF
```

## Estrutura padrão da réplica

```
[CABEÇALHO] — endereçamento simples (2 linhas centralizadas) + processo
[Apresentação enxuta — 1 frase]

>>> [INSERIR MANUALMENTE — Bloco padrão de fraude sistêmica do INSS, com tabela visual da reportagem Metrópoles
     "R$ 466 BILHÕES EM CONSIGNADOS" e investigações PF/CGU. NÃO entra automaticamente.]

SÍNTESE PROCESSUAL (bullets curtos, não parágrafo único)
└── Resumo das teses arguidas pelo banco

PRELIMINARES (na ordem em que o banco arguiu)
├── Pilotos LITERAIS aplicáveis
├── Pilotos novos disponíveis: perda-objeto-contrato-liquidado-refin · litigancia-ma-fe-banco-rebate

>>> [INSERIR MANUALMENTE — Bloco padrão de Lei 14.063/2020 (3 tipos de assinatura eletrônica)]
>>> [INSERIR MANUALMENTE — Bloco padrão de Selfie liveness (11 requisitos NT INSS)]
>>> [INSERIR MANUALMENTE — Bloco padrão de Assinatura inválida (validador ITI)]
>>> [INSERIR MANUALMENTE — Bloco padrão de Modus operandi "kit fraude"]

MÉRITO
├── Da irregularidade da contratação (abertura)
├── DO CONTRATO FÍSICO Nº {{XXX}} (quando houver)
│     - [PLACEHOLDER MANUAL — análise grafotécnica]
│     - Robôs para falsificar (piloto)
│     - Análises específicas detectadas
│
├── DOS CONTRATOS DIGITAIS (quando houver) — seção III.X estruturada
│     [Inserida via `helpers.injetar_pericia_digital(doc, pericia_json)`]
│     │
│     ├── III.X     Abertura: impugnação geral + tabela de identificação
│     │             (número, ADE, data, valor, evento/ID, status)
│     │
│     ├── III.X.1   Da moldura técnica geral [PILOTO FIXO MANUAL — amarelo]
│     │             Lei 14.063/2020 + MP 2.200-2/2001 + Res. CMN 5.057/2022
│     │
│     ├── III.X.2   Da régua biométrica [PILOTO FIXO MANUAL — amarelo,
│     │             apenas se banco invocou selfie/biometria]
│     │             11 requisitos liveness — IN INSS 138/2022, ISO 30107-3,
│     │             IEEE 2790-2020
│     │
│     ├── III.X.3   Da régua de assinatura digital [PILOTO FIXO MANUAL — amarelo,
│     │             apenas se há pretensa assinatura digital]
│     │             Validador ITI — MP 2.200-2 art. 10 §1º
│     │
│     ├── III.X.4   Das inconsistências individuais [SUB-BLOCO POR CONTRATO]
│     │             Para cada contrato digital, sub-bloco com:
│     │             - Tabela de achados aplicáveis (só A–K detectadas, risco
│     │               ALTO/MÉDIO/manual)
│     │             - Parágrafos por achado:
│     │                 * A → inconsistencias-dados-cadastrais
│     │                 * B → assinatura-invalida-validador-iti
│     │                 * C → ausencia-codigo-hash / codigo-hash / kit-fraude (C.3)
│     │                 * D → analise-metadados
│     │                 * E/F → ip-desconhecido / ip-correspondente-bancario
│     │                 * G → inconsistencias-trilha-auditoria /
│     │                       trilha-incompativel-comportamento-humano
│     │                 * H → selfie-liveness (+kit-fraude em H.2,
│     │                       +contratacao-digital-parte-analfabeta em H.4)
│     │                 * I → dados-correspondente-originador /
│     │                       correspondente-maues-manaus (caso AM)
│     │                 * J → inconsistencias-dados-cadastrais
│     │                 * K → ausencia-total-contrato-master
│     │                 * L → compensacao-valores-tese-nova (com calibração L.3 ética)
│     │
│     ├── III.X.5   Da matriz cruzada [APENAS SE ≥2 contratos digitais]
│     │             - Tabela comparativa: IP, sessão, selfie, correspondente,
│     │               horário aceite, hashes SHA-256
│     │             - Padrões sistêmicos detectados
│     │             - Aciona kit-fraude se ≥3 padrões;
│     │               cadeia-custodia-digital-inexistente se 1–2 padrões
│     │
│     ├── III.X.6   Da insuficiência probatória global
│     │             [piloto: insuficiencia-probatoria-prova-unilateral]
│     │             [+ piloto cadeia-custodia-digital-inexistente quando trilha
│     │              em arquivo separado da CCB sem hash de vínculo]
│     │             [+ piloto contratacao-digital-parte-analfabeta se autora
│     │              analfabeta]
│     │             [+ piloto merito-bradesco-logs específico Bradesco com logs]
│     │
│     └── III.X.7   Da utilização de robôs e do imperativo de perícia
│                   [piloto: robos-falsificar-assinatura]
│                   + pedido de perícia digital
│
├── Cadeia de refinanciamentos / migração (quando houver) — seção autônoma
│     [piloto: cadeia-refinanciamentos-fraude-autonoma]
│     [piloto: alegacao-refin-quando-nao-e — quando banco alega refin mas
│      HISCON mostra averbação nova]
├── Mapa visual da cadeia contratual (diagrama, quando houver)
├── Inversão do ônus / Tema 1.061 STJ
├── Compensação de valores (quando houver TED comprovado)
│     - Tabela do modus operandi (genérica)
│     - Tabela do lucro real do banco (só dos contratos com TED comprovado)
├── Ausência de dano material
├── Devolução em dobro
├── Ausência de defeito / Danos morais (QUASE OBRIGATÓRIA)
└── Juros moratórios

REQUERIMENTOS FINAIS — enxutos (5-6 itens, não 10+)
├── Rejeição dos argumentos do banco
├── Inversão do ônus da prova
├── Pedidos individualizados por contrato:
│     - Nulidade absoluta dos com cursiva fraudulenta
│     - Julgamento antecipado dos AUSENTES (art. 355 I + 400 CPC)
│     - Perícia papiloscópica dos a rogo
│     - Perícia grafotécnica dos físicos com cursiva
│     - Perícia digital dos digitais
├── Procedência dos pedidos da inicial (devolução em dobro + danos morais)
├── Eventual depoimento pessoal do preposto
└── Prequestionamento expresso

CIDADE/DATA — usar cidade da FILIAL do escritório que atende, não do juízo
ASSINATURA — apenas o advogado que assinou a INICIAL (NOME COMPLETO + OAB capturados da inicial)
```

## Tabela mestre de mapeamento — teses do banco × pilotos

A skill DEVE consultar e seguir esta tabela.

| Tese arguida pelo banco (variações) | Piloto do vault |
|---|---|
| Decadência (art. 178 CC, 4 anos) | `preliminares/decadencia` |
| Prescrição quinquenal (CDC, termo errado) | `preliminares/prescricao-quinquenal` |
| Prescrição trienal (CC) | `preliminares/prescricao-trienal` |
| Falta de interesse de agir / pretensão resistida (sem AR) | `preliminares/falta-prequestionamento` |
| Falta de interesse de agir (com AR digital juntado) | `preliminares/ausencia-interesse-agir-com-AR` |
| **Perda do objeto / contrato liquidado por refinanciamento** | `preliminares/perda-objeto-contrato-liquidado-refin` (NOVO) |
| Impugnação à JG / pedido INFOJUD | `preliminares/impugnacao-justica-gratuita` |
| Impugnação ao valor da causa | `preliminares/impugnacao-valor-causa` |
| Procuração inválida/genérica/não atualizada | `preliminares/validade-procuracao` |
| Comparecimento pessoal autora | `preliminares/comparecimento-pessoal-autora` |
| Identidade desatualizada | `preliminares/identidade-desatualizada` |
| Comprovante de residência | `preliminares/comprovante-residencia` |
| Inépcia / inicial genérica | `preliminares/inepcia-inicial-generica` |
| Coisa julgada | `preliminares/coisa-julgada` |
| Conexão | `preliminares/conexao` |
| Incompetência juizado/justiça federal | `preliminares/incompetencia-juizado-especial` |
| Lapso temporal / duty to mitigate / venire | `preliminares/lapso-temporal` + `merito-argumentativo/boa-fe-objetiva` |
| Ataques pessoais ao patrono / litigância predatória / contumaz / Recomendação 159 CNJ | `preliminares/ataques-defesa-patrono-cliente` |
| **Litigância de má-fé arguida pelo banco (multa art. 80 CPC)** | `preliminares/litigancia-ma-fe-banco-rebate` (NOVO) |
| Audiência de conciliação | `preliminares/audiencia-conciliacao` |
| Audiência de instrução e julgamento | `preliminares/audiencia-instrucao-julgamento` |
| Defesa templated / desconexa da inicial | `preliminares/desconexao-contestacao-generica` |
| Impugnação aos cálculos | `preliminares/impugnacao-aos-calculos` |
| Necessidade de extrato bancário | `preliminares/ausencia-juntada-extrato` |
| Regularização do CPF (autora "morta") | `preliminares/regularizacao-cpf` |
| Validade do contrato digital (biometria + IP + geo) | `merito-probatorio-digital/selfie-liveness` + `assinatura-invalida-validador-iti` + `codigo-hash` ou `ausencia-codigo-hash` + `inconsistencias-trilha-auditoria` |
| Assinatura a rogo (analfabeto) | `merito-probatorio-misto/contratacao-digital-parte-analfabeta` |
| Múltiplos refinanciamentos | `merito-probatorio-misto/cadeia-refinanciamentos-fraude-autonoma` |
| Originador/correspondente em cidade distante | `merito-probatorio-misto/dados-correspondente-originador` ou `correspondente-maues-manaus` (caso AM) |
| IP da contratação | `merito-probatorio-misto/ip-correspondente-bancario` ou `merito-probatorio-digital/ip-desconhecido` |
| Comportamento concludente / venire / supressio / aceitação tácita | `merito-argumentativo/boa-fe-objetiva` + `merito-argumentativo/supressio` |
| Modulação repetição (EAREsp 600.663/RS) | `danos-fechamento/devolucao-em-dobro` (Camada 3 já tem nota) |
| Inexistência dano material | `danos-fechamento/ausencia-dano-material` |
| Inexistência dano moral / "indústria do dano moral" / razoabilidade | `danos-fechamento/ausencia-defeito-prestacao-servico-danos-morais` |
| Juros desde citação / arbitramento | `danos-fechamento/juros-moratorios` |
| Inversão do ônus inaplicável | `merito-argumentativo/inversao-onus-prova-tema-1061` |
| Compensação (banco depositou) | `merito-argumentativo/compensacao-valores-tese-nova` ou `compensacao-valores-versao-simples` |
| Cessão de crédito / portabilidade | `merito-argumentativo/responsabilidade-cessionario-portabilidade` |
| Culpa exclusiva da vítima (forneceu senha) | `merito-argumentativo/impossibilidade-culpa-exclusiva-consumidor` |
| Boa-fé objetiva genérica do banco | `merito-argumentativo/responsabilidade-objetiva-sumula-479` |
| Banco NÃO juntou contrato (presunção art. 400) | `processuais-especiais/ausencia-total-contrato-master` (preliminares + mérito) + `processuais-especiais/preclusao-contrato-documentos` (preliminar autônoma art. 434 CPC) |
| Análise de metadados | `merito-probatorio-digital/analise-metadados` |
| Selfie/biometria | `merito-probatorio-digital/selfie-liveness` |
| Assinatura digital ICP-Brasil/ZapSign | `merito-probatorio-digital/assinatura-invalida-validador-iti` |
| Hash incompatível | `merito-probatorio-digital/codigo-hash` |
| Hash ausente | `merito-probatorio-digital/ausencia-codigo-hash` |
| Trilha contrato + relatório separados | `merito-probatorio-digital/cadeia-custodia-digital-inexistente` |
| Aceites em segundos / contratante idoso | `merito-probatorio-digital/trilha-incompativel-comportamento-humano` |
| Dados cadastrais do contrato inconsistentes | `merito-probatorio-digital/inconsistencias-dados-cadastrais` |
| Insuficiência probatória geral | `merito-probatorio-misto/insuficiencia-probatoria-prova-unilateral` |
| Refinanciamento alegado mas HISCON mostra averbação nova | `merito-probatorio-misto/alegacao-refin-quando-nao-e` |
| Caso específico Bradesco (logs e demonstrativo) | `merito-probatorio-misto/merito-bradesco-logs` |
| Imprescindibilidade de perícia | `danos-fechamento/imprescindibilidade-pericia-digital` |
| Robôs falsificando assinaturas | `merito-probatorio-digital/robos-falsificar-assinatura` |
| Kit fraude (selfies + documentos comercializados) | `merito-probatorio-digital/kit-fraude` |

## Pipeline OCR híbrido (proposta C)

A skill usa estratégia híbrida para extrair conteúdo do PDF:

1. **Texto principal via pymupdf** (rápido) — funciona para PDFs com camada de texto
2. **Para PEÇAS CRÍTICAS, leitura visual nativa** — eu (Claude) leio a imagem PNG diretamente:
   - Comprovante de TED / DEMTRANSF / COMPTRANS — confirmar conta destino
   - Selfies dos contratos digitais — comparar reutilização
   - Trilha de auditoria — quando em formato de imagem
   - Páginas do contrato físico com assinatura — para classificar tipo
   - Declarações anexas (residência, hipossuficiência) — flagrar campos em branco
   - Prints da CCB — quando texto não extrai (PDF digitalizado)
3. **Tesseract opcional** — só se um caso específico precisar de OCR em massa de PDF totalmente digitalizado. Não faz parte do pipeline padrão.

Implementação no `references/visual_pipeline.py`.

## Regras inegociáveis

### Regra 1 — Grifo amarelo

**Grifar em amarelo** TUDO que foi modificado/adaptado ao caso:
- Dados específicos preenchidos nos slots Camada 2 (nomes, CPFs, datas, valores, cidades, números de contrato)
- Decisões resolvidas nas zonas Camada 3 (escolha de variantes, adaptações narrativas)
- Inserções factuais específicas do caso

**NÃO grifar** o núcleo doutrinário fixo da Camada 1 — texto que vem direto do piloto sem alteração.

### Regra 2 — Teses sem piloto

Se uma tese arguida pelo banco NÃO tiver piloto correspondente no vault:
1. Criar título da seção com nome da tese arguida
2. Inserir parágrafo em AMARELO com texto: `[TESE A SER DESENVOLVIDA — banco arguiu X mas não há piloto pronto. Desenvolver manualmente antes do protocolo.]`
3. Deixar 3 linhas em branco para preenchimento manual

NUNCA pular ou fingir que o banco não arguiu.

### Regra 3 — TED para conta divergente (HISCRE)

Quando o banco juntar comprovante de TED para conta diferente da declarada na inicial:

1. Antes de argumentar fraude, conferir HISCRE (Histórico de Créditos do INSS) na competência exata da TED.
2. Se a conta do TED **coincide** com banco de pagamento INSS na época → autora apenas mudou de conta. **NÃO usar argumento de fraude.**
3. Se **NÃO coincide** → fraude confirmada. Invocar HISCRE como **prova documental**.
4. Se HISCRE não disponível na pasta → ALERTAR explicitamente o usuário antes do protocolo.
5. **VALOR DO DEPÓSITO** sai do TED, não da contestação (banco pode errar na transcrição).
6. **COMPENSAÇÃO** só dos contratos com TED COMPROVADO (com fls./Num. específicos). Não incluir contratos sem comprovante.

### Regra 4 — Padrão visual

- Fonte: Cambria 12pt para corpo
- Citações: Cambria 11pt itálico, recuo 4cm
- Margens: 3cm (sup./esq.), 2cm (inf./dir.)
- Espaçamento: 1,5 linhas, justificado
- Negrito para títulos e termos-chave
- ZERO travessão (—) ou hífen (-) como aposto. Use vírgula ou parênteses.
- Listas: a), b), c) ou i, ii, iii. NUNCA traços.
- **Sem numeração contínua de parágrafos** — escrever em prosa contínua, com parágrafos separados por linha em branco. NÃO numerar parágrafos como 1., 2., 3.
- **Cabeçalho simples** (2 linhas centralizadas: vara + processo)
- **Apresentação em 1 frase**
- **Síntese em bullets curtos** (sem explicações longas entre parênteses)
- **Requerimentos finais com 5-6 itens** (não 10+)

### Regra 5 — Cidade e advogado da assinatura

- **Cidade** = cidade da FILIAL do escritório que atende a parte autora (capturar de "endereço onde recebem avisos e intimações" da inicial), não a cidade do juízo
- **Advogado** = nome completo + OAB do procurador que assinou a inicial. Não usar lista fixa de 3 advogados. Capturar do rodapé da inicial.

### Regra 6 — Cuidado com juiz Anderson (Maués/AM)

Em comarcas onde o juiz Anderson atua:
- Evitar peças muito longas e padronizadas
- Variar narrativa factual (não copiar "foi à agência INSS" entre processos consecutivos)
- Encurtar blocos doutrinários quando possível

### Regra 7 — Imagens

- Imagens devem ser **embutidas** no DOCX quando disponíveis (extraídas do PDF ou fornecidas pelo usuário)
- Para casos onde a imagem não pode ser embutida automaticamente, inserir placeholder textual em amarelo: `[INSERIR — Imagem 1: Print do validador ITI mostrando assinatura inválida]`

### Regra 8 — Blocos manuais (NÃO inserir automaticamente)

Os seguintes blocos são padrão do escritório e o usuário insere MANUALMENTE depois:

- **Bloco introdutório de fraude sistêmica do INSS** (com tabela visual da Metrópoles "R$ 466 bilhões")
- **Lei 14.063/2020** (3 tipos de assinatura eletrônica)
- **Selfie liveness** (11 requisitos NT INSS)
- **Assinatura inválida** (validador ITI)
- **Modus operandi "kit fraude"**

A skill apenas marca a posição com `[INSERIR MANUALMENTE — bloco padrão X]` em amarelo.

### Regra 9 — Análise grafotécnica é manual

A análise grafotécnica conclusiva é decisão humana. A skill apenas insere placeholder em cada contrato físico:

```
[ANÁLISE GRAFOTÉCNICA — PREENCHER MANUALMENTE NO CHAT
Comparar visualmente:
- Assinatura na CCB do contrato {{NUMERO}} (Evento {{X}}, fl. {{Y}})
- Assinatura padrão na Procuração (Evento {{X}}, doc {{Y}})
- Assinatura padrão no RG/CNH (Evento {{X}}, doc {{Y}})
Apontar: traçado, fluidez, pressão, fragmentação, similitudes/divergências.
Indicar se há indício de decalque (preto-e-branco, ausência de variação de pressão).]
```

### Regra 10 — Decisão editorial é humana

A skill insere TODOS os pilotos aplicáveis ao que o banco arguiu. A decisão de cortar/integrar pilotos redundantes é EDITORIAL HUMANA, feita pelo usuário no Word após a entrega. A skill nunca corta nem decide o que é "supérfluo".

### Regra 12 — L.3 ético: TED para conta diversa da do INSS (CALIBRAÇÃO OBRIGATÓRIA)

Quando o pipeline de perícia detecta verificação L.3 (TED depositado em conta diversa daquela em que a autora recebia o INSS na época, conforme HISCRE), aplicar **rigorosamente** a tese calibrada:

**PROIBIDO** afirmar ou pedir, sob qualquer circunstância:

- ❌ "Conta de terceiro" / "fraude para terceiro"
- ❌ "A autora não recebeu os valores"
- ❌ Pedido de **intimação da autora** para esclarecer titularidade

**Why:** se o advogado afirma que a autora não recebeu os valores ou pede intimação dela, e a autora possuir efetivamente conta no banco destino (que ela mesma pode não ter declarado na inicial), o cliente pode levar **má-fé processual**. O risco recai sobre o cliente, não sobre o banco.

**PERMITIDO (limite seguro — texto que entra na réplica):**

1. Mencionar a divergência factual: "TED foi para conta `<X>`, conta diversa daquela em que a autora recebia INSS na época, conforme HISCRE em todas as competências relevantes"
2. (Opcional, no máximo) Acrescentar que a autora "não percebeu o referido depósito" dentre os múltiplos lançamentos do extrato
3. Acionar a tese da `compensacao-valores-tese-nova`: o depósito não é prova de contratação, mas elemento da própria fraude; em eventual procedência, autoriza-se a compensação dos valores efetivamente creditados para evitar enriquecimento ilícito

**Pedido associado correto:** procedência + compensação dos valores efetivamente creditados — NUNCA intimação da autora.

A função `helpers.add_subbloco_contrato_digital()` já injeta o texto calibrado quando o JSON traz `variante: "L.3"`. O campo `texto_calibrado_etico` no JSON serve de lembrete reforçado para revisão.

### Regra 11 — Petição apartada de litigância predatória do Banco PAN

Em alguns processos, o **Banco PAN** apresenta, ALÉM da contestação, uma **petição apartada** alegando litigância predatória (em geral subscrita pelo escritório Lima e Feigelson Advogados — `pan.civel@limafeigelson.com.br`). Essa petição costuma vir como movimentação separada e foca em ataques ao patrono/cliente (Recomendação 159 CNJ, fracionamento, contumácia, etc.).

**A skill IGNORA essa petição apartada.** Não rebater nesta réplica:
- A peça gerada pela skill responde EXCLUSIVAMENTE à contestação propriamente dita do PAN.
- A defesa contra a petição apartada de litigância predatória, se necessária, é peça AUTÔNOMA, redigida manualmente pelo usuário em momento próprio (geralmente em manifestação específica após o juízo abrir vista).
- Caso a contestação propriamente dita já invoque, dentro de seu próprio corpo, o argumento de litigância de má-fé contra a parte autora (art. 80 CPC), ESSE rebate vai na réplica usando o piloto `litigancia-ma-fe-banco-rebate`. A regra acima vale apenas para a peça **APARTADA** de "litigância predatória".

### Regra 13 — Banco NÃO juntou contrato (cenário CCB-ausente, art. 400 + art. 434 CPC)

Quando o banco apresenta contestação SEM juntar o instrumento contratual impugnado (CCB, ficha cadastral, "laudo digital", trilha de auditoria), juntando apenas telas genéricas da plataforma de contratação, manuais de política de privacidade, normas técnicas (ISO 19794-5), prints de canais de atendimento etc., a skill DEVE acionar **automaticamente** o seguinte conjunto de teses:

**Detecção (heurística obrigatória do analisador):**

1. Contestação afirma "validade do contrato digital" / "biometria facial" / "assinatura eletrônica" / "selfie + IP + geolocalização" MAS;
2. Não há, anexada à contestação, CCB com dados do cliente (nome, CPF, valor, parcelas, conta) NEM trilha de auditoria com IDs de sessão/device/IP nominais ao caso concreto NEM imagem da selfie nominativa.
3. Os anexos do banco se resumem a: telas-padrão da plataforma + descrições genéricas + comprovante de TED (no máximo).

**Quando detectar, inserir OBRIGATORIAMENTE:**

- **Em PRELIMINARES:** [[processuais-especiais/preclusao-contrato-documentos]] (art. 434 CPC) — rebate antecipado a eventual juntada extemporânea.
- **Em PRELIMINARES (se o banco arguiu interesse processual, tutela ou pacta sunt servanda):** seções 1, 2 e 4 do [[processuais-especiais/ausencia-total-contrato-master]].
- **Em MÉRITO — primeiro bloco "Da irregularidade da contratação":** texto-padrão derivado do master (Seção 5 — presunção de veracidade do art. 400 CPC), com adaptação obrigatória listando, em letras a) b) c) d), os documentos que o banco efetivamente juntou, demonstrando a insuficiência de cada um. Padrão típico:
  - "(a) descrição genérica da plataforma de contratação digital do [BANCO], sem indicação de quaisquer documentos específicos;
  - (b) prints de telas de 'Política de Contratação por biometria facial' e 'Política de Privacidade';
  - (c) print do procedimento de captura de selfie segundo norma ISO 19794-5:2011;
  - (d) afirmações genéricas sobre 'laudo digital' que conteria nome do usuário, IP, ID da sessão e geolocalização — todavia, sem juntada do laudo em si nos autos;
  - (e) print de tela 'RESULTADO DE PESQUISA EM SISTEMA INTERNO';
  - (f) prints de canais de atendimento."

**O que NÃO fazer neste cenário:**

- ❌ NÃO injetar a seção III.X de perícia digital (não há contrato para periciar)
- ❌ NÃO acionar pilotos `merito-probatorio-digital/*` (selfie-liveness, hash, ITI, IP, metadados, etc.) — sem objeto de prova, esses pilotos perdem força
- ❌ NÃO listar verificações A–L como achados periciais (não há documentação para verificar)
- ❌ NÃO incluir tabela de identificação de contratos digitais (III.X)

**O que pode permanecer:**

- Tese de `robos-falsificar-assinatura` (genérica, não depende do contrato)
- `inversao-onus-prova-tema-1061` (rebate específico)
- `boa-fe-objetiva` (rebate venire/supressio quando arguidos)
- Cálculo de lucro do banco (apenas se houver TED comprovado nos autos)

**Caso paradigma:** Domingos × PAN (Teste 6, 2026-05-04, 1ª Vara Federal de Lages/SC). O banco PAN contestou afirmando contratação digital regular mas não juntou nenhum contrato — apenas telas genéricas da plataforma. A versão protocolada pela equipe usou exatamente este conjunto: preclusão (art. 434), presunção (art. 400) com lista a)-(f) dos anexos genéricos, irregularidade da contratação focada na ausência de assinatura, sem qualquer seção de perícia digital. Estrutura final enxuta: 5 preliminares + 8 sub-blocos de mérito + 5 requerimentos.

### Regra 14 — Glossário canônico dos slots de gênero (preenchimento dos DADOS_CASO)

A skill usa duas famílias de slots para gênero da parte autora, com **significados distintos** que NÃO podem ser confundidos. Erro de preenchimento gera frases gramaticalmente quebradas no DOCX final.

**Slot de SUJEITO COMPLETO** (substantivo + artigo, usado como sujeito da oração):

| Slot | Autor masculino | Autora feminina |
|---|---|---|
| `PARTE_AUTORA_GENERO` | `"o autor"` | `"a autora"` |
| `PARTE_AUTORA_NOMINATIVO` | `"o autor"` | `"a autora"` |
| `PARTE_AUTORA_OBJETO` | `"o Autor"` | `"a Autora"` |
| `PARTE_AUTORA_GENERO_CONSUMIDOR` | `"o consumidor"` | `"a consumidora"` |

**Slot de FLEXÃO ISOLADA** (apenas o artigo ou letra de flexão, agregado a outro substantivo):

| Slot | Autor masculino | Autora feminina |
|---|---|---|
| `PARTE_AUTORA_GENERO_MIN` | `"o"` | `"a"` |
| `PARTE_AUTORA_GENERO_O_A` | `"o"` | `"a"` |
| `GENERO_FLEXAO_O_A` | `"o"` | `"a"` |
| `GENERO_FLEXAO` | `""` (vazio) | `"a"` |
| `GENERO_FLEXAO_VAZIO_A` | `""` (vazio) | `"a"` |

**Slot de GENITIVO** (`do autor`/`da autora` — apesar do nome enganoso ter "DATIVO"):

> ⚠️ **Atenção: nomes enganosos.** Os slots a seguir começam com `_DATIVO` mas são GENITIVOS nos pilotos do vault. A tabela abaixo dá o preenchimento que efetivamente funciona em todos os contextos atuais (validado contra os pilotos `ausencia-defeito`, `compensacao-valores-tese-nova`, `litigancia-ma-fe-banco-rebate` etc.).

| Slot | Autor masculino | Autora feminina | Uso típico |
|---|---|---|---|
| `PARTE_AUTORA_DATIVO` | `"do autor"` | `"da autora"` | "descontado do benefício **do autor**" |
| `PARTE_AUTORA_DATIVO_AUTOR` | `"do autor"` | `"da autora"` | "padrão de vida **do autor**" |
| `PARTE_AUTORA_DATIVO_DEMANDANTE` | `"do demandante"` | `"da demandante"` | "sem autorização **do demandante**" |
| `PARTE_AUTORA_DATIVO_CONSUMIDOR` | `"ao consumidor"` | `"à consumidora"` | "transferir **ao consumidor** a responsabilidade" (este aqui é dativo de verdade) |

**Erro comum (já cometido em produção):** preencher `PARTE_AUTORA_GENERO` com apenas `"o"` ou `"a"`. Isso gera frases como:

- `"Em síntese, é o réu quem se apresenta com prova frágil [...] não o."` (faltou o substantivo)
- `"O é pessoa de poucos recursos financeiros."` (idem)
- `"O afirma que jamais contratou."` (idem)

**Régua imediata de revisão:** após gerar o DOCX, fazer Ctrl+F por `" o."`, `" a."`, `" o,"`, `" a,"` e verificar se há ocorrências em final de frase ou seguidas de pontuação. Se houver, slot foi mal preenchido.

**Configuração canônica para autor MASCULINO:**

```python
DADOS_CASO = {
    # SUJEITOS COMPLETOS
    "PARTE_AUTORA": "parte autora",
    "PARTE_AUTORA_GENERO": "o autor",
    "PARTE_AUTORA_NOMINATIVO": "o autor",
    "PARTE_AUTORA_OBJETO": "o autor",
    "PARTE_AUTORA_GENERO_CONSUMIDOR": "o consumidor",
    "PARTE_AUTORA_GENERO_CONSUMIDORA": "o consumidor",
    "AUTOR_GENERO": "o autor",
    "AUTOR_GENERO_CONSUMIDORA": "o consumidor",
    # FLEXÕES ISOLADAS (artigo / sufixo)
    "PARTE_AUTORA_GENERO_MIN": "o",
    "PARTE_AUTORA_GENERO_O_A": "o",
    "GENERO_FLEXAO_O_A": "o",
    "GENERO_FLEXAO": "",            # vazio: "vencedor" sem 'a'
    "GENERO_FLEXAO_VAZIO_A": "",    # idem
    # GENITIVOS (apesar do nome conter "DATIVO")
    "PARTE_AUTORA_DATIVO": "do autor",
    "PARTE_AUTORA_DATIVO_AUTOR": "do autor",
    "PARTE_AUTORA_DATIVO_DEMANDANTE": "do demandante",
    "PARTE_AUTORA_AUTORIZACAO": "do autor",
    # DATIVOS DE VERDADE
    "PARTE_AUTORA_DATIVO_CONSUMIDOR": "ao consumidor",
}
```

**Configuração canônica para autora FEMININA:** trocar todos os "o autor" por "a autora", "ao" por "à", e "" por "a" nas flexões.

A documentação completa dos slots vive em `regras-de-adaptacao.md` no vault, seção "Slots universais → Gênero da parte autora".

### Regra 15 — TODAS as strings literais que vão para o DOCX devem ter acentuação plena em português

**Erro recorrente já cometido em produção** (Teste 7, 8 e 10): ao escrever os textos literais nos scripts de redação (cabeçalho, síntese processual, blocos custom, requerimentos finais, parágrafos de bridge entre pilotos), tendi a digitar SEM acento por reflexo de digitação no terminal — gerando frases como `"ja qualificada nos autos da acao em epigrafe"`, `"a regular tramitacao do feito"`, `"em razoes que nao se sustentam"`. Isso quebra a leitura técnica da peça e fica visualmente inaceitável no protocolo.

**Regra obrigatória:**

1. **Toda string literal Python que será inserida no DOCX deve usar acentuação plena**, incluindo:
   - cabeçalhos (`EXCELENTÍSSIMO`, não `EXCELENTISSIMO`)
   - apresentação (`já qualificada nos autos da ação em epígrafe`)
   - síntese processual em bullets
   - blocos custom de mérito e preliminares
   - tabelas (cabeçalho e células)
   - requerimentos finais (`a regular tramitação`, `a determinação da inversão do ônus`)
   - texto de signatária (`Termos em que pede deferimento`)
   - texto dos campos do JSON `_pericia.json` (especialmente `texto_achado`, `texto_calibrado_etico`, `texto`, `observacao_padrao`, `observacao`, `mapeamento_observacao`)

2. **Strings que NÃO devem ter acento (paths e identificadores):**
   - paths de pilotos no vault: `preliminares/ausencia-interesse-agir-com-AR`, `merito-probatorio-digital/inconsistencias-trilha-auditoria`
   - paths de imports/diretórios: `replica-nao-contratado`, `ReplicasNaoContratado`
   - código Python: nomes de variáveis, funções, métodos
   - chaves de dict no `DADOS_CASO`: `PARTE_AUTORA_GENERO`, `BANCO_NOME`, etc.
   - valores de campos de path no JSON: `piloto_acionado`, `evidencia_pdf`, `input_pdf`

3. **Régua imediata de revisão pré-protocolo:** rodar Ctrl+F no DOCX final por:
   - `"ja "` (com espaço — deve ser `"já "`)
   - `"acao "` / `"contestacao"` / `"contratacao"` / `"manifestacao"` (devem ser `ação`/`contestação`/`contratação`/`manifestação`)
   - `"onus"` (deve ser `ônus`)
   - `"sera "` (deve ser `será`)
   - `"sao "` (deve ser `são`)
   - `"ate "` (deve ser `até`)
   - `"razoes"` (deve ser `razões`)
   - `"epigrafe"` (deve ser `epígrafe`)

4. **Ferramenta automatizada:** o repositório `~/OneDrive/Área de Trabalho/CLAUDE/replicas-nao-contratado/` traz dois utilitários:
   - `_acentuar.py <arquivo.py> [...]` — aplica acentuação em strings Python (incluindo f-strings, que em Python 3.12+ são tokenizadas como `FSTRING_MIDDLE`)
   - `_acentuar_json.py <arquivo.json> [...]` — aplica acentuação em valores de strings de JSON, preservando paths e identificadores via lista `CHAVES_LITERAIS`
   - Sempre rodar antes de gerar o DOCX final.

5. **Se for usar `_acentuar.py` em script novo:** rodar SEMPRE seguido de `_desacentuar_paths.py` (que reverte acentuação indevida em paths de pilotos e nome da skill).

**Caso paradigma:** Réplicas dos Testes 7, 8 (C6 e BB) e 10 saíram com 30+ palavras sem acento na primeira geração; após aplicar `_acentuar.py` + `_desacentuar_paths.py` + `_acentuar_json.py`, validação detectou 0 palavras sem acento em todas as quatro peças.

### Regra 16 — Estrutura sem III.X integrado: títulos individuais por achado pericial

**Decisão de revisão da equipe (Teste 8, 2026-05-05):** a versão protocolada NÃO usa a seção III.X agrupada (com placeholders manuais III.X.1/2/3 para moldura geral, régua biométrica, régua ITI; e III.X.4 com tabela compacta de achados por contrato). Em vez disso, **cada achado pericial vira um título individual de mérito** na ordem narrativa.

**Estrutura adotada pela equipe (cenário com contrato digital — C6, Teste 8):**

```
III - MÉRITO
├── Da irregularidade da contratação            (abertura sintética)
├── Da "selfie" / prova de vida                  (achado H — separado)
├── Da Assinatura inválida ITI                   (achado B)
├── Da Selfie liveness                           (achado H — versão técnica das normas)
├── Do código hash                               (achado C)
├── Da Trilha de auditoria incompatível com comportamento humano real  (achado G)
├── Do modus operandi da fraude digital mediante "KIT FRAUDE"          (cadeia)
├── Da demora no ajuizamento da ação             (rebate supressio)
├── Do depósito como elemento de fraude e não como prova de contratação (compensação)
├── Do Dano material                             (bloco curto novo)
├── Da ausência de defeito na prestação do serviço (rebate)
├── Devolução em dobro
└── Do cabimento da inversão do ônus da prova    (NO FIM, não no início)
```

**Estrutura adotada pela equipe (cenário sem contrato digital ou portabilidade — BB, Teste 8):**

```
III - MÉRITO
├── Da irregularidade da contratação por autoatendimento  (genérico, não por contrato)
├── Da alegação de culpa exclusiva da vítima              (rebate)
├── Da compensação                                         (versão curta)
├── Da cadeia de refinanciamento e da fraude autônoma nas renovações  (cadeia detalhada)
├── Do Dano material                                      (bloco curto)
├── Da ausência de defeito na prestação do serviço       (rebate)
├── Devolução em dobro
└── Do cabimento da inversão do ônus da prova            (NO FIM)
```

**O que NÃO usar:**

- ❌ NÃO inserir `add_placeholder_manual` para "PILOTO FIXO — Lei 14.063/2020" / "11 requisitos NT INSS" / "Validador ITI" como blocos externos. As regras técnicas vão DENTRO de cada tese individual.
- ❌ NÃO inserir tabela compacta de achados por contrato (III.X.4 com 3 colunas Cód./Achado/Risco). A equipe trata cada achado como tese narrativa.
- ❌ NÃO inserir tabela de identificação de contratos digitais (III.X abertura). A enumeração dos contratos vai na "Síntese processual" ou na "Irregularidade da contratação" abertura.

**O que MANTER:**

- ✅ A injeção via `helpers.injetar_pericia_digital()` ainda é OPCIONAL — útil quando o caso tem MUITOS contratos digitais (5+) ou quando o juízo prefere apresentação esquemática. Para casos comuns (1-3 contratos), preferir a estrutura da equipe (títulos individuais).
- ✅ O `_pericia.json` continua sendo a fonte da verdade dos achados — a função `injetar_pericia_digital` é uma das formas de materializá-lo, não a única.

### Regra 17 — Ordem do mérito: inversão do ônus vai NO FIM, não no início

**Erro recorrente já cometido em produção** (Testes 7, 8 e 10): inversão do ônus da prova era inserida logo após a abertura do mérito (depois da insuficiência probatória), pretendendo "preparar o terreno" para os achados subsequentes. **A equipe coloca esse bloco como ÚLTIMA tese do mérito**, antes dos requerimentos finais.

**Razão pedagógica:** quando a inversão vem no início, o juízo lê argumento processual antes de conhecer os fatos. Quando vem no fim, o juízo já assimilou todas as inconsistências da contestação e a inversão soa como conclusão natural ("dado tudo isto, é caso de inverter").

**Ordem canônica do mérito (a partir do Teste 8):**

1. Irregularidade da contratação (abertura)
2. Achados periciais individuais (selfie, ITI, hash, trilha, kit fraude...)
3. Cadeia de refinanciamento / portabilidade
4. Demora no ajuizamento (rebate supressio) ou Boa-fé objetiva
5. Compensação / Depósito como fraude
6. Dano material (bloco curto)
7. Ausência de defeito na prestação do serviço (rebate)
8. Devolução em dobro
9. **Inversão do ônus da prova** ← FECHAMENTO

### Regra 18 — Bloco "Fraude em empréstimos consignados do INSS" como PRIMEIRA preliminar (não placeholder externo)

**Erro corrigido pela equipe (Teste 8):** o bloco padrão sobre fraude sistêmica do INSS (com tabela Metrópoles "R$ 466 bilhões" e investigações PF/CGU) era inserido como `add_placeholder_manual` externo, antes da síntese processual. A equipe trata como **primeira tese formal das preliminares**, com título "Fraude em empréstimos consignados do INSS com instituições financeiras".

**Implementação correta:**

- Inserir como **subtítulo intermediário** no início das PRELIMINARES.
- Texto do bloco vem do banco interno do escritório (com a tabela visual da reportagem Metrópoles e investigações da PF/CGU) — a skill insere placeholder amarelo para o usuário colar manualmente OU pode ter o piloto canônico no vault (`preliminares/fraude-sistemica-inss-bloco-padrao` — TODO).
- Não confundir com placeholder externo de "Bloco padrão de fraude sistêmica" — nesta posição, ele é tese formal numerada.

### Regra 19 — Cenários BB / portabilidade: NÃO fazer mérito separado por contrato

**Padrão da equipe (Teste 8 BB):** quando há vários contratos por portabilidade (5+ contratos no caso da Maria de Lourdes), o mérito NÃO se divide em sub-blocos por contrato. Trata-se a totalidade dos contratos em DOIS títulos:

1. **"Da irregularidade da contratação por autoatendimento"** — fala de TODOS os contratos juntos, focando em (i) ausência de trilha digital, (ii) incompatibilidade lógica em casos pontuais (parcelas que aumentam em portabilidade), (iii) prova unilateral.

2. **"Da cadeia de refinanciamento e da fraude autônoma nas renovações"** — explica a dinâmica da cadeia, cita IN INSS 28/2008 (autorização expressa por operação), demonstra que cada renovação é negócio jurídico autônomo.

**O que NÃO fazer:**

- ❌ NÃO criar uma seção III.X.4 com sub-bloco para cada um dos 5 contratos.
- ❌ NÃO repetir os mesmos argumentos genéricos para cada contrato — fica redundante.
- ❌ NÃO tentar "mapear HISCON × interno do banco" como pedido específico — a equipe não usa.

**O que fazer:**

- ✅ Citar incompatibilidades lógicas pontuais dentro do bloco "Da irregularidade" (ex.: 37 → 42 parcelas é impossível em portabilidade pura).
- ✅ Tratar a cadeia como tese autônoma e densa (com IN INSS, art. 169 CC sobre nulidade que não convalesce, etc.).

**Pilotos novos do vault para esses cenários (criados em 2026-05-05):**

- `preliminares/ilegitimidade-passiva-banco-cessionario-cedente` — rebate ilegitimidade passiva genérica
- `preliminares/perda-objeto-portabilidade-refinanciamento` — rebate perda do objeto via refinanciamento/portabilidade (versão expandida)
- `preliminares/inepcia-procuracao-comprovante-residencia` — versão fundida de validade-procuração + comprovante-residência
- `merito-argumentativo/demora-ajuizamento-supressio` — versão alternativa enxuta do `boa-fe-objetiva`
- `danos-fechamento/dano-material-autonomo` — bloco curto autônomo

## Configuração

| Variável | Default | Para quê |
|---|---|---|
| `OBSIDIAN_VAULT` | `~/Documentos/Obsidian Vault/` | Raiz do vault com `Modelos/ReplicasNaoContratado/` |

## Arquivos de referência no vault (consultar, não duplicar aqui)

1. `Modelos/ReplicasNaoContratado/_MOC.md` — mapa principal, árvore de decisão
2. `Modelos/ReplicasNaoContratado/estrutura-padrao.md` — sequência de blocos por cenário
3. `Modelos/ReplicasNaoContratado/regras-de-adaptacao.md` — slots universais e variantes
4. `Modelos/ReplicasNaoContratado/erros-herdados.md` — armadilhas frequentes
5. `Modelos/ReplicasNaoContratado/checklist-protocolo.md` — conferência pré-protocolo
6. `Modelos/ReplicasNaoContratado/teses-modulares/<categoria>/<piloto>.md` — pilotos modulares (60+)

## Modelos de referência (réplicas validadas pela equipe)

Em `~/OneDrive/Área de Trabalho/Correção/7 - Laudos/`:

- `1. Teste 1` — Jorge Bispo × PAN — caso digital + impossibilidade temporal CCB×HISCON + inconsistências cadastrais (estado civil, endereço, e-mail vazio) + originador distante
- `2. Teste 2` — Sebastiana × Itaú — analfabeta com RG "impossibilidade de assinar"; 11 contratos (2 cursiva fraudulenta + 8 a rogo + 1 ausente); pedidos individualizados por tipo
- `3. Teste 3` — Edinete × Mercantil — TED para conta de terceiro confirmado por HISCRE; divergência interna na contestação; cessão de crédito não notificada
- `4. Teste 4` — Domingos × Safra — múltiplos contratos digitais com hash idêntico; reutilização de selfie; trilha 100% Incompleto; SMS para SP; e-mail safra@safra.com.br como identificação

Cada pasta tem o arquivo `Réplica <Nome>.docx` ou `.pdf` com a versão revisada pela equipe + meu script `_redigir-replica-*.py` em `~/OneDrive/Área de Trabalho/CLAUDE/replicas-nao-contratado/`. Estudar antes de gerar nova réplica.

## Entrega ao usuário — formato fixo

```
Réplica gerada.

Arquivo: <PATH_DOCX>

Pilotos usados: <N>
Teses sem piloto: <LISTA> ([TESE A SER DESENVOLVIDA] no DOCX)
Verificações automáticas executadas:
  - HISCRE × TED: <RESULTADO>
  - CCB × HISCON: <RESULTADO>
  - Hash idêntico entre digitais: <RESULTADO>
  - Reutilização de selfie: <RESULTADO>
  - Anotação RG impossibilidade: <RESULTADO>
  - Tipo de assinatura por contrato: <RESULTADO>
  - Divergência interna contestação: <RESULTADO>
  - Cessão de crédito não notificada: <RESULTADO>
  - (demais conforme aplicável)
Placeholders pendentes (preencher manualmente):
  - Bloco padrão de fraude sistêmica INSS (com tabela Metrópoles)
  - Lei 14.063/2020 (3 tipos)
  - Selfie liveness (11 requisitos)
  - Validador ITI (assinatura inválida)
  - Modus operandi kit fraude
  - Análise grafotécnica de cada contrato físico
Provas a anexar: <LISTA CURTA — prints ITI, Localizeip, HISCRE específico>
Alertas: <LISTA CURTA OU "nenhum">
```

## O que esta skill NÃO faz

1. Não redige inicial, apelação ou cumprimento
2. Não negocia acordo (skill `analise-proposta-acordo` faz isso)
3. Não trata RMC/RCC com vício de consentimento
4. Não fatia PDF (chamar skill `fatiar-processo` se precisar)
5. Não faz perícia técnica conclusiva (skill `pericia-contrato-digital` faz)
6. **Não insere blocos padrão manuais** (fraude INSS, Lei 14.063, selfie liveness, ITI, kit fraude) — apenas marca posição
7. **Não corta pilotos** por decisão editorial (humano decide no Word)
8. **Não rebate contestação do INSS** (peça autônoma)

## Retomada em nova sessão

A skill é stateless — pode ser invocada de novo na mesma pasta sem problema. Se já existe um DOCX gerado anteriormente, sobrescreve.
