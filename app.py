import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import datetime

# --- 網頁設定 ---
st.set_page_config(
    page_title="全球市場儀表板",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 自定義 CSS ---
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 18px; }
    .stTitle { font-size: 2.5rem !important; font-weight: bold; }
    .stMarkdown p { font-size: 1.1rem; line-height: 1.6; }
    .indicator-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #ddd; }
    .card-title { font-size: 1.3rem; color: #555; font-weight: bold; margin-bottom: 10px; }
    .current-value { font-size: 3rem !important; font-weight: bold; margin-right: 10px; }
    .ma-text { font-size: 1rem; color: #666; }
    .trend-bullish { color: #FF4B4B !important; } /* 紅色 */
    .trend-bearish { color: #00C853 !important; } /* 綠色 */
    .trend-neutral { color: #777 !important; }
    [data-testid="stDataFrame"] { display: none; }
    @media (max-width: 640px) {
        .reportview-container .main .block-container{ padding-left: 1rem; padding-right: 1rem; }
        .current-value { font-size: 2.5rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌐 全球市場儀表板")
st.markdown("觀察指標：**Oil (成本)｜DXY (資金)｜VIX (情緒)｜Gold (避險)｜Yield (利率)**")
st.markdown("---")

indicators = {
    "VIX (恐慌指數)": "^VIX",
    "DXY (美元指數)": "DX-Y.NYB",
    "Crude Oil (原油)": "CL=F",
    "Gold (黃金)": "GC=F",
    "10Y Yield (殖利率)": "^TNX"
}

# 抓取資料函數 (快取 5 分鐘)
@st.cache_data(ttl=300)
def fetch_all_data():
    all_data = {}
    summary_list = []
    
    for name, ticker in indicators.items():
        try:
            df = yf.Ticker(ticker).history(period="3mo")
            if not df.empty:
                df['MA5'] = df['Close'].rolling(window=5).mean()
                df['MA10'] = df['Close'].rolling(window=10).mean()
                
                current_price = float(df['Close'].iloc[-1])
                prev_price = float(df['Close'].iloc[-2])
                ma5_val = float(df['MA5'].iloc[-1])
                ma10_val = float(df['MA10'].iloc[-1])
                
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100
                
                if current_price > ma5_val:
                    trend_text = "偏多"
                    color_class = "trend-bullish"
                    arrow = "🔼"
                elif current_price < ma5_val:
                    trend_text = "偏空"
                    color_class = "trend-bearish"
                    arrow = "🔽"
                else:
                    trend_text = "盤整"
                    color_class = "trend-neutral"
                    arrow = "➖"
                
                df = df.reset_index()
                all_data[name] = df
                
                summary_list.append({
                    "name": name,
                    "current": current_price,
                    "change_pct": change_pct,
                    "trend_text": trend_text,
                    "color_class": color_class,
                    "arrow": arrow,
                    "ma5": ma5_val,
                    "ma10": ma10_val
                })
        except Exception as e:
            st.error(f"資料抓取失敗 {name}: {e}")
            
    return summary_list, all_data

# --- 繪製帶有高低點標籤的走勢線 ---
def plot_sparkline_with_labels(df, color_class):
    line_color = '#FF4B4B' if color_class == 'trend-bullish' else '#00C853'
    if color_class == 'trend-neutral': line_color = '#777'
    
    # 準備最近 30 天的資料
    plot_df = df.tail(30).copy()
    
    # 將日期格式化為 MM/DD 用於顯示
    plot_df['DateStr'] = plot_df['Date'].dt.strftime('%m/%d')
    # 建立標籤文字：數值 (日期)
    plot_df['Label'] = plot_df['Close'].round(2).astype(str) + " (" + plot_df['DateStr'] + ")"
    
    # 找出最高點與最低點
    max_idx = plot_df['Close'].idxmax()
    min_idx = plot_df['Close'].idxmin()
    max_df = plot_df.loc[[max_idx]]
    min_df = plot_df.loc[[min_idx]]
    
    # 1. 基礎走勢線
    base_line = alt.Chart(plot_df).mark_line(
        interpolate='basis', strokeWidth=3
    ).encode(
        x=alt.X('Date:T', axis=None),
        y=alt.Y('Close:Q', scale=alt.Scale(zero=False), axis=None),
        color=alt.value(line_color)
    )
    
    # 2. 最高點標記與文字
    max_point = alt.Chart(max_df).mark_circle(color='#FF4B4B', size=60).encode(x='Date:T', y='Close:Q')
    max_text = alt.Chart(max_df).mark_text(
        align='center', baseline='bottom', dy=-10, color='#555', fontSize=12, fontWeight='bold'
    ).encode(x='Date:T', y='Close:Q', text='Label')
    
    # 3. 最低點標記與文字
    min_point = alt.Chart(min_df).mark_circle(color='#00C853', size=60).encode(x='Date:T', y='Close:Q')
    min_text = alt.Chart(
