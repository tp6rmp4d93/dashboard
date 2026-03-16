import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import datetime
import requests
import urllib3
import concurrent.futures

# 關閉不安全的 SSL 憑證警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 網頁設定 ---
st.set_page_config(page_title="專業市場儀表板", layout="wide", initial_sidebar_state="expanded")

# --- 🚀 台股八大產業分類字典 (各約 40~50 檔指標股) ---
INDUSTRY_STOCKS = {
    "🛠️ 半導體業": ["2330.TW 台積電", "2454.TW 聯發科", "2303.TW 聯電", "3711.TW 日月光投控", "2379.TW 瑞昱", "2408.TW 南亞科", "3443.TW 創意", "3034.TW 聯詠", "4966.TW 譜瑞-KY", "6415.TW 矽力*-KY", "3529.TW 力旺", "8299.TW 群聯", "6770.TW 力積電", "6488.TW 環球晶", "2338.TW 光罩", "2344.TW 華邦電", "2449.TW 京元電子", "3014.TW 聯陽", "6239.TW 力成", "3189.TW 景碩", "2401.TW 凌陽", "3532.TW 台勝科", "6531.TW 愛普*", "4919.TW 新唐", "3006.TW 晶豪科", "5347.TW 世界", "6147.TW 頎邦", "8016.TW 矽創", "8081.TW 致新", "3260.TW 威剛", "6202.TW 盛群", "3588.TW 通嘉", "2436.TW 偉詮電", "3661.TW 世芯-KY", "6643.TW M31", "8150.TW 南茂", "3141.TW 晶宏", "3583.TW 辛耘", "5269.TW 祥碩", "2458.TW 義隆", "3016.TW 嘉晶", "6138.TW 茂達", "3227.TW 原相", "2481.TW 強茂", "3374.TW 精材", "3035.TW 智原"],
    "💻 電腦及週邊": ["2382.TW 廣達", "3231.TW 緯創", "2356.TW 英業達", "2324.TW 仁寶", "2376.TW 技嘉", "2395.TW 研華", "6669.TW 緯穎", "2353.TW 宏碁", "2357.TW 華碩", "3005.TW 神基", "2362.TW 藍天", "3013.TW 晟銘電", "4938.TW 和碩", "6206.TW 飛捷", "3017.TW 奇鋐", "6166.TW 凌華", "2377.TW 微星", "6515.TW 穎崴", "2301.TW 光寶科", "2397.TW 友通", "3022.TW 威強電", "6117.TW 迎廣", "3046.TW 建碁", "2399.TW 映泰", "2371.TW 大同", "3050.TW 鈺德", "3211.TW 順達", "3515.TW 華擎", "6277.TW 宏正", "6412.TW 群電", "6414.TW 樺漢", "6579.TW 研揚", "8112.TW 至上", "8210.TW 勤誠", "4915.TW 致伸", "3706.TW 神達", "3483.TW 力致", "3413.TW 京鼎", "3058.TW 立德", "2425.TW 承啟", "2387.TW 精元"],
    "🏦 金融保險業": ["2881.TW 富邦金", "2882.TW 國泰金", "2891.TW 中信金", "2886.TW 兆豐金", "2884.TW 玉山金", "2892.TW 第一金", "2885.TW 元大金", "2880.TW 華南金", "2890.TW 永豐金", "2883.TW 開發金", "2887.TW 台新金", "2801.TW 彰銀", "2834.TW 臺企銀", "2838.TW 聯邦銀", "2845.TW 遠東銀", "2850.TW 新產", "2851.TW 中再保", "2852.TW 第一保", "2809.TW 京城銀", "5880.TW 合庫金", "5876.TW 上海商銀", "6005.TW 群益證", "2812.TW 台中銀", "2820.TW 華票", "2832.TW 台產", "2888.TW 新光金", "2889.TW 國票金", "2897.TW 王道銀行", "6016.TW 康和證", "6024.TW 群益期", "2855.TW 統一證", "6023.TW 元大期", "5871.TW 中租-KY"],
    "🚢 航運業": ["2603.TW 長榮", "2609.TW 陽明", "2615.TW 萬海", "2618.TW 長榮航", "2610.TW 華航", "2606.TW 裕民", "2637.TW 慧洋-KY", "2605.TW 新興", "2612.TW 中航", "2613.TW 中櫃", "2617.TW 台航", "2601.TW 益航", "2611.TW 志信", "5608.TW 四維航", "2607.TW 榮運", "2634.TW 漢翔", "2614.TW 東森", "2633.TW 台灣高鐵", "2642.TW 宅配通", "2646.TW 星宇航空", "2616.TW 山隆", "2208.TW 台船", "2636.TW 台驊投控", "5609.TW 中菲行", "5607.TW 遠雄港", "2641.TW 正德", "2643.TW 捷迅", "2630.TW 亞航"],
    "🔌 電子零組件": ["2308.TW 台達電", "2327.TW 國巨", "3037.TW 欣興", "2313.TW 華通", "3044.TW 健鼎", "2368.TW 金像電", "3324.TW 雙鴻", "2383.TW 台光電", "2492.TW 華新科", "6269.TW 台郡", "3346.TW 麗清", "2421.TW 建準", "6274.TW 台燿", "2375.TW 智寶", "2428.TW 興勤", "2355.TW 敬鵬", "3042.TW 晶技", "6197.TW 佳必琪", "3026.TW 禾伸堂", "3217.TW 優群", "2316.TW 楠梓電", "2351.TW 順德", "2367.TW 燿華", "2385.TW 群光", "2420.TW 新巨", "2439.TW 美律", "2457.TW 飛宏", "2472.TW 立隆電", "2478.TW 大毅", "2484.TW 希華", "3003.TW 健和興", "3015.TW 全漢", "3023.TW 信邦", "3031.TW 佰鴻", "3033.TW 威健", "3090.TW 日電貿", "3305.TW 昇貿", "3308.TW 聯德"],
    "📡 通信網路業": ["2412.TW 中華電", "3045.TW 台灣大", "4904.TW 遠傳", "2345.TW 智邦", "3596.TW 智易", "5388.TW 中磊", "6285.TW 啟碁", "3704.TW 合勤控", "2419.TW 仲琦", "2485.TW 兆赫", "2450.TW 神腦", "3062.TW 建漢", "2314.TW 台揚", "2498.TW 宏達電", "3149.TW 正達", "2332.TW 友訊", "2455.TW 全新", "3047.TW 訊舟", "3162.TW 精確", "3234.TW 光環", "3312.TW 弘憶股", "3363.TW 上詮", "3380.TW 明泰", "3491.TW 昇達科", "3558.TW 神準", "3682.TW 亞太電", "4906.TW 正文", "4977.TW 眾達-KY", "4979.TW 華星光", "6112.TW 聚碩", "6190.TW 萬泰科", "6216.TW 居易", "6245.TW 立端", "6263.TW 普萊德", "6279.TW 胡連"],
    "💡 光電業": ["3008.TW 大立光", "3406.TW 玉晶光", "2409.TW 友達", "3481.TW 群創", "6116.TW 彩晶", "2448.TW 晶電", "6209.TW 今國光", "3141.TW 晶宏", "2426.TW 鼎元", "6120.TW 達運", "3622.TW 洋華", "3019.TW 亞光", "2393.TW 億光", "3576.TW 聯合再生", "6456.TW GIS-KY", "6443.TW 元晶", "2323.TW 中環", "2340.TW 光磊", "2349.TW 錸德", "2374.TW 佳能", "2406.TW 國碩", "2486.TW 一詮", "2489.TW 瑞軒", "3059.TW 華晶科", "3338.TW 泰碩", "3356.TW 奇偶", "3362.TW 先進光", "3441.TW 聯一光", "3450.TW 聯鈞", "3454.TW 晶睿", "3504.TW 揚明光", "3535.TW 晶彩科", "3591.TW 艾笛森", "3698.TW 隆達", "4934.TW 太極"],
    "⚙️ 電機機械業": ["1504.TW 東元", "1519.TW 華城", "1590.TW 亞德客-KY", "1513.TW 中興電", "1514.TW 亞力", "1503.TW 士電", "1515.TW 力山", "1522.TW 堤維西", "1532.TW 勤美", "1521.TW 大億", "1525.TW 江申", "1537.TW 廣隆", "1536.TW 和大", "1589.TW 永冠-KY", "1524.TW 耿鼎", "4532.TW 瑞智", "4571.TW 鈞興-KY", "8996.TW 高力", "4583.TW 台灣精銳", "1506.TW 正道", "1507.TW 永大", "1526.TW 日馳", "1527.TW 鑽全", "1533.TW 車王電", "1539.TW 巨庭", "1558.TW 伸興", "1560.TW 中砂", "1568.TW 倉佑", "1582.TW 信錦", "1583.TW 程泰", "1598.TW 岱宇", "2049.TW 上銀", "2228.TW 劍麟", "2239.TW 英利-KY", "4526.TW 東台", "4536.TW 拓凱", "4540.TW 吉茂", "4551.TW 智伸科"]
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
    .show-df [data-testid="stDataFrame"] { display: block !important; }
    </style>
""", unsafe_allow_html=True)

# --- 側邊欄 ---
st.sidebar.title("📊 儀表板選單")
page = st.sidebar.radio("請選擇模組：", [
    "🇹🇼 台灣市場 (台股)", 
    "🌐 全球市場 (總經)", 
    "📂 產業股票池", 
    "🔍 潛力股自動篩選",
    "💰 即時 ETF 殖利率與人氣模組"
])

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

# --- 資料抓取模組 ---
@st.cache_data(ttl=86400)
def fetch_all_twse_tickers():
    try:
        url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo"
        res = requests.get(url, timeout=10, verify=False)
        if res.status_code == 200:
            data = res.json()
            tickers = [
                f"{item['stock_id']}.TW {item.get('stock_name', '')}".strip()
                for item in data.get('data', []) 
                if item.get('type') == 'twse' and len(item.get('stock_id', '')) == 4 and item['stock_id'].isdigit()
            ]
            if tickers: return list(set(tickers))
    except Exception as e: st.error(f"全市場 API 連線異常：{e}")
    return []

@st.cache_data(ttl=300)
def fetch_data(indicators_dict):
    all_data, summary_list = {}, []
    for name, ticker_display in indicators_dict.items():
        try:
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

@st.cache_data(ttl=1800)
def fetch_institutional_data():
    try:
        start_date = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime("%Y-%m-%d")
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockTotalInstitutionalInvestors&start_date={start_date}"
        res = requests.get(url, timeout=10, verify=False)
        if res.status_code == 200:
            data_list = res.json().get('data', [])
            if data_list:
                df = pd.DataFrame(data_list).sort_values('date')
                latest_date = df['date'].iloc[-1]
                latest_data = df[df['date'] == latest_date]
                
                inst_data = {"外資": 0.0, "投信": 0.0, "自營商": 0.0, "日期": latest_date}
                for _, row in latest_data.iterrows():
                    name = str(row.get('name', '')).lower()
                    buy_val = float(row.get('buy', 0))
                    sell_val = float(row.get('sell', 0))
                    net_val = (buy_val - sell_val) / 100000000 
                    
                    if "外資" in name or "foreign" in name: inst_data["外資"] += net_val
                    elif "投信" in name or "investment" in name or "trust" in name: inst_data["投信"] += net_val
                    elif "自營" in name or "dealer" in name: inst_data["自營商"] += net_val
                        
                inst_data["合計"] = inst_data["外資"] + inst_data["投信"] + inst_data["自營商"]
                return inst_data
    except Exception: pass
    return None

def generate_dynamic_analysis(summary, inst_data):
    def get_val(name, key, default=0): 
        return next((x[key] for x in summary if name in x['name']), default)
    
    taiex_c = get_val("加權指數", "current")
    taiex_trend = get_val("加權指數", "trend_text", "盤整")
    otc_trend = get_val("櫃買指數", "trend_text", "盤整")
    twd_c = get_val("美元/台幣", "current")
    twd_trend = get_val("美元/台幣", "trend_text", "盤整")
    sox_trend = get_val("費城半導體", "trend_text", "盤整")
    
    analysis = f"📉 **大盤實況與內外資結構**：\n目前加權指數收在 **{taiex_c:,.0f} 點**，短線呈現**{taiex_trend}**格局。櫃買指數呈現**{otc_trend}**。"
    if taiex_trend == "偏多" and otc_trend == "偏多": analysis += " 資金良性輪動，市場整體風險偏好強勁。\n\n"
    elif taiex_trend == "偏多" and otc_trend == "偏空": analysis += " 資金集中權值股撐盤，中小型股面臨提款賣壓。\n\n"
    elif taiex_trend == "偏空" and otc_trend == "偏空": analysis += " 系統性修正壓力大，建議嚴格控管資金水位。\n\n"
    else: analysis += " 市場板塊出現分歧，資金傾向於特定題材各自表現。\n\n"

    if inst_data:
        total_net = inst_data['合計']
        analysis += f"📊 **三大法人實質籌碼 (資料日期: {inst_data['日期']})**：\n法人整體呈現 **{'買超' if total_net > 0 else '賣超'} {abs(total_net):.1f} 億元**。"
        analysis += f" 其中，外資**{'買超' if inst_data['外資'] > 0 else '賣超'} {abs(inst_data['外資']):.1f} 億**，投信**{'買超' if inst_data['投信'] > 0 else '賣超'} {abs(inst_data['投信']):.1f} 億**，自營商**{'買超' if inst_data['自營商'] > 0 else '賣超'} {abs(inst_data['自營商']):.1f} 億**。"
        if inst_data['外資'] > 0 and inst_data['投信'] > 0: analysis += " 土洋法人同步買超，籌碼支撐強。\n\n"
        elif inst_data['外資'] < 0 and inst_data['投信'] > 0: analysis += " 籌碼面呈現「外資提款、投信低接」的對作態勢。\n\n"
        elif inst_data['外資'] < 0 and inst_data['投信'] < 0: analysis += " 內外資大舉撤出，籌碼面極度弱勢。\n\n"
        else: analysis += "\n\n"
    else: analysis += "📊 **籌碼面**：目前暫無法人買賣超資料連線。\n\n"

    analysis += f"🌍 **國際連動與匯率熱錢**：\n美元兌台幣報 **{twd_c:.2f}**，趨勢**{twd_trend}**。"
    if twd_trend == "偏多": analysis += " 台幣貶值態勢與熱錢匯出壓力相符。"
    else: analysis += " 台幣維持強勢，資金動能有利推升指數。"
    analysis += f" 費半指數呈現**{sox_trend}**，直接影響台股電子板塊。"
    return analysis

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
    inst_data = fetch_institutional_data()
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
    if st.button("📥 一鍵載入「全市場台股 (約1000檔)」", type="primary"):
        with st.spinner("正在連線 API 獲取全市場代碼與名稱..."):
            all_tickers = fetch_all_twse_tickers()
            if all_tickers:
                st.session_state.stock_pool = list(set(st.session_state.stock_pool + all_tickers))
                st.success(f"✅ 成功載入！目前篩選池共有 {len(st.session_state.stock_pool)} 檔標的。")
            else: st.error("❌ 無法連線至 API。")

    col1, col2 = st.columns([1, 2])
    with col1:
        timeframe = st.selectbox("選擇 K線週期：", ["日 K線 (短線)", "週 K線 (中線)", "月 K線 (長線)"])
        period, interval = ("6mo", "1d") if "日" in timeframe else ("2y", "1wk") if "週" in timeframe else ("5y", "1mo")
    with col2:
        pool_input = st.text_area("當前篩選股票池：", value=", ".join(st.session_state.stock_pool))
        current_pool = [x.strip().upper() for x in pool_input.split(",") if x.strip()]

    if st.button("🗑️ 清空清單"): st.session_state.stock_pool = []; st.rerun()

    if st.button("🚀 啟動演算法篩選", use_container_width=True):
        if not current_pool: st.warning("股票池為空。")
        else:
            if len(current_pool) > 100: st.warning(f"⚠️ 即將掃描 {len(current_pool)} 檔股票。預計需要數分鐘。")
            results = {"ma_breakout": [], "vol_up": [], "hammer": []}
            bar = st.progress(0)
            status_text = st.empty()
            for idx, ticker_display in enumerate(current_pool):
                status_text.text(f"掃描中 {ticker_display} ... ({idx+1}/{len(current_pool)})")
                try:
                    yf_ticker = ticker_display.split()[0]
                    df = yf.Ticker(yf_ticker).history(period=period, interval=interval)
                    if len(df) >= 20:
                        df['MA5'], df['MA10'], df['MA20'] = df['Close'].rolling(5).mean(), df['Close'].rolling(10).mean(), df['Close'].rolling(20).mean()
                        curr, prev = df.iloc[-1], df.iloc[-2]
                        C, O, H, L, V, prev_V = curr['Close'], curr['Open'], curr['High'], curr['Low'], curr['Volume'], prev['Volume']
                        ma5, ma10, ma20 = curr['MA5'], curr['MA10'], curr['MA20']
                        if (C > O) and ((min(O, C) - L) > abs(C - O)*2) and ((H - max(O, C)) < abs(C - O)*0.5): results["hammer"].append(f"**{ticker_display}** ({C:.2f})")
                        if (C > prev['Close']) and (V > prev_V * 1.5): results["vol_up"].append(f"**{ticker_display}** ({C:.2f})")
                        max_ma, min_ma = max(ma5, ma10, ma20), min(ma5, ma10, ma20)
                        if (((max_ma - min_ma) / min_ma) < 0.03) and (C > max_ma) and (prev['Close'] < max_ma): results["ma_breakout"].append(f"**{ticker_display}** ({C:.2f})")
                except: pass
                bar.progress((idx + 1) / len(current_pool))
                
            status_text.text("✅ 全面掃描完成！")
            st.markdown("#### 🔥 均線糾結且向上突破 (起漲爆發)")
            if results["ma_breakout"]: 
                for s in results["ma_breakout"]: st.error(f"🚀 {s}")
            else: st.write("無符合標的。")
            st.markdown("#### 📈 價漲量增 (資金湧入)")
            if results["vol_up"]: 
                for s in results["vol_up"]: st.success(s)
            else: st.write("無符合標的。")
            st.markdown("#### 🔨 陽線錘子 (底部支撐)")
            if results["hammer"]: 
                for s in results["hammer"]: st.warning(s)
            else: st.write("無符合標的。")

# ==========================================
# 頁面五：高股息/ETF 即時人氣模組
# ==========================================
elif page == "💰 即時 ETF 殖利率與人氣模組":
    st.markdown("<div class='show-df'>", unsafe_allow_html=True)
    st.title("💰 終極版 187 檔台股 ETF 即時運算引擎")
    st.markdown("系統正運用 **多執行緒 (Multi-threading)** 技術，向 Yahoo Finance 引擎以每秒並發的方式，閃電抓取全台灣 187 檔熱門 ETF 的「今日現價」、「過去一年配息總額」以及「最新成交量」，並即時算出最精準的年化殖利率！")
    st.info("💡 **操作提示**：點擊表格上方的標題（例如：`即時殖利率(%)` 或 `今日成交量(張)`），系統就會自動幫您由高到低排序！")
    st.markdown("---")
    
    # 內建您提供的 100 檔超完整 ETF 名單字典
    FULL_ETF_LIST = {
        '0050.TW': '元大台灣50', '0051.TW': '元大中型100', '0052.TW': '富邦科技', '0053.TW': '元大電子', '0055.TW': '元大MSCI金融', '0056.TW': '元大高股息', '006201.TW': '元大富櫃50', '006203.TW': '元大MSCI台灣', '006204.TW': '永豐臺灣加權', '006208.TW': '富邦台50', '00679B.TW': '元大美債20年', '00687B.TW': '國泰20年美債', '00690.TW': '兆豐藍籌30', '00692.TW': '富邦公司治理', '00694B.TW': '富邦美債1-3', '00695B.TW': '富邦美債7-10', '00696B.TW': '富邦美債20年', '00697B.TW': '元大美債7-10', '00701.TW': '國泰股利精選30', '00702.TW': '國泰標普低波高息', '00710B.TW': '復華彭博非投等債', '00711B.TW': '復華彭博新興債', '00712.TW': '復華富時不動產', '00713.TW': '元大台灣高息低波', '00714.TW': '群益道瓊美國地產', '00717.TW': '富邦美國特別股', '00719B.TW': '元大美債1-3', '00720B.TW': '元大投資級公司債', '00722B.TW': '群益投資級電信債', '00723B.TW': '群益投資級科技債', '00724B.TW': '群益投資級金融債', '00725B.TW': '國泰投資級公司債', '00726B.TW': '國泰新興投等債', '00727B.TW': '國泰優選非投等債', '00728.TW': '第一金工業30', '00730.TW': '富邦臺灣優質高息', '00731.TW': '復華富時高息低波', '00733.TW': '富邦臺灣中小', '00734B.TW': '台新JPM新興債', '00735.TW': '國泰臺韓科技', '00736.TW': '國泰新興市場', '00739.TW': '元大MSCIA股', '00740B.TW': '富邦全球投等債', '00741B.TW': '富邦全球非投等債', '00746B.TW': '富邦A級公司債', '00749B.TW': '凱基新興債10+', '00750B.TW': '凱基科技債10+', '00751B.TW': '元大AAA至A公司', '00754B.TW': '群益AAA-AA公司', '00755B.TW': '群益投資級公用債', '00756B.TW': '群益投等新興公債', '00758B.TW': '復華能源債', '00759B.TW': '復華製藥債', '00760B.TW': '復華新興企業債', '00761B.TW': '國泰A級公司債', '00764B.TW': '群益25年美債', '00768B.TW': '復華20年美債', '00770.TW': '國泰北美科技', '00771.TW': '元大US高息特別', '00772B.TW': '中信高評級公司債', '00773B.TW': '中信優先金融債', '00775B.TW': '新光投等債15+', '00777B.TW': '凱基AAA至A公司', '00778B.TW': '凱基金融債20+', '00779B.TW': '凱基美債25+', '00780B.TW': '國泰A級金融債', '00781B.TW': '國泰A級科技債', '00782B.TW': '國泰A級公用債', '00785B.TW': '富邦金融投等債', '00786B.TW': '元大10年IG銀行', '00787B.TW': '元大10年IG醫療', '00788B.TW': '元大10年IG電能', '00789B.TW': '復華公司債A3', '00791B.TW': '復華信用債1-5', '00792B.TW': '群益A級公司債', '00793B.TW': '群益AAA-A醫療債', '00795B.TW': '中信美國公債20', '00799B.TW': '國泰A級醫療債', '00830.TW': '國泰費城半導體', '00834B.TW': '第一金金融債10+', '00836B.TW': '永豐10年A公司債', '00840B.TW': '凱基IG精選15+', '00841B.TW': '凱基AAA-AA公司', '00842B.TW': '台新美元銀行債', '00844B.TW': '新光15年IG金融', '00845B.TW': '富邦新興投等債', '00846B.TW': '富邦歐洲銀行債', '00847B.TW': '中信美國市政債', '00848B.TW': '中信新興亞洲債', '00849B.TW': '中信EM主權債0-5', '00850.TW': '元大臺灣ESG永續', '00851.TW': '台新全球AI', '00853B.TW': '統一美債10年Aa-', '00856B.TW': '永豐1-3年美公債', '00857B.TW': '永豐20年美公債', '00858.TW': '永豐美國500大', '00859B.TW': '群益0-1年美債', '00860B.TW': '群益1-5Y投資級', '00862B.TW': '中信投資級公司債', '00863B.TW': '中信全球電信債', '00864B.TW': '中信美國公債0-1', '00867B.TW': '新光A-BBB電信債', '00870B.TW': '元大15年EM主權', '00878.TW': '國泰永續高股息', '00881.TW': '國泰台灣科技龍頭', '00882.TW': '中信中國高股息', '00883B.TW': '中信ESG投資級債', '00884B.TW': '中信低碳新興債', '00888.TW': '永豐台灣ESG', '00890B.TW': '凱基ESGBBB債15', '00891.TW': '中信關鍵半導體', '00892.TW': '富邦台灣半導體', '00894.TW': '中信小資高價30', '00896.TW': '中信綠能及電動車', '00900.TW': '富邦特選高股息3', '00901.TW': '永豐智能車供應鏈', '00904.TW': '新光臺灣半導體3', '00905.TW': 'FT臺灣Smart', '00907.TW': '永豐優息存股', '00908.TW': '富邦入息REITs+', '00909.TW': '國泰數位支付服務', '00911.TW': '兆豐洲際半導體', '00912.TW': '中信臺灣智慧50', '00913.TW': '兆豐台灣晶圓製造', '00915.TW': '凱基優選高股息3', '00916.TW': '國泰全球品牌50', '00917.TW': '中信特選金融', '00918.TW': '大華優利高填息3', '00919.TW': '群益台灣精選高息', '00920.TW': '富邦ESG綠色電力', '00921.TW': '兆豐龍頭等權重', '00922.TW': '國泰台灣領袖50', '00923.TW': '群益台ESG低碳50', '00926.TW': '凱基全球菁英55', '00927.TW': '群益半導體收益', '00928.TW': '中信上櫃ESG30', '00929.TW': '復華台灣科技優息', '00930.TW': '永豐ESG低碳高息', '00931B.TW': '統一美債20年', '00932.TW': '兆豐永續高息等權', '00933B.TW': '國泰10Y+金融債', '00934.TW': '中信成長高股息', '00935.TW': '野村臺灣新科技5', '00936.TW': '台新永續高息中小', '00937B.TW': '群益ESG投等債20', '00938.TW': '凱基優選30', '00939.TW': '統一台灣高息動能', '00940.TW': '元大台灣價值高息', '00942B.TW': '台新美A公司債20', '00943.TW': '兆豐電子高息等權', '00944.TW': '野村趨勢動能高息', '00945B.TW': '凱基美國非投等債', '00946.TW': '群益科技高息成長', '00947.TW': '台新臺灣IC設計', '00948B.TW': '中信優息投資級債', '00950B.TW': '凱基A級公司債', '00951.TW': '台新日本半導體', '00952.TW': '凱基台灣AI50', '00953B.TW': '群益優選非投等債', '00956.TW': '中信日經高股息', '00957B.TW': '兆豐US優選投等', '00958B.TW': '永豐ESG銀行債15', '00959B.TW': '大華投等美債15Y', '00960.TW': '野村全球航運龍頭', '00961.TW': 'FT臺灣永續高息', '00962.TW': '台新AI優息動能', '00963.TW': '中信全球高股息', '00964.TW': '中信亞太高股息', '00966B.TW': '統一ESG投等債15', '00967B.TW': '元大優息美債', '00968B.TW': '元大優息投等債', '00970B.TW': '新光BBB投等債20', '00971.TW': '野村美國研發龍頭', '00972.TW': '野村日本動能高息', '009802.TW': '富邦旗艦50', '009803.TW': '保德信市值動能5', '009804.TW': '聯邦台精彩50', '009808.TW': '華南永昌優選50', '00980A.TW': '主動野村臺灣優選', '00980B.TW': '台新特選IG債10+', '00980D.TW': '主動聯博投等入息', '00981B.TW': '第一金優選非投債', '00981D.TW': '主動中信非投等債', '00982A.TW': '主動群益台灣強棒', '00982B.TW': 'FT投資級債20+', '00984A.TW': '主動安聯台灣高息', '00985B.TW': '群益ESG投等債0-'}

    # 定義單檔抓取函數，準備餵給多執行緒
    def fetch_single_etf(ticker, name):
        try:
            tkr = yf.Ticker(ticker)
            hist = tkr.history(period="1y")
            if hist.empty: return None
            
            current_price = float(hist['Close'].iloc[-1])
            avg_vol = float(hist['Volume'].tail(5).mean()) / 1000
            daily_vol = float(hist['Volume'].iloc[-1]) / 1000
            
            divs = tkr.dividends
            ttm_div = 0.0
            if not divs.empty:
                # 只算過去365天內的真實配息
                one_year_ago = pd.Timestamp.now(tz=divs.index.tz) - pd.DateOffset(days=365)
                ttm_div = float(divs[divs.index >= one_year_ago].sum())
            
            div_yield = (ttm_div / current_price) * 100 if current_price > 0 else 0.0
            
            # 智慧判斷ETF類型
            etf_type = "其他"
            if "B" in ticker or "債" in name: etf_type = "債券型"
            elif "主動" in name: etf_type = "主動型"
            elif "高" in name or "息" in name or "收益" in name: etf_type = "高股息"
            else: etf_type = "市值/主題型"
            
            return {
                "代號": ticker.replace(".TW", ""),
                "名稱": name,
                "現價": round(current_price, 2),
                "近一年累計配息": round(ttm_div, 3),
                "即時殖利率(%)": round(div_yield, 2),
                "今日成交量(張)": int(daily_vol),
                "五日均量(張)": int(avg_vol),
                "類型": etf_type
            }
        except: return None

    # 快取整併函數，避免頻繁請求
    @st.cache_data(ttl=1800)
    def run_all_etfs_multithread():
        results = []
        # 使用 ThreadPoolExecutor 以 10 條執行緒並發抓取 (大幅加速)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_etf = {executor.submit(fetch_single_etf, t, n): (t, n) for t, n in FULL_ETF_LIST.items()}
            for future in concurrent.futures.as_completed(future_to_etf):
                data = future.result()
                if data: results.append(data)
        # 預設依殖利率排序
        return sorted(results, key=lambda x: x["即時殖利率(%)"], reverse=True)

    with st.spinner(f"⚡ 正在透過多執行緒引擎閃電抓取全台 100 檔 ETF 的即時股價與配息資料... (約需 10~15 秒)"):
        etf_data = run_all_etfs_multithread()
        
    if etf_data:
        df_etf = pd.DataFrame(etf_data)
        
        # 建立上方篩選器
        col1, col2 = st.columns(2)
        with col1: type_filter = st.selectbox("篩選 ETF 類型：", ["全部顯示", "高股息", "市值/主題型", "債券型", "主動型"])
        with col2: st.metric(label="成功載入檔數", value=len(df_etf))
            
        if type_filter != "全部顯示":
            df_etf = df_etf[df_etf["類型"] == type_filter]
            
        st.dataframe(
            df_etf,
            use_container_width=True,
            hide_index=True,
            column_config={
                "代號": st.column_config.TextColumn("代號", width="small"),
                "名稱": st.column_config.TextColumn("ETF 名稱", width="medium"),
                "現價": st.column_config.NumberColumn("現價", format="%.2f 元"),
                "近一年累計配息": st.column_config.NumberColumn("近一年累計配息", format="%.3f 元"),
                "即時殖利率(%)": st.column_config.ProgressColumn(
                    "即時年化殖利率 (%)",
                    help="真實配息 ÷ 即時現價",
                    format="%.2f %%",
                    min_value=0, max_value=12,
                ),
                "今日成交量(張)": st.column_config.NumberColumn(
                    "今日成交量 (人氣指標)",
                    help="今日最新成交張數，數值越高代表買氣越旺",
                    format="%d 張",
                ),
                "五日均量(張)": st.column_config.NumberColumn(
                    "五日均量 (波段指標)",
                    format="%d 張",
                ),
            }
        )
    else:
        st.error("暫時無法取得資料。")
        
    st.markdown("---")
    st.caption("註：年化殖利率採計過去 365 天內該檔 ETF 實際發放的除息總和，除以 Yahoo Finance 即時現價而得。新上市未滿一年或近期未配息之 ETF，數值可能為 0。")
    st.markdown("</div>", unsafe_allow_html=True)

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
st.caption("免責聲明：本儀表板技術與配息數據均由 Yahoo Finance 提供，不構成任何投資建議。")
