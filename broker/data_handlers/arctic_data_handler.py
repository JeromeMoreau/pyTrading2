from datetime import datetime
from arctic import Arctic
import pandas as pd
import numpy as np
from events import MarketEvent
from broker.symbol import Symbol
from broker.data_handlers.data_handler import AbstractDataHandler

class ArcticDatabaseDataHandler(AbstractDataHandler):

    def __init__(self,events_queue, symbol_list,account,db_adress='localhost', timeframe='D1',
                 start_date = datetime(2001,1,1), end_date=datetime(2015,1,1),data_vendor='FX'):

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
        store = Arctic(db_adress)
        library = store['FOREX_SYMBOLS']
        items = library.read('oanda_symbols')
        instruments = pd.DataFrame(items.data).set_index('instrument')
        return instruments

    def _get_data_from_database(self,db_adress):
        store = Arctic(db_adress)
        library = store['FOREX_DATA']

        order = ['open','high','low','close']
        for instrument in self.instruments_list:
            #Creates a symbol object and get the data
            info = self.instruments_info.ix[instrument[:3]+'_'+instrument[-3:]]
            conversion_rate = info.currency + self.account.currency
            inverse_rate=conversion_rate[-3:]+conversion_rate[:3]
            symbol = Symbol(instrument,self.timeframe,conversion_rate,inverse_rate,margin=info.marginRate,one_pip=info.pip)

            db_data = library.read(instrument)
            self.data[instrument]= pd.DataFrame(db_data.data).set_index('datetime')[order]
            self.data[instrument] = self.data[instrument].truncate(before=self.start_date, after=self.end_date)
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
        for instrument,symbol in self.symbols_obj.items():
            conversion_symbol = symbol.conversion_rate
            inverse_symbol = symbol.conversion_rate[3:] + symbol.conversion_rate[:3]
            self.latest_data[conversion_symbol] = []

            if library.has_symbol(conversion_symbol):
                db_data = library.read(conversion_symbol)
                self.data[conversion_symbol] = pd.DataFrame(db_data.data)[['datetime', 'close']].set_index('datetime')

            elif library.has_symbol(inverse_symbol):
                db_data = library.read(inverse_symbol)
                self.data[conversion_symbol] = 1 / pd.DataFrame(db_data.data)[['datetime', 'close']].set_index('datetime')

            elif conversion_symbol[:3] == conversion_symbol[3:]:
                self.data[conversion_symbol] = pd.DataFrame(np.ones(len(self.comb_index)),index=self.comb_index,columns=['close'])

            else:
                print('Pairs %s and %s not available in DB' % (conversion_symbol, inverse_symbol))

        # Creates the generator
        #print('Data fetched from db',flush=True)
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
        #print('Generator reseted',flush=True)


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