# import send, recieve, robotFrontEnd
import time
import random
from typing import *
import boto3
from sqs import send_sqs_message, retrieve_sqs_messages, purge_queues
import sys
import json
from os import path
import threading

# TODO:
# ----1. Nodes need to use permanent storage
# 2. Punches stopped for three seconds after a succesful block
# 3. Communication and server between them can fail???
# 4. Server maintain game state???
# 5. fail(), recover(), and timeout()
# 6. Node can recover log after it fails and misses some events

class RaftNode:
    def __init__(self, sqs_config, node_id, isCandidate = False, isLeader = False, isFollower = True):

        self.nodes_sqs_info = sqs_config["nodes"]
        self.leader_sqs_info = sqs_config["leader"]
        self.clients_sqs_info = sqs_config["clients"]
        self.node_id = node_id

        self.isLeader = isLeader
        self.isFollower = isFollower
        self.isCandidate = isCandidate

        self.num_nodes = len(self.nodes_sqs_info)

        self.stateFile = "state" + str(self.node_id) + ".json"

        # Need to write these to persistent storage before responding to any message
        if path.exists(self.stateFile):
            with open(self.stateFile) as f:
                state = json.load(f)
            print(state)
            self.currentTerm = state["currentTerm"]
            self.votedFor = state["votedFor"]
            self.log = state["log"]
        else:
            self.currentTerm = 0
            self.votedFor = None 
            self.log = []

        self.votes = 0

        self.log_acks = {}

        # TODO: get this being used
        self.lastLogIndex = 0
        self.lastLogTerm = 0
        self.commitIndex = -1
        self.nextIndex = self.lastLogIndex + 1


        self.sqs_client = boto3.client('sqs', region_name='us-east-2')
        self.sqs_resource = boto3.resource('sqs', region_name='us-east-2')

        purge_queues(self.sqs_client, self.nodes_sqs_info[self.node_id]["queue_url"])

        # Setting self.timeout_time
        self.reset_timeout()

    # TODO: make sure this works
    def write_state_to_disk(self):

        state = {"currentTerm": self.currentTerm, "votedFor": self.votedFor, "log": self.log}

        with open("state" + str(self.node_id) + ".json", "w") as f:
            f.write(json.dumps(state))

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

    def send_message_to_all_other_nodes(self, message: str) -> None:

        self.write_state_to_disk()
        for node_info in self.nodes_sqs_info:
            if node_info["id"] == self.node_id:
                continue
            result = send_sqs_message(self.sqs_resource, node_info["queue_url"], node_info["queue_name"], message)
            #print(result)

    def send_message_to_one_node(self, node_id: int, message: str) -> None:

        self.write_state_to_disk()
        node_info = self.nodes_sqs_info[node_id]
        result = send_sqs_message(self.sqs_resource, node_info["queue_url"], node_info["queue_name"], message)
        #print(result)

    def check_timeout(self) -> bool:
        return time.time() >= self.timeout_time

    def reset_timeout(self, rand_lowerb=15, rand_upperb=40) -> None:
        self.timeout_time = time.time() + random.uniform(rand_lowerb, rand_upperb)

    def check_if_won(self) -> bool:

        if self.votes/self.num_nodes >= 0.5:
            return True
        else:
            return False

    def send_heartbeats(self):

        msg = {"type": "AppendEntries",
               "term": self.currentTerm,
               "node_id": self.node_id, 
               "prevLogIndex": None, 
               "prevLogTerm": None, 
               "entries": [],
               "commitIndex": self.commitIndex
              }

        self.send_message_to_all_other_nodes(json.dumps(msg))

    def process_Vote_message(self, message: Dict):

        self.votes += 1
        return
    

    def process_AppendEntries_message(self, message: Dict):

        if message["term"] < self.currentTerm:
            return

        if message["term"] > self.currentTerm:
            self.currentTerm = message["term"]

        if self.isCandidate == True or self.isLeader == True:
            self.set_as_follower()
            self.votedFor = None

        self.reset_timeout()

        if len(message["entries"]) > 0:

            print("adding entries to log...")

            # 5.Return failure if log doesn’t contain an entry
            #   at prevLogIndex whose term matches prevLogTerm

            # if len(self.log) < message["prevLogIndex"]:
            #     # Fail and send fail ack
            #     print("first fail")
            #     failMsg = {"type": "AppendAck", "status": "FAIL"}
            #     return

            # elif self.log[message["prevLogIndex"]]["term"] != message["prevLogTerm"]:
            #     # Fail and send fail ack
            #     print("second fail")
            #     return

            # 6.If existing entries conflict with new entries,
            #   delete all existing entries starting with first
            #   conflicting entry

            # 7.Append any new entries not already in the log

            successful_entries = []

            for entry in message["entries"]:
                if len(self.log) == entry["index"]:
                    self.log.append(entry)
                    successful_entries.append(entry["index"])
                else:
                    print("Adding entry to wrong index!!!!!!!!!!")

            successMsg = {"type": "AppendAck", "status": "SUCCESS", "successful_entries": successful_entries}

            # 8.Advance state machine with newly committed entries

            self.send_message_to_one_node(message["node_id"], json.dumps(successMsg))

    def process_AppendAck_message(self, message):

        if message["status"] == "SUCCESS":

            for entry_index in message["successful_entries"]:

                if entry_index in self.log_acks:

                    self.log_acks[entry_index] += 1

                    if self.log_acks[entry_index] / self.num_nodes > 0.5:

                        # This doesn't seem right, because it needs to be in order !!!!!!!!!!
                        if entry_index == self.commitIndex + 1:

                            print("commiting entry: " + str(entry_index))

                            self.commitIndex = max(self.commitIndex, entry_index)

                            message = {"type": "commitConfirm", "command": self.log[entry_index]["command"]}

                            self.send_reply_to_clients(json.dumps(message))


    def send_reply_to_clients(self, message):

        for client_info in self.clients_sqs_info:

            print("Sending to client: " + message)

            print(client_info)
            result = send_sqs_message(self.sqs_resource, client_info["queue_url"], client_info["queue_name"], message)



    # 1.If term > currentTerm, currentTerm ← term(step down if leader or candidate)
    # 2.If term == currentTerm, votedForis null or candidateId, and candidate's log
    #  is at least as complete as local log, grant vote and reset election timeout
    def process_RequestVote_message(self, message: Dict):
        
        if message["term"] > self.currentTerm:

            self.currentTerm = message["term"]

            if self.isCandidate == True or self.isLeader == True:
                self.set_as_follower()
                self.votedFor = None

        if message["term"] >= self.currentTerm or (self.votedFor is None or self.votedFor == message["node_id"]):# and candidate's log is at least as complete as local log
        # if self.votedFor is None or self.votedFor == message["node_id"]:# and candidate's log is at least as complete as local log

            self.votedFor = message["node_id"]
            vote_msg = {"type": "Vote", "node_id": self.node_id, "term": self.currentTerm}

            print("Outgoing message: " + json.dumps(vote_msg))

            self.send_message_to_one_node(message["node_id"], json.dumps(vote_msg))

    def process_latest_message(self):
        
        raw_message = retrieve_sqs_messages(self.sqs_client, self.nodes_sqs_info[self.node_id]["queue_url"])

        if raw_message is None:
            return
        message = json.loads(raw_message)

        if message["type"] == "AppendEntries":
            if len(message["entries"]) == 0:
                print("Incoming message: heartbeat from node " + str(message["node_id"]))
            else:
                print("Incoming message: " + raw_message)
        else:
            print("Incoming message: " + raw_message)

        if message["type"] == "Vote":
            self.process_Vote_message(message)

        elif message["type"] == "AppendEntries":
            self.process_AppendEntries_message(message)

        elif message["type"] == "RequestVote":
            self.process_RequestVote_message(message)

        elif message["type"] == "AppendAck":
            self.process_AppendAck_message(message)
        
        else:
            print("UKNOWN MESSAGE!!!!!!!!!!!!!!!!!!!!!!!!!!!")



    def process_leader_message(self):

        raw_message = retrieve_sqs_messages(self.sqs_client, self.leader_sqs_info["queue_url"])

        if raw_message is None:
            return

        message = json.loads(raw_message)

        print("Incoming message: " + raw_message)

        entry = {"term": self.currentTerm, "index": len(self.log), "command": message}

        appendMsg = {"type": "AppendEntries",
               "term": self.currentTerm,
               "node_id": self.node_id, 
               "prevLogIndex": self.lastLogIndex,
               "prevLogTerm": self.lastLogTerm,
               "entries": [entry],
               "commitIndex": self.commitIndex
              }

        self.log_acks[self.lastLogIndex] = 1

        self.lastLogIndex += 1
        self.lastLogTerm = self.currentTerm
        self.log.append(entry)


        print("Outgoing message: " + json.dumps(appendMsg))

        self.send_message_to_all_other_nodes(json.dumps(appendMsg))

    def start_election(self):

        self.set_as_candidate()
        self.currentTerm += 1
        self.votedFor = self.node_id
        self.votes = 1 # reset votes to just yourself
        self.reset_timeout()

        # send request for vote messages to all other nodes
        msg = {"type": "RequestVote", "node_id": self.node_id, "term": self.currentTerm, "lastLogIndex": self.lastLogIndex, "lastLogTerm": self.lastLogTerm}
        self.send_message_to_all_other_nodes(json.dumps(msg))


    def main_loop(self):

        counter = 0

        while True:

            counter += 1

            ## Debug printing
            # if counter % 10 == 0:
            #     print("Log and acks:")
            #     print(self.log)
            #     print(self.log_acks)

            # print("")

            # Check messages
            self.process_latest_message()

            # Timed out, start new election!
            if self.check_timeout() and self.isLeader == False:

                print("I've timed out!!!!")
                print("Starting election")

                self.start_election()

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
                # print("Sending heartbeat")
                self.send_heartbeats()
                self.process_leader_message()

    def server_ui(self):

        while True:

            print("")
            print("Please select from the following menu:")
            print("1. Print Log") 
            print("2. Timeout Node") 
            print("3. Debug Node State") 
            print("")

            user_input = input()


            if user_input == "1":

                print("Log:")
                print(self.Log)

            if user_input == "2":

                print("Manual timeout!")
                print("Starting election")

                self.start_election()

            if user_input == "3":
                print("Log:")
                print(self.log)
                print(self.log_acks)
                print(self.commitIndex)


 
if __name__ == "__main__":

    node_id = int(sys.argv[1])

    with open('ec2_setup.json') as f:
        CONFIG = json.load(f)

    myNode = RaftNode(CONFIG, node_id)

    # listenerThread = threading.Thread(target = myNode.process_latest_message)
    # listenerThread.start()

    listenerThread = threading.Thread(target = myNode.main_loop)
    listenerThread.start()

    myNode.server_ui()