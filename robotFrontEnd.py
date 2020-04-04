import json
import sys
import threading
import boto3
from random import randint
import logging
from botocore.exceptions import ClientError
import ast
import sqs


class RobotClient:
    def __init__(self, client_id):
        self.client_id =  client_id
        self.isBlockingWithLeft = False
        self.isBlockingWithRight = False

    def setIsBlockingWithLeft(self, boolean):
        self.isBlockingWithLeft = boolean
    
    def getIsBlockingWithLeft(self, boolean):
        return self.isBlockingWithLeft 

    def setIsBlockingWithRight(self, boolean):
        self.isBlockingWithRight = boolean
    
    def getIsBlockingWithRight(self, boolean):
        return self.isBlockingWithRight

def inputMenu():

    while True:

        print("")
        print("Please select from the following menu:")
        print("w. Right Punch") 
        print("q. Left Punch") 
        print("a. Block Left")
        print("s. Block Right")
        print("")

        user_input = input()

        if user_input == "w":
            # robots can only be blocking until their next move
            if robotClient.getIsBlockingWithRight == True:
                robotClient.setIsBlockingWithRight == False
            if robotClient.getIsBlockingWithLeft == True:
                robotClient.setIsBlockingWithLeft == False
            msg_body = '{{"data": "punch_right", "client": {client_id}}}'.format(client_id=int(client_id))
            send_sqs_message(sqs_resource, leader_queue_url, leader_queue_name, msg_body)

        if user_input == "q":
            # robots can only be blocking until their next move
            if robotClient.getIsBlockingWithRight == True:
                robotClient.setIsBlockingWithRight == False
            if robotClient.getIsBlockingWithLeft == True:
                robotClient.setIsBlockingWithLeft == False
            msg_body = '{{"data": "punch_left", "client": {client_id}}}'.format(client_id=int(client_id))
            send_sqs_message(sqs_resource, leader_queue_url, leader_queue_name, msg_body)

        if user_input == "a":
            # robots can only be blocking until their next move
            if robotClient.getIsBlockingWithRight == True:
                robotClient.setIsBlockingWithRight == False
            robotClient.setIsBlockingWithLeft(True)
            msg_body = '{{"data": "block_left", "client": {client_id}}}'.format(client_id=int(client_id))
            send_sqs_message(sqs_resource, leader_queue_url, leader_queue_name, msg_body)
        
        if user_input == "s":
            # robots can only be blocking until their next move
            if robotClient.getIsBlockingWithLeft == True:
                robotClient.setIsBlockingWithLeft == False
            robotClient.setIsBlockingWithRight(True)
            msg_body = '{{"data": "block_right", "client": {client_id}}}'.format(client_id=int(client_id))
            send_sqs_message(sqs_resource, leader_queue_url, leader_queue_name, msg_body)
            

def retrieve_sqs_messages(sqs_client, sqs_queue_url, num_msgs=1, wait_time=1, visibility_time=5):
    # Assign this value before running the program
    num_messages = 1
    while True:
        # Retrieve messages from an SQS queue
        msgs = sqs_client.receive_message(QueueUrl=sqs_queue_url,
                                              MaxNumberOfMessages=num_msgs,
                                              WaitTimeSeconds=wait_time,
                                              VisibilityTimeout=visibility_time)
        if "Messages" in msgs:
            for msg in msgs["Messages"]:

                # string message 
                msg_json = msg["Body"]
                # covert body of message to a dictionary
                D2=ast.literal_eval(msg_json)
                handle_recieve(D2)
                 # Remove the message from the queue
                delete_sqs_message(sqs_client, sqs_queue_url, msg['ReceiptHandle'])

                    

def delete_sqs_message(sqs_client, sqs_queue_url, msg_receipt_handle):

    # Delete the message from the SQS queue
    sqs_client.delete_message(QueueUrl=sqs_queue_url,
                              ReceiptHandle=msg_receipt_handle)

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

    response = sqs_client.purge_queue(QueueUrl=queue_url)
    return response

def handle_recieve(dicti):
    if dicti["data"] == "block_left" and dicti["client"] != client_id:
        print('yay')
    elif dicti["data"] == "block_right" and dicti["client"] != client_id:
        pass
    elif dicti["data"] == "punch_left" and dicti["client"] != client_id:
        pass
    elif dicti["data"] == "punch_right" and dicti["client"] != client_id:
        pass

if __name__ == "__main__":


    client_id = int(sys.argv[1])

    with open('ec2_setup.json') as f:
        CONFIG = json.load(f)

    # recieveing     
    '''  for client in CONFIG["clients"]:
        if client["id"] == client_id:
            sqs_queue_url = client["queue_url"]'''
    sqs_queue_url = CONFIG["clients"][client_id]["queue_url"]

    print(sqs_queue_url)
    sqs_client = boto3.client('sqs', region_name='us-east-2')

    sqs.purge_queues(sqs_client, CONFIG["leader"]["queue_url"])

    # listening thread starting
    listenerThread = threading.Thread(target =retrieve_sqs_messages, args=(sqs_client, sqs_queue_url, 1, 1, 5))
    listenerThread.start()

    # sending 
    sqs_resource = boto3.resource('sqs', region_name='us-east-2')
    leader_queue_url = CONFIG["leader"]["queue_url"]
    leader_queue_name = CONFIG["leader"]["queue_name"]
    #my_queue = CONFIG["clients"][client_id]

    #msg_body = '{"data": "block_left", "client": 0}'

    #send_sqs_message(sqs_resource, leader_queue_url, leader_queue_name, msg_body)

    # create a robot client to store data 
    robotClient = RobotClient(client_id)

    # run main loop
    inputMenu()






    # my_queue["queue_url"]
    # my_queue["queue_name"]

    # leader_queue["queue_url"]
    # leader_queue["queue_name"]

    # {"data": "block_left", "client": 0}



    #inputMenu()

