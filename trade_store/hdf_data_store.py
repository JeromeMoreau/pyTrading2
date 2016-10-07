from datetime import datetime

import h5py

from settings import DATA_DIR
from trade_store.base_data_store import AbstractDataStore


class HDFDataStore(AbstractDataStore):

    def __init__(self,filename=None):
        self.filename = filename if filename is not None else "trade_store"
        self.data_dir = DATA_DIR
        self.file = h5py.File(filename+"_"+datetime.utcnow(),'a',)
        self.dset = self.file.create_dataset('trades')


    def add_open_trade(self, trade):

        pass

    def add_close_trade(self, trade):
        pass

    def getTradeById(self, id):
        trade = self.dset





