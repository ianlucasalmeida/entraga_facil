import pika
import time

def callback(ch, method, properties, body):
    print("[NOTIFICAÇÃO]:", body.decode())
    ch.basic_ack(delivery_tag=method.delivery_tag)

def iniciar_consumidor():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
            channel = connection.channel()
            channel.queue_declare(queue='fila_notificacoes', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='fila_notificacoes', on_message_callback=callback)
            print(' [*] Aguardando notificações...')
            channel.start_consuming()
        except Exception as e:
            print("Erro no consumidor de notificações:", e)
            time.sleep(5)

if __name__ == '__main__':
    iniciar_consumidor()