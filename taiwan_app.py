import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import datetime

# --- 網頁設定 ---
st.set_page_config(
    page_title="台股核心儀表板",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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

st.title("🇹🇼 台股五大核心儀表板")
st.markdown("觀察指標：**加權(大盤)｜櫃買(內資)｜台積電(權值)｜匯率(熱錢)｜費半(國際科技)**")
st.markdown("---")

# --- 定義台股專屬指標 ---
# 註：TWD=X 為美元兌台幣，數值上升代表台幣貶值
indicators = {
    "加權指數 (TAIEX)": "^TWII",
    "櫃買指數 (OTC)": "^TWOII",
    "台積電 (2330)": "2330.TW",
    "美元/台幣 (匯率)": "TWD=X",
    "費城半導體 (SOX)": "^SOX"
}

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
                
                # 台股習慣：現價大於5MA為偏多(紅)
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
    
    chart = alt.layer(base_line, max_point, max_text, min_point, min_text).properties(height=100).configure_view(strokeWidth=0)
    return chart

summary, history = fetch_all_data()

if summary:
    # ==========================================
    # 區塊一：台股專屬綜合評析
    # ==========================================
    st.subheader("🧠 盤勢綜合評析 (台股邏輯)")
    try:
        def get_val(name, key):
            return next((x[key] for x in summary if x['name'] == name), "盤整")
        
        taiex_trend = get_val("加權指數 (TAIEX)", "trend_text")
        otc_trend = get_val("櫃買指數 (OTC)", "trend_text")
        tsmc_trend = get_val("台積電 (2330)", "trend_text")
        twd_trend = get_val("美元/台幣 (匯率)", "trend_text")
        sox_trend = get_val("費城半導體 (SOX)", "trend_text")

        analysis_text = ""

        # 1. 內外資市場寬度 (大盤 vs 櫃買)
        if taiex_trend == "偏多" and otc_trend == "偏多":
            analysis_text += "📈 **<span class='trend-bullish'>內外資齊聚，健康輪動：</span>** 加權與櫃買指數同步站上均線。顯示大型權值股與中小型股皆有表現，市場信心充足，屬於較好操作的多頭環境。<br><br>"
        elif taiex_trend == "偏多" and otc_trend == "偏空":
            analysis_text += "⚠️ **<span class='trend-bearish'>拉積盤疑慮，提防賺指數賠差價：</span>** 大盤偏多但櫃買走弱。資金高度集中在台積電等少數權值股撐盤，中小型股反而遭到提款，個股操作難度極高。<br><br>"
        elif taiex_trend == "偏空" and otc_trend == "偏空":
            analysis_text += "📉 **<span class='trend-bearish'>覆巢之下無完卵：</span>** 大盤與櫃買同步弱勢。系統性風險較高，市場全面保守，建議提高現金水位或保持觀望。<br><br>"
        else:
            analysis_text += "⚖️ **板塊分歧，個股表現：** 大盤與中小型股步調不一，大盤可能受權值股壓抑，但部分題材股仍有發揮空間。<br><br>"

        # 2. 科技股與國際連動 (費半 vs 台積電)
        if sox_trend == "偏多" and tsmc_trend == "偏多":
            analysis_text += "🚀 **<span class='trend-bullish'>科技主升段：</span>** 費城半導體與台積電同步強勢，台股最大的引擎啟動！有利於半導體設備、IC設計與泛AI供應鏈的表現。<br><br>"
        elif sox_trend == "偏空" and tsmc_trend == "偏空":
            analysis_text += "🧊 **科技股面臨逆風：** 費半弱勢直接拖累台積電與電子股估值，由於電子股市值龐大，大盤短期難有顯著表現空間。<br><br>"

        # 3. 匯率與熱錢動能 (台幣匯率)
        # 邏輯反轉：匯率數值上升 = 台幣貶值 = 偏空；數值下降 = 台幣升值 = 偏多
        if twd_trend == "偏多":
            analysis_text += "💸 **外資匯出壓力：** 美元兌台幣走升（台幣貶值）且站上均線。這通常代表外資熱錢正在匯出台灣，大型權值股較易遭遇提款賣壓。"
        elif twd_trend == "偏空":
            analysis_text += "🌊 **熱錢湧入動能：** 美元兌台幣走跌（台幣強勢升值）且跌破均線。資金動能充沛，有利於外資順勢大買台股，推升指數。"

        st.markdown(f"<div style='background-color: #f9f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #4a90e2; margin-bottom: 30px;'>{analysis_text}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"數據收集不全，無法生成評析: {e}")

    # ==========================================
    # 區塊二：各指標詳細數據卡片
    # ==========================================
    st.subheader("📊 各項指標詳細數據 (近30日走勢)")
    
    for i in range(len(summary)):
        item = summary[i]
        hist_df = history[item['name']]
        
        with st.container():
            # 針對匯率跟費半調整小數點位數
            precision = ".2f" if "台積電" in item['name'] else ".2f"
            if "加權" in item['name'] or "櫃買" in item['name'] or "費城" in item['name']: precision = ".0f"
            
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
            
            st.altair_chart(plot_sparkline_with_labels(hist_df, item['color_class']), use_container_width=True)
            st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

st.markdown("---")
st.caption(f"數據最後更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (每5分鐘自動更新)")
st.caption("免責聲明：本儀表板數據由 Yahoo Finance 提供。紅色/🔼 代表站上5日均線(偏多)，綠色/🔽 代表跌破5日均線(偏空)。【註：匯率數值上升代表台幣貶值，屬資金流出訊號】")