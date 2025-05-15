import pika
import json
import time
import sqlite3

def init_db():
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

def salvar_pedido_sqlite(pedido):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pedidos (cliente, produto_id, nome_produto, quantidade, valor_total)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        pedido['cliente'],
        pedido['produto_id'],
        pedido['nome_produto'],
        pedido['quantidade'],
        pedido['valor_total']
    ))
    conn.commit()
    conn.close()

def callback(ch, method, properties, body):
    print("[x] Recebido pedido:", body.decode())
    pedido = json.loads(body)

    print(f"[PROCESSAMENTO] Validando pedido {pedido['cliente']}")
    print(f"[ESTOQUE] Atualizando estoque para produto ID {pedido['produto_id']}")
    print(f"[NOTA FISCAL] Gerando NF para R${pedido['valor_total']}")

    salvar_pedido_sqlite(pedido)

    enviar_notificacao(pedido)

    ch.basic_ack(delivery_tag=method.delivery_tag)

def enviar_notificacao(pedido):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()
    channel.queue_declare(queue='fila_notificacoes', durable=True)
    msg = f"Pedido de {pedido['cliente']} foi processado com sucesso!"
    channel.basic_publish(
        exchange='',
        routing_key='fila_notificacoes',
        body=msg,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

def iniciar_consumidor():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
            channel = connection.channel()
            channel.queue_declare(queue='fila_pedidos', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='fila_pedidos', on_message_callback=callback)
            print(' [*] Aguardando pedidos...')
            channel.start_consuming()
        except Exception as e:
            print("Erro no consumidor:", e)
            time.sleep(5)

if __name__ == '__main__':
    init_db()
    iniciar_consumidor()