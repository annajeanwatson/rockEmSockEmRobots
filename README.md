
# Requirements:

https://docs.google.com/document/d/e/2PACX-1vRJFJ7UjEs_6elTgSAySg71z08Be3kk52MaHLQrxL-RcwXAtzbL0S1f_ajyRZFLJX0xMfYAI_PVynao/pub

# Raft implementation
- You will host your game on using two clients and five servers. 
- We will assume that clients do not fail, but the servers and communication between them can. 
- The role of the servers is to maintain game state and arbiter the order of player actions.

- The five servers will run the Raft consensus protocol to maintain between them log of player actions. 
- To implement the game, the servers will also need to use this log to maintain game state, specifically whether a player is currently blocking and whether they are allowed yet to dispatch another punch.

In addition to normal Raft operation, your servers need support the following operations:

    fail() - the server ‘crashes’ and loses all local state
    recover() - the server ‘recovers,’ rejoins the Raft protocol, and recovers the log and state
    timeout() - the server decides that it has not heard from the coordinator within a timeout



# Game:
punch_with_left() [Q]
punch_with_right() [W]
block_with_left() [A]
block_with_right() [S]

When a robot blocks, it enters a blocking_with_left, or blocking_with_right state, which persists until another action is taken.
When blocking_with_left opponent’s punches with the right are blocked.
Analogously for blocking_with_right, punches with opponent’s left are blocked.

When punching an opponent who is not blocking, a robot has 10% chance of landing a hit.
If a hit lands, the opponent’s head is knocked off and the the match is over.
A robot can only punch once a second. After being blocked, a robot cannot punch for three seconds with either hand.

One of your tasks will be to define a user interface that lets a user take actions and receive feedback as to its effect.
Because your system includes two players, you may need to write scripts that trigger their actions.



# Approach