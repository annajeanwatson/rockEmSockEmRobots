import send, recieve, robotFrontEnd

class Node:
    def __init__(self, leader, candidate, follower):
        # possible states

        '''Can receive:
		1. Client requests
		2. ACKs from followers
        
        Can send:
		1. Heartbeats to maintain authority
		2. AppendLog RPCs to servers
		3. Response to client'''
        self.leader = leader


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
        # should initalize as a follower
        self.follower = follower

        def setLeader(self, setValue):
            self.leader = setValue

        def isLeader():
            if (self.leader == True):
                return True
            else:
                return False

        def setCandidate(self, setValue):
            self.candidate = setValue

        def isCandidate():
            if (self.candidate == True):
                return True
            else:
                return False

        def setFollower(self, setValue):
            self.follower = setValue

        def isFollower():
            if (self.follower == True):
                return True
            else:
                return False

        
