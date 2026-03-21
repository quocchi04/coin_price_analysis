import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys
import io

# --- ĐƯỜNG DẪN TỰ ĐỘNG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def run_correlation():
    # Fix hiển thị Tiếng Việt
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if not os.path.exists(DATA_FILE):
        print(" Không tìm thấy file dữ liệu!")
        return

    df = pd.read_csv(DATA_FILE)
    
    # 1. Lấy dữ liệu mới nhất
    latest_time = df['time_collected'].max()
    df_latest = df[df['time_collected'] == latest_time].copy()

    # 2. Chọn các cột số để phân tích
    # Phân tích mối quan hệ giữa các biến số của 500 đồng coin
    cols = ['current_price_usd', 'market_cap', 'total_volume', 'price_change_24h']
    
    # Chuyển đổi sang kiểu số và bỏ qua các dòng lỗi
    for col in cols:
        df_latest[col] = pd.to_numeric(df_latest[col], errors='coerce')
    
    analysis_df = df_latest[cols].dropna()

    # 3. Tính ma trận tương quan (Pearson Correlation)
    corr_matrix = analysis_df.corr()

    print("\n MA TRẬN TƯƠNG QUAN GIỮA CÁC CHỈ SỐ (Correlation Matrix):")
    print(corr_matrix.round(3))

    # 4. Vẽ biểu đồ Heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='RdYlGn', center=0, fmt=".2f")
    plt.title('Bản đồ nhiệt tương quan giữa các đặc trưng Crypto', fontsize=15)
    
    # Lưu ảnh vào thư mục Data
    # plt.savefig(os.path.join(BASE_DIR, "Data", "correlation_heatmap.png"))
    # print(f"\n Đã lưu biểu đồ Heatmap tại thư mục Data")
    
    # 5. Phân tích thêm: Scatter Plot (Tương quan giữa Market Cap và Volume)
    plt.figure(figsize=(10, 6))
    sns.regplot(x='market_cap', y='total_volume', data=analysis_df, scatter_kws={'alpha':0.5})
    plt.xscale('log')
    plt.yscale('log')
    plt.title('Mối liên hệ giữa Vốn hóa và Khối lượng giao dịch (Log Scale)')
    plt.show()

if __name__ == "__main__":
    run_correlation()