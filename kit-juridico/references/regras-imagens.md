# Regras de Processamento de Imagens

Este arquivo detalha como tratar imagens encontradas nos kits documentais, incluindo casos especiais que exigem tratamento diferenciado.

## Índice

1. [Múltiplos documentos na mesma imagem](#1-múltiplos-documentos-na-mesma-imagem)
2. [Dados sensíveis em imagens](#2-dados-sensíveis-em-imagens)
3. [Fotos de cautela (cliente assinando)](#3-fotos-de-cautela-cliente-assinando)
4. [Documentos que devem ser recortados](#4-documentos-que-devem-ser-recortados)
5. [Critérios de qualidade do recorte](#5-critérios-de-qualidade-do-recorte)

---

## 1. Múltiplos documentos na mesma imagem

É comum que o cliente ou o escritório fotografe mais de um documento na mesma imagem. Exemplos típicos:

- RG + senha do INSS na mesma foto
- RG + CPF lado a lado
- Frente e verso do RG na mesma imagem
- Documento + bilhete com anotações
- Comprovante de residência + documento pessoal

**Procedimento:**
1. Identificar todos os documentos/elementos presentes na imagem.
2. Avaliar cada elemento: é um documento processual, um dado sensível ou um item residual?
3. Recortar cada documento processual individualmente — cada um vira um PDF separado.
4. Dados sensíveis (senhas, credenciais) devem ser descartados e registrados na planilha de pendências.
5. Itens residuais (anotações, bilhetes) ficam na pasta `0. Kit`.

### 1.1 Armadilha CIN moderna — frente e verso pertencem à mesma pessoa

A Carteira de Identidade Nacional (CIN) emitida a partir de 2023 tem duas
faces visualmente distintas:

| Face | Conteúdo |
|---|---|
| Frente | Foto, nome do titular, número RG/CPF, data de nascimento, assinatura |
| Verso | Filiação (nome dos pais), órgão expedidor, local e data de emissão, naturalidade |

**Armadilha recorrente:** o verso da CIN traz a filiação do **titular**. Se o
titular se chama "ADALTO MAXIMIANO PINHEIRO" e a filiação é
"FRANCISCA MÁXIMIANO + DANILO PINHEIRO DOS SANTOS", um agente desatento pode
classificar o verso como "CIN da Francisca" — porque o nome de Francisca
aparece com destaque. **Isso é erro.**

**Regra:**
- Frente e verso da CIN são páginas do **mesmo documento** e ficam **juntas** no PDF `3. RG e CPF.pdf` do titular.
- Antes de classificar uma CIN como sendo "de outra pessoa", confira se o nome em destaque é o do **titular** (geralmente na frente, fonte grande, com foto) ou se é apenas a **filiação** (no verso, listada como "Pai:" / "Mãe:" / "Filiação:").
- Quando um KIT compactado tem várias páginas de CIN, mapeie qual frente combina com qual verso ANTES de fatiar — o emparelhamento pelo nome da filiação é o teste decisivo.

Caso paradigma (ADALTO, 2026-05-11): o verso da CIN do ADALTO foi inicialmente
classificado como CIN da Francisca (testemunha 1) porque o verso lista
"FRANCISCA MÁXIMIANO" como mãe. Corrigido após emparelhar frente+verso.

---

## 2. Dados sensíveis em imagens

Frequentemente os clientes enviam, junto com os documentos, informações sensíveis como senhas e credenciais de acesso. Isso acontece porque muitos clientes são idosos e enviam tudo que têm junto.

**Exemplos de dados sensíveis:**
- Senha do INSS / Meu INSS / GOV.BR
- Senha de banco
- Login e senha de aplicativos
- QR codes de autenticação
- Tokens ou códigos de acesso

**Regras obrigatórias:**
- Dados sensíveis NUNCA devem ser incluídos nas pastas de ação.
- Se o dado sensível estiver na mesma imagem que um documento válido (ex: foto do RG com a senha do INSS embaixo), recortar CADA elemento separadamente.
- O documento válido (RG) segue para a pasta de ação normalmente.
- O dado sensível (senha) deve ser salvo separadamente e mantido APENAS na pasta `0. Kit`. Renomear como: `Senha INSS` ou `Senha GOV` (conforme o caso).
- Dados sensíveis não são documentos processuais, mas fazem parte do material recebido e devem ser preservados no kit.

---

## 3. Fotos de cautela (cliente assinando)

Em muitos kits, o escritório envia fotos do cliente no momento da assinatura dos documentos. Essas fotos mostram a pessoa efetivamente assinando o kit e servem como prova de cautela para o escritório.

**Como identificar:**
- Foto de uma pessoa assinando um documento
- Pessoa segurando caneta sobre papel
- Ambiente doméstico ou de escritório visível
- Pode mostrar o rosto do cliente ou apenas as mãos assinando
- O documento na foto geralmente é o contrato de prestação de serviços ou o KIT

**Regras obrigatórias:**
- Essas fotos são registros de cautela e NÃO são documentos processuais.
- NÃO devem ser recortadas, processadas ou convertidas.
- Devem permanecer APENAS na pasta `0. Kit`.
- NÃO devem ser colocadas nas pastas de ação.
- Renomear como: `Foto de cautela - assinatura` (ou `Foto de cautela - assinatura 1`, `Foto de cautela - assinatura 2` se houver mais de uma).

---

## 4. Documentos que devem ser recortados

O procedimento de recorte e centralização deve ser aplicado a:

- RG (frente e/ou verso)
- CPF
- CNH
- Comprovante de residência
- Documentos bancários fotografados
- Contratos fotografados
- Declarações fotografadas
- Qualquer documento processual enviado como foto

---

## 5. Critérios de qualidade do recorte

O documento final processado NÃO pode conter:
- Fundo visível (mesa, chão, tecido)
- Partes do corpo (mãos, dedos)
- Objetos ao redor (canetas, copos, celulares)
- Múltiplos documentos no mesmo enquadramento
- Sombras que prejudiquem a leitura
- Outros elementos que não sejam o documento em si

O resultado deve ser: exclusivamente o documento, limpo e centralizado, ocupando a maior área possível da página.
