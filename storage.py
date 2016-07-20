import pymongo

class MongoTradeStore(object):
    def __init__(self,db_adress,db_name):
        self.trade_store = self._connect_to_mongodb(db_adress,db_name)


    def _connect_to_mongodb(self,db_adress,db_name):
        client = pymongo.MongoClient(db_adress,db_name)
        collection = client[db_name]
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
                'close_price':trade.close_price}

        self.trade_store.insert_one(json)

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
                'close_price':trade.close_price}
        self.trade_store.replace_one({'ticket':trade.ticket},json)

