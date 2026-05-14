# Schema do `_pericia.json`

**Propósito.** Define o formato exato do JSON gerado pelo pipeline de perícia digital (`pipeline-pericia-digital.py`) e consumido pelos helpers de injeção no DOCX. É o contrato entre o que a perícia detecta e o que a réplica materializa.

**Localização do arquivo.** `_pericia/_pericia.json` ao lado do PDF do processo. Reutilizado em chamadas subsequentes (cache).

---

## Estrutura raiz

```json
{
  "meta": {
    "processo": "0006002-52.2026.4.05.8001",
    "autor": "MARIA DE LOURDES DANTAS DA SILVA",
    "cpf_autor": "029.873.624-12",
    "uf_autora": "AL",
    "data_pericia": "2026-05-05",
    "bancos_passivo": ["C6 CONSIGNADO", "BANCO DO BRASIL"],
    "perito": "skill replica-nao-contratado v2026-05",
    "input_pdf": "0006002-52.2026.4.05.8001.pdf"
  },
  "contratos_digitais": [
    { /* objeto contrato — schema na seção "Contrato individual" */ }
  ],
  "matriz_cruzada": { /* schema na seção "Matriz cruzada" */ },
  "padroes_sistemicos": [ /* lista de strings com padrões detectados */ ],
  "alertas": [ /* lista de strings com alertas para o usuário */ ]
}
```

---

## Contrato individual (cada item de `contratos_digitais`)

Estrutura completa de um contrato com todas as verificações A–L. Campos opcionais sinalizados com comentário; quando o achado não se aplica ou não foi detectado, usar `null` ou `"nao_aplicavel"`.

```json
{
  "numero": "901301 61082",
  "ade": "57130823",
  "banco": "C6 CONSIGNADO",
  "tipo": "DIGITAL",
  "data_alegada": "2023-12-19",
  "valor_liberado": 9195.86,
  "parcelas_qtd": 41,
  "parcelas_valor": 313.40,
  "status": "ATIVO_OU_BAIXADO",
  "evento_pdf": "Ev18.3 - mov. 18.3 - paginas 239-249",

  "achados": {
    "A_email": {
      "resultado": "vazio",
      "valor": null,
      "risco": "ALTO",
      "evidencia_pdf": "Evento 18.3 pag 2 da CCB",
      "piloto_acionado": "merito-probatorio-digital/inconsistencias-dados-cadastrais",
      "variante": "A.1",
      "texto_achado": "Campo e-mail vazio na CCB do contrato 901301 61082 — em contratacao supostamente digital, ausencia injustificavel"
    },
    "B_iti": {
      "resultado": "manual",
      "valor_validador": null,
      "risco": "manual",
      "evidencia_pdf": null,
      "piloto_acionado": "merito-probatorio-digital/assinatura-invalida-validador-iti",
      "variante": "B.1",
      "texto_achado": "Validador ITI requer print externo manual",
      "placeholder_visual": "[INSERIR — Imagem: print do validador ITI para o contrato 901301 61082]"
    },
    "C_hash": {
      "resultado": "ausente",
      "hash_calculado": "sha256:abc123...",
      "hash_esperado": null,
      "componentes": {
        "envelope": null,
        "ccb": null,
        "cet": null,
        "termo_inss": null,
        "cadastro": null,
        "evidencias": null
      },
      "compartilhado_com": [],
      "risco": "ALTO",
      "piloto_acionado": "merito-probatorio-digital/ausencia-codigo-hash",
      "variante": "C.2"
    },
    "D_metadados": {
      "resultado": "irregular",
      "data_criacao": "2024-01-15",
      "data_modificacao": null,
      "software": "Aspose.PDF for .NET 22.10",
      "data_alegada_contrato": "2023-12-19",
      "risco": "ALTO",
      "piloto_acionado": "merito-probatorio-digital/analise-metadados",
      "variante": "D.1"
    },
    "E_ip": {
      "resultado": "irregular",
      "valor": "10.1.1.1",
      "tipo": "privado_RFC1918",
      "geolocalizacao": null,
      "distancia_residencia_km": null,
      "compartilhado_com": ["901301 61362"],
      "risco": "ALTO",
      "piloto_acionado": "merito-probatorio-digital/ip-desconhecido",
      "variante": "E.1"
    },
    "F_geo": {
      "resultado": "compativel_residencia",
      "lat": -3.4,
      "lon": -57.7,
      "distancia_residencia_km": 0.5,
      "risco": "BAIXO",
      "piloto_acionado": null,
      "variante": null
    },
    "G_sessao": {
      "resultado": "irregular",
      "id": "sess_abc123",
      "compartilhada_com": ["901301 61362"],
      "horario_aceite": "2023-12-19T14:23:05",
      "horarios_proximos_outros": [{"contrato": "901301 61362", "horario": "2023-12-19T14:23:05", "diferenca_segundos": 0}],
      "risco": "ALTO",
      "piloto_acionado": "merito-probatorio-digital/inconsistencias-trilha-auditoria",
      "variante": "G.1"
    },
    "H_selfie": {
      "resultado": "reutilizada",
      "presente": true,
      "reutilizada_com": ["901301 61362"],
      "comparacao_visual": "Mesma roupa, mesmo fundo, mesma posicao da face entre os dois contratos",
      "liveness_adequado": null,
      "risco": "ALTO",
      "piloto_acionado": "merito-probatorio-digital/selfie-liveness",
      "variante": "H.2",
      "ativa_kit_fraude": true
    },
    "I_correspondente": {
      "resultado": "irregular",
      "nome": "FONTES PROMOTORA",
      "cnpj": "11.643.037/0001-54",
      "cidade": "Florianopolis/SC",
      "distancia_km": 3500,
      "uf_autora": "AL",
      "compartilhado_com_contratos": ["901301 61362"],
      "compartilhado_entre_bancos": false,
      "risco": "ALTO",
      "piloto_acionado": "merito-probatorio-misto/dados-correspondente-originador",
      "variante": "I.1"
    },
    "J_telefone": {
      "resultado": "compativel",
      "numero": "(82) 99999-9999",
      "ddd_registrado": "82",
      "ddd_esperado": "82",
      "telefones_distintos_outros_contratos": [],
      "risco": "BAIXO",
      "piloto_acionado": null,
      "variante": null
    },
    "K_ausencia": {
      "resultado": "juntado",
      "contrato_juntado": true,
      "evidencia_pdf": "Evento 18.3",
      "risco": "BAIXO",
      "piloto_acionado": null,
      "variante": null
    },
    "L_ted": {
      "resultado": "irregular",
      "valor_ted": 4307.15,
      "valor_ccb": 4307.15,
      "diferenca": 0.00,
      "data_ted": "2023-12-19",
      "horario_ted": "14:30:00",
      "horario_aceite": "2023-12-19T14:23:05",
      "banco_destino": "Banco 237 - BRADESCO",
      "agencia_destino": "3169",
      "conta_destino": "1015906-7",
      "banco_inss_hiscre": "Banco 1 - BRASIL",
      "competencias_verificadas_hiscre": ["10/2023", "11/2023", "12/2023"],
      "destino_coincide_com_inss": false,
      "comprovante_presente": true,
      "nsu_endtoendid_presente": false,
      "risco": "ALTO",
      "piloto_acionado": "merito-argumentativo/compensacao-valores-tese-nova",
      "variante": "L.3",
      "texto_calibrado_etico": "TED destinado a conta diversa daquela em que a autora recebia INSS na epoca; aciona tese da compensacao; PROIBIDO afirmar conta de terceiro ou pedir intimacao da autora"
    }
  },

  "achados_aplicaveis_count": 8,
  "achados_alto_risco_count": 7,
  "classificacao_individual": "ALTO_RISCO"
}
```

### Convenções de campos

- `resultado`: `"regular"` (sem inconsistência), `"irregular"` (achado positivo), `"vazio"`, `"ausente"`, `"reutilizada"`, `"manual"` (precisa intervenção humana), `"nao_aplicavel"` (verificação não cabe), `"compativel"` (passou).
- `risco`: `"ALTO"`, `"MEDIO"`, `"BAIXO"`, `"manual"`, `"nao_verificavel"`.
- `piloto_acionado`: caminho relativo do piloto no vault. `null` se não aciona.
- `variante`: código `A.1`, `H.2`, `L.3` etc., conforme `tabela-mestre-achado-piloto.md`. `null` se não há variante específica.
- `texto_achado`: frase pronta que entra no DOCX como descrição do achado (curta, factual). O piloto traz a fundamentação doutrinária; este campo traz só o dado do caso.
- `evidencia_pdf`: localização do achado nos autos (referência: "Evento X pag Y" ou "fls. Z").
- `compartilhado_com` / `compartilhada_com` / `reutilizada_com`: lista de números de OUTROS contratos com o mesmo valor — usado pela matriz cruzada.

---

## Matriz cruzada (`matriz_cruzada`)

Estrutura que consolida padrões entre 2+ contratos digitais. Vazio se houver apenas 1 contrato.

```json
{
  "tabela_comparativa": [
    {
      "campo": "ip",
      "linhas": [
        {"contrato": "901301 61082", "valor": "10.1.1.1"},
        {"contrato": "901301 61362", "valor": "10.1.1.1"}
      ],
      "padrao_detectado": true
    },
    {
      "campo": "sessao",
      "linhas": [
        {"contrato": "901301 61082", "valor": "sess_abc123"},
        {"contrato": "901301 61362", "valor": "sess_abc123"}
      ],
      "padrao_detectado": true
    },
    {
      "campo": "selfie_hash",
      "linhas": [
        {"contrato": "901301 61082", "valor": "selfie_001"},
        {"contrato": "901301 61362", "valor": "selfie_001"}
      ],
      "padrao_detectado": true
    },
    {
      "campo": "correspondente",
      "linhas": [
        {"contrato": "901301 61082", "valor": "FONTES PROMOTORA"},
        {"contrato": "901301 61362", "valor": "FONTES PROMOTORA"}
      ],
      "padrao_detectado": true
    },
    {
      "campo": "horario_aceite",
      "linhas": [
        {"contrato": "901301 61082", "valor": "14:23:05"},
        {"contrato": "901301 61362", "valor": "14:23:05"}
      ],
      "padrao_detectado": true
    },
    {
      "campo": "hash_componente_termo_cadastro",
      "linhas": [
        {"contrato": "901301 61082", "valor": "sha256:def456..."},
        {"contrato": "901301 61362", "valor": "sha256:def456..."}
      ],
      "padrao_detectado": true
    }
  ],
  "padroes_count": 6,
  "ativa_kit_fraude": true,
  "ativa_cadeia_custodia": false,
  "observacao_padrao": "5+ padroes sistemicos detectados — esquema estruturado, aciona kit-fraude"
}
```

### Regras de ativação

- `ativa_kit_fraude = true` quando `padroes_count >= 3` E há mais de um tipo de padrão (não só hash idêntico isolado).
- `ativa_cadeia_custodia = true` quando há hash idêntico em 1–2 componentes mas demais campos não compartilhados (ou apenas 2 contratos no caso).
- Decisão entre kit-fraude vs cadeia-custódia em C.3 segue a regra: maior densidade → kit-fraude; menor densidade ou caso isolado → cadeia-custódia.

---

## Padrões sistêmicos (`padroes_sistemicos`)

Lista de strings textuais com cada padrão detectado, prontas para serem inseridas como observações no DOCX.

```json
[
  "Mesmo IP (10.1.1.1) entre os contratos 901301 61082 e 901301 61362 — operacao em lote no mesmo correspondente",
  "Mesma session ID (sess_abc123) entre os dois contratos — sessao automatizada nao reaberta",
  "Selfie reutilizada entre os contratos — mesma imagem facial, mesma roupa, mesma posicao",
  "Mesmo correspondente (FONTES PROMOTORA, Florianopolis/SC) originou os dois contratos no mesmo dia (19/12/2023)",
  "Aceite dos dois contratos as 14:23:05 — diferenca zero segundos, humanamente impossivel"
]
```

---

## Alertas (`alertas`)

Lista de strings que sinalizam ao usuário pontos de atenção antes do protocolo (ex.: HISCRE não disponível, perícia ITI manual pendente, etc.).

```json
[
  "Validador ITI: print externo nao realizado — anexar ao protocolo",
  "Selfie do contrato 901301 61082 nao foi extraida visualmente — comparacao manual recomendada",
  "L.3 ATIVO: TED destinado a Bradesco ag 3169, divergente do BB do INSS na epoca; usar tese calibrada (NAO afirmar conta de terceiro)"
]
```

---

## Convenções gerais

1. **Datas em ISO 8601** (`YYYY-MM-DD` ou `YYYY-MM-DDTHH:MM:SS`).
2. **Valores monetários** sempre em `float` (não string), em reais.
3. **CPFs e documentos** sempre como string com pontuação (`"029.873.624-12"`).
4. **Strings vazias** são representadas como `null`, não `""`.
5. **Achados não detectados** têm `risco: "BAIXO"` e `piloto_acionado: null`.
6. **Achados manuais** (ITI, selfie) têm `risco: "manual"` e descrição do que precisa ser feito.
7. **L.3 calibrado** sempre traz `texto_calibrado_etico` lembrando o que NÃO afirmar.

---

## Reaproveitamento (cache)

Se `_pericia/_pericia.json` já existe na pasta:
- O pipeline carrega o JSON existente em vez de re-executar a perícia.
- Útil quando o usuário roda `/replica-nao-contratado` mais de uma vez na mesma pasta.
- Para forçar refazer, deletar `_pericia/_pericia.json`.

## Próximo arquivo da pipeline

`pipeline-pericia-digital.py` — script que recebe a pasta do processo, detecta contratos digitais, executa as verificações A–L e gera este JSON.
