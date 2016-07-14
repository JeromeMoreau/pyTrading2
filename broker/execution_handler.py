from events import FillEvent, CloseEvent

class SimulatedExecution(object):
    """
    The simulated execution handler simply converts all order objects into their equivalent fill objects automatically
    without latency or fill-ratio issues.

    This allows a straightforward 'first-go' test of any strategy, before implementation with a more sophisticated
    execution handler
    """

    def __init__(self,events_queue,prices,spread = 0.,execute_on='close'):
        """
        Initialises the handler.

        Parameters:
        events - The Queue of Event object.
        prices - The prices feed
        spread - Spread added to each trade, default:0
        execute_on - Whether to execute on close or on next open. values('close' or 'open'), default:'close'
        """
        self.events = events_queue
        self.prices = prices
        self.spread = spread
        self.execute_on = execute_on
        self.orders = []

        self.ticket = 0

    def execute_order(self,event):
        """
        Simply converts Order objects into Fill objects naively. Stores Limit orders

        Parameters:
        event - Contains an Event object with order information.
        """

        if event.type == 'ORDER':
            # Converts the OrderEvent to FillEvent
            if event.order_type == 'market':
                if self.execute_on == 'close':
                    # Fill the Order
                    self.ticket +=1
                    spread = self.spread if event.side == 'buy' else -self.spread
                    price = self.prices.get_latest_bar_value(event.instrument) + spread/2
                    open_date = self.prices.get_latest_bar_datetime(event.instrument)

                    fill_event = FillEvent(event.side, self.ticket, event.instrument, event.units,
                                           price, open_date,strategy=event.strategy, stop_loss=event.stop_loss,
                                           take_profit=event.take_profit, trailing_stop=0)
                    self.events.put(fill_event)
                elif self.execute_on=='open':
                    self.orders.append(event)

        elif event.type == 'EXIT_ORDER':
            # Converts the OrderEvent to CloseEvent
            pnl = 0.
            interest = 0.0
            spread = self.spread if event.trade.side == 'buy' else -self.spread
            close_price = self.prices.get_latest_bar_value(event.trade.instrument) - spread/2
            close_time = self.prices.get_latest_bar_datetime(event.trade.instrument)
            quote_home_rate = self.prices.get_home_quote(self.prices.symbols_obj[event.trade.instrument].conversion_rate)
            if event.trade.side == 'buy':
                pnl = (close_price - event.trade.open_price) * quote_home_rate * event.trade.units
            elif event.trade.side == 'sell':
                pnl = (event.trade.open_price - close_price) * quote_home_rate * event.trade.units


            close_event = CloseEvent(event.trade.side,event.trade.ticket,event.trade.instrument,event.trade.units,close_price,close_time,pnl,interest,strategy=event.strategy,accountBalance=123)
            self.events.put(close_event)

class OandaExecution(object):
    def __init__(self,events_queue,prices,):