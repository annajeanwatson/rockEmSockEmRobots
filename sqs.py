import logging
import boto3
from botocore.exceptions import ClientError
import time
import json
from random import randint

def retrieve_sqs_messages(sqs_client, sqs_queue_url, num_msgs=1, wait_time=0, visibility_time=1):

    # Assign this value before running the program
    num_messages = 1

    # Retrieve messages from an SQS queue
    try:
        msgs = sqs_client.receive_message(QueueUrl=sqs_queue_url,
                                          MaxNumberOfMessages=num_msgs,
                                          WaitTimeSeconds=wait_time,
                                          VisibilityTimeout=visibility_time)
        if "Messages" not in msgs:
            return None

        # string message 
        msg = msgs["Messages"][0]

        # Remove the message from the queue
        sqs_client.delete_message(QueueUrl=sqs_queue_url,
                                ReceiptHandle=msg['ReceiptHandle'])
        return msg["Body"]
        

    except ClientError as e:
        print(e)
        logging.error(e)
        return None


def send_sqs_message(sqs_resource, sqs_queue_url, queue_name, msg_body):

    # Send the SQS message
    queue = sqs_resource.get_queue_by_name(QueueName=queue_name)
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

def purge_queues(sqs_client, queue_url):

    try:
        response = sqs_client.purge_queue(QueueUrl=queue_url)
        return response
    except:
        print("purge timeout...")
