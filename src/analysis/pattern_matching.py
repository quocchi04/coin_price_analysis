import pandas as pd
import numpy as np
import os
import sys
import io
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

# Thu vien quan trong de so sanh hinh thai chuoi thoi gian
try:
    from tslearn.metrics import dtw
except ImportError:
    # Neu thieu thu vien, ham show se bao loi cho nguoi dung
    pass

# --- DUONG DAN TU DONG ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def normalize_segment(segment):
    if len(segment) < 2: return segment
    scaler = MinMaxScaler()
    return scaler.fit_transform(segment)

def find_similar_patterns(df, coin_id, window_size=3, k=3):
    # Loc du lieu cho dong coin cu the
    df_coin = df[df["id"] == coin_id].sort_values("time_collected").copy()
    df_coin = df_coin.dropna(subset=["current_price_usd", "market_cap"])

    if len(df_coin) < (window_size + 2):
        return [], None

    data = df_coin[["current_price_usd", "market_cap"]].values
    
    # Lay doan du lieu hien tai (cuoi cung)
    current_segment_raw = data[-window_size:]
    current_segment = normalize_segment(current_segment_raw)
    
    matches = []
    # Quet du lieu qua khu
    for i in range(0, len(data) - window_size - 1):
        past_segment_raw = data[i : i + window_size]
        past_segment = normalize_segment(past_segment_raw)
        
        # Tinh khoang cach DTW (cang nho cang giong)
        try:
            dist = dtw(current_segment, past_segment)
        except:
            continue

        # Xem bien dong gia ngay sau doan qua khu do
        future_price = data[i + window_size, 0]
        base_price = data[i + window_size - 1, 0]
        future_return = (future_price - base_price) / (base_price + 1e-9)
        direction = "Up" if future_return > 0 else "Down"

        matches.append({
            "match_start_idx": i,
            "distance": dist,
            "future_return": future_return,
            "future_direction": direction,
            "past_segment": past_segment
        })

    # Sap xep theo do tuong dong (distance nho nhat)
    matches = sorted(matches, key=lambda x: x["distance"])
    return matches[:k], current_segment

def plot_pattern_comparison(coin_id, matches, current_segment, is_streamlit=False):
    fig = plt.figure(figsize=(12, 6))
    # Ve doan hien tai
    plt.plot(current_segment[:, 0], label="Hien tai (Gia)", color='black', linewidth=4)
    
    # Ve cac doan qua khu tuong dong de so sanh
    for i, m in enumerate(matches):
        plt.plot(m['past_segment'][:, 0], linestyle='--', 
                 label=f"Mau {i+1} (DTW={m['distance']:.2f}, Sau do: {m['future_direction']})")

    plt.title(f"Phan tich hinh thai gia (DTW Matching): {coin_id}", fontsize=14, fontweight='bold')
    plt.xlabel("Buoc thoi gian")
    plt.ylabel("Gia chuan hoa (0-1)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    if is_streamlit:
        import streamlit as st
        st.pyplot(fig)
    else:
        plt.show()

# --- HAM NAY DE APP.PY GOI ---
def show(df):
    import streamlit as st
    st.write("### Nhận dạng hình thái (Pattern Matching)")
    
    # Kiem tra thu vien
    try:
        from tslearn.metrics import dtw
    except ImportError:
        st.error("Thieu thu vien 'tslearn'. Hay cai dat bang lenh: pip install tslearn")
        return

    # Chon coin de soi mau hinh
    coins = df['id'].unique()
    selected_coin = st.selectbox("Chon Coin de phan tich hinh thai:", coins)
    
    w_size = st.slider("Do dai cua mau (Window Size):", 3, 10, 3)
    
    results, current_seg = find_similar_patterns(df, selected_coin, window_size=w_size)
    
    if results and current_seg is not None:
        st.info(f"Tim thay {len(results)} doan trong qua khu co hinh thai gia giong voi hien tai.")
        
        # Ve bieu do so sanh
        plot_pattern_analysis = plot_pattern_comparison(selected_coin, results, current_seg, is_streamlit=True)
        
        # Bang du lieu du bao dua tren lich su
        st.write("#### Kết quả từ quá khứ:")
        res_df = pd.DataFrame(results)[["distance", "future_direction", "future_return"]]
        res_df["future_return"] = res_df["future_return"].apply(lambda x: f"{x:.2%}")
        st.table(res_df)
    else:
        st.warning(f"Khong du du lieu de so sanh mau hinh cho {selected_coin}. Can it nhat {w_size*2} dong du lieu.")

# --- CHAY RIENG (TERMINAL) ---
if __name__ == "__main__":
    if os.path.exists(DATA_FILE):
        df_raw = pd.read_csv(DATA_FILE)
        res, seg = find_similar_patterns(df_raw, "bitcoin", window_size=3)
        if res:
            plot_pattern_comparison("bitcoin", res, seg, is_streamlit=False)
        else:
            print("Khong du du lieu mau.")