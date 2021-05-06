


from vnpy.trader.database import *
from WindPy import w
from vnpy.trader.object import BarData
from datetime import *
import chinese_calendar
w.start()
w.isconnected()
symbols = ['rb2105']

class Ex:
    CZCE = 'CZC'
    DCE = 'DCE'
    SHFE = 'SHF'

for symbol in symbols:
    start_time = datetime.strptime('2020-06-01 09:00:00', "%Y-%m-%d %H:%M:%S")
    last_close = last_oi = 0
    while start_time < datetime.now():
        end_time = start_time + timedelta(days=7)
        result = w.wsi('{}.{}'.format(symbol, Ex.SHFE), 'open,close,high,low,volume,oi',
                       start_time.strftime("%Y-%m-%d %H:%M:%S"), end_time.strftime("%Y-%m-%d %H:%M:%S"), 'BarSize=1')
        start_time = end_time
        try:
            open, close, high, low, volume, oi = result.Data
        except:
            open, close, high, low, volume, oi = last_close, last_close, last_close, last_close, 0, last_oi
        if open is None:
            open, close, high, low, volume, oi = last_close, last_close, last_close, last_close, 0, last_oi
        last_close = close
        last_oi = oi
        time_list = result.Times
        total_num = len(open)
        data_list = []
        for i in range(total_num):
            data_list.append(
                BarData(
                    symbol=symbol,
                    exchange=Exchange.SHFE,
                    interval=Interval.MINUTE,
                    datetime=time_list[i],
                    open_price=open[i],
                    close_price=close[i],
                    high_price=high[i],
                    low_price=low[i],
                    volume=volume[i],
                    open_interest=oi[i],
                    gateway_name='WIND'
                )
            )
        database_manager.save_bar_data(data_list)
