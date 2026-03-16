import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import datetime
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 網頁設定 ---
st.set_page_config(page_title="專業市場儀表板", layout="wide", initial_sidebar_state="expanded")

# --- 擴充版：台股產業分類字典 (大幅增加規模標的) ---
INDUSTRY_STOCKS = {
    "🛠️ 半導體業 (晶圓/IC/封測)": ["2330.TW", "2454.TW", "2303.TW", "3711.TW", "2379.TW", "2408.TW", "3443.TW", "3034.TW", "4966.TW", "6415.TW", "3529.TW", "8299.TW", "6770.TW", "6488.TW", "2338.TW", "2344.TW", "2449.TW", "3014.TW", "6239.TW", "3189.TW", "2401.TW", "3532.TW", "6531.TW", "4919.TW", "3006.TW"],
    "💻 電腦及週邊設備 (AI伺服器/PC)": ["2382.TW", "3231.TW", "2356.TW", "2324.TW", "2376.TW", "2395.TW", "6669.TW", "2353.TW", "2357.TW", "3005.TW", "2362.TW", "3013.TW", "4938.TW", "6206.TW", "3017.TW", "6166.TW", "2377.TW", "6515.TW", "5269.TW", "2301.TW"],
    "🏦 金融保險業 (金控/銀行)": ["2881.TW", "2882.TW", "2891.TW", "2886.TW", "2884.TW", "2892.TW", "2885.TW", "2880.TW", "2890.TW", "2883.TW", "2887.TW", "2801.TW", "2834.TW", "2838.TW", "2845.TW", "2850.TW", "2851.TW", "2852.TW", "2809.TW", "5880.TW", "5876.TW", "6005.TW"],
    "🚢 航運業 (貨櫃/散裝/航空)": ["2603.TW", "2609.TW", "2615.TW", "2618.TW", "2610.TW", "2606.TW", "2637.TW", "2605.TW", "2612.TW", "2613.TW", "2617.TW", "2601.TW", "2611.TW", "5608.TW", "2607.TW", "2634.TW", "2614.TW", "2633.TW"],
    "🔌 電子零組件業 (被動/PCB/散熱)": ["2308.TW", "2327.TW", "3037.TW", "2313.TW", "3044.TW", "2368.TW", "3017.TW", "2492.TW", "2383.TW", "6269.TW", "3346.TW", "2421.TW", "6274.TW", "2375.TW", "2428.TW", "2355.TW", "3042.TW", "6197.TW", "3026.TW", "3217.TW"],
    "📡 通信網路業 (電信/網通)": ["2412.TW", "3045.TW", "4904.TW", "2345.TW", "3596.TW", "5388.TW", "3380.TW", "6285.TW", "3704.TW", "2419.TW", "2485.TW", "2450.TW", "3062.TW", "2314.TW", "2444.TW", "2498.TW", "3149.TW"],
    "💡 光電業 (面板/鏡頭)": ["3008.TW", "3406.TW", "2409.TW", "3481.TW", "6116.TW", "2448.TW", "6209.TW", "2340.TW", "4960.TW", "3141.TW", "2426.TW", "6120.TW", "3622.TW", "3019.TW", "2393.TW", "3576.TW", "6456.TW", "6443.TW", "2323.TW"],
    "⚙️ 電機機械業 (重電/工具機)": ["1504.TW", "1519.TW", "1590.TW", "1513.TW", "1514.TW", "1503.TW", "1515.TW", "1522.TW", "1532.TW", "1521.TW", "1525.TW", "1537.TW", "1536.TW", "1589.TW", "1524.TW", "4532.TW", "4571.TW", "8996.TW", "4583.TW"]
}

# --- 初始化暫存狀態 ---
if 'custom_tickers' not in st.session_state: st.session_state.custom_tickers = []
if 'stock_pool' not in st.session_state: st.session_state.stock_pool = ["2330.TW", "2317.TW", "2454.TW", "2881.TW", "2603.TW"]

# --- 側邊欄與選單 ---
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
    st.sidebar.write("📌 目前名單：")
    for ticker in st.session_state.custom_tickers:
        c1, c2 = st.sidebar.columns([3, 1])
        c1.markdown(f"**{ticker}**")
        if c2.button("刪除", key=f"del_{ticker}"):
            st.session_state.custom_tickers.remove(ticker)
            if ticker in st.session_state.stock_pool: st.session_state.stock_pool.remove(ticker)
            st.rerun()

# --- 資料抓取與API模組 ---
@st.cache_data(ttl=86400) # 快取一天
def fetch_all_twse_tickers():
    """介接證交所 OpenAPI，取得所有上市股票代碼"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
        
        # 💡 終極秘訣：加入 verify=False 強制略過龜毛的 SSL 驗證
        res = requests.get(url, headers=headers, timeout=10, verify=False)
        res.raise_for_status() 
        data = res.json()
        
        tickers = [f"{item['Code']}.TW" for item in data if len(item['Code']) == 4 and item['Code'].isdigit()]
        return tickers
    except Exception as e:
        st.error(f"連線失敗，詳細錯誤原因：{e}") 
        return []

@st.cache_data(ttl=1800) # 30分鐘更新一次
def fetch_twse_institutional():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        url = "https://openapi.twse.com.tw/v1/fund/BFI82U"
        
        # 💡 籌碼面同樣加入 verify=False
        res = requests.get(url, headers=headers, timeout=5, verify=False)
        data = res.json()
        
        inst_data = {"外資": 0.0, "投信": 0.0, "自營商": 0.0}
        for item in data:
            name = item.get("type", "")
            net_val = float(item.get("buy_sell", "0").replace(",", "")) / 100000000
            
            if "外資及陸資" in name and "不含外資自營商" in name: inst_data["外資"] = net_val
            elif "投信" in name: inst_data["投信"] = net_val
            elif "自營商" in name: inst_data["自營商"] += net_val
                
        inst_data["合計"] = inst_data["外資"] + inst_data["投信"] + inst_data["自營商"]
        return inst_data
    except Exception as e:
        return None

@st.cache_data(ttl=1800) # 30分鐘更新一次
def fetch_twse_institutional():
    try:
        # 籌碼面同樣加上 Headers 偽裝
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        url = "https://openapi.twse.com.tw/v1/fund/BFI82U"
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        
        inst_data = {"外資": 0.0, "投信": 0.0, "自營商": 0.0}
        for item in data:
            name = item.get("type", "")
            net_val = float(item.get("buy_sell", "0").replace(",", "")) / 100000000
            
            if "外資及陸資" in name and "不含外資自營商" in name: inst_data["外資"] = net_val
            elif "投信" in name: inst_data["投信"] = net_val
            elif "自營商" in name: inst_data["自營商"] += net_val
                
        inst_data["合計"] = inst_data["外資"] + inst_data["投信"] + inst_data["自營商"]
        return inst_data
    except Exception as e:
        return None

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
    st.markdown("""<style>.indicator-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #ddd; } .card-title { font-size: 1.3rem; color: #555; font-weight: bold; margin-bottom: 10px; } .current-value { font-size: 3rem !important; font-weight: bold; margin-right: 10px; } .trend-bullish { color: #FF4B4B !important; } .trend-bearish { color: #00C853 !important; } .trend-neutral { color: #777 !important; }</style>""", unsafe_allow_html=True)
    for item in summary:
        precision = ".0f" if "加權" in item['name'] or "櫃買" in item['name'] or "費城" in item['name'] else ".2f"
        if "DXY" in item['name'] or "VIX" in item['name']: precision = ".1f"
        st.markdown(f"""
        <div class="indicator-card">
            <div class="card-title">{item['name']}</div>
            <div style="display: flex; align-items: baseline; flex-wrap: wrap;">
                <span class="current-value {item['color_class']}">{item['current']:{precision}}</span>
                <span class="{item['color_class']}" style="font-size: 1.2rem; font-weight: bold; margin-right: 15px;">{item['arrow']} {item['change_pct']:.2f}% (日)</span>
            </div>
            <div style="margin-top: 5px; color: #666;">5MA: {item['ma5']:{precision}} ｜ 10MA: {item['ma10']:{precision}}</div>
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
    if summary: render_cards(summary, history)

elif page == "🌐 全球市場 (總經)":
    st.title("🌐 全球市場儀表板")
    st.markdown("---")
    global_indicators = {"VIX (恐慌指數)": "^VIX", "DXY (美元指數)": "DX-Y.NYB", "Crude Oil (原油)": "CL=F", "Gold (黃金)": "GC=F", "10Y Yield (殖利率)": "^TNX"}
    summary, history = fetch_data(global_indicators)
    if summary: render_cards(summary, history)

elif page == "📂 產業股票池":
    st.title("📂 擴充版：台股核心產業分類清單")
    st.markdown("這裡整理了各大產業**規模最大、最具代表性的數十檔中大型股**。")
    st.markdown("---")
    for industry_name, stocks in INDUSTRY_STOCKS.items():
        with st.expander(f"{industry_name} ({len(stocks)} 檔)"):
            st.write("包含標的：", ", ".join(stocks))
            if st.button(f"將 {industry_name} 匯入篩選器", key=f"add_{industry_name}"):
                for s in stocks:
                    if s not in st.session_state.stock_pool: st.session_state.stock_pool.append(s)
                st.success("匯入成功！請前往「潛力股自動篩選」執行策略。")

elif page == "🔍 潛力股自動篩選":
    st.title("🔍 多維度技術面篩選機 (支援全市場)")
    st.markdown("---")
    
    # 全市場載入按鈕區塊
    st.info("💡 **進階功能**：您可以一鍵載入證交所最新公佈的所有上市股票代碼進行全市場大掃描。")
    if st.button("📥 一鍵載入「全市場台股 (約1000檔)」", type="primary"):
        with st.spinner("正在連線證交所 OpenAPI 獲取全市場代碼..."):
            all_tickers = fetch_all_twse_tickers()
            if all_tickers:
                # 合併且不重複
                st.session_state.stock_pool = list(set(st.session_state.stock_pool + all_tickers))
                st.success(f"✅ 成功載入 {len(all_tickers)} 檔上市股票！目前篩選池共有 {len(st.session_state.stock_pool)} 檔標的。")
            else:
                st.error("❌ 無法連線至證交所 API，請稍後再試。")

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
            if len(current_pool) > 100:
                st.warning(f"⚠️ 系統提示：您即將掃描 {len(current_pool)} 檔股票。因資料龐大，預計需要數分鐘至十幾分鐘不等，請耐心等候進度條跑完，切勿關閉視窗。")
            
            st.markdown("### 📊 篩選結果報告")
            results = {"ma_breakout": [], "vol_up": [], "hammer": []}
            bar = st.progress(0)
            status_text = st.empty()
            
            for idx, ticker in enumerate(current_pool):
                status_text.text(f"正在掃描 {ticker} ... ({idx+1}/{len(current_pool)})")
                try:
                    df = yf.Ticker(ticker).history(period=period, interval=interval)
                    if len(df) >= 20:
                        df['MA5'], df['MA10'], df['MA20'] = df['Close'].rolling(5).mean(), df['Close'].rolling(10).mean(), df['Close'].rolling(20).mean()
                        curr, prev = df.iloc[-1], df.iloc[-2]
                        C, O, H, L, V, prev_V = curr['Close'], curr['Open'], curr['High'], curr['Low'], curr['Volume'], prev['Volume']
                        ma5, ma10, ma20 = curr['MA5'], curr['MA10'], curr['MA20']
                        
                        # 策略判斷
                        if (C > O) and ((min(O, C) - L) > abs(C - O)*2) and ((H - max(O, C)) < abs(C - O)*0.5): 
                            results["hammer"].append(f"**{ticker}** ({C:.2f})")
                        if (C > prev['Close']) and (V > prev_V * 1.5): 
                            results["vol_up"].append(f"**{ticker}** ({C:.2f})")
                        
                        max_ma, min_ma = max(ma5, ma10, ma20), min(ma5, ma10, ma20)
                        if (((max_ma - min_ma) / min_ma) < 0.03) and (C > max_ma) and (prev['Close'] < max_ma): 
                            results["ma_breakout"].append(f"**{ticker}** ({C:.2f})")
                except: pass
                bar.progress((idx + 1) / len(current_pool))
                
            status_text.text("✅ 全面掃描完成！")

            # 修正渲染顯示，避免出現 DeltaGenerator 火星文
            st.markdown("#### 🔥 均線糾結且向上突破 (起漲爆發)")
            if results["ma_breakout"]:
                for s in results["ma_breakout"]: st.error(f"🚀 {s}")
            else:
                st.write("無符合標的。")
                
            st.markdown("#### 📈 價漲量增 (資金湧入)")
            if results["vol_up"]:
                for s in results["vol_up"]: st.success(s)
            else:
                st.write("無符合標的。")
                
            st.markdown("#### 🔨 陽線錘子 (底部支撐)")
            if results["hammer"]:
                for s in results["hammer"]: st.warning(s)
            else:
                st.write("無符合標的。")

# ==========================================
# 底部共用區塊
# ==========================================
if page in ["🇹🇼 台灣市場 (台股)", "🌐 全球市場 (總經)"] and st.session_state.custom_tickers:
    st.markdown("---")
    st.subheader("🎯 自訂觀察名單")
    custom_dict = {ticker: ticker for ticker in st.session_state.custom_tickers}
    c_summary, c_history = fetch_data(custom_dict)
    if c_summary: render_cards(c_summary, c_history)

st.markdown("---")
st.caption(f"數據最後更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("免責聲明：技術分析訊號僅供參考，不構成任何投資建議。全市場資料來源為證交所 Open API，報價由 Yahoo Finance 提供。")
