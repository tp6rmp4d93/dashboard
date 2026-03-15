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
    .stTitle { font-size: 2rem !important; font-weight: bold; }
    .stMarkdown p { font-size: 1.1rem; line-height: 1; }
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
    min_text = alt.Chart(min_df).mark_text(
        align='center', baseline='top', dy=10, color='#555', fontSize=12, fontWeight='bold'
    ).encode(x='Date:T', y='Close:Q', text='Label')
    
    # 將所有圖層疊加 (稍微增加高度以容納文字)
    chart = alt.layer(base_line, max_point, max_text, min_point, min_text).properties(
        height=100 
    ).configure_view(
        strokeWidth=0
    )
    return chart

# --- 執行資料抓取 ---
summary, history = fetch_all_data()

if summary:
    # ==========================================
    # 區塊一：初步綜合評析 (移至最上方)
    # ==========================================
    st.subheader("🧠 初步綜合評析")
    try:
        def get_val(name, key):
            return next((x[key] for x in summary if x['name'] == name), "盤整")
        
        vix_trend = get_val("VIX (恐慌指數)", "trend_text")
        gold_trend = get_val("Gold (黃金)", "trend_text")
        dxy_trend = get_val("DXY (美元指數)", "trend_text")
        yield_trend = get_val("10Y Yield (殖利率)", "trend_text")
        oil_trend = get_val("Crude Oil (原油)", "trend_text")

        analysis_text = ""

        # 情緒與避險
        if vix_trend == "偏多" and gold_trend == "偏多":
            analysis_text += "⚠️ **<span class='trend-bullish'>避險情緒顯著升溫：</span>** 恐慌指數 VIX 與黃金同步走強。市場正為潛在風險支付高額保險費，資金明顯流向避險資產，這對一般股市通常是強烈警訊。<br><br>"
        elif vix_trend == "偏空" and gold_trend == "偏空":
            analysis_text += "🟢 **<span class='trend-bearish'>風險偏好良好：</span>** VIX 處於均線下方，市場情緒穩定；黃金也未獲避險資金大量青睞。這是有利於風險資產（如股市）持續表現的環境。<br><br>"
        else:
            analysis_text += "⚖️ **市場情緒觀望中：** VIX 與黃金走勢分歧，市場情緒處於轉換期或等待下一個明確數據指引，短期波動可能增加。<br><br>"

        # 資金流動性
        if dxy_trend == "偏多" and yield_trend == "偏多":
            analysis_text += "📉 **<span class='trend-bullish'>全球流動性收緊：</span>** 美元與美債殖利率同步站上均線。美元走強會壓制新興市場與大宗商品，殖利率上升則提高資金成本，對成長股估值造成壓力。<br><br>"
        elif dxy_trend == "偏空" and yield_trend == "偏空":
            analysis_text += "🌊 **<span class='trend-bearish'>資金動能充沛：</span>** 美元走軟且利率下降。全球流動性環境趨於寬鬆，有利於資金外溢至股市、非美市場及原物料板塊。<br><br>"
        else:
            analysis_text += "🔄 **資金流動中性：** 美元與殖利率方向不一。代表資金可能正在市場板塊間（例如：防禦股與成長股）輪動，而非整體系統性的撤資或進駐。<br><br>"

        # 通膨與成本
        if oil_trend == "偏多":
            analysis_text += "🛢️ **成本壓力觀察：** 油價趨勢偏多。需留意若是供給衝擊導致，可能引發通膨死灰復燃引發央行緊縮擔憂；若是需求擴張導致，則代表經濟仍強韌。"
        else:
            analysis_text += "🛢️ **成本壓力溫和：** 油價未見強勢反轉，企業成本與通膨壓力暫時可控。"

        st.markdown(f"<div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #4a90e2; margin-bottom: 30px;'>{analysis_text}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"數據收集不全，無法生成評析: {e}")


    # ==========================================
    # 區塊二：各指標詳細數據卡片與走勢線
    # ==========================================
    st.subheader("📊 各項指標詳細數據 (近30日走勢)")
    
    for i in range(len(summary)):
        item = summary[i]
        hist_df = history[item['name']]
        
        with st.container():
            precision = ".1f" if "DXY" in item['name'] or "VIX" in item['name'] else ".2f"
            
            html_content = f"""
            <div class="indicator-card">
                <div class="card-title">{item['name']}</div>
                <div style="display: flex; align-items: baseline; flex-wrap: wrap;">
                    <span class="current-value {item['color_class']}">{item['current']:{precision}}</span>
                    <span class="{item['color_class']}" style="font-size: 1.2rem; font-weight: bold; margin-right: 15px;">
                        {item['arrow']} {item['change_pct']:.2f}% (日)
                    </span>
                    <span class="ma-text">
                        趨勢：<span class="{item['color_class']}" style="font-weight:bold;">{item['trend_text']}</span>
                    </span>
                </div>
                <div class="ma-text" style="margin-top: 5px;">
                    5日均線: {item['ma5']:{precision}} ｜ 10日均線: {item['ma10']:{precision}}
                </div>
            </div>
            """
            st.markdown(html_content, unsafe_allow_html=True)
            
            # 繪製含有高低點標籤的圖表
            st.altair_chart(plot_sparkline_with_labels(hist_df, item['color_class']), use_container_width=True)
            st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

st.markdown("---")
st.caption(f"數據最後更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (每5分鐘自動更新)")
st.caption("免責聲明：本儀表板數據由 Yahoo Finance 提供。紅色/🔼 代表站上5日均線(偏多)，綠色/🔽 代表跌破5日均線(偏空)。")
            
