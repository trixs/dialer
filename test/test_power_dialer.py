'''
Tests for power_dialer module
'''
import unittest
from ..dialer.agent_state import AgentState
from ..dialer.call_state import CallState
from ..dialer.power_dialer import PowerDialer
from .dialing_service_stub import DialingServiceStub
from .database_stub import DatabaseStub
from .log_inspector import LogInspector

# I didn't find unit test hooks in Python unittest that are executed only once per class
# hence I perform test initialization here
LogInspector.setup_logging()

class TestPowerDialer(unittest.TestCase):
    '''
    Tests for PowerDialer class
    '''

    def setUp(self):
        '''
        Clears test stage before each test
        '''
        LogInspector.reset_buffer()

    def test_constructor(self):
        '''
        Testing constructor and initial values
        '''
        dialer = PowerDialer(None, None, 'agent1')
        self.assertEqual('agent1', dialer.agent_id)
        self.assertEqual(False, dialer.is_logging_out)
        self.assertEqual('', dialer.current_lead)
        self.assertEqual(AgentState.UNAVAILABLE, dialer.agent_state)

    def test_on_agent_login_successful(self):
        '''
        Testing state change after a login
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        self.assertEqual(False, dialer.is_logging_out)
        self.assertEqual('', dialer.current_lead)
        self.assertEqual(AgentState.AVAILABLE, dialer.agent_state)

    def test_on_agent_login_cant_login_twice(self):
        '''
        Testing that attempt to login while being logged in
        should raise an exception and a log message
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        try:
            dialer.on_agent_login()
            raise Exception('Undetected error')
        except Exception as ex: # pylint: disable=broad-except
            msg = str(ex)
            self.assertIn('Agent "agent1" must be in UNAVAILABLE', msg)
            self.assertIn('"AgentState.AVAILABLE"', msg)
        logs = LogInspector.get_messages()
        self.assertListEqual(logs, ['Agent "agent1" must be in UNAVAILABLE state. '
                                    'Current state is "AgentState.AVAILABLE"'])

    def test_on_agent_login_after_logout(self):
        '''
        Testing that agent can login after logging out
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.on_agent_logout()
        dialer.on_agent_login()
        self.assertEqual(False, dialer.is_logging_out)
        self.assertEqual('', dialer.current_lead)
        self.assertEqual(AgentState.AVAILABLE, dialer.agent_state)

    def test_on_agent_logout(self):
        '''
        Testing status change after logout
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.on_agent_logout()
        self.assertEqual(False, dialer.is_logging_out)
        self.assertEqual('', dialer.current_lead)
        self.assertEqual(AgentState.UNAVAILABLE, dialer.agent_state)

    def test_on_agent_logout_twice(self):
        '''
        Testing that logging out after a logout doesn't cause exceptions
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.on_agent_logout()
        dialer.on_agent_logout()
        self.assertEqual(False, dialer.is_logging_out)
        self.assertEqual('', dialer.current_lead)
        self.assertEqual(AgentState.UNAVAILABLE, dialer.agent_state)

    def test_on_agent_logout_during_connect1(self):
        '''
        Testing that an agent can indicate desire to logout during a call
        He will be logged out after the call ends
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.connect()
        dialer.on_agent_logout()
        self.assertEqual(True, dialer.is_logging_out)
        self.assertEqual('+12123334444', dialer.current_lead)
        self.assertEqual(AgentState.BUSY, dialer.agent_state)
        dialer.on_call_ended()
        self.assertEqual(False, dialer.is_logging_out)
        self.assertEqual('', dialer.current_lead)
        self.assertEqual(AgentState.UNAVAILABLE, dialer.agent_state)

    def test_on_agent_logout_during_connect2(self):
        '''
        Testing that an agent can indicate desire to logout during a call
        He will be logged out after the call fails
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.connect()
        dialer.on_agent_logout()
        self.assertEqual(True, dialer.is_logging_out)
        self.assertEqual('+12123334444', dialer.current_lead)
        self.assertEqual(AgentState.BUSY, dialer.agent_state)
        dialer.on_call_failed()
        self.assertEqual(False, dialer.is_logging_out)
        self.assertEqual('', dialer.current_lead)
        self.assertEqual(AgentState.UNAVAILABLE, dialer.agent_state)

    def test_on_call_started_without_connect(self):
        '''
        Test that attempt to call on_call_started when agent is not in WAITING state
        should raise an exception and log an error message
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        try:
            dialer.on_call_started('+12123334444')
            raise Exception('Undetected error')
        except Exception as ex: # pylint: disable=broad-except
            msg = str(ex)
            self.assertIn('Agent "agent1" must be in WAITING', msg)
            self.assertIn('"AgentState.AVAILABLE"', msg)
        logs = LogInspector.get_messages()
        self.assertListEqual(logs, ['Agent "agent1" must be in WAITING state. '
                                    'Current state is "AgentState.AVAILABLE"'])

    def test_on_call_failed(self):
        '''
        Test status change when call terminates unexpectedly
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.connect()
        dialer.on_call_failed()
        self.assertEqual(False, dialer.is_logging_out)
        self.assertEqual('', dialer.current_lead)
        self.assertEqual(AgentState.AVAILABLE, dialer.agent_state)
        logs = LogInspector.get_messages()
        self.assertListEqual(logs, ['Call failed for agent="agent1" lead="+12123334444"'])

    def test_on_call_failed_without_connect(self):
        '''
        Test that attempt to call on_call_failed when agent is not on the call
        should raise an exception and log an error message
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        try:
            dialer.on_call_failed()
            raise Exception('Undetected error')
        except Exception as ex: # pylint: disable=broad-except
            msg = str(ex)
            self.assertIn('Agent "agent1" must be in BUSY', msg)
            self.assertIn('"AgentState.AVAILABLE"', msg)
        logs = LogInspector.get_messages()
        self.assertListEqual(logs, ['Agent "agent1" must be in BUSY state. '
                                    'Current state is "AgentState.AVAILABLE"'])

    def test_on_call_ended(self):
        '''
        Test status change when call terminates correctly
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.connect()
        dialer.on_call_ended()
        self.assertEqual(False, dialer.is_logging_out)
        self.assertEqual('', dialer.current_lead)
        self.assertEqual(AgentState.AVAILABLE, dialer.agent_state)

    def test_on_call_ended_without_connect(self):
        '''
        Test that attempt to call on_call_failed when agent is not on the call
        should raise an exception and log an error message
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        try:
            dialer.on_call_ended()
            raise Exception('Undetected error')
        except Exception as ex: # pylint: disable=broad-except
            msg = str(ex)
            self.assertIn('Agent "agent1" must be in BUSY', msg)
            self.assertIn('"AgentState.AVAILABLE"', msg)
        logs = LogInspector.get_messages()
        self.assertListEqual(logs, ['Agent "agent1" must be in BUSY state. '
                                    'Current state is "AgentState.AVAILABLE"'])

    #FIXME: add multithreading tests # pylint: disable=fixme
    def test_connect_agent_should_login(self):
        '''
        Testing that attempt to connect without a login
        results in an exception and a log message
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        try:
            dialer.connect()
            raise Exception('Undetected error')
        except Exception as ex: # pylint: disable=broad-except
            msg = str(ex)
            self.assertIn('Agent "agent1" must be in AVAILABLE', msg)
            self.assertIn('"AgentState.UNAVAILABLE"', msg)
        logs = LogInspector.get_messages()
        self.assertListEqual(logs, ['Agent "agent1" must be in AVAILABLE state. '
                                    'Current state is "AgentState.UNAVAILABLE"'])

    def test_connect_successful(self):
        '''
        Testing status change after successful connection
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED}
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.connect()
        self.assertEqual(dialer.agent_state, AgentState.BUSY)
        self.assertEqual(dialer.current_lead, '+12123334444')

def wait_for_all_threads(dialer):
    '''
    helper utility
    waits until all threads started in dialer.connect() terminate
    '''
    for thread in dialer.threads:
        thread.join()

class TestConcurrentConnections(unittest.TestCase):
    '''
    Tests concurrent aspects of optimistic dialing
    '''

    def setUp(self):
        '''
        Clears test stage before each test
        '''
        LogInspector.reset_buffer()


    def test_connect_without_leads(self):
        '''
        Testing that if database has no leads, then agent's status doesn't change
        '''
        ctx = {
        }
        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.connect()
        def validate():
            self.assertEqual(dialer.agent_state, AgentState.AVAILABLE)
            self.assertEqual(dialer.current_lead, '')
        validate() # validate immediately after connect
        wait_for_all_threads(dialer)
        validate() # re-validate after all threads terminate

    def test_connect_two_leads_successfull(self):
        '''
        Testing that when dialing 2 numbers. We will use the one we connected to sooner
        '''
        ctx = {
            '+12123334444': {'state': CallState.CONNECTED, 'waitMs': 5},
            '+12123334449': {'state': CallState.CONNECTED, 'waitMs': 10}
        }

        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.connect()
        def validate():
            self.assertEqual(dialer.agent_state, AgentState.BUSY)
            self.assertEqual(dialer.current_lead, '+12123334444')
        validate() # validate immediately after connect
        wait_for_all_threads(dialer)
        validate() # re-validate after all threads terminate

    def test_connect_two_leads_one_fails(self):
        '''
        Testing that when dialing 2 numbers. One connection fails, one succeeds.
        Status should reflect proper connection
        '''
        ctx = {
            '+12123334444': {'state': CallState.DISCONNECTED, 'waitMs': 5},
            '+12123334449': {'state': CallState.CONNECTED, 'waitMs': 10}
        }

        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.connect()
        def validate():
            self.assertEqual(dialer.agent_state, AgentState.BUSY)
            self.assertEqual(dialer.current_lead, '+12123334449')
        validate() # validate immediately after connect
        wait_for_all_threads(dialer)
        validate() # re-validate after all threads terminate

    def test_connect_two_leads_one_throws(self):
        '''
        Testing that when dialing 2 numbers. One connection connects, the other throws an exception
        Status should reflect proper connection
        '''
        ctx = {
            '+12123334444': {'exception': Exception('Dialing service failed'), 'waitMs': 5},
            '+12123334449': {'state': CallState.CONNECTED, 'waitMs': 10}
        }

        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.connect()
        def validate():
            self.assertEqual(dialer.agent_state, AgentState.BUSY)
            self.assertEqual(dialer.current_lead, '+12123334449')
            logs = LogInspector.get_messages()
            self.assertListEqual(logs, [
                'Dialing "+12123334444" for agent "agent1" failed. Error: "Dialing service failed"'
            ])
        validate() # validate immediately after connect
        wait_for_all_threads(dialer)
        validate() # re-validate after all threads terminate

    def test_connect_two_leads_fail_should_try_third(self):
        '''
        Testing that when dialing 2 numbers. Both attempts fail
        The code should fetch yet another number or two from the database
        '''
        ctx = {
            '+12123334444': {'exception': Exception('Dialing service failed'), 'waitMs': 5},
            '+12123334449': {'state': CallState.FAILED, 'waitMs': 10},
            '+12123334447': {'state': CallState.CONNECTED, 'waitMs': 5}
        }

        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.connect()
        def validate():
            self.assertEqual(dialer.agent_state, AgentState.BUSY)
            self.assertEqual(dialer.current_lead, '+12123334447')
            logs = LogInspector.get_messages()
            self.assertListEqual(logs, [
                'Dialing "+12123334444" for agent "agent1" failed. Error: "Dialing service failed"'
            ])
        validate() # validate immediately after connect
        wait_for_all_threads(dialer)
        validate() # re-validate after all threads terminate

    def test_connect_all_leads_fail(self):
        '''
        Testing that when dialing all available numbers from the database,
        and all connections failing. The agent should keep AVAILABLE status
        '''
        ctx = {
            '+12123334444': {'exception': Exception('Dialing service failed'), 'waitMs': 5},
            '+12123334449': {'state': CallState.FAILED, 'waitMs': 10},
            '+12123334447': {'state': CallState.DISCONNECTED, 'waitMs': 5}
        }

        dialer = PowerDialer(DatabaseStub(ctx), DialingServiceStub(ctx), 'agent1')
        dialer.on_agent_login()
        dialer.connect()
        def validate():
            self.assertEqual(dialer.agent_state, AgentState.AVAILABLE)
            self.assertEqual(dialer.current_lead, '')
            logs = LogInspector.get_messages()
            self.assertListEqual(logs, [
                'Dialing "+12123334444" for agent "agent1" failed. Error: "Dialing service failed"'
            ])
        validate() # validate immediately after connect
        wait_for_all_threads(dialer)
        validate() # re-validate after all threads terminate
