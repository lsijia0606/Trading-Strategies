import numpy as np
from py_security.security import Security
from py_simulator.day.day_context import DayContext
from py_simulator.min.min_context import MinContext
from py_simulator.util import context_helper
from py_helper.py_table import PYTable
from PyQt5.QtWidgets import *
import sys
from scipy import stats
import copy
import statsmodels.api as sm
import seaborn as sns
import pandas as pd

"""
 * This Strategy class is where the strategy logic is implemented. The user
 * should only modify the initialize(...) and runStratety(...) function in 
 * this class. User defined supporting functions and classes can be defined 
 * at will. The entry point of the compiled binary is in BackTester class which
 * is intentionally hidden from the user.
"""


def main():
    security = Security(user='readonly', password='123456', country=0)
    strategy = SampleStrategy(security)
    o = strategy.get_output()
    b = context_helper.get_bench_output(security, bench=strategy.benchTicker, start=strategy.startDate, end=strategy.endDate)

    # get results as pandas df
    summary = context_helper.get_summary(o, b)
    portf_value = context_helper.get_portf_value(o)
    month_value = context_helper.get_monthly_portf_value(o)

    # show table view
    app = QApplication(sys.argv)
    summary = PYTable(summary, title='Performance Summary')
    portf_value = PYTable(portf_value, title='Porffolio Value')
    month = PYTable(month_value, title='Porffolio Monthly Value')
    sys.exit(app.exec_())


class SampleStrategy(DayContext):

    def initialize(self):
        # This function is called before the framework calling runStrategy
        # define stocks universe and other stuff here.
        self.initCashPosition = 1000000.0
        self.tickers.append("JPM")
        self.tickers.append("GS")
        self.tickers.append("V")
        self.tickers.append("BAC")
        self.tickers.append("MA")
        self.tickers.append("TD")
        self.tickers.append("PYPL")
        self.tickers.append("GS")
        self.tickers.append("RY")
        self.tickers.append("CM")

        self.startDate = "2007-06-04 00:00:00"
        self.endDate = "2010-06-04 16:00:00"  # you must change this
        self.benchTicker = "SPY"
        self.annualRiskFreeInterestRate = 0.00375

    def run_strategy(self, executor):

        t_day = 120

        for dtIdx in np.arange(0, self.numBarsWithData):  # for each day

            # p values
            pairs = []

            for symbIdx in np.arange(0, self.numOfSymbols):  # for each stock

                for symbIdx2 in np.arrange(symbIdx + 1, self.numOfSymbols ):

                    prices1 = self.closePx[symbIdx][dtIdx]
                    prices2 = self.closePx[symbIdx2][dtIdx]
                    result = sm.tsa.stattools.coint(prices1,prices2)
                    pvalue = result[1]
                    if pvalue < 0.05:
                        pairs.append({'stock': (symbIdx,symbIdx2),'pvalue': pvalue})
            min_value_item = min(pairs,key = lambda x: x['pvalue'])
            stock1 = min_value_item['stock'][0] #first stock
            stock2 = min_value_item['stock'][1] #second stock

            #OLS
            priceOfStock1 = Series()
            priceOfStock2 = Series()
            for i in range(dtIdx - t_day + 1, dtIdx + 1):
                priceOfStock1.append(self.closePx[stock1][i])
                priceOfStock2.append(self.closePx[stock2][i])
            X = sm.add_constant(priceOfStock1)
            result2 = (sm.OLS(priceOfStock2, X)).fit()
            cor = result2.params[1]
            z_score = zscorecalcu(priceOfStock2 - cor*priceOfStock1)

            # Default position
            price1 = self.closePx[stock1][0]
            price2 = self.closePx[stock2][0]
            size = {'stock1': (self.initCashPosition * 0.5) / price1, 'stock2': (self.initCashPosition * 0.5) / price2}

            # start to trade
            if dtIdx == 0:
                    # define your first day trading logic
                executor.tradeAtClose(dtIdx,stock1,size['stock1'])
                executor.tradeAtClose(dtIdx,stock2,size['stock2'])

            elif dtIdx > 0:
                price_stock1 = self.closePx[stock1][dtIdx]
                price_stock2 = self.closePx[stock2][dtIdx]
                if z_score > 1:
                    amount_stock2 = price_stock2 * size['stock2']
                    sizeTobuy2 = size['stock2'] * (-1)
                    sizeTobuy1 = amount_stock2 /price_stock1
                    executor.tradeAtClose(dtIdx,stock2, sizeTobuy2) #卖出stock2
                    executor.tradeAtClose(dtIdx,stock1, sizeTobuy1) #买入stock1
                    size['stock1'] = size['stock1'] + sizeTobuy1
                    size['stock2'] = size['stock2'] + sizeTobuy2

                elif z_score < -1:
                    amount_stock1 = price_stock1 * size['stock1']
                    sizeTobuy1_2 = size['stock1'] * (-1)
                    sizeTobuy2_2 = amount_stock1 / price_stock2
                    executor.tradeAtClose(dtIdx, stock1, sizeTobuy1_2)  # 卖出stock1
                    executor.tradeAtClose(dtIdx, stock2, sizeTobuy2_2)  # 买入stock2
                    size['stock1'] = size['stock1'] + sizeTobuy1_2
                    size['stock2'] = size['stock2'] + sizeTobuy2_2

                elif -1 <= z_score <= 1:
                    if -0.1 <= z_score <= 0.1 and size['stock1'] == 0 or size['stock2'] == 0:
                        #zscore = 0 and all position in one stock
                        if size['stock1'] == 0:  # all position in stock2
                            amountOfstock2 = size['stock2'] * price_stock2
                            sizeTobuy1_3 = amountOfstock2 * 0.5/price_stock1
                            sizeTobuy2_3 = amountOfstock2 * 0.5/price_stock2*(-1)
                            executor.tradeAtClose(dtIdx, stock1, sizeTobuy1_3)  # 买入stock1
                            executor.tradeAtClose(dtIdx, stock2, sizeTobuy2_3)  # 卖出stock2
                        elif size['stock2'] == 0:  # all position in stock1
                            amountOfstock1 = size['stock1'] * price_stock1
                            sizeTobuy1_4 = amountOfstock1 * 0.5 / price_stock1 *(-1)
                            sizeTobuy2_4 = amountOfstock1 * 0.5 / price_stock2
                            executor.tradeAtClose(dtIdx, stock1, sizeTobuy1_4)  # 卖出stock1
                            executor.tradeAtClose(dtIdx, stock2, sizeTobuy2_4)  # 买入stock2

                executor.nextTradingDay(dtIdx)  # some house keeping when the clock turns to next trading day

            pass

    def zscorecalcu(series):
        return (series[len(series)-1] - series.mean()) / np.std(series)


if __name__ == '__main__':
    main()
    print("All Done!")
