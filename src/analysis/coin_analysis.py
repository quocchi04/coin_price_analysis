import pandas as pd
import numpy as np
import os
import sys
import io
import matplotlib.pyplot as plt
import seaborn as sns

# --- CAU HINH DUONG DAN ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def format_volume(volume):
    if pd.isna(volume) or volume == 0: return "0"
    if volume >= 1_000_000_000: return f"{volume/1_000_000_000:.1f}B"
    elif volume >= 1_000_000: return f"{volume/1_000_000:.1f}M"
    return f"{volume:,.0f}"

def find_abnormal_volumes(df, threshold=2):
    if len(df) < 2: return pd.Series(False, index=df.index)
    # Xu ly log volume de tim diem bat thuong
    volumes = df['total_volume'].replace(0, 1)
    log_volumes = np.log(volumes)
    return log_volumes > (log_volumes.mean() + threshold * log_volumes.std())

def plot_market_analysis(df_latest, is_streamlit=False):
    # Lay Top 10 moi loai
    high_growth = df_latest[df_latest['price_change_24h'] > 0].nlargest(10, 'price_change_24h')
    abnormal_vol = df_latest[find_abnormal_volumes(df_latest)].nlargest(10, 'total_volume')

    # --- VE BIEU DO ---
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    time_str = df_latest["time_collected"].iloc[0] if not df_latest.empty else "N/A"
    fig.suptitle(f'PHAN TICH THI TRUONG CRYPTO ({time_str})', fontsize=16, fontweight='bold')

    # Biểu đồ 1: Tăng trưởng giá
    if not high_growth.empty:
        sns.barplot(ax=axes[0], x='price_change_24h', y='name', data=high_growth, palette='Greens_r')
        axes[0].set_title('Top 10 Coin Tang Gia Manh Nhat (24h %)', fontsize=14)
        axes[0].set_xlabel('% Thay doi')
    else:
        axes[0].text(0.5, 0.5, 'Khong co du lieu tang gia', ha='center')

    # Biểu đồ 2: Volume bất thường
    if not abnormal_vol.empty:
        sns.barplot(ax=axes[1], x='total_volume', y='name', data=abnormal_vol, palette='Oranges_r')
        axes[1].set_title('Top 10 Coin co Volume Bat Thuong (USD)', fontsize=14)
        axes[1].set_xlabel('Volume (USD)')
        axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_volume(x)))
    else:
        axes[1].text(0.5, 0.5, 'Khong co volume bat thuong', ha='center')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    if is_streamlit:
        import streamlit as st
        st.pyplot(fig)
    else:
        plt.show()

# --- HAM NAY DE APP.PY GOI ---
def show(df):
    import streamlit as st
    st.write("### Phân tích chung (Coin Analysis)")
    
    if df is not None and not df.empty:
        # Lay du lieu moi nhat
        latest_time = df['time_collected'].max()
        df_latest = df[df['time_collected'] == latest_time].copy()
        
        # Ve bieu do len App
        plot_market_analysis(df_latest, is_streamlit=True)
        
        # Hien thi bang du lieu duoi bieu do
        st.write("Danh sách chi tiết:")
        st.dataframe(df_latest[['name', 'symbol', 'price_change_24h', 'total_volume']].nlargest(10, 'price_change_24h'))
    else:
        st.error("Khong co du lieu de hien thi.")

# --- CHAY RIENG (FILE DOC LAP) ---
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if not os.path.exists(DATA_FILE):
        print("Khong thay file data tai:", DATA_FILE)
    else:
        df_raw = pd.read_csv(DATA_FILE)
        if not df_raw.empty:
            latest_time = df_raw['time_collected'].max()
            df_latest = df_raw[df_raw['time_collected'] == latest_time].copy()
            print(f"Dang phan tich du lieu luc: {latest_time}")
            plot_market_analysis(df_latest, is_streamlit=False)
        else:
            print("File data rong.")