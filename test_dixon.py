import yfinance as yf
import pandas as pd

symbol = "DIXON.NS"
df = yf.download(symbol, start="2025-07-01", end="2025-07-10", interval="30m")
df["SMA20"] = df["Close"].rolling(20).mean()
df["SMA50"] = df["Close"].rolling(50).mean()

print(df.tail(20))
