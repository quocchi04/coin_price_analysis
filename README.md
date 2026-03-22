# 🚀 Crypto Auto-Alert & Dashboard

**Hệ thống giám sát và phân tích thị trường Tiền điện tử thông minh.** Hệ thống theo dõi giá Crypto 24/7, từ việc thu thập dữ liệu thời gian thực, tự động lưu trữ dữ liệu lên Google Cloud, phân tích và gửi cảnh báo qua Email. Dự án kết hợp sức mạnh của Python, Cloud Computing và Automation.

---
### 🌟 Tính năng nổi bật
* **📡 Real-time Data Collection:** Tự động lấy dữ liệu giá, vốn hóa và khối lượng giao dịch của Top 500 đồng coin từ CoinGecko API mỗi giờ.

* **☁️ Cloud Automation:** Vận hành hoàn toàn trên GitHub Actions, không cần treo máy cá nhân.

* **💾 Hybrid Storage:** Kết hợp lưu trữ tạm thời trên máy ảo và lưu trữ vĩnh viễn (Data Lake) trên Google Drive thông qua Service Account.

* **🔔 Smart Alert System:** Hệ thống tự động phân tích biến động và gửi cảnh báo "tức thời" qua Email khi thị trường có biến động mạnh.

* **📊 Interactive Dashboard:** Trực quan hóa xu hướng giá, phân cụm thị trường (Clustering) và dự báo xu hướng (Trend Prediction) thông qua Streamlit.

### 🛠 Tech Stack
| Thành phần | Công nghệ sử dụng |
| :--- | :--- |
| **Ngôn ngữ** | Python 3.10+ |
| **Xử lý dữ liệu** | Pandas, Numpy |
| **Giao diện** | Streamlit, Plotly |
| **Tự động hóa** | GitHub Actions (Cronjob) |
| **Lưu trữ** | Google Cloud (Drive API / GCS) |


### 🔄 Luồng hoạt động chi tiết (Workflow)

Hệ thống vận hành khép kín qua 4 giai đoạn chính:

#### **Giai đoạn 1: Tự động hóa & Thu thập (Automation)**
* **Kích hoạt:** GitHub Actions đóng vai trò là "bộ não" điều phối, tự động kích hoạt script Python chạy mỗi 60 phút (Cron job).
* **Thu thập:** Script thực hiện gọi API từ các sàn giao dịch để lấy dữ liệu giá thời gian thực (Real-time) của các cặp tiền tệ phổ biến.

#### **Giai đoạn 2: Lưu trữ đám mây (Cloud Sync)**
* **Xử lý:** Dữ liệu thô sau khi thu thập được làm sạch, chuẩn hóa cấu trúc và tính toán các chỉ số cần thiết bằng thư viện **Pandas**.
* **Đồng bộ:** Hệ thống kết nối với **Google Cloud (Drive/GCS)** để lưu trữ dữ liệu lịch sử. Việc lưu trữ đám mây giúp dữ liệu tồn tại bền vững, không bị mất khi máy ảo GitHub Actions kết thúc phiên chạy.

#### **Giai đoạn 3: Phân tích & Cảnh báo (Smart Alert)**
* **Kiểm tra:** Script thực hiện so sánh giá hiện tại với các ngưỡng giá mục tiêu (Threshold) đã được thiết lập sẵn.
* **Cảnh báo:** Nếu giá đạt hoặc vượt ngưỡng, hệ thống tự động khởi tạo kết nối SMTP và gửi Email thông báo ngay lập tức đến người dùng qua **Gmail API**.

#### **Giai đoạn 4: Trực quan hóa (Dashboard)**
* **Truy xuất:** Ứng dụng **Streamlit** đóng vai trò giao diện hiển thị, thực hiện đọc dữ liệu trực tiếp từ Google Cloud mỗi khi có người dùng truy cập.
* **Hiển thị:** Dữ liệu được trực quan hóa thành các biểu đồ tương tác bằng **Plotly**, giúp người dùng dễ dàng theo dõi xu hướng và biến động của thị trường.

### 📁 Cấu trúc dự án (Project Structure)

```text
├── .github/workflows/      # Cấu hình chạy main.yml tự động mỗi giờ
├── Data/                   # Chứa các file dữ liệu CSV cục bộ
├── src/                    # Thư mục chứa mã nguồn chính
│   ├── alert/              # Logic kiểm tra giá & gửi Email
│   │   ├── crypto_alert.py
│   │   └── del_alert.py
│   ├── analysis/           # Các module phân tích chuyên sâu
│   │   ├── coin_analysis.py
│   │   ├── coin_ranking.py
│   │   ├── coin_trend.py
│   │   ├── dbscan_clustering.py
│   │   ├── KMeans_clustering.py
│   │   └── pattern_matching.py
│   ├── data/               # Module thu thập dữ liệu (collect_data.py)
│   ├── Prediction/         # Các mô hình dự báo giá
│   │   ├── coin_prediction.py
│   │   └── price_trend_prediction.py
│   └── untils/             # Tiện ích hệ thống (Drive API, Send Mail)
│       ├── drive.py
│       ├── send_mail_auto.py
│       └── upload_to_drive.py
├── app.py                  # Giao diện chính chạy trên Streamlit
├── requirements.txt        # Danh sách các thư viện cần cài đặt
└── service_account.json    # File xác thực Google Cloud (Chạy Local)
```
### 🚀 Hướng dẫn Cài đặt & Sử dụng

### 1. Yêu cầu hệ thống
* **Python:** Phiên bản 3.10 trở lên.
* **Tài khoản Google Cloud:** Để lấy file `service_account.json` (quyền Drive/GCS).
* **Gmail App Password:** Để gửi email cảnh báo tự động (16 ký tự mã xác thực ứng dụng).

### 2. Cài đặt tại máy cục bộ (Local)

**Bước 1: Clone dự án về máy**
```bash
git clone [https://github.com/quocchi04/coin_price_analysis.git](https://github.com/quocchi04/coin_price_analysis.git)
cd coin_price_analysis
```
**Bước 2: Cài đặt các thư viện cần thiết và môi trường**
```bash
pip install -r requirements.txt
```

```bash
python -m venv venv
# Trên Windows
venv\Scripts\activate
# Trên macOS/Linux
source venv/bin/activate
```
**Bước 3: Thiết lập file cấu hình**

#### 1. Lấy Google Service Account & Drive ID
* **Service Account**: 
1. Truy cập [**Google Cloud Console:**](https://console.cloud.google.com/)
2. Tạo một Project mới.
3. Vào mục **APIs & Services** > **Library**, tìm và Enable **Google Drive API**.
4. Vào mục **IAM & Admin** > **Service Accounts** > **Create Service Account**.
5. Sau khi tạo, vào tab **Keys** > **Add Key** > **Create new key** (chọn định dạng **JSON**). Tải file này về và đổi tên thành `service_account.json`.

* **Drive Folder ID**:
1. Mở thư mục [**Drive Folder:**](https://drive.google.com/drive/u/1/folders/1DfQtRJ9IWW05TegnXf6o4xKes190DbUu)
2. ID là chuỗi ký tự cuối cùng trên thanh địa chỉ trình duyệt (sau chữ `folders/`).
3. **Quan trọng**: Nhấn nút **Share** thư mục này cho email của Service Account (có trong file JSON) với quyền **Editor**.

#### 2. Lấy CoinGecko API (Tùy chọn)
* Dự án hiện đang dùng API công khai (Public) không cần Key.

* Nếu bạn sử dụng tài khoản Demo/Pro để tránh bị giới hạn tốc độ (Rate limit), hãy đăng ký tại CoinGecko Developer Dashboard và thêm `API_KEY` vào file `.env`.

#### 3. Lấy Gmail App Password (Cho hệ thống Alert)
Để hệ thống có thể gửi email cảnh báo tự động:

1. Truy cập vào [**Tài khoản Google**](https://myaccount.google.com/) của bạn.

2. Bật **Xác minh 2 lớp (2-Step Verification)**.

3. Tìm kiếm mục **App Passwords** (Mật khẩu ứng dụng).

4. Chọn ứng dụng là "Thư" và thiết bị là "Khác", đặt tên là "Crypto Alert".

5. Copy mã 16 ký tự hiện ra để dán vào biến `EMAIL_PASS` trên GitHub Secrets.

**Bước 4: Chạy ứng dụng Dashboard**
```bash
streamlit run app.py
```
### 3. Cấu hình Chạy tự động (GitHub Actions)
Để hệ thống tự động cập nhật giá mỗi giờ và gửi mail, bạn cần thiết lập Secrets trên GitHub:

#### 1. Truy cập vào Repository trên `GitHub` > `Settings` > `Secrets and variable`s > `Actions`.

#### 2. Nhấn `New repository secret` và thêm các biến sau:

* `GCP_SERVICE_ACCOUNT`: Dán nội dung JSON của file Service Account.

* `DRIVE_FOLDER_ID` : Địa chỉ ID của thư mục lưu trữ trên Google Drive.

* `EMAIL_USER`: Địa chỉ Gmail gửi cảnh báo.

* `EMAIL_PASS`: Mật khẩu ứng dụng (App Password) của Gmail.

* `RECEIVER_EMAIL`: Địa chỉ Email nhận thông báo.
---

### 🛠 Khắc phục lỗi thường gặp
* **FileNotFoundError**: Đảm bảo file `service_account.json` nằm đúng ở thư mục gốc (root).

* **SMTPAuthenticationError**: Kiểm tra lại `EMAIL_PASS`, đảm bảo đó là mã 16 ký tự từ `Google App Password`.

* **ModuleNotFoundError**: Hãy chắc chắn bạn đã chạy lệnh cài đặt thư viện ở Bước 2.
---
### 🌐 Live Demo
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://coin-price-analysis.streamlit.app/)