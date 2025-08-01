import streamlit as st
import pandas as pd
import pyotp
from smartapi import SmartConnect
import yfinance as yf
import datetime as dt
import pytz

# Load config
import json
with open("config.json") as f:
    config = json.load(f)

API_KEY = config["api_key"]
CLIENT_ID = config["client_id"]
PASSWORD = config["password"]
TOTP_SECRET = config["totp_secret"]

# Removed global totp generation to avoid stale OTP credentials

# SmartAPI login (deferred until user presses the button)
smartApi = None

# NOTE: TOTP should be generated at the moment we try to login, not at module import time.
def login_smartapi():
    """Login to SmartAPI and return the SmartConnect instance or raise an error."""
    totp = pyotp.TOTP(TOTP_SECRET).now()  # generate fresh token
    smart_api = SmartConnect(api_key=API_KEY)
    smart_api.generateSession(CLIENT_ID, PASSWORD, totp)
    return smart_api

st.title("📈 Intraday Bounce Scanner (IST)")

symbol = st.text_input("Enter NSE Stock Symbol (e.g., DIXON.NS)", "DIXON.NS")
tf = st.selectbox("Select Timeframe", ["15m", "30m", "1h"])
period = st.selectbox("Select Period", ["5d", "1mo", "3mo"])

if st.button("Fetch Data"):
    # Perform SmartAPI login with a fresh OTP each time the user clicks the button
    if smartApi is None:
        try:
            smartApi = login_smartapi()
            st.sidebar.success("✅ SmartAPI Login Successful")
        except Exception as e:
            st.sidebar.error(f"SmartAPI Login Failed: {e}")

    df = yf.download(symbol, period=period, interval=tf)
    if df.empty:
        st.error("No data found.")
    else:
        # Ensure the timestamp index is timezone aware in UTC before converting
        if df.index.tz is None:
            df = df.tz_localize("UTC")
        df = df.tz_convert("Asia/Kolkata")
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()

        st.write(df.tail(10))

        last = df.iloc[-1]
        st.write(f"Last Candle Time (IST): {last.name}")
        st.write(f"Close: {last['Close']}, SMA20: {last['SMA20']}, SMA50: {last['SMA50']}")

