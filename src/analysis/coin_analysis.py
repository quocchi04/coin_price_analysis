import pandas as pd
import numpy as np
import sys
import io
import os
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "Data", "coin_analysis_result.csv")

def format_volume(volume):
    if pd.isna(volume) or volume == 0: return "0"
    if volume >= 1_000_000_000: return f"{volume/1_000_000_000:.1f}B"
    elif volume >= 1_000_000: return f"{volume/1_000_000:.1f}M"
    return f"{volume:,.0f}"

def find_abnormal_volumes(df, threshold=2):
    if len(df) < 2: return pd.Series(False, index=df.index)
    log_volumes = np.log(df['total_volume'].replace(0, 1))
    return log_volumes > (log_volumes.mean() + threshold * log_volumes.std())

def rank_coins():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if not os.path.exists(DATA_FILE):
        print(" Không thấy file data!")
        return
    
    df = pd.read_csv(DATA_FILE)
    latest_data = df[df['time_collected'] == df['time_collected'].max()].copy()
    
    # Lọc dữ liệu (Lấy Top 10 mỗi loại để biểu đồ không bị rối)
    high_growth = latest_data[latest_data['price_change_24h'] > 0].nlargest(10, 'price_change_24h')
    abnormal_vol = latest_data[find_abnormal_volumes(latest_data)].nlargest(10, 'total_volume')

    # --- VẼ BIỂU ĐỒ ---
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle(f'PHÂN TÍCH THỊ TRƯỜNG CRYPTO ({latest_data["time_collected"].iloc[0]})', fontsize=16, fontweight='bold')

    # Biểu đồ 1: Tăng trưởng giá
    if not high_growth.empty:
        sns.barplot(ax=axes[0], x='price_change_24h', y='name', data=high_growth, palette='Greens_r')
        axes[0].set_title('Top 10 Coin Tăng Giá Mạnh Nhất (24h %)', fontsize=14)
        axes[0].set_xlabel('% Thay đổi')
    else:
        axes[0].text(0.5, 0.5, 'Không có coin nào tăng giá mạnh', ha='center')

    # Biểu đồ 2: Volume bất thường
    if not abnormal_vol.empty:
        sns.barplot(ax=axes[1], x='total_volume', y='name', data=abnormal_vol, palette='Oranges_r')
        axes[1].set_title('Top 10 Coin có Volume Bất Thường (USD)', fontsize=14)
        axes[1].set_xlabel('Volume (USD)')
        # Format lại trục X cho dễ đọc
        axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_volume(x)))
    else:
        axes[1].text(0.5, 0.5, 'Không có volume bất thường', ha='center')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Lưu ảnh để dán vào báo cáo
    # chart_path = os.path.join(BASE_DIR, "Data", "market_analysis_chart.png")
    # plt.savefig(chart_path)
    # print(f" Đã lưu biểu đồ tại: {chart_path}")
    
    plt.show()

if __name__ == "__main__":
    rank_coins()