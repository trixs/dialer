'''
Mocks dialing service interface
'''
import time
from ..dialer.call_state import CallState

# pylint: disable=too-few-public-methods
class DialingServiceStub:
    '''
    Implements `dial` method
    '''
    def __init__(self, ctx: dict):
        '''Constructor

        :context: A hashmap with phone numbers as keys and result scenarios as values
        '''
        self.ctx = ctx

    def dial(self, agent_id: str, number: str)->CallState: # pylint: disable=unused-argument
        '''
        - Finds scenario corresponding to the phone number
        - Waits for some time if specified in the scenario
        - Eventually either returns a value or throws an exception, as configured in scenario
        '''
        scenario = self.ctx[number]
        if 'waitMs' in scenario:
            time.sleep(scenario['waitMs'] / 1000)
        if 'state' in scenario: # pylint: disable=no-else-return
            return scenario['state']
        elif 'exception' in scenario:
            raise scenario['exception']
        raise Exception('Invalid scenario. A scenario must specify either '
                        '"state", or "exception" field')
