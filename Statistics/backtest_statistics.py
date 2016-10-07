from Statistics.metrics import *
from Statistics.abstract_statistics import AbstractStatistics
import seaborn as sns
from matplotlib import cm
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as mdates


class Statistics(AbstractStatistics):
    def __init__(self,portfolio):
        self.history, self.exposure = self._format_history(portfolio.history)
        self.trades = self._format_trades(portfolio.closed_trades)

        self.number_of_trades = len(self.trades)
        self.average_duration = np.mean(self.trades.duration)

        self.total_exposure = self.exposure.sum(axis=1)
        self.time_in_market = 1-((len(self.total_exposure[self.total_exposure == 0])/len(self.total_exposure)))

        self.win_rate = len(self.trades[self.trades.profit >0])/len(self.trades.profit)
        self.avg_win = np.mean(self.trades.profit_R[self.trades.profit_R > 0])
        self.avg_loss = np.mean(self.trades.profit_R[self.trades.profit_R < 0])
        self.trading_edge = (self.win_rate*self.avg_win) + (1-self.win_rate)*self.avg_loss
        self.cagr = create_cagr(self.history.open_equity)
        self.history['drawdown'],self.max_dd,self.dd_duration = create_drawdowns(self.history.open_equity)

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
        trades = pd.DataFrame(data= ((tr.ticket, tr.strategy, tr.open_date, tr.instrument, tr.side, tr.open_price,
                                      tr.stop_loss, tr.units, tr.close_date, tr.close_price, tr.MAE, tr.MFE,
                                      tr.pnl) for tr in closed_trades),
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

    def get_results(self):
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
        stats['Long only']=self._full_stats(self.trades[self.trades.direction == 1])
        stats['Short only']=self._full_stats(self.trades[self.trades.direction == -1])
        return stats


    def _full_stats(self,pnl):

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


    def plot_results(self):
        # Plot four charts: Equity curve, drawdowns, monthly returns, yearly returns
        rc = {
            'lines.linewidth': 1.0,
            'axes.facecolor': '0.995',
            'figure.facecolor': '0.97',
            'font.family': 'serif',
            'font.serif': 'Ubuntu',
            'font.monospace': 'Ubuntu Mono',
            'font.size': 10,
            'axes.labelsize': 10,
            'axes.labelweight': 'bold',
            'axes.titlesize': 10,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
            'legend.fontsize': 10,
            'figure.titlesize': 12
        }
        sns.set_context(rc)

        sns.set_style("whitegrid")
        sns.set_palette("deep",desat=.6)

        vertival_sections = 5
        fig = plt.figure(figsize=(10, vertival_sections*3))
        gs = GridSpec(vertival_sections,3,wspace=0.1,hspace=0.05)

        ax_equity = plt.subplot(gs[:2, :])
        ax_drawdown = plt.subplot(gs[2, :], sharex=ax_equity)
        ax_monthly_returns = plt.subplot(gs[3, :2])
        ax_yearly_returns = plt.subplot(gs[3, 2])

        self._plot_equity(ax_equity)
        self._plot_drawdown(ax_drawdown)
        self._plot_monthly_returns(ax_monthly_returns)
        self._plot_yearly_returns(ax_yearly_returns)

        plt.show()



    """------------------------------------------
    --------------INDIVIDUAL CHARTS PLOTS--------------
    """#------------------------------------------

    def _plot_monthly_returns(self,ax=None):
        if ax is None: ax = plt.gca()
        monthly_ret = aggregate_returns(self.history['returns'],'monthly')
        monthly_ret = monthly_ret.unstack()
        monthly_ret = np.round(monthly_ret,3)
        monthly_ret.rename(
            columns={1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
                     5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
                     9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'},
            inplace=True)

        sns.heatmap(monthly_ret.fillna(0) *100.,
                    annot=True,
                    fmt='0.1f',
                    center=0.0,
                    cbar=False,
                    cmap=cm.RdYlGn,
                    ax=ax)
        ax.set_title('Monthly Returns (%)', fontweight='bold')
        ax.set_ylabel('')
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        ax.set_xlabel('')

        return ax


    def _plot_yearly_returns(self,ax=None):
        if ax is None: ax = plt.gca()

        def format_perc(x, pos):
            return '%.0f%%' % x

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

        yearly_ret = aggregate_returns(self.history['returns'],'yearly')*100.
        yearly_ret.plot(kind="bar",ax=ax)
        ax.set_title('Yearly Returns (%)', fontweight='bold')
        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

        return ax



    def _plot_equity(self,ax=None):
        # Plots the equity curve
        if ax is None: ax = plt.gca()

        def format_two_dec(x, pos):
            return '%.2f' % x

        y_axis_formatter = FuncFormatter(format_two_dec)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
        ax.xaxis.set_tick_params(reset=True)
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        self.history['equity_curve'].plot(ax=ax, color="blue", lw=2.,label="Backtest")
        ax.set_ylabel('Cumulative returns')
        ax.axhline(1.0, linestyle='--', color='black', lw=1)

        return ax

    def _plot_drawdown(self,ax=None):
        # Plot the drawdowns (underwater equity)
        if ax is None: ax = plt.gca()

        def format_perc(x, pos):
            return '%.0f%%' % x

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))


        (self.history['drawdown'] * -100).plot(ax=ax,kind="area",alpha=0.3, color="red", lw=2.)

        ax.set_title('Drawdown (%)', fontweight='bold')
        return ax

    def _plot_exposure(self,ax=None):
        if ax is None: ax = plt.gca()

        exposure_df = pd.DataFrame.from_dict(data=self.history.exposure.to_dict(),orient='index')
        exposure_df.plot(kind='line',ax=ax)

        ax.set_title('Raw Exposure', fontweight='bold')
        return ax
