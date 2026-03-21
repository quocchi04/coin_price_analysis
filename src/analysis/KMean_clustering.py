import pandas as pd
import numpy as np
import os
import sys
import io
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns

# --- ĐƯỜNG DẪN TỰ ĐỘNG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def perform_kmeans_clustering(df_out, features=None, n_clusters=4):
    if features is None:
        # Chọn các đặc trưng quan trọng nhất để phân cụm
        features = ["current_price_usd", "price_change_24h", "market_cap", "total_volume"]

    # Kiểm tra và xử lý dữ liệu số
    df_working = df_out.copy()
    for col in features:
        if col not in df_working.columns:
            print(f" Cảnh báo: Thiếu cột {col}, sẽ bỏ qua đặc trưng này.")
            features.remove(col)
            continue
        df_working[col] = pd.to_numeric(df_working[col], errors='coerce').fillna(0)

    # Loại bỏ các dòng có giá trị vô lý (ví dụ vốn hóa = 0) để cụm đẹp hơn
    df_cluster_input = df_working[df_working['market_cap'] > 0][features]

    if len(df_cluster_input) < n_clusters:
        raise ValueError(f"Dữ liệu quá ít ({len(df_cluster_input)} dòng) để chia làm {n_clusters} cụm.")

    # Chuẩn hóa (Z-score Scaling)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_cluster_input)

    # Huấn luyện KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    # Gán nhãn cụm vào dataframe gốc
    df_working["cluster"] = -1 # Mặc định là -1 (không thuộc cụm nào)
    df_working.loc[df_cluster_input.index, "cluster"] = labels
    
    return df_working

def plot_kmeans_clusters(df_out):
    # Lọc bỏ các dòng không được phân cụm (cluster -1)
    df_plot = df_out[df_out["cluster"] != -1].copy()

    sns.set(style="whitegrid")
    plt.figure(figsize=(12, 8))

    # Vẽ biểu đồ: Trục X là Biến động giá, Trục Y là Vốn hóa (thang log)
    scatter = sns.scatterplot(
        data=df_plot,
        x="price_change_24h",
        y="market_cap",
        hue="cluster",
        style="cluster",
        palette="viridis",
        s=100,
        alpha=0.7
    )

    plt.yscale("log")
    plt.xlabel("Biến động giá 24h (%)", fontsize=12)
    plt.ylabel("Vốn hóa thị trường (USD - Log scale)", fontsize=12)
    plt.title("PHÂN CỤM THỊ TRƯỜNG CRYPTO (K-MEANS)", fontsize=16, fontweight='bold')
    
    # Chú thích các cụm (Dành cho báo cáo)
    plt.legend(title="Nhóm Cụm", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # Lưu biểu đồ
    plt.savefig(os.path.join(BASE_DIR, "Data", "kmeans_clusters.png"))
    print(f" Đã lưu biểu đồ phân cụm tại thư mục Data")
    plt.show()

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if not os.path.exists(DATA_FILE):
        print(f" Không tìm thấy file: {DATA_FILE}")
    else:
        df_raw = pd.read_csv(DATA_FILE)
        
        # Lấy mốc thời gian mới nhất
        latest_time = df_raw["time_collected"].max()
        df_latest = df_raw[df_raw["time_collected"] == latest_time].copy()
        
        print(f" Đang tiến hành phân cụm cho {len(df_latest)} đồng coin...")
        df_clustered = perform_kmeans_clustering(df_latest, n_clusters=4)
        
        # In thử số lượng coin trong mỗi cụm
        print("\n Thống kê số lượng mỗi cụm:")
        print(df_clustered['cluster'].value_counts().sort_index())
        
        plot_kmeans_clusters(df_clustered)