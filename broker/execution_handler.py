from events import FillEvent, CloseEvent
import oandapy
from datetime import datetime

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
            if self.prices.symbols_obj[event.trade.instrument].use_inverse_rate == True:
                quote_home_rate = self.prices.get_home_quote(self.prices.symbols_obj[event.trade.instrument].inverse_rate)
            else:
                quote_home_rate = self.prices.get_home_quote(self.prices.symbols_obj[event.trade.instrument].conversion_rate)
            if event.trade.side == 'buy':
                pnl = (close_price - event.trade.open_price) * quote_home_rate * event.trade.units
            elif event.trade.side == 'sell':
                pnl = (event.trade.open_price - close_price) * quote_home_rate * event.trade.units
            #print('units',event.trade.units)

            close_event = CloseEvent(event.trade.side,event.trade.ticket,event.trade.instrument,event.trade.units,close_price,close_time,pnl,interest,strategy=event.strategy,accountBalance=123)
            self.events.put(close_event)

class OandaExecution(object):
    def __init__(self,events_queue,account):
        """

        :param events_queue:
        :param prices: price feed
        :param account: account object to get Token and account_id
        :return:
        """

        self.events = events_queue
        self.account=account
        self.oanda = oandapy.API(account.environment,account.token)

    def execute_order(self,order_event):
        if order_event.type =='ORDER':
            # Send an order to oanda API and wait for response
            params={'instrument':order_event.instrument,
                    'units':int(order_event.units/10), #Divided by 10 for testing purposes
                    'side':order_event.side,
                    'type':order_event.order_type,
                    'stopLoss':round(order_event.stop_loss,4),
                    'takeProfit':round(order_event.take_profit,4)}
            try:
                response = self.oanda.create_order(self.account.id, **params)
                #print(response)
            except oandapy.OandaError as err:
                print('Execution: Failed to execute order: %s' %err)
            else:
                fill_event = self._create_fill(response,order_event)
                if fill_event is not None: self.events.put(fill_event)


        elif order_event.type=='EXIT_ORDER':
            #print('EXECUTION: Received Exit_order')
            try:
                response = self.oanda.close_trade(self.account.id,order_event.ticket)
            except oandapy.OandaError as err:
                print('Execution: Failed to execute order: %s' %err)
            else:
                #close_event =self._create_fill(response,order_event)
                #self.events.put(close_event)
                print('EXECUTION:',response)


    def _create_fill(self,response,order_event):
        try:
            if response['tradeOpened'] != {}:
                params={'side':response['tradeOpened']['side'],
                        'ticket':response['tradeOpened']['id'],
                        'instrument':response['instrument'],
                        'units':response['tradeOpened']['units'],
                        'price':response['price'],
                        'open_date':datetime.strptime(response['time'],'%Y-%m-%dT%H:%M:%S.%fz'),
                        'stop_loss':response['tradeOpened']['stopLoss'],
                        'take_profit':response['tradeOpened']['takeProfit'],
                        'trailing_stop':response['tradeOpened']['trailingStop'],
                        'strategy':order_event.strategy}
                return FillEvent(**params)

            elif response['tradeReduced'] != {}:
                print('Execution: Something trying to reduce trade')
                print(response)

            elif response['tradesClosed']!= {}:
                params={'side':response['tradesClosed']['side'],
                        'ticket':response['tradesClosed']['id'],
                        'instrument':response['instrument'],
                        'units':response['tradesClosed']['units'],
                        'close_price':response['price'],
                        'close_date':datetime.strptime(response['time'],'%Y-%m-%dT%H:%M:%S.%fz'),
                        'strategy':order_event.strategy,
                        'pnl':response['profit'],
                        'interest':0,
                        'accountBalance':0}
                return CloseEvent(**params)

        except KeyError:
            print('Execution: response',response)
            print('Execution: order_event',order_event.__dict__)
