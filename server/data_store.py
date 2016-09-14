from abc import abstractmethod,ABCMeta



class DataStore(object):
    """
    Metaclass for data_stores
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def add_open_trade(self,trade):
        """

        :param trade:
        :return:
        """
        raise NotImplementedError("Should implement add_open_trade()")

    @abstractmethod
    def add_close_trade(self,trade):
        """

        :param trade:
        :return:
        """
        raise NotImplementedError("Should implement add_close_trade()")
