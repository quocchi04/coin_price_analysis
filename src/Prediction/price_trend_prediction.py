import pandas as pd
import numpy as np
import os
import sys
import io
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# --- ĐƯỜNG DẪN DỮ LIỆU ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def setup_console():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def prepare_data(df):
    # Sắp xếp theo thời gian
    df = df.sort_values(['id', 'time_collected'])
    
    # Tạo biến mục tiêu (Target): 1 nếu giá bước sau cao hơn bước trước, 0 nếu thấp hơn
    # Dùng hàm shift(-1) để lấy giá của tương lai đặt cạnh giá hiện tại
    df['next_price'] = df.groupby('id')['current_price_usd'].shift(-1)
    df['target'] = (df['next_price'] > df['current_price_usd']).astype(int)
    
    # Chọn các đặc trưng (Features) để học
    features = ['current_price_usd', 'market_cap', 'total_volume', 'price_change_24h']
    
    # Ép kiểu số và xóa bỏ dòng NaN (dòng cuối cùng của mỗi coin sẽ bị NaN vì ko có tương lai)
    for col in features:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df_ml = df.dropna(subset=features + ['target'])
    return df_ml[features], df_ml['target']

def run_prediction():
    setup_console()
    
    if not os.path.exists(DATA_FILE):
        print(" Không tìm thấy dữ liệu!")
        return

    df = pd.read_csv(DATA_FILE)
    
    # Kiểm tra lượng dữ liệu
    if len(df) < 100:
        print(f" Dữ liệu quá ít ({len(df)} dòng). Cần thêm dữ liệu để huấn luyện AI.")
        return

    print(" Đang chuẩn bị dữ liệu và huấn luyện mô hình Random Forest...")
    X, y = prepare_data(df)
    
    if len(X) < 10:
        print(" Không đủ mẫu sau khi xử lý. Hãy chạy collect_data.py thêm nhiều lần!")
        return

    # Chia dữ liệu: 80% để học, 20% để kiểm tra
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Khởi tạo mô hình Random Forest
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Dự đoán
    y_pred = model.predict(X_test)

    # --- KẾT QUẢ ---
    print("\n" + "="*40)
    print(" KẾT QUẢ DỰ BÁO XU HƯỚNG GIÁ")
    print("="*40)
    print(f"Độ chính xác (Accuracy): {accuracy_score(y_test, y_pred):.2%}")
    print("\n Chi tiết ma trận nhầm lẫn (Confusion Matrix):")
    print(confusion_matrix(y_test, y_pred))
    
    print("\n Tầm quan trọng của các chỉ số (Feature Importance):")
    importances = model.feature_importances_
    for i, feat in enumerate(X.columns):
        print(f"- {feat}: {importances[i]:.4f}")

    print("\n Dự báo hoàn tất.")

if __name__ == "__main__":
    run_prediction()