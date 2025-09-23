import pika
import os
import json
import logging
from . import db_operations

rabbit_user = os.getenv("RABBIT_USER", "")
rabbit_pass = os.getenv("RABBIT_PASSWORD", "")

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logging.info(
            f'[Consumer] Received batch: {data.get("batch_id", "unknown")}')
        logging.info(
            f'[Consumer] Targets count: {len(data.get("targets", []))}')
        logging.info(f'[Consumer] Full data: {data}')

        targets = data.get('targets', [])
        for target in targets:
            logging.info(f'[Consumer] Processing target: {target}')

        db_operations.update_enrichment(targets)

    except Exception as e:
        logging.error(f'[Consumer] Error processing message: {e}')


def get_batches():
    try:
        credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
        parameters = pika.ConnectionParameters(
        host="rabbitmq",
        port=5672,  # use container port
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30,
        )
        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.queue_declare(queue='vuln_tasks', durable=True)

        channel.basic_consume(
            queue= 'vuln_tasks',
            on_message_callback=callback,
            auto_ack=True
        )

        logging.info(
            '[Consumer] Waiting for banner tasks. To exit press CTRL+C')
        channel.start_consuming()

    except Exception as e:
        logging.error(f'[Consumer] Error: {e}')
    finally:
        if 'connection' in locals() and not connection.is_closed:
            connection.close()
