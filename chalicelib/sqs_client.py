import boto3
import logging
import os

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOG_LEVEL', logging.INFO))


class SQSClientException(Exception):
    pass


class SQSQueueNotFoundException(SQSClientException):
    pass


class SQSClient:

    def __init__(self, queue_name, region='us-east-1'):
        self.sqs_client = boto3.client('sqs', region_name=region)
        self.queue_name = queue_name
        logger.debug(f'Connecting to SQS queue [{queue_name}] in region [{region}]')
        try:
            self.queue_url = self.sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
        except self.sqs_client.exceptions.QueueDoesNotExist:
            logger.error(f'Unable to find SQS queue [{queue_name}] in region [{region}]')
            raise SQSQueueNotFoundException(queue_name)

    def send_message(self, body):
        logger.debug(f'Sending to SQS queue [{self.queue_name}] with body [{body}] ')
        response = self.sqs_client.send_message(QueueUrl=self.queue_url, MessageBody=body)
        logger.debug(f'SQS send message response [{response}]')
        return response

    def change_visibility_timeout(self, receipt_handle, timeout):
        self.sqs_client.change_message_visibility(
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=timeout
        )
