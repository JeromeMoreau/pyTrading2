from abc import ABCMeta, abstractmethod


class AbstractDataHandler(object):
    """
    DataHandler is an abstract base class providing an interface for
    all subsequent (inherited) data handlers (both live and historic).

    The goal of a (derived) DataHandler object is to output a generated
    set of bars (OLHCVI) for each symbol requested.

    This will replicate how a live strategy would function as current
    market data would be sent "down the pipe". Thus a historic and live
    system will be treated identically by the rest of the backtesting suite.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or fewer if less bars are available.
        """
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def get_latest_bar_value(self,symbol,val_type='close'):
        """

        :param symbol: name of symbol to get data for
        :param val_type: (open,high,low,close,volume,open_interest): volume and OI are only available for specific symbols
        :return: the val_type latest_value of symbol

        """
        raise NotImplementedError("Should implement get_latest_bar_value()")

    @abstractmethod
    def get_latest_bars_values(self,symbol,val_type='close'):
        """

        :param symbol:
        :param val_type:
        :return: an array containing the (open/high/low/close) of the specified symbol
        """
        raise NotImplementedError("Shoud implement get_latest_bars_values()")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """

        :param symbol:
        :return: the datetime object of the latest bar
        """
        raise NotImplementedError("Should implement get_latest_bar_datetime()")
