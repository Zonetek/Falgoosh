import pika
import json
from datetime import datetime


def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def send_vuln_batches(targets_list, host='broker'):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
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
