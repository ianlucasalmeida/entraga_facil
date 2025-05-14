import pika
import json
import requests
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)
RABBITMQ_HOST = "rabbitmq"  # Nome do serviço definido no docker-compose.yml

# Inicialização do Banco SQLite
def init_db():
    import sqlite3
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            produto_id TEXT,
            nome_produto TEXT,
            quantidade INTEGER,
            valor_total REAL,
            data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# === ROTAS FLASK ===

@app.route('/')
def index():
    return redirect(url_for("loja"))

@app.route('/loja')
def loja():
    return render_template("loja.html")

@app.route('/produto/<int:id>')
def produto(id):
    return render_template("produto.html")

@app.route('/produto/api/<int:id>')
def produto_api(id):
    try:
        response = requests.get(f"https://fakestoreapi.com/products/ {id}")
        return response.json()
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/carrinho')
def carrinho():
    return render_template("carrinho.html")

@app.route('/pedidos')  # Para visualizar todos os pedidos salvos no SQLite
def listar_pedidos():
    import sqlite3
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pedidos')
    rows = cursor.fetchall()
    conn.close()

    pedidos = []
    for row in rows:
        pedidos.append({
            "id": row[0],
            "cliente": row[1],
            "produto_id": row[2],
            "nome_produto": row[3],
            "quantidade": row[4],
            "valor_total": row[5],
            "data_pedido": row[6]
        })
    return pedidos

@app.route('/pedido', methods=['POST'])
def criar_pedido():
    cliente = request.form.get('cliente')
    produto_id = request.form.get('produto_id', '1')
    quantidade = request.form.get('quantidade', '1')

    try:
        produto_resp = requests.get(f"https://fakestoreapi.com/products/ {produto_id}")
        produto = produto_resp.json()
        valor_total = float(produto["price"]) * int(quantidade)

        pedido = {
            "cliente": cliente,
            "produto_id": produto_id,
            "nome_produto": produto["title"],
            "quantidade": quantidade,
            "valor_total": valor_total
        }

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue='fila_pedidos', durable=True)
        channel.basic_publish(
            exchange='',
            routing_key='fila_pedidos',
            body=json.dumps(pedido),
            properties=pika.BasicProperties(delivery_mode=2)  # Persistência da mensagem
        )
        connection.close()
        return "Pedido enviado à fila!"
    except Exception as e:
        return {"erro": str(e)}, 500


# === PONTO DE ENTRADA ===
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)