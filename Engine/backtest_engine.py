import queue
import pyprind
from Statistics.backtest_statistics import Statistics
from Engine.trading_engine import TradingEngine


class BacktestEngine(TradingEngine):
    """
    Implementation of a TradingEngine to be used for backtests. It runs on a single thread
    """

    def __init__(self,events,data_handler,execution_handler,portfolio,strategy_manager,data_store=None):

        # Init the TradingEngine
        super().__init__(events,data_handler,execution_handler,portfolio,strategy_manager,data_store)

        #Whether or not to show the progress bar and the results
        self.show_progression = True


    def _run_backtest(self):
        """
        Execute the backtest in a loop until the data_handler has no more data.
        """
        if self.show_progression==True: bar = pyprind.ProgBar(self.data.data_length)

        # Start the loop
        while True:
            if self.show_progression: bar.update()

            # Update the market bars
            if self.data.continue_backtest:
                self.data.update_bars()
            else:
                break

            # Handle the events
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event.type =='MARKET':
                        #Notify the strategies
                        self.strategy_manager.calculate_signals(market_event=event)
                        #Update the portfolio
                        self.portfolio.on_bar()
                    elif event.type == 'SIGNAL':
                        self.portfolio.execute_signal(event)
                    elif event.type == 'ORDER' or event.type == 'EXIT_ORDER':
                        self.execution.execute_order(event)
                    elif event.type == 'FILL':
                        self.portfolio.add_new_trade(event)
                    elif event.type == 'TRADE_CLOSED':
                        self.portfolio.remove_trade(event)

                    if self.has_data_store:
                        self.data_store.add_event(event)

    def _output_performance(self):
        self.stats = Statistics(self.portfolio)

    def run(self):
        self._run_backtest()
        self._output_performance()