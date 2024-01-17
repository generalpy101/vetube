import time
import boto3
import dotenv
import os
import logging
import requests
import pika

logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv()

SLEEP_TIME_BEFORE_RETRY = 5

# Localstack configuration
LOCALSTACK_URL = os.getenv('LOCALSTACK_URL', 'http://localhost:4566')
logging.info(f'Using LocalStack at {LOCALSTACK_URL}')

# S3 configuration
BUCKET_NAME = os.getenv('BUCKET_NAME', 'vetube')

# Lambda configuration
LAMBDA_FUNCTION_NAME = os.getenv('LAMBDA_FUNCTION_NAME', 'handle-video-upload')
LAMBDA_HANDLER = os.getenv('LAMBDA_HANDLER', 'lambda_function.lambda_handler')
LAMBDA_FUNCTION_PATH = os.getenv('LAMBDA_FUNCTION_PATH', os.path.join('.', 'lambda', 'lambda_publish_to_rabbitmq.zip'))
LAMBDA_ROLE_ARN = os.getenv('LAMBDA_ROLE_ARN', 'arn:aws:iam::000000000000:role/irrelevant')

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT', 5672)
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')

os.environ['AWS_DEFAULT_REGION'] = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

def wait_for_localstack():
    # Wait for LocalStack to be ready
    max_attempts = 10
    current_attempt = 0
    logging.info('Waiting for LocalStack to be ready...')
    while current_attempt < max_attempts:
        try:
            resp = requests.get(LOCALSTACK_URL)
            if resp.status_code == 200:
                logging.info('LocalStack is ready!')
            break
        except Exception:
            logging.info(f'LocalStack is not ready yet. Retrying in {SLEEP_TIME_BEFORE_RETRY} second...')
            logging.info(f'Attempt {current_attempt} of {max_attempts}')
            current_attempt += 1
            time.sleep(SLEEP_TIME_BEFORE_RETRY)
    else:
        logging.error('LocalStack is not ready. Aborting...')
        exit(1)
        
def wait_for_rabbitmq():
    # Wait for RabbitMQ to be ready
    max_attempts = 10
    current_attempt = 0
    logging.info('Waiting for RabbitMQ to be ready...')
    while current_attempt < max_attempts:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
            connection.close()
            logging.info('RabbitMQ is ready!')
            break
        except Exception:
            logging.info(f'RabbitMQ is not ready yet. Retrying in {SLEEP_TIME_BEFORE_RETRY} second...')
            logging.info(f'Attempt {current_attempt} of {max_attempts}')
            current_attempt += 1
            time.sleep(SLEEP_TIME_BEFORE_RETRY)
    else:
        logging.error('RabbitMQ is not ready. Aborting...')
        exit(1)

def create_s3_bucket():
    # Create S3 bucket
    logging.info(f'Creating S3 bucket {BUCKET_NAME}...')
    s3 = boto3.client(
        's3',
        endpoint_url=LOCALSTACK_URL,
        aws_access_key_id='irrelevant',
        aws_secret_access_key='irrelevant'
    )
    s3.create_bucket(Bucket=BUCKET_NAME)
    
    # Check if bucket was created
    logging.info(f'Checking if S3 bucket {BUCKET_NAME} was created...')
    while True:
        try:
            s3.list_objects_v2(Bucket=BUCKET_NAME)
            break
        except Exception:
            logging.info(f'S3 bucket {BUCKET_NAME} was not created yet. Retrying in {SLEEP_TIME_BEFORE_RETRY} second...')
            time.sleep(SLEEP_TIME_BEFORE_RETRY)

def create_lambda_function():
    # Create Lambda function
    lambda_client = boto3.client(
        'lambda',
        endpoint_url=LOCALSTACK_URL,
        aws_access_key_id='irrelevant',
        aws_secret_access_key='irrelevant'
    )
    logging.info(f'Creating Lambda function {LAMBDA_FUNCTION_NAME}...')
    lambda_client.create_function(
        FunctionName=LAMBDA_FUNCTION_NAME,
        Runtime='python3.8',
        Role=LAMBDA_ROLE_ARN,
        Handler=LAMBDA_HANDLER,
        Code={
            'ZipFile': _aws_file_as_bytes(LAMBDA_FUNCTION_PATH)
        },
    )
    
    logging.info(f'Adding permission to Lambda function {LAMBDA_FUNCTION_NAME}...')
    # Add permussion to Lambda function to be invoked by S3
    lambda_client.add_permission(
        FunctionName=LAMBDA_FUNCTION_NAME,
        StatementId='1',
        Action='lambda:InvokeFunction',
        # Principal for localstack
        Principal='s3.amazonaws.com',
        SourceArn=f'arn:aws:s3:::{BUCKET_NAME}',
    )
    time.sleep(5)

def configure_s3_event():
    # Configure S3 event on Lambda
    s3 = boto3.client(
        's3',
        endpoint_url=LOCALSTACK_URL,
        aws_access_key_id='irrelevant',
        aws_secret_access_key='irrelevant'
    )
    
    lambda_function_arn = f'arn:aws:lambda:us-east-1:000000000000:function:{LAMBDA_FUNCTION_NAME}'
    
    logging.info(f'Configuring S3 event on Lambda {lambda_function_arn}...')
    s3.put_bucket_notification_configuration(
        Bucket=BUCKET_NAME,
        NotificationConfiguration={
            'LambdaFunctionConfigurations': [
                {
                    'LambdaFunctionArn': lambda_function_arn,
                    'Events': ['s3:ObjectCreated:*']
                }
            ]
        }
    )
    
def _aws_file_as_bytes(file_name):
    with open(file_name, 'rb') as f:
        return f.read()

if __name__ == "__main__":
    wait_for_rabbitmq()
    wait_for_localstack()
    create_s3_bucket()
    create_lambda_function()
    configure_s3_event()
    
    logging.info('Local dev environment is ready to be used!')
