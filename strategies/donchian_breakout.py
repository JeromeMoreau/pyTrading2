from events import SignalEvent
import numpy as np
import pandas as pd
from talib import ATR,SMA

class DonchianBreakout(object):
    def __init__(self, prices,events, entry_lookback=50, exit_lookback=25, atr_stop=2.,TP_atr=None, name=None, symbols=None):
        self.bars = prices
        self.events = events
        self.symbol_list = self.bars.instruments_list if symbols is None else symbols
        
        self.entry_lookback = entry_lookback
        self.exit_lookback = exit_lookback
        self.ma_trend_filter = entry_lookback *2
        self.trailing_atr = atr_stop
        self.tp_atr = TP_atr
        
        self.identifier = 'DC_Breakout' if name is None else name
        self.invested, self.stop_loss = self._calculate_invested()
        self.min_bars = max(entry_lookback, exit_lookback,self.ma_trend_filter)+1

        print('Strategy %s, lookback: %sx%s, atr_stop %s' %(self.identifier, self.entry_lookback,self.exit_lookback, self.trailing_atr))

        
    def _calculate_invested(self):
        invested = {}
        stop_loss = {}
        for s in self.symbol_list:
            invested[s]= 'OUT'
            stop_loss[s]= None
        return invested, stop_loss
   
    def time_filter(self,bar_date):
        if pd.to_datetime(bar_date).hour >= 0 and pd.to_datetime(bar_date).hour <= 17:
            return True
        else:
            return True
    
    def calculate_signals(self,events):
        for symbol in self.symbol_list:
            bars_close = self.bars.get_latest_bars_values(symbol,'close',N=self.min_bars)

            if len(bars_close) < self.min_bars:
                #Exit if not enough data for indicator
                break

            bars_high = self.bars.get_latest_bars_values(symbol,'high',N=self.min_bars)
            bars_low = self.bars.get_latest_bars_values(symbol,'low',N=self.min_bars)
            atr = ATR(bars_high,bars_low,bars_close,timeperiod=20)
            atr = atr[~np.isnan(atr)]
            latest_close = bars_close[-1]
            
            if bars_close is not None:
                entry_long_trigger = np.max(bars_close[-self.entry_lookback:])
                exit_long_trigger = np.min(bars_close[-self.exit_lookback:])
                entry_short_trigger = np.min(bars_close[-self.entry_lookback:])
                exit_short_trigger = np.max(bars_close[-self.exit_lookback:])
                ma_filter = SMA(bars_close,timeperiod=self.ma_trend_filter)[-1]

                #EXITS
                if self.stop_loss[symbol] is not None:
                    if latest_close < self.stop_loss[symbol] and self.invested[symbol]=='LONG':
                            signal = SignalEvent(symbol,'market','exit',self.identifier)
                            self.events.put(signal)
                            self.invested[symbol]='OUT'
                    elif latest_close > self.stop_loss[symbol] and self.invested[symbol]=='SHORT':
                            signal = SignalEvent(symbol,'market','exit',self.identifier)
                            self.events.put(signal)
                            self.invested[symbol] = 'OUT'

                    if latest_close == exit_long_trigger  and self.invested[symbol]=='LONG':
                        signal = SignalEvent(symbol,'market','exit',self.identifier,self.stop_loss[symbol])
                        self.events.put(signal)
                        self.invested[symbol]='OUT'
                    elif latest_close == exit_short_trigger  and self.invested[symbol]=='SHORT' :
                        signal = SignalEvent(symbol,'market','exit',self.identifier,self.stop_loss[symbol])
                        self.events.put(signal)
                        self.invested[symbol] = 'OUT'

                #ENTRIES
                if latest_close == entry_long_trigger and latest_close >= ma_filter:
                    if self.invested[symbol]=='OUT' :
                        self.stop_loss[symbol] = latest_close - self.trailing_atr*atr[-1]
                        signal = SignalEvent(symbol,'market','buy',self.identifier,self.stop_loss[symbol])
                        self.events.put(signal)
                        self.invested[symbol] = 'LONG'
                            
                if latest_close == entry_short_trigger and latest_close <= ma_filter:
                    if self.invested[symbol]=='OUT':
                        self.stop_loss[symbol] = latest_close + self.trailing_atr*atr[-1]
                        signal = SignalEvent(symbol,'market','sell',self.identifier,self.stop_loss[symbol])
                        self.events.put(signal)
                        self.invested[symbol] = 'SHORT'


                #TRAILING STOP
                if self.invested[symbol]=='LONG':
                    stop_price = latest_close - self.trailing_atr*atr[-1]
                    if stop_price > self.stop_loss[symbol]:
                        #Move stop up
                        self.stop_loss[symbol] = stop_price
                elif self.invested[symbol]=='SHORT':
                    stop_price = latest_close + self.trailing_atr*atr[-1]
                    if stop_price < self.stop_loss[symbol]:
                        #Move stop down
                        self.stop_loss[symbol] = stop_price

                