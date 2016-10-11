class Event(object):
    pass

class TickEvent(Event):
    def __init__(self,instrument,time,bid,ask,epoch):
        self.type ='TICK'
        self.instrument = instrument
        self.time = time
        self.bid = bid
        self.ask = ask
        self.price = round((bid+ask)/2,5)
        self.epoch = epoch

class MarketEvent(Event):
    def __init__(self):
        self.type = 'MARKET'

class OrderEvent(Event):
    def __init__(self,instrument,units,order_type,side,strategy,price=0.,expiry=None,stop_loss=0.,take_profit=0.):
        self.type='ORDER'
        self.instrument=instrument
        self.units = units
        self.order_type = order_type
        self.side = side
        self.strategy=strategy
        self.price = price
        self.expiry=expiry
        self.stop_loss = stop_loss
        self.take_profit = take_profit

class ExitOrderEvent(Event):
    def __init__(self,trade):
        self.type = 'EXIT_ORDER'
        self.trade = trade #Trade (object) attached to the event
        self.ticket = trade.ticket
        self.strategy = trade.strategy

class SignalEvent(Event):
    def __init__(self,instrument,order_type,side,strategy,stop_loss=0.,take_profit=0.,price=0.,expiry=None):
        self.type = 'SIGNAL'
        self.instrument = instrument
        self.order_type = order_type
        self.side = side
        self.strategy = strategy
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.price = price
        self.expiry = expiry

class FillEvent(Event):
    def __init__(self,side,ticket,instrument,units,price,open_date,stop_loss,take_profit,trailing_stop,strategy):
        self.type = 'FILL'
        self.side = side
        self.ticket = ticket
        self.instrument = instrument
        self.units = units
        self.price = price
        self.open_date = open_date
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trailing_stop = trailing_stop
        self.strategy = strategy

class CloseEvent(Event):
    def __init__(self,side,ticket,instrument,units,close_price,close_date,pnl,interest,accountBalance,strategy):
        self.type = 'TRADE_CLOSED'
        self.side = side
        self.ticket = ticket
        self.instrument = instrument
        self.units = units
        self.close_price = close_price
        self.close_date = close_date
        self.pnl = pnl
        self.interest = interest
        self.accountBalance = accountBalance
        self.strategy = strategy
