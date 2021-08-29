from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
from vnpy.trader.constant import Interval


class WatchKdjStrategy(CtaTemplate):
    """"""
    author = "用Python的交易员"


    fixed_size = 1

    parameters = []

    variables = ['']

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)


        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

        self.bg_day = BarGenerator(self.on_bar, 1, self.on_day_bar, interval=Interval.DAILY)
        self.am_day = ArrayManager()

        self.bg15 = BarGenerator(self.on_bar, 1, self.on_15min_bar, interval=Interval.HOUR)
        self.am15 = ArrayManager()

        self.file = open('kdj_value.txt', 'w+')

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(1)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")
        self.file.close()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg5.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        # self.bg5.update_bar(bar)
        # self.bg15.update_bar(bar)
        self.bg_day.update_bar(bar)
        self.am.update_bar(bar)
        if not self.am.inited:
            return
        # self.file.write(f'{self.am.kdj(only_close=True)}, {bar.datetime}\n')
        

    def on_5min_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        self.am5.update_bar(bar)
        if not self.am5.inited:
            return


        # if self.pos == 0:
        #     if self.ma_trend > 0 and self.rsi_value >= self.rsi_long:
        #         self.buy(bar.close_price + 5, self.fixed_size)
        #     elif self.ma_trend < 0 and self.rsi_value <= self.rsi_short:
        #         self.short(bar.close_price - 5, self.fixed_size)
        #
        # elif self.pos > 0:
        #     if self.ma_trend < 0 or self.rsi_value < 50:
        #         self.sell(bar.close_price - 5, abs(self.pos))
        #
        # elif self.pos < 0:
        #     if self.ma_trend > 0 or self.rsi_value > 50:
        #         self.cover(bar.close_price + 5, abs(self.pos))

        self.put_event()

    def on_15min_bar(self, bar: BarData):
        """"""
        self.file.write(f'{bar.datetime}@@\n')
        self.am15.update_bar(bar)
        if not self.am15.inited:
            return

    def on_day_bar(self, bar: BarData):
        """"""
        self.file.write(f'{bar.datetime}@@\n')
        self.am_day.update_bar(bar)
        if not self.am15.inited:
            return


    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
