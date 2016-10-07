from trade_store.base_data_store import AbstractDataStore

class CSVDataStore(AbstractDataStore):
    def __init__(self,csv_data_dir,filename_suffix=None):
        self.path = csv_data_dir
        self.suffix = filename_suffix

    def getTradeById(self,id):
        pass

    def add_close_trade(self, trade):
        pass


    def add_open_trade(self, trade):
        pass