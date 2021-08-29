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
from vnpy.app.cta_strategy.strategies.consts import MaState, KdjState, KdjThreshold
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
                self.ma_state = MaState.START_LONG
                self.last_high = self.am.close[-30:-4].max()
            elif ma10[-1] < ma20[-1] < ma30[-1] < ma60[-1] and not (ma10[-2] < ma20[-2] < ma30[-2] < ma60[-2]) and \
                self.am.close[-30:].min() == self.am.close[-1]:
                self.ma_state = MaState.START_SHORT
                self.last_low = self.am.close[-30:-4].min()
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
        k, d, j = self.am.kdj()
        diff, dea, macd = self.am.macd()
        if old_state == MaState.BLANK:
            if self.ma_state == MaState.START_LONG:
                # 进入建仓期
                if j < KdjThreshold.KDJ_HIGH:
                    self.set_signal_pos(1)
            elif self.ma_state == MaState.START_SHORT:
                # 进入建仓期
                if j < KdjThreshold.KDJ_LOW:
                    self.set_signal_pos(-1)



class MidSignal(CtaSignal):
    """
    短周期信号管理
    """

    def __init__(self, period_minute: int = 15):
        """"""
        super().__init__()

        self.bg = BarGenerator(self.on_bar, period_minute, self.on_short_period_bar, Interval.MINUTE)
        self.am = ArrayManager()
        self.kdj_signal = KdjSignal_1()
        self.macd_signal = MacdSignal()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)
        self.kdj_signal.on_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)
        self.kdj_signal.on_bar(bar)
        self.macd_signal.on_bar(bar)

    def on_short_period_bar(self, bar: BarData):
        """

        :param bar:
        :return:
        """
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)
        # 通过macd和kdj给出相关信号
        if self.kdj_signal.get_signal_pos() == 1 and self.macd_signal.get_signal_pos() == 1:
            self.set_signal_pos(1)
        elif self.kdj_signal.get_signal_pos() == -1 and self.macd_signal.get_signal_pos() == -1:
            self.set_signal_pos(-1)


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
        self.kdj_signal = KdjSignal()

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


class KdjState:

    def __init__(self, state, k=0.0, d=0.0, j=0.0, high=0.0, low=0.0):
        self.state = state
        self.k = k
        self.d = d
        self.j = j
        self.high = high
        self.low = low

    def update(self, k=None, d=None, j=None, high=None, low=None):
        if self.state == 0:
            for key, value in zip(('k', 'd', 'j', 'high', 'low'), (k, d, j, high, low)):
                if value is not None:
                    self.__setattr__(key, min(value,self.__getattribute__(key)))
        else:
            for key, value in zip(('k', 'd', 'j', 'high', 'low'), (k, d, j, high, low)):
                if value is not None:
                    self.__setattr__(key, max(value,self.__getattribute__(key)))


class KdjSignal_1(CtaSignal):
    """"""

    def __init__(self, only_close=False):
        """"""
        super().__init__()

        self.last_over_buy_value = 0
        self.last_over_sell_value = 0
        self.last_state = KdjState.BLANK
        self.state = KdjState.BLANK
        self.bg = BarGenerator(self.on_bar, 15, self.on_15min_bar)
        self.am = ArrayManager()
        self.only_close = only_close

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

    def on_15min_bar(self, bar: BarData):
        """"""
        self.am.update_bar(bar)
        if not self.am.inited:
            self.set_signal_pos(0)

        _, _, j = self.am.kdj()
        if j > KdjThreshold.KDJ_HIGH:
            if self.state == KdjState.BLANK:
                pass
            elif self.state == KdjState.OVER_BUY:
                pass
            else:
                pass


class KdjSignal_2(CtaSignal):
    """
    分时的kdj
    """

    def __init__(self, only_close=True):
        """"""
        super().__init__()

        self.last_over_buy_state = None
        self.last_over_sell_state = None
        self.last_state = None
        self.cur_state = None
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
        self.only_close = only_close

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

        k, _, _ = self.am.kdj(self.only_close)
        if self.cur_state:
            if self.cur_state.state == 1:
                if k < self.cur_state.k:
                    self.set_signal_pos(-1)
            elif self.cur_state.state == 0:
                if k > self.cur_state.k:
                    self.set_signal_pos(1)

        if k >= KdjThreshold.KDJ_HIGH:
            if not self.cur_state:
                self.cur_state = KdjState(state=1, k=k, high=bar.close_price)
            else:
                self.cur_state.update(k=k, high=bar.close_price)
        elif k <= KdjThreshold.KDJ_LOW:
            if not self.cur_state:
                self.cur_state = KdjState(state=1, k=k, low=bar.close_price)
            else:
                self.cur_state.update(k=k, low=bar.close_price)
        else:
            if not self.last_state and self.cur_state:
                self.last_state = self.cur_state
            if self.last_state.state == 0:
                self.last_over_sell_state = self.last_state
            else:
                self.last_over_buy_state = self.last_state
            self.cur_state = None


class HxtStrategy(TargetPosTemplate):
    """"""

    author = "HXT"

    long_period = 2   # hour
    mid_period = 15   # minute

    signal_pos = {}

    parameters = []
    variables = []

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

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        super(HxtStrategy, self).on_bar(bar)

        self.long_signal.on_bar(bar)
        self.mid_signal.on_bar(bar)
        self.short_signal.on_bar(bar)

        if self.long_signal.get_signal_pos() == 1 and self.mid_signal.get_signal_pos() == 1 and \
                self.short_signal.get_signal_pos() == 1:
            if self.pos == 0:
                self.buy(bar.close_price, 1)
        if self.long_signal.get_signal_pos() == -1 and self.mid_signal.get_signal_pos() == -1 and \
                self.short_signal.get_signal_pos() == -1:
            if self.pos == 0:
                self.short(bar.close_price, 1)

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
