'''
Contains CallState class
'''
import enum

class CallState(enum.Enum):
    '''
    Enumerated states of a phone connection
    '''
    CREATED = 1
    ALERTING = 2
    CONNECTED = 3
    DISCONNECTED = 4
    FAILED = 5
