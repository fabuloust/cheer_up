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
from vnpy.app.cta_strategy.strategies.consts import MaState, KdjState
from vnpy.trader.constant import Interval


class LongSignal(CtaSignal):
    """"""

    def __init__(self, period_hour: int = 2):
        """Constructor"""
        super().__init__()
        self.ma_state = MaState.BLANK
        self.last_high = 0
        self.last_low = 0
        self.kdj_state = KdjState.BLANK
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

    def cal_ma_state(self, ma10, ma20, ma30, ma60):

        if self.ma_state == MaState.BLANK:
            # 从 震荡到多头趋势需要两个：
            # 1.均线多头排列
            # 2.价格创最近30个bar的新高
            if ma10[-1] > ma20[-1] > ma30[-1] > ma60[-1] and not (ma10[-2] > ma20[-2] > ma30[-2] > ma60[-2]) and \
                 self.am.close[-30:].max() == self.am.close[-1]:
                self.ma_state = MaState.LONG
                self.last_high = self.am.close[-30:-4].max
            elif ma10[-1] < ma20[-1] < ma30[-1] < ma60[-1] and not (ma10[-2] < ma20[-2] < ma30[-2] < ma60[-2]) and \
                self.am.close[-30:].min() == self.am.close[-1]:
                self.ma_state = MaState.LONG
                self.last_low = self.am.close[-30:-4].min
        elif self.ma_state == MaState.LONG:
            # 先想想吧
            pass
        elif self.ma_state == MaState.SHORT:
            pass

            

    def on_long_period(self, bar: BarData):
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)
            return
        # 通过均线来判断趋势，通过kdj来判断是否短期超买超卖
        ma10 = self.am.sma(10, True)[:5]
        ma20 = self.am.sma(20, True)[:5]
        ma30 = self.am.sma(30, True)[:5]
        ma60 = self.am.sma(60, True)[:5]
        old_state = self.ma_state
        self.cal_ma_state(ma10, ma20, ma30, ma60)
        if old_state == MaState.BLANK:
            if self.ma_state == MaState.LONG:
                # 进入建仓期
                self.set_signal_pos(1)
        k, d, j = self.am.kdj()
        diff, dea, macd = self.am.macd()


class MidSignal(CtaSignal):
    """
    短周期信号管理
    """

    def __init__(self, period_minute: int = 15):
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
        # 通过macd和kdj给出相关信号
        self


class ShortSignal(CtaSignal):
    """
    短周期信号管理
    通过KD信号执行买卖
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

        self.long_signal = LongSignal()
        self.mid_signal = MidSignal()
        self.short_signal = ShortSignal()

        self.signal_pos = {
            "long": 0,
            "mid": 0,
            "short": 0
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
        super(HxtStrategy, self).on_tick(tick)

        self.long_signal.on_tick(tick)
        self.mid_signal.on_tick(tick)
        self.short_signal.on_tick(tick)

        self.calculate_target_pos()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        super(HxtStrategy, self).on_bar(bar)

        self.long_signal.on_bar(bar)
        self.mid_signal.on_bar(bar)
        self.short_signal.on_bar(bar)

        self.calculate_target_pos()

    def calculate_target_pos(self):
        """"""
        self.signal_pos["rsi"] = self.long_signal.get_signal_pos()
        self.signal_pos["cci"] = self.mid_signal.get_signal_pos()
        self.signal_pos["ma"] = self.short_signal.get_signal_pos()

        target_pos = 0
        for v in self.signal_pos.values():
            target_pos += v

        self.set_target_pos(target_pos)

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        super(HxtStrategy, self).on_order(order)

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
