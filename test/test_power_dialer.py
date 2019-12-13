import unittest
from ..dialer.power_dialer import PowerDialer

class TestPowerDialer(unittest.TestCase):

    def test_constructor(self):
        pd = PowerDialer('agent1')
        self.assertEqual('agent1', pd.agent_id)
