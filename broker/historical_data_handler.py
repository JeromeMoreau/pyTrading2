from datetime import datetime
import pymongo
import pandas as pd
import numpy as np
from broker.symbol import Symbol
from events import MarketEvent
import os


class DatabaseDataHandler(object):
    """
    DatabaseDataHandler is designed to query the database for each requested symbol and provide
    an interface to obtain the latest bar in a manner identical to a live trading interface.
    """
    def __init__(self,events_queue, symbol_list,account,db_adress='localhost', timeframe='D1',
                 start_date = datetime(2001,1,1), end_date=datetime(2015,1,1),data_vendor='FX'):
        """
        Initialises the historic data handler by requesting  list of symbols.

        Parameters:
        db_adress - Adress of Mongo database
        events_queue - The Event Queue.
        symbol_list - A list of symbol strings
        timeframe - Timeframe of datafeed
        start_date - Starting date for the backtest
        end_date - Last date for the backtest
        data_vendor - Which data provider to use
        account - Account object containing infos

        NOTE: conversion rate to home currency use D1 close data
        """
        self.events = events_queue
        self.instruments_list = symbol_list
        self.account = account
        self.start_date = start_date
        self.end_date = end_date
        self.timeframe = timeframe
        self.data_vendor = data_vendor

        # Containers for the data and time index to align
        self.data={}
        self.latest_data={}
        self.data_generator={}
        self.comb_index = None

        # Container for Symbol (objects)
        self.symbols_obj = {}

        # Variables for backtesting
        self.continue_backtest = True
        self.data_length = 0

        # Fetch the data from database
        self.instruments_info = self._get_instruments_info(db_adress)
        self._get_data_from_database(db_adress)

    def _get_instruments_info(self,db_adress):
        client = pymongo.MongoClient(db_adress)
        db = client['symbols']
        instruments = db['oanda_symbols'].find({})
        instruments = pd.DataFrame(list(instruments))
        instruments['currency']=instruments.instrument.str[-3:]
        instruments['base']=instruments.instrument.str[:-3]
        instruments.set_index('instrument',inplace=True)
        instruments.drop('_id',axis=1,inplace=True)

        return instruments

    def _get_data_from_database(self,db_adress):

        client = pymongo.MongoClient(db_adress)
        db = None
        if self.timeframe == 'D1' or self.timeframe == 'H1':
            db_name = 'Forex_Master_' + self.timeframe
            db =client[db_name]
            need_resampling = False
        #TODO Support for other timeframes + resampling + data_transformation

        order = ['open','high','low','close']
        for instrument in self.instruments_list:
            #Creates a symbol object and get the data
            info = self.instruments_info.ix[instrument[:3]+'_'+instrument[-3:]]
            conversion_rate = info.currency +self.account.currency
            inverse_rate=conversion_rate[-3:]+conversion_rate[:3]
            symbol = Symbol(instrument,self.timeframe,conversion_rate,inverse_rate,margin=info.marginRate,one_pip=info.pip)

            data = db[instrument].find({'$and': [{'datetime': {"$gte": self.start_date}},
                                                  {'datetime': {"$lte": self.end_date}},
                                                  {'data_vendor': {"$eq": self.data_vendor}}
                                                  ]})
            self.data[instrument]= pd.DataFrame(list(data)).set_index('datetime').drop(['_id','data_vendor'],axis=1)[order]
            self.symbols_obj[instrument]=symbol

            #Create or combine the list of dates
            if self.comb_index is None:
                self.comb_index = self.data[instrument].index
            else:
                self.comb_index.union(self.data[instrument].index)

            #Set the latest_data to none for the instrument
            self.latest_data[instrument]=[]

        self.data_length=len(self.comb_index)


        #Get conversion rate data
        db = client['Forex_Master_D1']
        pairs_available = db.collection_names()

        for instrument,symbol in self.symbols_obj.items():
            conversion_symbol = symbol.conversion_rate
            inverse_symbol = symbol.conversion_rate[3:] + symbol.conversion_rate[:3]
            self.latest_data[conversion_symbol] = []

            if conversion_symbol in pairs_available:
                data = db[conversion_symbol].find({'$and': [{'datetime': {"$gte": self.start_date}},
                                                 {'datetime': {"$lte": self.end_date}}
                                                 ]})
                self.data[conversion_symbol] = pd.DataFrame(list(data))[['datetime', 'close']].set_index('datetime')

            elif inverse_symbol in pairs_available:
                data = db[inverse_symbol].find({'$and': [{'datetime': {"$gte": self.start_date}},
                                                         {'datetime': {"$lte": self.end_date}}
                                                         ]})
                self.data[conversion_symbol] = 1 / pd.DataFrame(list(data))[['datetime', 'close']].set_index('datetime')

            elif conversion_symbol[:3] == conversion_symbol[3:]:
                self.data[conversion_symbol] = pd.DataFrame(np.ones(len(self.comb_index)),index=self.comb_index,columns=['close'])

            else:
                print('Pairs %s and %s not available in DB' % (conversion_symbol, inverse_symbol))

        # Creates the generator
        self.create_generator()

    def create_generator(self):
        #Reindex the dataframes and create generators
        self.data_generator.clear()
        for instrument,symbol in self.symbols_obj.items():
            self.data_generator[instrument]=self.data[instrument].reindex(index=self.comb_index,method='pad').itertuples()
            self.data_generator[symbol.conversion_rate] = self.data[symbol.conversion_rate].reindex(index=self.comb_index,method='pad').itertuples()

    def reset_generator(self):
        self.create_generator()
        self.continue_backtest=True





    def _get_new_bar(self,symbol):
        # Returns the latest bar from the data feed.
        for b in self.data_generator[symbol]:
            yield b

    def get_latest_bars(self, symbol, N=1):
        # Returns the last N bars from the latest_symbol list.
        try:
            bars_list = self.latest_data[symbol]
        except KeyError:
            print("Symbol %s is not available in the historical data set." % symbol)
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_value(self,symbol,val_type='close'):
        # Returns  of OHLCVI values form the pandas Bar series object.
        try:
            bars_list = self.latest_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return getattr(bars_list[-1], val_type)


    def get_latest_bars_values(self, symbol, val_type, N=1):
        # Returns the last N bar values from the latest_symbol list, or N-k if less available.
        bars_list = self.get_latest_bars(symbol, N)

        return np.array([getattr(b, val_type) for b in bars_list])

    def get_latest_bar_datetime(self, symbol):
        # Returns a Python datetime object for the last bar.
        try:
            bars_list = self.latest_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1][0]

    def update_bars(self):
        # pushes the latest bar to the latest_symbol_data structure for all symbols in the symbol list.
        for s in self.data_generator:
            try:
                bar = next(self._get_new_bar(s))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_data[s].append(bar)

        self.events.put(MarketEvent())

    def get_home_quote(self, currency):
        # Returns the conversion factor
        quote = self.get_latest_bar_value(currency)
        return quote


class CSVDataHandler(object):
    def __init__(self,events_queue, symbol_list,account,csv_dir='sample_data/', timeframe='D1',
                 start_date = datetime(2001,1,1), end_date=datetime(2015,1,1)):
        self.events = events_queue
        self.instruments_list = symbol_list
        self.account = account
        self.start_date = start_date
        self.end_date = end_date
        self.csv_dir = csv_dir
        self.timeframe = timeframe


        # Containers for the data and time index to align
        self.data={}
        self.latest_data={}
        self.data_generator={}
        self.comb_index = None

        # Container for Symbol (objects)
        self.symbols_obj = {}

        # Variables for backtesting
        self.continue_backtest = True
        self.data_length = 0

        # Fetch the data from database
        self.pairs_available = self._get_instruments_info()
        self._load_data()

    def _get_instruments_info(self):
        pairs_available = []
        directory = self.csv_dir+self.timeframe
        for file in os.listdir(directory):
            if file.endswith(".csv"):
                pairs_available.append(file[:-4])

        return pairs_available

    def _load_data(self):

        for instrument in self.instruments_list:
            if instrument not in self.pairs_available:
                print('Symbol %s not in the csv_dir specified' %instrument)
                break

            conversion_rate = instrument[-3:] + self.account.currency
            inverse_rate = conversion_rate[-3:]+conversion_rate[:3]
            symbol = Symbol(instrument,self.timeframe,conversion_rate,inverse_rate,0)
            if conversion_rate not in self.pairs_available and inverse_rate in self.pairs_available:
                symbol.use_inverse_rate == True
            elif inverse_rate not in self.pairs_available:
                print('Neither conversion rate %s or inverse rate %s is available in csv_dir' %(conversion_rate,inverse_rate))

            self.symbols_obj[instrument]=symbol

            #Get the data
            csv_data = self._load_csv(instrument,self.timeframe)
            self.data[instrument] = csv_data.truncate(before=self.start_date, after=self.end_date)

            #Create or combine the list of dates
            if self.comb_index is None:
                self.comb_index = self.data[instrument].index
            else:
                self.comb_index.union(self.data[instrument].index)

            #Set the latest_data to none for the instrument
            self.latest_data[instrument]=[]

            self.data_length=len(self.comb_index)

            #Load conversion data
            if symbol.conversion_rate == 'USDUSD':
                self.data[symbol.conversion_rate]=pd.DataFrame(np.ones(len(self.comb_index)),index=self.comb_index,columns=['close'])
                self.latest_data[symbol.conversion_rate]=[]
            else:
                if symbol.use_inverse_rate==True:
                    conversion_data = 1/ self._load_csv(symbol.inverse_rate,self.timeframe)
                    self.data[symbol.conversion_rate]=conversion_rate.truncate(before=self.start_date, after=self.end_date)
                    self.latest_data[symbol.conversion_rate]=[]
                else:
                    conversion_data = self._load_csv(symbol.conversion_rate,self.timeframe)
                    self.data[symbol.conversion_rate]=conversion_data.truncate(before=self.start_date, after=self.end_date)
                    self.latest_data[symbol.conversion_rate]=[]

        self.create_generators()


    def _load_csv(self,symbol,timeframe):
            file_adress = self.csv_dir+timeframe+'/'+symbol+'.csv'
            csv_data = pd.read_csv(file_adress,header=0, index_col=0,parse_dates={'datetime': [1, 2]})
            csv_data.drop('<TICKER>',axis=1,inplace=True)
            csv_data.columns = ['open','low','high','close']

            return csv_data[['open','high','low','close']]

    def create_generators(self):
        #Reindex the dataframes and create generators
        self.data_generator.clear()
        for instrument,symbol in self.symbols_obj.items():
            self.data_generator[instrument]=self.data[instrument].reindex(index=self.comb_index,method='pad').itertuples()
            self.data_generator[symbol.conversion_rate] = self.data[symbol.conversion_rate].reindex(index=self.comb_index,method='pad').itertuples()



    def _get_new_bar(self,symbol):
        # Returns the latest bar from the data feed.
        for b in self.data_generator[symbol]:
            yield b

    def get_latest_bars(self, symbol, N=1):
        # Returns the last N bars from the latest_symbol list.
        try:
            bars_list = self.latest_data[symbol]
        except KeyError:
            print("Symbol %s is not available in the historical data set." % symbol)
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_value(self,symbol,val_type='close'):
        # Returns  of OHLCVI values form the pandas Bar series object.
        try:
            bars_list = self.latest_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return getattr(bars_list[-1], val_type)


    def get_latest_bars_values(self, symbol, val_type, N=1):
        # Returns the last N bar values from the latest_symbol list, or N-k if less available.
        bars_list = self.get_latest_bars(symbol, N)

        return np.array([getattr(b, val_type) for b in bars_list])

    def get_latest_bar_datetime(self, symbol):
        # Returns a Python datetime object for the last bar.
        try:
            bars_list = self.latest_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1][0]

    def update_bars(self):
        # pushes the latest bar to the latest_symbol_data structure for all symbols in the symbol list.
        for s in self.data_generator:
            try:
                bar = next(self._get_new_bar(s))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_data[s].append(bar)

        self.events.put(MarketEvent())

    def get_home_quote(self, currency):
        # Returns the conversion factor
        quote = self.get_latest_bar_value(currency)
        return quote