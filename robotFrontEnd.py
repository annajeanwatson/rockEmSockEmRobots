import json
import sys
import threading
import boto3
import random
import logging
from botocore.exceptions import ClientError
import time
from sqs import *

class RobotClient:

    def __init__(self, client_id, sqs_info):

        self.client_id = client_id
        self.sqs_info = sqs_info

        # Can be "bl", "br", "pl", "pr"
        self.state = None

        self.sqs_client = boto3.client('sqs', region_name='us-east-2')
        self.sqs_resource = boto3.resource('sqs', region_name='us-east-2')

        self.punch_timeout_time = time.time()

        purge_queues(self.sqs_client, self.sqs_info["clients"][self.client_id]["queue_url"])

    def reset_punch_timeout(self, seconds):

        self.punch_timeout_time = time.time() + seconds

    def check_punch_timeout(self):

        return time.time() < self.punch_timeout_time

    def punch_with_left(self):

        if self.check_punch_timeout():
            print("Can only punch once per second or three seconds after being blocked!")
            return False

        self.state = "pl"
        self.reset_punch_timeout(1)
        return True

    def punch_with_right(self):

        if self.check_punch_timeout():
            print("Can only punch once per second or three seconds after being blocked!")
            return False

        self.state = "pr"
        self.reset_punch_timeout(1)
        return True

    def block_with_left(self):

        self.state = "bl"
        return True

    def block_with_right(self):

        self.state = "br"
        return True


    def process_opponent_action(self, opponent_state):

        if opponent_state == "br":
            print("Opponent blocked with right!")
            return False

        if opponent_state == "bl":
            print("Opponent blocked with left!")
            return False

        if opponent_state == "pr" and self.state == "bl":

            print("Opponent threw a right punch, but it was blocked!")
            return False

        if opponent_state == "pl" and self.state == "br":

            print("Opponent threw a left punch, but it was blocked!")
            return False

        # Successful punch, return hit with prob
        isHit = random.random() < .1

        if isHit:
            print("Opponent threw a punch and it landed! GAME OVER!")
        else:
            print("Opponent threw a punch and but it missed!")

        return isHit

    # TODO: need to implement logic that times out punching for three seconds after being blocked

    def listen_for_messages(self):

        while True:

            raw_message = retrieve_sqs_messages(self.sqs_client, self.sqs_info["clients"][self.client_id]["queue_url"])

            if raw_message is None:
                continue

            print("Incoming: " + raw_message)
            message = json.loads(raw_message)

            if message["type"] != "commitConfirm":
                print("ERRROR what type of message is this?")
                return

            command = message["command"]

            # Process opponent state
            if command["client_id"] != self.client_id and command["state"] is not None:
                self.process_opponent_action(command["state"])


    def send_state_to_leader(self):

        msg_json = {"type": "Action", "state": self.state, "client_id": self.client_id}

        print("Outgoing: " + json.dumps(msg_json))
        send_sqs_message(self.sqs_resource, self.sqs_info["leader"]["queue_url"], self.sqs_info["leader"]["queue_name"], json.dumps(msg_json))

def inputMenu(robotClient):

    while True:

        print("")
        print("Please select from the following menu:")
        print("q. Left Punch") 
        print("w. Right Punch") 
        print("a. Block Left")
        print("s. Block Right")
        print("")

        user_input = input()

        if user_input == "w":

            actionSuccessful = robotClient.punch_with_right()
            if not actionSuccessful:
                continue

        if user_input == "q":

            actionSuccessful = robotClient.punch_with_left()
            if not actionSuccessful:
                continue

        if user_input == "a":
            robotClient.block_with_left()
        
        if user_input == "s":
            robotClient.block_with_right()

        robotClient.send_state_to_leader()

if __name__ == "__main__":

    client_id = int(sys.argv[1])

    with open('ec2_setup.json') as f:
        CONFIG = json.load(f)

    robotClient = RobotClient(client_id, CONFIG)

    # listening thread starting
    listenerThread = threading.Thread(target = robotClient.listen_for_messages)
    listenerThread.start()

    # run main loop
    inputMenu(robotClient)