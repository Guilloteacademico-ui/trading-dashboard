import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# -------------------
# AUTO REFRESH
# -------------------
st_autorefresh(interval=60000, key="refresh")

st.set_page_config(layout="wide")

# -------------------
# ESTILO (Wallbit/Bloomberg)
# -------------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}
.metric-card {
    background-color: #151a23;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 0px 10px rgba(0,0,0,0.5);
}
.green { color: #00ff9c; }
.red { color: #ff4b4b; }
</style>
""", unsafe_allow_html=True)

# -------------------
# CONFIG
# -------------------
TICKERS = ["C", "GOLD", "CMCSA", "BTG", "ONC"]
CAPITAL = 10000
RIESGO = 0.01

# -------------------
# DATA
# -------------------
@st.cache_data
def get_data(ticker):
    try:
        df = yf.download(ticker, interval="1h", period="3mo")

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[["Open", "High", "Low", "Close", "Volume"]]
        df = df.astype(float)
        df.dropna(inplace=True)

        if len(df) < 30:
            return None

        return df
    except:
        return None

# -------------------
# INDICADORES
# -------------------
def add_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()

    return df

# -------------------
# SEÑALES
# -------------------
def get_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if last['EMA20'] > last['EMA50'] and last['Close'] < last['EMA20']:
        return "PULLBACK"

    if last['Close'] > prev['High']:
        return "BREAKOUT"

    return "NEUTRAL"

# -------------------
# RIESGO
# -------------------
def calcular_trade(precio, atr):
    if pd.isna(atr) or atr <= 0:
        atr = precio * 0.02

    stop = precio - (1.2 * atr)
    riesgo = precio - stop

    capital_riesgo = CAPITAL * RIESGO
    size = capital_riesgo / riesgo

    return round(stop, 2), max(1, int(size))

# -------------------
# SIDEBAR
# -------------------
st.sidebar.title("📊 Trading Desk")

st.sidebar.markdown("### Capital")
st.sidebar.write(f"${CAPITAL:,.0f}")

st.sidebar.markdown("### Riesgo por trade")
st.sidebar.write(f"{RIESGO*100}%")

# -------------------
# HEADER
# -------------------
st.title("📈 Trading Dashboard Pro")

# -------------------
# CARDS SUPERIORES
# -------------------
cols = st.columns(len(TICKERS))

signals_log = []

for i, ticker in enumerate(TICKERS):
    with cols[i]:
        df = get_data(ticker)

        if df is None:
            st.warning("Sin datos")
            continue

        df = add_indicators(df)

        precio = df['Close'].iloc[-1]
        atr = df['ATR'].iloc[-1]

        signal = get_signal(df)
        stop, size = calcular_trade(precio, atr)

        signals_log.append([ticker, signal, round(precio,2)])

        st.markdown(f"### {ticker}")
        st.metric("Precio", round(precio, 2))

        if signal == "PULLBACK":
            st.success("🟢 PULLBACK")
        elif signal == "BREAKOUT":
            st.info("🔵 BREAKOUT")
        else:
            st.warning("⚪ NEUTRAL")

        st.write(f"Stop: {stop}")
        st.write(f"Size: {size}")

# -------------------
# GRÁFICO PRINCIPAL
# -------------------
st.markdown("## 📊 Chart principal")

ticker_sel = st.selectbox("Seleccionar activo", TICKERS)

df = get_data(ticker_sel)

if df is not None:
    df = add_indicators(df)

    chart_df = df[['Close', 'EMA20', 'EMA50']].copy()
    chart_df.columns = ['Precio', 'EMA20', 'EMA50']

    st.line_chart(chart_df.tail(150))

# -------------------
# TABLA SEÑALES
# -------------------
st.markdown("## 📡 Últimas señales")

signals_df = pd.DataFrame(signals_log, columns=["Ticker", "Señal", "Precio"])
st.dataframe(signals_df, use_container_width=True)

# -------------------
# PANEL RIESGO
# -------------------
st.markdown("## ⚖️ Risk Overview")

total_positions = len([s for s in signals_log if s[1] != "NEUTRAL"])
risk_used = total_positions * (CAPITAL * RIESGO)

col1, col2, col3 = st.columns(3)

col1.metric("Posiciones activas", total_positions)
col2.metric("Riesgo usado", f"${risk_used:,.0f}")
col3.metric("Riesgo disponible", f"${CAPITAL - risk_used:,.0f}")
