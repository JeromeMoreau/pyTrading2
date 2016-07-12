import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def backtest_performance(portfolio):
    trades = portfolio.trades_history.dropna()

    number_of_trades = len(trades)
    avg_duration = np.mean(trades.duration)
    #backtest_duration = self.data_handler.end_date - self.data_handler.start_date
    total_exposure = portfolio.exposure_df.sum(axis=1)
    time_in_market = 1-((len(total_exposure[total_exposure == 0])/len(total_exposure)))
    win_rate = len(trades[trades.profit >0])/len(trades.profit)
    avg_win = np.mean(trades.profit_R[trades.profit_R >0])
    avg_loss = np.mean(trades.profit_R[trades.profit_R <0])
    trading_edge = (win_rate*avg_win) + (1-win_rate)*avg_loss
    right_tail = np.percentile(trades.profit_R,95)
    left_tail = np.percentile(trades.profit_R,5)
    tail_ratio = abs(right_tail/left_tail)
    gain_pain_ratio = abs(sum(trades.profit_R[trades.profit_R >0])/sum(trades.profit_R[trades.profit_R<0]))
    common_sense_ratio = tail_ratio * gain_pain_ratio
    MFE_MAE = np.mean(trades.MFE) / -np.mean(trades.MAE)
    total_gain_R = trades.profit_R.sum()

    stats = pd.DataFrame(data=[number_of_trades,avg_duration,(time_in_market*100),(win_rate*100),avg_win,avg_loss,trading_edge,common_sense_ratio,MFE_MAE,total_gain_R],
                         index=['# of trades','Avg Duration','Exposure %','Win Rate %','Avg Win','Avg Loss','Edge','CSR','e-ratio','Total_gain(R)'],
                         columns=['Statistics'])
    return stats


def plot_performance(portfolio):
    # Plot four charts: Equity curve, period returns, drawdowns, exposure

    fig = plt.figure(figsize=(10,15))
    #Set the outer colour to white
    fig.patch.set_facecolor('white')

    # Plot eht equity curve
    ax1 = fig.add_subplot(411, ylabel='Portfolio value, %')
    portfolio.history['equity_curve'].plot(ax=ax1, color="blue", lw=2.)
    #if benchmark is not None: benchmark.plot(ax=ax1, color='grey',lw=2.)
    plt.grid(True)

    # Plot the returns
    ax2 = fig.add_subplot(412, ylabel='Period returns, %')
    portfolio.history['returns'].plot(ax=ax2, color="black", lw=2.)
    plt.grid(True)

    # Plot the drawdowns
    ax3 = fig.add_subplot(413, ylabel='Drawdowns, %')
    (portfolio.history['drawdown']*100).plot(ax=ax3, color="red", lw=2.)
    plt.grid(True)

    ax4 = fig.add_subplot(414, ylabel='Exposure')
    exposure_df = pd.DataFrame.from_dict(data=portfolio.history.exposure.to_dict(),orient='index')
    exposure_df.plot(kind='line',ax=ax4)
    plt.grid(True)

    # Plot the figure
    plt.show()