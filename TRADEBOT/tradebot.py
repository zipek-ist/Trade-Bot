import ccxt
import pandas as pd
import stockstats
import yfinance as yf
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import datetime
import time
import openpyxl



"""
geo=yf.download("GEO",keepna=False)
geodataframe=pd.DataFrame(geo)
plt.plot(geodataframe.index,geo["Close"])
plt.show()
"""
fakeusdbalance=10000
fakeassetbalance=0
while True:

    exchange = ccxt.binance({
        'apiKey': 'iAapVX3si3h9rkbifCATeTeRLW2zMsqj6Myq5otLukCIhllPIpzv8auyZdtlRpmD',
        'secret': 'DT1TH5I7pmoGWCf0Xrb1RlIOymQjdE1hLzVTdV0FLpRZGdewnzM2jU8ACumboUur',
    })

    exchange.load_markets("BTCUSD")
    ticker = exchange.fetch_ticker('BTC/USDT')
    price=ticker["last"]

    def fetch(asset,frame):
        data=exchange.fetch_ohlcv(asset, timeframe=frame)
        df= pd.DataFrame(data,columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df

    table=fetch("BTCBUSD","1m")



    balance = exchange.fetch_balance()

    for asset, details in balance.items():
        if asset=="BUSD":
            print(f"{asset}: {details['free']}")


    table['close_change'] = table['close'].diff()
    table=table.dropna()

    s = stockstats.StockDataFrame(table)
    rsi=s.get("rsi_14")
    bolingertop = s.get('boll_ub')
    bolingerfloor = s.get('boll_lb')
    cci=s.get("cci_14")


    def check_rsi(rsi):
        if rsi > 70:
            return 'overbought'
        elif rsi < 30:
            return 'oversold'
        else:
            return 'neutral'

    def check_cci(cci):
        if cci > 200:
            return 'overbought'
        elif cci < -200:
            return 'oversold'
        else:
            return 'neutral'




    table['rsi_status'] = rsi.apply(check_rsi)
    table["bollingertop"]=bolingertop
    table["bollingerfloor"]=bolingerfloor
    table["cci_status"]=cci.apply(check_cci)
    table=table.dropna()
    table=table.drop(columns=["rs_14","boll","boll_ub","boll_lb"])
    table=table[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_change',
           'rsi_14', 'rsi_status', 'bollingertop', 'bollingerfloor', 'cci_14',
           'cci_status']]


    def action():
        if table["rsi_status"].iloc[-1]==table["cci_status"].iloc[-1]:
            return table["rsi_status"].iloc[-1]
        elif table["rsi_status"].iloc[-1]=="neutral":
            if table["cci_status"].iloc[-1]=="overbought" or "oversold":
                return table["cci_status"].iloc[-1]
        elif table["cci_status"].iloc[-1] == "neutral":
            if table["rsi_status"].iloc[-1] == "overbought" or "oversold":
                return table["rsi_status"].iloc[-1]
        elif table["cci_status"].iloc[-1]=="overbought":
            if table["rsi_status"].iloc[-1]=="oversold":
                return "neutral"
        elif table["rsi_status"].iloc[-1] == "overbought":
            if table["cci_status"].iloc[-1] == "oversold":
                return "neutral"

        else:
            pass
    table["action"]=action()


    #Lineer Regression ile ML çalışması
    dumtable=pd.get_dummies(table,columns=["rsi_status","cci_status","action"],drop_first=True)
    y=dumtable["close"]
    x=dumtable.drop(columns=["close"])
    x_train,x_test,y_train,y_test=train_test_split(x,y,train_size=0.80)

    reg=LinearRegression()

    model=reg.fit(x_train,y_train)
    lineerscore=model.score(x_train,y_train)
    lineerpredict=model.predict(x)

    table["lineerscore"]=lineerscore
    table["lineerpredict"]=lineerpredict

    writer = pd.ExcelWriter('trading.xlsx')
    table.to_excel(writer)
    writer.save()
    print("DataFrame is exported successfully to 'trading.xlsx' Excel File.")
    now=datetime.datetime.now()
    print(f"Last update : {now}")
    signal=table["action"].iloc[-1]
    print(f'RSI: {table["rsi_14"].iloc[-1]}')
    print(f'CCI: {table["cci_14"].iloc[-1]}')

    print("Action :"+signal)

    if signal=="oversold":
        if fakeusdbalance>=table["close"].iloc[-1]*0.1:
            fakeassetbalance=fakeassetbalance+0.1
            fakeusdbalance=fakeusdbalance-table["close"].iloc[-1]*0.1

    elif signal=="overbought":
        if fakeassetbalance>=0.1:
            fakeassetbalance=fakeassetbalance-0.1
            fakeusdbalance=fakeusdbalance+table["close"].iloc[-1]*0.1

    else:
        pass
    print(f"FAKE USD BALANCE :{fakeusdbalance}")
    print(f"FAKE ASSET BALANCE :{fakeassetbalance}")
    time.sleep(60)


