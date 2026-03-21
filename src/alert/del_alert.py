import json
import os

# 1. Tự động tìm đường dẫn đến file alert_list.json ở thư mục gốc
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILE_PATH = os.path.join(BASE_DIR, "alert_list.json")

def read_json_from_gcs():
    # Kiểm tra nếu chưa có file thì trả về danh sách rỗng
    if not os.path.exists(FILE_PATH):
        return []
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def write_json_to_gcs(data):
    # Ghi dữ liệu trực tiếp vào ổ cứng máy tính
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"💾 Đã lưu danh sách cảnh báo vào: {FILE_PATH}")

def format_float(f):
    return f"{float(f):.15f}".rstrip("0").rstrip(".")

def Del_Alert(mail, coin, breakout, breakdown):
    data = read_json_from_gcs()
    for user in data:
        if user.get("mail") == mail:
            for item in user["coins"][:]:
                if coin in item:
                    info = item[coin]
                    if format_float(info["breakout"]) == format_float(breakout) and \
                       format_float(info["breakdown"]) == format_float(breakdown):
                        user["coins"].remove(item)
    write_json_to_gcs(data)