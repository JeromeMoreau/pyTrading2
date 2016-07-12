
class SimulatedBroker(object):
    def __init__(self,account,execution,prices):
        self.account = account
        self.execution = execution
        self.prices = prices