import sqlite3

# Caminho completo para o arquivo database.db
db_path = "H:\\Meu Drive\\2. ANALISE E DESENVOLVIMENTO DE SISTEMAS\\3° SEMESTRE\\DESAFIO TECH EXPERIENCE\\univest-tech-experience-2024-desafios-master\\desafio-1-supermercado-garibaldi\\template-api-python\\src\\database.db"

# Conectar ao banco de dados
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Consultar todos os produtos
cursor.execute("SELECT * FROM produto")
produtos = cursor.fetchall()

# Verificar e imprimir os produtos
if produtos:
    print("Produtos na tabela 'produto':")
    for produto in produtos:
        print(produto)
else:
    print("Nenhum produto encontrado na tabela 'produto'.")

# Fechar a conexão
conn.close()
