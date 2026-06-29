import os
import io
import pandas as pd


def _base_dir():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _clean_df(df):
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Làm sạch tên cột
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.duplicated()].copy()

    # Xóa cột index rác nếu có
    for col in ["Unnamed: 0", "index"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    required_cols = ["id", "time_collected", "current_price_usd"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"❌ File thiếu cột bắt buộc: {missing}")
        print(f"📌 Các cột hiện có: {list(df.columns)}")
        return pd.DataFrame()

    # Ép kiểu dữ liệu
    df["id"] = df["id"].astype(str).str.strip().str.lower()
    df["time_collected"] = pd.to_datetime(df["time_collected"], errors="coerce")

    numeric_cols = [
        "current_price_usd",
        "market_cap",
        "price_change_24h",
        "total_volume",
        "circulating_supply",
        "total_supply",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Chỉ bỏ dòng thiếu id, thời gian, giá
    df = df.dropna(subset=["id", "time_collected", "current_price_usd"])
    df = df.sort_values(["id", "time_collected"]).reset_index(drop=True)

    return df


def _read_local_csv(base_dir):
    local_paths = [
        os.path.join(base_dir, "Data", "crypto_full_data.csv"),
        os.path.join(base_dir, "data", "crypto_full_data.csv"),
        os.path.join(base_dir, "crypto_full_data.csv"),
    ]

    for path in local_paths:
        if os.path.exists(path):
            try:
                print(f"📄 Đang đọc dữ liệu local: {path}")
                df = pd.read_csv(path, dtype={"time_collected": str}, low_memory=False)
                df = _clean_df(df)

                if not df.empty:
                    print(f"✅ Đã đọc local thành công: {len(df)} dòng")
                    return df

            except Exception as e:
                print(f"⚠️ Lỗi đọc file local {path}: {e}")

    return pd.DataFrame()


def _read_drive_csv(base_dir):
    service_account_file = os.path.join(base_dir, "service_account.json")

    # Ưu tiên lấy từ Streamlit Secrets / GitHub Secrets nếu có
    folder_id = os.getenv("DRIVE_FOLDER_ID")

    # Nếu bạn chưa khai báo DRIVE_FOLDER_ID thì dùng ID cũ của bạn
    if not folder_id:
        folder_id = "1DfQtRJ9IWW05TegnXf6o4xKes190DbUu"

    if not os.path.exists(service_account_file):
        print(f"⚠️ Không tìm thấy service_account.json tại: {service_account_file}")
        return pd.DataFrame()

    if not folder_id:
        print("⚠️ Chưa có DRIVE_FOLDER_ID")
        return pd.DataFrame()

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload

        scopes = ["https://www.googleapis.com/auth/drive.readonly"]

        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=scopes,
        )

        drive_service = build("drive", "v3", credentials=credentials)

        print(f"🔍 Đang quét Google Drive folder: {folder_id}")

        response = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false and name contains 'crypto_full_data'",
            orderBy="modifiedTime desc",
            spaces="drive",
            fields="files(id, name, modifiedTime, mimeType)",
            pageSize=10,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()

        files = response.get("files", [])

        if not files:
            print("⚠️ Không tìm thấy file crypto_full_data trên Drive")
            return pd.DataFrame()

        file = files[0]
        file_id = file["id"]
        print(f"📥 Đang tải file Drive mới nhất: {file['name']}")

        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        fh.seek(0)

        df = pd.read_csv(fh, dtype={"time_collected": str}, low_memory=False)
        df = _clean_df(df)

        if not df.empty:
            print(f"✅ Đã đọc Drive thành công: {len(df)} dòng")
            return df

    except Exception as e:
        print(f"⚠️ Lỗi đọc Google Drive: {e}")

    return pd.DataFrame()


def get_data():
    base_dir = _base_dir()

    # 1. Thử đọc Drive trước để app vẫn cập nhật tự động như cũ
    df_drive = _read_drive_csv(base_dir)
    if not df_drive.empty:
        return df_drive

    # 2. Nếu Drive lỗi thì đọc file local Data/crypto_full_data.csv
    df_local = _read_local_csv(base_dir)
    if not df_local.empty:
        return df_local

    print("❌ Không tải được dữ liệu từ Drive hoặc local CSV")
    return pd.DataFrame()


if __name__ == "__main__":
    df_test = get_data()
    print(df_test.head())
    print(df_test.shape)