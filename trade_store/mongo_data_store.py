import pymongo
from datetime import datetime,timezone
from arctic import Arctic

from trade_store.base_data_store import AbstractDataStore


class MongoTradeStore(AbstractDataStore):
    def __init__(self, db_name, db_adress='localhost', record_tick=True):
        self.database = self._connect_to_mongodb(db_name, db_adress)
        if record_tick==False: self.store = Arctic('localhost')
        self.record_tick = record_tick

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

    def addTickToDB(self,data):
        """
        Add the tick to the db
        :return:
        """
        if self.record_tick == False: return
        library = self.store['TICKS']
        tick = {"pair":data["instrument"],"bid":data['bid'],"ask":data['ask'],"index":datetime.now(timezone.utc)}
        library.write('oanda_ticks',[tick])

    def addEventToDB(self,data,broker):
        """
        Add the events received from the broker to DB - useful for debugging
        data: the event data in a dict format
        broker: the broker name
        :return:
        """
        data = data['transaction']
        data['broker']=broker
        self.database['EVENTS'].insert_one(data)
