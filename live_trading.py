import queue

#imports for debugging
from broker.execution_handler import OandaExecution

from strategies.donchian_breakout import DonchianBreakout
from strategies.RSI_MOM_2 import RSI_Trading_Strategy
from strategies.PA_test import PA_Test

from broker.data_handlers.oanda_data_handler import OandaDataHandler
from portfolio import Portfolio
from settings import DOMAIN, ACCESS_TOKEN, OANDA_ACCOUNT_ID
from broker.account import OandaAccount
from strategy_manager import StrategyManager
from Engine.live_engine import LiveEngine
from trade_store.mongo_data_store import MongoTradeStore




if __name__ == "__main__":
    heartbeat = 1
    events = queue.Queue()
    symbol_list = ['EUR_USD','AUD_USD']
    risk = 0.02

    account = OandaAccount(DOMAIN, ACCESS_TOKEN, OANDA_ACCOUNT_ID)
    store = MongoTradeStore('TRADES',record_tick=False)

    prices = OandaDataHandler(account,events,["EUR_USD","AUD_USD","GBP_USD"],'M5',data_store=store)
    execution = OandaExecution(events_queue=events,account=account)

    strategy_1 = DonchianBreakout(prices,events, entry_lookback=20, exit_lookback=20, atr_stop=3.,TP_atr=5.,name='DC_20x20')
    strategy_2 = DonchianBreakout(prices,events, entry_lookback=50, exit_lookback=30, atr_stop=3.,TP_atr=5.,name='DC_50x30')
    strategy_3 = DonchianBreakout(prices,events, entry_lookback=100, exit_lookback=50, atr_stop=3.,TP_atr=5.,name='DC_100x50')
    strategy_4 = DonchianBreakout(prices,events, entry_lookback=200, exit_lookback=100, atr_stop=3.,TP_atr=5.,name='DC_200x100')
    strategy_5 = RSI_Trading_Strategy(prices,events,rsi_lookback=15, rsi_trigger_offset=25,trailing_stop_atr=1.8, take_profit_atr=3)
    strategy_6 = PA_Test(prices,events,atr_stop=1.8,TP_atr=4.)
    manager = StrategyManager([strategy_1,strategy_2,strategy_3,strategy_4,strategy_5,strategy_6])


    portfolio = Portfolio(events_queue=events, prices=prices,account=account, risk_per_trade = risk,strat_manager=manager,data_store=store)

    engine = LiveEngine(heartbeat,events,prices,execution,portfolio,manager)
    engine.run()
