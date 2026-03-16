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

# --- 🚀 全新產業鏈與趨勢主題分類庫 ---
INDUSTRY_STOCKS = {
    "🔌 電子工業：半導體業 (IC設計/代工/封測)": ["2330.TW 台積電", "2454.TW 聯發科", "2303.TW 聯電", "3711.TW 日月光投控", "2379.TW 瑞昱", "2408.TW 南亞科", "3443.TW 創意", "3034.TW 聯詠", "4966.TW 譜瑞-KY", "6415.TW 矽力*-KY", "3529.TW 力旺", "8299.TW 群聯", "6770.TW 力積電", "6488.TW 環球晶", "2338.TW 光罩", "2449.TW 京元電子", "6239.TW 力成", "3189.TW 景碩", "6531.TW 愛普*", "4919.TW 新唐", "3661.TW 世芯-KY"],
    "🔌 電子工業：電子零組件 (PCB/被動/連接器)": ["2308.TW 台達電", "2327.TW 國巨", "3037.TW 欣興", "2313.TW 華通", "3044.TW 健鼎", "2368.TW 金像電", "3324.TW 雙鴻", "2383.TW 台光電", "2492.TW 華新科", "6269.TW 台郡", "3042.TW 晶技", "6197.TW 佳必琪", "3217.TW 優群", "2351.TW 順德", "2428.TW 興勤", "3023.TW 信邦", "3031.TW 佰鴻"],
    "💻 電子工業：電腦及週邊設備 (伺服器/NB)": ["2382.TW 廣達", "3231.TW 緯創", "2356.TW 英業達", "2324.TW 仁寶", "2376.TW 技嘉", "2395.TW 研華", "6669.TW 緯穎", "2353.TW 宏碁", "2357.TW 華碩", "3005.TW 神基", "3013.TW 晟銘電", "4938.TW 和碩", "3017.TW 奇鋐", "2377.TW 微星", "6515.TW 穎崴", "2301.TW 光寶科", "8210.TW 勤誠", "3483.TW 力致"],
    "📡 電子工業：通信網路業 (網通/光通訊)": ["2412.TW 中華電", "3045.TW 台灣大", "4904.TW 遠傳", "2345.TW 智邦", "3596.TW 智易", "5388.TW 中磊", "6285.TW 啟碁", "3704.TW 合勤控", "2419.TW 仲琦", "3363.TW 上詮", "3380.TW 明泰", "3491.TW 昇達科", "3558.TW 神準", "4906.TW 正文", "4977.TW 眾達-KY", "4979.TW 華星光", "6442.TW 光聖"],
    "💡 電子工業：光電業 (面板/LED)": ["3008.TW 大立光", "3406.TW 玉晶光", "2409.TW 友達", "3481.TW 群創", "6116.TW 彩晶", "2448.TW 晶電", "3141.TW 晶宏", "3019.TW 亞光", "2393.TW 億光", "6456.TW GIS-KY", "2340.TW 光磊", "3450.TW 聯鈞", "3454.TW 晶睿", "3504.TW 揚明光", "3698.TW 隆達", "6209.TW 今國光"],
    "🛒 電子工業：通路、資服與其他電子": ["3702.TW 大聯大", "2347.TW 聯強", "3036.TW 文曄", "6139.TW 亞翔", "6180.TW 橘子", "2427.TW 宏碁資訊", "6214.TW 精誠", "2354.TW 鴻準", "2359.TW 所羅門", "5434.TW 崇越", "2404.TW 漢唐", "3231.TW 緯創"],
    "🏭 傳統產業：水泥/食品/塑膠/紡織": ["1101.TW 台泥", "1102.TW 亞泥", "1216.TW 統一", "1227.TW 佳格", "1210.TW 大成", "1301.TW 台塑", "1303.TW 南亞", "1326.TW 台化", "1304.TW 台聚", "1402.TW 遠東新", "1476.TW 儒鴻", "1477.TW 聚陽", "1409.TW 新纖"],
    "⚙️ 傳統產業：電機/電器/玻璃/造紙/鋼鐵": ["1504.TW 東元", "1519.TW 華城", "1513.TW 中興電", "1514.TW 亞力", "1503.TW 士電", "1605.TW 華新", "1609.TW 大亞", "1802.TW 台玻", "1904.TW 正隆", "1907.TW 永豐餘", "2002.TW 中鋼", "2014.TW 中鴻", "2027.TW 大成鋼", "2006.TW 東和鋼鐵"],
    "🏗️ 傳統產業：橡膠/汽車/建材營造": ["2105.TW 正新", "2106.TW 建大", "2201.TW 裕隆", "2207.TW 和泰車", "2231.TW 為升", "2204.TW 中華", "2504.TW 國產", "2511.TW 太子", "2542.TW 興富發", "2548.TW 華固", "2520.TW 冠德", "5522.TW 遠雄"],
    "🚢 傳統產業：航運業 (航空/海運)": ["2603.TW 長榮", "2609.TW 陽明", "2615.TW 萬海", "2618.TW 長榮航", "2610.TW 華航", "2606.TW 裕民", "2637.TW 慧洋-KY", "2605.TW 新興", "2633.TW 台灣高鐵", "2636.TW 台驊投控", "2634.TW 漢翔", "2646.TW 星宇航空"],
    "🏨 傳統產業：觀光餐旅/綠能休閒/居家生活": ["2707.TW 晶華", "2727.TW 王品", "2731.TW 雄獅", "2739.TW 寒舍", "2748.TW 雲品", "9914.TW 美利達", "9921.TW 巨大", "9904.TW 寶成", "8996.TW 高力", "9910.TW 豐泰", "8464.TW 億豐", "9927.TW 泰銘"],
    "🏦 金融與服務：金融保險 (金控/銀行/證券)": ["2881.TW 富邦金", "2882.TW 國泰金", "2891.TW 中信金", "2886.TW 兆豐金", "2884.TW 玉山金", "2892.TW 第一金", "2885.TW 元大金", "2880.TW 華南金", "2890.TW 永豐金", "2883.TW 開發金", "2887.TW 台新金", "2801.TW 彰銀", "2834.TW 臺企銀", "5880.TW 合庫金", "5871.TW 中租-KY"],
    "🏬 金融與服務：貿易百貨": ["2912.TW 統一超", "2915.TW 潤泰全", "2903.TW 遠百", "2929.TW 淘帝-KY", "8454.TW 富邦媒", "2908.TW 特力", "2911.TW 麗嬰房", "5904.TW 寶雅"],
    "🤖 趨勢主題：AI人工智慧與伺服器": ["2330.TW 台積電", "2382.TW 廣達", "3231.TW 緯創", "6669.TW 緯穎", "2376.TW 技嘉", "2356.TW 英業達", "3017.TW 奇鋐", "3324.TW 雙鴻", "3661.TW 世芯-KY", "3443.TW 創意", "2317.TW 鴻海", "8210.TW 勤誠", "6515.TW 穎崴"],
    "🚗 趨勢主題：電動車輛產業": ["2317.TW 鴻海", "2201.TW 裕隆", "1536.TW 和大", "3665.TW 貿聯-KY", "6282.TW 康舒", "6279.TW 胡連", "2308.TW 台達電", "2231.TW 為升", "4739.TW 康普", "5243.TW 乙盛-KY", "8367.TW 建新國際"],
    "🛰️ 趨勢主題：太空衛星科技": ["2314.TW 台揚", "3491.TW 昇達科", "2313.TW 華通", "6285.TW 啟碁", "5388.TW 中磊", "2419.TW 仲琦", "3380.TW 明泰", "3234.TW 光環", "3311.TW 閎暉", "3466.TW 致振"],
    "🖨️ 趨勢主題：印刷電路板 (PCB)": ["2313.TW 華通", "3037.TW 欣興", "8046.TW 南電", "2368.TW 金像電", "3044.TW 健鼎", "6269.TW 台郡", "6153.TW 嘉聯益", "2367.TW 燿華", "5469.TW 瀚宇博", "8150.TW 南茂", "2383.TW 台光電", "6274.TW 台燿"],
    "🍃 趨勢主題：ESG / 淨零碳排與風力發電": ["1513.TW 中興電", "1519.TW 華城", "1514.TW 亞力", "1503.TW 士電", "3708.TW 上緯投控", "9958.TW 世紀鋼", "6806.TW 森崴能源", "6869.TW 雲豹能源", "8996.TW 高力", "1589.TW 永冠-KY", "2013.TW 中鋼構"],
    "☁️ 趨勢主題：數位雲端與資訊安全": ["6183.TW 關貿", "6214.TW 精誠", "2427.TW 宏碁資訊", "6690.TW 安碁資訊", "6811.TW 宏碁智醫", "5203.TW 訊連", "3029.TW 零壹", "2480.TW 敦陽科", "6112.TW 聚碩", "3130.TW 一零四"]
}

FULL_ETF_LIST = {
    '0050.TW': '元大台灣50', '0051.TW': '元大中型100', '0052.TW': '富邦科技', '0053.TW': '元大電子', '0055.TW': '元大MSCI金融', '0056.TW': '元大高股息', '006201.TW': '元大富櫃50', '006203.TW': '元大MSCI台灣', '006204.TW': '永豐臺灣加權', '006208.TW': '富邦台50', '00679B.TW': '元大美債20年', '00687B.TW': '國泰20年美債', '00690.TW': '兆豐藍籌30', '00692.TW': '富邦公司治理', '00694B.TW': '富邦美債1-3', '00695B.TW': '富邦美債7-10', '00696B.TW': '富邦美債20年', '00697B.TW': '元大美債7-10', '00701.TW': '國泰股利精選30', '00702.TW': '國泰標普低波高息', '00710B.TW': '復華彭博非投等債', '00711B.TW': '復華彭博新興債', '00712.TW': '復華富時不動產', '00713.TW': '元大台灣高息低波', '00714.TW': '群益道瓊美國地產', '00717.TW': '富邦美國特別股', '00719B.TW': '元大美債1-3', '00720B.TW': '元大投資級公司債', '00722B.TW': '群益投資級電信債', '00723B.TW': '群益投資級科技債', '00724B.TW': '群益投資級金融債', '00725B.TW': '國泰投資級公司債', '00726B.TW': '國泰新興投等債', '00727B.TW': '國泰優選非投等債', '00728.TW': '第一金工業30', '00730.TW': '富邦臺灣優質高息', '00731.TW': '復華富時高息低波', '00733.TW': '富邦臺灣中小', '00734B.TW': '台新JPM新興債', '00735.TW': '國泰臺韓科技', '00736.TW': '國泰新興市場', '00739.TW': '元大MSCIA股', '00740B.TW': '富邦全球投等債', '00741B.TW': '富邦全球非投等債', '00746B.TW': '富邦A級公司債', '00749B.TW': '凱基新興債10+', '00750B.TW': '凱基科技債10+', '00751B.TW': '元大AAA至A公司', '00754B.TW': '群益AAA-AA公司', '00755B.TW': '群益投資級公用債', '00756B.TW': '群益投等新興公債', '00758B.TW': '復華能源債', '00759B.TW': '復華製藥債', '00760B.TW': '復華新興企業債', '00761B.TW': '國泰A級公司債', '00764B.TW': '群益25年美債', '00768B.TW': '復華20年美債', '00770.TW': '國泰北美科技', '00771.TW': '元大US高息特別', '00772B.TW': '中信高評級公司債', '00773B.TW': '中信優先金融債', '00775B.TW': '新光投等債15+', '00777B.TW': '凱基AAA至A公司', '00778B.TW': '凱基金融債20+', '00779B.TW': '凱基美債25+', '00780B.TW': '國泰A級金融債', '00781B.TW': '國泰A級科技債', '00782B.TW': '國泰A級公用債', '00785B.TW': '富邦金融投等債', '00786B.TW': '元大10年IG銀行', '00787B.TW': '元大10年IG醫療', '00788B.TW': '元大10年IG電能', '00789B.TW': '復華公司債A3', '00791B.TW': '復華信用債1-5', '00792B.TW': '群益A級公司債', '00793B.TW': '群益AAA-A醫療債', '00795B.TW': '中信美國公債20', '00799B.TW': '國泰A級醫療債', '00830.TW': '國泰費城半導體', '00834B.TW': '第一金金融債10+', '00836B.TW': '永豐10年A公司債', '00840B.TW': '凱基IG精選15+', '00841B.TW': '凱基AAA-AA公司', '00842B.TW': '台新美元銀行債', '00844B.TW': '新光15年IG金融', '00845B.TW': '富邦新興投等債', '00846B.TW': '富邦歐洲銀行債', '00847B.TW': '中信美國市政債', '00848B.TW': '中信新興亞洲債', '00849B.TW': '中信EM主權債0-5', '00850.TW': '元大臺灣ESG永續', '00851.TW': '台新全球AI', '00853B.TW': '統一美債10年Aa-', '00856B.TW': '永豐1-3年美公債', '00857B.TW': '永豐20年美公債', '00858.TW': '永豐美國500大', '00859B.TW': '群益0-1年美債', '00860B.TW': '群益1-5Y投資級', '00862B.TW': '中信投資級公司債', '00863B.TW': '中信全球電信債', '00864B.TW': '中信美國公債0-1', '00867B.TW': '新光A-BBB電信債', '00870B.TW': '元大15年EM主權', '00878.TW': '國泰永續高股息', '00881.TW': '國泰台灣科技龍頭', '00882.TW': '中信中國高股息', '00883B.TW': '中信ESG投資級債', '00884B.TW': '中信低碳新興債', '00888.TW': '永豐台灣ESG', '00890B.TW': '凱基ESGBBB債15', '00891.TW': '中信關鍵半導體', '00892.TW': '富邦台灣半導體', '00894.TW': '中信小資高價30', '00896.TW': '中信綠能及電動車', '00900.TW': '富邦特選高股息3', '00901.TW': '永豐智能車供應鏈', '00904.TW': '新光臺灣半導體3', '00905.TW': 'FT臺灣Smart', '00907.TW': '永豐優息存股', '00908.TW': '富邦入息REITs+', '00909.TW': '國泰數位支付服務', '00911.TW': '兆豐洲際半導體', '00912.TW': '中信臺灣智慧50', '00913.TW': '兆豐台灣晶圓製造', '00915.TW': '凱基優選高股息3', '00916.TW': '國泰全球品牌50', '00917.TW': '中信特選金融', '00918.TW': '大華優利高填息3', '00919.TW': '群益台灣精選高息', '00920.TW': '富邦ESG綠色電力', '00921.TW': '兆豐龍頭等權重', '00922.TW': '國泰台灣領袖50', '00923.TW': '群益台ESG低碳50', '00926.TW': '凱基全球菁英55', '00927.TW': '群益半導體收益', '00928.TW': '中信上櫃ESG30', '00929.TW': '復華台灣科技優息', '00930.TW': '永豐ESG低碳高息', '00931B.TW': '統一美債20年', '00932.TW': '兆豐永續高息等權', '00933B.TW': '國泰10Y+金融債', '00934.TW': '中信成長高股息', '00935.TW': '野村臺灣新科技5', '00936.TW': '台新永續高息中小', '00937B.TW': '群益ESG投等債20', '00938.TW': '凱基優選30', '00939.TW': '統一台灣高息動能', '00940.TW': '元大台灣價值高息', '00942B.TW': '台新美A公司債20', '00943.TW': '兆豐電子高息等權', '00944.TW': '野村趨勢動能高息', '00945B.TW': '凱基美國非投等債', '00946.TW': '群益科技高息成長', '00947.TW': '台新臺灣IC設計', '00948B.TW': '中信優息投資級債', '00950B.TW': '凱基A級公司債', '00951.TW': '台新日本半導體', '00952.TW': '凱基台灣AI50', '00953B.TW': '群益優選非投等債', '00956.TW': '中信日經高股息', '00957B.TW': '兆豐US優選投等', '00958B.TW': '永豐ESG銀行債15', '00959B.TW': '大華投等美債15Y', '00960.TW': '野村全球航運龍頭', '00961.TW': 'FT臺灣永續高息', '00962.TW': '台新AI優息動能', '00963.TW': '中信全球高股息', '00964.TW': '中信亞太高股息', '00966B.TW': '統一ESG投等債15', '00967B.TW': '元大優息美債', '00968B.TW': '元大優息投等債', '00970B.TW': '新光BBB投等債20', '00971.TW': '野村美國研發龍頭', '00972.TW': '野村日本動能高息', '009802.TW': '富邦旗艦50', '009803.TW': '保德信市值動能5', '009804.TW': '聯邦台精彩50', '009808.TW': '華南永昌優選50', '00980A.TW': '主動野村臺灣優選', '00980B.TW': '台新特選IG債10+', '00980D.TW': '主動聯博投等入息', '00981B.TW': '第一金優選非投債', '00981D.TW': '主動中信非投等債', '00982A.TW': '主動群益台灣強棒', '00982B.TW': 'FT投資級債20+', '00984A.TW': '主動安聯台灣高息', '00985B.TW': '群益ESG投等債0-'}

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

# ==========================================
# 核心資料抓取與 API 函數 (全域宣告)
# ==========================================
@st.cache_data(ttl=86400)
def fetch_all_twse_tickers():
    """獲取台股全市場代碼及名稱"""
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
    """進階抓取模組：包含開高低收、成交量、20日均線"""
    all_data, summary_list = {}, []
    for name, ticker_display in indicators_dict.items():
        try:
            yf_ticker = ticker_display.split()[0]
            df = yf.Ticker(yf_ticker).history(period="3mo")
            if not df.empty:
                df['MA5'] = df['Close'].rolling(window=5).mean()
                df['MA10'] = df['Close'].rolling(window=10).mean()
                df['MA20'] = df['Close'].rolling(window=20).mean()
                
                O = float(df['Open'].iloc[-1])
                H = float(df['High'].iloc[-1])
                L = float(df['Low'].iloc[-1])
                C = float(df['Close'].iloc[-1])
                V = float(df['Volume'].iloc[-1]) # 成交量(股數/單位)
                
                prev_C = float(df['Close'].iloc[-2])
                ma5 = float(df['MA5'].iloc[-1]) if len(df) >= 5 else C
                ma10 = float(df['MA10'].iloc[-1]) if len(df) >= 10 else C
                ma20 = float(df['MA20'].iloc[-1]) if len(df) >= 20 else C
                
                change_val = C - prev_C
                change_pct = (change_val / prev_C) * 100
                trend_text, color_class, arrow = ("偏多", "trend-bullish", "🔼") if C > ma5 else ("偏空", "trend-bearish", "🔽") if C < ma5 else ("盤整", "trend-neutral", "➖")
                
                df = df.reset_index()
                all_data[name] = df
                summary_list.append({
                    "name": name, "current": C, "change_pct": change_pct, "change_val": change_val,
                    "open": O, "high": H, "low": L, "volume": V,
                    "trend_text": trend_text, "color_class": color_class, "arrow": arrow,
                    "ma5": ma5, "ma10": ma10, "ma20": ma20
                })
        except Exception: pass
    return summary_list, all_data

@st.cache_data(ttl=1800)
def fetch_institutional_data():
    """抓取跨日三大法人籌碼"""
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

@st.cache_data(ttl=600)
def fetch_global_for_analysis():
    """專門為動態評析抓取全球重要指數與原物料，避免干擾主畫面卡片"""
    tickers = {"S&P 500": "^GSPC", "那斯達克": "^IXIC", "日經": "^N225", "韓國": "^KS11", "原油": "CL=F", "黃金": "GC=F"}
    res = {}
    for name, symbol in tickers.items():
        try:
            hist = yf.Ticker(symbol).history(period="5d")
            if len(hist) >= 2:
                c = float(hist['Close'].iloc[-1])
                p = float(hist['Close'].iloc[-2])
                res[name] = {"current": c, "change_pct": (c - p) / p * 100}
        except: pass
    return res

def generate_dynamic_analysis(summary, inst_data, global_data):
    # 提取台股大盤資料
    taiex_item = next((x for x in summary if "加權" in x['name']), None)
    if taiex_item:
        O, H, L, C = taiex_item['open'], taiex_item['high'], taiex_item['low'], taiex_item['current']
        chg, pct = taiex_item['change_val'], taiex_item['change_pct']
        vol = taiex_item['volume']
        ma5, ma20 = taiex_item['ma5'], taiex_item['ma20']
        
        # 判斷趨勢詞彙
        up_down = "上漲" if chg > 0 else "下跌"
        ma5_rel = "站上" if C >= ma5 else "跌破"
        ma20_rel = "守穩" if C >= ma20 else "失守"
        
        # 處理 Yahoo Finance 的大盤成交量 (單位為股數，轉為億，若為0則顯示暫無)
        vol_str = f"{vol / 100000000:,.0f} 億 (Yahoo原始單位)" if vol > 0 else "暫無即時量能資料"
        
        analysis = f"📉 **大盤實況與技術面觀察**：\n今日加權指數開盤為 {O:,.0f} 點，盤中最高來到 {H:,.0f} 點，最低至 {L:,.0f} 點。**終場收在 {C:,.0f} 點，{up_down} {abs(chg):,.0f} 點 ({pct:+.2f}%)**，成交量為 {vol_str}。"
        analysis += f" 從技術面來看，目前加權指數已{ma5_rel}短期周線 ({ma5:,.0f})，且{ma20_rel}中期生命線即月線 ({ma20:,.0f})，多空交戰激烈。\n\n"
    else:
        analysis = "📉 **大盤實況**：目前暫無加權指數連線資料。\n\n"

    # 籌碼面分析
    if inst_data:
        total_net = inst_data['合計']
        analysis += f"📊 **三大法人實質籌碼 (資料日期: {inst_data['日期']})**：\n法人整體呈現 **{'買超' if total_net > 0 else '賣超'} {abs(total_net):.1f} 億元**。"
        analysis += f" 其中，外資**{'買超' if inst_data['外資'] > 0 else '賣超'} {abs(inst_data['外資']):.1f} 億**，投信**{'買超' if inst_data['投信'] > 0 else '賣超'} {abs(inst_data['投信']):.1f} 億**，自營商**{'買超' if inst_data['自營商'] > 0 else '賣超'} {abs(inst_data['自營商']):.1f} 億**。"
        if inst_data['外資'] > 0 and inst_data['投信'] > 0: analysis += " 土洋法人同步站在買方，為台股底氣提供實質的籌碼支撐。\n\n"
        elif inst_data['外資'] < 0 and inst_data['投信'] > 0: analysis += " 籌碼面呈現「外資提款、投信低接」的土洋對作態勢。\n\n"
        elif inst_data['外資'] < 0 and inst_data['投信'] < 0: analysis += " 內外資同步撤出，籌碼面極度弱勢，需嚴控資金水位。\n\n"
        else: analysis += "\n\n"
    else: analysis += "📊 **籌碼面**：目前暫無法人買賣超資料連線。\n\n"

    # 全球與原物料連動分析
    analysis += f"🌍 **國際股市與大宗商品動態**：\n"
    if "S&P 500" in global_data and "那斯達克" in global_data:
        analysis += f"美股方面，S&P 500 指數收在 {global_data['S&P 500']['current']:,.0f} 點 ({global_data['S&P 500']['change_pct']:+.2f}%)，那斯達克指數收在 {global_data['那斯達克']['current']:,.0f} 點 ({global_data['那斯達克']['change_pct']:+.2f}%)。整體美股走勢對台股高科技與半導體板塊具有關鍵的指引作用。 "
    if "日經" in global_data and "韓國" in global_data:
        analysis += f"亞洲鄰國股市部分，日經指數目前為 {global_data['日經']['current']:,.0f} 點 ({global_data['日經']['change_pct']:+.2f}%)，韓國 KOSPI 指數為 {global_data['韓國']['current']:,.0f} 點 ({global_data['韓國']['change_pct']:+.2f}%)。 "
    if "原油" in global_data and "黃金" in global_data:
        analysis += f"\n原物料與避險指標方面，最新原油報價為 {global_data['原油']['current']:.2f} 美元/桶 ({global_data['原油']['change_pct']:+.2f}%)，黃金報價為 {global_data['黃金']['current']:,.1f} 美元/盎司 ({global_data['黃金']['change_pct']:+.2f}%)。若黃金走強通常反映市場避險情緒升溫，而油價波動則會牽動全球的通膨預期與利率決策方向。"

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

# --- 🚀 ETF 專屬資料抓取與多執行緒函數 ---
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
            if divs.index.tz is not None:
                one_year_ago = pd.Timestamp.now(tz=divs.index.tz) - pd.DateOffset(days=365)
            else:
                one_year_ago = pd.Timestamp.now() - pd.DateOffset(days=365)
            ttm_div = float(divs[divs.index >= one_year_ago].sum())
        
        div_yield = (ttm_div / current_price) * 100 if current_price > 0 else 0.0
        
        etf_type = "市值/主題型"
        if "B" in ticker or "債" in name: etf_type = "債券型"
        elif "主動" in name: etf_type = "主動型"
        elif "高" in name or "息" in name or "收益" in name: etf_type = "高股息"
        
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

@st.cache_data(ttl=1800, show_spinner=False)
def run_all_etfs_multithread():
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_etf = {executor.submit(fetch_single_etf, t, n): (t, n) for t, n in FULL_ETF_LIST.items()}
        for future in concurrent.futures.as_completed(future_to_etf):
            data = future.result()
            if data: results.append(data)
    return sorted(results, key=lambda x: x["即時殖利率(%)"], reverse=True)


# --- 側邊欄 ---
st.sidebar.title("📊 儀表板選單")
page = st.sidebar.radio("請選擇模組：", [
    "🇹🇼 台灣市場 (台股)", 
    "🌐 全球市場 (總經)", 
    "📂 產業及趨勢主題池", 
    "🔍 潛力股自動篩選",
    "💰 即時 ETF 殖利率與人氣模組"
])

st.sidebar.markdown("---")
st.sidebar.subheader("➕ 自訂觀察標的")
st.sidebar.caption("輸入代碼 (例：純數字 2317，或 NVDA)：")
new_ticker = st.sidebar.text_input("輸入台股/美股代碼:", key="ticker_input").strip().upper()

if st.sidebar.button("加入標的"):
    if new_ticker:
        search_str = f"{new_ticker}.TW" if new_ticker.isdigit() else new_ticker
        
        found_full_name = new_ticker
        all_twse = fetch_all_twse_tickers()
        
        for t in all_twse:
            if t.startswith(search_str):
                found_full_name = t
                break
                
        if found_full_name == new_ticker:
            for t_code, t_name in FULL_ETF_LIST.items():
                if t_code.startswith(search_str):
                    found_full_name = f"{t_code} {t_name}"
                    break
                    
        if found_full_name == new_ticker and new_ticker.isdigit():
            found_full_name = f"{new_ticker}.TW"
            
        if found_full_name not in st.session_state.custom_tickers:
            st.session_state.custom_tickers.append(found_full_name)
            if found_full_name not in st.session_state.stock_pool: 
                st.session_state.stock_pool.append(found_full_name)
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


# ==========================================
# 網頁主內容區塊
# ==========================================
if page == "🇹🇼 台灣市場 (台股)":
    st.title("🇹🇼 台股核心實況儀表板")
    st.markdown("---")
    
    # 取得台股大盤資料、籌碼資料、與國際重要指數供評析使用
    tw_indicators = {"加權指數 (TAIEX)": "^TWII", "櫃買指數 (OTC)": "^TWOII", "台積電 (2330)": "2330.TW", "美元/台幣 (匯率)": "TWD=X", "費城半導體 (SOX)": "^SOX"}
    summary, history = fetch_data(tw_indicators)
    inst_data = fetch_institutional_data()
    global_data = fetch_global_for_analysis()
    
    if summary:
        st.subheader("🧠 實況數據動態評析")
        dynamic_text = generate_dynamic_analysis(summary, inst_data, global_data)
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #4a90e2; margin-bottom: 30px;'>{dynamic_text}</div>", unsafe_allow_html=True)
        st.subheader("📊 核心指標監控")
        render_cards(summary, history)

elif page == "🌐 全球市場 (總經)":
    st.title("🌐 全球市場儀表板")
    st.markdown("---")
    global_indicators = {"VIX (恐慌指數)": "^VIX", "DXY (美元指數)": "DX-Y.NYB", "Crude Oil (原油)": "CL=F", "Gold (黃金)": "GC=F", "10Y Yield (殖利率)": "^TNX"}
    summary, history = fetch_data(global_indicators)
    if summary: render_cards(summary, history)

elif page == "📂 產業及趨勢主題池":
    st.title("📂 全新產業鏈與趨勢主題分類清單")
    st.markdown("已更新為最精細的市場區塊與未來趨勢主題。一鍵匯入自動篩選機，捕捉主流板塊的資金輪動！")
    st.markdown("---")
    for industry_name, stocks in INDUSTRY_STOCKS.items():
        with st.expander(f"{industry_name} ({len(stocks)} 檔)"):
            st.write("包含標的：", ", ".join(stocks))
            if st.button(f"將此板塊匯入篩選器", key=f"add_{industry_name}"):
                for s in stocks:
                    if s not in st.session_state.stock_pool: st.session_state.stock_pool.append(s)
                st.success(f"匯入成功！請前往「潛力股自動篩選」執行策略。")

elif page == "🔍 潛力股自動篩選":
    st.title("🔍 多維度技術面篩選機 (支援全市場)")
    st.markdown("---")
    
    st.info("💡 **進階功能**：一鍵連線 API 抓取全市場上市股票 (包含中文名稱)。")
    if st.button("📥 一鍵載入「全市場台股」", type="primary"):
        with st.spinner("正在連線 API 獲取全市場代碼與名稱..."):
            all_tickers = fetch_all_twse_tickers()
            if all_tickers:
                st.session_state.stock_pool = list(set(st.session_state.stock_pool + all_tickers))
                st.success(f"✅ 成功載入！目前篩選池共有 {len(st.session_state.stock_pool)} 檔標的。")
            else: st.error("❌ 無法連線至 API，請稍後再試。")

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
            if len(current_pool) > 100: st.warning(f"⚠️ 即將掃描 {len(current_pool)} 檔股票。預計需要數分鐘，請耐心等候。")
            
            st.markdown("### 📊 篩選結果報告")
            results = {"ma_breakout": [], "vol_up": [], "hammer": []}
            bar = st.progress(0)
            status_text = st.empty()
            
            for idx, ticker_display in enumerate(current_pool):
                status_text.text(f"正在掃描 {ticker_display} ... ({idx+1}/{len(current_pool)})")
                try:
                    yf_ticker = ticker_display.split()[0]
                    df = yf.Ticker(yf_ticker).history(period=period, interval=interval)
                    if len(df) >= 20:
                        df['MA5'], df['MA10'], df['MA20'] = df['Close'].rolling(5).mean(), df['Close'].rolling(10).mean(), df['Close'].rolling(20).mean()
                        curr, prev = df.iloc[-1], df.iloc[-2]
                        C, O, H, L, V, prev_V = curr['Close'], curr['Open'], curr['High'], curr['Low'], curr['Volume'], prev['Volume']
                        ma5, ma10, ma20 = curr['MA5'], curr['MA10'], curr['MA20']
                        
                        if (C > O) and ((min(O, C) - L) > abs(C - O)*2) and ((H - max(O, C)) < abs(C - O)*0.5): results["hammer"].append(f"**{ticker_display}** (現價: {C:.2f})")
                        if (C > prev['Close']) and (V > prev_V * 1.5): results["vol_up"].append(f"**{ticker_display}** (現價: {C:.2f})")
                        max_ma, min_ma = max(ma5, ma10, ma20), min(ma5, ma10, ma20)
                        if (((max_ma - min_ma) / min_ma) < 0.03) and (C > max_ma) and (prev['Close'] < max_ma): results["ma_breakout"].append(f"**{ticker_display}** (現價: {C:.2f})")
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
    st.title("💰 終極版台股 ETF 即時運算引擎")
    st.markdown("系統正運用 **多執行緒 (Multi-threading)** 技術，向 Yahoo Finance 引擎以並發方式閃電抓取您專屬 ETF 庫的「今日現價」、「過去一年配息總額」以及「最新成交量」，並即時算出最精準的年化殖利率！")
    st.info("💡 **操作提示**：點擊表格上方的標題（例如：`即時殖利率(%)` 或 `今日成交量(張)`），系統就會自動幫您由高到低排序！")
    st.markdown("---")
    
    with st.spinner(f"⚡ 正在透過多執行緒引擎閃電抓取您專屬 ETF 庫的即時股價與配息資料... (約需 10~15 秒)"):
        etf_data = run_all_etfs_multithread()
        
    if etf_data:
        df_etf = pd.DataFrame(etf_data)
        
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
        st.error("暫時無法取得 ETF 即時資料，請稍後重試。")
        
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 底部共用區塊 (自訂名單 + 數據更新時間 + ETF操作提示)
# ==========================================
if page in ["🇹🇼 台灣台灣市場 (台股)", "🌐 全球市場 (總經)"] and st.session_state.custom_tickers:
    st.markdown("---")
    st.subheader("🎯 自訂觀察名單")
    custom_dict = {ticker: ticker for ticker in st.session_state.custom_tickers}
    c_summary, c_history = fetch_data(custom_dict)
    if c_summary: render_cards(c_summary, c_history)

st.markdown("---")

# 轉換為台灣時間 (UTC+8)
tw_tz = datetime.timezone(datetime.timedelta(hours=8))
current_time = datetime.datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M:%S')
st.caption(f"📅 數據最後更新 (台灣當地時間): {current_time}")

# ETF 操作提示與附註，獨立顯示在頁尾
if page == "💰 即時 ETF 殖利率與人氣模組":
    st.caption("💡 **ETF 操作提示**：選擇高股息 ETF 時，除了看『年化配息率』，更重要的是看『今日成交量』與『五日均量』，成交量的爆發才是最準確的人氣溫度計！")
    st.caption("註：年化殖利率採計過去 365 天內該檔 ETF 實際發放的除息總和，除以 Yahoo Finance 即時現價而得。新上市未滿一年或近期未配息之 ETF，數值可能為 0。")

st.caption("免責聲明：技術分析與數據計算結果僅供參考，不構成任何投資建議。全市場資料由 FinMind 介接，報價由 Yahoo Finance 提供。")
