"""Catálogo canônico de bancos para iniciais NÃO CONTRATADO.

Espelho do `Modelos/IniciaisNaoContratado/bancos-canonicos.md`. Atualizar SEMPRE
em ambos quando adicionar/corrigir banco.

Estrutura: BANCOS[chave_canonica][jurisdicao] = {nome, descricao_pj, cnpj, endereco}
- chave_canonica: lowercase sem pontuação (ex.: "itau", "pan", "agibank")
- jurisdicao: "matriz" / "AL" / "AM" / "BA"
- descricao_pj: "pessoa jurídica de direito privado", "sociedade anônima fechada", etc.
"""

INSS_FIXO = {
    'nome': 'INSTITUTO NACIONAL DO SEGURO SOCIAL — INSS',
    'descricao_pj': 'autarquia federal',
    'cnpj': '29.979.036/0001-40',
    'enderecos_subsecao': {
        'Salvador': 'Av. Sete de Setembro, 1078 - Mercês, Salvador/BA',
        'Manaus': 'Rua Ferreira Pena, 1129, Centro, Manaus/AM',
        'Maceió': 'Av. Fernandes Lima, S/N, Farol, Maceió/AL',
        'Belo Horizonte': 'Av. Augusto de Lima, 1234, Barro Preto, Belo Horizonte/MG',
        'Brasília': 'SAUS Quadra 02, Bloco "O", Brasília/DF, CEP 70.070-946',
    },
}

BANCOS = {
    # === MATRIZ (default) ===
    'agibank': {
        'matriz': {
            'nome': 'BANCO AGIBANK SA',
            'descricao_pj': 'sociedade anônima fechada',
            'cnpj': '10.664.513/0001-50',
            'endereco': 'Rua Sergio Fernandes Borges Soares, Prédio 12 E-1, nº 1000, Bairro Distrito Industrial, Campinas/SP, CEP 13.054-709',
        },
        'AL': {
            'nome': 'BANCO AGIBANK S.A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '10.664.513/0001-50',  # CNPJ matriz — doc-fonte tinha erro com 59.285.411/0041-00
            'endereco': 'R. Barão de Penedo, nº 306, Centro, Maceió/AL, CEP 57.036-730',
            'observacao_alerta': 'CONFERIR CNPJ — doc-fonte traz CNPJ do PAN/AL',
        },
        'BA': {
            'nome': 'BANCO AGIBANK S.A',
            'descricao_pj': 'instituição financeira de direito privado',
            'cnpj': '10.664.513/0001-50',  # CNPJ matriz — doc-fonte tinha erro com 13.660.104/0001-74
            'endereco': 'Estr. do Coqueiro Grande, nº 126, Bairro Cajazeiras/BA, CEP 41.343-855',
            'observacao_alerta': 'CONFERIR CNPJ — doc-fonte traz CNPJ da AGIPLAN',
        },
        'MG': {
            'nome': 'AGIBANK S.A.',
            'descricao_pj': 'instituição financeira de direito privado',
            'cnpj': '10.664.513/0001-50',
            'endereco': 'Rua Curvelo, nº 95, Floresta, Belo Horizonte/MG, CEP 31.015-172',
        },
    },
    'agiplan': {
        'BA': {
            'nome': 'AGIPLAN S.A.',
            'descricao_pj': 'instituição financeira de direito privado',
            'cnpj': '13.660.104/0001-74',
            'endereco': 'Rua Miguel Calmon, nº 125, Comércio, Salvador/BA, CEP 40.015-010',
        },
    },
    'banrisul': {
        'matriz': {
            'nome': 'BANCO BANRISUL S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '92.702.067/0001-96',
            'endereco': 'Rua Capitão Montanha, nº 177, Centro, Porto Alegre/RS, CEP 90.010-040',
        },
        'BA': {
            'nome': 'BANCO BANRISUL S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '92.702.067/0001-96',
            'endereco': 'Rua Alceu Amoroso Lima, Loja 01, Caminho das Árvores, Salvador/BA, CEP 41.820-770',
        },
    },
    'bb': {  # Banco do Brasil — REGRA DO ESCRITÓRIO: sempre matriz Brasília.
        # Não cadastrar entradas por UF (a matriz é a referência única).
        'matriz': {
            'nome': 'BANCO DO BRASIL S/A',
            'descricao_pj': 'sociedade de economia mista',
            'cnpj': '00.000.000/0001-91',
            'endereco': 'SAUN Quadra 5, Lote B, Ed. Banco do Brasil, 3º andar, Brasília/DF, CEP 70.040-912',
        },
    },
    'bgn_cetelem': {
        'matriz': {
            'nome': 'BANCO BGN/CETELEM S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '00.558.456/0001-71',
            'endereco': '— matriz não informada no doc-fonte; CONFERIR',
        },
        'AL': {
            'nome': 'BANCO BGN/CETELEM S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '00.558.456/0001-71',
            'endereco': 'Rua do Sol, nº 187, Centro, Janpeter, Maceió/AL, CEP 57.020-070',
        },
        'AM': {
            'nome': 'BANCO BGN/CETELEM S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '00.558.456/0001-71',
            'endereco': 'Rua Doutor Moreira, nº 238, Centro, Manaus/AM, CEP 69.005-250',
        },
        'BA': {
            'nome': 'BANCO BGN/CETELEM S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '00.558.456/0005-03',
            'endereco': 'Av. Barnabé, nº 3259, sala 1202, Barbalho, Salvador/BA, CEP 40.301-155',
        },
    },
    'bmg': {
        'matriz': {
            'nome': 'BANCO BMG S/A',
            'descricao_pj': 'sociedade anônima aberta',
            'cnpj': '61.186.680/0001-74',
            'endereco': 'Av. Presidente Juscelino Kubitschek, nº 1830, Vila Nova Conceição, São Paulo/SP, CEP 04.543-900',
        },
        'AL': {
            'nome': 'BANCO BMG S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '61.186.680/0001-74',
            'endereco': 'Rua do Sol, nº 117, Centro, Maceió/AL, CEP 57.020-070',
        },
        'AM': {
            'nome': 'BANCO BMG S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '61.186.680/0031-90',
            'endereco': 'Rua Marcelio Dias, nº 291, Centro, Manaus/AM, CEP 69.005-270',
        },
        'BA': {
            'nome': 'BANCO BMG S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '61.186.680/0033-51',
            'endereco': 'Rua da Espanha, Salas 01 e 02, Comércio, Salvador/BA, CEP 40.010-040',
        },
    },
    'bnp_paribas': {
        'matriz': {
            'nome': 'BANCO BNP PARIBAS BRASIL S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '01.522.368/0001-82',
            'endereco': 'Av. Juscelino Kubistschek, nº 1.909, 9° e 11° andares, Torre Sul, Vila Nova, São Paulo/SP, CEP 04.543-907',
        },
    },
    'bradesco': {
        'matriz': {
            'nome': 'BANCO BRADESCO S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '60.746.948/0001-12',
            'endereco': 'Cidade de Deus, Vila Yara, S/N, Osasco/SP, CEP 06.029-900',
        },
        'AL': {
            'nome': 'BANCO BRADESCO S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '60.746.948/0001-12',
            'endereco': 'Avenida Menino Marcelo, Serraria, S/N, Maceió/AL, CEP 57.046-000',
        },
        'AM': {
            'nome': 'BANCO BRADESCO S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '60.746.948/0320-73',
            'endereco': 'Avenida Sete de Setembro, nº 895, Centro, Manaus/AM, CEP 69.005-140',
        },
        'BA': {
            'nome': 'BANCO BRADESCO S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '60.746.948/0020-85',
            'endereco': 'Avenida Antônio Carlos Magalhães, nº 3752, 2º andar, Iguatemi, Salvador/BA, CEP 41.820-000',
        },
    },
    'brb': {
        'matriz': {
            'nome': 'BRB CRÉDITO FINANCIAMENTO E INVESTIMENTO S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '33.136.888/0001-43',
            'endereco': 'Q SAUN Quadra 5, Bloco C, Torre III, sala 301, Asa Norte, Brasília/DF, CEP 70.040-250',
        },
    },
    'c6': {
        'matriz': {
            'nome': 'BANCO C6 CONSIGNADO S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '61.348.538/0001-86',
            'endereco': 'Av. Nove de Julho, nº 3148, Jardim Paulista, São Paulo/SP, CEP 01.406-000',
        },
        'AM': {
            'nome': 'BANCO C6 CONSIGNADO SA',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '34.679.085/0001-06',
            'endereco': 'R. Loris Cordovil, nº 28, Centro, Manaus/AM, CEP 69.043-010',
        },
    },
    'caixa': {
        'matriz': {
            'nome': 'CAIXA ECONÔMICA FEDERAL',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '00.360.305/0001-04',
            'endereco': 'Setor Bancário Sul, Quadra 04, nº 34, Bloco A, Asa Sul, Brasília/DF, CEP 70.092-900',
        },
        'BA': {
            'nome': 'CAIXA ECONÔMICA FEDERAL',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '00.360.305/1517-49',
            'endereco': 'Rua Rodoviários, nº 01, Loja 07, Cabula, Salvador/BA, CEP 41.150-125',
        },
    },
    'capital_consignado': {
        'matriz': {
            'nome': 'CAPITAL CONSIGNADO SA',
            'descricao_pj': 'pessoa jurídica',
            'cnpj': '40.083.667/0001-10',
            'endereco': 'Rua Nova Jerusalém, nº 1069, Chácara Santo Antônio (Zona Leste), São Paulo/SP, CEP 03.410-000',
        },
        'AL': {
            'nome': 'CAPITAL CONSIGNADO SA',
            'descricao_pj': 'pessoa jurídica',
            'cnpj': '40.083.667/0001-10',
            'endereco': 'Rua da Alegria, nº 370, Centro, Maceió/AL, CEP 57.020-320',
        },
        'BA': {
            'nome': 'CAPITAL CONSIG SOCIEDADE DE CRÉDITO DIRETO S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '40.083.667/0001-10',
            'endereco': 'Rua Nova Jerusalém, nº 1069, Chácara Santo Antônio, São Paulo/SP, CEP 03.410-000',
        },
    },
    'cifra': {
        'BA': {
            'nome': 'BANCO CIFRA S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '62.421.979/0008-03',
            'endereco': 'Rua Coronel Almerindo Rehem, nº 126, Sala 302, Caminho das Árvores, Salvador/BA, CEP 41.820-768',
        },
    },
    'crefisa': {
        'matriz': {
            'nome': 'BANCO CREFISA S/A',
            'descricao_pj': 'sociedade anônima fechada',
            'cnpj': '61.033.106/0001-86',
            'endereco': 'Rua Canadá, nº 390, Jardim América, São Paulo/SP, CEP 01.436-000',
        },
    },
    'daycoval': {
        'matriz': {
            'nome': 'BANCO DAYCOVAL S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '62.232.889/0001-90',
            'endereco': 'Avenida Paulista, nº 1793, Bela Vista, São Paulo/SP, CEP 01.311-200',
        },
        'AL': {
            'nome': 'BANCO DAYCOVAL S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '62.232.889/0020-52',
            'endereco': 'Rua Sampaio Marques, nº 25, Pajuçara, Maceió/AL, CEP 57.030-107',
        },
        'AM': {
            'nome': 'BANCO DAYCOVAL S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '62.232.889/0001-90',
            'endereco': 'Avenida Djalma Batista, nº 1661, Torre Business, Chapada, 15º andar, Salas 1508/1509/1510, Manaus/AM, CEP 69.050-010',
        },
        'BA': {
            'nome': 'BANCO DAYCOVAL S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '62.232.889/0008-66',
            'endereco': 'Avenida Antônio Carlos Magalhães, nº 3244, Caminho das Árvores, Edifício Thomé de Souza, Salvador/BA, CEP 41.820-000',
        },
    },
    'digio': {
        'matriz': {
            'nome': 'BANCO DIGIO SA',
            'descricao_pj': 'sociedade anônima fechada',
            'cnpj': '27.098.060/0001-45',
            'endereco': 'Alameda Xingu, nº 512, Alphaville/SP, 7º andar, CEP 06.455-030',
        },
        'AM': {
            'nome': 'BANCO DIGIO S.A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '27.098.060/0035-94',
            'endereco': 'Avenida Eduardo Ribeiro, nº 475, Centro, Manaus/AM, CEP 69.010-000',
        },
    },
    'facta': {
        'matriz': {
            'nome': 'FACTA FINANCEIRA S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '15.581.638/0001-30',
            'endereco': 'Rua dos Andradas, nº 1409, 7º andar, Centro Histórico, Porto Alegre/RS, CEP 90.020-011',
        },
        'AL': {
            'nome': 'FACTA FINANCEIRA S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '15.581.638/0001-30',
            'endereco': 'Rua Barão de Penedo, nº 197, Centro, Maceió/AL, CEP 57.020-340',
        },
        'BA': {
            'nome': 'FACTA FINANCEIRA S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '01.360.251/0096-00',
            'endereco': 'Rua da Bélgica, nº 148, Loja C, Comércio, Salvador/BA, CEP 40.010-030',
        },
    },
    'inbursa': {
        'matriz': {
            'nome': 'BANCO INBURSA S.A.',
            'descricao_pj': 'sociedade anônima fechada',
            'cnpj': '04.866.275/0001-63',
            'endereco': 'Rua Henri Dunant, nº 780, Santo Amaro, São Paulo/SP, CEP 04.709-110',
        },
    },
    'inter': {
        'matriz': {
            'nome': 'BANCO INTER SA',
            'descricao_pj': 'sociedade anônima fechada',
            'cnpj': '00.416.968/0001-01',
            'endereco': 'Av. Barbacena, nº 1219, Santo Agostinho, Belo Horizonte/MG, CEP 30.190-131',
        },
        'BA': {
            'nome': 'BANCO INTER S.A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '00.416.968/0002-84',
            'endereco': 'Rua Portugal, nº 74, sala 907, Comércio, Salvador/BA, CEP 40.015-001',
        },
    },
    'itau': {
        'matriz': {
            'nome': 'BANCO ITAU CONSIGNADO SA',
            'descricao_pj': 'sociedade anônima fechada',
            'cnpj': '33.885.724/0001-19',
            'endereco': 'Pça Alfredo Egydio de Souza Aranha, nº 100, Parque Jabaquara, São Paulo/SP, CEP 04.344-902',
        },
        'AM': {
            'nome': 'BANCO ITAÚ CONSIGNADO SA',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '60.701.190/1343-05',
            'endereco': 'Avenida Djalma Batista, nº 390, Nossa Senhora das Graças, Manaus/AM, CEP 69.053-000',
        },
    },
    'master': {
        'matriz': {
            'nome': 'BANCO MASTER S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '33.923.798/0001-00',
            'endereco': 'Praça Botafogo, nº 228, Botafogo, Rio de Janeiro/RJ, CEP 22.250-906',
        },
    },
    'mercantil': {
        'matriz': {
            'nome': 'BANCO MERCANTIL DO BRASIL S/A',
            'descricao_pj': 'pessoa jurídica',
            'cnpj': '17.184.037/0001-10',
            'endereco': 'Av. Afonso Pena, nº 1940, Funcionários, Belo Horizonte/MG, CEP 30.130-007',
        },
        'AL': {
            'nome': 'BANCO MERCANTIL DO BRASIL S/A',
            'descricao_pj': 'pessoa jurídica',
            'cnpj': '17.184.037/0001-10',
            'endereco': 'Rua do Sol, nº 167, Centro, Maceió/AL, CEP 57.020-070',
        },
        'BA': {
            'nome': 'BANCO MERCANTIL DO BRASIL S/A',
            'descricao_pj': 'pessoa jurídica',
            'cnpj': '17.184.037/0400-90',
            'endereco': 'Rua Ewerton Visco, nº 290, sala 2103, Caminho das Árvores, Salvador/BA, CEP 41.820-022',
        },
    },
    'nubank': {
        'matriz': {
            'nome': 'BANCO NUBANK',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '18.236.120/0001-58',
            'endereco': 'Rua Capote Valente, nº 39, São Paulo/SP, CEP 05.409-000',
        },
    },
    'ole': {  # Olé / BonSucesso
        'matriz': {
            'nome': 'BANCO OLE BONSUCESSO CONSIGNADO S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '71.371.686/0001-00',
            'endereco': '— matriz não informada no doc-fonte; CONFERIR',
        },
        'AL': {
            'nome': 'BANCO OLE BONSUCESSO CONSIGNADO S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '71.371.686/6043-01',
            'endereco': 'Rua Des. Artur Jucá, Centro, Maceió/AL, CEP 57.020-640',
        },
        'BA': {
            'nome': 'BANCO OLE BONSUCESSO CONSIGNADO S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '71.371.686/0003-37',
            'endereco': 'Avenida Tancredo Neves, Ed. Salvador Trade Cen., Torre Norte, Salas 2207 a 2209, Caminho das Árvores, Salvador/BA, CEP 41.820-020',
        },
    },
    'parana_banco': {
        'matriz': {
            'nome': 'PARANÁ BANCO S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '14.388.334/0001-99',
            'endereco': 'Rua Visconde de Nácar, nº 1.440, Centro, Curitiba/PR, CEP 80.410-201',
        },
    },
    'senff': {
        'matriz': {
            'nome': 'SENFF S.A. CRÉDITO, FINANCIAMENTO E INVESTIMENTO',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '11.378.938/0001-07',
            'endereco': 'Avenida Cândido de Abreu, nº 526, Edifício Centro Empresarial, 9º andar, Centro Cívico, Curitiba/PR, CEP 80.530-000',
        },
    },
    'inter': {
        'matriz': {
            'nome': 'BANCO INTER S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '00.416.968/0001-01',
            'endereco': 'Avenida Barbacena, nº 1.219, Santo Agostinho, Belo Horizonte/MG, CEP 30.190-131',
        },
    },
    'pan': {
        'matriz': {
            'nome': 'BANCO PAN S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '59.285.411/0001-13',
            'endereco': 'Avenida Paulista, nº 1.374, 16º andar, Bela Vista, São Paulo/SP, CEP 01.310-916',
        },
        'AL': {
            'nome': 'BANCO PAN SA',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '59.285.411/0041-00',
            'endereco': 'Rua do Sol, nº 123, Centro, Maceió/AL, CEP 57.020-070',
        },
        'AM': {
            'nome': 'BANCO PAN S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '59.285.411/0001-13',
            'endereco': 'Avenida Ephigenio Salles, nº 1.327, Aleixo, Manaus/AM, CEP 69.060-020',
        },
        'BA': {
            'nome': 'BANCO PAN S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '59.285.411/0001-13',
            'endereco': 'Avenida Luís Viana Filho, nº 6462, Patamares, Salvador/BA, CEP 41.680-400',
        },
    },
    'parana': {
        'matriz': {
            'nome': 'PARANÁ BANCO S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '14.388.334/0001-99',
            'endereco': 'Rua Comendador Araújo, nº 614, Batel, Curitiba/PR, CEP 80.420-063',
        },
    },
    'parati': {
        'matriz': {
            'nome': 'BANCO PARATI – CFI S.A.',
            'descricao_pj': 'sociedade anônima fechada',
            'cnpj': '03.311.443/0001-91',
            'endereco': 'Av. Nossa Senhora da Penha, nº 2796, Santa Luzia, Vitória/ES, CEP 29.045-402',
        },
    },
    'picpay': {
        'matriz': {
            'nome': 'PICPAY INSTITUIÇÃO DE PAGAMENTO S/A',
            'descricao_pj': 'sociedade anônima fechada',
            'cnpj': '22.896.431/0001-10',
            'endereco': 'Av. Manuel Bandeira, nº 291, Vila Leopoldina, São Paulo/SP, CEP 05.317-020',
        },
    },
    'pine': {
        'matriz': {
            'nome': 'BANCO PINE S.A.',
            'descricao_pj': 'sociedade anônima aberta',
            'cnpj': '62.144.175/0001-20',
            'endereco': 'Av. Juscelino Kubistschek, nº 1830, Vila Nova Conceição, São Paulo/SP, CEP 04.543-900',
            'observacao_alerta': 'CNPJ tinha espaço estranho no doc-fonte ("14. 62.144.175/0001-20") — adotado 62.144.175/0001-20',
        },
        'AL': {
            'nome': 'BANCO PINE S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '62.144.175/0001-20',
            'endereco': 'Rua Doutor Antônio Pedro de Mendonça, nº 102, Pajuçara, Maceió/AL, CEP 57.022-187',
        },
    },
    'qi_scd': {
        'matriz': {
            'nome': 'QI SOCIEDADE DE CRÉDITO DIRETO S/A',
            'descricao_pj': 'sociedade anônima fechada',
            'cnpj': '32.402.502/0001-35',
            'endereco': 'Av. Rebouças, nº 2942, 16º andar, Pinheiros, São Paulo/SP, CEP 05.402-500',
        },
    },
    'safra': {
        'matriz': {
            'nome': 'BANCO SAFRA S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '58.160.789/0001-28',
            'endereco': 'Avenida Paulista, nº 2.100, Bela Vista, São Paulo/SP, CEP 01.310-930',
        },
    },
    'santander': {
        'matriz': {
            'nome': 'BANCO SANTANDER (BRASIL) S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '90.400.888/0001-42',
            'endereco': 'Av. Presidente Juscelino Kubitschek, nº 2041, Conjunto 281, Bloco A, Cond. WTORRE JK, Vila Nova Conceição, São Paulo/SP, CEP 04.543-011',
        },
        'AL': {
            'nome': 'BANCO SANTANDER S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '90.400.888/2373-12',
            'endereco': 'Rua do Sol, nº 310, Centro, Maceió/AL, CEP 57.020-070',
        },
        'AM': {
            'nome': 'BANCO SANTANDER S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '90.400.888/2371-50',
            'endereco': 'Avenida Eduardo Ribeiro, nº 590, Centro, Manaus/AM, CEP 69.010-000',
        },
        'BA': {
            'nome': 'BANCO SANTANDER S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '90.400.888/2446-02',
            'endereco': 'Avenida Antônio Carlos Magalhães, nº 3305, Loja, Brotas, Salvador/BA, CEP 40.280-000',
        },
    },
    'seguro': {
        'matriz': {
            'nome': 'BANCO SEGURO S/A',
            'descricao_pj': 'sociedade anônima fechada',
            'cnpj': '10.264.663/0001-77',
            'endereco': 'Av. Brig. Faria Lima, nº 1.384, Jardim Paulistano, São Paulo/SP, CEP 01.451-001',
        },
    },
    'senff': {
        'matriz': {
            'nome': 'BANCO SENFF S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '11.970.623/0002-94',
            'endereco': 'Av. das Nações Unidas, nº 18801, Jardim Bom Bosco, São Paulo/SP, CEP 04.757-025',
        },
    },
    'sicoob': {
        'matriz': {
            'nome': 'BANCO COOPERATIVO SICOOB S.A.',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '02.038.232/0001-64',
            'endereco': 'St. de Indústrias Gráficas, Quadra 06, Plano Piloto, nº 2080, Brasília/DF, CEP 70.610-460',
        },
    },
    'via_certa': {
        'matriz': {
            'nome': 'VIA CERTA FINANCIADORA S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '05.192.316/0001-46',
            'endereco': 'Rua Tenente Jung, nº 366, Centro, Santo Cristo/RS, CEP 98.960-000',
        },
    },
    'votorantim': {
        'matriz': {
            'nome': 'BANCO VOTORANTIM S.A.',
            'descricao_pj': 'sociedade anônima fechada',
            'cnpj': '59.588.111/0001-03',
            'endereco': 'Av. das Nações Unidas, nº 14171, Vila Gertrudes, São Paulo/SP, CEP 07.794-000',
        },
    },
    'zema': {
        'matriz': {
            'nome': 'BANCO ZEMA FINANCEIRA S/A',
            'descricao_pj': 'pessoa jurídica de direito privado',
            'cnpj': '05.351.887/0001-86',
            'endereco': 'Av. José Ananias de Aguiar, nº 5005, Conj. Habitacional Boa Vista, Araxá/MG, CEP 38.184-200',
        },
    },
}


# === Aliases (variações de escrita encontradas em pastas/HISCON) ===
ALIASES = {
    # nome encontrado → chave canônica
    'BANCO ITAU CONSIGNADO': 'itau',
    'ITAU CONSIGNADO': 'itau',
    'ITAÚ': 'itau',
    'ITAU': 'itau',
    'BANCO ITAÚ': 'itau',
    'BANCO ITAU': 'itau',

    'FACTA FINANCEIRA S A': 'facta',
    'FACTA': 'facta',
    'BANCO FACTA': 'facta',

    'BANCO AGIBANK': 'agibank',
    'AGIBANK FINANCEIRA': 'agibank',
    'AGIBANK': 'agibank',

    'BANCO INTER': 'inter',
    'BANCO INTER S/A': 'inter',
    'BANCO INTER SA': 'inter',
    'INTER': 'inter',

    'BANCO PAN': 'pan',
    'PAN': 'pan',

    'PARANÁ BANCO': 'parana_banco',
    'PARANA BANCO': 'parana_banco',
    'BANCO PARANÁ': 'parana_banco',
    'BANCO PARANA': 'parana_banco',

    'SENFA': 'senff',
    'SENFF': 'senff',
    'BANCO SENFA': 'senff',
    'BANCO SENFF': 'senff',
    'SENFF S.A. CRÉDITO': 'senff',
    'SENFF S A CREDITO': 'senff',

    'BANCO BRADESCO': 'bradesco',
    'BANCO BRADESCO FINANCIAMENTOS': 'bradesco',
    'BRADESCO FINANCIAMENTOS': 'bradesco',
    'BRADESCO': 'bradesco',

    'BANCO C6 CONSIGNADO': 'c6',
    'C6 CONSIGNADO': 'c6',
    'C6': 'c6',

    'BANCO BMG': 'bmg',
    'BMG': 'bmg',

    'BANCO VOTORANTIM': 'votorantim',
    'VOTORANTIM': 'votorantim',

    'BANCO OLE CONSIGNADO': 'ole',
    'BANCO OLE BONSUCESSO': 'ole',
    'OLE': 'ole',

    'BANCO DAYCOVAL': 'daycoval',
    'DAYCOVAL': 'daycoval',

    'BANCO DO BRASIL': 'bb',
    'BB': 'bb',
    'DO BRASIL': 'bb',
    'BANCO BB': 'bb',

    'BANCO MERCANTIL DO BRASIL': 'mercantil',
    'BANCO MERCANTIL': 'mercantil',
    'MERCANTIL DO BRASIL': 'mercantil',
    'MERCANTIL': 'mercantil',

    'BANCO SANTANDER': 'santander',
    'BANCO SANTANDER (BRASIL)': 'santander',
    'BANCO SANTANDER BRASIL': 'santander',
    'SANTANDER': 'santander',
    'SANTANDER FINANCIAMENTOS': 'santander',
    'SANTANDER FINANCIAMENTO': 'santander',
    'BANCO SANTANDER FINANCIAMENTO': 'santander',

    'BANCO INTER': 'inter',
    'BANCO INTER S A': 'inter',
    'BANCO INTER SA': 'inter',
    'INTER': 'inter',

    'BANCO INBURSA': 'inbursa',
    'INBURSA': 'inbursa',

    'QI SOCIEDADE DE CREDITO DIRETO': 'qi_scd',
    'QI SOCIEDADE DE CRÉDITO DIRETO': 'qi_scd',
    'QI SCD': 'qi_scd',
    'QI': 'qi_scd',

    'CETELEM': 'bgn_cetelem',
    'BANCO CETELEM': 'bgn_cetelem',
    'BANCO BGN': 'bgn_cetelem',
    'BGN': 'bgn_cetelem',
    'BGN/CETELEM': 'bgn_cetelem',
    'BANCO BGN/CETELEM': 'bgn_cetelem',
}


def resolver_banco(nome_bruto, jurisdicao='matriz'):
    """Resolve um nome bruto (do HISCON ou da pasta) para os dados canônicos.

    Tenta:
    1. Match exato no ALIASES
    2. Match por substring (nome_bruto contém alguma chave de ALIASES)
    3. Match por chave canônica direta

    Args:
        nome_bruto: ex. "029 - BANCO ITAU CONSIGNADO SA" (HISCON) ou "BANCO ITAÚ" (pasta)
        jurisdicao: "matriz" / "AL" / "AM" / "BA"

    Returns:
        dict com {nome, descricao_pj, cnpj, endereco} ou None se não achar.
    """
    # Limpeza: remover prefixo numérico do HISCON ("029 - ", "121 - ", etc.)
    import re
    nome_limpo = re.sub(r'^\d{3}\s*-\s*', '', nome_bruto.strip()).upper()
    # Versão sem espaços, para tolerar parser HISCON que insere espaços no meio
    # de palavras ("BANCO BRADE SCO" → "BANCOBRADESCO", "SANTA NDER" → "SANTANDER",
    # "AGIBAN K FINANC EIRA" → "AGIBANKFINANCEIRA", "MERCA NTIL" → "MERCANTIL").
    nome_sem_espacos = re.sub(r'\s+', '', nome_limpo)

    chave_canonica = None

    # Tentativa 1: ALIAS exato
    if nome_limpo in ALIASES:
        chave_canonica = ALIASES[nome_limpo]
    else:
        # Tentativa 2a: substring com nome original
        for alias, chave in ALIASES.items():
            if alias in nome_limpo:
                chave_canonica = chave
                break
        # Tentativa 2b: substring com nome SEM espaços (tolera parser HISCON)
        if not chave_canonica:
            for alias, chave in ALIASES.items():
                alias_sem_espacos = re.sub(r'\s+', '', alias)
                if alias_sem_espacos and alias_sem_espacos in nome_sem_espacos:
                    chave_canonica = chave
                    break

    # Tentativa 3: chave canônica direta (já normalizada)
    if not chave_canonica:
        nome_norm = nome_limpo.lower().replace(' ', '_').replace('/', '')
        if nome_norm in BANCOS:
            chave_canonica = nome_norm

    if not chave_canonica:
        return None

    banco = BANCOS.get(chave_canonica, {})
    return banco.get(jurisdicao) or banco.get('matriz')


if __name__ == '__main__':
    # Smoke test
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    casos = [
        ('029 - BANCO ITAU CONSIGNADO SA', 'matriz'),
        ('935 - FACTA FINANCEIRA S A', 'matriz'),
        ('121 - BANCO AGIBANK SA', 'BA'),
        ('BANCO ITAÚ', 'matriz'),
        ('BANCO PAN', 'AM'),
        ('Bradesco', 'BA'),
        ('XYZ DESCONHECIDO', 'matriz'),
    ]
    for nome, jur in casos:
        r = resolver_banco(nome, jur)
        if r:
            print(f'✓ "{nome}" ({jur}) → {r["nome"]} | CNPJ {r["cnpj"]}')
        else:
            print(f'✗ "{nome}" ({jur}) → NÃO ENCONTRADO')
