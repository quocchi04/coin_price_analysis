import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import io
import os

# --- TU DONG XAC DINH DUONG DAN ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def process_supply_data(df):
    # Ep kieu du lieu so
    df = df.copy()
    target_cols = ["circulating_supply", "total_supply"]
    for col in target_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Loc bo du lieu loi
    df_supply = df.dropna(subset=target_cols)
    df_supply = df_supply[df_supply["total_supply"] > 0].copy()
    
    if df_supply.empty:
        return None

    # Tinh ty le luu hanh
    df_supply['supply_ratio'] = df_supply['circulating_supply'] / df_supply['total_supply']
    df_supply['supply_ratio'] = np.clip(df_supply['supply_ratio'], 0, 1)
    
    return df_supply

def plot_supply_chart(df_supply, is_streamlit=False):
    fig = plt.figure(figsize=(10, 6))
    plt.hist(df_supply['supply_ratio'], bins=20, color='#3498db', edgecolor='white', alpha=0.8)
    
    plt.title('PHAN PHOI TY LE CUNG LUU HANH (CIRCULATING / TOTAL)', fontsize=14, fontweight='bold')
    plt.xlabel('Ty le (0.0: Moi phat hanh - 1.0: Da xa het)', fontsize=12)
    plt.ylabel('So luong dong coin', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    if is_streamlit:
        import streamlit as st
        st.pyplot(fig)
    else:
        plt.show()

# --- HAM NAY DE APP.PY GOI ---
def show(df):
    import streamlit as st
    st.write("### Phân tích xu hướng (Coin Trend Analysis)")
    
    latest_time = df['time_collected'].max()
    df_latest = df[df['time_collected'] == latest_time].copy()
    
    df_supply = process_supply_data(df_latest)
    
    if df_supply is not None:
        # Hien thi thong ke nhanh
        col1, col2, col3 = st.columns(3)
        col1.metric("Ty le cung TB", f"{df_supply['supply_ratio'].mean():.2%}")
        col2.metric("So coin phan tich", len(df_supply))
        col3.write(f"Snapshot: {latest_time}")
        
        # Ve bieu do
        plot_supply_chart(df_supply, is_streamlit=True)
        
        # In danh sach rui ro
        st.subheader("Top 10 Coin co rui ro lam phat cao (Cung thap)")
        top_low = df_supply[['symbol', 'name', 'supply_ratio']].sort_values('supply_ratio').head(10).copy()
        top_low['supply_ratio'] = top_low['supply_ratio'].apply(lambda x: f"{x:.2%}")
        st.table(top_low)
    else:
        st.error("Khong co du lieu cung cau hop le.")

# --- CHAY RIENG (TERMINAL) ---
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    if not os.path.exists(DATA_FILE):
        print(f"Khong tim thay file: {DATA_FILE}")
    else:
        df_all = pd.read_csv(DATA_FILE)
        latest_time = df_all['time_collected'].max()
        df_latest = df_all[df_all['time_collected'] == latest_time].copy()
        
        df_supply = process_supply_data(df_latest)
        if df_supply is not None:
            print(f"\nTy le cung trung binh: {df_supply['supply_ratio'].mean():.2%}")
            plot_supply_chart(df_supply, is_streamlit=False)