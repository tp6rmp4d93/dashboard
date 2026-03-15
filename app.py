import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import datetime

# --- 網頁設定 ---
st.set_page_config(
    page_title="全球市場儀表板",
    layout="wide", # 雖然是 wide，但在手機上會自動堆疊
    initial_sidebar_state="collapsed"
)

# --- 自定義 CSS (放大字體、手機優化、調整顏色) ---
st.markdown("""
    <style>
    /* 全域放大字體 */
    html, body, [class*="css"] {
        font-size: 18px;
    }
    
    /* 標題放大 */
    .stTitle {
        font-size: 2.5rem !important;
        font-weight: bold;
    }
    
    /* 綜合評析文字放大 */
    .stMarkdown p {
        font-size: 1.1rem;
        line-height: 1.6;
    }

    /* 指標卡片容器 */
    .indicator-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #ddd;
    }
    
    /* 卡片標題 */
    .card-title {
        font-size: 1.3rem;
        color: #555;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    /* 現值數字超放大 */
    .current-value {
        font-size: 3rem !important;
        font-weight: bold;
        margin-right: 10px;
    }
    
    /* 趨勢與均線文字 */
    .ma-text {
        font-size: 1rem;
        color: #666;
    }
    
    /* 定義顏色：偏多紅，偏空綠 (台股習慣) */
    .trend-bullish { color: #FF4B4B !important; } /* 紅色 */
    .trend-bearish { color: #00C853 !important; } /* 綠色 */
    .trend-neutral { color: #777 !important; } /* 灰色 */

    /* 隱藏預設的 DataFrame 顯示，我們自己畫卡片 */
    [data-testid="stDataFrame"] { display: none; }
    
    /* 行動端優化 padding */
    @media (max-width: 640px) {
        .reportview-container .main .block-container{
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .current-value { font-size: 2.5rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌐 全球市場儀表板")
st.markdown("觀察指標：**Oil (成本)｜DXY (資金)｜VIX (情緒)｜Gold (避險)｜Yield (利率)**")
st.markdown("---")

# 定義五大指標對應的 Yahoo Finance 代碼
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
            # 改用 yf.Ticker().history 抓取過去 3 個月的資料，避開新版 download 的格式問題
            df = yf.Ticker(ticker).history(period="3mo")
            
            if not df.empty:
                # 計算均線
                df['MA5'] = df['Close'].rolling(window=5).mean()
                df['MA10'] = df['Close'].rolling(window=10).mean()
                
                # 取得最新一筆與上一筆數據，並強制轉為純數字 (float)
                current_price = float(df['Close'].iloc[-1])
                prev_price = float(df['Close'].iloc[-2])
                ma5_val = float(df['MA5'].iloc[-1])
                ma10_val = float(df['MA10'].iloc[-1])
                
                # 計算漲跌
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100
                
                # --- 核心邏輯：判定趨勢與顏色 ---
                if current_price > ma5_val:
                    trend_text = "偏多"
                    color_class = "trend-bullish" # 紅色
                    arrow = "🔼"
                elif current_price < ma5_val:
                    trend_text = "偏空"
                    color_class = "trend-bearish" # 綠色
                    arrow = "🔽"
                else:
                    trend_text = "盤整"
                    color_class = "trend-neutral"
                    arrow = "➖"
                
                # 重新設定 index 以利後續畫圖
                df = df.reset_index()
                all_data[name] = df # 儲存完整歷史用於畫圖
                
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

# --- 繪製走勢線 (Sparkline) 的函數 ---
def plot_sparkline(df, color_class):
    # 設定圖表顏色
    line_color = '#FF4B4B' if color_class == 'trend-bullish' else '#00C853'
    if color_class == 'trend-neutral': line_color = '#777'
    
    # 準備最近 30 天的資料
    plot_df = df.tail(30).reset_index()
    
    # 使用 Altair 繪製輕量化圖表
    chart = alt.Chart(plot_df).mark_line(
        interpolate='basis', # 讓線條平滑
        strokeWidth=3
    ).encode(
        x=alt.X('Date', axis=None), # 隱藏 X 軸
        y=alt.Y('Close', scale=alt.Scale(zero=False), axis=None), # 隱藏 Y 軸
        color=alt.value(line_color) # 設定線條顏色
    ).properties(
        height=70 # 設定高度，使其像是在字裡行間
    ).configure_view(
        strokeWidth=0 # 隱藏外框
    )
    return chart

# --- 主程式執行 ---
summary, history = fetch_all_data()

if summary:
    # 畫出卡片
    st.subheader("📊 即時市場儀表板")
    
    # 迭代每個指標，手動構建卡片 HTML
    for i in range(len(summary)):
        item = summary[i]
        hist_df = history[item['name']]
        
        # 使用 Container 包裹卡片和圖表
        with st.container():
            # 1. 數據文字部分 (使用 HTML 放大和配色)
            # DXY 和 VIX 顯示一位小數，其餘兩位
            precision = ".1f" if "DXY" in item['name'] or "VIX" in item['name'] else ".2f"
            
            html_content = f"""
            <div class="indicator-card">
                <div class="card-title">{item['name']}</div>
                <div style="display: flex; align-items: baseline; flex-wrap: wrap;">
                    <span class="current-value {item['color_class']}">
                        {item['current']:{precision}}
                    </span>
                    <span class="{item['color_class']}" style="font-size: 1.2rem; font-weight: bold; margin-right: 15px;">
                        {item['arrow']} {item['change_pct']:.2f}% (日)
                    </span>
                    <span class="ma-text">
                        趨勢：<span class="{item['color_class']}" style="font-weight:bold;">{item['trend_text']}</span>
                    </span>
                </div>
                <div class="ma-text" style="margin-top: 5px;">
                    5日均: {item['ma5']:{precision}} ｜ 10日均: {item['ma10']:{precision}}
                </div>
            </div>
            """
            st.markdown(html_content, unsafe_allow_html=True)
            
            # 2. 走勢線部分 (緊跟在卡片 HTML 後面)
            # 在手機上調整圖表位置
            st.altair_chart(plot_sparkline(hist_df, item['color_class']), use_container_width=True)
            
            # 卡片間距
            st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

    # --- 綜合評析邏輯 ---
    st.markdown("---")
    st.subheader("🧠 初步綜合評析")
    
    # 提取數據用於邏輯判斷
    try:
        def get_val(name, key):
            return next(x[key] for x in summary if x['name'] == name)
        
        vix_trend = get_val("VIX (恐慌指數)", "trend_text")
        gold_trend = get_val("Gold (黃金)", "trend_text")
        dxy_trend = get_val("DXY (美元指數)", "trend_text")
        yield_trend = get_val("10Y Yield (殖利率)", "trend_text")
        oil_trend = get_val("Crude Oil (原油)", "trend_text")

        # 分析文字放大顯示
        analysis_text = ""

        # 評析一：市場情緒與避險 (VIX + Gold)
        if vix_trend == "偏多" and gold_trend == "偏多":
            analysis_text += "⚠️ **<span class='trend-bullish'>避險情緒顯著升溫：</span>** 恐慌指數 VIX 與黃金同步走強。市場正為潛在風險支付高額保險費，資金明顯流向避險資產，這對一般股市通常是強烈警訊。<br><br>"
        elif vix_trend == "偏空" and gold_trend == "偏空":
            analysis_text += "🟢 **<span class='trend-bearish'>風險偏好良好：</span>** VIX 處於均線下方，市場情緒穩定；黃金也未獲資金青睞。這是有利於風險資產（如股市）持續表現的環境。<br><br>"
        else:
            analysis_text += "⚖️ **市場情緒觀望中：** VIX 與黃金走勢分歧，市場情緒處於轉換期或等待下一個明確數據指引，短期波動可能增加。<br><br>"

        # 評析二：資金流動性 (DXY + Yield)
        if dxy_trend == "偏多" and yield_trend == "偏多":
            analysis_text += "📉 **<span class='trend-bullish'>全球流動性收緊：</span>** 美元與美債殖利率同步站上均線。美元走強會壓制新興市場股票與大宗商品，殖利率上升則提高資金成本，對科技股等成長股估值造成壓力。<br><br>"
        elif dxy_trend == "偏空" and yield_trend == "偏空":
            analysis_text += "🌊 **<span class='trend-bearish'>資金動能充沛：</span>** 美元走軟且利率下降。全球流動性環境趨於寬鬆，有利於資金外溢至股市、非美市場及原物料。<br><br>"
        else:
            analysis_text += "🔄 **資金流動中性：** 美元與殖利率方向不一。這通常代表資金正在市場板塊間（例如：防禦股與成長股）輪動，而非整體系統性的撤資或進駐。<br><br>"

        # 評析三：通膨與成本 (Oil)
        if oil_trend == "偏多":
            analysis_text += "🛢️ **成本壓力觀察：** 油價趨勢偏多。需留意若是供給衝擊導致，可能引發通膨死灰復燃引發央行緊縮擔憂；若是需求擴張導致，則代表經濟仍強韌。"
        else:
            analysis_text += "🛢️ **成本壓力溫和：** 油價未見強勢反轉，企業成本與通膨壓力暫時可控。"

        # 顯示評析
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px;'>{analysis_text}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"數據收集不全，無法生成評析: {e}")

st.markdown("---")
st.caption(f"數據最後更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (每5分鐘自動更新)")
st.caption("免責聲明：本儀表板數據由 Yahoo Finance 提供。紅色/🔼 代表站上5日均線(偏多)，綠色/🔽 代表跌破5日均線(偏空)。")
