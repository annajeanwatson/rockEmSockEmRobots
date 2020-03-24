
import logging
import boto3
from botocore.exceptions import ClientError
from random import randint


def send_sqs_message(sqs_queue_url, queue_name, msg_body):

    # Send the SQS message
    sqs_client = boto3.resource('sqs')
    queue = sqs_client.get_queue_by_name(QueueName=queue_name)
    try:
        dedup_id = str(randint(0,1e10))
        msg = queue.send_message(QueueUrl=sqs_queue_url,
                                      MessageBody=msg_body, MessageGroupId='string', MessageDeduplicationId=dedup_id)

    except ClientError as e:
        print("ERROR yo!")
        print(e)
        logging.error(e)
        return None
    return msg