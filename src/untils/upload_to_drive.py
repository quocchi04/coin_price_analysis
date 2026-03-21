from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os
import io
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# ==== CẤU HÌNH ĐƯỜNG DẪN CHÍNH XÁC ====
# Lấy đường dẫn thư mục gốc (Coins_Price_Analysis)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. Fix đường dẫn file JSON
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'service_account.json')
SCOPES = ['https://www.googleapis.com/auth/drive']

# 2. Fix ID thư mục Drive
FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
FILENAME = "crypto_full_data.csv"

# 3. Fix đường dẫn file CSV
LOCAL_NEW_FILE = os.path.join(BASE_DIR, 'Data', 'crypto_full_data.csv')

def get_existing_file_id(service):
    query = f"name='{FILENAME}' and '{FOLDER_ID}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        supportsAllDrives=True,
        spaces='drive',
        fields='files(id, name)',
        includeItemsFromAllDrives=True
    ).execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def download_drive_file(service, file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return pd.read_csv(fh)

def upload_to_drive():
    # Kiểm tra file CSV
    if not os.path.exists(LOCAL_NEW_FILE):
        print(f"❌ Không tìm thấy file dữ liệu tại: {LOCAL_NEW_FILE}")
        return

    # Kiểm tra file JSON xác thực
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"❌ Không tìm thấy file xác thực tại: {SERVICE_ACCOUNT_FILE}")
        print("💡 Hãy đảm bảo file service_account.json nằm ở thư mục gốc dự án.")
        return

    # Khởi tạo dịch vụ Google Drive
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=creds)

    file_id = get_existing_file_id(service)
    print(f"🔍 Đang kiểm tra file {FILENAME} trên Drive...")

    # Đọc dữ liệu mới từ máy tính
    df_new = pd.read_csv(LOCAL_NEW_FILE)
    
    if file_id:
        print(f"📥 Đã tìm thấy file cũ trên Drive. Đang gộp dữ liệu...")
        try:
            df_old = download_drive_file(service, file_id)
            # Gộp và xóa trùng lặp
            df_combined = pd.concat([df_old, df_new], ignore_index=True).drop_duplicates()
            df_combined.to_csv(LOCAL_NEW_FILE, index=False, encoding='utf-8-sig')
            print(f"🔄 Gộp xong! Tổng cộng: {len(df_combined)} dòng.")
        except Exception as e:
            print(f"⚠️ Lỗi khi gộp: {e}")
    else:
        print("📄 Chưa có file trên Drive, sẽ tạo mới.")

    # Upload
    media = MediaFileUpload(LOCAL_NEW_FILE, mimetype='text/csv', resumable=False)

    if file_id:
        service.files().update(
            fileId=file_id,
            media_body=media,
            supportsAllDrives=True
        ).execute()
        print("✅ Đã UPDATE file lên Google Drive thành công.")
    else:
        file_metadata = {'name': FILENAME, 'parents': [FOLDER_ID]}
        service.files().create(
            body=file_metadata,
            media_body=media,
            supportsAllDrives=True,
            fields='id'
        ).execute()
        print("✅ Đã TẠO file mới lên Google Drive thành công.")

if __name__ == "__main__":
    upload_to_drive()