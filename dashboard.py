import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide")

# -------------------
# CONFIG
# -------------------
CAPITAL = 10000
RIESGO = 0.01

# 🔴 Universo reducido pero efectivo
TICKERS = [
    "AAPL","CAT","NVDA","AMZN","ASML",
    "TSLA","AMD","GOOGL","NFLX","JPM",
    "XOM","BA","EWZ","UBER","PLTR","AMD","MU","AVGO","ASML","HMY","TSM"
]

# -------------------
# DATA SEGURA
# -------------------
@st.cache_data(ttl=300)
def get_data(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        df = df.reset_index()

        cols = ["Open","High","Low","Close","Volume"]
        df = df[cols]

        df = df.astype(float)
        df = df.dropna()

        if len(df) < 30:
            return None

        return df

    except Exception:
        return None

# -------------------
# INDICADORES
# -------------------
def indicadores(df):
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    tr = (df["High"] - df["Low"])
    df["ATR"] = tr.rolling(14).mean()

    return df

# -------------------
# SEÑAL SIMPLE
# -------------------
def señal(df):
    try:
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # tendencia
        if last["EMA20"] > last["EMA50"]:

            # breakout simple
            if last["Close"] > prev["High"]:
                return "COMPRA"

        return None
    except:
        return None

# -------------------
# PLAN TRADE
# -------------------
def plan(precio, atr):
    if atr == 0 or pd.isna(atr):
        atr = precio * 0.02

    stop = precio - atr
    riesgo = precio - stop

    tp = precio + (riesgo * 2)

    size = (CAPITAL * RIESGO) / riesgo

    return round(stop,2), round(tp,2), int(max(1,size))

# -------------------
# UI
# -------------------
st.title("🚀 Scanner simple USA (estable)")

resultados = []

for ticker in TICKERS:
    df = get_data(ticker)

    if df is None:
        continue

    df = indicadores(df)

    s = señal(df)

    if s == "COMPRA":
        precio = df["Close"].iloc[-1]
        atr = df["ATR"].iloc[-1]

        stop, tp, size = plan(precio, atr)

        resultados.append({
            "Ticker": ticker,
            "Comprar": round(precio,2),
            "Vender": tp,
            "Stop": stop,
            "Tamaño": size
        })

# -------------------
# OUTPUT
# -------------------
if len(resultados) == 0:
    st.warning("No hay señales ahora")
else:
    df_res = pd.DataFrame(resultados)

    st.markdown("## 🏆 Oportunidades detectadas")

    st.dataframe(df_res, use_container_width=True)

    cols = st.columns(len(df_res))

    for i, row in df_res.iterrows():
        with cols[i % len(cols)]:
            st.subheader(row["Ticker"])

            st.metric("💰 Comprar", row["Comprar"])
            st.success(f"🎯 Vender: {row['Vender']}")
            st.error(f"🛑 Stop: {row['Stop']}")
            st.write(f"📦 Tamaño: {row['Tamaño']}")
