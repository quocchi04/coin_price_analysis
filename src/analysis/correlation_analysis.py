import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys
import io

# --- DUONG DAN TU DONG ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def calculate_correlation(df):
    # 1. Lay du lieu moi nhat
    latest_time = df['time_collected'].max()
    df_latest = df[df['time_collected'] == latest_time].copy()

    # 2. Chon cac cot so de phan tich
    cols = ['current_price_usd', 'market_cap', 'total_volume', 'price_change_24h']
    
    # Chuyen doi sang kieu so
    for col in cols:
        df_latest[col] = pd.to_numeric(df_latest[col], errors='coerce')
    
    analysis_df = df_latest[cols].dropna()
    
    # 3. Tinh ma tran tuong quan
    corr_matrix = analysis_df.corr()
    return corr_matrix, analysis_df

def plot_heatmap(corr_matrix, is_streamlit=False):
    fig = plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='RdYlGn', center=0, fmt=".2f")
    plt.title('Ban do nhiet tuong quan giua cac dac trung Crypto', fontsize=15)
    
    if is_streamlit:
        import streamlit as st
        st.pyplot(fig)
    else:
        plt.show()

def plot_scatter(analysis_df, is_streamlit=False):
    fig = plt.figure(figsize=(10, 6))
    sns.regplot(x='market_cap', y='total_volume', data=analysis_df, scatter_kws={'alpha':0.5})
    plt.xscale('log')
    plt.yscale('log')
    plt.title('Moi lien he giua Von hoa va Khoi luong giao dich (Log Scale)')
    
    if is_streamlit:
        import streamlit as st
        st.pyplot(fig)
    else:
        plt.show()

# --- HAM NAY DE APP.PY GOI ---
def show(df):
    import streamlit as st
    st.write("### Phân tích tương quan (Correlation Analysis)")
    
    if df is not None and not df.empty:
        corr_matrix, analysis_df = calculate_correlation(df)
        
        st.write("#### 1. Ma tran tuong quan (Heatmap)")
        plot_heatmap(corr_matrix, is_streamlit=True)
        
        st.write("#### 2. Tuong quan Von hoa & Khoi luong (Scatter Plot)")
        plot_scatter(analysis_df, is_streamlit=True)
        
        with st.expander("Giai thich chi so tuong quan"):
            st.write("""
            - **1.0**: Tuong quan thuan hoan hao.
            - **0.0**: Khong co moi lien he tuyen tinh.
            - **-1.0**: Tuong quan nghich hoan hao.
            """)
    else:
        st.error("Khong co du lieu de phan tich.")

# --- CHAY RIENG (TERMINAL) ---
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if not os.path.exists(DATA_FILE):
        print("Khong tim thay file du lieu!")
    else:
        df_raw = pd.read_csv(DATA_FILE)
        corr, analysis = calculate_correlation(df_raw)
        print("\nMA TRAN TUONG QUAN:")
        print(corr.round(3))
        plot_heatmap(corr, is_streamlit=False)
        plot_scatter(analysis, is_streamlit=False)