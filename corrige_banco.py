import sqlite3
import os

# Caminho para o banco de dados
db_path = "H:\\Meu Drive\\2. ANALISE E DESENVOLVIMENTO DE SISTEMAS\\3° SEMESTRE\\DESAFIO TECH EXPERIENCE\\univest-tech-experience-2024-desafios-master\\desafio-1-supermercado-garibaldi\\template-api-python\\src\\database.db"

# Verificar se o arquivo existe
if not os.path.exists(db_path):
    print("Erro: O arquivo do banco de dados não foi encontrado.")
else:
    # Conectar ao banco de dados e corrigir a estrutura da tabela
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verificar se a coluna 'quantidade_estoque' existe
    cursor.execute("PRAGMA table_info(produto)")
    columns = cursor.fetchall()

    # Verificar e adicionar as colunas 'quantidade_estoque' e 'data_validade' se necessário
    column_names = [column[1] for column in columns]
    if 'quantidade_estoque' not in column_names:
        cursor.execute("ALTER TABLE produto ADD COLUMN quantidade_estoque INTEGER")
        print("Coluna 'quantidade_estoque' adicionada com sucesso.")
    else:
        print("A coluna 'quantidade_estoque' já existe na tabela.")

    if 'data_validade' not in column_names:
        cursor.execute("ALTER TABLE produto ADD COLUMN data_validade DATE")
        print("Coluna 'data_validade' adicionada com sucesso.")
    else:
        print("A coluna 'data_validade' já existe na tabela.")

    # Confirmar e fechar a conexão
    conn.commit()
    conn.close()
