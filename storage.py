import pymongo

class MongoTradeStore(object):
    def __init__(self,db_adress,db_name):
        self.trade_store = self._connect_to_mongodb(db_adress,db_name)


    def _connect_to_mongodb(self,db_adress,db_name):
        client = pymongo.MongoClient(db_adress)
        database = client['TRADES']
        collection = database[db_name]
        return collection

    def add_open_trade(self,trade):
        #Receive a Trade (object) and put it into the database
        json = {'ticket':trade.ticket,
                'side':trade.side,
                'instrument':trade.instrument,
                'units':trade.units,
                'open_price':trade.open_price,
                'open_date':trade.open_date,
                'strategy':trade.strategy,
                'stop_loss':trade.stop_loss,
                'take_profit':trade.take_profit,
                'trailing_stop':trade.trailing_stop,
                'close_date':trade.close_date,
                'close_price':trade.close_price,
                'pnl':trade.pnl}

        result = self.trade_store.insert_one(json)
        print('DataStore: open trade added',result)


    def find_trade(self,ticket):
        trade = self.trade_store.find_one({'ticket':ticket})
        return trade

    def add_close_trade(self,trade):
        json = {'ticket':trade.ticket,
                'side':trade.side,
                'instrument':trade.instrument,
                'units':trade.units,
                'open_price':trade.open_price,
                'open_date':trade.open_date,
                'strategy':trade.strategy,
                'stop_loss':trade.stop_loss,
                'take_profit':trade.take_profit,
                'trailing_stop':trade.trailing_stop,
                'close_date':trade.close_date,
                'close_price':trade.close_price,
                'pnl':trade.pnl}
        result = self.trade_store.replace_one({'ticket':trade.ticket},json)
        print('DataStore: close trade added',result)

class CSVTradeStore(object):
    def __init__(self,path_to_csv):
        self.path = path_to_csv

    def add_open_trade(self,trade):
        pass

    def add_close_trade(self,trade):
        pass

    def find_trade(self,ticket):
        pass