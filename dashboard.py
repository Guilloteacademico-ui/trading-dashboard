import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.set_page_config(layout="wide")

TICKERS = ["C", "GOLD", "CMCSA", "BTG", "ONC"]
CAPITAL = 10000
RIESGO = 0.01

# -------------------
# DATA ROBUSTO
# -------------------
@st.cache_data
def get_data(ticker):
    try:
        df = yf.download(ticker, interval="1h", period="3mo")

        if df is None or df.empty:
            return None

        # 🔴 FIX CLAVE: eliminar multi-index
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # asegurar columnas
        df = df[["Open", "High", "Low", "Close", "Volume"]]

        # 🔴 convertir a float
        df = df.astype(float)

        df.dropna(inplace=True)

        if len(df) < 30:
            return None

        return df

    except Exception as e:
        return None

# -------------------
# INDICADORES SIN LIB ta (más estable)
# -------------------
def add_indicators(df):
    try:
        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()

        # 🔴 ATR manual (evita errores de ta)
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(14).mean()

        return df

    except:
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
        if pd.isna(atr) or atr == 0:
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
            st.warning("Sin datos")
            continue

        df = add_indicators(df)

        try:
            precio = float(df['Close'].iloc[-1])
            atr = float(df['ATR'].iloc[-1])
        except:
            st.warning("Error datos")
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

        try:
            st.line_chart(df[['Close', 'EMA20', 'EMA50']])
        except:
            st.write("Sin gráfico")
