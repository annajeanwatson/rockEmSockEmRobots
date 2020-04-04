import json
import sys
import threading

class RobotClient:
    def __init__(self, client_id):
        self.client_id =  client_id
        self.isBlockingWithLeft = False
        self.isBlockingWithRight = False

    def setIsBlockingWithLeft(boolean):
        self.isBlockingWithLeft = boolean
    
    def getIsBlockingWithLeft(boolean):
        return self.isBlockingWithLeft 

    def setIsBlockingWithRight(boolean):
        self.isBlockingWithRight = boolean
    
    def getIsBlockingWithRight(boolean):
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

            pass

        if user_input == "q":

            pass

        if user_input == "a":

            pass
        
        if user_input == "s":

           pass

def retrieve_sqs_messages(sqs_client, sqs_queue_url, num_msgs=1, wait_time=1, visibility_time=5):

    # Assign this value before running the program
    num_messages = 1
    while True:
        # Retrieve messages from an SQS queue
        try:
            msgs = sqs_client.receive_message(QueueUrl=sqs_queue_url,
                                              MaxNumberOfMessages=num_msgs,
                                              WaitTimeSeconds=wait_time,
                                              VisibilityTimeout=visibility_time)
            if "Messages" in msgs:
                for msg in msgs["Messages"]:

                    # string message 
                    msg_json = msg["Body"]

                    # Remove the message from the queue
                    delete_sqs_message(sqs_client, sqs_queue_url, msg['ReceiptHandle'])

                    # function call        

       except ClientError as e:
            print(e)
            logging.error(e)

def delete_sqs_message(sqs_client, sqs_queue_url, msg_receipt_handle):

    # Delete the message from the SQS queue
    sqs_client.delete_message(QueueUrl=sqs_queue_url,
                              ReceiptHandle=msg_receipt_handle)

def purge_queues(sqs_client, queue_url):

    response = sqs_client.purge_queue(QueueUrl=queue_url)
    return response

if __name__ == "__main__":


    client_id = int(sys.argv[1])

    with open('ec2_setup.json') as f:
        CONFIG = json.load(f)

    # recieveing     
    sqs_queue_url = CONFIG["clients"][queue_url]
    sqs_client = boto3.client('sqs', region_name='us-east-2')

    listenerThread = threading.Thread(target =retrieve_sqs_messages, args=(sqs_client, sqs_queue_url, num_msgs=1, wait_time=1, visibility_time=5)):

    # sending 
    sqs_resource = boto3.resource('sqs', region_name='us-east-2')
    leader_queue = CONFIG["leader"]
    my_queue = CONFIG["clients"][client_id]



    # my_queue["queue_url"]
    # my_queue["queue_name"]

    # leader_queue["queue_url"]
    # leader_queue["queue_name"]

    # {"data": "block_left", "client": 0}

    inputMenu()

