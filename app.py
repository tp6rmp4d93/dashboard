import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import datetime
import requests

# --- 網頁設定 ---
st.set_page_config(page_title="專業市場儀表板", layout="wide", initial_sidebar_state="expanded")

# --- 內建台股產業分類字典 ---
INDUSTRY_STOCKS = {
    "🛠️ 半導體業": ["2330.TW", "2454.TW", "2303.TW", "3711.TW", "2379.TW", "3231.TW", "2408.TW", "3443.TW"],
    "💻 電腦及週邊設備": ["2382.TW", "3231.TW", "2356.TW", "2324.TW", "2376.TW", "2395.TW", "6669.TW"],
    "🏦 金融保險業": ["2881.TW", "2882.TW", "2891.TW", "2886.TW", "2884.TW", "2892.TW", "2885.TW", "2880.TW"],
    "🚢 航運業": ["2603.TW", "2609.TW", "2615.TW", "2618.TW", "2610.TW", "2606.TW", "2637.TW"],
    "🔌 電子零組件業": ["2308.TW", "2327.TW", "3037.TW", "2313.TW", "3044.TW", "2368.TW", "3017.TW"]
}

# --- 初始化暫存狀態 ---
if 'custom_tickers' not in st.session_state: st.session_state.custom_tickers = []
if 'stock_pool' not in st.session_state: st.session_state.stock_pool = ["2330.TW", "2317.TW", "2454.TW", "2881.TW", "2603.TW"]

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
    .trend-bullish { color: #FF4B4B !important; }
    .trend-bearish { color: #00C853 !important; }
    .trend-neutral { color: #777 !important; }
    [data-testid="stDataFrame"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# --- 側邊欄 ---
st.sidebar.title("📊 儀表板選單")
page = st.sidebar.radio("請選擇模組：", ["🇹🇼 台灣市場 (台股)", "🌐 全球市場 (總經)", "📂 產業股票池", "🔍 潛力股自動篩選"])

st.sidebar.markdown("---")
st.sidebar.subheader("➕ 自訂觀察標的")
new_ticker = st.sidebar.text_input("輸入 Yahoo 財經代碼:", key="ticker_input").strip().upper()
if st.sidebar.button("加入標的"):
    if new_ticker and new_ticker not in st.session_state.custom_tickers:
        st.session_state.custom_tickers.append(new_ticker)
        if new_ticker not in st.session_state.stock_pool: st.session_state.stock_pool.append(new_ticker)
        st.rerun()

if st.session_state.custom_tickers:
    st.sidebar.write("📌 目前觀察名單：")
    for ticker in st.session_state.custom_tickers:
        col1, col2 = st.sidebar.columns([3, 1])
        col1.markdown(f"**{ticker}**")
        if col2.button("刪除", key=f"del_{ticker}"):
            st.session_state.custom_tickers.remove(ticker)
            if ticker in st.session_state.stock_pool: st.session_state.stock_pool.remove(ticker)
            st.rerun()

# --- 核心資料模組 (YFinance) ---
@st.cache_data(ttl=300)
def fetch_data(indicators_dict):
    all_data, summary_list = {}, []
    for name, ticker in indicators_dict.items():
        try:
            df = yf.Ticker(ticker).history(period="3mo")
            if not df.empty:
                df['MA5'] = df['Close'].rolling(window=5).mean()
                df['MA10'] = df['Close'].rolling(window=10).mean()
                
                C, prev_C = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2])
                ma5, ma10 = float(df['MA5'].iloc[-1]), float(df['MA10'].iloc[-1])
                change_pct = ((C - prev_C) / prev_C) * 100
                
                trend_text, color_class, arrow = ("偏多", "trend-bullish", "🔼") if C > ma5 else ("偏空", "trend-bearish", "🔽") if C < ma5 else ("盤整", "trend-neutral", "➖")
                
                df = df.reset_index()
                all_data[name] = df
                summary_list.append({
                    "name": name, "current": C, "change_pct": change_pct,
                    "trend_text": trend_text, "color_class": color_class, "arrow": arrow,
                    "ma5": ma5, "ma10": ma10
                })
        except Exception: pass
    return summary_list, all_data

# --- 籌碼面：介接證交所 OpenAPI 抓取三大法人 ---
@st.cache_data(ttl=1800) # 30分鐘更新一次
def fetch_twse_institutional():
    try:
        url = "https://openapi.twse.com.tw/v1/fund/BFI82U"
        res = requests.get(url, timeout=5)
        data = res.json()
        
        inst_data = {"外資": 0.0, "投信": 0.0, "自營商": 0.0}
        for item in data:
            name = item.get("type", "")
            # 取得買賣超金額並轉換為「億」元
            net_val = float(item.get("buy_sell", "0").replace(",", "")) / 100000000
            
            if "外資及陸資" in name and "不含外資自營商" in name:
                inst_data["外資"] = net_val
            elif "投信" in name:
                inst_data["投信"] = net_val
            elif "自營商" in name:
                inst_data["自營商"] += net_val
                
        inst_data["合計"] = inst_data["外資"] + inst_data["投信"] + inst_data["自營商"]
        return inst_data
    except Exception as e:
        return None

# --- 動態實況評析生成引擎 ---
def generate_dynamic_analysis(summary, inst_data):
    def get_val(name, key, default=0): 
        return next((x[key] for x in summary if name in x['name']), default)
    
    # 提取實際數據
    taiex_c = get_val("加權指數", "current")
    taiex_trend = get_val("加權指數", "trend_text", "盤整")
    otc_trend = get_val("櫃買指數", "trend_text", "盤整")
    twd_c = get_val("美元/台幣", "current")
    twd_trend = get_val("美元/台幣", "trend_text", "盤整")
    sox_trend = get_val("費城半導體", "trend_text", "盤整")
    
    # 1. 構建大盤與資金動向
    analysis = f"📉 **大盤實況與內外資結構**：\n目前加權指數收在 **{taiex_c:,.0f} 點**，技術面呈現**{taiex_trend}**格局。與此同時，代表內資與中小型股的櫃買指數呈現**{otc_trend}**。"
    
    if taiex_trend == "偏多" and otc_trend == "偏多":
        analysis += " 數據顯示大型權值與中小型股步調一致，資金良性輪動，市場整體風險偏好強勁。\n\n"
    elif taiex_trend == "偏多" and otc_trend == "偏空":
        analysis += " 值得注意的是，大盤雖穩但櫃買走弱，顯示資金過度集中於少數大型權值股撐盤（拉積盤效應），中小型股實質面臨提款賣壓，操作難度增加。\n\n"
    elif taiex_trend == "偏空" and otc_trend == "偏空":
        analysis += " 顯示市場出現系統性修正壓力，內外資同步保守退場，建議嚴格控管資金水位。\n\n"
    else:
        analysis += " 市場板塊出現分歧，指數空間受限，資金傾向於特定題材各自表現。\n\n"

    # 2. 構建籌碼面數據分析
    if inst_data:
        total_net = inst_data['合計']
        analysis += f"📊 **三大法人實質籌碼**：\n根據證交所最新資料，三大法人整體呈現 **{'買超' if total_net > 0 else '賣超'} {abs(total_net):.1f} 億元**。"
        analysis += f" 其中，**外資{'買超' if inst_data['外資'] > 0 else '賣超'} {abs(inst_data['外局']):.1f} 億元**，"
        analysis += f"**投信{'買超' if inst_data['投信'] > 0 else '賣超'} {abs(inst_data['投信']):.1f} 億元**，"
        analysis += f"**自營商{'買超' if inst_data['自營商'] > 0 else '賣超'} {abs(inst_data['自營商']):.1f} 億元**。"
        
        if inst_data['外資'] > 0 and inst_data['投信'] > 0:
            analysis += " 土洋法人同步站在買方，為台股底氣提供實質的籌碼支撐。\n\n"
        elif inst_data['外資'] < 0 and inst_data['投信'] > 0:
            analysis += " 籌碼面呈現「外資提款、投信低接」的土洋對作態勢，後續大盤仍需等待外資賣壓宣洩完畢。\n\n"
        elif inst_data['外資'] < 0 and inst_data['投信'] < 0:
            analysis += " 需高度警惕！內外資同步大舉撤出，籌碼面極度弱勢，技術面隨時有跌破支撐的風險。\n\n"
        else:
            analysis += "\n\n"
    else:
        analysis += "📊 **籌碼面**：目前暫時無法取得今日證交所最新法人買賣超資料（可能為盤中或假日）。\n\n"

    # 3. 構建國際連動與匯率
    analysis += f"🌍 **國際連動與匯率熱錢**：\n匯市方面，目前美元兌台幣報 **{twd_c:.2f}**，趨勢**{twd_trend}**。"
    if twd_trend == "偏多":
        analysis += " 台幣技術面呈現貶值態勢（突破均線），這與外資熱錢匯出壓力相符，大型權值股較易受資金撤出影響。"
    else:
        analysis += " 台幣維持升值或強勢格局，有利於外資熱錢滯留台灣尋找投資標的。"
        
    analysis += f" 國際科技股部分，費城半導體指數目前呈現**{sox_trend}**，對高度依賴半導體出口的台股電子板塊產生直接的連動效應。"

    return analysis

# --- 繪圖與卡片渲染模組 ---
def plot_sparkline(df, color_class):
    line_color = '#FF4B4B' if color_class == 'trend-bullish' else '#00C853'
    if color_class == 'trend-neutral': line_color = '#777'
    plot_df = df.tail(30).copy()
    plot_df['DateStr'] = plot_df['Date'].dt.strftime('%m/%d')
    plot_df['Label'] = plot_df['Close'].round(2).astype(str) + " (" + plot_df['DateStr'] + ")"
    
    max_idx, min_idx = plot_df['Close'].idxmax(), plot_df['Close'].idxmin()
    base_line = alt.Chart(plot_df).mark_line(interpolate='basis', strokeWidth=3).encode(x=alt.X('Date:T', axis=None), y=alt.Y('Close:Q', scale=alt.Scale(zero=False), axis=None), color=alt.value(line_color))
    max_text = alt.Chart(plot_df.loc[[max_idx]]).mark_text(align='center', baseline='bottom', dy=-10, color='#555', fontSize=12, fontWeight='bold').encode(x='Date:T', y='Close:Q', text='Label')
    min_text = alt.Chart(plot_df.loc[[min_idx]]).mark_text(align='center', baseline='top', dy=10, color='#555', fontSize=12, fontWeight='bold').encode(x='Date:T', y='Close:Q', text='Label')
    return alt.layer(base_line, max_text, min_text).properties(height=100).configure_view(strokeWidth=0)

def render_cards(summary, history):
    for item in summary:
        precision = ".0f" if "加權" in item['name'] or "櫃買" in item['name'] or "費城" in item['name'] else ".2f"
        if "DXY" in item['name'] or "VIX" in item['name']: precision = ".1f"
        st.markdown(f"""
        <div class="indicator-card">
            <div class="card-title">{item['name']}</div>
            <div style="display: flex; align-items: baseline; flex-wrap: wrap;">
                <span class="current-value {item['color_class']}">{item['current']:{precision}}</span>
                <span class="{item['color_class']}" style="font-size: 1.2rem; font-weight: bold; margin-right: 15px;">{item['arrow']} {item['change_pct']:.2f}% (日)</span>
                <span class="ma-text">短線趨勢：<span class="{item['color_class']}" style="font-weight:bold;">{item['trend_text']}</span></span>
            </div>
            <div class="ma-text" style="margin-top: 5px;">5MA: {item['ma5']:{precision}} ｜ 10MA: {item['ma10']:{precision}}</div>
        </div>
        """, unsafe_allow_html=True)
        st.altair_chart(plot_sparkline(history[item['name']], item['color_class']), use_container_width=True)

# ==========================================
# 網頁主內容區塊
# ==========================================
if page == "🇹🇼 台灣市場 (台股)":
    st.title("🇹🇼 台股核心實況儀表板")
    st.markdown("---")
    
    tw_indicators = {"加權指數 (TAIEX)": "^TWII", "櫃買指數 (OTC)": "^TWOII", "台積電 (2330)": "2330.TW", "美元/台幣 (匯率)": "TWD=X", "費城半導體 (SOX)": "^SOX"}
    summary, history = fetch_data(tw_indicators)
    inst_data = fetch_twse_institutional()
    
    if summary:
        st.subheader("🧠 實況數據動態評析")
        dynamic_text = generate_dynamic_analysis(summary, inst_data)
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #4a90e2; margin-bottom: 30px;'>{dynamic_text}</div>", unsafe_allow_html=True)
        
        st.subheader("📊 核心指標監控")
        render_cards(summary, history)

elif page == "🌐 全球市場 (總經)":
    st.title("🌐 全球市場儀表板")
    st.markdown("---")
    global_indicators = {"VIX (恐慌指數)": "^VIX", "DXY (美元指數)": "DX-Y.NYB", "Crude Oil (原油)": "CL=F", "Gold (黃金)": "GC=F", "10Y Yield (殖利率)": "^TNX"}
    summary, history = fetch_data(global_indicators)
    if summary: render_cards(summary, history)

elif page == "📂 產業股票池":
    st.title("📂 台股核心產業分類清單")
    st.markdown("---")
    for industry_name, stocks in INDUSTRY_STOCKS.items():
        with st.expander(f"{industry_name} ({len(stocks)} 檔)"):
            st.write("包含標的：", ", ".join(stocks))
            if st.button(f"將 {industry_name} 匯入篩選器", key=f"add_{industry_name}"):
                for s in stocks:
                    if s not in st.session_state.stock_pool: st.session_state.stock_pool.append(s)
                st.success("匯入成功！請前往「潛力股自動篩選」執行策略。")

elif page == "🔍 潛力股自動篩選":
    st.title("🔍 多維度技術面篩選機")
    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        timeframe = st.selectbox("選擇 K線週期：", ["日 K線 (短線)", "週 K線 (中線)", "月 K線 (長線)"])
        period, interval = ("6mo", "1d") if "日" in timeframe else ("2y", "1wk") if "週" in timeframe else ("5y", "1mo")
    with col2:
        pool_input = st.text_area("當前篩選股票池：", value=", ".join(st.session_state.stock_pool))
        current_pool = [x.strip().upper() for x in pool_input.split(",") if x.strip()]

    if st.button("🗑️ 清空清單"): st.session_state.stock_pool = []; st.rerun()

    if st.button("🚀 啟動演算法篩選", use_container_width=True):
        if not current_pool: st.warning("股票池為空，請輸入代碼或由產業池匯入。")
        else:
            st.markdown("### 📊 篩選結果")
            results = {"ma_breakout": [], "vol_up": [], "hammer": []}
            bar = st.progress(0)
            
            for idx, ticker in enumerate(current_pool):
                try:
                    df = yf.Ticker(ticker).history(period=period, interval=interval)
                    if len(df) >= 20:
                        df['MA5'], df['MA10'], df['MA20'] = df['Close'].rolling(5).mean(), df['Close'].rolling(10).mean(), df['Close'].rolling(20).mean()
                        curr, prev = df.iloc[-1], df.iloc[-2]
                        C, O, H, L, V, prev_V = curr['Close'], curr['Open'], curr['High'], curr['Low'], curr['Volume'], prev['Volume']
                        ma5, ma10, ma20 = curr['MA5'], curr['MA10'], curr['MA20']
                        
                        # 策略判斷
                        if (C > O) and ((min(O, C) - L) > abs(C - O)*2) and ((H - max(O, C)) < abs(C - O)*0.5): results["hammer"].append(f"**{ticker}** ({C:.2f})")
                        if (C > prev['Close']) and (V > prev_V * 1.5): results["vol_up"].append(f"**{ticker}** ({C:.2f})")
                        
                        max_ma, min_ma = max(ma5, ma10, ma20), min(ma5, ma10, ma20)
                        if (((max_ma - min_ma) / min_ma) < 0.03) and (C > max_ma) and (prev['Close'] < max_ma): results["ma_breakout"].append(f"**{ticker}** ({C:.2f})")
                except: pass
                bar.progress((idx + 1) / len(current_pool))
                
            st.markdown("#### 🔥 均線糾結且向上突破 (起漲爆發)")
            [st.error(f"🚀 {s}") for s in results["ma_breakout"]] if results["ma_breakout"] else st.write("無符合標的。")
            st.markdown("#### 📈 價漲量增 (資金湧入)")
            [st.success(s) for s in results["vol_up"]] if results["vol_up"] else st.write("無符合標的。")
            st.markdown("#### 🔨 陽線錘子 (底部支撐)")
            [st.warning(s) for s in results["hammer"]] if results["hammer"] else st.write("無符合標的。")

st.markdown("---")
st.caption("免責聲明：籌碼資料來源為證交所 Open API，報價由 Yahoo Finance 提供。所有動態生成之評析與篩選結果僅為數據客觀呈現，不構成任何投資建議。")
