
class MaState:
    """
    b -> L -> B -> s
    """

    BLANK = 'BLANK'  # 震荡
    START_LONG = 'START_LONG'
    LONG = 'LONG'
    LONG_END = 'END_LONG'
    START_SHORT = 'START_SHORT'
    SHORT = 'SHORT'
    SHORT_END = 'SHORT_END'


class KdjThreshold:
    """
    kdj
    """
    KDJ_S_HIGH = 100
    KDJ_HIGH = 80
    KDJ_LOW = 20
    KDJ_SLOW = 0


class KdjState:
    """
    kdj状态
    """
    BLANK = 'BLANK'
    OVER_BUY = 'OVER_BUY'
    OVER_SELL = 'OVER_SEll'
    STRONG_BUY = 'STRONG_BUY'
    STRONG_SELL = 'STRONG_SELL'

