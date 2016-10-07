import pymongo

from trade_store.base_data_store import AbstractDataStore


class MongoTradeStore(AbstractDataStore):
    def __init__(self, db_name, db_adress='localhost'):
        self.database = self._connect_to_mongodb(db_name, db_adress)

    def _connect_to_mongodb(self, db_name, db_adress):
        client = pymongo.MongoClient(db_adress)
        database = client[db_name]
        return database

    def add_open_trade(self, trade):
        # Receive a Trade (object) and put it into the database

        result = self.database['OPENED_TRADES'].insert_one(trade.to_JSON())

    def add_close_trade(self, trade):
        result = self.database['CLOSED_TRADES'].insert_one(trade.to_JSON())
        result1 = self.database['OPENED_TRADES'].delete_one({'ticket': trade.ticket})
        # result = self.database.replace_one({'ticket':trade.ticket},json)

    def add_event(self,event):
        result = self.database['EVENTS'].insert_one(event.to_JSON())
        print(result)


    def getAllOpenedTrades(self):
        trades = self.database['OPENED_TRADES'].find()
        print(list(trades))

    def getTradeById(self, id):
        trade = self.database.find_one({'ticket': id})
        # TODO: should i create a trade object ?
        return trade
