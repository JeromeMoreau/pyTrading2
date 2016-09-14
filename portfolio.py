from events import OrderEvent, ExitOrderEvent
from trade import Trade
import numpy as np

class Portfolio(object):
    def __init__(self,events_queue,prices,account,strat_manager,risk_per_trade,data_store=None):
        """
        Portfolio object to execute signals and create orders, responsible for position sizing.

        :param events_queue:
        :param prices: candle feed for symbols
        :param account: account object
        :param strat_manager: strategy manager object
        :param risk_per_trade: risk per trade in percent
        :param data_store: object responsible for storing the data
        :return: none
        """

        self.events = events_queue
        self.prices = prices
        self.account =account
        self.manager = strat_manager
        self.equity = account.equity
        self.starting_equity = account.equity
        self.risk = risk_per_trade
        self.data_store = data_store
        self.symbol_list = self.prices.instruments_list
        self.compound = True

        # Containers for history and  trades
        self.open_trades = []
        self.open_orders = []
        self._check_account_trades()
        self.history=[]
        self.closed_trades=[]


    def _setup_strategies(self,strategies):
        strategy={}
        weight={}
        for strat in strategies:
            strategy[strat.identifier]=strat
            weight[strat.identifier]= 1/len(strategies)

        return strategy,weight

    def _check_account_trades(self):
        if self.account.open_trades == True:
            # Create a Trade for each opened trades
            trade_list = self.account.trades_info()
            for trade in trade_list:
                if trade.strategy == 'unknown':
                    strategy = self.data_store.find_trade(trade.ticket)['strategy']
                    trade.strategy=strategy
                    #TODO: The manager must handle the initial trade conditions
                    #self.strategies[trade.strategy].invested[trade.instrument]='LONG' if trade.side=='buy' else 'SHORT'
                    #self.strategies[trade.strategy].stop_loss[trade.instrument]=trade.stop_loss
                self.open_trades.append(trade)
        if self.account.open_orders == True:
            # Create an Order object for each opened object
            order_list = self.account.orders_info()
            for order in order_list:
                self.open_orders.append(order)


    def add_new_trade(self,event):
        # Converts a FillEvent to Trade object and put it in trades list
        trade = Trade(ticket=event.ticket, side = event.side, instrument=event.instrument, units=event.units,
                      open_price=event.price, open_date=event.open_date, strategy=event.strategy,
                      stop_loss=event.stop_loss, take_profit=event.take_profit, trailing_stop=event.trailing_stop)
        self.open_trades.append(trade)

        #Notify the strategy
        if event.side =='buy':
            self.manager.set_invested(event.strategy,event.instrument,'LONG')
        else:
            self.manager.set_invested(event.strategy,event.instrument,'SHORT')
        #self.strategies[event.strategy].invested[event.instrument]='LONG' if event.side=='buy' else 'SHORT'

        #Record to trade_store
        if self.data_store:
            self.data_store.add_open_trade(trade)

    def remove_trade(self,close_event):
        # Get the Trade object, updates it and place it in closed_trades
        for trade in self.open_trades:
            if trade.ticket == close_event.ticket:
                if self.prices.symbols_obj[trade.instrument].use_inverse_rate == True:
                    conversion_rate = self.prices.symbols_obj[trade.instrument].inverse_rate
                    conversion_factor = 1 / self.prices.get_home_quote(conversion_rate)
                else:
                    conversion_rate = self.prices.symbols_obj[trade.instrument].conversion_rate
                    conversion_factor = self.prices.get_home_quote(conversion_rate)
                trade.update_trade(cur_price=close_event.close_price,conversion_factor=conversion_factor)
                trade.close_price = close_event.close_price
                trade.close_date = close_event.close_date
                self.equity += trade.pnl

                self.closed_trades.append(trade)
                self.open_trades.remove(trade)

                # Notify the strategy
                #self.strategies[trade.strategy].invested[close_event.instrument]='OUT'
                self.manager.set_invested(trade.strategy,close_event.instrument,'OUT')

                #Record to trade_store
                if self.data_store:
                    self.data_store.add_close_trade(trade)

    def on_bar(self):
        # Updates every Trade in open_trade and record metrics
        pnl = 0.0
        exposure = dict(zip(self.symbol_list,np.zeros(len(self.symbol_list))))
        for trade in self.open_trades:
            price = self.prices.get_latest_bar_value(trade.instrument)
            if self.prices.symbols_obj[trade.instrument].use_inverse_rate == True:
                conversion_rate = self.prices.symbols_obj[trade.instrument].inverse_rate
                conversion_factor = 1 / self.prices.get_home_quote(conversion_rate)
            else:
                conversion_rate = self.prices.symbols_obj[trade.instrument].conversion_rate
                conversion_factor = self.prices.get_home_quote(conversion_rate)
            trade.update_trade(price,conversion_factor)

            #records for history
            pnl += trade.pnl
            direction = 1 if trade.side=='buy' else -1
            exposure[trade.instrument] += trade.units*direction
        self.history.append([self.prices.get_latest_bar_datetime(self.symbol_list[0]),pnl,self.equity,exposure])

    def execute_signal(self,signal_event):
        if signal_event.side == 'buy' or signal_event.side == 'sell':
            # Convert the SignalEvent into OrderEvent
            open_price=self.prices.get_latest_bars_values(signal_event.instrument,"close")
            if self.prices.symbols_obj[signal_event.instrument].use_inverse_rate == True:
                conversion_rate = self.prices.symbols_obj[signal_event.instrument].inverse_rate
                conversion_factor = 1 / self.prices.get_home_quote(conversion_rate)
            else:
                conversion_rate = self.prices.symbols_obj[signal_event.instrument].conversion_rate
                conversion_factor = self.prices.get_home_quote(conversion_rate)
            units = self._calculate_position_size(open_price,signal_event.stop_loss,conversion_factor)
            units = int(units)

            order = OrderEvent(signal_event.instrument,units=units, order_type=signal_event.order_type,side = signal_event.side,
                               strategy=signal_event.strategy, stop_loss=signal_event.stop_loss)
            self.events.put(order)

        elif signal_event.side == 'exit':
            # Converts the SignalEvent into ExitOrderEvent
            for trade in self.open_trades:
                if trade.instrument == signal_event.instrument and trade.strategy == signal_event.strategy:
                    #Close this trade
                    exit_order = ExitOrderEvent(trade)
                    self.events.put(exit_order)
                    break

    def _calculate_position_size(self,open_price,stop_loss,conversion_factor):
        if self.compound == True:
            position_size = (self.equity * self.risk) / (abs(stop_loss-open_price)*conversion_factor)
            #print(position_size)
            return position_size if position_size > 0 else 0
        else:
            position_size = (self.starting_equity * self.risk) / (abs(stop_loss-open_price)*conversion_factor)
            return position_size if position_size > 0 else 0