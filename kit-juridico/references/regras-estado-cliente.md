# Dossiê do Cliente — `_estado_cliente.json`

Arquivo único, salvo na raiz da pasta do cliente, que serve como
**dossiê compartilhado** entre as skills do escritório:

```
kit-juridico → notificacao-extrajudicial → inicial-nao-contratado/inicial-bradesco
       ↓                ↓                              ↓
       cria             enriquece                     enriquece + finaliza
```

Cada skill **lê o que existe**, faz o seu trabalho, e **adiciona o que produziu**.
A próxima skill consome sem precisar reextrair dados.

## Localização

```
<pasta-cliente>/_estado_cliente.json
```

Sempre na raiz da pasta do cliente. Nunca dentro de subpastas de banco.

## Schema (v1)

```json
{
  "schema_version": "1.0",
  "ultima_atualizacao": "2026-05-08T16:30:00",

  "cliente": {
    "nome_completo": "ANAIZA MARIA DA CONCEIÇÃO",
    "nome_arquivo_padrao": "Anaiza Maria da Conceição",
    "cpf": "870.969.274-68",
    "rg": null,
    "rg_orgao_expedidor": null,
    "data_nascimento": "1949-04-29",
    "nacionalidade": "brasileira",
    "estado_civil": "viúva",
    "profissao": "aposentada",
    "endereco": {
      "logradouro": "Rua Antonio Gomes",
      "numero": "S/N",
      "complemento": null,
      "bairro": null,
      "municipio": "Maribondo",
      "uf": "AL",
      "cep": "57670-000",
      "fonte": "comprovante_residencia"
    },
    "telefone": null,
    "email": null
  },

  "beneficios_inss": [
    {
      "nb": "041.645.683-9",
      "especie_codigo": 21,
      "especie_nome": "PENSÃO POR MORTE PREVIDENCIÁRIA",
      "pasta_label": "PENSÃO",
      "situacao": "ATIVO",
      "titular": "ANAIZA MARIA DA CONCEIÇÃO",
      "banco_pagador": "CAIXA ECONÔMICA FEDERAL",
      "agencia_pagadora": "2046",
      "conta_pagadora": "8065641529",
      "renda_mensal": null
    }
  ],

  "contratos": [
    {
      "id_interno": "C001",
      "contrato": "631248310",
      "banco_chave": "ITAU",
      "banco_nome_completo": "BANCO ITAÚ CONSIGNADO SA",
      "banco_codigo_inss": "029",
      "tipo": "CONSIGNADO",
      "situacao": "Ativo",
      "origem_averbacao": "Averbação por Refinanciamento",
      "data_inclusao": "14/09/2021",
      "data_exclusao": null,
      "motivo_exclusao": null,
      "valor_parcela": "R$27,60",
      "valor_emprestado": "R$1.211,32",
      "qtd_parcelas": 84,
      "competencia_inicio": "10/2021",
      "competencia_fim": "09/2028",
      "primeiro_desconto": null,
      "beneficio_nb": "041.645.683-9",
      "beneficio_pasta": "PENSÃO",
      "procuracao_origem_pagina": 1,
      "procuracao_path_relativo": "PENSÃO/BANCO ITAU CONSIGNADO/2- Procuração - Banco Itau Consignado - Contrato 631248310.pdf"
    }
  ],

  "cadeias": [
    {
      "id": "C-01",
      "tipo": "CADEIA",
      "subtipo": "REFIN_DIRETO",
      "bancos": ["BANCO ITAÚ CONSIGNADO"],
      "beneficio": "PENSÃO",
      "contratos_ids": ["C003", "C001"],
      "cor_grifo_hex": "FFF066",
      "cor_nome": "Amarelo",
      "valor_parcela_referencia": "R$236,30",
      "data_referencia": "14/09/2021",
      "narrativa": "Contrato 626702215 (08/07/2020) foi excluído por refinanciamento em 14/09/2021, dando origem ao 632948666 com mesma parcela e mesma data."
    }
  ],

  "pastas_acao": [
    {
      "path_relativo": "PENSÃO/BANCO ITAU CONSIGNADO",
      "beneficio": "PENSÃO",
      "bancos": ["BANCO ITAÚ CONSIGNADO"],
      "tese": "consignado_nao_contratado",
      "tipo_pasta": "banco_unico",
      "cadeias_ids": ["C-01", "C-02", "C-03", "C-04"],
      "contratos_ids": ["C001", "C002", "..."],
      "contratos_impugnar_ids": ["C001", "C002"],
      "contratos_impugnar_origem": "sugestao_automatica",
      "estudo_path": "PENSÃO/BANCO ITAU CONSIGNADO/ESTUDO DE CADEIA - BANCO ITAU CONSIGNADO.docx",
      "extrato_grifado_path": "PENSÃO/BANCO ITAU CONSIGNADO/6- Histórico de empréstimo PENSÃO (grifado).pdf"
    }
  ],

  "captador": {
    "nome": "Marcio Teixeira",
    "slug": "marcio-teixeira",
    "estado_origem_cliente": "BA"
  },

  "advogado_responsavel": {
    "nome": "Tiago Azevedo Lima",
    "oab": "OAB/AL 20906A",
    "uf_atuacao": "AL",
    "escritorio_endereco": "Rua Nossa Senhora da Salete, nº 597, Sala 04, Térreo, Bairro Itapoã, Arapiraca-AL"
  },

  "historico_skills": [
    {
      "skill": "kit-juridico",
      "versao": "v2.0",
      "data": "2026-05-08T15:42:00",
      "acao": "Pasta organizada: 5 pastas de banco, 7 cadeias detectadas, 2 benefícios.",
      "alertas": []
    }
  ],

  "notificacoes_extrajudiciais": [],

  "iniciais": [],

  "anotacoes_livres": ""
}
```

## Regras de uso

### Quem cria

A primeira skill que tocar a pasta cria o JSON. Hoje é o `kit-juridico`.

### Quem atualiza

Toda skill que rodar:
1. **Lê** o JSON existente (se houver) — usa os dados como fonte de verdade
2. **Faz seu trabalho**
3. **Atualiza** os campos que produziu + adiciona entrada em `historico_skills`
4. **Salva** com `ultima_atualizacao` no campo

### Validação

- `schema_version` permite migrações futuras (v1.0 hoje; podemos quebrar e migrar)
- Campos com valor desconhecido devem ser `null` (não `""` ou ausentes)
- Datas em ISO 8601 (`YYYY-MM-DDTHH:MM:SS`) ou `DD/MM/AAAA` (legível ao usuário, mantém compatibilidade com extratos)
- Valores monetários como string com prefixo `R$` (mantém formatação amigável)

### `contratos_impugnar_ids` por pasta_acao

Cada `pastas_acao[]` contém o subconjunto de contratos do HISCON que será objeto de ação. Populado automaticamente pela `kit-juridico` v2.1+ via heurística (`scripts/seletor_contratos.py`):

- **Cadeia ativa ou totalmente encerrada**: toda a cadeia entra (refinanciamentos antecessores respondem solidariamente).
- **Contrato independente Ativo**: entra (`motivo: ativo_independente`).
- **Contrato independente Excluído/Encerrado**: entra com flag `revisar_prescricao` (`motivo: encerrado_independente`).
- **RMC/RCC**: todos os candidatos entram (margem encerrada pode ter cobranças residuais).
- **De-duplicação**: por número de contrato, preferindo `Ativo`.

Campo `contratos_impugnar_origem` enum:
- `sugestao_automatica` — heurística sem revisão humana
- `sugestao_automatica_revisada` — após advogado revisar a planilha `_contratos_a_impugnar.xlsx`
- `manual` — populado manualmente

**Regra para skills consumidoras** (notificacao-extrajudicial, inicial-*):

```python
ids = pasta_acao.get('contratos_impugnar_ids')
if ids:
    contratos_alvo = [c for c in todos_contratos if c['id_interno'] in ids]
else:
    # Fallback legado: nome de arquivo da procuração
    ...
```

A planilha `_contratos_a_impugnar.xlsx` na raiz do cliente é o ponto de revisão humana antes de gerar peças.

### Conflitos entre skill e JSON existente

Se a skill detecta um valor diferente do que está no JSON (ex: cliente mudou de endereço — comprovante novo divergente do JSON anterior), ela DEVE:
1. Atualizar o campo
2. Adicionar entrada em `historico_skills` com `acao: "Endereço atualizado: <antigo> → <novo>"`
3. Não silenciar a divergência

## Política de versionamento do JSON

- A skill **não cria backup** automático antes de sobrescrever
- A skill **NUNCA** apaga campos que ela não conhece (preserva o que outras skills puseram)
- Se houver mudança breaking de schema, criar `_estado_cliente.json.bak` antes de migrar

## Por que JSON e não Markdown/Excel?

- **JSON** é estruturado, validável, fácil de ler programaticamente
- **Markdown** seria difícil de manter consistente entre N skills (parsing frágil)
- **Excel** é binário, não rastreável em git, ruim pra editar com script

O usuário pode abrir o JSON no Notepad++ ou VS Code se quiser ver/editar manualmente.
Para visualização amigável, futuramente pode-se gerar um `_estado_cliente.html` ao final.
