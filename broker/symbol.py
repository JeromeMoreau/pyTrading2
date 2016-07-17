import pymongo

class Symbol(object):
    def __init__(self,name,timeframe,home_currency,margin,data_vendor=None,one_pip = 0.0001):
        self.name = name
        self.pip = one_pip
        self.maxTradeUnits = None
        self.marginRate = margin
        self.halted = False

        self.timeframe = timeframe
        self.data_vendor = data_vendor

        self.conversion_rate =self._setup_conversion_rate(home_currency)
        self.db_symbol_name = None

    def _setup_conversion_rate(self,home_currency):

        conversion_rate = self.name[-3:] + home_currency
        return conversion_rate