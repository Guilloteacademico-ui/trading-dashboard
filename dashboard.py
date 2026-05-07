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
# ESTILO
# -------------------
st.markdown("""
<style>
body { background-color: #0e1117; color: white; }
.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# -------------------
# CONFIG
# -------------------
TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META",
    "TSLA","AMD","GOOGL","NFLX","BABA",
    "JPM","XOM","CVX","BA","DIS",
    "UBER","COIN","PLTR","SHOP","SNOW"
]

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

    # ATR manual
    hl = df['High'] - df['Low']
    hc = (df['High'] - df['Close'].shift()).abs()
    lc = (df['Low'] - df['Close'].shift()).abs()

    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()

    # Momentum
    df['RET_5'] = df['Close'].pct_change(5)

    return df

# -------------------
# SCORING (clave)
# -------------------
def score_setup(df):
    try:
        last = df.iloc[-1]
        prev = df.iloc[-2]

        score = 0
        signal = "NEUTRAL"

        # tendencia
        if last['EMA20'] > last['EMA50']:
            score += 2

        # pullback
        if last['Close'] < last['EMA20']:
            score += 2
            signal = "PULLBACK"

        # breakout
        if last['Close'] > prev['High']:
            score += 3
            signal = "BREAKOUT"

        # momentum
        if last['RET_5'] > 0:
            score += 1

        return score, signal

    except:
        return 0, "NEUTRAL"

# -------------------
# RIESGO
# -------------------
def calcular_trade(precio, atr):
    if pd.isna(atr) or atr <= 0:
        atr = precio * 0.02

    stop = precio - (1.2 * atr)
    riesgo = precio - stop

    size = (CAPITAL * RIESGO) / riesgo
    return round(stop,2), int(max(1, size))

# -------------------
# UI
# -------------------
st.title("📊 Scanner de Trading (Top Oportunidades)")

results = []

# -------------------
# SCAN
# -------------------
for ticker in TICKERS:
    df = get_data(ticker)

    if df is None:
        continue

    df = add_indicators(df)

    score, signal = score_setup(df)

    if score >= 4:  # 🔥 FILTRO CLAVE
        precio = df['Close'].iloc[-1]
        atr = df['ATR'].iloc[-1]

        stop, size = calcular_trade(precio, atr)

        results.append({
            "Ticker": ticker,
            "Señal": signal,
            "Score": score,
            "Precio": round(precio,2),
            "Stop": stop,
            "Size": size
        })

# -------------------
# RESULTADOS
# -------------------
if len(results) == 0:
    st.warning("No hay oportunidades claras ahora")
else:
    df_res = pd.DataFrame(results)

    # ordenar por calidad
    df_res = df_res.sort_values(by="Score", ascending=False)

    st.markdown("## 🚀 Top oportunidades")

    st.dataframe(df_res, use_container_width=True)

    # -------------------
    # TOP 5 VISUAL
    # -------------------
    st.markdown("## 🏆 Top 5 setups")

    top5 = df_res.head(5)

    cols = st.columns(len(top5))

    for i, row in top5.iterrows():
        with cols[i % len(cols)]:
            st.subheader(row["Ticker"])

            st.metric("Precio", row["Precio"])

            if row["Señal"] == "PULLBACK":
                st.success("🟢 PULLBACK")
            else:
                st.info("🔵 BREAKOUT")

            st.write(f"Score: {row['Score']}")
            st.write(f"Stop: {row['Stop']}")
            st.write(f"Size: {row['Size']}")
