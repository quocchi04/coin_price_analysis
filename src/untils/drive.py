import os
import io
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


def clean_df(df):
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.duplicated()].copy()

    required_cols = ["id", "time_collected", "current_price_usd", "market_cap"]
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        print(f"❌ File dữ liệu thiếu cột: {missing}")
        print(f"📌 Các cột hiện có: {list(df.columns)}")
        return pd.DataFrame()

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

    df = df.dropna(subset=["id", "time_collected", "current_price_usd"])
    df = df.sort_values(["id", "time_collected"]).reset_index(drop=True)

    return df


def get_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    service_account_file = os.path.join(base_dir, "service_account.json")

    file_id = os.getenv("DRIVE_FILE_ID", "1v_EbHYMazXALKZD6dldtgkqVz-9WzWU5")

    if not os.path.exists(service_account_file):
        print(f"❌ Không tìm thấy service_account.json tại: {service_account_file}")
        return pd.DataFrame()

    try:
        scopes = ["https://www.googleapis.com/auth/drive.readonly"]

        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=scopes
        )

        drive_service = build("drive", "v3", credentials=credentials)

        print(f"📥 Đang tải file CSV từ Google Drive, file_id={file_id}")

        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()

        downloader = MediaIoBaseDownload(fh, request)
        done = False

        while not done:
            _, done = downloader.next_chunk()

        fh.seek(0)

        df = pd.read_csv(fh, dtype={"time_collected": str}, low_memory=False)
        df = clean_df(df)

        print(f"✅ Đã đọc Drive thành công: {len(df)} dòng")
        return df

    except Exception as e:
        print(f"❌ Lỗi đọc file Google Drive: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    df = get_data()
    print(df.shape)
    print(df.head())