
from events import CloseEvent,OrderEvent

class EventHandler(object):
    def __init__(self,events_queue):
        self.events = events_queue

    def process_event(self,data):
        if data['type'] == 'TRADE_CLOSE' or data['type'] == 'STOP_LOSS_FILLED' or data['type'] == 'TAKE_PROFIT_FILLED':
            # Generate CloseEvent
            print('Generating CloseEvent')
            close_event = CloseEvent(data['side'],data['tradeId'],data['instrument'],
                                     data['units'],data['price'],data['time'],data['pl'],data['interest'],data['accountBalance'],strategy='unknown')
            self.events.put(close_event)
        elif data['type'] == 'MARKET_ORDER_CREATE':
            #Should create an order object
            order_event = OrderEvent()
            print('Data: Received MARKET_ORDER_CREATE Event,not yet supported')

        elif data['type'] == 'MARKET_IF_TOUCHED_ORDER_CREATE':
            #Should create a limit order object
            print('Data: Received MARKET_IF_TOUCHED_ORDER_CREATE Event,not yet supported')

        elif data['type'] == 'ORDER_FILLED':
            #Should fill an order object
            print('Data: Received ORDER_FILLED Event,not yet supported')

        elif data['type'] == 'DAILY_INTEREST':
            #Should create a swap event
            #TODO Create a swap event, handle with portfolio
            print('Data: Received DAILY_INTEREST Event,not yet supported')

        else:
            print('Data: Received unsupported Event %s' %data)
