
class Symbol(object):
    def __init__(self,name,timeframe,conversion_rate,inverse_rate,margin,data_vendor=None,one_pip = 0.0001):
        self.name = name
        self.pip = one_pip
        self.maxTradeUnits = None
        self.marginRate = margin
        self.halted = False

        self.timeframe = timeframe
        self.data_vendor = data_vendor

        self.conversion_rate = conversion_rate
        self.use_inverse_rate=False
        self.inverse_rate = inverse_rate
        print(self.conversion_rate,self.inverse_rate)

