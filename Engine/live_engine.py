from Engine.trading_engine import TradingEngine
import queue
import threading
import time
from datetime import datetime
from server.zeroMQ_server import ZMQServer

class LiveEngine(TradingEngine):
    """
    Trading Engine implementation for live trading. Runs on 3 threads:
    """
    def __init__(self,heartbeat,events,data_handler,execution_handler,portfolio,strategy_manager,data_store=None,server=None):

        super().__init__(events,data_handler,execution_handler,portfolio,strategy_manager,data_store)

        self.heartbeat = heartbeat

        #Create Threads
        self.engine_thread=threading.Thread(target=self._start_engine, args=[])
        self.price_thread = threading.Thread(target=self.data.stream.stream_prices, args=[])
        self.event_thread = threading.Thread(target=self.data.stream.stream_events, args=[])

        #Server
        server = ZMQServer(self.portfolio)
        #self.server_thread = server.startAsync()


    def _start_engine(self):
        while True:
            try:
                event = self.events.get(False)
            except queue.Empty:
                pass
            else:
                # Handle the event

                if event.type =='MARKET':
                    self.strategy_manager.calculate_signals(market_event=event)
                    self.portfolio.on_bar()
                elif event.type =='SIGNAL':
                    self.portfolio.execute_signal(event)
                elif event.type =='ORDER' or event.type=='EXIT_ORDER':
                    self.execution.execute_order(event)
                elif event.type == 'FILL':
                    self.portfolio.add_new_trade(event)
                elif event.type == 'TRADE_CLOSED':
                    self.portfolio.remove_trade(event)
                if self.has_data_store:
                    self.data_store.add_event(event)

            time.sleep(self.heartbeat)



    def run(self):
        print('Engine started, time: %s' %datetime.utcnow())
        self.engine_thread.start()
        self.price_thread.start()
        self.event_thread.start()