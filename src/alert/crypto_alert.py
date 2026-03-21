import sys
import os

# Thêm thư mục gốc của đồ án vào hệ thống để Python tìm thấy module 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.untils.drive import get_data
import pandas as pd
from datetime import datetime, timedelta, timezone
from src.untils.drive import get_data
# from google.cloud import storage
import json
from src.alert.del_alert import read_json_from_gcs, write_json_to_gcs
from src.untils.send_mail_auto import send_email

BUCKET_NAME = "alert_list"
BLOB_NAME = "alert_list.json"

def get_datas():
    df = get_data()
    # Chuyển cột thời gian sang định dạng datetime nếu chưa có
    df['time_collected'] = pd.to_datetime(df['time_collected'])
    
    # Lấy mốc thời gian mới nhất trong dữ liệu
    latest_time = df['time_collected'].max()
    latest_price = df[df['time_collected'] == latest_time]
    
    # Lấy dữ liệu 7 ngày qua (tính từ mốc mới nhất trở về trước)
    seven_days_ago = latest_time - timedelta(days=7)
    df_history = df[(df['time_collected'] >= seven_days_ago) & (df['time_collected'] < latest_time)]
    
    return df_history, latest_price

# Khởi tạo dữ liệu
df_history, latest_price_df = get_datas()

def min_max_latest_price(coin_id=""):
    if coin_id == "" or coin_id not in df_history['id'].values:
        return None, None
    
    coin_data = df_history[df_history['id'] == coin_id]
    price_min = coin_data['current_price_usd'].min()
    price_max = coin_data['current_price_usd'].max()
    return price_min, price_max

def writing_alert(mail=None, coin=None, breakdown=None, breakout=None):
    if mail is None or coin is None:
        return "Thông tin thiếu" 

    minn, maxx = min_max_latest_price(coin)
    
    # Nếu không truyền ngưỡng, tự động lấy min/max 7 ngày
    if breakdown is None: breakdown = minn
    if breakout is None: breakout = maxx
    
    new_coin_config = {coin: {"breakout": float(breakout), "breakdown": float(breakdown)}}
    
    try:
        data = read_json_from_gcs()
    except Exception:
        data = [] # Nếu chưa có file trên GCS thì tạo list rỗng

    found_user = False
    for user in data:
        if user.get("mail") == mail:
            found_user = True
            found_coin = False
            for co_dict in user["coins"]:
                if coin in co_dict:
                    co_dict[coin]["breakout"] = float(breakout)
                    co_dict[coin]["breakdown"] = float(breakdown)
                    found_coin = True
                    break
            if not found_coin:
                user["coins"].append(new_coin_config)
            break
            
    if not found_user:
        data.append({
            "mail": mail,
            "coins": [new_coin_config]
        })
    
    write_json_to_gcs(data)
    print(f" Đã cập nhật cảnh báo cho {coin} ({mail})")

def alert():
    try:
        users = read_json_from_gcs()
    except Exception as e:
        print(f" Không thể đọc dữ liệu từ GCS: {e}")
        return
        
    if not users:
        print("ℹ Không có cảnh báo nào để kiểm tra.")
        return
        
    for user in users:
        email = user['mail']
        for detail in user['coins']:
            for coin_name, thresholds in detail.items():
                breakout = thresholds['breakout']
                breakdown = thresholds['breakdown']
                
                # Lấy giá hiện tại an toàn hơn
                current_price_row = latest_price_df.loc[latest_price_df['id'] == coin_name, 'current_price_usd']
                
                if not current_price_row.empty:
                    current_p = current_price_row.values[0]
                    
                    # Kiểm tra Breakout
                    if current_p > breakout:
                        msg = f"Giá coin {coin_name} hiện tại là {current_p} đã VƯỢT ngưỡng breakout ({breakout})"
                        try:
                            send_email(" CẢNH BÁO BREAKOUT", msg, email)
                            print(f" Đã gửi mail breakout cho {email}")
                        except:
                            print(f" Lỗi khi gửi mail tới {email}")
                            
                    # Kiểm tra Breakdown
                    elif current_p < breakdown:
                        msg = f"Giá coin {coin_name} hiện tại là {current_p} đã THỦNG ngưỡng breakdown ({breakdown})"
                        try:
                            send_email(" CẢNH BÁO BREAKDOWN", msg, email)
                            print(f" Đã gửi mail breakdown cho {email}")
                        except:
                            print(f" Lỗi khi gửi mail tới {email}")
                else:
                    print(f" Không tìm thấy giá mới nhất của {coin_name}")

if __name__ == "__main__":
    # Nếu không điền breakout/breakdown, nó sẽ tự lấy Min/Max của 7 ngày qua
    writing_alert(mail="quocchi2708ax@gmail.com", coin="bitcoin", breakout=60000, breakdown=50000)
   
    print("--- Đã đăng ký xong, chuẩn bị quét giá thực tế ---")
    alert()