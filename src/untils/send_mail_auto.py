import smtplib
import os
from email.message import EmailMessage

# --- SUA DOAN NAY DE CHAY DUOC TREN CLOUD ---
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Logged: Load .env thành công (Local)")
except ImportError:
    # Nếu chạy trên GitHub Actions, thư viện dotenv không cần thiết
    # vì GitHub tự nạp Secrets vào biến môi trường hệ thống (os.environ)
    print("Logged: Chạy trên môi trường Cloud (GitHub/Streamlit)")

def send_email(subject, body, to_email=None):
    # 2. Lấy thông tin từ biến môi trường
    # Lưu ý: Đảm bảo tên biến EMAIL_USER, EMAIL_PASS trùng với tên bạn đặt trong GitHub Secrets
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")
    default_receiver = os.getenv("RECEIVER_EMAIL")

    # Nếu không truyền to_email thì dùng email mặc định
    target_email = to_email if to_email else default_receiver

    if not email_user or not email_pass:
        print("Loi: Chua cau hinh EMAIL_USER hoac EMAIL_PASS")
        return

    msg = EmailMessage()
    msg['From'] = email_user
    msg['To'] = target_email
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        # Sử dụng cổng 587 cho Gmail
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            # Loại bỏ khoảng trắng trong mật khẩu app (nếu có)
            clean_pass = str(email_pass).replace(" ", "")
            smtp.login(email_user, clean_pass)
            smtp.send_message(msg)
        print(f"Email da duoc gui thanh cong toi {target_email}.")
    except Exception as e:
        print(f"Loi gui mail: {e}")

if __name__ == "__main__":
    # Chạy thử nghiệm
    send_email(
        subject="Test Mail He Thong",
        body="He thong canh bao da hoat dong!",
    )