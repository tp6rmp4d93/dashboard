import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import datetime

# --- 網頁設定 (設定側邊欄預設展開) ---
st.set_page_config(
    page_title="專業市場儀表板",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 自定義 CSS ---
st.markdown("""
    <style>
    html, body, [class*="css"] { font-size: 16px; }
    .stTitle { font-size: 2rem !important; font-weight: bold; }
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

# --- 建立側邊欄選單 ---
st.sidebar.title("📊 儀表板選單")
page = st.sidebar.radio(
    "請選擇欲觀察的市場：",
    ["🇹🇼 台灣市場(台股)", "🌐 全球市場"]
)
st.sidebar.markdown("---")
st.sidebar.caption("使用說明：\n切換選單即可載入不同市場的專屬指標與分析邏輯。")

# --- 共用函數：抓取資料 (依照傳入的市場類型載入不同指標) ---
@st.cache_data(ttl=300)
def fetch_market_data(market_type):
    if market_type == "global":
        indicators = {
            "VIX (恐慌指數)": "^VIX",
            "DXY (美元指數)": "DX-Y.NYB",
            "Crude Oil (原油)": "CL=F",
            "Gold (黃金)": "GC=F",
            "10Y Yield (殖利率)": "^TNX"
        }
    else:
        indicators = {
            "加權指數 (TAIEX)": "^TWII",
            "櫃買指數 (OTC)": "^TWOII",
            "台積電 (2330)": "2330.TW",
            "美元/台幣 (匯率)": "TWD=X",
            "費城半導體 (SOX)": "^SOX"
        }
        
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
                    "name": name, "current": current_price, "change_pct": change_pct,
                    "trend_text": trend_text, "color_class": color_class, "arrow": arrow,
                    "ma5": ma5_val, "ma10": ma10_val
                })
        except Exception as e:
            st.error(f"資料抓取失敗 {name}: {e}")
            
    return summary_list, all_data

# --- 共用函數：繪製走勢線 ---
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

# ==========================================
# 頁面一：全球市場邏輯
# ==========================================
if page == "🌐 全球市場 (總經)":
    st.title("🌐 全球市場儀表板")
    st.markdown("觀察指標：**Oil (成本)｜DXY (資金)｜VIX (情緒)｜Gold (避險)｜Yield (利率)**")
    st.markdown("---")
    
    summary, history = fetch_market_data("global")
    
    if summary:
        st.subheader("🧠 總經綜合評析")
        try:
            def get_val(name, key): return next((x[key] for x in summary if x['name'] == name), "盤整")
            vix_trend = get_val("VIX (恐慌指數)", "trend_text")
            gold_trend = get_val("Gold (黃金)", "trend_text")
            dxy_trend = get_val("DXY (美元指數)", "trend_text")
            yield_trend = get_val("10Y Yield (殖利率)", "trend_text")
            oil_trend = get_val("Crude Oil (原油)", "trend_text")

            analysis_text = ""
            if vix_trend == "偏多" and gold_trend == "偏多":
                analysis_text += "⚠️ **<span class='trend-bullish'>避險情緒顯著升溫：</span>** 恐慌指數 VIX 與黃金同步走強。資金明顯流向避險資產，對股市通常是強烈警訊。<br><br>"
            elif vix_trend == "偏空" and gold_trend == "偏空":
                analysis_text += "🟢 **<span class='trend-bearish'>風險偏好良好：</span>** VIX 均線下方，市場情緒穩定；黃金也未獲青睞。有利於風險資產表現。<br><br>"
            else:
                analysis_text += "⚖️ **市場情緒觀望中：** VIX 與黃金走勢分歧，市場情緒處於轉換期或等待下一個明確數據指引。<br><br>"

            if dxy_trend == "偏多" and yield_trend == "偏多":
                analysis_text += "📉 **<span class='trend-bullish'>全球流動性收緊：</span>** 美元與美債殖利率同步站上均線。美元強勢壓制新興市場，殖利率上升對成長股估值造成壓力。<br><br>"
            elif dxy_trend == "偏空" and yield_trend == "偏空":
                analysis_text += "🌊 **<span class='trend-bearish'>資金動能充沛：</span>** 美元走軟且利率下降。全球流動性環境趨於寬鬆。<br><br>"
            else:
                analysis_text += "🔄 **資金流動中性：** 美元與殖利率方向不一，代表資金可能正在市場板塊間輪動。<br><br>"

            if oil_trend == "偏多":
                analysis_text += "🛢️ **成本壓力觀察：** 油價趨勢偏多。需留意是否引發通膨死灰復燃引發央行緊縮擔憂。"
            else:
                analysis_text += "🛢️ **成本壓力溫和：** 油價未見強勢反轉，企業成本與通膨壓力暫時可控。"

            st.markdown(f"<div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #4a90e2; margin-bottom: 30px;'>{analysis_text}</div>", unsafe_allow_html=True)
        except Exception as e: st.error(f"評析生成失敗: {e}")

        st.subheader("📊 各項指標詳細數據 (近30日走勢)")
        for item in summary:
            precision = ".1f" if "DXY" in item['name'] or "VIX" in item['name'] else ".2f"
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
# 頁面二：台股市場邏輯
# ==========================================
elif page == "🇹🇼 台灣市場 (台股)":
    st.title("🇹🇼 台股核心儀表板")
    st.markdown("觀察指標：**加權(大盤)｜櫃買(內資)｜台積電(權值)｜匯率(熱錢)｜費半(國際科技)**")
    st.markdown("---")
    
    summary, history = fetch_market_data("taiwan")
    
    if summary:
        st.subheader("🧠 盤勢綜合評析 (台股邏輯)")
        try:
            def get_val(name, key): return next((x[key] for x in summary if x['name'] == name), "盤整")
            taiex_trend = get_val("加權指數 (TAIEX)", "trend_text")
            otc_trend = get_val("櫃買指數 (OTC)", "trend_text")
            tsmc_trend = get_val("台積電 (2330)", "trend_text")
            twd_trend = get_val("美元/台幣 (匯率)", "trend_text")
            sox_trend = get_val("費城半導體 (SOX)", "trend_text")

            analysis_text = ""
            if taiex_trend == "偏多" and otc_trend == "偏多":
                analysis_text += "📈 **<span class='trend-bullish'>內外資齊聚，健康輪動：</span>** 加權與櫃買同步站上均線。大型權值與中小型股皆有表現，屬於較好操作的多頭環境。<br><br>"
            elif taiex_trend == "偏多" and otc_trend == "偏空":
                analysis_text += "⚠️ **<span class='trend-bearish'>拉積盤疑慮：</span>** 大盤偏多但櫃買走弱。資金高度集中少數權值股，中小型股遭提款，個股操作難度高。<br><br>"
            elif taiex_trend == "偏空" and otc_trend == "偏空":
                analysis_text += "📉 **<span class='trend-bearish'>覆巢之下無完卵：</span>** 大盤與櫃買同步弱勢。系統性風險較高，建議提高現金水位。<br><br>"
            else:
                analysis_text += "⚖️ **板塊分歧：** 大盤與中小型股步調不一，部分題材股仍有發揮空間。<br><br>"

            if sox_trend == "偏多" and tsmc_trend == "偏多":
                analysis_text += "🚀 **<span class='trend-bullish'>科技主升段：</span>** 費半與台積電同步強勢，有利於半導體設備、IC設計與泛AI供應鏈表現。<br><br>"
            elif sox_trend == "偏空" and tsmc_trend == "偏空":
                analysis_text += "🧊 **科技股逆風：** 費半弱勢直接拖累台積電與電子股估值，大盤短期難有表現空間。<br><br>"

            if twd_trend == "偏多":
                analysis_text += "💸 **外資匯出壓力：** 美元兌台幣走升（貶值）。通常代表外資熱錢匯出台灣，大型權值股易遇提款賣壓。"
            elif twd_trend == "偏空":
                analysis_text += "🌊 **熱錢湧入動能：** 美元兌台幣走跌（升值）。資金動能充沛，有利於推升指數。"

            st.markdown(f"<div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #4a90e2; margin-bottom: 30px;'>{analysis_text}</div>", unsafe_allow_html=True)
        except Exception as e: st.error(f"評析生成失敗: {e}")

        st.subheader("📊 各項指標詳細數據 (近30日走勢)")
        for item in summary:
            precision = ".0f" if "加權" in item['name'] or "櫃買" in item['name'] or "費城" in item['name'] else ".2f"
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

# 頁尾共用聲明
st.markdown("---")
st.caption(f"數據最後更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (每5分鐘自動更新)")
st.caption("免責聲明：本儀表板數據由 Yahoo Finance 提供。紅色/🔼 代表站上5日均線(偏多)，綠色/🔽 代表跌破5日均線(偏空)。")
