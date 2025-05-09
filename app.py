import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta, time

# --- Ticker Selection ---
ticker_list = [
    "SPY", "QQQ", "DIA", "IWM", "VTI", "XLF", "XLK", "XLE", "XLY", "XLV",
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "AMD", "INTC",
    "BA", "JPM", "BAC", "WFC", "UNH", "V", "MA", "T", "DIS", "PEP",
    "KO", "COST", "WMT", "HD", "NKE", "CRM", "PYPL", "ADBE", "AVGO", "CSCO",
    "CVX", "XOM", "PFE", "MRK", "ABBV", "TMO", "AMGN", "JNJ", "VRTX", "LMT",
    "GE", "GM", "F", "UBER", "LYFT", "PLTR", "SNOW", "NET", "ROKU", "SQ",
    "SHOP", "BABA", "BIDU", "JD", "TSM", "ASML", "IBM", "ORCL", "QCOM", "TXN",
    "ETSY", "EBAY", "ZM", "DOCU", "RBLX", "TWLO", "PANW", "OKTA", "CRWD", "DDOG",
    "TLT", "HYG", "IEF", "SHY", "GLD", "SLV", "USO", "UNG", "UUP", "FXI"
]

ticker = st.selectbox("Select a stock or ETF:", sorted(ticker_list))

# --- Time Selector ---
times = []
start = datetime.combine(datetime.today(), time(9, 30))
end = datetime.combine(datetime.today(), time(16, 0))
while start <= end:
    times.append(start.time())
    start += timedelta(minutes=5)

time_options = ["Any time"] + [t.strftime("%H:%M") for t in times]
selected_time = st.selectbox("Choose a time of day:", time_options)

# --- Weekday Selector ---
selected_day = st.selectbox("Choose a weekday:", ["Any day", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
weekday_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}

# --- Download Data + Compute RSI up front for sliders ---
st.write(f"📦 Downloading 5-minute {ticker} data from the past 30 days...")
df = yf.Ticker(ticker).history(period="30d", interval="5m").reset_index()
df = df[(df["Datetime"].dt.time >= time(9, 30)) & (df["Datetime"].dt.time <= time(16, 0))]
df["RSI"] = RSIIndicator(close=df["Close"], window=14).rsi()

# --- Sliders show before button ---
rsi_min, rsi_max = st.slider("RSI range:", 0, 100, (0, 100))
volume_min, volume_max = st.slider("Volume range:", 0, int(df["Volume"].max()), (0, int(df["Volume"].max())))

# --- Forecast Button Logic ---
if st.button("Get Historical Forecast"):
    returns_5 = []
    returns_15 = []

    for date in df["Datetime"].dt.date.unique():
        if selected_day != "Any day" and datetime.strptime(str(date), "%Y-%m-%d").weekday() != weekday_map[selected_day]:
            continue

        day_df = df[df["Datetime"].dt.date == date].copy()

        if selected_time == "Any time":
            match_rows = day_df
        else:
            match_rows = day_df[day_df["Datetime"].dt.strftime("%H:%M") == selected_time]

        for idx in match_rows.index:
            rsi_now = df.loc[idx, "RSI"]
            volume_now = df.loc[idx, "Volume"]

            if pd.isna(rsi_now) or not (rsi_min <= rsi_now <= rsi_max):
                continue
            if not (volume_min <= volume_now <= volume_max):
                continue

            try:
                price_now = df.loc[idx, "Close"]
                price_5 = df.loc[idx + 1, "Close"]
                price_15 = df.loc[idx + 3, "Close"]

                ret_5 = ((price_5 - price_now) / price_now) * 100
                ret_15 = ((price_15 - price_now) / price_now) * 100
                returns_5.append(ret_5)
                returns_15.append(ret_15)
            except IndexError:
                continue

    if returns_5:
        avg_5 = round(sum(returns_5) / len(returns_5), 3)
        avg_15 = round(sum(returns_15) / len(returns_15), 3)

        st.success(f"📊 Average 5-min return: **{avg_5}%**")
        st.success(f"📊 Average 15-min return: **{avg_15}%**")
        st.caption(f"Matches: {len(returns_5)} — RSI {rsi_min}-{rsi_max}, Volume {volume_min}-{volume_max}")
    else:
        st.warning("Not enough data for those filters.")
