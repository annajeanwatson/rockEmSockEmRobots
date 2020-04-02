# import send, recieve, robotFrontEnd
import time
import random
from typing import *
import zmq

class Node:
    def __init__(self, candidate = False, leader = False, follower = True):
        # possible states

        '''Can receive:
		1. Client requests
		2. ACKs from followers
        
        Can send:
		1. Heartbeats to maintain authority
		2. AppendLog RPCs to servers
		3. Response to client'''
        self.leader = leader
        self.num_nodes = 5


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

        # should initalize as a follower
        self.follower = follower

        # Setting self.timeout_time
        self.reset_timeout()

    def check_timeout(self) -> bool:
        return time.time() >= self.timeout_time

    def reset_timeout(self) -> None:
        self.timeout_time = time.time() + random.uniform(15, 25)

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

    def start_election(self):

        # Send election message to every other node
        self.send_election_messages()

        self.receive_election_messages()

        print("Won election!")

        return True



    def check_if_won(self) -> bool:

        if self.votes/self.num_nodes >= 0.5:
            return True
        else:
            return False



    def send_election_messages(self):
        print("Sending Election Messages to all nodes")
        pass

    def receive_election_messages(self):
        print("Receiving election messages...")
        time.sleep(2)
        pass
        

    def send_heartbeats(self):

        print("Sending heartbeats...")
        pass

    def process_incoming_messages(self):

        # Somehow build message list
        messages = []
        for message in messages:
            if message["type"] == "vote":
                self.votes += 1
            elif message["type"] == "heartbeat":
                if self.isCandidate():
                    if message["term"] >= self.term:
                        self.set_as_follower()
            elif message["type"] == "VoteRequest":
                if self.isFollower():
                    # Send vote to requester
                # What do I do if I'm a candidate or leader?


    def main_loop(self):

        while True:

            # Check messages
            self.process_incoming_messages()

            # Timed out, start new election!
            if self.check_timeout() and not self.isLeader():

                print("I've timed out!!!!")
                print("Starting election")

                self.reset_timeout()
                self.set_as_candidate()
                self.term += 1
                self.votes += 1

                # send request for vote messages to all other nodes

            # Check if we've won election
            if self.isCandidate():

                # Check for incoming votes
                # votes += received_votes
                if self.check_if_won():
                    self.set_as_leader()
                    self.send_heartbeats()


            if self.isLeader():

                # Send heartbeat to other nodes
                self.send_heartbeats()

            # If leader send hearbeat
            # Check for messages
            # 
            


if __name__ == "__main__":

    myNode = Node()
    myNode.main_loop()