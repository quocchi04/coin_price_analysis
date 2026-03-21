import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import io
from sklearn.preprocessing import MinMaxScaler

# --- KIỂM TRA THƯ VIỆN ---
try:
    from tslearn.metrics import dtw
except ImportError:
    print(" Đang thiếu thư viện 'tslearn'. Hãy cài đặt: pip install tslearn")

# --- ĐƯỜNG DẪN DỮ LIỆU ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def setup_console():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def normalize_segment(segment):
    if len(segment) < 2: return segment
    scaler = MinMaxScaler()
    return scaler.fit_transform(segment)

def find_similar_patterns(df, coin_id, window_size=3, k=3):
    """
    SỬA LỖI: Luôn trả về 2 giá trị (matches, current_segment)
    """
    # Lọc dữ liệu cho đồng coin cụ thể
    df_coin = df[df["id"] == coin_id].sort_values("time_collected").copy()
    df_coin = df_coin.dropna(subset=["current_price_usd", "market_cap"])

    # CHỐT CHẶN 1: Nếu dữ liệu quá ít, trả về rỗng và None ngay
    if len(df_coin) < (window_size + 2):
        return [], None

    data = df_coin[["current_price_usd", "market_cap"]].values
    
    # Lấy đoạn dữ liệu hiện tại
    current_segment_raw = data[-window_size:]
    current_segment = normalize_segment(current_segment_raw)
    
    matches = []
    # CHỐT CHẶN 2: Quét dữ liệu quá khứ (không bao gồm đoạn hiện tại)
    # i chạy từ đầu đến sát đoạn current_segment
    for i in range(0, len(data) - window_size - 1):
        past_segment_raw = data[i : i + window_size]
        past_segment = normalize_segment(past_segment_raw)
        
        # Tính khoảng cách DTW
        dist = dtw(current_segment, past_segment)

        # Xem giá ngay sau đoạn quá khứ đó
        future_price = data[i + window_size, 0]
        base_price = data[i + window_size - 1, 0]
        future_return = (future_price - base_price) / (base_price + 1e-9)
        direction = "up" if future_return > 0 else "down"

        matches.append({
            "match_start_idx": i,
            "distance": dist,
            "future_return": future_return,
            "future_direction": direction,
            "past_segment": past_segment
        })

    # Sắp xếp theo độ tương đồng
    matches = sorted(matches, key=lambda x: x["distance"])
    return matches[:k], current_segment

def plot_matches(coin_id, matches, current_segment):
    if not matches or current_segment is None:
        print(" Không có đủ dữ liệu mẫu để vẽ biểu đồ.")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(current_segment[:, 0], label="Hiện tại (Giá)", color='black', linewidth=3)
    
    for i, m in enumerate(matches):
        plt.plot(m['past_segment'][:, 0], linestyle='--', 
                 label=f"Mẫu {i+1} (DTW={m['distance']:.2f}, Xu hướng: {m['future_direction']})")

    plt.title(f" Phân tích hình thái giá (DTW Matching): {coin_id}")
    plt.xlabel("Thời điểm (bước)")
    plt.ylabel("Giá đã chuẩn hóa (0-1)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

if __name__ == "__main__":
    setup_console()
    if os.path.exists(DATA_FILE):
        df_all = pd.read_csv(DATA_FILE)
        
        # Cấu hình tham số
        coin_to_check = "bitcoin"
        # Sửa window_size nhỏ lại (3) để dễ tìm thấy mẫu khi data còn ít
        W_SIZE = 3 
        
        print(f" Đang tìm kiếm mẫu hình tương đồng cho {coin_to_check}...")
        
        # THỰC THI
        results, current_seg = find_similar_patterns(df_all, coin_to_check, window_size=W_SIZE)
        
        if results and current_seg is not None:
            print(f" Tìm thấy {len(results)} mẫu tương đồng nhất:")
            for i, m in enumerate(results):
                print(f"   + Mẫu {i+1}: Giống tại index {m['match_start_idx']}, "
                      f"Biến động sau đó: {m['future_return']*100:.2f}% ({m['future_direction']})")
            plot_matches(coin_to_check, results, current_seg)
        else:
            print(f" Dữ liệu hiện tại chỉ có {len(df_all[df_all['id']==coin_to_check])} dòng.")
            print(f"   Cần ít nhất {W_SIZE * 2} dòng để so sánh. Hãy chạy collect_data.py thêm vài lần!")
    else:
        print(f" Không tìm thấy file: {DATA_FILE}")