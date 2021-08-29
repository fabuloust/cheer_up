import math
from vnpy.trader.database import *
from WindPy import w
from vnpy.trader.object import BarData
from datetime import *
import numpy as np
w.start()
w.isconnected()
class Ex:
    CZCE = 'CZC'
    DCE = 'DCE'
    SHFE = 'SHF'


symbols = ['SA201']

if __name__ == '__main__':
    for symbol in symbols:
        start_time = datetime.strptime('2021-05-01 09:00:00', "%Y-%m-%d %H:%M:%S")
        last_close = last_oi = 0
        while start_time < datetime.now():
            end_time = start_time + timedelta(days=10)
            result = w.wsi('{}.{}'.format(symbol, Ex.CZCE), 'open,close,high,low,volume,oi',
                           start_time.strftime("%Y-%m-%d %H:%M:%S"), end_time.strftime("%Y-%m-%d %H:%M:%S"), 'BarSize=1')
            start_time = end_time
            try:
                open_price, close, high, low, volume, oi = result.Data
                time_list = result.Times
            except Exception as e:
                print(result.Data, e)
            total_num = len(open_price)
            data_list = []
            for i in range(total_num):
                if np.isnan(open_price[i]):
                    continue
                data_list.append(
                    BarData(
                        symbol=symbol,
                        exchange=Exchange.CZCE,
                        interval=Interval.MINUTE,
                        datetime=time_list[i],
                        open_price=open_price[i],
                        close_price=close[i],
                        high_price=high[i],
                        low_price=low[i],
                        volume=volume[i],
                        open_interest=oi[i],
                        gateway_name='WIND'
                    )
                )
            database_manager.save_bar_data(data_list)
