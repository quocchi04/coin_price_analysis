import pandas as pd
import requests
import time
from datetime import datetime
import os

# ===== 1. CẤU HÌNH ĐƯỜNG DẪN TỰ ĐỘNG =====
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "Data")
INPUT_FILE = os.path.join(DATA_DIR, "top_500_coin_ids_only.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "crypto_full_data.csv")

# ===== 2. CONFIG API =====
BATCH_SIZE = 50 
SLEEP_TIME = 20          # Nghỉ lâu một chút để CoinGecko không chặn IP bạn
MAX_RETRY = 3 
HEADERS = {"User-Agent": "Mozilla/5.0"}

def collect_data():
    print(f" Đang đọc danh sách coin từ: {INPUT_FILE}")
    
    try:
        df_ids = pd.read_csv(INPUT_FILE)
        coin_ids = df_ids["id"].tolist()
    except Exception as e:
        print(f" Lỗi đọc file: {e}")
        return

    all_data = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for i in range(0, len(coin_ids), BATCH_SIZE):
        batch = coin_ids[i:i+BATCH_SIZE]
        ids_str = ",".join(batch)
        print(f" Đang lấy dữ liệu batch {i//BATCH_SIZE + 1}...")

        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ids_str,
            "price_change_percentage": "24h"
        }

        success = False
        for attempt in range(MAX_RETRY):
            response = requests.get(url, params=params, headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                for coin in data:
                    all_data.append({
                        "id": coin.get("id"),
                        "name": coin.get("name"),
                        "symbol": coin.get("symbol"),
                        "current_price_usd": coin.get("current_price"),
                        "market_cap": coin.get("market_cap"),
                        "price_change_24h": coin.get("price_change_percentage_24h"),
                        "total_volume": coin.get("total_volume"),
                        "circulating_supply": coin.get("circulating_supply"),
                        "total_supply": coin.get("total_supply"),
                        "time_collected": now_str
                    })
                success = True
                break
            elif response.status_code == 429:
                print(" Bị giới hạn API, đang nghỉ 30s...")
                time.sleep(30)
            else:
                print(f" Lỗi {response.status_code}")
                time.sleep(5)

        time.sleep(SLEEP_TIME) # Nghỉ giữa các batch

    # Lưu dữ liệu
    df_out = pd.DataFrame(all_data)
    if os.path.exists(OUTPUT_FILE):
        df_old = pd.read_csv(OUTPUT_FILE)
        df_out = pd.concat([df_old, df_out], ignore_index=True).drop_duplicates()
    
    df_out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"✨ XONG! Đã lưu {len(df_out)} dòng vào {OUTPUT_FILE}")

if __name__ == "__main__":
    collect_data()