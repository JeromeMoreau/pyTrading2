from abc import abstractmethod,ABCMeta



class AbstractDataStore(object):
    """
    Abstract class that every DataStore should implement.

    required implementation:
    -add_open_trade(Trade)
    -add_close_trade(Trade)
    -getAllTrades()

    optional implementation:
    -recordTick(instrument,bid,ask)


    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def add_open_trade(self, trade):
        """

        :param trade: Trade object
        :return:
        """
        raise NotImplementedError("Should implement add_open_trade()")

    @abstractmethod
    def add_close_trade(self, trade):
        """

        :param trade: Trade object
        :return:
        """
        raise NotImplementedError("Should implement add_close_trade()")



    @abstractmethod
    def getTradeById(self,id):
        """

        :param id: OrderId in the database
        :return: trade object
        """
        raise NotImplementedError("Should implement getTradeById()")


    def recordTick(self, instrument,bid,ask):
        """

        :param instrument:
        :param bid:
        :param ask:
        :return:
        """
        pass