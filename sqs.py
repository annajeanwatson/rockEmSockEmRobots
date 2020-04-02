import logging
import boto3
from botocore.exceptions import ClientError
import time
import json
from random import randint

def retrieve_sqs_messages(sqs_client, sqs_queue_url, num_msgs=1, wait_time=1, visibility_time=5):

    # Assign this value before running the program
    num_messages = 1

    # Retrieve messages from an SQS queue
    try:
        msgs = sqs_client.receive_message(QueueUrl=sqs_queue_url,
                                          MaxNumberOfMessages=num_msgs,
                                          WaitTimeSeconds=wait_time,
                                          VisibilityTimeout=visibility_time)
        # print(msgs)
        if msgs is not None:
            for msg in msgs["Messages"]:

                # string message 
                msg_json = msg["Body"]

                # Remove the message from the queue
                delete_sqs_message(sqs_client, sqs_queue_url, msg['ReceiptHandle'])
                return msg_json

    except ClientError as e:
        print(e)
        logging.error(e)
        return None


def delete_sqs_message(sqs_client, sqs_queue_url, msg_receipt_handle):

    # Delete the message from the SQS queue
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

                dist_dict.receive(msg_json)

                # Remove the message from the queue
                delete_sqs_message(sqs_queue_url, msg['ReceiptHandle'])
                conflict_occured = dist_dict.fix_meeting_conflicts()

                if conflict_occured:
                    # print("Conflict on receive, updating!")
                    for node in CONFIG["nodes"]:
                        if node["id"] != dist_dict.node_id:
                            message = dist_dict.send(node["id"])
                            send_sqs_message(node["queue_url"], node["queue_name"], json.dumps(message))



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