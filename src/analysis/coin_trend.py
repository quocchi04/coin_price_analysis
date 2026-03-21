import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import io
import os

# --- TỰ ĐỘNG XÁC ĐỊNH ĐƯỜNG DẪN ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def setup_console_encoding():
    # Fix lỗi hiển thị tiếng Việt trên Terminal Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def analyze_supply_distribution():
    setup_console_encoding()
    
    if not os.path.exists(DATA_FILE):
        print(f" Không tìm thấy file dữ liệu tại: {DATA_FILE}")
        return

    try:
        # 1. Đọc dữ liệu
        df_all = pd.read_csv(DATA_FILE)
        
        # 2. Lấy dữ liệu mới nhất
        latest_time = df_all['time_collected'].max()
        df = df_all[df_all['time_collected'] == latest_time].copy()

        # 3. Ép kiểu dữ liệu số (Vô cùng quan trọng)
        # Nếu API trả về null hoặc chuỗi, code sẽ không bị crash
        target_cols = ["circulating_supply", "total_supply"]
        for col in target_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                print(f" Cảnh báo: Thiếu cột '{col}'. Hãy kiểm tra lại file collect_data.py")
                return

        # 4. Lọc bỏ các dòng không có dữ liệu cung hoặc cung bằng 0 (để tránh chia cho 0)
        df_supply = df.dropna(subset=target_cols)
        df_supply = df_supply[df_supply["total_supply"] > 0].copy()

        if df_supply.empty:
            print(" Không có đủ dữ liệu cung hợp lệ để phân tích.")
            return

        # 5. Tính tỷ lệ lưu hành (Supply Ratio)
        df_supply['supply_ratio'] = df_supply['circulating_supply'] / df_supply['total_supply']

        # Chuẩn hóa tỷ lệ (về khoảng 0 - 1)
        df_supply['supply_ratio'] = np.clip(df_supply['supply_ratio'], 0, 1)
        
        # 6. Thống kê
        print("\n THỐNG KÊ PHÂN PHỐI CUNG (SUPPLY)")
        print("="*40)
        print(f"Tổng số coin snapshot: {len(df)}")
        print(f"Số coin đủ dữ liệu:    {len(df_supply)}")
        print(f"Tỷ lệ cung trung bình: {df_supply['supply_ratio'].mean():.2%}")
        print(f"Độ lệch chuẩn:         {df_supply['supply_ratio'].std():.4f}")

        # 7. Phân nhóm
        bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
        labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
        df_supply['ratio_group'] = pd.cut(df_supply['supply_ratio'], bins=bins, labels=labels, include_lowest=True)
        
        print("\n PHÂN BỔ THEO NHÓM LƯU HÀNH:")
        print(df_supply['ratio_group'].value_counts().sort_index())
        
        # 8. Vẽ biểu đồ
        plt.figure(figsize=(10, 6))
        n, bins, patches = plt.hist(df_supply['supply_ratio'], bins=20, color='#3498db', edgecolor='white', alpha=0.8)
        
        plt.title('PHÂN PHỐI TỶ LỆ CUNG LƯU HÀNH (CIRCULATING / TOTAL)', fontsize=14, fontweight='bold')
        plt.xlabel('Tỷ lệ (0.0: Mới phát hành - 1.0: Đã xả hết)', fontsize=12)
        plt.ylabel('Số lượng đồng coin', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Lưu ảnh vào folder Data
        # save_path = os.path.join(BASE_DIR, "Data", "supply_distribution.png")
        # plt.savefig(save_path)
        # print(f"\n Đã lưu biểu đồ: {save_path}")
        plt.show()

        # 9. In danh sách rủi ro (Cung thấp = Dễ bị xả/Lạm phát cao)
        print("\n TOP 10 COIN CÓ TỶ LỆ LƯU HÀNH THẤP NHẤT (Rủi ro pha loãng):")
        print("-" * 60)
        top_low = df_supply[['symbol', 'name', 'supply_ratio']].sort_values('supply_ratio').head(10)
        # Chuyển sang % cho dễ đọc
        top_low['supply_ratio'] = top_low['supply_ratio'].apply(lambda x: f"{x:.2%}")
        print(top_low.to_string(index=False))

    except Exception as e:
        print(f" Lỗi hệ thống: {str(e)}")

if __name__ == "__main__":
    analyze_supply_distribution()