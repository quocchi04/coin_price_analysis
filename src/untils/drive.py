import os
import tempfile
import pandas as pd


DRIVE_FILE_ID = "1v_EbHYMazXALKZD6dldtgkqVz-9WzWU5"


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


def read_local_backup():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    local_file = os.path.join(base_dir, "Data", "crypto_full_data.csv")

    if os.path.exists(local_file):
        print(f"📄 Đọc file local backup: {local_file}")
        df = pd.read_csv(local_file, dtype={"time_collected": str}, low_memory=False)
        return clean_df(df)

    print("⚠️ Không có file local backup.")
    return pd.DataFrame()


def get_data():
    """
    Streamlit Cloud đọc trực tiếp file CSV từ Google Drive public.
    Không dùng service_account.json để tránh lỗi Secrets.
    """

    file_id = os.getenv("DRIVE_FILE_ID", DRIVE_FILE_ID)
    temp_file = os.path.join(tempfile.gettempdir(), "crypto_full_data.csv")

    try:
        import gdown

        url = f"https://drive.google.com/uc?id={file_id}"
        print(f"📥 Đang tải dữ liệu từ Google Drive file_id={file_id}")

        output = gdown.download(url, temp_file, quiet=False)

        if output is None:
            print("❌ gdown không tải được file từ Drive.")
            return read_local_backup()

        if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
            print("❌ File tải từ Drive bị rỗng.")
            return read_local_backup()

        df = pd.read_csv(temp_file, dtype={"time_collected": str}, low_memory=False)
        df = clean_df(df)

        print(f"✅ Đã đọc Drive thành công: {len(df)} dòng")
        return df

    except Exception as e:
        print(f"❌ Lỗi tải Drive bằng gdown: {e}")
        print("🔁 Chuyển sang đọc file local backup nếu có.")
        return read_local_backup()


if __name__ == "__main__":
    df = get_data()
    print(df.shape)
    print(df.columns.tolist())
    print(df.head())