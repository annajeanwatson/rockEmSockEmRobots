# import send, recieve, robotFrontEnd
import time
import random
from typing import *
import boto3
from sqs import send_sqs_message, delete_sqs_message, retrieve_sqs_messages, purge_queues
import sys
import json

class Node:
    def __init__(self, sqs_info, node_id, candidate = False, leader = False, follower = True):
        # possible states

        '''Can receive:
		1. Client requests
		2. ACKs from followers
        
        Can send:
		1. Heartbeats to maintain authority
		2. AppendLog RPCs to servers
		3. Response to client'''
        self.leader = leader
        self.num_nodes = len(sqs_info)

        '''Can receive:
		1. RequestVote RPCs --> refuse
		2. RequestVote RPC Responses -> processCollectVote
		3. Heartbeat --> Follower

	    Can send:
		1. RequestVote RPCs'''
        self.candidate = candidate

        '''Can receive:
		1. Heartbeats from leader (reset timeout)
		2. RequestVote RPCs (if haven't voted and candidate term is better or log is longer, vote for them)
		3. Client request -> redirect to leader
		4. AppendLog RPCs
	    Can send:
		1. Response to RequestVote'''

        self.term = 0

        self.votes = 0
        self.hasVoted = False

        # should initalize as a follower
        self.follower = follower

        # Setting self.timeout_time
        self.reset_timeout()

        self.sqs_client = boto3.client('sqs', region_name='us-east-2')
        self.sqs_resource = boto3.resource('sqs', region_name='us-east-2')

        self.sqs_info = sqs_info
        self.node_id = node_id

        self.log = []

        try:
            purge_queues(self.sqs_client, self.sqs_info[self.node_id]["queue_url"])
        except:
            print("purge timeout...")

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

    def isLeader(self):
        if (self.leader == True):
            return True
        else:
            return False

    def set_as_candidate(self):
        self.leader = False
        self.follower = False
        self.candidate = True

    def set_as_leader(self):
        self.leader = True
        self.follower = False
        self.candidate = False

    def set_as_follower(self):
        self.leader = False
        self.follower = True
        self.candidate = False

    def isCandidate(self):
        if (self.candidate == True):
            return True
        else:
            return False

    def isFollower(self):
        if (self.follower == True):
            return True
        else:
            return False




    def check_if_won(self) -> bool:

        if self.votes/self.num_nodes >= 0.5:
            return True
        else:
            return False


        

    def send_heartbeats(self):

        msg = {"type": "heartbeat", "node_id": self.node_id, "log": self.log, "term": self.term}
        self.send_message_to_all_other_nodes(json.dumps(msg))

    # {"type": "electionRequest", "node_id": 0, "log": []}

    def process_latest_message(self):
        
        # Somehow build message list
        raw_message = retrieve_sqs_messages(self.sqs_client, self.sqs_info[self.node_id]["queue_url"])

        if raw_message is None:
            return
        message = json.loads(raw_message)

        print("Incoming message: " + raw_message)

        if message["type"] == "vote":
            self.votes += 1
            # if it's the majority (3) you win self.leader = true

        elif message["type"] == "heartbeat":

            if self.isCandidate():
                if message["term"] >= self.term:
                    self.set_as_follower()
                    self.reset_timeout()
            else:
                self.reset_timeout()

            self.hasVoted = False

        elif message["type"] == "electionRequest":

            if self.hasVoted == False:
                vote_msg = {"type": "vote", "node_id": self.node_id, "log": self.log, "term": self.term}

                print("Outgoing message: " + json.dumps(vote_msg))
                self.send_message_to_one_node(message["node_id"], json.dumps(vote_msg))
                self.hasVoted = True 

        elif message["type"] == "event":

            if not self.isLeader():
                return

            entry = {"data": message["data"], "term": self.term}
            self.log.append(entry)

            msg = {"type": "AppendEvent", "node_id": self.node_id, "log": self.log, "term": self.term}

            self.send_message_to_all_other_nodes(json.dumps(msg))


    def main_loop(self):

        while True:
            print("")

            # Check messages
            self.process_latest_message()

            # Timed out, start new election!
            if self.check_timeout() and not self.isLeader():

                print("I've timed out!!!!")
                print("Starting election")

                self.reset_timeout()
                self.set_as_candidate()
                self.hasVoted = False
                self.term += 1
                self.votes = 1 # reset votes to just yourself

                # send request for vote messages to all other nodes
                msg = {"type": "electionRequest", "node_id": self.node_id, "log": self.log, "term": self.term}
                self.send_message_to_all_other_nodes(json.dumps(msg))


            # Check if we've won election
            if self.isCandidate():

                # Check for incoming votes
                if self.check_if_won():
                    print("Won election!")
                    self.set_as_leader()
                    print("Sending heartbeat after election")
                    self.send_heartbeats()


            if self.isLeader():

                # Send heartbeat to other nodes
                print("Sending heartbeat")
                self.send_heartbeats()

            # If leader send hearbeat
            # Check for messages
            # 
            # 
 
if __name__ == "__main__":

    node_id = int(sys.argv[1])

    with open('ec2_setup.json') as f:
        CONFIG = json.load(f)

    myNode = Node(CONFIG["nodes"], node_id)
    myNode.main_loop()