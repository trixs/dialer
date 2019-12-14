'''
A helper utility to intercept log messages.
'''
import logging
from logging.handlers import MemoryHandler

BUFFER = [] # global buffer for capture logged messages

# pylint: disable=too-few-public-methods
class CaptureFilter(logging.Filter):
    '''
    This filter captures all messages in a global variable
    '''
    def filter(self, record):
        BUFFER.append(record.msg)
        return True

class LogInspector:
    '''
    It is used in unit tests to ensure that logged messages contain
    all necessary details
    '''

    @staticmethod
    def setup_logging():
        '''
        Adds a filter to capture messages being logged
        '''
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        # create a dummy handler, because filter needs to be attached to a handler
        handler = MemoryHandler(10000)
        root_logger.addHandler(handler)
        custom_filter = CaptureFilter()
        handler.addFilter(custom_filter)

    @staticmethod
    def reset_buffer():
        '''
        Removes all messages from the buffer
        '''
        BUFFER.clear()

    @staticmethod
    def get_messages():
        '''
        Returns all messages from the buffer
        '''
        return BUFFER
