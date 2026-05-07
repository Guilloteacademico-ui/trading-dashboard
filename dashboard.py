import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.set_page_config(layout="wide")

# -------------------
# CONFIG
# -------------------
TICKERS = ["C", "GOLD", "CMCSA", "BTG", "ONC"]
CAPITAL = 10000
RIESGO = 0.01

# -------------------
# DATA (ROBUSTO)
# -------------------
@st.cache_data
def get_data(ticker):
    try:
        df = yf.download(ticker, interval="1h", period="3mo")

        if df is None or df.empty:
            return None

        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in required_cols:
            if col not in df.columns:
                return None

        df.dropna(inplace=True)

        if len(df) < 20:
            return None

        return df

    except:
        return None

# -------------------
# INDICADORES (ROBUSTO)
# -------------------
def add_indicators(df):
    if df is None or df.empty:
        return df

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    try:
        atr = ta.volatility.AverageTrueRange(
            df['High'], df['Low'], df['Close'], window=14
        )
        df['ATR'] = atr.average_true_range()
    except:
        df['ATR'] = 0

    return df

# -------------------
# SEÑAL
# -------------------
def get_signal(df):
    try:
        last = df.iloc[-1]

        if last['Close'] > last['EMA50'] and last['Close'] < last['EMA20']:
            return "BUY_PULLBACK"

        if last['Close'] > df['High'].rolling(20).max().iloc[-2]:
            return "BUY_BREAKOUT"

        return "—"
    except:
        return "—"

# -------------------
# RIESGO
# -------------------
def calcular_trade(precio, atr):
    try:
        if atr == 0:
            return 0, 0

        stop = precio - (1.3 * atr)
        riesgo = precio - stop

        if riesgo <= 0:
            return 0, 0

        size = (CAPITAL * RIESGO) / riesgo
        return round(stop, 2), int(size)
    except:
        return 0, 0

# -------------------
# UI
# -------------------
st.title("📊 Trading Dashboard")

cols = st.columns(len(TICKERS))

for i, ticker in enumerate(TICKERS):
    with cols[i]:
        st.subheader(ticker)

        df = get_data(ticker)

        if df is None:
            st.warning("Sin datos disponibles")
            continue

        df = add_indicators(df)

        try:
            precio = df['Close'].iloc[-1]
            atr = df['ATR'].iloc[-1]
        except:
            st.warning("Error en datos")
            continue

        signal = get_signal(df)
        stop, size = calcular_trade(precio, atr)

        st.metric("Precio", round(precio, 2))

        if signal != "—":
            st.success(signal)
        else:
            st.warning("Sin señal")

        st.write(f"🛑 Stop: {stop}")
        st.write(f"📦 Size: {size}")

        # gráfico seguro
        try:
            st.line_chart(df[['Close', 'EMA20', 'EMA50']])
        except:
            st.write("No se pudo generar gráfico")
    
