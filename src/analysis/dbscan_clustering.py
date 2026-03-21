import pandas as pd
import numpy as np
import os
import sys
import io
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
import seaborn as sns

# --- ĐƯỜNG DẪN TỰ ĐỘNG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def perform_dbscan_clustering(df_out, features=None, eps=0.5, min_samples=3):
    if features is None:
        # Tập trung vào các đặc trưng có độ tin cậy cao từ API
        features = ["price_change_24h", "market_cap", "total_volume"]

    df_working = df_out.copy()
    
    # Chuyển đổi sang số và xử lý log scale cho các cột giá trị lớn để DBSCAN hoạt động tốt hơn
    for col in ["market_cap", "total_volume"]:
        df_working[col] = pd.to_numeric(df_working[col], errors='coerce').fillna(0)
        # Sử dụng log(x+1) để thu hẹp khoảng cách dữ liệu cực lớn
        df_working[f"log_{col}"] = np.log1p(df_working[col])

    log_features = ["price_change_24h", "log_market_cap", "log_total_volume"]
    df_cluster = df_working[log_features].dropna()

    if len(df_cluster) == 0:
        print(" Không có dữ liệu đủ để phân cụm.")
        df_working["cluster_dbscan"] = -1
        return df_working

    # Chuẩn hóa
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_cluster)

    # DBSCAN: eps nhỏ thì khắt khe, eps lớn thì dễ dãi
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(X_scaled)

    # Gán nhãn
    df_working["cluster_dbscan"] = -1  # Mặc định là noise
    df_working.loc[df_cluster.index, "cluster_dbscan"] = labels

    # Thống kê
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    print(f" DBSCAN hoàn tất: Tìm thấy {n_clusters} cụm và {n_noise} điểm dị biệt (Noise).")

    return df_working

def plot_dbscan_clusters(df_out):
    if "cluster_dbscan" not in df_out.columns:
        raise ValueError("Thiếu nhãn cụm. Hãy chạy clustering trước!")

    plt.figure(figsize=(12, 8))
    sns.set(style="whitegrid")

    # 1. Vẽ các cụm bình thường
    core_samples = df_out[df_out["cluster_dbscan"] != -1]
    if not core_samples.empty:
        sns.scatterplot(
            data=core_samples,
            x="price_change_24h",
            y="market_cap",
            hue="cluster_dbscan",
            palette="viridis",
            s=80,
            alpha=0.6,
            edgecolor='w'
        )

    # 2. Vẽ các điểm Noise
    noise_samples = df_out[df_out["cluster_dbscan"] == -1]
    if not noise_samples.empty:
        sns.scatterplot(
            data=noise_samples,
            x="price_change_24h",
            y="market_cap",
            color="red",
            label="Dị biệt (Outliers)",
            marker="x",
            s=100,
            alpha=0.9
        )

    plt.yscale("log")
    plt.xlabel("Biến động giá 24h (%)")
    plt.ylabel("Vốn hóa thị trường (USD - Log scale)")
    plt.title("PHÂN TÍCH ĐIỂM DỊ BIỆT THỊ TRƯỜNG (DBSCAN)", fontsize=16, fontweight='bold')
    plt.legend(title="Phân loại", loc='upper right')
    
    # Lưu ảnh
    # plt.savefig(os.path.join(BASE_DIR, "Data", "dbscan_outliers.png"))
    plt.show()

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if not os.path.exists(DATA_FILE):
        print(" Không thấy file data!")
    else:
        df_raw = pd.read_csv(DATA_FILE)
        latest_time = df_raw["time_collected"].max()
        df_latest = df_raw[df_raw["time_collected"] == latest_time].copy()
        
        # Chạy clustering
        df_clustered = perform_dbscan_clustering(df_latest, eps=0.5, min_samples=3)
        
        # In danh sách các đồng coin "dị biệt" (Noise)
        outliers = df_clustered[df_clustered["cluster_dbscan"] == -1]
        print("\n Một số đồng coin có hành vi dị biệt (Top 5):")
        print(outliers[['symbol', 'price_change_24h', 'market_cap']].head())
        
        plot_dbscan_clusters(df_clustered)