"""
台幣匯率轉換 Streamlit 應用
"""

import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import time
from crawler import fetch_exchange_rates, clean_exchange_data, convert_currency

# 頁面配置
st.set_page_config(
    page_title="台幣匯率轉換",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("💱 台幣匯率轉換")

# 初始化 session state
if "exchange_data" not in st.session_state:
    st.session_state.exchange_data = []
if "last_update_time" not in st.session_state:
    st.session_state.last_update_time = None
if "last_fetch_time" not in st.session_state:
    st.session_state.last_fetch_time = datetime.now()


async def fetch_rates():
    """非同步獲取匯率"""
    try:
        raw_data = await fetch_exchange_rates()
        cleaned_data = clean_exchange_data(raw_data)
        return cleaned_data
    except Exception as e:
        st.error(f"爬蟲錯誤: {str(e)}")
        return []


import traceback


def update_exchange_rates():
    """更新匯率資料（含詳細錯誤顯示）"""
    try:
        raw_data = asyncio.run(fetch_exchange_rates())
        st.session_state.exchange_data = clean_exchange_data(raw_data)
        st.session_state.last_update_time = datetime.now()
        st.session_state.last_fetch_time = datetime.now()
        st.success("✅ 匯率已更新")
    except Exception as e:
        # 顯示詳細錯誤到 Streamlit UI，並在 console 打印 traceback
        tb = traceback.format_exc()
        st.error(f"更新失敗: {str(e)}")
        try:
            st.code(tb)
        except Exception:
            # 若在 st.code 顯示失敗，仍在 console 輸出
            pass
        print("--- 更新失敗 traceback ---")
        print(tb)
        # 常見原因提示
        st.warning("可能原因：未安裝 Playwright 瀏覽器或環境無法啟動 headless 瀏覽器。若使用 Playwright，請執行 `python -m playwright install` 並確保系統允許啟動瀏覽器；或檢查網路/代理設定與 crawl4ai 認證設定。")


# 頁面頂部：更新時間和手動更新按鈕
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if st.session_state.last_update_time:
        st.write(f"⏰ 最後更新: {st.session_state.last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.write("⏰ 尚未更新過")

with col3:
    if st.button("🔄 手動更新", use_container_width=True):
        update_exchange_rates()
        st.rerun()

# 自動更新邏輯（每 10 分鐘）
if st.session_state.last_fetch_time:
    time_diff = datetime.now() - st.session_state.last_fetch_time
    if time_diff.total_seconds() > 600:  # 10 分鐘 = 600 秒
        update_exchange_rates()
        st.rerun()

# 初次載入時獲取資料
if not st.session_state.exchange_data and st.session_state.last_update_time is None:
    update_exchange_rates()

# 主要內容：雙欄佈局
col_left, col_right = st.columns(2)

# ========== 左欄：匯率計算器 ==========
with col_left:
    st.subheader("💰 匯率計算器（台幣轉外幣）")
    
    if not st.session_state.exchange_data:
        st.info("⏸️ 暫停交易 - 暫無匯率資料可用")
    else:
        # 幣別選擇
        currencies = [item["幣別"] for item in st.session_state.exchange_data]
        selected_currency = st.selectbox("選擇幣別", currencies, key="currency_select")
        
        # 找出選中幣別的匯率
        selected_rate = None
        for item in st.session_state.exchange_data:
            if item["幣別"] == selected_currency:
                selected_rate = item
                break
        
        if selected_rate:
            # 顯示即期匯率
            st.metric("本行即期賣出", f"{selected_rate['本行即期賣出']}")
            
            # 輸入台幣金額
            twd_input = st.number_input(
                "輸入台幣金額 (TWD)",
                min_value=0,
                value=1000,
                step=100,
                key="twd_input"
            )
            
            # 計算轉換結果
            if twd_input >= 0:
                foreign_amount = convert_currency(twd_input, selected_rate["本行即期賣出"])
                st.metric(
                    f"轉換結果",
                    f"{foreign_amount:,.2f} {selected_currency}"
                )
            else:
                st.warning("請輸入有效的金額")

# ========== 右欄：匯率表 ==========
with col_right:
    st.subheader("📊 匯率資料表")
    
    if not st.session_state.exchange_data:
        st.info("⏸️ 暫停交易 - 暫無匯率資料可用")
    else:
        # 轉換為 DataFrame 顯示
        df = pd.DataFrame(st.session_state.exchange_data)
        
        # 格式化匯率欄位
        df["本行即期買入"] = df["本行即期買入"].apply(lambda x: f"{x:.4f}")
        df["本行即期賣出"] = df["本行即期賣出"].apply(lambda x: f"{x:.4f}")
        
        # 重新命名欄位以符合需求
        df.rename(columns={
            "幣別": "幣別",
            "本行即期買入": "買入",
            "本行即期賣出": "賣出"
        }, inplace=True)
        
        # 顯示表格
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.caption(f"共 {len(st.session_state.exchange_data)} 種可交易幣別")

# 頁面底部：自動刷新提示
st.divider()
st.caption("💡 提示：應用會自動每 10 分鐘更新一次匯率，或點擊「手動更新」按鈕立即刷新")
