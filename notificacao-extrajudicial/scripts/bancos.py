"""
Cadastro de bancos para notificações extrajudiciais.

Estrutura: dict por banco_chave (a mesma chave usada em _estado_cliente.json).
Cada entrada tem o nome qualificado completo + endereço da MATRIZ + (opcional)
filiais por UF.

Regra de seleção:
  - Tese RMC/RCC em AL → filial AL se houver
  - Tese RMC/RCC em AM → filial AM se houver
  - Demais casos → matriz

Fonte: "Endereços dos bancos.docx" (MODELOS VICE NOTIFICAÇÕES) — extraído
2026-05-08.
"""

BANCOS = {
    'BMG': {
        'nome_qualificado': 'BANCO BMG S.A., sociedade anônima aberta',
        'matriz': {
            'cnpj': '61.186.680/0001-74',
            'logradouro': 'Avenida Presidente Juscelino Kubitschek, nº 1830',
            'bairro': 'Vila Nova Conceição',
            'municipio': 'São Paulo',
            'uf': 'SP',
            'cep': '04.543-900',
        },
        'filiais': {
            'AL': {
                'cnpj': '61.186.680/0001-74',
                'logradouro': 'Rua do Sol, nº 117',
                'bairro': 'Centro',
                'municipio': 'Maceió',
                'uf': 'AL',
                'cep': '57020-070',
            },
            'AM': {
                'cnpj': '61.186.680/0031-90',
                'logradouro': 'Rua Marcílio Dias, nº 291',
                'bairro': 'Centro',
                'municipio': 'Manaus',
                'uf': 'AM',
                'cep': '69.005-270',
            },
        },
    },
    'BRADESCO': {
        'nome_qualificado': 'BANCO BRADESCO S/A, pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '60.746.948/0001-12',
            'logradouro': 'Cidade de Deus, S/N',
            'bairro': 'Vila Yara',
            'municipio': 'Osasco',
            'uf': 'SP',
            'cep': '06.029-900',
        },
        'filiais': {
            'AL': {
                'cnpj': '60.746.948/0001-12',
                'logradouro': 'Avenida Menino Marcelo, S/N',
                'bairro': 'Serraria',
                'municipio': 'Maceió',
                'uf': 'AL',
                'cep': '57.046-000',
            },
            'AM': {
                'cnpj': '60.746.948/0320-73',
                'logradouro': 'Avenida Sete de Setembro, nº 895',
                'bairro': 'Centro',
                'municipio': 'Manaus',
                'uf': 'AM',
                'cep': '69.005-140',
            },
        },
    },
    'ITAU': {
        'nome_qualificado': 'BANCO ITAU CONSIGNADO SA, sociedade anônima fechada',
        'matriz': {
            'cnpj': '33.885.724/0001-19',
            'logradouro': 'Praça Alfredo Egydio De Souza Aranha, nº 100',
            'bairro': 'Parque Jabaquara',
            'municipio': 'São Paulo',
            'uf': 'SP',
            'cep': '04.344-902',
        },
    },
    'C6': {
        'nome_qualificado': 'BANCO C6 CONSIGNADO S.A., pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '61.348.538/0001-86',
            'logradouro': 'Avenida Nove de Julho, nº 3148',
            'bairro': 'Jardim Paulista',
            'municipio': 'São Paulo',
            'uf': 'SP',
            'cep': '01406-000',
        },
    },
    'PAN': {
        'nome_qualificado': 'BANCO PAN S/A, pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '59.285.411/0001-13',
            'logradouro': 'Avenida Paulista, nº 1.374, 16º andar',
            'bairro': 'Bela Vista',
            'municipio': 'São Paulo',
            'uf': 'SP',
            'cep': '01.310-916',
        },
    },
    'CAIXA': {
        'nome_qualificado': 'CAIXA ECONÔMICA FEDERAL, pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '00.360.305/0001-04',
            'logradouro': 'Setor Bancário Sul, Quadra 04, nº 34, Bloco A',
            'bairro': 'Asa Sul',
            'municipio': 'Brasília',
            'uf': 'DF',
            'cep': '70092-900',
        },
    },
    'BB': {
        'nome_qualificado': 'BANCO DO BRASIL S/A, sociedade de economia mista',
        'matriz': {
            'cnpj': '00.000.000/0001-91',
            'logradouro': 'SAUN, Quadra 5, Lote B, Ed. Banco do Brasil, 3º andar',
            'bairro': 'Asa Norte',
            'municipio': 'Brasília',
            'uf': 'DF',
            'cep': '70.040-912',
        },
        'filiais': {
            'AL': {
                'cnpj': '00.558.456/0001-71',
                'logradouro': 'Avenida Fernandes Lima, nº 2591',
                'bairro': 'Pinheiro',
                'municipio': 'Maceió',
                'uf': 'AL',
                'cep': '57.057-450',
            },
        },
    },
    'SANTANDER': {
        'nome_qualificado': 'BANCO SANTANDER (BRASIL) S.A., pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '90.400.888/0001-42',
            'logradouro': 'Avenida Presidente Juscelino Kubitschek, nº 2041, Conjunto 281, Bloco A, Cond. WTORRE JK',
            'bairro': 'Vila Nova Conceição',
            'municipio': 'São Paulo',
            'uf': 'SP',
            'cep': '04543-011',
        },
        'filiais': {
            'AL': {
                'cnpj': '90.400.888/2373-12',
                'logradouro': 'Rua do Sol, nº 310',
                'bairro': 'Centro',
                'municipio': 'Maceió',
                'uf': 'AL',
                'cep': '57.020-070',
            },
            'AM': {
                'cnpj': '90.400.888/2371-50',
                'logradouro': 'Avenida Eduardo Ribeiro, nº 590',
                'bairro': 'Centro',
                'municipio': 'Manaus',
                'uf': 'AM',
                'cep': '69010-000',
            },
        },
    },
    'DAYCOVAL': {
        'nome_qualificado': 'BANCO DAYCOVAL S/A, pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '62.232.889/0001-90',
            'logradouro': 'Avenida Paulista, nº 1793',
            'bairro': 'Bela Vista',
            'municipio': 'São Paulo',
            'uf': 'SP',
            'cep': '01311-200',
        },
        'filiais': {
            'AL': {
                'cnpj': '62.232.889/0020-52',
                'logradouro': 'Rua Sampaio Marques, nº 25',
                'bairro': 'Pajuçara',
                'municipio': 'Maceió',
                'uf': 'AL',
                'cep': '57.030-107',
            },
            'AM': {
                'cnpj': '62.232.889/0001-90',
                'logradouro': 'Avenida Djalma Batista, nº 1661, Torre Business, 15º andar, Salas 1508/1509/1510, SH Millennium Center',
                'bairro': 'Chapada',
                'municipio': 'Manaus',
                'uf': 'AM',
                'cep': '69050-010',
            },
        },
    },
    'MERCANTIL': {
        'nome_qualificado': 'BANCO MERCANTIL DO BRASIL S/A, pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '17.184.037/0001-10',
            'logradouro': 'Avenida Afonso Pena, nº 1940',
            'bairro': 'Funcionários',
            'municipio': 'Belo Horizonte',
            'uf': 'MG',
            'cep': '30.130-007',
        },
        'filiais': {
            'AL': {
                'cnpj': '17.184.037/0001-10',
                'logradouro': 'Rua do Sol, nº 167',
                'bairro': 'Centro',
                'municipio': 'Maceió',
                'uf': 'AL',
                'cep': '57020-070',
            },
        },
    },
    'FACTA': {
        'nome_qualificado': 'FACTA FINANCEIRA S.A., pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '15.581.638/0001-30',
            'logradouro': 'Rua dos Andradas, nº 1409, 7º andar',
            'bairro': 'Centro Histórico',
            'municipio': 'Porto Alegre',
            'uf': 'RS',
            'cep': '90020-011',
        },
        'filiais': {
            'AL': {
                'cnpj': '15.581.638/0001-30',
                'logradouro': 'Rua Barão de Penedo, nº 197',
                'bairro': 'Centro',
                'municipio': 'Maceió',
                'uf': 'AL',
                'cep': '57.020-340',
            },
        },
    },
    'AGIBANK': {
        'nome_qualificado': 'BANCO AGIBANK S.A., sociedade anônima fechada',
        'matriz': {
            'cnpj': '10.664.513/0001-50',
            'logradouro': 'Rua Sergio Fernandes Borges Soares, Prédio 12 E-1, nº 1000',
            'bairro': 'Distrito Industrial',
            'municipio': 'Campinas',
            'uf': 'SP',
            'cep': '13054-709',
        },
    },
    'OLE': {
        'nome_qualificado': 'BANCO OLE BONSUCESSO CONSIGNADO S.A., pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '71.371.686/0001-75',
            'logradouro': 'Rua Sergipe, nº 1057',
            'bairro': 'Funcionários',
            'municipio': 'Belo Horizonte',
            'uf': 'MG',
            'cep': '30130-171',
        },
        'filiais': {
            'AL': {
                'cnpj': '71.371.686/6043-01',
                'logradouro': 'Rua Desembargador Artur Jucá',
                'bairro': 'Centro',
                'municipio': 'Maceió',
                'uf': 'AL',
                'cep': '57.020-640',
            },
        },
    },
    'BGN': {
        'nome_qualificado': 'BANCO BGN/CETELEM S.A., pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '00.558.456/0001-71',
            'logradouro': 'Rua do Sol, nº 187',
            'bairro': 'Centro',
            'municipio': 'Maceió',
            'uf': 'AL',
            'cep': '57.020-070',
        },
        'filiais': {
            'AM': {
                'cnpj': '00.558.456/0001-71',
                'logradouro': 'Rua Doutor Moreira, nº 238',
                'bairro': 'Centro',
                'municipio': 'Manaus',
                'uf': 'AM',
                'cep': '69.005-250',
            },
        },
    },
    'CETELEM': {
        # Mesmo banco que BGN
        'nome_qualificado': 'BANCO BGN/CETELEM S.A., pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '00.558.456/0001-71',
            'logradouro': 'Rua do Sol, nº 187',
            'bairro': 'Centro',
            'municipio': 'Maceió',
            'uf': 'AL',
            'cep': '57.020-070',
        },
    },
    'MASTER': {
        'nome_qualificado': 'BANCO MASTER S/A, pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '33.923.798/0001-00',
            'logradouro': 'Praia de Botafogo, nº 228',
            'bairro': 'Botafogo',
            'municipio': 'Rio de Janeiro',
            'uf': 'RJ',
            'cep': '22.250-906',
        },
    },
    'SAFRA': {
        'nome_qualificado': 'BANCO SAFRA S/A, pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '58.160.789/0001-28',
            'logradouro': 'Avenida Paulista, nº 2.100',
            'bairro': 'Bela Vista',
            'municipio': 'São Paulo',
            'uf': 'SP',
            'cep': '01.310-930',
        },
    },
    'CREFISA': {
        'nome_qualificado': 'BANCO CREFISA S/A, sociedade anônima fechada',
        'matriz': {
            'cnpj': '61.033.106/0001-86',
            'logradouro': 'Rua Canada, nº 390',
            'bairro': 'Jardim América',
            'municipio': 'São Paulo',
            'uf': 'SP',
            'cep': '01.436-000',
        },
    },
    'PARANA': {
        'nome_qualificado': 'PARANÁ BANCO S.A., pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '14.388.334/0001-99',
            'logradouro': 'Rua Comendador Araújo, nº 614',
            'bairro': 'Batel',
            'municipio': 'Curitiba',
            'uf': 'PR',
            'cep': '80420-063',
        },
    },
    'DIGIO': {
        'nome_qualificado': 'BANCO DIGIO SA, sociedade anônima fechada',
        'matriz': {
            'cnpj': '27.098.060/0001-45',
            'logradouro': 'Alameda Xingu, nº 512, 7º andar',
            'bairro': 'Alphaville',
            'municipio': 'Barueri',
            'uf': 'SP',
            'cep': '06.455-030',
        },
    },
    'BANRISUL': {
        'nome_qualificado': 'BANCO BANRISUL S.A., pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '92.702.067/0001-96',
            'logradouro': 'Rua Capitão Montanha, nº 177',
            'bairro': 'Centro',
            'municipio': 'Porto Alegre',
            'uf': 'RS',
            'cep': '90010-040',
        },
    },
    'PINE': {
        'nome_qualificado': 'BANCO PINE S.A., pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '62.144.175/0001-20',
            'logradouro': 'Avenida das Nações Unidas, nº 8501, 30º andar',
            'bairro': 'Pinheiros',
            'municipio': 'São Paulo',
            'uf': 'SP',
            'cep': '05425-070',
        },
    },
    'BRB': {
        'nome_qualificado': 'BRB CRÉDITO FINANCIAMENTO E INVESTIMENTO S.A., pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '33.136.888/0001-43',
            'logradouro': 'Q SAUN Quadra 5, Bloco C, Torre III, sala 301',
            'bairro': 'Asa Norte',
            'municipio': 'Brasília',
            'uf': 'DF',
            'cep': '70040-250',
        },
    },
    'CAPITAL': {
        'nome_qualificado': 'CAPITAL CONSIGNADO SA, pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '40.083.667/0001-10',
            'logradouro': 'Rua Nova Jerusalém, nº 1069',
            'bairro': 'Chácara Santo Antônio',
            'municipio': 'São Paulo',
            'uf': 'SP',
            'cep': '03410-000',
        },
    },
    'INBURSA': {
        'nome_qualificado': 'BANCO INBURSA S.A., sociedade anônima fechada',
        'matriz': {
            'cnpj': '04.866.275/0001-63',
            'logradouro': 'Rua Henri Dunant, nº 780',
            'bairro': 'Santo Amaro',
            'municipio': 'São Paulo',
            'uf': 'SP',
            'cep': '04709-110',
        },
    },
    'INTER': {
        'nome_qualificado': 'BANCO INTER S.A., pessoa jurídica de direito privado',
        'matriz': {
            'cnpj': '00.416.968/0001-01',
            'logradouro': 'Avenida Barbacena, nº 1219',
            'bairro': 'Santo Agostinho',
            'municipio': 'Belo Horizonte',
            'uf': 'MG',
            'cep': '30190-131',
        },
        'filial_sp': {
            'cnpj': '00.416.968/0001-01',
            'logradouro': 'Avenida Presidente Juscelino Kubitschek, nº 1.400, 8º andar, CJ 81',
            'bairro': 'Vila Nova Conceição',
            'municipio': 'São Paulo',
            'uf': 'SP',
            'cep': '04543-000',
        },
    },
}


# Aliases comuns para banco_chave (lookup case-insensitive)
ALIASES = {
    'BANCO BMG': 'BMG',
    'BANCO BMG S/A': 'BMG',
    'BANCO BMG S.A.': 'BMG',
    'BANCO BRADESCO S/A': 'BRADESCO',
    'BANCO BRADESCO S.A.': 'BRADESCO',
    'BANCO ITAU CONSIGNADO': 'ITAU',
    'BANCO ITAU': 'ITAU',
    'BANCO C6 CONSIGNADO': 'C6',
    'BANCO C6': 'C6',
    'BANCO PAN': 'PAN',
    'BANCO PAN S/A': 'PAN',
    'CAIXA ECONOMICA FEDERAL': 'CAIXA',
    'CAIXA ECONÔMICA FEDERAL': 'CAIXA',
    'BANCO DO BRASIL': 'BB',
    'BANCO SANTANDER': 'SANTANDER',
    'BANCO DAYCOVAL': 'DAYCOVAL',
    'BANCO MERCANTIL': 'MERCANTIL',
    'BANCO MERCANTIL DO BRASIL': 'MERCANTIL',
    'FACTA FINANCEIRA': 'FACTA',
    'BANCO AGIBANK': 'AGIBANK',
    'BANCO OLE': 'OLE',
    'OLE BONSUCESSO': 'OLE',
    'BANCO BGN': 'BGN',
    'BGN CETELEM': 'BGN',
    'BANCO MASTER': 'MASTER',
    'BANCO SAFRA': 'SAFRA',
    'BANCO CREFISA': 'CREFISA',
    'PARANA BANCO': 'PARANA',
    'PARANÁ BANCO': 'PARANA',
    'BANCO DIGIO': 'DIGIO',
    'BANCO BANRISUL': 'BANRISUL',
    'BANCO INTER': 'INTER',
    'BANCO INTER S.A.': 'INTER',
    'BANCO INTER S/A': 'INTER',
    'INTER S.A.': 'INTER',
    'BANCO INBURSA': 'INBURSA',
    'BANCO INBURSA S.A.': 'INBURSA',
    'INBURSA': 'INBURSA',
    'CAPITAL CONSIG': 'CAPITAL',
    'CAPITAL CONSIGNADO': 'CAPITAL',
    'CAPITAL CONSIGNADO SA': 'CAPITAL',
    'BRB': 'BRB',
    'BRB CRED FINANC': 'BRB',
    'BRB CRÉDITO': 'BRB',
    'BANCO PINE': 'PINE',
    'PINE': 'PINE',
}


def resolver_chave(banco_chave_ou_nome: str) -> str | None:
    """Tenta resolver chave de banco (BMG, BRADESCO, ITAU, etc.)
    a partir de uma string vinda do _estado_cliente.json (banco_chave OU banco_nome_completo)."""
    if not banco_chave_ou_nome:
        return None
    s = banco_chave_ou_nome.strip().upper()
    # Match direto
    if s in BANCOS:
        return s
    # Match via alias
    for alias, chave in ALIASES.items():
        if alias.upper() == s:
            return chave
    # Match parcial (substring)
    for chave in BANCOS:
        if chave in s:
            return chave
    for alias, chave in ALIASES.items():
        if alias.upper() in s:
            return chave
    return None


def obter_endereco(banco_chave: str, uf_acao: str | None = None) -> dict | None:
    """Retorna dict com nome_qualificado + endereço apropriado para a tese.

    Se uf_acao for AL ou AM e o banco tiver filial nessa UF, usa a filial.
    Senão, usa a matriz.
    """
    chave = resolver_chave(banco_chave)
    if not chave or chave not in BANCOS:
        return None
    banco = BANCOS[chave]
    end = banco['matriz']
    if uf_acao and uf_acao.upper() in banco.get('filiais', {}):
        end = banco['filiais'][uf_acao.upper()]
    return {
        'banco_chave': chave,
        'nome_qualificado': banco['nome_qualificado'],
        'cnpj': end['cnpj'],
        'logradouro': end['logradouro'],
        'bairro': end['bairro'],
        'municipio': end['municipio'],
        'uf': end['uf'],
        'cep': end['cep'],
    }
