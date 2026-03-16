import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import datetime
import requests
import urllib3

# 關閉不安全的 SSL 憑證警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 網頁設定 ---
st.set_page_config(page_title="專業市場儀表板", layout="wide", initial_sidebar_state="expanded")

# --- 🚀 究極擴充版：台股八大產業分類字典 (各約 40~50 檔) ---
INDUSTRY_STOCKS = {
    "🛠️ 半導體業 (晶圓/IC/封測)": [
        "2330.TW 台積電", "2454.TW 聯發科", "2303.TW 聯電", "3711.TW 日月光投控", "2379.TW 瑞昱", "2408.TW 南亞科", "3443.TW 創意", "3034.TW 聯詠", "4966.TW 譜瑞-KY", "6415.TW 矽力*-KY", "3529.TW 力旺", "8299.TW 群聯", "6770.TW 力積電", "6488.TW 環球晶", "2338.TW 光罩", "2344.TW 華邦電", "2449.TW 京元電子", "3014.TW 聯陽", "6239.TW 力成", "3189.TW 景碩", "2401.TW 凌陽", "3532.TW 台勝科", "6531.TW 愛普*", "4919.TW 新唐", "3006.TW 晶豪科", "5347.TW 世界", "6147.TW 頎邦", "8016.TW 矽創", "8081.TW 致新", "3260.TW 威剛", "6202.TW 盛群", "3588.TW 通嘉", "2436.TW 偉詮電", "6237.TW 驊訊", "2369.TW 菱生", "3661.TW 世芯-KY", "6643.TW M31", "8150.TW 南茂", "3141.TW 晶宏", "6533.TW 晶心科", "6282.TW 康舒", "3583.TW 辛耘", "5269.TW 祥碩", "2458.TW 義隆", "3016.TW 嘉晶", "6138.TW 茂達", "3227.TW 原相", "2481.TW 強茂", "3374.TW 精材", "3035.TW 智原"
    ],
    "💻 電腦及週邊設備 (AI伺服器/PC)": [
        "2382.TW 廣達", "3231.TW 緯創", "2356.TW 英業達", "2324.TW 仁寶", "2376.TW 技嘉", "2395.TW 研華", "6669.TW 緯穎", "2353.TW 宏碁", "2357.TW 華碩", "3005.TW 神基", "2362.TW 藍天", "3013.TW 晟銘電", "4938.TW 和碩", "6206.TW 飛捷", "3017.TW 奇鋐", "6166.TW 凌華", "2377.TW 微星", "6515.TW 穎崴", "2301.TW 光寶科", "2397.TW 友通", "2465.TW 麗臺", "3022.TW 威強電", "6117.TW 迎廣", "3046.TW 建碁", "2399.TW 映泰", "3494.TW 誠研", "2371.TW 大同", "3050.TW 鈺德", "3060.TW 銘異", "3211.TW 順達", "3515.TW 華擎", "6277.TW 宏正", "6412.TW 群電", "6414.TW 樺漢", "6579.TW 研揚", "8112.TW 至上", "8210.TW 勤誠", "8416.TW 實威", "5215.TW 捷波", "4999.TW 鑫禾", "4915.TW 致伸", "3706.TW 神達", "3483.TW 力致", "3413.TW 京鼎", "3058.TW 立德", "2425.TW 承啟", "2417.TW 圓剛", "2405.TW 浩鑫", "2387.TW 精元", "2365.TW 昆盈"
    ],
    "🏦 金融保險業 (金控/銀行/證券)": [
        "2881.TW 富邦金", "2882.TW 國泰金", "2891.TW 中信金", "2886.TW 兆豐金", "2884.TW 玉山金", "2892.TW 第一金", "2885.TW 元大金", "2880.TW 華南金", "2890.TW 永豐金", "2883.TW 開發金", "2887.TW 台新金", "2801.TW 彰銀", "2834.TW 臺企銀", "2838.TW 聯邦銀", "2845.TW 遠東銀", "2850.TW 新產", "2851.TW 中再保", "2852.TW 第一保", "2809.TW 京城銀", "5880.TW 合庫金", "5876.TW 上海商銀", "6005.TW 群益證", "2812.TW 台中銀", "2820.TW 華票", "2832.TW 台產", "2849.TW 安泰銀", "2867.TW 三商壽", "2888.TW 新光金", "2889.TW 國票金", "2897.TW 王道銀行", "5878.TW 台名", "6016.TW 康和證", "6024.TW 群益期", "2836.TW 高雄銀", "2855.TW 統一證", "6015.TW 宏遠證", "6020.TW 大展證", "6021.TW 大慶證", "6023.TW 元大期", "5864.TW 致和證", "5871.TW 中租-KY"
    ],
    "🚢 航運業 (貨櫃/散裝/航空)": [
        "2603.TW 長榮", "2609.TW 陽明", "2615.TW 萬海", "2618.TW 長榮航", "2610.TW 華航", "2606.TW 裕民", "2637.TW 慧洋-KY", "2605.TW 新興", "2612.TW 中航", "2613.TW 中櫃", "2617.TW 台航", "2601.TW 益航", "2611.TW 志信", "5608.TW 四維航", "2607.TW 榮運", "2634.TW 漢翔", "2614.TW 東森", "2633.TW 台灣高鐵", "2642.TW 宅配通", "2646.TW 星宇航空", "2616.TW 山隆", "2208.TW 台船", "2636.TW 台驊投控", "5609.TW 中菲行", "5607.TW 遠雄港", "2641.TW 正德", "2643.TW 捷迅", "2748.TW 雲品", "2630.TW 亞航", "2618A.TW 長榮航特"
    ],
    "🔌 電子零組件業 (被動/PCB/散熱)": [
        "2308.TW 台達電", "2327.TW 國巨", "3037.TW 欣興", "2313.TW 華通", "3044.TW 健鼎", "2368.TW 金像電", "3324.TW 雙鴻", "2383.TW 台光電", "2492.TW 華新科", "6269.TW 台郡", "3346.TW 麗清", "2421.TW 建準", "6274.TW 台燿", "2375.TW 智寶", "2428.TW 興勤", "2355.TW 敬鵬", "3042.TW 晶技", "6197.TW 佳必琪", "3026.TW 禾伸堂", "3217.TW 優群", "2316.TW 楠梓電", "2351.TW 順德", "2367.TW 燿華", "2373.TW 震旦行", "2385.TW 群光", "2390.TW 云辰", "2415.TW 錩新", "2420.TW 新巨", "2431.TW 聯昌", "2439.TW 美律", "2440.TW 太空梭", "2457.TW 飛宏", "2460.TW 建通", "2462.TW 良得電", "2472.TW 立隆電", "2478.TW 大毅", "2484.TW 希華", "2493.TW 揚博", "3003.TW 健和興", "3015.TW 全漢", "3023.TW 信邦", "3031.TW 佰鴻", "3033.TW 威健", "3051.TW 力特", "3090.TW 日電貿", "3209.TW 全科", "3296.TW 勝德", "3305.TW 昇貿", "3308.TW 聯德", "3311.TW 閎暉"
    ],
    "📡 通信網路業 (電信/網通)": [
        "2412.TW 中華電", "3045.TW 台灣大", "4904.TW 遠傳", "2345.TW 智邦", "3596.TW 智易", "5388.TW 中磊", "6285.TW 啟碁", "3704.TW 合勤控", "2419.TW 仲琦", "2485.TW 兆赫", "2450.TW 神腦", "3062.TW 建漢", "2314.TW 台揚", "2444.TW 友旺", "2498.TW 宏達電", "3149.TW 正達", "2321.TW 東訊", "2332.TW 友訊", "2432.TW 倚強科", "2442.TW 新美齊", "2455.TW 全新", "3025.TW 星通", "3047.TW 訊舟", "3162.TW 精確", "3234.TW 光環", "3309.TW 智建", "3312.TW 弘憶股", "3363.TW 上詮", "3380.TW 明泰", "3438.TW 類比科", "3491.TW 昇達科", "3550.TW 聯穎", "3558.TW 神準", "3580.TW 友威科", "3664.TW 安瑞-KY", "3682.TW 亞太電", "4903.TW 聯光通", "4906.TW 正文", "4977.TW 眾達-KY", "4979.TW 華星光", "5290.TW 邑錡", "6112.TW 聚碩", "6136.TW 富爾特", "6142.TW 星寶國際", "6152.TW 百一", "6190.TW 萬泰科", "6216.TW 居易", "6245.TW 立端", "6263.TW 普萊德", "6279.TW 胡連"
    ],
    "💡 光電業 (面板/鏡頭)": [
        "3008.TW 大立光", "3406.TW 玉晶光", "2409.TW 友達", "3481.TW 群創", "6116.TW 彩晶", "2448.TW 晶電", "6209.TW 今國光", "3141.TW 晶宏", "2426.TW 鼎元", "6120.TW 達運", "3622.TW 洋華", "3019.TW 亞光", "2393.TW 億光", "3576.TW 聯合再生", "6456.TW GIS-KY", "6443.TW 元晶", "2323.TW 中環", "2340.TW 光磊", "2349.TW 錸德", "2374.TW 佳能", "2406.TW 國碩", "2429.TW 銘旺科", "2438.TW 翔耀", "2466.TW 冠西電", "2486.TW 一詮", "2489.TW 瑞軒", "2491.TW 吉祥全", "3024.TW 憶聲", "3038.TW 全台", "3052.TW 夆典", "3059.TW 華晶科", "3297.TW 杭特", "3338.TW 泰碩", "3356.TW 奇偶", "3362.TW 先進光", "3383.TW 新世紀", "3437.TW 榮創", "3441.TW 聯一光", "3450.TW 聯鈞", "3454.TW 晶睿", "3498.TW 陽程", "3504.TW 揚明光", "3519.TW 綠能", "3535.TW 晶彩科", "3557.TW 嘉威", "3562.TW 頂晶科", "3591.TW 艾笛森", "3623.TW 富晶通", "3698.TW 隆達", "4934.TW 太極"
    ],
    "⚙️ 電機機械業 (重電/工具機)": [
        "1504.TW 東元", "1519.TW 華城", "1590.TW 亞德客-KY", "1513.TW 中興電", "1514.TW 亞力", "1503.TW 士電", "1515.TW 力山", "1522.TW 堤維西", "1532.TW 勤美", "1521.TW 大億", "1525.TW 江申", "1537.TW 廣隆", "1536.TW 和大", "1589.TW 永冠-KY", "1524.TW 耿鼎", "4532.TW 瑞智", "4571.TW 鈞興-KY", "8996.TW 高力", "4583.TW 台灣精銳", "1506.TW 正道", "1507.TW 永大", "1512.TW 瑞利", "1517.TW 利奇", "1526.TW 日馳", "1527.TW 鑽全", "1528.TW 恩德", "1529.TW 樂士", "1530.TW 亞星", "1531.TW 高林股", "1533.TW 車王電", "1535.TW 中宇", "1539.TW 巨庭", "1540.TW 喬福", "1541.TW 錩泰", "1558.TW 伸興", "1560.TW 中砂", "1568.TW 倉佑", "1582.TW 信錦", "1583.TW 程泰", "1598.TW 岱宇", "2049.TW 上銀", "2228.TW 劍麟", "2239.TW 英利-KY", "3167.TW 大量", "3379.TW 彬台", "4526.TW 東台", "4536.TW 拓凱", "4540.TW 吉茂", "4545.TW 銘鈺", "4551.TW 智伸科"
    ]
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

# --- 🚀 跨日備援：FinMind 三大法人 API ---
@st.cache_data(ttl=1800)
def fetch_institutional_data():
    """改用 FinMind API 獲取跨日法人資料，避免假日/盤中抓不到"""
    try:
        # 往前推 10 天，確保能抓到最近一個有效交易日的資料
        start_date = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime("%Y-%m-%d")
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockTotalInstitutionalInvestors&start_date={start_date}"
        res = requests.get(url, timeout=10, verify=False)
        
        if res.status_code == 200:
            data_list = res.json().get('data', [])
            if data_list:
                df = pd.DataFrame(data_list)
                df = df.sort_values('date')
                latest_date = df['date'].iloc[-1] # 取得最新有效交易日
                latest_data = df[df['date'] == latest_date]
                
                inst_data = {"外資": 0.0, "投信": 0.0, "自營商": 0.0, "日期": latest_date}
                for _, row in latest_data.iterrows():
                    name = row['name']
                    # 將買賣超轉換為「億」元
                    net_val = (row['buy'] - row['sell']) / 100000000 
                    if "外資及陸資" in name and "不含外資自營商" in name: inst_data["外資"] = net_val
                    elif "投信" in name: inst_data["投信"] = net_val
                    elif "自營商" in name: inst_data["自營商"] += net_val
                        
                inst_data["合計"] = inst_data["外資"] + inst_data["投信"] + inst_data["自營商"]
                return inst_data
    except Exception: pass
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
        analysis += f"📊 **三大法人實質籌碼 (資料日期: {inst_data['日期']})**：\n根據最新資料，三大法人整體呈現 **{'買超' if total_net > 0 else '賣超'} {abs(total_net):.1f} 億元**。"
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
        analysis += "📊 **籌碼面**：目前暫無法人買賣超資料連線。\n\n"

    analysis += f"🌍 **國際連動與匯率熱錢**：\n匯市方面，目前美元兌台幣報 **{twd_c:.2f}**，趨勢**{twd_trend}**。"
    if twd_trend == "偏多":
        analysis += " 台幣呈現貶值態勢（突破均線），這與外資熱錢匯出壓力相符，大型權值股易受提款影響。"
    else:
        analysis += " 台幣維持升值或強勢格局，資金動能充沛，有利於推升指數。"
        
    analysis += f" 費半指數呈現**{sox_trend}**，對台股電子板塊產生直接連動效應。"

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
        precision = ".0f" if "加權" in item['name'] or "櫃買" in item['name'] or "費城" in item['name'] else ".
