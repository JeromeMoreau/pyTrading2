import queue
import time
import threading
from datetime import datetime

#imports for debugging
from broker.execution_handler import OandaExecution
from strategies.donchian_breakout import DonchianBreakout
from broker.oanda_data_handler import OandaDataHandler
from portfolio import Portfolio
from settings import DOMAIN, ACCESS_TOKEN, OANDA_ACCOUNT_ID
from broker.account import OandaAccount
from server.server import Server
from storage import MongoTradeStore


class TradingEngine(object):
    def __init__(self,heartbeat,events_queue,account,data_handler,execution_handler,portfolio,strategies,server=None):
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
        self.server = server

        #Create Threads
        self.engine_thread=threading.Thread(target=self.start_engine,args=[])
        self.price_thread = threading.Thread(target=self.prices.stream.stream_prices,args=[])
        self.event_thread = threading.Thread(target=self.prices.stream.stream_events,args=[])
        #self.server_thread = threading.Thread(target=self.server._start_server,args=[])

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
                print(event)
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
                elif event.type == 'TRADE_CLOSED':
                    self.portfolio.remove_trade(event)

            time.sleep(self.heartbeat)
        print('WARNING: Exiting Trading Engine loop')

    def start_live_trading(self):
        self.engine_thread.start()
        self.price_thread.start()
        self.event_thread.start()
        #self.server_thread.start()



if __name__ == "__main__":
    heartbeat = 1
    events = queue.Queue()
    symbol_list = ['EUR_USD','AUD_USD']
    risk = 0.02

    account = OandaAccount(DOMAIN, ACCESS_TOKEN, OANDA_ACCOUNT_ID)

    prices = OandaDataHandler(account,events,["EUR_USD","AUD_USD"],'S30')
    execution = OandaExecution(events_queue=events,account=account)

    strategy_1 = DonchianBreakout(prices,events, entry_lookback=20, exit_lookback=20, atr_stop=3.,TP_atr=5.,name='DC_20x20')
    strategy_2 = DonchianBreakout(prices,events, entry_lookback=50, exit_lookback=30, atr_stop=3.,TP_atr=5.,name='DC_50x30')
    strategy_3 = DonchianBreakout(prices,events, entry_lookback=100, exit_lookback=50, atr_stop=3.,TP_atr=5.,name='DC_100x50')
    strategy_4 = DonchianBreakout(prices,events, entry_lookback=200, exit_lookback=100, atr_stop=3.,TP_atr=5.,name='DC_200x100')
    strategies = [strategy_1,strategy_2,strategy_3,strategy_4]

    data_store= MongoTradeStore(db_adress='localhost',db_name='test')
    portfolio = Portfolio(events_queue=events, prices=prices,account=account, risk_per_trade = risk,strategies=strategies,data_store=data_store)
    #server = Server(account,portfolio)

    engine = TradingEngine(heartbeat,events,account,prices,execution,portfolio,strategies)
    engine.start_live_trading()
    print('Engine started, time: %s' %datetime.utcnow())