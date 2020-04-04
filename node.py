# import send, recieve, robotFrontEnd
import time
import random
from typing import *
import boto3
from sqs import send_sqs_message, delete_sqs_message, retrieve_sqs_messages, purge_queues
import sys
import json


# TODO:
# 1. Might need isFollowers to update currentTerm number when isLeader is elected
# 2. Nodes need to use permanent storage

class Node:
    def __init__(self, sqs_info, node_id, candidate = False, isLeader = False, isFollower = True):
        # possible states

        self.isLeader = isLeader
        self.isFollower = isFollower
        self.isCandidate = isCandidate

        self.num_nodes = len(sqs_info)

        self.currentTerm = 0
        self.votedFor = None

        # Need to write these to persistent storage before responding to any message
        self.votes = 0
        self.hasVoted = False
        self.log = []

        self.lastLogIndex = 0
        self.lastLogTerm = 0

        self.sqs_client = boto3.client('sqs', region_name='us-east-2')
        self.sqs_resource = boto3.resource('sqs', region_name='us-east-2')

        self.sqs_info = sqs_info
        self.node_id = node_id


        try:
            purge_queues(self.sqs_client, self.sqs_info[self.node_id]["queue_url"])
        except:
            print("purge timeout...")

        # Setting self.timeout_time
        self.reset_timeout()


    def set_as_candidate(self):
        self.isLeader = False
        self.isFollower = False
        self.isCandidate = True

    def set_as_leader(self):
        self.isLeader = True
        self.isFollower = False
        self.isCandidate = False

    def set_as_follower(self):
        self.isLeader = False
        self.isFollower = True
        self.isCandidate = False

    def send_message_to_all_other_nodes(self, message: str):

        for node in self.sqs_info:
            if node["id"] == self.node_id:
                continue
            send_sqs_message(self.sqs_resource, node["queue_url"], node["queue_name"], message)

    def send_message_to_one_node(self, node_id: int, message: str):
        node = self.sqs_info[node_id]
        send_sqs_message(self.sqs_resource, node["queue_url"], node["queue_name"], message)

    def check_timeout(self) -> bool:
        return time.time() >= self.timeout_time

    def reset_timeout(self) -> None:
        self.timeout_time = time.time() + random.uniform(15, 40)

    def check_if_won(self) -> bool:

        if self.votes/self.num_nodes >= 0.5:
            return True
        else:
            return False

    def send_heartbeats(self):

        msg = {"type": "heartbeat", "node_id": self.node_id, "currentTerm": self.currentTerm}
        self.send_message_to_all_other_nodes(json.dumps(msg))

    def process_latest_message(self):
        
        raw_message = retrieve_sqs_messages(self.sqs_client, self.sqs_info[self.node_id]["queue_url"])

        if raw_message is None:
            return
        message = json.loads(raw_message)

        print("Incoming message: " + raw_message)

        if message["type"] == "vote":
            self.votes += 1
            # if it's the majority (3) you win self.isLeader = true

        elif message["type"] == "heartbeat":

            if self.isCandidate == True:
                if message["currentTerm"] >= self.currentTerm:
                    self.set_as_follower()
                    self.reset_timeout()
            else:
                self.reset_timeout()

            self.hasVoted = False

        elif message["type"] == "RequestVotes":

            if self.hasVoted == False:
                vote_msg = {"type": "vote", "node_id": self.node_id, "currentTerm": self.currentTerm, "lastLogIndex": self.lastLogIndex, "lastLogTerm": self.lastLogTerm}

                print("Outgoing message: " + json.dumps(vote_msg))
                self.send_message_to_one_node(message["node_id"], json.dumps(vote_msg))
                self.hasVoted = True 

        elif message["type"] == "AppendEntries":
            pass

            
    def process_client_message(self):

        raw_message = retrieve_sqs_messages(self.sqs_client, self.sqs_info["leader"]["queue_url"])

        if raw_message is None:
            return

        message = json.loads(raw_message)

        entry = {"currentTerm": self.currentTerm, "index": len(self.log), "command": message}
        
        self.log.append(entry)

        appendEntryMsg = {"type": "AppendEntries", "node_id": self.node_id, "entry": entry, "currentTerm": self.currentTerm}

        print("Outgoing message: " + json.dumps(appendEntryMsg))

        self.send_message_to_all_other_nodes(json.dumps(appendEntryMsg))


    def main_loop(self):

        while True:
            print("")

            # Check messages
            self.process_latest_message()

            # Timed out, start new election!
            if self.check_timeout() and self.isLeader == False:

                print("I've timed out!!!!")
                print("Starting election")

                self.currentTerm += 1
                self.votes = 1 # reset votes to just yourself
                self.reset_timeout()
                self.set_as_candidate()
                self.hasVoted = False

                # send request for vote messages to all other nodes
                msg = {"type": "RequestVotes", "node_id": self.node_id, "currentTerm": self.currentTerm}
                self.send_message_to_all_other_nodes(json.dumps(msg))


            # Check if we've won election
            if self.isCandidate == True:

                # Check for incoming votes
                if self.check_if_won():
                    print("Won election!")
                    self.set_as_leader()
                    print("Sending heartbeat after election")
                    self.send_heartbeats()


            if self.isLeader == True:

                # Send heartbeat to other nodes
                print("Sending heartbeat")
                self.send_heartbeats()

            # If isLeader send hearbeat
            # Check for messages
            # 
            # 
 
if __name__ == "__main__":

    node_id = int(sys.argv[1])

    with open('ec2_setup.json') as f:
        CONFIG = json.load(f)

    myNode = Node(CONFIG["nodes"], node_id)
    myNode.main_loop()