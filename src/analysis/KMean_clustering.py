import pandas as pd
import numpy as np
import os
import sys
import io
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns

# --- DUONG DAN TU DONG ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def perform_kmeans_clustering(df_out, features=None, n_clusters=4):
    if features is None:
        features = ["current_price_usd", "price_change_24h", "market_cap", "total_volume"]

    df_working = df_out.copy()
    
    # Kiem tra va xu ly du lieu so
    valid_features = []
    for col in features:
        if col in df_working.columns:
            df_working[col] = pd.to_numeric(df_working[col], errors='coerce').fillna(0)
            valid_features.append(col)

    # Loc bo cac dong co von hoa = 0 de bieu do dep hon
    df_cluster_input = df_working[df_working['market_cap'] > 0][valid_features]

    if len(df_cluster_input) < n_clusters:
        return df_working

    # Chuan hoa du lieu
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_cluster_input)

    # Huan luyen KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    # Gan nhan cum
    df_working["cluster"] = -1 
    df_working.loc[df_cluster_input.index, "cluster"] = labels
    
    return df_working

def plot_kmeans_clusters(df_out, is_streamlit=False):
    df_plot = df_out[df_out["cluster"] != -1].copy()
    if df_plot.empty:
        return

    sns.set(style="whitegrid")
    fig = plt.figure(figsize=(12, 8))

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
    plt.xlabel("Bien dong gia 24h (%)", fontsize=12)
    plt.ylabel("Von hoa thi truong (USD - Log scale)", fontsize=12)
    plt.title("PHAN CUM THI TRUONG CRYPTO (K-MEANS)", fontsize=16, fontweight='bold')
    plt.legend(title="Nhom Cum", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    if is_streamlit:
        import streamlit as st
        st.pyplot(fig)
    else:
        plt.show()

# --- HAM NAY DE APP.PY GOI ---
def show(df):
    import streamlit as st
    st.write("### Gom cụm K-Means (K-Means Clustering Analysis)")
    
    # Sidebar hoac Slider de chon so cum ngay tren App
    n_clusters = st.slider("Chọn số lượng cụm (K):", min_value=2, max_value=10, value=4)
    
    latest_time = df["time_collected"].max()
    df_latest = df[df["time_collected"] == latest_time].copy()
    
    # Chay phan cum
    df_clustered = perform_kmeans_clustering(df_latest, n_clusters=n_clusters)
    
    # Ve bieu do
    plot_kmeans_clusters(df_clustered, is_streamlit=True)
    
    # Thong ke so luong
    st.write("Thống kê số lượng coin mỗi cụm:")
    st.bar_chart(df_clustered['cluster'].value_counts().sort_index())

# --- CHAY RIENG (TERMINAL) ---
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if not os.path.exists(DATA_FILE):
        print(f"Khong tim thay file: {DATA_FILE}")
    else:
        df_raw = pd.read_csv(DATA_FILE)
        latest_time = df_raw["time_collected"].max()
        df_latest = df_raw[df_raw["time_collected"] == latest_time].copy()
        
        print(f"Đang phân cụm cho {len(df_latest)} dòng coin...")
        df_clustered = perform_kmeans_clustering(df_latest, n_clusters=4)
        print(df_clustered['cluster'].value_counts().sort_index())
        plot_kmeans_clusters(df_clustered, is_streamlit=False)