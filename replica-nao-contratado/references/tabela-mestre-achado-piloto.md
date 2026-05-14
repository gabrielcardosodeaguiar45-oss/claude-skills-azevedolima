# Tabela Mestre — Achado Pericial → Piloto da Réplica

**Propósito.** Mapear cada verificação técnica da skill `pericia-contrato-digital` (códigos A–L) ao piloto correspondente do vault `Modelos/ReplicasNaoContratado/teses-modulares/`. É o documento que amarra o pipeline de perícia ao DOCX da réplica: para cada achado detectado pela perícia, indica qual piloto deve ser inserido na seção `III.X.4 — Inconsistências individuais por contrato` da estrutura padrão.

**Como ler.** Para cada verificação, traz: (1) o que a perícia detecta; (2) variantes do achado (quando há subdivisão, ex.: H.1/H.2/H.3); (3) o piloto canônico do vault; (4) os slots `{{...}}` que precisam ser preenchidos com dados do caso; (5) critério de não-aplicação (quando o achado fica fora da réplica).

**Princípio central.** Um achado só vira parágrafo da réplica se o banco juntou documentação que permita verificá-lo. Sem documento, sem achado — sem achado, o piloto correspondente não entra. Isso evita inflar a peça com argumentos abstratos.

---

## A — E-mail cadastrado

**O que a perícia detecta.** Se o campo "E-mail" da CCB ou da trilha de auditoria está vazio, preenchido com placeholder (`nnnn@gmail.com`, `email@email.com`, `xxx@xxx.com`), ou compatível com identidade do banco (ex.: `safra@safra.com.br`).

| Variante | Achado pericial | Piloto do vault | Slots a preencher |
|---|---|---|---|
| A.1 — campo vazio | "Campo e-mail vazio na CCB do contrato `<num>`, em contratação supostamente digital" | `merito-probatorio-digital/inconsistencias-dados-cadastrais` | `{{N_CONTRATOS}}`, tabela CCB×Email, descrição do padrão |
| A.2 — placeholder genérico | "Campo e-mail preenchido com `<placeholder>`, sequência sem correspondência com endereço real" | `merito-probatorio-digital/inconsistencias-dados-cadastrais` (variação Camada 3 "e-mail fantasma") | idem + `{{DESCRICAO_PADRAO_EMAIL}}` |
| A.3 — e-mail do próprio banco | "Identificação eletrônica por e-mail do próprio banco (ex.: `safra@safra.com.br`), não por e-mail pessoal do consumidor" | `merito-probatorio-digital/inconsistencias-dados-cadastrais` (parágrafo específico) | descrição do e-mail e seu domínio |

**Não entra se:** banco não juntou CCB ou trilha; ou e-mail é real e compatível com perfil do consumidor.

---

## B — Validador ITI

**O que a perícia detecta.** Resultado da consulta a `validar.iti.gov.br` para o PDF do contrato. Pode ser INVÁLIDO (sem certificação ICP-Brasil, sem assinatura digital reconhecida) ou VÁLIDO (raro). Verificação tipicamente manual (print externo).

| Variante | Achado pericial | Piloto do vault | Slots |
|---|---|---|---|
| B.1 — assinatura inválida no ITI | "Assinatura digital do contrato `<num>` retornou INVÁLIDA no validador oficial do ITI — sem integridade criptográfica" | `merito-probatorio-digital/assinatura-invalida-validador-iti` | `{{NUMERO_CONTRATO}}`, `{{DATA_VALIDACAO}}`, print do validador |
| B.2 — não verificável | "Documento não passou pelo validador ITI por ausência de assinatura digital reconhecida" | `merito-probatorio-digital/assinatura-invalida-validador-iti` (variação Camada 3 "sem ICP-Brasil") | `{{NUMERO_CONTRATO}}` |

**Não entra se:** banco juntou contrato físico (a rogo) e não alegou assinatura digital; OU validador retornou VÁLIDA (caso raríssimo, não impugnar nesse ângulo).

**Pré-requisito visual.** Print do validador ITI a anexar como prova documental (placeholder amarelo `[INSERIR — Imagem: print do validador ITI]`).

---

## C — Hash SHA do PDF

**O que a perícia detecta.** Compara o hash impresso na CCB ou na trilha (quando há) com o hash calculado do arquivo (`sha256sum`).

| Variante | Achado pericial | Piloto do vault | Slots |
|---|---|---|---|
| C.1 — hash divergente | "Hash impresso na CCB (`<esperado>`) diverge do calculado (`<calculado>`) — documento adulterado, efeito avalanche (REsp 2.159.442/PR)" | `merito-probatorio-digital/codigo-hash` | `{{HASH_ESPERADO}}`, `{{HASH_CALCULADO}}`, `{{NUMERO_CONTRATO}}` |
| C.2 — hash ausente | "CCB do contrato `<num>` desprovida de código hash — impossível verificar integridade" | `merito-probatorio-digital/ausencia-codigo-hash` | `{{NUMERO_CONTRATO}}` |
| C.3 — hash idêntico entre contratos digitais | "Hashes SHA-256 idênticos detectados entre contratos `<X>` e `<Y>` (componente `<envelope/CCB/CET/...>`) — mesmo PDF reutilizado" | `merito-probatorio-digital/kit-fraude` (caso múltiplo) + tabela inventário hashes em `helpers.add_tabela_hashes` | inventário SHA-256 dos 6 componentes |

**Não entra se:** banco não juntou PDF do contrato (ou só prints); OU contrato é físico (a rogo).

---

## D — Metadados do PDF

**O que a perícia detecta.** Inspeção via `pdfinfo`: data de criação, data de modificação, software gerador. Detecta criação posterior à data alegada de contratação ou software incompatível (Aspose.PDF, PDFium com data pós-fato).

| Variante | Achado pericial | Piloto do vault | Slots |
|---|---|---|---|
| D.1 — criação posterior | "Metadados revelam criação do arquivo em `<data_criacao>`, posterior à data alegada de contratação `<data_contrato>` — indício de adulteração" | `merito-probatorio-digital/analise-metadados` | `{{DATA_CRIACAO}}`, `{{DATA_CONTRATO}}`, `{{SOFTWARE}}` |
| D.2 — software automatizado | "Documento gerado por `<software>` (Aspose.PDF / PDFium / outro), incompatível com fluxo de assinatura digital legítima" | `merito-probatorio-digital/analise-metadados` (variação Camada 3 "software impróprio") | `{{SOFTWARE}}`, `{{NUMERO_CONTRATO}}` |
| D.3 — modificação posterior à assinatura | "Documento foi modificado em `<data_mod>`, após a suposta assinatura em `<data_sig>` — quebra da integridade pós-assinatura" | `merito-probatorio-digital/analise-metadados` | `{{DATA_MODIFICACAO}}`, `{{DATA_ASSINATURA}}` |

**Não entra se:** PDF nativo digital sem metadados extraíveis; OU metadados consistentes com data alegada e software regular.

---

## E — Endereço IP

**O que a perícia detecta.** Classifica o IP registrado na trilha. Privado (RFC 1918: 10.x.x.x, 172.16-31.x.x, 192.168.x.x) ou Público. Se público, geolocaliza e compara com residência/correspondente.

| Variante | Achado pericial | Piloto do vault | Slots |
|---|---|---|---|
| E.1 — IP privado RFC 1918 | "IP `<endereco>` pertence a faixa privada RFC 1918 — acesso originado em rede corporativa interna, não doméstica" | `merito-probatorio-digital/ip-desconhecido` | `{{IP}}`, `{{FAIXA_PRIVADA}}`, `{{NUMERO_CONTRATO}}` |
| E.2 — IP público distante da residência | "IP `<endereco>` geolocalizado em `<cidade>`, a `<X>` km da residência da autora — incompatível com acesso pelo titular" | `merito-probatorio-misto/ip-correspondente-bancario` | `{{IP}}`, `{{CIDADE_GEO}}`, `{{DISTANCIA_KM}}`, `{{ENDERECO_AUTORA}}` |
| E.3 — IP do correspondente bancário | "IP geolocalizado coincide com a sede do correspondente `<nome>` — acesso a partir do parceiro, não do consumidor" | `merito-probatorio-misto/ip-correspondente-bancario` | `{{IP}}`, `{{NOME_CORRESPONDENTE}}`, `{{CIDADE_CORRESP}}` |

**Não entra se:** trilha não traz IP.

---

## F — Geolocalização (lat/long)

**O que a perícia detecta.** Coordenadas registradas na trilha. Compara com endereço da autora e com sede do correspondente.

| Variante | Achado pericial | Piloto do vault | Slots |
|---|---|---|---|
| F.1 — coordenadas distantes do autor | "Coordenadas `<lat,lon>` apontam para `<local>`, a `<X>` km da residência da autora" | (entra junto com E na mesma seção) | idem E |
| F.2 — coordenadas na sede do correspondente | "Coordenadas coincidem com a sede do correspondente — acesso a partir do parceiro" | (entra junto com E + I) | idem E.3 |

**Não entra se:** trilha não traz lat/long.

**Convenção.** Quando E e F apontam para o mesmo lugar, fundir em um único parágrafo (não duplicar).

---

## G — Session ID e horário do aceite

**O que a perícia detecta.** ID de sessão registrado na trilha. Compara IDs entre contratos. Verifica horário de aceite (segundos).

| Variante | Achado pericial | Piloto do vault | Slots |
|---|---|---|---|
| G.1 — sessão compartilhada entre contratos | "Session ID `<id>` repetido nos contratos `<X>`, `<Y>`, `<Z>` — operação automatizada em lote, não interação humana real" | `merito-probatorio-digital/inconsistencias-trilha-auditoria` | `{{SESSAO_ID}}`, `{{LISTA_CONTRATOS}}` |
| G.2 — aceite ao segundo entre contratos | "Aceite registrado às `<hh:mm:ss>` em múltiplos contratos com diferença ≤ 60s — humanamente impossível" | `merito-probatorio-digital/trilha-incompativel-comportamento-humano` | `{{HORARIOS_ACEITE}}`, `{{LISTA_CONTRATOS}}` |
| G.3 — trilha 100% "Incompleto" / etapas ausentes | "Trilha de auditoria com status 'Incompleto' em todos os passos, incluindo a etapa final 'Proposta Paga'" | `merito-probatorio-digital/inconsistencias-trilha-auditoria` (Camada 3 "trilha incompleta") | descrição da trilha do caso |

**Não entra se:** banco não juntou trilha; OU sessão única e horário compatível com fluxo humano.

---

## H — Selfie / liveness

**O que a perícia detecta.** Selfie presente, ausente, reutilizada (visualmente comparável entre contratos), com ou sem liveness adequado conforme 11 requisitos da NT INSS.

| Variante | Achado pericial | Piloto do vault | Slots |
|---|---|---|---|
| H.1 — selfie ausente | "Contrato `<num>` desprovido de captura biométrica — impossível atestar autoria do ato" | `merito-probatorio-digital/selfie-liveness` (variação Camada 3 "ausência total") | `{{NUMERO_CONTRATO}}` |
| H.2 — selfie reutilizada entre contratos | "Mesma imagem facial detectada nos contratos `<X>`, `<Y>` — mesma roupa, mesmo fundo, mesma posição: imagem estática reutilizada, não captura ao vivo (violação ISO 30107-3 / IEEE 2790-2020)" | `merito-probatorio-digital/selfie-liveness` (variação Camada 3 "reutilização") + `merito-probatorio-digital/kit-fraude` (se ≥3 padrões na matriz) | `{{LISTA_CONTRATOS}}`, descrição visual da reutilização |
| H.3 — selfie sem liveness adequado | "Imagem capturada não atende requisitos técnicos de liveness conforme NT INSS / IEEE 2790-2020 (sem prova de vida demonstrável)" | `merito-probatorio-digital/selfie-liveness` (Camada 1 — 11 requisitos) | descrição do que falta |
| H.4 — RG impossibilidade de assinar × selfie | "RG do autor consigna 'IMPOSSIBILIDADE DE ASSINAR', porém banco apresenta selfie como prova de assinatura — inconciliável" | `merito-probatorio-digital/selfie-liveness` + `merito-probatorio-misto/contratacao-digital-parte-analfabeta` | data do RG, descrição da anotação |

**Não entra se:** banco não invocou selfie como prova; OU selfie regular, com liveness adequado, sem reutilização.

**Pré-requisito visual.** Comparação visual de selfies entre contratos exige leitura visual nativa de Claude (não automatizável).

---

## I — Correspondente bancário / originador

**O que a perícia detecta.** Razão social, CNPJ, cidade do correspondente que originou a operação. Compara com endereço da autora (distância km) e com cidade da geolocalização do aceite.

| Variante | Achado pericial | Piloto do vault | Slots |
|---|---|---|---|
| I.1 — correspondente em cidade distante | "Correspondente `<nome>` situado em `<cidade>`, a `<X>` km da residência da autora — inverossímil deslocamento ou contato remoto" | `merito-probatorio-misto/dados-correspondente-originador` | `{{NOME_CORRESPONDENTE}}`, `{{CNPJ}}`, `{{CIDADE}}`, `{{DISTANCIA_KM}}` |
| I.2 — caso AM (Maués/Manaus) | "Correspondente em Manaus/AM, autora residente em Maués/AM — inverossímil contato presencial" | `merito-probatorio-misto/correspondente-maues-manaus` | dados do caso |
| I.3 — múltiplos contratos no mesmo dia mesmo correspondente | "Correspondente `<nome>` originou os contratos `<X>`, `<Y>`, `<Z>` no mesmo dia — operação em lote" | `merito-probatorio-misto/dados-correspondente-originador` (Camada 3 "lote no mesmo dia") | datas, lista de contratos |
| I.4 — correspondente comum entre bancos diferentes | "Mesmo correspondente `<nome>` originou contratos em bancos distintos `<A>` e `<B>` — consórcio de fraude" | `merito-probatorio-digital/kit-fraude` (achado central) + `dados-correspondente-originador` | matriz cruzada banco × correspondente |

**Não entra se:** CCB não traz campo "Correspondente/Originador"; OU correspondente está na cidade da autora.

**Distância mínima relevante.** Acima de 50 km já vale; acima de 200 km é forte; acima de 500 km é devastador.

---

## J — Telefone

**O que a perícia detecta.** Número cadastrado na CCB e/ou trilha. Compara DDD com UF de residência da autora. Compara entre contratos da mesma autora.

| Variante | Achado pericial | Piloto do vault | Slots |
|---|---|---|---|
| J.1 — DDD divergente da UF | "Telefone `<numero>` (DDD `<X>`) cadastrado para autora residente em `<UF>` (DDD esperado `<Y>`) — incompatibilidade geográfica" | `merito-probatorio-digital/inconsistencias-dados-cadastrais` (Camada 3 "DDD divergente") | `{{TELEFONE}}`, `{{DDD_REGISTRADO}}`, `{{DDD_ESPERADO}}`, `{{UF_RESIDENCIA}}` |
| J.2 — telefones distintos entre contratos da mesma autora | "Telefones divergentes entre contratos: `<tel1>` (CCB X) versus `<tel2>` (CCB Y) — dados inseridos por terceiros distintos" | `merito-probatorio-digital/inconsistencias-dados-cadastrais` (Camada 3 "telefones múltiplos") | tabela telefone × contrato |
| J.3 — SMS de formalização para telefone com DDD diferente | "SMS de formalização enviado para telefone DDD `<X>`, autora residente em UF cujo DDD é `<Y>`" | `merito-probatorio-digital/inconsistencias-trilha-auditoria` | dados da trilha |

**Não entra se:** banco não juntou telefone; OU telefone real e compatível.

---

## K — Contrato citado mas não juntado

**O que a perícia detecta.** Compara contratos citados na contestação ou na inicial × contratos efetivamente juntados pelo banco como CCB.

| Variante | Achado pericial | Piloto do vault | Slots |
|---|---|---|---|
| K.1 — contrato impugnado não juntado pelo banco | "Contrato `<num>` impugnado na inicial não foi juntado pelo banco em sua contestação — presunção art. 400, par. único, CPC" | `processuais-especiais/ausencia-total-contrato-master` | `{{NUMERO_CONTRATO_AUSENTE}}`, referência onde foi citado |
| K.2 — contestação cita contrato sem anexar | "Contestação menciona contrato `<num>` mas não junta a respectiva CCB — vício probatório agravado" | `processuais-especiais/ausencia-total-contrato-master` (variação Camada 3 "citado e não anexado") | idem |

**Não entra se:** todos os contratos impugnados foram juntados.

**Pedido associado.** Julgamento antecipado favorável à autora, art. 355 I + 400 CPC.

---

## L — Comprovante de TED / PIX (específico de empréstimo)

**O que a perícia detecta.** Recibo SPB (DEMTRANSF, COMPTRANS) com banco/agência/conta destino, valor, data. Compara com (i) valor da CCB; (ii) horário do aceite; (iii) banco do INSS no HISCRE da competência.

| Variante | Achado pericial | Piloto do vault | Slots |
|---|---|---|---|
| L.1 — valor TED divergente da CCB | "Valor do TED (R$ `<x>`) divergente do valor liberado na CCB (R$ `<y>`), sem justificativa de IOF/seguro" | `merito-argumentativo/compensacao-valores-tese-nova` (zona de adaptação "divergência interna") | `{{VALOR_TED}}`, `{{VALOR_CCB}}`, `{{DIFERENCA}}` |
| L.2 — horário TED incompatível com aceite | "TED realizado às `<hora>`, mas trilha registra aceite às `<hora>` — divergência temporal" | `merito-probatorio-digital/trilha-incompativel-comportamento-humano` | dados do TED e da trilha |
| L.3 — **TED depositado em conta diversa da que recebia o INSS (REGRA HISCRE — CALIBRADA)** | "TED destinado à conta `<banco_destino, ag/conta>`, **conta diversa daquela em que a autora recebia seu benefício previdenciário** (`<banco_inss>`, conforme HISCRE em todas as competências relevantes). A autora, ademais, **não percebeu o referido depósito** dentre os múltiplos lançamentos de seu extrato bancário. Aciona-se, na sequência, a tese da compensação: o depósito não é prova de contratação, mas elemento da própria fraude — em eventual procedência, autoriza-se a compensação dos valores efetivamente creditados para evitar enriquecimento ilícito." **PROIBIDO afirmar 'conta de terceiro', 'autora não recebeu os valores' ou pedir intimação da autora — risco de má-fé processual contra o cliente.** | `merito-argumentativo/compensacao-valores-tese-nova` (sempre acionada em conjunto) | `{{BANCO_DESTINO_TED}}`, `{{AG_CONTA_DESTINO}}`, `{{BANCO_INSS_HISCRE}}`, `{{COMPETENCIAS_VERIFICADAS}}`. **Pedido associado:** procedência + compensação dos valores efetivamente creditados (tese-nova já traz o pedido). |
| L.4 — comprovante TED ausente | "Banco alega liberação de crédito mas não junta comprovante SPB — ônus probatório não atendido" | `merito-probatorio-misto/insuficiencia-probatoria-prova-unilateral` (Modelo E "comprovante sem NSU/EndToEndID") | `{{NUMERO_CONTRATO}}` |
| L.5 — comprovante sem NSU/EndToEndID | "Comprovante apresentado não traz NSU ou EndToEndID — impossibilidade de rastreamento técnico da operação" | `merito-probatorio-misto/insuficiencia-probatoria-prova-unilateral` (Modelo E) | descrição do comprovante |

**Não entra se:** caso é RMC/RCC (sem TED) — usar verificações M–P (fora do escopo desta skill).

**Tese central conectada.** O TED **NÃO** é prova de contratação — é a materialização da fraude. Tabela do lucro do banco entra junto via `helpers.add_tabela_lucro` se há ≥1 TED comprovado.

---

## Pilotos transversais (acionados por padrão / conjunto, não por achado isolado)

Pilotos que **não** correspondem a uma verificação A–L específica, mas entram conforme cenário do caso. Vão em seções próprias (III.X.5, III.X.6, III.X.7) ou no mérito argumentativo geral, não dentro do sub-bloco por contrato.

| Piloto | Quando aciona | Onde entra na estrutura |
|---|---|---|
| `merito-probatorio-digital/kit-fraude` | ≥3 padrões sistêmicos na matriz cruzada (mesmo IP + mesma sessão + selfie reutilizada + correspondente comum + horário ao segundo) | III.X.5 (matriz cruzada) |
| `merito-probatorio-misto/insuficiencia-probatoria-prova-unilateral` | Sempre que o conjunto probatório do banco é só prints sistêmicos sem certificação externa | III.X.6 |
| `merito-probatorio-digital/robos-falsificar-assinatura` | Sempre que há contratação digital impugnada (tese-bloco doutrinária + Tema 1.061 STJ + IN INSS 162/2024) | III.X.7 (fechamento + pedido de perícia) |
| `merito-probatorio-digital/cadeia-custodia-digital-inexistente` | Quando a trilha vem em arquivo separado do contrato sem hash de vínculo | III.X.6 (combinada com insuficiência) |
| `merito-probatorio-misto/contratacao-digital-parte-analfabeta` | Autora analfabeta com contrato digital alegado | III.X.4 (preâmbulo do sub-bloco) ou III.X.6 |
| `merito-probatorio-misto/cadeia-refinanciamentos-fraude-autonoma` | Refinanciamentos sucessivos no mesmo banco (não é achado pericial isolado, é análise de cadeia) | seção de mérito argumentativo (não dentro de III.X) |
| `merito-probatorio-misto/alegacao-refin-quando-nao-e` | Banco alega refin mas HISCON mostra averbação nova | seção de mérito argumentativo |
| `merito-probatorio-misto/merito-bradesco-logs` | Específico Bradesco com prova baseada em logs internos | III.X.4 (preâmbulo) ou III.X.6 |
| `merito-argumentativo/responsabilidade-cessionario-portabilidade` | Banco alega ilegitimidade por portabilidade ou cessão de crédito | preliminares (não dentro de III.X) |

---

## Tabela mestre consolidada — visão única

| Cód. | Verificação | Variantes | Piloto canônico | Pilotos secundários |
|---|---|---|---|---|
| A | E-mail | A.1 vazio · A.2 placeholder · A.3 do banco | `inconsistencias-dados-cadastrais` | — |
| B | Validador ITI | B.1 inválida · B.2 não verificável | `assinatura-invalida-validador-iti` | — |
| C | Hash SHA | C.1 divergente · C.2 ausente · C.3 idêntico entre contratos | `codigo-hash` (C.1) · `ausencia-codigo-hash` (C.2) · **C.3 flexível por caso concreto: `kit-fraude` OU `cadeia-custodia-digital-inexistente`** conforme densidade de padrões | — |
| D | Metadados | D.1 criação posterior · D.2 software · D.3 modificação pós-assinatura | `analise-metadados` | — |
| E | IP | E.1 privado · E.2 público distante · E.3 sede do correspondente | `ip-desconhecido` (E.1) · `ip-correspondente-bancario` (E.2/E.3) | — |
| F | Geolocalização | F.1 distante · F.2 sede do correspondente | (combinar com E) | — |
| G | Sessão / aceite | G.1 sessão compartilhada · G.2 aceite ao segundo · G.3 trilha incompleta | `inconsistencias-trilha-auditoria` (G.1, G.3) · `trilha-incompativel-comportamento-humano` (G.2) | — |
| H | Selfie / liveness | H.1 ausente · H.2 reutilizada · H.3 sem liveness · H.4 RG impossib. de assinar | `selfie-liveness` | `kit-fraude` (H.2) · `contratacao-digital-parte-analfabeta` (H.4) |
| I | Correspondente | I.1 distante · I.2 AM · I.3 lote no mesmo dia · I.4 entre bancos | `dados-correspondente-originador` · `correspondente-maues-manaus` (caso AM) | `kit-fraude` (I.4) |
| J | Telefone | J.1 DDD divergente · J.2 telefones distintos · J.3 SMS DDD diverso | `inconsistencias-dados-cadastrais` (J.1, J.2) · `inconsistencias-trilha-auditoria` (J.3) | — |
| K | Contrato ausente | K.1 não juntado · K.2 citado sem anexar | `ausencia-total-contrato-master` | — |
| L | TED / PIX | L.1 valor divergente · L.2 horário · L.3 conta divergente HISCRE · L.4 ausente · L.5 sem NSU | `compensacao-valores-tese-nova` (L.1, L.3) · `trilha-incompativel-comportamento-humano` (L.2) · `insuficiencia-probatoria-prova-unilateral` (L.4, L.5) | — |

---

## Convenções de uso

1. **Achado sem documentação correspondente do banco → fora da réplica.** Princípio cirúrgico: não argumentar sobre algo que o banco nem pretende provar.
2. **Achado sem piloto canônico → registrar como `[TESE A SER DESENVOLVIDA]`** no DOCX em amarelo (Regra 2 da SKILL.md).
3. **Múltiplos achados em um único piloto** (ex.: A + J no `inconsistencias-dados-cadastrais`) → consolidar em um único parágrafo da réplica, com a tabela completa na zona de adaptação.
4. **Achados em variantes (H.1/H.2/H.3)** → pode haver mais de uma variante no mesmo caso; cada uma vira parágrafo distinto dentro do mesmo sub-bloco.
5. **Pilotos transversais (kit-fraude, robôs, insuficiência-probatória)** entram em III.X.5/6/7, não dentro do sub-bloco por contrato.
6. **Slots `{{...}}` do piloto** preenchidos com dados do `_pericia.json` automaticamente, com grifo amarelo (`<H>...</H>`) na injeção.

---

## Próximo arquivo da pipeline

`schema-pericia.md` — define o formato exato do JSON gerado pela perícia, com os campos que correspondem a cada variante desta tabela mestre. A injeção no DOCX consome esse JSON e usa esta tabela para escolher o piloto certo para cada achado.
