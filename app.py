import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 設定網頁標題與排版
st.set_page_config(page_title="全球市場五大核心儀表板", layout="wide")
st.title("🌐 全球市場五大核心儀表板 (即時監控)")
st.markdown("觀察指標：**Oil (成本)｜DXY (資金)｜VIX (情緒)｜Gold (避險)｜Yield (利率)**")
st.markdown("---")

# 定義五大指標對應的 Yahoo Finance 代碼
indicators = {
    "VIX (恐慌指數)": "^VIX",
    "DXY (美元指數)": "DX-Y.NYB",
    "Crude Oil (原油)": "CL=F",
    "Gold (黃金)": "GC=F",
    "10Y Yield (美債殖利率)": "^TNX"
}

# 抓取資料與計算均線的函數
@st.cache_data(ttl=300) # 每5分鐘重新抓取一次資料
def fetch_data():
    results = []
    for name, ticker in indicators.items():
        try:
            # 抓取過去一個月的資料來計算均線
            data = yf.Ticker(ticker).history(period="1mo")
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                prev_price = data['Close'].iloc[-2]
                ma5 = data['Close'].rolling(window=5).mean().iloc[-1]
                ma10 = data['Close'].rolling(window=10).mean().iloc[-1]
                
                # 計算趨勢與漲跌幅
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100
                trend = "🔼 偏多" if current_price > ma5 else ("🔽 偏空" if current_price < ma5 else "➖ 盤整")
                
                results.append({
                    "指標": name,
                    "現值": round(current_price, 2),
                    "漲跌幅 (%)": f"{round(change_pct, 2)}%",
                    "短線趨勢": trend,
                    "5日均線": round(ma5, 2),
                    "10日均線": round(ma10, 2)
                })
        except Exception as e:
            st.error(f"無法抓取 {name} 的資料: {e}")
    return pd.DataFrame(results)

# 載入並顯示數據表格
df = fetch_data()
st.subheader("📊 即時數據與均線狀態")
st.dataframe(df, use_container_width=True, hide_index=True)

# --- 綜合評析邏輯 ---
st.markdown("---")
st.subheader("🧠 初步綜合評析")

# 提取各指標現值與10日均線進行邏輯判斷
try:
    vix_val = df.loc[df['指標'] == 'VIX (恐慌指數)', '現值'].values[0]
    vix_ma10 = df.loc[df['指標'] == 'VIX (恐慌指數)', '10日均線'].values[0]
    
    dxy_val = df.loc[df['指標'] == 'DXY (美元指數)', '現值'].values[0]
    dxy_ma10 = df.loc[df['指標'] == 'DXY (美元指數)', '10日均線'].values[0]
    
    oil_val = df.loc[df['指標'] == 'Crude Oil (原油)', '現值'].values[0]
    oil_ma10 = df.loc[df['指標'] == 'Crude Oil (原油)', '10日均線'].values[0]
    
    gold_val = df.loc[df['指標'] == 'Gold (黃金)', '現值'].values[0]
    gold_ma10 = df.loc[df['指標'] == 'Gold (黃金)', '10日均線'].values[0]
    
    yield_val = df.loc[df['指標'] == '10Y Yield (美債殖利率)', '現值'].values[0]
    yield_ma10 = df.loc[df['指標'] == '10Y Yield (美債殖利率)', '10日均線'].values[0]

    # 評析一：市場情緒與避險 (VIX + Gold)
    if vix_val > vix_ma10 and gold_val > gold_ma10:
        st.warning("⚠️ **避險情緒升溫：** VIX 與黃金同步站上均線，市場正為潛在風險支付保險費，資金明顯流向避險資產，建議降低風險曝險。")
    elif vix_val < vix_ma10 and gold_val < gold_ma10:
        st.success("🟢 **風險偏好良好：** VIX 處於相對低檔，市場情緒穩定，有利於風險資產（如股市）表現。")
    else:
        st.info("⚖️ **情緒觀望中：** VIX 與黃金走勢分歧，市場情緒處於轉換期或等待新數據指引。")

    # 評析二：資金流動性 (DXY + Yield)
    if dxy_val > dxy_ma10 and yield_val > yield_ma10:
        st.error("📉 **流動性收緊壓力：** 美元強勢且殖利率攀升，全球資金有回流美國及債市的跡象，新興市場與股市估值面臨壓力。")
    elif dxy_val < dxy_ma10 and yield_val < yield_ma10:
        st.success("🌊 **資金動能充沛：** 美元轉弱且資金成本（殖利率）下降，有利於資金外溢至股市及非美市場。")
    else:
        st.info("🔄 **資金流動中性：** 美元與殖利率未見同步方向，資金可能正在板塊間輪動，而非整體大進大出。")

    # 評析三：通膨與成本 (Oil)
    if oil_val > oil_ma10:
        st.warning("🛢️ **成本壓力觀察：** 油價站上均線。需留意是需求擴張帶動，還是供給衝擊。若伴隨殖利率上升，需警惕通膨死灰復燃引發的央行緊縮擔憂。")
    else:
        st.info("🛢️ **成本壓力溫和：** 油價未見強勢反轉，企業成本與通膨壓力暫時可控。")

except Exception as e:
    st.error("數據不足，無法生成完整評析。")

st.markdown("---")
st.caption("免責聲明：本儀表板數據由 Yahoo Finance 提供，分析結果僅供市場觀察參考，不構成任何投資建議。市場瞬息萬變，請搭配其他總經數據綜合判斷。")