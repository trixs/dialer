'''
Contains class AgentState
'''
import enum

class AgentState(enum.Enum):
    '''
    States of a customer support agent
    '''
    AVAILABLE = 1 # logged in
    WAITING = 2 # waiting to be connected to a customer
    BUSY = 3 # talking to a customer
    UNAVAILABLE = 4 # logged out
