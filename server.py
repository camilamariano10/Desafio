from sqlite3 import connect, Connection, Row, Cursor
from flask import Flask, jsonify, Response, request, render_template
from datetime import datetime, timedelta
import pandas as pd
from sklearn.linear_model import LinearRegression
from flask_cors import CORS

# Banco de Dados
DATABASE = "database.db"

def connection_database() -> Connection:
    """Cria e retorna uma conexão com o Banco de Dados"""
    connection = connect(DATABASE)
    connection.row_factory = Row
    return connection

# Servidor Flask
app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    """Renderiza a página principal"""
    return render_template("index.html")

# Funções das rotas para relatório de vendas, alertas de validade e previsão de demanda
@app.get("/api/sales-report")
def sales_report() -> tuple[Response, int]:
    """Relatório de vendas por período"""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        return jsonify({"error": "Datas de início e fim são obrigatórias"}), 400

    # Convertendo as datas de string para timestamp em milissegundos
    try:
        start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
        end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)
    except ValueError:
        return jsonify({"error": "Formato de data inválido. Use AAAA-MM-DD"}), 400

    try:
        db = connection_database()
        query = """
            SELECT p.nome AS produto, p.estoqueAtual AS quantidade_estoque, 
                   SUM(vp.quantidadeProduto) AS quantidade_vendida,
                   SUM(vp.quantidadeProduto * vp.precoVenda) AS total_vendas
            FROM vendaProduto AS vp
            JOIN produto AS p ON vp.produtoId = p.id
            JOIN venda AS v ON vp.vendaId = v.id
            WHERE v.dataVenda BETWEEN ? AND ?
            GROUP BY p.id
            ORDER BY quantidade_vendida DESC
        """
        cursor = db.execute(query, (start_timestamp, end_timestamp))
        sales_data = cursor.fetchall()

        return jsonify([dict(item) for item in sales_data]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/expiration-alerts")
def expiration_alerts():
    """Alerta de produtos próximos da validade"""
    try:
        conn = connection_database()
        cursor = conn.cursor()

        today = datetime.now()
        alert_date = today + timedelta(days=7)

        query = "SELECT nome, estoqueAtual AS quantidade_estoque, dataValidade FROM produto WHERE dataValidade <= ?"
        cursor.execute(query, (alert_date,))
        products = cursor.fetchall()

        return jsonify([
            {"produto": prod["nome"], "estoque": prod["quantidade_estoque"], "data_validade": prod["dataValidade"]}
            for prod in products
        ]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/api/demand-forecast")
def demand_forecast() -> tuple[Response, int]:
    """Previsão de demanda com base em vendas passadas"""
    try:
        forecast_period = request.args.get("forecast_period", default=30, type=int)
        db = connection_database()

        query = """
            SELECT p.nome AS produto, v.dataVenda AS data_venda, SUM(vp.quantidadeProduto) AS quantidade_vendida
            FROM vendaProduto AS vp
            JOIN produto AS p ON vp.produtoId = p.id
            JOIN venda AS v ON vp.vendaId = v.id
            GROUP BY p.id, v.dataVenda
            ORDER BY v.dataVenda
        """

        print("Executando consulta de previsão de demanda...")
        sales_data = pd.read_sql_query(query, db)
        print("Dados recuperados da consulta:", sales_data)

        if sales_data.empty:
            print("Nenhum dado foi recuperado da consulta.")
            return jsonify([]), 200

        forecasts = []

        for product, group_data in sales_data.groupby("produto"):
            print(f"Processando previsões para o produto: {product}")
            print("Dados do grupo:", group_data)
            print("Tipos de dados:", group_data.dtypes)

            try:
                # Tenta converter `data_venda` para datas, utilizando `errors='coerce'` para lidar com valores inválidos
                group_data["data_venda"] = pd.to_datetime(group_data["data_venda"], errors='coerce')

                # Verifica se há valores `NaT` após a conversão e os remove
                if group_data["data_venda"].isnull().any():
                    print(f"Dados de data inválidos encontrados para {product}. Ignorando essas entradas.")
                    group_data = group_data.dropna(subset=["data_venda"])

                # Confirma novamente se há dados suficientes após a limpeza
                if len(group_data) < 2:
                    print(f"Dados insuficientes para previsão de {product} após limpeza de dados.")
                    continue

                # Calcula a coluna `dias` a partir da primeira data de venda
                group_data["dias"] = (group_data["data_venda"] - group_data["data_venda"].min()).dt.days
                X = group_data[["dias"]]
                y = group_data["quantidade_vendida"]

                model = LinearRegression()
                model.fit(X, y)
                future_days = X["dias"].max() + forecast_period
                predicted_demand = model.predict([[future_days]])[0]

                forecasts.append({
                    "produto": product,
                    "previsao_demanda": round(predicted_demand),
                    "recomendacao_reabastecimento": max(0, round(predicted_demand) - group_data["quantidade_vendida"].iloc[-1])
                })
            except Exception as e:
                print(f"Erro ao processar previsão para {product}: {e}")
                continue

        return jsonify(forecasts), 200
    except Exception as e:
        import traceback
        error_message = str(e)
        traceback.print_exc()  # Imprime a stack trace completa no terminal para diagnóstico
        return jsonify({"error": f"Erro interno no servidor: {error_message}"}), 500




if __name__ == "__main__":
    app.run(debug=True, port=8080)
