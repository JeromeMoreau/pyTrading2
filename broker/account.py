import pandas as pd
import pymongo
from broker.symbol import Symbol

class SimulatedAccount(object):

    def __init__(self,equity,leverage,currency):
        self.equity = equity
        self.leverage = leverage
        self.currency = currency
        self.instruments = self._instruments_info()

    def _instruments_info(self):
        client = pymongo.MongoClient()
        db = client['symbols']
        instruments = db['oanda_symbols'].find({})
        instruments = pd.DataFrame(list(instruments)).set_index('instrument')
        instruments.drop('_id',axis=1,inplace=True)

        return instruments

    def get_symbol(self,instrument,timeframe):
        info = self.instruments.ix[instrument[:3]+'_'+instrument[-3:]]
        symbol = Symbol(instrument,timeframe,self.currency,margin=info.marginRate,one_pip=info.pip)
        return symbol

class OandaAccount(object):
    def __init__(self,environment,access_token,account_id):
        self.environment = environment
        self.token = access_token
        self.id = account_id
        self.currency = 'USD'
        self.equity = 1000.
        self.instruments = self._instruments_info()

    def _instruments_info(self):
        client = pymongo.MongoClient()
        db = client['symbols']
        instruments = db['oanda_symbols'].find({})
        instruments = pd.DataFrame(list(instruments)).set_index('instrument')
        instruments.drop('_id',axis=1,inplace=True)

        return instruments

    def get_symbol(self,instrument,timeframe):
        info = self.instruments.ix[instrument[:3]+'_'+instrument[-3:]]
        symbol = Symbol(instrument,timeframe,self.currency,margin=info.marginRate,one_pip=info.pip)
        return symbol