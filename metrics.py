import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


class Statistics(object):
    def __init__(self,portfolio):
        self.history, self.exposure = self._format_history(portfolio.history)
        self.trades = self._format_trades(portfolio.closed_trades)
        
        self.number_of_trades = len(self.trades)
        self.average_duration = np.mean(self.trades.duration)

        self.total_exposure = self.exposure.sum(axis=1)
        self.time_in_market = 1-((len(self.total_exposure[self.total_exposure == 0])/len(self.total_exposure)))

        self.win_rate = len(self.trades[self.trades.profit >0])/len(self.trades.profit)
        self.avg_win = np.mean(self.trades.profit_R[self.trades.profit_R >0])
        self.avg_loss = np.mean(self.trades.profit_R[self.trades.profit_R <0])
        self.trading_edge = (self.win_rate*self.avg_win) + (1-self.win_rate)*self.avg_loss
        self.cagr = create_cagr(self.history.open_equity)
        drawdown,self.max_dd,self.dd_duration = create_drawdowns(self.history.open_equity)
        self.history['drawdown'] = drawdown
        self.sharpe = create_sharpe_ratio(self.history.returns)
        self.r_squared = rsquared(np.arange(len(self.history.equity)),self.history.equity)
        
        
        
        
    def _format_history(self,history):
        history= pd.DataFrame(history,columns=('datetime','pnl','equity','exposure')).set_index('datetime')
        history['open_equity']=history.equity + history.pnl
        history['returns'] = history['open_equity'].pct_change()
        history['equity_curve'] = (1.0 + history['returns']).cumprod()
        exposure_df = pd.DataFrame.from_dict(data=history.exposure.to_dict(),orient='index')
        history = pd.concat([history,exposure_df],axis=1)
        history.index.name = 'datetime'
        return history,exposure_df
    
    
    def _format_trades(self,closed_trades):
        trades = pd.DataFrame(data= ([tr.ticket,tr.strategy,tr.open_date,tr.instrument,tr.side,tr.open_price,
                                                   tr.stop_loss,tr.units,tr.close_date,tr.close_price,tr.MAE,tr.MFE,
                                                   tr.pnl] for tr in closed_trades),
                                           columns=['ticket','strategy','open_date','symbol','direction',
                                                    'open_price','stop_loss','units','close_date',
                                                    'close_price','MAE','MFE','profit'])
        trades = trades.set_index('ticket').dropna()
        trades.open_date = pd.to_datetime(trades.open_date)
        trades.close_date = pd.to_datetime(trades.close_date)
        trades['duration']=trades.close_date - trades.open_date
        trades['direction'] = np.where(trades.direction=='buy',1,-1)
        trades['profit_R'] = (trades.open_price-trades.close_price)/(trades.stop_loss-trades.open_price)
        trades['MAE'] = (trades.open_price-trades.MAE)/(trades.open_price) * -trades.direction
        trades['MFE'] = (trades.open_price-trades.MFE)/(trades.open_price) * -trades.direction
        return trades

    def output_base_stats(self):
        stats = pd.DataFrame(data=[int(self.number_of_trades),(self.cagr*100),self.trading_edge,self.sharpe],
                             index=['#Trades','CAGR(%)','Avg trade(R)','Daily Sharpe'],
                             columns=['Base Stats'])
        return stats
    
    def output_full_stats(self):
        right_tail = np.percentile(self.trades.profit_R,95)
        left_tail = np.percentile(self.trades.profit_R,5)
        tail_ratio = abs(right_tail/left_tail)
        gain_pain_ratio = abs(sum(self.trades.profit_R[self.trades.profit_R >0])/sum(self.trades.profit_R[self.trades.profit_R<0]))
        common_sense_ratio = tail_ratio * gain_pain_ratio
        MFE_MAE = np.mean(self.trades.MFE) / -np.mean(self.trades.MAE)
        total_gain_R = self.trades.profit_R.sum()
    
        stats = pd.DataFrame(index=['#Trades','CAGR(%)','Avg trade(R)','Daily Sharpe','Max Drawdown(%)','Avg Duration','Exposure %','Win Rate %','Avg Win','Avg Loss','CSR','MFE/MAE','Total_gain(R)'],
                             columns=['All Trades','Long only','Short only'])
        stats['All Trades']=[self.number_of_trades,(self.cagr*100),self.trading_edge,self.sharpe,self.max_dd,self.average_duration,(self.time_in_market*100),(self.win_rate*100),self.avg_win,self.avg_loss,common_sense_ratio,MFE_MAE,total_gain_R]
        stats['Long only']=self.full_stats(self.trades[self.trades.direction == 1])
        stats['Short only']=self.full_stats(self.trades[self.trades.direction == -1])
        return stats


    def full_stats(self,pnl):
        
        win_rate = len(pnl.profit_R[pnl.profit_R > 0]) / len(pnl.profit_R)
        avg_win = np.mean(pnl.profit_R[pnl.profit_R > 0])
        avg_loss = np.mean(pnl.profit_R[pnl.profit_R < 0])
        avg_trade = (win_rate*avg_win) + (1-win_rate)*avg_loss
        avg_duration = np.mean(pnl.duration)
        if np.sum(pnl.direction)>1:
            exposure = (len(self.total_exposure[self.total_exposure > 0])/len(self.total_exposure))
        else:
            exposure = (len(self.total_exposure[self.total_exposure < 0])/len(self.total_exposure))
        
        right_tail = np.percentile(pnl.profit_R,95)
        left_tail = np.percentile(pnl.profit_R,5)
        tail_ratio = abs(right_tail/left_tail)
        gain_pain_ratio = abs(sum(pnl.profit_R[pnl.profit_R >0])/sum(pnl.profit_R[pnl.profit_R<0]))
        common_sense_ratio = tail_ratio * gain_pain_ratio
        MFE_MAE = np.mean(pnl.MFE) / -np.mean(pnl.MAE)
        total_gain_R = pnl.profit_R.sum()
        
        return [len(pnl),np.nan,avg_trade,np.nan,np.nan,avg_duration,(exposure*100),win_rate,avg_win,avg_loss,common_sense_ratio,MFE_MAE,total_gain_R]


    def plot_performance(self):
        # Plot four charts: Equity curve, period returns, drawdowns, exposure
    
        fig = plt.figure(figsize=(10,15))
        #Set the outer colour to white
        fig.patch.set_facecolor('white')
    
        # Plot eht equity curve
        ax1 = fig.add_subplot(411, ylabel='Portfolio value, %')
        self.history['equity_curve'].plot(ax=ax1, color="blue", lw=2.)
        #if benchmark is not None: benchmark.plot(ax=ax1, color='grey',lw=2.)
        plt.grid(True)
    
        # Plot the returns
        ax2 = fig.add_subplot(412, ylabel='Period returns, %')
        self.history['returns'].plot(ax=ax2, color="black", lw=2.)
        plt.grid(True)
    
        # Plot the drawdowns
        ax3 = fig.add_subplot(413, ylabel='Drawdowns, %')
        (self.history['drawdown']*100).plot(ax=ax3, color="red", lw=2.)
        plt.grid(True)
    
        ax4 = fig.add_subplot(414, ylabel='Exposure')
        exposure_df = pd.DataFrame.from_dict(data=self.history.exposure.to_dict(),orient='index')
        exposure_df.plot(kind='line',ax=ax4)
        plt.grid(True)
    
        # Plot the figure
        plt.show()

def create_drawdowns(equity):
    """
    Calculate the largest peak-to-trough drawdown of the PnL curve as well as the duration of the drawdown.
    Requires that the pnl_returns is a pandas Series.

    Parameters:
    pnl - A pandas Series representing period percentage returns

    Returns:
    drawdown(series), max_drawdown ,duration - Highest peak-to-trough drawdown and duration
    """

    #Calculate the cumulative returns curve and set up the High Water Mark (hwm)
    hwm = np.zeros(len(equity))

    #Create thet drawdown and duration series
    idx=equity.index
    drawdown = np.zeros(len(equity))
    duration = np.zeros(len(equity))

    #Loop over the index range
    for t in range (1, len(equity)):
        hwm[t] = max(hwm[t-1], equity[t])
        drawdown[t]= (hwm[t] - equity[t]) / hwm[t]
        duration[t]= (0 if drawdown[t] == 0 else duration[t-1]+1)

    drawdown = pd.Series(data=drawdown,index=idx)

    return drawdown, drawdown.max()*100, duration.max()

def create_cagr(equity):
    #print(equity)
    data = equity.reset_index()
    start_date = min(data.datetime)
    end_date = max(data.datetime)
    number_year = (end_date - start_date).days /364.25
    number_year = number_year if number_year > 0 else 1
    cagr = (equity[-1]/equity[0])**(1/(number_year)) -1
    #print(start_date, end_date, number_year, cagr)

    return cagr

def create_sharpe_ratio(returns, periods=252):

    """
    Cerate the Sharpe Ratio for the strategy, basedon a benchmark of zero(no risk-free rate information).

    Parameters:
    returns - A pandas Series representing period percentage returns.
    periods - Daily (252), Hourly (252*6.5), Minutely(252*6.5*60) etc.
    """
    return np.sqrt(periods)*(np.mean(returns)) / np.std(returns)

def rsquared(x, y):
    """ Return R^2 where x and y are array-like."""
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    return r_value**2