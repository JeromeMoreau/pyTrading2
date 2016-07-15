from events import OrderEvent, ExitOrderEvent
from trade import Trade
import numpy as np

class Portfolio(object):
    def __init__(self,events_queue,prices,account,strategies,risk_per_trade,open_trades=[]):
        """
        Portfolio object to execute signals and create orders, responsible for position sizing.

        :param events_queue:
        :param account:
        :param strategies:
        :param risk_per_trade:
        :param trades:
        :return:
        """

        self.events = events_queue
        self.prices = prices
        self.account =account
        self.strategies,self.weigths = self._setup_strategies(strategies)
        self.equity = account.equity
        self.risk = risk_per_trade
        self.open_trades = open_trades
        self.symbol_list = self.prices.instruments_list

        # Containers for history and closed trades
        self.history=[]
        self.closed_trades=[]


    def _setup_strategies(self,strategies):
        strategy={}
        weight={}
        for strat in strategies:
            strategy[strat.identifier]=strat
            weight[strat.identifier]= 1/len(strategies)

        return strategy,weight

    def add_new_trade(self,event):
        # Converts a FillEvent to Trade object and put it in trades list
        trade = Trade(ticket=event.ticket, side = event.side, instrument=event.instrument, units=event.units,
                      open_price=event.price, open_date=event.open_date, strategy=event.strategy,
                      stop_loss=event.stop_loss, take_profit=event.take_profit, trailing_stop=event.trailing_stop)
        self.open_trades.append(trade)

        #Notify the strategy
        self.strategies[event.strategy].invested[event.instrument]='LONG' if event.side=='buy' else 'SHORT'

    def remove_trade(self,close_event):
        # Get the Trade object, updates it and place it in closed_trades
        for trade in self.open_trades:
            if trade.ticket == close_event.ticket:
                conversion_factor = self.prices.get_home_quote(self.prices.symbols_obj[trade.instrument].conversion_rate)
                trade.update_trade(cur_price=close_event.close_price,conversion_factor=conversion_factor)
                trade.close_price = close_event.close_price
                trade.close_date = close_event.close_date
                self.equity += trade.pnl

                self.closed_trades.append(trade)
                self.open_trades.remove(trade)

                # Notify the strategy
                self.strategies[close_event.strategy].invested[close_event.instrument]='OUT'

    def on_bar(self):
        # Updates every Trade in open_trade and record metrics
        pnl = 0.0
        exposure = dict(zip(self.symbol_list,np.zeros(len(self.symbol_list))))
        for trade in self.open_trades:
            price = self.prices.get_latest_bar_value(trade.instrument)
            conversion_factor = self.prices.get_home_quote(self.prices.symbols_obj[trade.instrument].conversion_rate)
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
            conversion_factor = self.prices.get_home_quote(self.prices.symbols_obj[signal_event.instrument].conversion_rate)
            units = self._calculate_position_size(open_price,signal_event.stop_loss,conversion_factor)
            units = int(units * self.weigths[signal_event.strategy])

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
        position_size = (self.equity * self.risk) / (abs(stop_loss-open_price)*conversion_factor)

        return position_size if position_size > 0 else 0