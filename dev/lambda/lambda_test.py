import json
import pika
import os
import datetime

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT', 5672)
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)

parameters = pika.ConnectionParameters(credentials=credentials, host=RABBITMQ_HOST, virtual_host=RABBITMQ_PORT) 

def lambda_handler(event, context):
    print("Received S3 event:", json.dumps(event, indent=2))
    
    connection = pika.BlockingConnection(parameters)
    
    channel = connection.channel()
    channel.basic_publish(exchange='', routing_key='hello', body=f'Hello World! It is {datetime.datetime.now()}')
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }