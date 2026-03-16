import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import datetime
import requests
import urllib3

# 關閉不安全的 SSL 憑證警告 (避免政府網站與API連線報錯)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 網頁設定 ---
st.set_page_config(page_title="專業市場儀表板", layout="wide", initial_sidebar_state="expanded")

# --- 擴充版：台股產業分類字典 (加入中文名稱) ---
INDUSTRY_STOCKS = {
    "🛠️ 半導體業 (晶圓/IC/封測)": ["2330.TW 台積電", "2454.TW 聯發科", "2303.TW 聯電", "3711.TW 日月光投控", "2379.TW 瑞昱", "2408.TW 南亞科", "3443.TW 創意", "3034.TW 聯詠", "4966.TW 譜瑞-KY", "6415.TW 矽力*-KY"],
    "💻 電腦及週邊設備 (AI伺服器/PC)": ["2382.TW 廣達", "3231.TW 緯創", "2356.TW 英業達", "2324.TW 仁寶", "2376.TW 技嘉", "2395.TW 研華", "6669.TW 緯穎", "2353.TW 宏碁", "2357.TW 華碩", "3005.TW 神基"],
    "🏦 金融保險業 (金控/銀行)": ["2881.TW 富邦金", "2882.TW 國泰金", "2891.TW 中信金", "2886.TW 兆豐金", "2884.TW 玉山金", "2892.TW 第一金", "2885.TW 元大金", "2880.TW 華南金", "2890.TW 永豐金", "2883.TW 開發金"],
    "🚢 航運業 (貨櫃/散裝/航空)": ["2603.TW 長榮", "2609.TW 陽明", "2615.TW 萬海", "2618.TW 長榮航", "2610.TW 華航", "2606.TW 裕民", "2637.TW 慧洋-KY", "2605.TW 新興", "2612.TW 中航"],
    "🔌 電子零組件業 (被動/PCB/散熱)": ["2308.TW 台達電", "2327.TW 國巨", "3037.TW 欣興", "2313.TW 華通", "3044.TW 健鼎", "2368.TW 金像電", "3017.TW 奇鋐", "3324.TW 雙鴻", "2383.TW 台光電"],
    "📡 通信網路業 (電信/網通)": ["2412.TW 中華電", "3045.TW 台灣大", "4904.TW 遠傳", "2345.TW 智邦", "3596.TW 智易", "5388.TW 中磊", "6285.TW 啟碁", "3704.TW 合勤控"],
    "💡 光電業 (面板/鏡頭)": ["3008.TW 大立光", "3406.TW 玉晶光", "2409.TW 友達", "3481.TW 群創", "6116.TW 彩晶", "2448.TW 晶電", "6209.TW 今國光", "3141.TW 晶宏"],
    "⚙️ 電機機械業 (重電/工具機)": ["1504.TW 東元", "1519.TW 華城", "1590.TW 亞德客-KY", "1513.TW 中興電", "1514.TW 亞力", "1503.TW 士電", "1515.TW 力山", "1522.TW 堤維西"]
}

# --- 初始化暫存狀態 ---
if 'custom_tickers' not in st.session_state: st.session_state.custom_tickers = []
if 'stock_pool' not in st.session_state: st.session_state.stock_pool = ["2330.TW 台積電", "2317.TW 鴻海", "2454.TW 聯發科", "2881.TW 富邦金", "2603.TW 長榮"]

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
new_ticker = st.sidebar.text_input("輸入代碼 (例：2317.TW 鴻海):", key="ticker_input").strip().upper()
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

# --- 資料抓取與 API 模組 ---
@st.cache_data(ttl=86400) # 快取一天
def fetch_all_twse_tickers():
    """改用開源金融 API (FinMind) 獲取台股代碼與名稱，避開證交所防火牆"""
    try:
        url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo"
        res = requests.get(url, timeout=10, verify=False)
        if res.status_code == 200:
            data = res.json()
            # 組合出 "代碼.TW 名稱" 的格式
            tickers = [
                f"{item['stock_id']}.TW {item.get('stock_name', '')}".strip()
                for item in data.get('data', []) 
                if item.get('type') == 'twse' and len(item.get('stock_id', '')) == 4 and item['stock_id'].isdigit()
            ]
            if tickers:
                return list(set(tickers))
    except Exception as e:
        st.error(f"全市場 API 連線異常：{e}")
    return []

@st.cache_data(ttl=300)
def fetch_data(indicators_dict):
    all_data, summary_list = {}, []
    for name, ticker_display in indicators_dict.items():
        try:
            # 智慧拆解：如果傳入的是 "2330.TW 台積電"，只取前面的 "2330.TW" 丟給 Yahoo Finance
            yf_ticker = ticker_display.split()[0]
            df = yf.Ticker(yf_ticker).history(period="3mo")
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

@st.cache_data(ttl=1800) # 30分鐘更新一次
def fetch_twse_institutional():
    """抓取證交所三大法人買賣超金額 (加上 verify=False 放行 SSL)"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        url = "https://openapi.twse.com.tw/v1/fund/BFI82U"
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
    except Exception:
        return None

# --- 動態實況評析生成引擎 ---
def generate_dynamic_analysis(summary, inst_data):
    def get_val(name, key, default=0): 
        return next((x[key] for x in summary if name in x['name']), default)
    
    taiex_c = get_val("加權指數", "current")
    taiex_trend = get_val("加權指數", "trend_text", "盤整")
    otc_trend = get_val("櫃買指數", "trend_text", "盤整")
    twd_c = get_val("美元/台幣", "current")
    twd_trend = get_val("美元/台幣", "trend_text", "盤整")
    sox_trend = get_val("費城半導體", "trend_text", "盤整")
    
    analysis = f"📉 **大盤實況與內外資結構**：\n目前加權指數收在 **{taiex_c:,.0f} 點**，短線呈現**{taiex_trend}**格局。代表內資與中小型股的櫃買指數呈現**{otc_trend}**。"
    
    if taiex_trend == "偏多" and otc_trend == "偏多":
        analysis += " 顯示大型權值與中小型股步調一致，資金良性輪動，市場整體風險偏好強勁。\n\n"
    elif taiex_trend == "偏多" and otc_trend == "偏空":
        analysis += " 大盤雖穩但櫃買走弱，顯示資金過度集中於少數大型權值股撐盤（拉積盤效應），中小型股面臨提款賣壓，個股操作難度高。\n\n"
    elif taiex_trend == "偏空" and otc_trend == "偏空":
        analysis += " 市場出現系統性修正壓力，內外資同步保守退場，建議嚴格控管資金水位。\n\n"
    else:
        analysis += " 市場板塊出現分歧，資金傾向於特定題材各自表現。\n\n"

    if inst_data:
        total_net = inst_data['合計']
        analysis += f"📊 **三大法人實質籌碼**：\n根據證交所最新資料，三大法人整體呈現 **{'買超' if total_net > 0 else '賣超'} {abs(total_net):.1f} 億元**。"
        analysis += f" 其中，外資**{'買超' if inst_data['外資'] > 0 else '賣超'} {abs(inst_data['外資']):.1f} 億元**，"
        analysis += f"投信**{'買超' if inst_data['投信'] > 0 else '賣超'} {abs(inst_data['投信']):.1f} 億元**，"
        analysis += f"自營商**{'買超' if inst_data['自營商'] > 0 else '賣超'} {abs(inst_data['自營商']):.1f} 億元**。"
        
        if inst_data['外資'] > 0 and inst_data['投信'] > 0:
            analysis += " 土洋法人同步站在買方，為台股底氣提供實質的籌碼支撐。\n\n"
        elif inst_data['外資'] < 0 and inst_data['投信'] > 0:
            analysis += " 籌碼面呈現「外資提款、投信低接」的土洋對作態勢，需等待外資賣壓宣洩完畢。\n\n"
        elif inst_data['外資'] < 0 and inst_data['投信'] < 0:
            analysis += " 需高度警惕！內外資同步大舉撤出，籌碼面極度弱勢，隨時有跌破支撐的風險。\n\n"
        else:
            analysis += "\n\n"
    else:
        analysis += "📊 **籌碼面**：目前暫無今日證交所最新法人買賣超資料（可能為盤中或假日）。\n\n"

    analysis += f"🌍 **國際連動與匯率熱錢**：\n匯市方面，目前美元兌台幣報 **{twd_c:.2f}**，趨勢**{twd_trend}**。"
    if twd_trend == "偏多":
        analysis += " 台幣呈現貶值態勢（突破均線），這與外資熱錢匯出壓力相符，大型權值股易受提款影響。"
    else:
        analysis += " 台幣維持升值或強勢格局，資金動能充沛，有利於推升指數。"
        
    analysis += f" 費城半導體指數呈現**{sox_trend}**，對台股電子板塊產生直接連動效應。"

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
    
    # 台股總經預設觀察標的
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
    st.title("📂 擴充版：台股核心產業分類清單")
    st.markdown("整理各大產業規模最大、最具代表性的中大型股。附有中文名稱，板塊輪動一目了然！")
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
    
    st.info("💡 **進階功能**：一鍵連線 FinMind 抓取全市場上市股票 (包含中文名稱)。")
    if st.button("📥 一鍵載入「全市場台股 (約1000檔)」", type="primary"):
        with st.spinner("正在連線 FinMind API 獲取全市場代碼與名稱..."):
            all_tickers = fetch_all_twse_tickers()
            if all_tickers:
                st.session_state.stock_pool = list(set(st.session_state.stock_pool + all_tickers))
                st.success(f"✅ 成功載入上市股票！目前篩選池共有 {len(st.session_state.stock_pool)} 檔標的。")
            else:
                st.error("❌ 無法連線至 API，請稍後再試。")

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
                st.warning(f"⚠️ 系統即將掃描 {len(current_pool)} 檔股票。預計需要數分鐘，請耐心等候進度條跑完。")
            
            st.markdown("### 📊 篩選結果報告")
            results = {"ma_breakout": [], "vol_up": [], "hammer": []}
            bar = st.progress(0)
            status_text = st.empty()
            
            for idx, ticker_display in enumerate(current_pool):
                status_text.text(f"正在掃描 {ticker_display} ... ({idx+1}/{len(current_pool)})")
                try:
                    # 智慧拆解：將 "2330.TW 台積電" 拆成 "2330.TW" 丟給 yfinance
                    yf_ticker = ticker_display.split()[0]
                    df = yf.Ticker(yf_ticker).history(period=period, interval=interval)
                    
                    if len(df) >= 20:
                        df['MA5'], df['MA10'], df['MA20'] = df['Close'].rolling(5).mean(), df['Close'].rolling(10).mean(), df['Close'].rolling(20).mean()
                        curr, prev = df.iloc[-1], df.iloc[-2]
                        C, O, H, L, V, prev_V = curr['Close'], curr['Open'], curr['High'], curr['Low'], curr['Volume'], prev['Volume']
                        ma5, ma10, ma20 = curr['MA5'], curr['MA10'], curr['MA20']
                        
                        # 策略判斷 (加入中文名稱顯示)
                        if (C > O) and ((min(O, C) - L) > abs(C - O)*2) and ((H - max(O, C)) < abs(C - O)*0.5): 
                            results["hammer"].append(f"**{ticker_display}** (現價: {C:.2f})")
                        if (C > prev['Close']) and (V > prev_V * 1.5): 
                            results["vol_up"].append(f"**{ticker_display}** (現價: {C:.2f})")
                        
                        max_ma, min_ma = max(ma5, ma10, ma20), min(ma5, ma10, ma20)
                        if (((max_ma - min_ma) / min_ma) < 0.03) and (C > max_ma) and (prev['Close'] < max_ma): 
                            results["ma_breakout"].append(f"**{ticker_display}** (現價: {C:.2f})")
                except: pass
                bar.progress((idx + 1) / len(current_pool))
                
            status_text.text("✅ 全面掃描完成！")

            # 顯示結果 (使用傳統迴圈，避免 Streamlit DeltaGenerator 印出火星文)
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
    # 將名單打包成 {顯示名稱: 顯示名稱} 的格式
    custom_dict = {ticker: ticker for ticker in st.session_state.custom_tickers}
    c_summary, c_history = fetch_data(custom_dict)
    if c_summary: render_cards(c_summary, c_history)

st.markdown("---")
st.caption(f"數據最後更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("免責聲明：技術分析訊號僅供參考，不構成投資建議。全市場資料來源為 FinMind API，三大法人來自證交所，報價由 Yahoo Finance 提供。")
