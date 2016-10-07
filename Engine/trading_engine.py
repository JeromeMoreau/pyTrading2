from abc import abstractmethod,ABCMeta

class TradingEngine(object):
    __metaclass__ = ABCMeta

    def __init__(self,events,data_handler,execution_handler,portfolio,strategy_manager,data_store=None):
        """
        Base Engine that will get the events from the queue and route them to the corresponding object

        :param events(Queue): where every events will be put/get
        :param data_handler(AbstractDataHandler):
        :param execution_handler(AbstractExecutionHandler): executes the orders
        :param portfolio: Object responsible for handling trades
        :param strategy_manager: Object responsible for generating signals
        :param data_store: facultative object to record data to a database for later inspection
        """
        self.events = events
        self.data = data_handler
        self.execution = execution_handler
        self.portfolio = portfolio
        self.strategy_manager = strategy_manager
        if data_store is not None:
            self.has_data_store = True
            self.data_store = data_store
        else:
            self.has_data_store = False

    @abstractmethod
    def run(self):
        raise NotImplementedError("Should implement run()")

    @classmethod
    def save_trade(cls,trade):
        if cls.has_data_store:
            if trade.close_date is None:
                #It is an opened trade
                cls.data_store.add_open_trade(trade)
            elif trade.close_date is not None:
                cls.data_store.add_close_trade(trade)
