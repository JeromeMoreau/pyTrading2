class Trade(object):
    def __init__(self,ticket,side,instrument,units,open_price,open_date,strategy,stop_loss=0.,take_profit=0.,trailing_stop=0.):
        """

        :param ticket: unique identifier for the trade (int)
        :param side:
        :param instrument:
        :param units:
        :param open_price:
        :param open_date:
        :param strategy:
        :param stop_loss:
        :param take_profit:
        :param trailing_stop:
        :return:
        """
        self.ticket = ticket
        self.side = side
        self.instrument = instrument
        self.units = units
        self.open_price = open_price
        self.open_date = open_date
        self.strategy = strategy
        self.stop_loss =stop_loss
        self.take_profit = take_profit
        self.trailing_stop = trailing_stop

        # Additionals variables set when closing the trade
        self.close_price = None
        self.close_date = None
        self.pnl = 0.

        # Initiates MAE and MFE to open_price
        self.MAE = open_price
        self.MFE = open_price

    def calculate_profit_base(self,cur_price,conversion_factor):
        mult = 1 if self.side == 'buy' else -1
        pips = mult * (cur_price - self.open_price)
        self.pnl = pips * conversion_factor * self.units

    def update_trade(self,cur_price,conversion_factor):
        #Update pnl
        self.calculate_profit_base(cur_price,conversion_factor)

        #Update MAE/MFE
        if self.side =='buy':
            if cur_price > self.MFE:
                self.MFE = cur_price
            elif cur_price < self.MAE:
                self.MAE = cur_price
        elif self.side =='sell':
            if cur_price > self.MAE:
                self.MAE = cur_price
            elif cur_price < self.MFE:
                self.MFE = cur_price





