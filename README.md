# 🚀 Crypto Auto-Alert & Dashboard

Hệ thống theo dõi giá Crypto 24/7, tự động lưu trữ dữ liệu lên Google Cloud và gửi cảnh báo qua Email. Dự án kết hợp sức mạnh của Python, Cloud Computing và Automation.

---

### 🌟 Tính năng chính
* **Auto-Tracking:** Tự động cập nhật giá từ API mỗi giờ (GitHub Actions).
* **Cloud Storage:** Lưu trữ dữ liệu lịch sử an toàn trên Google Drive/GCS.
* **Smart Alert:** Gửi thông báo Gmail ngay khi giá chạm ngưỡng mục tiêu.
* **Live Dashboard:** Theo dõi biến động trực quan qua giao diện Streamlit.

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
├── .github/workflows/      # Cấu hình GitHub Actions (chạy main.yml tự động)
├── Data/                   # Chứa các file dữ liệu CSV cục bộ (Full data, Top 500 ids)
├── src/                    # Thư mục chứa mã nguồn chính
│   ├── alert/              # Logic kiểm tra giá và gửi thông báo Email
│   │   ├── crypto_alert.py
│   │   └── del_alert.py
│   ├── analysis/           # Các module phân tích chuyên sâu
│   │   ├── coin_analysis.py      # Phân tích cơ bản
│   │   ├── coin_ranking.py       # Phân tích xếp hạng
│   │   ├── coin_trend.py         # Phân tích xu hướng giá
│   │   ├── dbscan_clustering.py  # Phân cụm mật độ DBSCAN
│   │   ├── KMeans_clustering.py  # Phân cụm K-Means
│   │   └── pattern_matching.py   # Nhận dạng hình thái
│   ├── data/               
│   │   └── collect_data.py       # Module thu thập dữ liệu
│   ├── Prediction/         # Các mô hình dự báo giá
│   │   ├── coin_prediction.py
│   │   └── price_trend_prediction.py
│   └── untils/             # Tiện ích hệ thống (Drive API, Send Mail)
│       ├── coin_prediction.py
│       └── price_trend_prediction.py
├── app.py                  # Giao diện chính chạy trên Streamlit
├── requirements.txt        # Danh sách các thư viện cần cài đặt
└── service_account.json    # File xác thực Google Cloud (Sử dụng tại Local)