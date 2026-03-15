import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import datetime

# --- 網頁設定 ---
st.set_page_config(page_title="專業市場儀表板", layout="wide", initial_sidebar_state="expanded")

# --- 初始化暫存狀態 (Session State) ---
# 確保每次重整網頁時，自訂的股票清單不會消失
if 'custom_tickers' not in st.session_state:
    st.session_state.custom_tickers = []

# --- 自定義 CSS ---
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 16px; }
    .stTitle { font-size: 1.8rem !important; font-weight: bold; }
    .stMarkdown p { font-size: 1.1rem; line-height: 1.6; }
    .indicator-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #ddd; }
    .card-title { font-size: 1.3rem; color: #555; font-weight: bold; margin-bottom: 10px; }
    .current-value { font-size: 3rem !important; font-weight: bold; margin-right: 10px; }
    .ma-text { font-size: 1rem; color: #666; }
    .trend-bullish { color: #FF4B4B !important; }
    .trend-bearish { color: #00C853 !important; }
    .trend-neutral { color: #777 !important; }
    [data-testid="stDataFrame"] { display: none; }
    @media (max-width: 640px) {
        .reportview-container .main .block-container{ padding-left: 1rem; padding-right: 1rem; }
        .current-value { font-size: 2.5rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 側邊欄：導覽列與自訂標的輸入 ---
st.sidebar.title("📊 儀表板選單")
page = st.sidebar.radio("請選擇欲觀察的市場：", ["🇹🇼 台灣市場(台股)", "🌐 全球市場"])

st.sidebar.markdown("---")
st.sidebar.subheader("➕ 自訂觀察標的")
st.sidebar.caption("輸入 Yahoo 財經代碼\n(台股請加 .TW，例：2317.TW / 美股直接打：NVDA)")

# 輸入框與新增按鈕
new_ticker = st.sidebar.text_input("輸入代碼:", key="ticker_input").strip().upper()
if st.sidebar.button("加入標的"):
    if new_ticker and new_ticker not in st.session_state.custom_tickers:
        st.session_state.custom_tickers.append(new_ticker)
        st.rerun() # 重新載入網頁更新畫面

# 顯示與刪除已加入的標的
if st.session_state.custom_tickers:
    st.sidebar.write("📌 目前觀察名單：")
    for ticker in st.session_state.custom_tickers:
        col1, col2 = st.sidebar.columns([3, 1])
        col1.markdown(f"**{ticker}**")
        if col2.button("刪除", key=f"del_{ticker}"):
            st.session_state.custom_tickers.remove(ticker)
            st.rerun()

# --- 核心共用模組 ---
@st.cache_data(ttl=300)
def fetch_data(indicators_dict):
    """彈性的資料抓取函數，傳入 {顯示名稱: 代碼} 的字典"""
    all_data = {}
    summary_list = []
    
    for name, ticker in indicators_dict.items():
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
                    trend_text, color_class, arrow = "偏多", "trend-bullish", "🔼"
                elif current_price < ma5_val:
                    trend_text, color_class, arrow = "偏空", "trend-bearish", "🔽"
                else:
                    trend_text, color_class, arrow = "盤整", "trend-neutral", "➖"
                
                df = df.reset_index()
                all_data[name] = df
                
                summary_list.append({
                    "name": name, "current": current_price, "change_pct": change_pct,
                    "trend_text": trend_text, "color_class": color_class, "arrow": arrow,
                    "ma5": ma5_val, "ma10": ma10_val
                })
        except Exception as e:
            st.error(f"資料抓取失敗 {name}: 請確認代碼是否正確。")
            
    return summary_list, all_data

def plot_sparkline_with_labels(df, color_class):
    line_color = '#FF4B4B' if color_class == 'trend-bullish' else '#00C853'
    if color_class == 'trend-neutral': line_color = '#777'
    
    plot_df = df.tail(30).copy()
    plot_df['DateStr'] = plot_df['Date'].dt.strftime('%m/%d')
    plot_df['Label'] = plot_df['Close'].round(2).astype(str) + " (" + plot_df['DateStr'] + ")"
    
    max_idx = plot_df['Close'].idxmax()
    min_idx = plot_df['Close'].idxmin()
    max_df = plot_df.loc[[max_idx]]
    min_df = plot_df.loc[[min_idx]]
    
    base_line = alt.Chart(plot_df).mark_line(interpolate='basis', strokeWidth=3).encode(
        x=alt.X('Date:T', axis=None), y=alt.Y('Close:Q', scale=alt.Scale(zero=False), axis=None), color=alt.value(line_color)
    )
    max_point = alt.Chart(max_df).mark_circle(color='#FF4B4B', size=60).encode(x='Date:T', y='Close:Q')
    max_text = alt.Chart(max_df).mark_text(align='center', baseline='bottom', dy=-10, color='#555', fontSize=12, fontWeight='bold').encode(x='Date:T', y='Close:Q', text='Label')
    min_point = alt.Chart(min_df).mark_circle(color='#00C853', size=60).encode(x='Date:T', y='Close:Q')
    min_text = alt.Chart(min_df).mark_text(align='center', baseline='top', dy=10, color='#555', fontSize=12, fontWeight='bold').encode(x='Date:T', y='Close:Q', text='Label')
    
    return alt.layer(base_line, max_point, max_text, min_point, min_text).properties(height=100).configure_view(strokeWidth=0)

def render_cards(summary, history):
    """共用渲染卡片的函數"""
    for item in summary:
        precision = ".0f" if "加權" in item['name'] or "櫃買" in item['name'] or "費城" in item['name'] else ".2f"
        if "DXY" in item['name'] or "VIX" in item['name']: precision = ".1f"
        
        st.markdown(f"""
        <div class="indicator-card">
            <div class="card-title">{item['name']}</div>
            <div style="display: flex; align-items: baseline; flex-wrap: wrap;">
                <span class="current-value {item['color_class']}">{item['current']:{precision}}</span>
                <span class="{item['color_class']}" style="font-size: 1.2rem; font-weight: bold; margin-right: 15px;">{item['arrow']} {item['change_pct']:.2f}% (日)</span>
                <span class="ma-text">趨勢：<span class="{item['color_class']}" style="font-weight:bold;">{item['trend_text']}</span></span>
            </div>
            <div class="ma-text" style="margin-top: 5px;">5日均線: {item['ma5']:{precision}} ｜ 10日均線: {item['ma10']:{precision}}</div>
        </div>
        """, unsafe_allow_html=True)
        st.altair_chart(plot_sparkline_with_labels(history[item['name']], item['color_class']), use_container_width=True)
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)


# ==========================================
# 網頁主內容區塊
# ==========================================
if page == "🇹🇼 台灣市場(台股)":
    st.title("🇹🇼 台股核心儀表板")
    st.markdown("觀察指標：**加權(大盤)｜櫃買(內資)｜台積電(權值)｜匯率(熱錢)｜費半(國際科技)**")
    st.markdown("---")
    
    tw_indicators = {"加權指數 (TAIEX)": "^TWII", "櫃買指數 (OTC)": "^TWOII", "台積電 (2330)": "2330.TW", "美元/台幣 (匯率)": "TWD=X", "費城半導體 (SOX)": "^SOX"}
    summary, history = fetch_data(tw_indicators)
    
    if summary:
        st.subheader("🧠 盤勢綜合評析 (台股邏輯)")
        try:
            def get_val(name, key): return next((x[key] for x in summary if x['name'] == name), "盤整")
            analysis_text = ""
            
            # 判斷邏輯 (精簡顯示)
            if get_val("加權指數 (TAIEX)", "trend_text") == "偏多" and get_val("櫃買指數 (OTC)", "trend_text") == "偏多":
                analysis_text += "📈 **<span class='trend-bullish'>內外資齊聚：</span>** 加權與櫃買同步站上均線，健康輪動，多頭環境良好。<br><br>"
            elif get_val("加權指數 (TAIEX)", "trend_text") == "偏多" and get_val("櫃買指數 (OTC)", "trend_text") == "偏空":
                analysis_text += "⚠️ **<span class='trend-bearish'>拉積盤疑慮：</span>** 資金集中權值股，中小型股弱勢，提防賺指數賠差價。<br><br>"
            
            if get_val("美元/台幣 (匯率)", "trend_text") == "偏多":
                analysis_text += "💸 **外資匯出壓力：** 台幣貶值站上均線，留意大型權值股提款賣壓。"
            elif get_val("美元/台幣 (匯率)", "trend_text") == "偏空":
                analysis_text += "🌊 **熱錢湧入動能：** 台幣升值，資金動能充沛。"
                
            st.markdown(f"<div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #4a90e2; margin-bottom: 30px;'>{analysis_text}</div>", unsafe_allow_html=True)
        except: pass

        st.subheader("📊 核心指標")
        render_cards(summary, history)

elif page == "🌐 全球市場":
    st.title("🌐 全球市場儀表板")
    st.markdown("觀察指標：**Oil (成本)｜DXY (資金)｜VIX (情緒)｜Gold (避險)｜Yield (利率)**")
    st.markdown("---")
    
    global_indicators = {"VIX (恐慌指數)": "^VIX", "DXY (美元指數)": "DX-Y.NYB", "Crude Oil (原油)": "CL=F", "Gold (黃金)": "GC=F", "10Y Yield (殖利率)": "^TNX"}
    summary, history = fetch_data(global_indicators)
    
    if summary:
        st.subheader("🧠 總經綜合評析")
        try:
            def get_val(name, key): return next((x[key] for x in summary if x['name'] == name), "盤整")
            analysis_text = ""
            if get_val("VIX (恐慌指數)", "trend_text") == "偏多" and get_val("Gold (黃金)", "trend_text") == "偏多":
                analysis_text += "⚠️ **<span class='trend-bullish'>避險情緒顯著升溫：</span>** 恐慌指數與黃金同步走強，資金流向避險資產。<br><br>"
            if get_val("DXY (美元指數)", "trend_text") == "偏多" and get_val("10Y Yield (殖利率)", "trend_text") == "偏多":
                analysis_text += "📉 **<span class='trend-bullish'>流動性收緊：</span>** 美元與殖利率攀升，對新興市場與成長股估值造成壓力。<br><br>"
            st.markdown(f"<div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #4a90e2; margin-bottom: 30px;'>{analysis_text}</div>", unsafe_allow_html=True)
        except: pass

        st.subheader("📊 核心指標")
        render_cards(summary, history)

# ==========================================
# 區塊三：自訂觀察標的 (全站共用顯示在最下方)
# ==========================================
if st.session_state.custom_tickers:
    st.markdown("---")
    st.subheader("🎯 自訂觀察名單")
    
    # 將自訂名單轉成 {代碼: 代碼} 的格式餵給資料抓取模組
    custom_dict = {ticker: ticker for ticker in st.session_state.custom_tickers}
    c_summary, c_history = fetch_data(custom_dict)
    
    if c_summary:
        render_cards(c_summary, c_history)

st.markdown("---")
st.caption(f"數據最後更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (每5分鐘自動更新)")
st.caption("免責聲明：本儀表板數據由 Yahoo Finance 提供。紅色/🔼 代表站上5日均線(偏多)，綠色/🔽 代表跌破5日均線(偏空)。")
