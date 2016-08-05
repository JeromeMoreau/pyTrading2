import pyprind
import metrics
import queue

class BacktestEngine(object):
    def __init__(self,events_queue,data_handler,execution_handler,portfolio,strat_manager):
        """
        Initialises the backtest.

        :param events_queue:
        :param data_handler:
        :param execution_handler:
        :param account_handler:
        :param portfolio:
        :param strategies:
        :return:
        """
        self.events = events_queue
        self.data_handler = data_handler
        self.execution_handler = execution_handler
        self.portfolio = portfolio
        self.manager = strat_manager

        #Whether or not to show the progress bar and the results
        self.show_progression = True


    def _run_backtest(self):
        """
        Execute the backtest
        :return:
        """
        if self.show_progression==True: bar = pyprind.ProgBar(self.data_handler.data_length)

        #Start the loop
        while True:
            if self.show_progression == True: bar.update()

            #Update the market bars
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars()
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
                        self.manager.calculate_signals(market_event=event)
                        #Update the portfolio
                        self.portfolio.on_bar()
                    elif event.type == 'SIGNAL':
                        self.portfolio.execute_signal(event)
                    elif event.type == 'ORDER' or event.type == 'EXIT_ORDER':
                        self.execution_handler.execute_order(event)
                    elif event.type == 'FILL':
                        self.portfolio.add_new_trade(event)
                    elif event.type == 'TRADE_CLOSED':
                        self.portfolio.remove_trade(event)

    def _output_performance(self):
        self.stats = metrics.Statistics(self.portfolio)




    def backtest_trading(self):
        """
        Simulates the bactest and outputs portfolio performance
        """
        self._run_backtest()
        self._output_performance()




