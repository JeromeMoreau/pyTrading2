import queue
import time
import threading

class TradingEngine(object):
    def __init__(self,heartbeat,events_queue,account,data_handler,execution_handler,portfolio,strategies):
        """

        :param heartbeat:
        :param events_queue:
        :param account:
        :param data_handler:
        :param execution_handler:
        :param portfolio:
        :param strategies:
        :return:
        """

        self.heartbeat =heartbeat
        self.events = events_queue
        self.account = account
        self.prices = data_handler
        self.execution = execution_handler
        self.portfolio = portfolio
        self.strategies = self._setup_strategies(strategies)

        #Create Threads
        self.engine_thread=threading.Thread(target=self.start_engine,args=[])
        self.price_thread = threading.Thread(target=self.prices.stream.stream_prices,args=[])
        self.event_thread = threading.Thread(target=self.prices.stream.stream_events,args=[])

    def _setup_strategies(self,strategies):
        dict = {}
        for strat in strategies:
            dict[strat.identifier] = strat
        return dict

    def start_engine(self):
        while True:
            try:
                event = self.events.get(False)
            except queue.Empty:
                pass
            else:
                # Handle the event
                if event.type =='MARKET':
                    for strat in self.strategies:
                        self.strategies[strat].calculate_signals(event)
                    self.portfolio.on_bar()
                elif event.type =='SIGNAL':
                    self.portfolio.execute_signal(event)
                elif event.type =='ORDER' or event.type=='EXIT_ORDER':
                    self.execution.execute_order(event)
                elif event.type == 'FILL':
                    self.portfolio.add_new_trade(event)
                elif event.type == 'TRADE_CLOSE':
                    self.portfolio.remove_trade(event)

            time.sleep(self.heartbeat)
        print('WARNING: Exiting Trading Engine loop')

    def start_live_trading(self):
        self.engine_thread.start()
        self.price_thread.start()
        self.event_thread.start()