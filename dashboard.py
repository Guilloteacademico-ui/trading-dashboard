import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.set_page_config(layout="wide")

TICKERS = ["C", "GOLD", "CMCSA", "BTG", "ONC"]
CAPITAL = 10000
RIESGO = 0.01

@st.cache_data
def get_data(ticker):
    df = yf.download(ticker, interval="1h", period="3mo")
    df.dropna(inplace=True)
    return df

def add_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    atr = ta.volatility.AverageTrueRange(
        df['High'], df['Low'], df['Close'], window=14
    )
    df['ATR'] = atr.average_true_range()
    return df

def get_signal(df):
    last = df.iloc[-1]

    if last['Close'] > last['EMA50'] and last['Close'] < last['EMA20']:
        return "BUY_PULLBACK"

    if last['Close'] > df['High'].rolling(20).max().iloc[-2]:
        return "BUY_BREAKOUT"

    return "—"

def calcular_trade(precio, atr):
    stop = precio - (1.3 * atr)
    riesgo = precio - stop
    size = (CAPITAL * RIESGO) / riesgo
    return round(stop,2), int(size)

st.title("📊 Trading Dashboard")

cols = st.columns(len(TICKERS))

for i, ticker in enumerate(TICKERS):
    with cols[i]:
        df = get_data(ticker)
        df = add_indicators(df)

        precio = df['Close'].iloc[-1]
        signal = get_signal(df)
        atr = df['ATR'].iloc[-1]

        stop, size = calcular_trade(precio, atr)

        st.subheader(ticker)
        st.metric("Precio", round(precio,2))

        if signal != "—":
            st.success(signal)
        else:
            st.warning("Sin señal")

        st.write(f"Stop: {stop}")
        st.write(f"Size: {size}")

        st.line_chart(df[['Close', 'EMA20', 'EMA50']])
