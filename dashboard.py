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

# -------------------
# UNIVERSO (S&P500 dinámico)
# -------------------
@st.cache_data
def get_sp500():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url)[0]
    return table['Symbol'].tolist()

# -------------------
# DATA
# -------------------
@st.cache_data
def get_data(ticker):
    try:
        df = yf.download(ticker, interval="1d", period="6mo")

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[["Open","High","Low","Close","Volume"]].astype(float)
        df.dropna(inplace=True)

        if len(df) < 50:
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

    df['RET_5'] = df['Close'].pct_change(5)

    return df

# -------------------
# SCORING
# -------------------
def score_setup(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0
    signal = "NEUTRAL"

    if last['EMA20'] > last['EMA50']:
        score += 2

    if last['Close'] < last['EMA20']:
        score += 2
        signal = "PULLBACK"

    if last['Close'] > prev['High']:
        score += 3
        signal = "BREAKOUT"

    if last['RET_5'] > 0:
        score += 1

    return score, signal

# -------------------
# RIESGO
# -------------------
def calcular_trade(precio, atr):
    if pd.isna(atr) or atr <= 0:
        atr = precio * 0.02

    stop = precio - (1.2 * atr)
    riesgo = precio - stop
    size = (CAPITAL * RIESGO) / riesgo

    return round(stop,2), int(max(1,size))

# -------------------
# UI
# -------------------
st.title("🚀 Scanner Real - Top 5 USA")

tickers = get_sp500()

results = []

progress = st.progress(0)
total = len(tickers)

# -------------------
# SCAN MASIVO
# -------------------
for i, ticker in enumerate(tickers[:200]):  # 🔴 limitamos a 200 para performance
    df = get_data(ticker)

    if df is None:
        continue

    df = add_indicators(df)
    score, signal = score_setup(df)

    if score >= 4:
        precio = df['Close'].iloc[-1]
        atr = df['ATR'].iloc[-1]

        stop, size = calcular_trade(precio, atr)

        results.append({
            "Ticker": ticker,
            "Score": score,
            "Señal": signal,
            "Precio": round(precio,2),
            "Stop": stop,
            "Size": size
        })

    progress.progress((i+1)/200)

# -------------------
# RESULTADOS
# -------------------
if len(results) == 0:
    st.warning("No hay oportunidades claras ahora")
else:
    df_res = pd.DataFrame(results)
    df_res = df_res.sort_values(by="Score", ascending=False)

    st.markdown("## 🏆 TOP 5 OPORTUNIDADES")

    top5 = df_res.head(5)

    st.dataframe(top5, use_container_width=True)

    cols = st.columns(5)

    for i, row in top5.iterrows():
        with cols[i % 5]:
            st.subheader(row["Ticker"])
            st.metric("Precio", row["Precio"])

            if row["Señal"] == "PULLBACK":
                st.success("🟢 PULLBACK")
            else:
                st.info("🔵 BREAKOUT")

            st.write(f"Score: {row['Score']}")
            st.write(f"Stop: {row['Stop']}")
            st.write(f"Size: {row['Size']}")
