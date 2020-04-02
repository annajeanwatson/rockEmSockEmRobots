import logging
import boto3
from botocore.exceptions import ClientError
from send import send_sqs_message
import time
import json

def retrieve_sqs_messages(sqs_queue_url, sqs_client, num_msgs=1, wait_time=1, visibility_time=5):

    # Retrieve messages from an SQS queue
    try:
        msgs = sqs_client.receive_message(QueueUrl=sqs_queue_url,
                                          MaxNumberOfMessages=num_msgs,
                                          WaitTimeSeconds=wait_time,
                                          VisibilityTimeout=visibility_time)
    except ClientError as e:
        print(e)
        logging.error(e)
        return None

    # Return the list of retrieved messages
    if msgs != None:
        if 'Messages' in msgs:
            #print(msgs)
            return msgs['Messages']


def delete_sqs_message(sqs_queue_url, msg_receipt_handle):

    # Delete the message from the SQS queue
    sqs_client = boto3.client('sqs')
    sqs_client.delete_message(QueueUrl=sqs_queue_url,
                              ReceiptHandle=msg_receipt_handle)


def initListener(sqs_queue_url, dist_dict, CONFIG):

    # Assign this value before running the program
    num_messages = 1
    sqs_client = boto3.client('sqs')

    while True:
        time.sleep(2)
        # Retrieve SQS messages
        msgs = retrieve_sqs_messages(sqs_queue_url, sqs_client, num_messages)
        if msgs is not None:
            for msg in msgs:

                msg_json = json.loads(msg["Body"])

                # recieve logic here 

                # Remove the message from the queue
                delete_sqs_message(sqs_queue_url, msg['ReceiptHandle'])