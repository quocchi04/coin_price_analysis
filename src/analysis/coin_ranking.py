import pandas as pd
import os
import sys
import io

# --- TỰ ĐỘNG XÁC ĐỊNH ĐƯỜNG DẪN ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def rank_top_gainers_and_volume(df):
    # Đảm bảo các cột số đúng định dạng
    df["current_price_usd"] = pd.to_numeric(df["current_price_usd"], errors='coerce')
    df["total_volume"] = pd.to_numeric(df["total_volume"], errors='coerce')
    df["price_change_24h"] = pd.to_numeric(df["price_change_24h"], errors='coerce')
    df["time_collected"] = pd.to_datetime(df["time_collected"])

    # Lấy thời gian gần nhất trong dữ liệu
    latest_time = df["time_collected"].max()
    df_latest = df[df["time_collected"] == latest_time].copy()

    # Logic 1: Xếp hạng theo biến động 24h (Lấy trực tiếp từ API)
    top_gainers_24h = df_latest.sort_values("price_change_24h", ascending=False).head(10)

    # Logic 2: Xếp hạng theo biến động từ lúc bắt đầu chạy Tool
    df_first = df.sort_values("time_collected").groupby("id").first().reset_index()
    df_first = df_first[["id", "current_price_usd"]].rename(columns={"current_price_usd": "first_price"})
    
    df_rank = pd.merge(df_latest, df_first, on="id", how="left")
    df_rank["pct_change_total"] = (df_rank["current_price_usd"] - df_rank["first_price"]) / df_rank["first_price"] * 100
    
    top_total_gainers = df_rank.sort_values("pct_change_total", ascending=False).head(10)

    # Logic 3: Top volume
    top_volume = df_latest.sort_values("total_volume", ascending=False).head(10)

    return top_gainers_24h, top_volume, top_total_gainers

def display_rankings(top_24h, top_vol, top_total):
    print("\n" + "="*30)
    print(" TOP 10 TĂNG GIÁ TRONG 24H QUA (Dữ liệu API)")
    print("="*30)
    print(top_24h[["symbol", "name", "current_price_usd", "price_change_24h"]].to_string(index=False))

    print("\n" + "="*30)
    print(" TOP 10 TĂNG GIÁ TỪ LÚC BẮT ĐẦU THU THẬP")
    print("="*30)
    # Nếu pct_change_total toàn là 0 (do mới chạy 1 lần), nó sẽ báo cho bạn biết
    if top_total["pct_change_total"].sum() == 0:
        print("(Dữ liệu mới thu thập 1 lần, chưa có biến động theo thời gian)")
    print(top_total[["symbol", "name", "current_price_usd", "pct_change_total"]].to_string(index=False))

    print("\n" + "="*30)
    print(" TOP 10 COIN CÓ KHỐI LƯỢNG GIAO DỊCH CAO NHẤT")
    print("="*30)
    print(top_vol[["symbol", "name", "current_price_usd", "total_volume"]].to_string(index=False))

if __name__ == "__main__":
    # Fix hiển thị terminal
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if not os.path.exists(DATA_FILE):
        print(f" Không tìm thấy file dữ liệu tại: {DATA_FILE}")
    else:
        df_raw = pd.read_csv(DATA_FILE)
        g_24h, vol, g_total = rank_top_gainers_and_volume(df_raw)
        display_rankings(g_24h, vol, g_total)