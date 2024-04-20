import abc
import random

class BaseResponseDecisionMaker(object):
    """
    
    """
    def __init__(self, user_context, logger):
        self._user_context = user_context
        self._logger = logger
    
    
    def decide(self):
        """
        Abstract method - must be implemented by an inheriting class.
        Returns an action - from the loggers.Actions enum.
        """
        
        # randomly decide whether to continue or not, for now
        if random.random() < 0.5:
            return True 
        else:    
            return False
