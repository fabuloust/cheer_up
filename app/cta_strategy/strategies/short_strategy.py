"""
由两个信号触发操作
1.长周期信号判断大方向
2.短信号判断买卖
"""

from vnpy.app.cta_strategy import (
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
    CtaSignal,
    TargetPosTemplate
)
from vnpy.trader.constant import Interval


class LongSignal(CtaSignal):
    """"""

    def __init__(self, period_hour: int):
        """Constructor"""
        super().__init__()

        self.bg = BarGenerator(self.on_bar, period_hour, self.on_long_period, Interval.HOUR)
        self.am = ArrayManager()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_long_period(self, bar: BarData):
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)
            return
        ma10 = self.am.sma(10, True)[:5]
        ma20 = self.am.sma(20, True)[:5]
        ma30 = self.am.sma(30, True)[:5]
        ma40 = self.am.sma(40, True)[:5]
        ma50 = self.am.sma(50, True)[:5]
        ma60 = self.am.sma(60, True)[:5]


class MidSignal(CtaSignal):
    """
    短周期信号管理
    """

    def __init__(self, period_minute: int):
        """"""
        super().__init__()

        self.bg = BarGenerator(self.on_bar, period_minute, self.on_short_period_bar, Interval.MINUTE)
        self.am = ArrayManager()
        self.kdj_signal = KdjSignal()
        self.macd_signal = MacdSignal()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_short_period_bar(self, bar: BarData):
        """

        :param bar:
        :return:
        """
        self.am.update_bar(bar)
        self.kdj_signal.on_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)
        # 开始计算各种东西
        self


class ShortSignal(CtaSignal):
    """
    短周期信号管理
    """

    def __init__(self):
        """"""
        super().__init__()

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)
            return
        # 开始计算各种东西
        k, d, j = self.am.kdj(only_close=True)
        # do sth



class MacdSignal(CtaSignal):
    """"""

    def __init__(self, fast_window: int, slow_window: int):
        """"""
        super().__init__()

        self.bg = BarGenerator(self.on_bar, 5, self.on_5min_bar)
        self.am = ArrayManager()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_5min_bar(self, bar: BarData):
        """"""
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)

        fast_ma = self.am.sma(self.fast_window)
        slow_ma = self.am.sma(self.slow_window)

        if fast_ma > slow_ma:
            self.set_signal_pos(1)
        elif fast_ma < slow_ma:
            self.set_signal_pos(-1)
        else:
            self.set_signal_pos(0)


class KdjSignal(CtaSignal):
    """"""

    def __init__(self, fast_window: int, slow_window: int):
        """"""
        super().__init__()

        self.fast_window = fast_window
        self.slow_window = slow_window

        self.bg = BarGenerator(self.on_bar, 5, self.on_5min_bar)
        self.am = ArrayManager()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_5min_bar(self, bar: BarData):
        """"""
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)

        fast_ma = self.am.sma(self.fast_window)
        slow_ma = self.am.sma(self.slow_window)

        if fast_ma > slow_ma:
            self.set_signal_pos(1)
        elif fast_ma < slow_ma:
            self.set_signal_pos(-1)
        else:
            self.set_signal_pos(0)


class HxtStrategy(TargetPosTemplate):
    """"""

    author = "HXT"

    long_period = 120
    mid_period = 15

    cci_level = 10
    fast_window = 5
    slow_window = 20

    signal_pos = {}

    parameters = ["rsi_window", "rsi_level", "cci_window",
                  "cci_level", "fast_window", "slow_window"]
    variables = ["signal_pos", "target_pos"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.l

        self.long_signal = LongSignal(self.rsi_window, self.rsi_level)
        self.mid_signal = MidSignal(self.cci_window, self.cci_level)
        self.short_signal = ShortSignal(self.fast_window, self.slow_window)

        self.signal_pos = {
            "rsi": 0,
            "cci": 0,
            "ma": 0
        }

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

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        super(MultiSignalStrategy, self).on_tick(tick)

        self.rsi_signal.on_tick(tick)
        self.cci_signal.on_tick(tick)
        self.ma_signal.on_tick(tick)

        self.calculate_target_pos()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        super(MultiSignalStrategy, self).on_bar(bar)

        self.rsi_signal.on_bar(bar)
        self.cci_signal.on_bar(bar)
        self.ma_signal.on_bar(bar)

        self.calculate_target_pos()

    def calculate_target_pos(self):
        """"""
        self.signal_pos["rsi"] = self.rsi_signal.get_signal_pos()
        self.signal_pos["cci"] = self.cci_signal.get_signal_pos()
        self.signal_pos["ma"] = self.ma_signal.get_signal_pos()

        target_pos = 0
        for v in self.signal_pos.values():
            target_pos += v

        self.set_target_pos(target_pos)

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        super(MultiSignalStrategy, self).on_order(order)

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
