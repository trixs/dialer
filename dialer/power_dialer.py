'''
This solution uses a slightly diferent interface from the one proposed in the design.
Instead of using functions `dial` and `get_lead_phone_number_to_dial`
this implementation expects two objects to be injected:

- dialing_service which implements method `dial`
- database which implements method `get_lead_phone_number_to_dial`

this way tests may inject stubs that implement desired behavior.
'''
import logging
import threading
from .agent_state import AgentState
from .call_data import CallData
from.call_state import CallState

# pylint: disable=too-many-instance-attributes
class PowerDialer:
    '''
    Automatic dialer connecting agent with a customer
    '''
    def __init__(self, database: object, dialing_service: object, agent_id: str):
        """Constructor

        :param agent_id: The name to use.
        :param database: an object implementing `get_lead_phone_number_to_dial` method
        :param dialing_service: an object implementing `dial` method
        """
        self.DIAL_RATIO = 2 # pylint: disable=invalid-name
        self.logger = logging.getLogger(__name__)
        self.database = database
        self.dialing_service = dialing_service
        self.agent_id = agent_id
        self.agent_state = AgentState.UNAVAILABLE
        self.current_lead = ''
        self.is_logging_out = False

    def on_agent_login(self):
        '''
        Notification when agent logs in and can be connected with customers
        '''
        if self.agent_state != AgentState.UNAVAILABLE:
            msg = (f'Agent "{self.agent_id}" must be in UNAVAILABLE state. '
                   f'Current state is "{self.agent_state}"')
            self.logger.error(msg)
            raise Exception(msg)
        self.agent_state = AgentState.AVAILABLE

    def on_agent_logout(self):
        '''
        Notification when agent logs out and should not be connected with customers anymore
        '''
        # if agent is not connected to a customer he can logout immediately
        if self.agent_state == AgentState.AVAILABLE:
            self.agent_state = AgentState.UNAVAILABLE
        # a busy, or connecting agent will be logged out later
        # after the end of the current call
        elif self.agent_state in [AgentState.BUSY, AgentState.WAITING]:
            self.is_logging_out = True
        # an attempt to logout again is treated as a no-op

    def on_call_started(self, lead_phone_number: str):
        '''
        Notification when agent is connected with a customer
        '''
        if self.agent_state != AgentState.WAITING:
            msg = (f'Agent "{self.agent_id}" must be in WAITING state. '
                   f'Current state is "{self.agent_state}"')
            self.logger.error(msg)
            raise Exception(msg)
        self.agent_state = AgentState.BUSY
        self.current_lead = lead_phone_number

    def on_call_failed(self):
        '''
        Notification when call unexpectedly ends. And the agent can be connected again
        '''
        if self.agent_state != AgentState.BUSY:
            msg = (f'Agent "{self.agent_id}" must be in BUSY state. '
                   f'Current state is "{self.agent_state}"')
            self.logger.error(msg)
            raise Exception(msg)

        warn_msg = f'Call failed for agent="{self.agent_id}" lead="{self.current_lead}"'
        self.logger.warning(warn_msg)
        self.current_lead = ''
        if self.is_logging_out:
            # agent wants to logout after the current call
            self.is_logging_out = False
            self.agent_state = AgentState.UNAVAILABLE
        else:
            self.agent_state = AgentState.AVAILABLE

    def on_call_ended(self):
        '''
        Notification when call ends. And the agent can be connected again
        '''
        if self.agent_state != AgentState.BUSY:
            msg = (f'Agent "{self.agent_id}" must be in BUSY state. '
                   f'Current state is "{self.agent_state}"')
            self.logger.error(msg)
            raise Exception(msg)

        self.current_lead = ''
        if self.is_logging_out:
            # agent wants to logout after the current call
            self.is_logging_out = False
            self.agent_state = AgentState.UNAVAILABLE
        else:
            self.agent_state = AgentState.AVAILABLE

    def dialing_wrapper(self, phone_number, call_data):
        '''
        Handles dialing of a single phone number. If this attempt is successful sets an event
        If this is the last thread to finish then also sets the event
        '''
        try:
            conn_state = self.dialing_service.dial(self.agent_id, phone_number)
        except Exception as ex: # pylint: disable=broad-except
            msg = f'Dialing "{phone_number}" for agent "{self.agent_id}" failed. Error: "{ex}"'
            self.logger.error(msg)
            conn_state = CallState.FAILED
        should_signal = False
        call_data.lock.acquire()
        if conn_state == CallState.CONNECTED and call_data.connected_number == '':
            call_data.connected_number = phone_number
            should_signal = True
        call_data.thread_counter = call_data.thread_counter - 1
        if call_data.thread_counter <= 0:
            should_signal = True
        # usually we put the code between .acquire and .release into a try/finally block
        # but in this particular case there is no need for it
        call_data.lock.release()
        if should_signal:
            call_data.event.set()

    def connect(self):
        '''
        Connects agent with the next customer
        '''
        # First let's ensure that agent is available
        if self.agent_state != AgentState.AVAILABLE:
            msg = (f'Agent "{self.agent_id}" must be in AVAILABLE state. '
                   f'Current state is "{self.agent_state}"')
            self.logger.error(msg)
            raise Exception(msg)

        # We start multiple concurrent attempts, but there is a small chance
        # that all attempts will fail. Then we will start a new batch
        should_retry = True
        while should_retry:
            # Fetch phone numbers from the database. We would like to get up to DIAL_RATIO
            # number of leads, but we need to take of exceptional cases when database
            # doesn't have not enough leads
            leads = []
            for i in range(self.DIAL_RATIO):
                lead = self.database.get_lead_phone_number_to_dial()
                if not lead is None:
                    leads.append(lead)
                else:
                    break

            # if we found some leads let's dial them
            if len(leads) > 0:
                call_data = CallData()
                self.agent_state = AgentState.WAITING
                threads = []
                call_data.thread_counter = len(leads)
                # create one thread per lead number
                for lead in leads:
                    thread = threading.Thread(
                        target=self.dialing_wrapper,
                        args=(lead, call_data)
                    )
                    threads.append(thread)
                    thread.start()
                call_data.event.wait()
                if call_data.connected_number != '':
                    self.on_call_started(call_data.connected_number)
                    should_retry = False
            else:
                # no more leads in the database
                self.agent_state = AgentState.AVAILABLE
                should_retry = False
