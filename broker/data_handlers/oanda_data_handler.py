from broker.streamer import Streaming
from broker.symbol import Symbol
from broker.data_handlers.data_handler import AbstractDataHandler
from events import MarketEvent
from datetime import datetime
import re
from errors import UnknownGranularity, UnknowSymbolName
import oandapy
import pandas as pd
import numpy as np
from broker.oanda_event_handler import EventHandler


def granularity_to_time(s):
    """
       get value in seconds for named granularities: M1, M5 ... H1 etc.
    """
    mfact = {
        'S': 1,
        'M': 60,
        'H': 3600,
        'D': 86400,
    }
    try:
        f, n = re.match("(?P<f>[SMHD])(?:(?P<n>\d+)|)", s).groups()
        n = n if n else 1
        return mfact[f] * int(n)
    except:
        raise UnknownGranularity(s)


class CandleGenerator(object):
    def __init__(self,instrument,granularity):
        self.instrument = instrument
        self.frameTime = granularity_to_time(granularity)
        self.granularity = granularity
        self.data = None
        self.start = None
        self.end = None


    def initData(self,tick):
        #init the candle, calculate the boundaries based on the tick timestamp
        self.start = tick.epoch - (tick.epoch % self.frameTime)
        self.end = tick.epoch - (tick.epoch % self.frameTime) + self.frameTime
        self.data = {
            'instrument': self.instrument,
            'start': self.start,
            'end': self.end,
            'granularity': self.granularity,
            'completed': False,
            'data': {
                'open':tick.price,
                'high':tick.price,
                'low':tick.price,
                'close':tick.price,
                'volume':1
            }
        }

    def make_candle(self,completed=False):
        self.data['completed']=completed
        return self.data.copy()

    def process_tick(self,tick):
        if not self.data:
            self.initData(tick)
            return None
        elif tick.epoch >= self.start and tick.epoch < self.end:
            #add the tick to this candle
            if tick.price > self.data['data']['high']:
                self.data['data']['high'] = round(tick.price,5)
            if tick.price < self.data['data']['low']:
                self.data['data']['low'] = round(tick.price,5)
            if tick.price != self.data['data']['close']:
                self.data['data']['close'] = round(tick.price,5)
            self.data['data']['volume'] += 1
            return None
        else:
            #close the candle and send it
            candle = self.make_candle(completed=True)
            self.initData(tick)
            return candle


class OandaDataHandler(AbstractDataHandler):
    def __init__(self,account,events_queue,instruments_list,granularity,data_store=None):
        super().__init__(account,events_queue,instruments_list,granularity,data_store)

        # Objects for handling ticks and events
        self.event_handler = EventHandler(events_queue)
        self.stream = Streaming(instruments_list=instruments_list, account=account,data_handler=self,event_handler=self.event_handler,data_store=self.data_store)

        # Containers for price data
        self.data = {}
        self.symbols_obj={}
        self.instruments_info = self._get_instruments_info()
        self.candles = self._setup_pairs()


    def _get_instruments_info(self):
        oanda = oandapy.API(self.account.environment,self.account.token)
        data = oanda.get_instruments(self.account.id,fields="marginRate,pip,displayName,maxTradeUnits,halted").get('instruments')
        instruments=pd.DataFrame(list(data))
        instruments['currency']=instruments.instrument.str[-3:]
        instruments['base']=instruments.instrument.str[:-4]
        instruments.set_index('instrument',inplace=True)

        return instruments


    def _setup_pairs(self):

        candles={}
        oanda = oandapy.API(self.account.environment,self.account.token)
        for instrument in self.instruments_list:

            # Create a CandleGenerator for every instrument
            candles[instrument] = CandleGenerator(instrument,self.granularity)

            # Create a symbol object and add conversion rate to stream
            info = self.instruments_info.ix[instrument]
            conversion_rate = info.currency +'_'+self.account.currency
            inverse_rate=conversion_rate[-3:]+'_'+conversion_rate[:3]
            symbol = Symbol(instrument,self.granularity,conversion_rate,inverse_rate,margin=info.marginRate,one_pip=info.pip)
            self.symbols_obj[instrument]=symbol

            if symbol.conversion_rate[:3] != symbol.conversion_rate[-3:]:
                conversion_rate = symbol.conversion_rate
                inverse_rate = symbol.inverse_rate
                if conversion_rate in self.instruments_info.index:
                    self.stream.add_instrument(symbol.conversion_rate[:3]+'_'+symbol.conversion_rate[-3:])
                    candles[symbol.conversion_rate] = CandleGenerator(symbol.conversion_rate,self.granularity)
                elif inverse_rate in self.instruments_info.index:
                    print('Portfolio: Using inverse symbol for conversion')
                    symbol.use_inverse_rate = True
                    self.stream.add_instrument(inverse_rate)
                    candles[symbol.conversion_rate] = CandleGenerator(symbol.conversion_rate,self.granularity)
                else:
                    print('Portfolio: Conversion instrument %s not found for symbol %s' %(symbol.conversion_rate,symbol.name))


            # Populate container self.data with some initial data
            self.data[instrument] = self._get_oanda_history(instrument,self.granularity)

        return candles

    def _get_oanda_history(self,instrument,granularity,count=100):
        oanda = oandapy.API(self.account.environment,self.account.token)
        history = oanda.get_history(instrument=instrument,granularity=self.granularity,candleFormat='midpoint',
                                    count=count,alignementTimezone="Europe/london")
        history = history.get('candles')
        order=['time','openMid','highMid','lowMid','closeMid','volume','complete']
        df = pd.DataFrame(list(history))[order]
        df.time = pd.to_datetime(df.time)
        df.columns=['datetime','open','high','low','close','volume','complete']
        return df

    def process_tick(self,tick):
        #Add the tick to the corresponding candle
        candle = self.candles[tick.instrument].process_tick(tick)
        if candle is not None:
            #Check if it should be merged with last candle

            if self.get_latest_bar_value(candle['instrument'],'complete')== False:
                #Merge with last candle
                last_candle = self.data[candle['instrument']].tail(1).to_dict(orient='records')[0]
                merged_candle=[last_candle['datetime'],last_candle['open'], #open
                               max(last_candle['high'],candle['data']['high']), #high
                               min(last_candle['low'],candle['data']['low']), #low
                               candle['data']['close'], #close
                               last_candle['volume']+candle['data']['volume'], #volume
                               True] #complete

                self.data[candle['instrument']][-1:]=merged_candle
                print('%s: merged with last candle' %tick.instrument)

            else:
                # Add the candle to the dataframe
                cdl = {'datetime':datetime.utcfromtimestamp(candle['start']),
                       'open':round(candle['data']['open'],5),
                       'high':round(candle['data']['high'],5),
                       'low':round(candle['data']['low'],5),
                       'close':round(candle['data']['close'],5),
                       'volume':candle['data']['volume'],
                       'complete':True
                       }

                self.data[candle['instrument']]=self.data[candle['instrument']].append(cdl,ignore_index=True)

            #print(self.data[candle['instrument']].tail(1))
            self.events.put(MarketEvent())


    def get_latest_bar_value(self,symbol,val_type='close'):
        bars_list = self.data[symbol][val_type]
        return bars_list.values[-1]

    def get_latest_bar_datetime(self,symbol):
        return self.get_latest_bar_value(symbol,'datetime')

    def get_latest_bars_values(self,symbol,val_type='close',N=1):
        if N > len(self.data[symbol]):
            print('DATA HANDLER: Adding data due to insuffisant quantity, %i requested, %i available' %(N,len(self.data[symbol])))
            self.data[symbol]=self._get_oanda_history(symbol,self.granularity,count=(N+10))
        bars_list = self.data[symbol][val_type]
        return np.array(bars_list.values[-N:])

    def get_home_quote(self,currency):
        if currency[:3] == currency[-3:]:
            return 1
        else:
            quote = self.get_latest_bar_value(currency)
            return quote