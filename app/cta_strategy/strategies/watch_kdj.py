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
    author = "银枪小霸王"


    fixed_size = 1

    parameters = ['up_thresh', 'down_thresh']

    variables = ['over_sell', 'over_buy', 'over_sell_15', 'over_buy_15', 'k_1', 'j_15']

    up_thresh = 90
    down_thresh = 10

    over_sell = False
    over_buy = False
    over_sell_15 = False
    over_buy_15 = False
    k_1 = 0
    j_15 = 0

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

        self.bg_day = BarGenerator(self.on_bar, 1, self.on_day_bar, interval=Interval.DAILY)
        self.am_day = ArrayManager()

        self.bg15 = BarGenerator(self.on_bar, 15, self.on_15min_bar, interval=Interval.MINUTE)
        self.am15 = ArrayManager()

        self.file = open('kdj_value.txt', 'w+')

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

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
        # self.bg5.update_bar(bar)
        self.bg15.update_bar(bar)
        self.bg_day.update_bar(bar)
        self.am.update_bar(bar)
        if not self.am.inited:
            return
        self.k_1, d, j = self.am.kdj()
        if self.k_1 < self.down_thresh:
            self.over_sell = True
            if self.over_sell_15:
                self.write_log(f'k值超卖触发！-{self.vt_symbol}')
        elif self.k_1 > self.up_thresh:
            self.over_buy = True
            if self.over_buy_15:
                self.write_log(f'K值超买-{self.vt_symbol}')
        else:
            self.over_buy = False
            self.over_sell = False

        # self.file.write(f'{self.am.kdj(only_close=True)}, {bar.datetime}\n')

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
        k, d, self.j_15 = self.am15.kdj()
        if self.j_15 < self.down_thresh:
            self.over_sell_15 = True
        elif self.j_15 > self.up_thresh:
            self.over_buy_15 = True
        else:
            self.over_sell_15 = False
            self.over_buy_15 = False

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
