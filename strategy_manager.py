
class StrategyManager(object):
    # Manage the stack of strategies, their updates and access. Will control the startegies status with adding/removing commands.
    #TODO: Include filters

    def __init__(self,strategies=[]):

        #Strategies are accessed via their name through the self.strategies dictionnary
        self.strategies = {}
        for strat in strategies:
            self.strategies[strat.identifier]=strat

    def add_strategy(self,strategy):
        # Adds a strategy object to the self.strategies dict
        self.strategies[strategy.identifier] = strategy
        print('Strategy %s added to the stack' %strategy.identifier)

    def calculate_signals(self,market_event):
        # Notify every strategies with a market_event, aggregate their signals and put them in the main queue.

        for strategy in self.strategies.values():
            strategy.calculate_signals(market_event)


    def set_invested(self,strategy_name,symbol,status):
        """

        :param strategy_name:
        :param symbol:
        :param status:
        :return:
        """
        self.strategies[strategy_name].invested[symbol]=status