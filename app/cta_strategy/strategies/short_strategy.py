"""
由两个信号触发操作
1.长周期信号判断大方向
2.短信号判断买卖
"""
from copy import copy

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
    """
    长周期的信号管理，就两个事情
    1.确认长周期均线多头排列
    2.KDJ超卖
    此时发出信号
    """

    def __init__(self, signal_pos_dict, period_hour: int = 2):
        """Constructor"""
        super().__init__()
        self.signal_pos_dict = signal_pos_dict
        self.bg = BarGenerator(self.on_bar, period_hour, self.on_long_period, Interval.HOUR)
        self.ma_state = 0
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
            return
        ma30 = self.am.sma(30, True)[:5]
        ma60 = self.am.sma(60, True)[:5]
        k, d, j = self.am.kdj()
        if ma30[-1] > ma30[-2] > ma60[-1] > ma60[-2]:
            if self.ma_state != 1:
                self.ma_state = 1
        elif ma30[-1] < ma30[-2] < ma60[-1] < ma60[-2]:
            if self.ma_state != -1:
                self.ma_state = -1
        else:
            self.ma_state = 0

        if j < 0 and self.ma_state == 1 and self.signal_pos_dict['long'] != 1:
            self.signal_pos_dict['long'] = 1
        if j > 100 and self.ma_state == -1 and self.signal_pos_dict['long'] != -1:
            self.signal_pos_dict['long'] = -1
        if 100 > j > 0:
            self.signal_pos_dict['long'] = 0


class MidSignal(CtaSignal):
    """
    短周期信号管理
    """
    j_low = 10
    j_high = 90

    def __init__(self, signal_pos_dict, period_minute: int = 15):
        """"""
        super().__init__()
        self.signal_pos_dict = signal_pos_dict
        self.bg = BarGenerator(self.on_bar, period_minute, self.on_short_period_bar, Interval.MINUTE)
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

    def on_short_period_bar(self, bar: BarData):
        """

        :param bar:
        :return:
        """
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)

        k, d, j = self.am.kdj()
        if self.signal_pos_dict['long'] == 1:
            if j < self.j_low and self.signal_pos_dict['mid'] != 1:
                self.signal_pos_dict['mid'] = 1

        elif self.signal_pos_dict['long'] == -1:
            if j > self.j_high and self.signal_pos_dict['mid'] != -1:
                self.signal_pos_dict['mid'] = -1

        if self.j_high > j and self.j_low:
            self.signal_pos_dict['mid'] = 0


class ShortSignal(CtaSignal):
    """
    短周期信号管理
    通过KD信号执行买卖
    """
    d_low = 10
    d_high = 90

    def __init__(self, signal_pos_dict):
        """"""
        super().__init__()
        self.signal_pos_dict = signal_pos_dict
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
            return
        # 开始计算各种东西
        k, d, j = self.am.kdj(only_close=True)
        # do sth
        if self.signal_pos_dict['mid'] == 1:
            if d < self.d_low:
                self.signal_pos_dict['short'] = 1
        elif self.signal_pos_dict['mid'] == -1:
            if d > self.d_high:
                self.signal_pos_dict['short'] = -1
        if self.d_high > d > self.d_low:
            self.signal_pos_dict['short'] = 0


class HxtStrategy(TargetPosTemplate):
    """"""

    author = "HXT"

    long_period = 2   # hour
    mid_period = 15   # minute

    signal_pos = {}
    long_state = 0
    mid_state = 0
    short_state = 0
    parameters = []
    variables = ['long_state', 'mid_state', 'short_state']

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.signal_pos = {
            "long": 0,
            "mid": 0,
            "short": 0
        }
        self.long_signal = LongSignal(self.signal_pos, self.long_period)
        self.mid_signal = MidSignal(self.signal_pos, self.mid_period)
        self.short_signal = ShortSignal(self.signal_pos)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(100)

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

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        super(HxtStrategy, self).on_bar(bar)
        old_one = copy(self.signal_pos)
        self.long_signal.on_bar(bar)
        self.mid_signal.on_bar(bar)
        self.short_signal.on_bar(bar)
        if self.signal_pos != old_one:
            self.long_state, self.mid_state, self.short_state = \
                self.signal_pos['long'], self.signal_pos['mid'], self.signal_pos['short']
            self.put_event()
            self.write_log(f'状态变化-{bar.datetime.strftime("%Y-%m-%d %H:%M:%S")-{self.signal_pos}')


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
