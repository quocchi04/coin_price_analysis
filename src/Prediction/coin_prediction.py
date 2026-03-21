import sys
import os
import pandas as pd
import numpy as np
import warnings
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# 1. Thêm đường dẫn hệ thống để nhận diện 'src'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from src.untils.drive import get_data
warnings.filterwarnings("ignore")

def Cre_Pivot(df):
    df['time_collected'] = pd.to_datetime(df['time_collected'])
    # Sắp xếp theo thời gian trước khi Pivot
    df = df.sort_values('time_collected')
    
    pivot_price = df.pivot_table(index='time_collected', columns='id', values='current_price_usd')
    pivot_mcap  = df.pivot_table(index='time_collected', columns='id', values='market_cap')
    
    # Điền giá trị thiếu cực bộ để tránh mất dòng khi shift dữ liệu
    pivot_price = pivot_price.ffill().bfill()
    pivot_mcap = pivot_mcap.ffill().bfill()
    
    return pivot_price, pivot_mcap

def create_dataset(pivot_price, pivot_mcap, coin_target='bitcoin', window_sizes=3, horizon=1):
    # Giảm window_sizes xuống còn 3 để dễ khớp dữ liệu ngắn
    df_price = pivot_price[[coin_target]].copy()
    
    timeline = pd.DataFrame(index=df_price.index)
    timeline['target_price'] = df_price[coin_target].shift(-horizon)
    timeline['current_price'] = df_price[coin_target]
    
    # Tạo biến trễ (Lag)
    for i in range(1, window_sizes + 1):
        timeline[f'lag_{i}'] = df_price[coin_target].shift(i)
    
    # Thêm đặc trưng thời gian
    timeline['hour'] = timeline.index.hour
    
    # Loại bỏ dòng NaN
    dataset = timeline.dropna()
    
    if dataset.empty:
        return None, None
        
    X = dataset.drop(columns=['target_price'])
    # Mục tiêu là dự báo giá trị tuyệt đối hoặc % thay đổi
    Y = (dataset['target_price'] - dataset['current_price']) / dataset['current_price']
    
    return X, Y

def show(coin_name, df):
    pivot_p, pivot_m = Cre_Pivot(df)
    
    # Chuẩn hóa tên coin
    actual_name = next((c for c in pivot_p.columns if c.lower() == coin_name.lower()), None)
    
    if not actual_name:
        return None, f"❌ Không tìm thấy {coin_name}"

    # 2. ÉP TẠO DATASET VỚI WINDOW NHỎ
    X, Y = create_dataset(pivot_p, pivot_m, coin_target=actual_name, window_sizes=2)
    
    if X is None or len(X) < 5:
        return None, f"❌ Dữ liệu '{actual_name}' quá rời rạc (chỉ có {len(X) if X is not None else 0} cặp thời gian liên tiếp)."

    # 3. Huấn luyện nhanh
    model = XGBRegressor(n_estimators=50, learning_rate=0.1)
    model.fit(X, Y)
    
    # 4. Dự báo dòng cuối cùng
    latest_feat = X.tail(1)
    pred_pct = model.predict(latest_feat)[0]
    current_p = latest_feat['current_price'].values[0]
    pred_p = current_p * (1 + pred_pct)
    
    return pred_p, f"✅ Dự báo {actual_name}: {pred_p:,.2f} USD ({pred_pct*100:+.2f}%)"

if __name__ == "__main__":
    print("📥 Đang tải dữ liệu...")
    df = get_data()
    if df is not None:
        # In thử số dòng của Bitcoin để kiểm tra
        btc_count = len(df[df['id'] == 'bitcoin'])
        print(f"📊 Tìm thấy {btc_count} dòng dữ liệu của Bitcoin.")
        
        p, txt = show("bitcoin", df)
        print("\n" + "="*30)
        print(txt)
        print("="*30)