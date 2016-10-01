import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats




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

def aggregate_returns(returns,convert_to):
    """

    :param returns:
    :param convert_to:
    :return:
    """
    def cumulate_returns(x):
        return np.exp(np.log(1 + x).cumsum())[-1] - 1

    if convert_to == 'weekly':
        return returns.groupby(
            [lambda x: x.year,
             lambda x: x.month,
             lambda x: x.isocalendar()[1]]).apply(cumulate_returns)
    elif convert_to == 'monthly':
        return returns.groupby(
            [lambda x: x.year, lambda x: x.month]).apply(cumulate_returns)
    elif convert_to == 'yearly':
        return returns.groupby(
            [lambda x: x.year]).apply(cumulate_returns)
    else:
        ValueError('convert_to must be weekly, monthly or yearly')