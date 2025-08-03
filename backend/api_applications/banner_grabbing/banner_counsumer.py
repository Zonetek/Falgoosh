import pika
import json
import logging

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        logging.info(f'[Consumer] Received batch: {data.get("batch_id", "unknown")}')
        logging.info(f'[Consumer] Targets count: {len(data.get("targets", []))}')
        logging.info(f'[Consumer] Full data: {data}')
        
        targets = data.get('targets', [])
        for target in targets:
            logging.info(f'[Consumer] Processing target: {target}')
            
    except Exception as e:
        logging.error(f'[Consumer] Error processing message: {e}')

def get_batches():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('broker'))
        channel = connection.channel()

        channel.queue_declare(queue='banner_tasks', durable=True)

        channel.basic_consume(
            queue='banner_tasks',
            on_message_callback=callback,
            auto_ack=True
        )

        logging.info('[Consumer] Waiting for banner tasks. To exit press CTRL+C')
        channel.start_consuming()
        
    except Exception as e:
        logging.error(f'[Consumer] Error: {e}')
    finally:
        if 'connection' in locals() and not connection.is_closed:
            connection.close()
