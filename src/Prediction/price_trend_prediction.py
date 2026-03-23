import pandas as pd
import numpy as np
import os
import sys
import io
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import json
# --- ĐƯỜNG DẪN DỮ LIỆU ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "Data", "crypto_full_data.csv")

def setup_console():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def prepare_data(df):
    df = df.sort_values(['id', 'time_collected'])
    
    # 1. Thêm chỉ số biến động (Giá hiện tại so với trung bình 3 phiên trước)
    df['ma_3'] = df.groupby('id')['current_price_usd'].transform(lambda x: x.rolling(window=3).mean())
    df['diff_ma'] = df['current_price_usd'] - df['ma_3']
    
    # 2. Thêm lợi nhuận của phiên trước (Lag features)
    df['prev_return'] = df.groupby('id')['current_price_usd'].transform(lambda x: x.pct_change(fill_method=None))

    # Tạo target như cũ
    df['next_price'] = df.groupby('id')['current_price_usd'].shift(-1)
    df['target'] = (df['next_price'] > df['current_price_usd']).astype(int)
    
    # Thêm các đặc trưng mới vào Features
    features = ['current_price_usd', 'market_cap', 'total_volume', 'price_change_24h', 'diff_ma', 'prev_return']
    
    # Xử lý NaN phát sinh do rolling/pct_change
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
    # Lấy dữ liệu mới nhất của mỗi coin (dòng cuối cùng) để dự báo
    latest_data = X.tail(len(df['id'].unique())) 
    all_predictions = model.predict(latest_data)
    # ---  LƯU KẾT QUẢ CHO APP ---
    up_ratio = (all_predictions == 1).sum() / len(all_predictions)
    
    market_sentiment = "TĂNG" if up_ratio > 0.5 else "GIẢM"

    result_data = {
        "accuracy": accuracy_score(y_test, y_pred),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "features": list(X.columns),
        "importances": importances.tolist(),
        "market_sentiment": market_sentiment, 
        "up_ratio": float(up_ratio) 
    }
    
    # Lưu vào thư mục Data
    result_path = os.path.join(BASE_DIR, "Data", "ml_results.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=4)
    print(f" Đã xuất file thông số mô hình ra: {result_path}")
if __name__ == "__main__":
    run_prediction()