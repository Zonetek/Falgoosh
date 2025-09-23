import pika
import os
import json
from datetime import datetime

rabbit_user = os.getenv("RABBIT_USER", "")
rabbit_pass = os.getenv("RABBIT_PASSWORD", "")


def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def send_vuln_batches(targets_list, host='rabbitmq'):
    credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
    parameters = pika.ConnectionParameters(
        host=host,
        port=5672,  # use container port
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30,
    )
    
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue='vuln_tasks', durable=True)

    message = {
        'targets': targets_list,
        'timestamp': datetime.now(),
        'batch_id': f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }

    json_data = json.dumps(message, default=json_serializer)

    channel.basic_publish(
        exchange='',
        routing_key='vuln_tasks',
        body=json_data,
        properties=pika.BasicProperties(
            delivery_mode=2,
        )
    )

    print(f"Sent batch with {len(targets_list)} targets")

    connection.close()
