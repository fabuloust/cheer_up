from datetime import timedelta
from typing import List, Optional
from pytz import timezone

from numpy import ndarray
from rqdatac import init as rqdata_init
from rqdatac.services.basic import all_instruments as rqdata_all_instruments
from rqdatac.services.get_price import get_price as rqdata_get_price
from rqdatac.share.errors import AuthenticationFailed

from .setting import SETTINGS
from .constant import Exchange, Interval
from .object import BarData, TickData, HistoryRequest
from .utility import round_to


INTERVAL_VT2RQ = {
    Interval.MINUTE: "1m",
    Interval.HOUR: "60m",
    Interval.DAILY: "1d",
}

INTERVAL_ADJUSTMENT_MAP = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.HOUR: timedelta(hours=1),
    Interval.DAILY: timedelta()         # no need to adjust for daily bar
}

CHINA_TZ = timezone("Asia/Shanghai")


class WindClient:
    """
    Client for querying history data from RQData.
    """

    def __init__(self):
        """"""
        self.inited: bool = False
        from WindPy import w
        self.w = w
        self.w.start()

    def init(self) -> bool:
        """"""

        if self.inited:
            return True

        if self.w.isconnected():
            self.inited = True
            return True
        else:
            return False

    def to_wind_symbol(self, symbol: str, exchange: Exchange) -> str:
        """
        CZCE product of RQData has symbol like "TA1905" while
        vt symbol is "TA905.CZCE" so need to add "1" in symbol.
        """
        # Equity
        if exchange in [Exchange.SSE, Exchange.SZSE]:
            if exchange == Exchange.SSE:
                wind_symbol = f"{symbol}.SH"
            else:
                wind_symbol = f"{symbol}.SZ"
        # Spot
        elif exchange in [Exchange.SGE]:
            for char in ["(", ")", "+"]:
                symbol = symbol.replace(char, "")
            symbol = symbol.upper()
            wind_symbol = f"{symbol}.SGEX"
        # Futures and Options
        elif exchange in [Exchange.SHFE, Exchange.CFFEX, Exchange.DCE, Exchange.CZCE, Exchange.INE]:
            for count, word in enumerate(symbol):
                if word.isdigit():
                    break

            product = symbol[:count]
            time_str = symbol[count:]

            # Futures
            if time_str.isdigit():
                # 万德的前面不变，exchange取前三位
                return f'{symbol.upper()}.{exchange.value[:3]}'

            # Options
            else:
                if exchange in [Exchange.CFFEX, Exchange.DCE, Exchange.SHFE]:
                    wind_symbol = symbol.replace("-", "").upper()
                elif exchange == Exchange.CZCE:
                    year = symbol[count]
                    suffix = symbol[count + 1:]

                    if year == "9":
                        year = "1" + year
                    else:
                        year = "2" + year

                    wind_symbol = f"{product}{year}{suffix}".upper()
        else:
            wind_symbol = f"{symbol}.{exchange.value}"

        return wind_symbol

    def query_history(self, req: HistoryRequest) -> Optional[List[BarData]]:
        """
        Query history bar data from RQData.
        """
        # if self.symbols is None:
        #     return None

        symbol = req.symbol
        exchange = req.exchange
        interval = req.interval
        start = req.start
        end = req.end

        # For adjust timestamp from bar close point (RQData) to open point (VN Trader)
        adjustment = INTERVAL_ADJUSTMENT_MAP[interval]

        # For querying night trading period data
        end += timedelta(1)

        # Only query open interest for futures contract
        fields = ["open", "high", "low", "close", "volume"]
        if not symbol.isdigit():
            fields.append("oi")

        result = self.w.wsi('{}.{}'.format(symbol, exchange.value[:3]), 'open,close,high,low,volume,oi',
                            start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"), 'BarSize=1')

        open_, close, high, low, volume, oi = result.Data
        time_list = result.Times
        total_num = len(open_)
        data: List[BarData] = []
        for i in range(total_num):
            data.append(
                BarData(
                    symbol=symbol,
                    exchange=exchange.value,
                    interval=Interval.MINUTE,
                    datetime=time_list[i],
                    open_price=open_[i],
                    close_price=close[i],
                    high_price=high[i],
                    low_price=low[i],
                    volume=volume[i],
                    open_interest=oi[i],
                    gateway_name='WIND'
                )
            )
        return data

    def query_tick_history(self, req: HistoryRequest) -> Optional[List[TickData]]:
        """
        Query history bar data from RQData.
        """
        # if self.symbols is None:
        #     return None

        symbol = req.symbol
        exchange = req.exchange
        start = req.start
        end = req.end

        wind_symbol = self.to_wind_symbol(symbol, exchange)
        # if wind_symbol not in self.symbols:
        #     return None

        # For querying night trading period data
        end += timedelta(1)

        # Only query open interest for futures contract
        fields = [
            "open",
            "high",
            "low",
            "last",
            "prev_close",
            "volume",
            "limit_up",
            "limit_down",
            "b1",
            "b2",
            "b3",
            "b4",
            "b5",
            "a1",
            "a2",
            "a3",
            "a4",
            "a5",
            "b1_v",
            "b2_v",
            "b3_v",
            "b4_v",
            "b5_v",
            "a1_v",
            "a2_v",
            "a3_v",
            "a4_v",
            "a5_v",
        ]
        if not symbol.isdigit():
            fields.append("open_interest")

        df = rqdata_get_price(
            wind_symbol,
            frequency="tick",
            fields=fields,
            start_date=start,
            end_date=end,
            adjust_type="none"
        )

        data: List[TickData] = []

        if df is not None:
            for ix, row in df.iterrows():
                dt = row.name.to_pydatetime()
                dt = CHINA_TZ.localize(dt)

                tick = TickData(
                    symbol=symbol,
                    exchange=exchange,
                    datetime=dt,
                    open_price=row["open"],
                    high_price=row["high"],
                    low_price=row["low"],
                    pre_close=row["prev_close"],
                    last_price=row["last"],
                    volume=row["volume"],
                    open_interest=row.get("open_interest", 0),
                    limit_up=row["limit_up"],
                    limit_down=row["limit_down"],
                    bid_price_1=row["b1"],
                    bid_price_2=row["b2"],
                    bid_price_3=row["b3"],
                    bid_price_4=row["b4"],
                    bid_price_5=row["b5"],
                    ask_price_1=row["a1"],
                    ask_price_2=row["a2"],
                    ask_price_3=row["a3"],
                    ask_price_4=row["a4"],
                    ask_price_5=row["a5"],
                    bid_volume_1=row["b1_v"],
                    bid_volume_2=row["b2_v"],
                    bid_volume_3=row["b3_v"],
                    bid_volume_4=row["b4_v"],
                    bid_volume_5=row["b5_v"],
                    ask_volume_1=row["a1_v"],
                    ask_volume_2=row["a2_v"],
                    ask_volume_3=row["a3_v"],
                    ask_volume_4=row["a4_v"],
                    ask_volume_5=row["a5_v"],
                    gateway_name="RQ"
                )

                data.append(tick)

        return data


wind_client = WindClient()
