import os
import io
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

def get_data():
    # ==== 1. CẤU HÌNH ĐƯỜNG DẪN TỰ ĐỘNG ==== #
    # Lấy thư mục gốc của dự án (Coins_Price_Analysis)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Ghép nối để luôn tìm đúng file json ở thư mục gốc
    SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'service_account.json')
    
    
    FOLDER_ID = '1DfQtRJ9IWW05TegnXf6o4xKes190DbUu' 
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    # Kiểm tra file xác thực trước khi chạy
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"❌ Không tìm thấy file xác thực tại: {SERVICE_ACCOUNT_FILE}. Hãy copy file này vào thư mục gốc dự án!")

    # ==== 2. XÁC THỰC ==== #
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=credentials)

    # ==== 3. LẤY TOÀN BỘ FILE CSV TRONG THƯ MỤC ==== #
    all_files = []
    page_token = None
    print(f"🔍 Đang quét thư mục Drive: {FOLDER_ID}...")
    
    try:
        while True:
            response = drive_service.files().list(
                q=f"'{FOLDER_ID}' in parents and mimeType='text/csv' and trashed=false",
                orderBy='createdTime desc',
                spaces='drive',
                fields='nextPageToken, files(id, name, createdTime)'
            ).execute()
            all_files.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            if not page_token:
                break
    except Exception as e:
        print(f"❌ Lỗi kết nối Google Drive: {e}")
        return pd.DataFrame() # Trả về df rỗng nếu lỗi

    # ==== 4. LỌC VÀ LẤY FILE MỚI NHẤT ==== #
    filtered_files = [f for f in all_files if f['name'].startswith("crypto_full_data")]
    if not filtered_files:
        print("⚠️ Không tìm thấy file nào có tên bắt đầu bằng 'crypto_full_data' trên Drive.")
        return pd.DataFrame()

    file = filtered_files[0]
    file_id = file['id']
    print(f"📥 Đang tải file mới nhất: {file['name']}")

    # ==== 5. TẢI VÀ ĐỌC DỮ LIỆU ==== #
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
        
    fh.seek(0)
    df = pd.read_csv(fh)
    
    # Chuyển đổi thời gian
    if "time_collected" in df.columns:
        df["time_collected"] = pd.to_datetime(df["time_collected"])
    
    print(f"✅ Thành công! Đã tải {len(df)} dòng dữ liệu từ Drive.")
    return df

if __name__ == "__main__":  
    df_test = get_data()
    if not df_test.empty:
        print(df_test.head())