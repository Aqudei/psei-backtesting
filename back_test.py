from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
from argparse import ArgumentParser

# Import the backtrader platform
import backtrader as bt
import backtrader.feeds as btfeeds

# Create a Stratey

# Create a subclass of Strategy to define the indicators and logic


class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=10,  # period for the fast moving average
        pslow=30   # period for the slow moving average
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):

        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f, PORT: %.2f' %
                 (trade.pnl, trade.pnlcomm, self.broker.getvalue()))

    def __init__(self):
        self.order = None
        self.buyprice = None
        self.buycomm = None

        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal
        self.atr = bt.ind.ATR()

    def next(self):
        if self.order:
            return

        if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                self.buy()  # enter long

        # in the market & cross to the downside
        elif self.crossover < 0 or (self.buyprice - 6 * self.atr[0]) > self.datas[0].close[0]:
            # import pdb; pdb.set_trace()
            # import pdb; pdb.set_trace()
            self.close()  # close long position


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('symbol')
    parser.add_argument('--pfast', type=int, default=20)
    parser.add_argument('--pslow', type=int, default=50)

    args = parser.parse_args()

    symbol = args.symbol

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(SmaCross, pfast=args.pfast, pslow=args.pslow)
    # cerebro.addstrategy(TestStrategy)

    data = btfeeds.GenericCSVData(
        dataname=f'./data/{symbol.upper()}.csv',

        fromdate=datetime.datetime(2018, 1, 1),
        todate=datetime.datetime.now().date(),

        nullvalue=0.0,

        dtformat=('%Y-%m-%d'),

        datetime=3,
        high=4,
        low=5,
        open=0,
        close=2,
        volume=1,
        openinterest=-1
    )

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.AllInSizer, percents=90)

    # Set the commission
    cerebro.broker.setcommission(commission=0.002)

    # Run over everything
    cerebro.run(maxcpus=1)

    print("Final Value:", cerebro.broker.getvalue())
    cerebro.plot()
