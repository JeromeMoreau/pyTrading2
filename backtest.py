import pyprind
import metrics
import queue

class BacktestEngine(object):
    def __init__(self,events_queue,data_handler,execution_handler,account_handler,portfolio,strategies):
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
        self.account_handler = account_handler
        self.portfolio = portfolio
        #self.strategy_dict = self._setup_strategies(strategies)
        self.strategies = strategies

        #Whether or not to show the progress bar and the results
        self.show_progression = True
        self.show_results = True



    def _setup_strategies(self,strategies):
        strategy_dict = {}
        for strategy in strategies:
            strategy_dict[strategy.identifier] = strategy

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
                        for strategy in self.strategies:
                            strategy.calculate_signal(event)
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
        stats = metrics.backtest_performance(self.portfolio)
        if self.show_results:
            metrics.plot_performance(self.portfolio)
            print(stats)
        return stats


    def backtest_trading(self):
        """
        Simulates the bactest and outputs portfolio performance
        """
        self._run_backtest()
        self._output_performance()




