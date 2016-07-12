import pandas as pd
import pymongo

class FakeAccount(object):

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