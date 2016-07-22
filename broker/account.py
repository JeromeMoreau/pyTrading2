import pandas as pd
import pymongo
import oandapy
from datetime import datetime
from trade import Trade

class SimulatedAccount(object):

    def __init__(self,equity,leverage,currency):
        self.equity = equity
        self.leverage = leverage
        self.currency = currency
        self.open_trades = False
        self.open_orders = False

    def _instruments_info(self):
        client = pymongo.MongoClient()
        db = client['symbols']
        instruments = db['oanda_symbols'].find({})
        instruments = pd.DataFrame(list(instruments)).set_index('instrument')
        instruments.drop('_id',axis=1,inplace=True)

        return instruments


class OandaAccount(object):
    def __init__(self,environment,access_token,account_id):
        self.environment = environment
        self.token = access_token
        self.id = account_id
        self.currency = 'USD'
        self.equity = 1000.
        self.oanda = oandapy.API(self.environment,self.token)
        self._get_account_infos()


    def _get_account_infos(self):
        infos = self.oanda.get_account(self.id)
        self.equity = infos['balance']
        self.currency = infos['accountCurrency']
        self.open_trades = True if infos['openTrades'] > 0 else False
        self.open_orders =  True if infos['openOrders'] > 0 else False
        self.margin_rate = infos['marginRate']

    def trades_info(self):
        # Creates a list of every Trade
        trades=[]
        tr_list = self.oanda.get_trades(self.id)
        tr_list = tr_list.get('trades')
        for tr in tr_list:
            specs={'ticket':tr['id'],
                   'side':tr['side'],
                   'instrument':tr['instrument'],
                   'units':tr['units'],
                   'open_price':tr['price'],
                   'open_date':datetime.strptime(tr['time'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                   'strategy':'unknown',
                   'stop_loss':tr['stopLoss'],
                   'take_profit':tr['takeProfit'],
                   'trailing_stop':tr['trailingStop'],
                   }
            trades.append(Trade(**specs))

        return trades

    def orders_info(self):
        or_list = self.oanda.get_orders(self.id)
        or_list = or_list.get('orders')
        return or_list

