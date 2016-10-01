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
    def find_trade(self, trade):
        """

        :param trade: Trade Object
        :return:
        """
        raise NotImplementedError("Should implement find_trade()")

    @abstractmethod
    def getAllTrades(self):
        """

        :return: None
        """
        raise NotImplementedError("Should implement find")


    def recordTick(self, instrument,bid,ask):
        """

        :param instrument:
        :param bid:
        :param ask:
        :return:
        """
        pass