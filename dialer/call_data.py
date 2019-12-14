'''
Group of data used fo synchronization between concurrent dialing threads
'''

import threading

# pylint: disable=too-few-public-methods
class CallData:
    '''
    Data shared between multiple calling threads
    '''
    def __init__(self):
        self.connected_number = ''
        self.thread_counter = 0
        # lock guarding connected_number and thread_counter variables
        self.lock = threading.RLock()
        # event to signal when connection is made, or all threads finished
        self.event = threading.Event()
