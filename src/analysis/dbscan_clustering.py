import pandas as pd
import numpy as np
import os
import sys
import io
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
import seaborn as sns

# --- DUONG DAN TU DONG ---
# Lay thu muc goc de tim file Data/crypto_full_data.csv
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def perform_dbscan_clustering(df_out, features=None, eps=0.5, min_samples=3):
    if features is None:
        features = ["price_change_24h", "market_cap", "total_volume"]

    df_working = df_out.copy()
    
    for col in ["market_cap", "total_volume"]:
        df_working[col] = pd.to_numeric(df_working[col], errors='coerce').fillna(0)
        df_working[f"log_{col}"] = np.log1p(df_working[col])

    log_features = ["price_change_24h", "log_market_cap", "log_total_volume"]
    df_cluster = df_working[log_features].dropna()

    if len(df_cluster) == 0:
        return df_working

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_cluster)

    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(X_scaled)

    df_working["cluster_dbscan"] = -1
    df_working.loc[df_cluster.index, "cluster_dbscan"] = labels

    return df_working

def plot_dbscan_clusters(df_out, is_streamlit=False):
    plt.figure(figsize=(12, 8))
    sns.set(style="whitegrid")

    # 1. Ve cac cum binh thuong
    core_samples = df_out[df_out["cluster_dbscan"] != -1]
    if not core_samples.empty:
        sns.scatterplot(
            data=core_samples, x="price_change_24h", y="market_cap",
            hue="cluster_dbscan", palette="viridis", s=80, alpha=0.6, edgecolor='w'
        )

    # 2. Ve cac diem Noise
    noise_samples = df_out[df_out["cluster_dbscan"] == -1]
    if not noise_samples.empty:
        sns.scatterplot(
            data=noise_samples, x="price_change_24h", y="market_cap",
            color="red", label="Di biet (Outliers)", marker="x", s=100, alpha=0.9
        )

    plt.yscale("log")
    plt.xlabel("Bien dong gia 24h (%)")
    plt.ylabel("Von hoa thi truong (USD - Log scale)")
    plt.title("PHAN TICH DIEM DI BIET THI TRUONG (DBSCAN)", fontsize=16, fontweight='bold')
    plt.legend(title="Phan loai", loc='upper right')
    
    # Neu la Streamlit thi dung st.pyplot, neu chay rieng thi plt.show
    if is_streamlit:
        import streamlit as st
        st.pyplot(plt)
    else:
        plt.show()

# --- HAM NAY DE APP.PY GOI ---
def show(df):
    import streamlit as st
    st.write("### Gom cụm DBSCAN (DBSCAN Clustering Analysis)")
    
    # Lay du lieu moi nhat giong code goc
    latest_time = df["time_collected"].max()
    df_latest = df[df["time_collected"] == latest_time].copy()
    
    # Chay clustering
    df_clustered = perform_dbscan_clustering(df_latest, eps=0.5, min_samples=3)
    
    # Ve len App
    plot_dbscan_clusters(df_clustered, is_streamlit=True)
    
    # Hien thi bang du lieu di biet
    outliers = df_clustered[df_clustered["cluster_dbscan"] == -1]
    st.write("Các dòng coin dị biệt (Outliers):")
    st.dataframe(outliers[['symbol', 'price_change_24h', 'market_cap']])

# --- CHAY RIENG (FILE DOC LAP) ---
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if not os.path.exists(DATA_FILE):
        print("Khong thay file data tai:", DATA_FILE)
    else:
        df_raw = pd.read_csv(DATA_FILE)
        latest_time = df_raw["time_collected"].max()
        df_latest = df_raw[df_raw["time_collected"] == latest_time].copy()
        
        df_clustered = perform_dbscan_clustering(df_latest, eps=0.5, min_samples=3)
        print("DBSCAN hoan tat.")
        plot_dbscan_clusters(df_clustered, is_streamlit=False)