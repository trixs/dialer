'''
Mocks database interface
'''
# pylint: disable=too-few-public-methods
class DatabaseStub:
    '''
    Implements `get_lead_phone_number_to_dial` method
    '''
    def __init__(self, ctx: dict):
        '''Constructor

        :context: A hashmap with phone numbers as keys.
        '''
        self.numbers = list(ctx.keys())

    def get_lead_phone_number_to_dial(self)->str:
        '''
        Removes the first element from the array of numbers
        and returns its value. When storage is empty returns None
        '''
        if len(self.numbers) == 0:
            return None
        number = self.numbers.pop(0)
        return number
