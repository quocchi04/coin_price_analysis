import pandas as pd
import numpy as np
import os
import sys
import io

# --- TU DONG XAC DINH DUONG DAN ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def rank_top_gainers_and_volume(df):
    # Dam bao cac cot so dung dinh dang
    df = df.copy()
    df["current_price_usd"] = pd.to_numeric(df["current_price_usd"], errors='coerce')
    df["total_volume"] = pd.to_numeric(df["total_volume"], errors='coerce')
    df["price_change_24h"] = pd.to_numeric(df["price_change_24h"], errors='coerce')
    df["time_collected"] = pd.to_datetime(df["time_collected"])

    # Lay thoi gian gan nhat
    latest_time = df["time_collected"].max()
    df_latest = df[df["time_collected"] == latest_time].copy()

    # 1. Top tang gia 24h
    top_gainers_24h = df_latest.sort_values("price_change_24h", ascending=False).head(10)

    # 2. Bien dong tu luc bat dau chay Tool
    df_first = df.sort_values("time_collected").groupby("id").first().reset_index()
    df_first = df_first[["id", "current_price_usd"]].rename(columns={"current_price_usd": "first_price"})
    
    df_rank = pd.merge(df_latest, df_first, on="id", how="left")
    df_rank["pct_change_total"] = (df_rank["current_price_usd"] - df_rank["first_price"]) / df_rank["first_price"] * 100
    top_total_gainers = df_rank.sort_values("pct_change_total", ascending=False).head(10)

    # 3. Top volume
    top_volume = df_latest.sort_values("total_volume", ascending=False).head(10)

    return top_gainers_24h, top_volume, top_total_gainers

# --- HAM HIEN THI CHO APP STREAMLIT ---
def show(df):
    import streamlit as st
    st.write("### Phân tích xếp hạng (Coin Ranking)")
    
    g_24h, vol, g_total = rank_top_gainers_and_volume(df)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 tăng giá 24h")
        st.dataframe(g_24h[["symbol", "price_change_24h", "current_price_usd"]])

    with col2:
        st.subheader("Top 10 Volume giao dịch")
        st.dataframe(vol[["symbol", "total_volume", "current_price_usd"]])

    st.subheader("Top 10 tăng giá từ lúc bắt đầu thu thập dữ liệu")
    if g_total["pct_change_total"].sum() == 0:
        st.info("Du lieu moi thu thap 1 lan, chua co bien dong thoi gian.")
    st.dataframe(g_total[["symbol", "name", "pct_change_total", "current_price_usd"]])

# --- CHAY RIENG (TERMINAL) ---
def display_rankings(top_24h, top_vol, top_total):
    print("\n" + "="*30)
    print(" TOP 10 TANG GIA 24H")
    print("="*30)
    print(top_24h[["symbol", "name", "price_change_24h"]].to_string(index=False))

    print("\n" + "="*30)
    print(" TOP 10 VOLUME")
    print("="*30)
    print(top_vol[["symbol", "name", "total_volume"]].to_string(index=False))

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if not os.path.exists(DATA_FILE):
        print(f"Khong tim thay file: {DATA_FILE}")
    else:
        df_raw = pd.read_csv(DATA_FILE)
        g_24h, vol, g_total = rank_top_gainers_and_volume(df_raw)
        display_rankings(g_24h, vol, g_total)