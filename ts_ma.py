import numpy as np

import operator
from py_security.security import Security
from py_simulator.day.day_context import DayContext
from py_simulator.min.min_context import MinContext
from py_simulator.util import context_helper
from py_helper.py_table import PYTable
from PyQt5.QtWidgets import *
import sys

"""
 * This Strategy class is where the strategy logic is implemented. The user
 * should only modify the initialize(...) and runStratety(...) function in 
 * this class. User defined supporting functions and classes can be defined 
 * at will. The entry point of the compiled binary is in BackTester class which
 * is intentionally hidden from the user.
"""


def main():
    security = Security(user='readonly', password='123456')
    strategy = SampleStrategy(security)
    o = strategy.get_output()
    b = context_helper.get_bench_output(security=security, bench=strategy.benchTicker, start=strategy.startDate,
                                        end=strategy.endDate)

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

        self.tickers = ['AAPL']
        self.tickers.append("GOOGL")
        self.tickers.append("AMZN")
        self.tickers.append("JPM")
        self.tickers.append("BAC")
        self.tickers.append("NFLX")
        self.tickers.append("CMCSA")
        self.tickers.append("MCD")
        self.tickers.append("XOM")
        self.tickers.append("RIO")
        self.tickers.append("JNJ")
        self.tickers.append("MRK")
        self.tickers.append("NVO")

        self.startDate = "2012-06-24 00:00:00"
        self.endDate = "2013-5-30 16:00:00"  # you must change this
        self.benchTicker = "SPY.US"
        self.annualRiskFreeInterestRate = 0.00375
        self.numTradingDaysAYear = 252
        self.numTradingMinsADay  = 6*60+30
        self.datetimeAlignTicker = 'SPY.US'


    def run_strategy(self, executor):

        ma_dev_ticker = list()
        ma_dev_total = list()
        t_day = 30

        for dtIdx in np.arange(0, self.numBarsWithData):  # for each day

            if dtIdx % t_day == 0 and dtIdx != 0:

                for symbIdx in np.arange(0, self.numOfSymbols):  # for each stock
                    # start to trade
                    ma_sum = 0
                    for i in range(dtIdx-29, dtIdx+1):
                        ma_sum += self.closePx[symbIdx][i]
                    ma_arg = ma_sum/t_day
                    ma_dev = (ma_arg - self.closePx[symbIdx][dtIdx])/ma_arg #deviation
                    ma_dev_ticker.append(symbIdx)
                    ma_dev_total.append(ma_dev)

                ma_dev_dict = dict(zip(ma_dev_ticker,ma_dev_total))
                ma_dev_sort = sorted(ma_dev_dict.items(),key = operator.itemgetter(1),reverse = True)#a sequence of deviation
                for j in range(10):
                    price = self.closePx[ma_dev_sort[j][0]][dtIdx]
                    weight = 1.0 / 10
                    sizeToBuy = self.initCashPosition * weight / price
                    executor.tradeAtClose(dtIdx,ma_dev_sort[j][0], sizeToBuy)
            else:
                pass
            executor.nextTradingDay(dtIdx)  # some house keeping when the clock turns to next trading day
        pass # used as debug break point


if __name__ == '__main__':
    main()
    print("All Done!")
