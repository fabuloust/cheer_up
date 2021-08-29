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


class MacdSuperStrategy(CtaTemplate):
    """"""
    author = "胡晓天"

    fixed_size = 1

    parameters = []

    variables = []

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(100)

        self.bg15 = BarGenerator(self.on_bar, 15, self.on_15min_bar)
        self.am15 = ArrayManager(100)

        self.bg_2h = BarGenerator(self.on_bar, 2, self.on_2h_bar, interval=Interval.HOUR)
        self.am_2h = ArrayManager(100)

        self.bg_day = BarGenerator(self.on_bar, 1, self.on_day_bar, interval=Interval.DAILY)
        self.am_day = ArrayManager(100)

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
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg15.update_bar(bar)
        self.bg_2h.update_bar(bar)
        self.bg_day.update_bar(bar)
        self.am.update_bar(bar)
        if not self.am.inited:
            return
        # self.file.write(f'{self.am.kdj(only_close=True)}, {bar.datetime}\n')

    def on_15min_bar(self, bar: BarData):
        """"""
        self.am15.update_bar(bar)
        if not self.am15.inited:
            return
        result = self.check_buy_status(self.am15)

        if result:
            self.file.write(f'十五分钟：{bar.datetime}\n')

    def on_2h_bar(self, bar: BarData):
        """"""
        self.am_2h.update_bar(bar)
        if not self.am_2h.inited:
            return
        result = self.check_buy_status(self.am_2h)
        if result:
            self.file.write(f'两小时：{bar.datetime}\n')

    def on_day_bar(self, bar: BarData):
        """"""
        self.am_day.update_bar(bar)
        if not self.am_day.inited:
            return
        result = self.check_buy_status(self.am_day)
        if result:
            self.file.write(f'日线：{bar.datetime}\n')

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

    def check_buy_status(self, am: ArrayManager):
        diff, dea, macd = am.macd(array=True)
        k, d, j = am.kdj()
        if macd[-1] > macd[-2] > 0 and diff[-1] > diff[-2] > diff[-3] and \
                dea[-3] < dea[-2] < dea[-1] < diff[-1] < macd[-1] and diff[-1] > 0 and macd[-1] > 3:
            self.file.write(f'{macd[-1]}-{diff[-1]}-{dea[-1]}\n')
            self.file.write(f'{am.close[-1]}-{am.close[-2]}')
            return True


