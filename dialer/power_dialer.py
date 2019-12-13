'''
Automatic dialer connecting agent with a customer
'''
class PowerDialer:
    '''
    Class to do the work
    '''
    def __init__(self, agent_id: str):
        """Copy-pasted docstring example.
        :param agent_id: The name to use. 
        :type agent_id: str. 
        """ 
        self.agent_id = agent_id

    def on_agent_login(self):
        """Copy-pasted docstring example.
        :param agent_id: The name to use. 
        :type agent_id: str. 
        """ 
        raise NotImplementedError

    def on_agent_logout(self):
        """Copy-pasted docstring example.
        :param agent_id: The name to use. 
        :type agent_id: str. 
        """ 
        raise NotImplementedError

    def on_call_started(self, lead_phone_number: str):
        raise NotImplementedError

    def on_call_failed(self, lead_phone_number: str):
        raise NotImplementedError

    def on_call_ended(self, lead_phone_number: str):
        raise NotImplementedError