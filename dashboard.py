import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=60000, key="refresh")
st.set_page_config(layout="wide")

# -------------------
# CONFIG
# -------------------
CAPITAL = 10000
RIESGO = 0.01

# 🔴 Universo robusto (evitamos scraping)
TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META","TSLA","AMD","GOOGL","NFLX","BABA",
    "JPM","XOM","CVX","BA","DIS","UBER","COIN","PLTR","SHOP","SNOW",
    "INTC","PYPL","CRM","ADBE","ORCL","CSCO","PEP","KO","MCD","WMT"
]

# -------------------
# DATA
# -------------------
@st.cache_data(ttl=300)
def get_data(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[["Open","High","Low","Close","Volume"]].astype(float)
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

    hl = df['High'] - df['Low']
    hc = (df['High'] - df['Close'].shift()).abs()
    lc = (df['Low'] - df['Close'].shift()).abs()

    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()

    return df

# -------------------
# LÓGICA
# -------------------
def analizar(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0
    señal = None

    if last['EMA20'] > last['EMA50']:
        score += 2

    if last['Close'] > prev['High']:
        señal = "COMPRA"
        score += 3

    elif last['Close'] < last['EMA20']:
        señal = "COMPRA"
        score += 2

    return señal, score

# -------------------
# PLAN
# -------------------
def plan_trade(precio, atr):
    if pd.isna(atr) or atr <= 0:
        atr = precio * 0.02

    stop = precio - (1.2 * atr)
    riesgo = precio - stop

    tp1 = precio + riesgo * 1.5
    tp2 = precio + riesgo * 3

    size = (CAPITAL * RIESGO) / riesgo

    return round(stop,2), round(tp1,2), round(tp2,2), int(max(1,size))

# -------------------
# UI
# -------------------
st.title("🚀 Scanner de Oportunidades USA")

resultados = []

# 🔴 límite controlado (clave)
for ticker in TICKERS:
    df = get_data(ticker)

    if df is None:
        continue

    df = add_indicators(df)

    señal, score = analizar(df)

    if señal == "COMPRA" and score >= 4:
        precio = df['Close'].iloc[-1]
        atr = df['ATR'].iloc[-1]

        stop, tp1, tp2, size = plan_trade(precio, atr)

        resultados.append({
            "Ticker": ticker,
            "Precio": round(precio,2),
            "Comprar": round(precio,2),
            "Stop": stop,
            "Vender TP1": tp1,
            "Vender TP2": tp2,
            "Tamaño": size,
            "Score": score
        })

# -------------------
# OUTPUT
# -------------------
if len(resultados) == 0:
    st.warning("No hay oportunidades claras ahora")
else:
    df_res = pd.DataFrame(resultados)
    df_res = df_res.sort_values(by="Score", ascending=False).head(10)

    st.markdown("## 🏆 TOP 10 PARA COMPRAR AHORA")

    st.dataframe(df_res, use_container_width=True)

    cols = st.columns(5)

    for i, row in df_res.iterrows():
        with cols[i % 5]:
            st.subheader(row["Ticker"])

            st.metric("💰 Comprar ahora", row["Comprar"])

            st.success(f"🎯 TP1: {row['Vender TP1']}")
            st.info(f"🚀 TP2: {row['Vender TP2']}")

            st.error(f"🛑 Stop: {row['Stop']}")
            st.write(f"📦 Tamaño: {row['Tamaño']}")
