import time 
import node

class Timeout:
    def __init__(self, timeTilTimeout, isNotTimedOut):
        self.timeTilTimeout = timeTilTimeout
        self.isNotTimedOut = isNotTimedOut
        
    timeoutTime = 0 
    self.timeTilTimeout = timeoutTime

    def beginTimer(self):
        while True: 
            while timeoutTime > 0: 
                time.sleep(1)
                timeoutTime -= 1
            # logic to handle timeout (start election)
            #timeoutTime = self.timeTilTimeout
            # i don't know it depends how we do this




    
 