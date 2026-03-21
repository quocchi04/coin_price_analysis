import sys
import os
import json
import pandas as pd
from datetime import datetime, timedelta

# Them thu muc goc de tim thay module src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.untils.drive import get_data
from src.alert.del_alert import read_json_from_gcs, write_json_to_gcs
from src.untils.send_mail_auto import send_email

# --- HAM LAY DU LIEU MOI NHAT ---
def get_current_market_data():
    """Tai du lieu moi tu Drive/GCS va chuan bi DataFrame"""
    try:
        df = get_data() # Lay data moi nhat
        df['time_collected'] = pd.to_datetime(df['time_collected'])
        
        # Lay moc thoi gian moi nhat
        latest_time = df['time_collected'].max()
        latest_price_df = df[df['time_collected'] == latest_time]
        
        # Lay lich su 7 ngay de tinh min/max
        seven_days_ago = latest_time - timedelta(days=7)
        df_history = df[(df['time_collected'] >= seven_days_ago) & (df['time_collected'] < latest_time)]
        
        return df_history, latest_price_df
    except Exception as e:
        print(f"Loi khi cap nhat du lieu thi truong: {e}")
        return None, None

def min_max_latest_price(df_history, coin_id=""):
    if df_history is None or coin_id not in df_history['id'].values:
        return None, None
    coin_data = df_history[df_history['id'] == coin_id]
    return coin_data['current_price_usd'].min(), coin_data['current_price_usd'].max()

# --- HAM GHI CANH BAO ---
def writing_alert(mail, coin, breakdown=None, breakout=None):
    df_history, _ = get_current_market_data()
    minn, maxx = min_max_latest_price(df_history, coin)
    
    # Neu khong truyen nguong, tu dong lay min/max 7 ngay
    breakdown = float(breakdown) if breakdown is not None else minn
    breakout = float(breakout) if breakout is not None else maxx
    
    new_coin_config = {coin: {"breakout": breakout, "breakdown": breakdown}}
    
    try:
        data = read_json_from_gcs()
    except:
        data = []

    found_user = False
    for user in data:
        if user.get("mail") == mail:
            found_user = True
            found_coin = False
            for co_dict in user.get("coins", []):
                if coin in co_dict:
                    co_dict[coin] = {"breakout": breakout, "breakdown": breakdown}
                    found_coin = True
                    break
            if not found_coin:
                user.setdefault("coins", []).append(new_coin_config)
            break
            
    if not found_user:
        data.append({"mail": mail, "coins": [new_coin_config]})
    
    write_json_to_gcs(data)
    print(f"Da cap nhat cau hinh cho {coin} ({mail})")

# --- HAM QUET VA GUI CANH BAO (CHINH) ---
def alert():
    # 1. Cap nhat gia thuc te truoc
    _, latest_price_df = get_current_market_data()
    if latest_price_df is None: 
        print("Khong co du lieu gia moi nhat.")
        return

    # 2. Doc danh sach dang ky tu GCS
    try:
        users = read_json_from_gcs()
    except Exception as e:
        print(f"Khong the doc danh sach alert: {e}")
        return
        
    if not users:
        print("Danh sach trong, khong co gi de kiem tra.")
        return
        
    for user in users:
        email = user.get('mail')
        if not email: continue
            
        for detail in user.get('coins', []):
            for coin_name, thresholds in detail.items():
                breakout = thresholds.get('breakout')
                breakdown = thresholds.get('breakdown')
                
                # Tim gia hien tai cua dong coin nay
                current_price_row = latest_price_df.loc[latest_price_df['id'] == coin_name, 'current_price_usd']
                
                if not current_price_row.empty:
                    current_p = current_price_row.values[0]
                    
                    if current_p > breakout:
                        msg = f"CANH BAO: {coin_name.upper()} BREAKOUT!\nGia: ${current_p:,.2f} > Nguong: ${breakout:,.2f}"
                        send_email("CANH BAO VUOT NGUONG", msg, email)
                        print(f"Da bao Breakout toi {email}")
                        
                    elif current_p < breakdown:
                        msg = f"CANH BAO: {coin_name.upper()} BREAKDOWN!\nGia: ${current_p:,.2f} < Nguong: ${breakdown:,.2f}"
                        send_email("CANH BAO THUNG NGUONG", msg, email)
                        print(f"Da bao Breakdown toi {email}")
                else:
                    print(f"Dang doi du lieu moi cho {coin_name}...")

if __name__ == "__main__":
    print(f"--- Bat dau quy trinh tu dong: {datetime.now()} ---")
    alert()