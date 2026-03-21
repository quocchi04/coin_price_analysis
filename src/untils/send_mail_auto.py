import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

# 1. Tải cấu hình từ file .env
load_dotenv()

def send_email(subject, body, to_email=None):
    # 2. Lấy thông tin từ biến môi trường
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")
    default_receiver = os.getenv("RECEIVER_EMAIL")

    # Nếu không truyền to_email thì dùng email mặc định trong .env
    target_email = to_email if to_email else default_receiver

    if not email_user or not email_pass:
        print(" Lỗi: Chưa cấu hình EMAIL_USER hoặc EMAIL_PASS trong file .env")
        return

    msg = EmailMessage()
    msg['From'] = email_user
    msg['To'] = target_email
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            # Xử lý mật khẩu: loại bỏ khoảng trắng nếu lỡ tay nhập "abcd efgh..."
            clean_pass = email_pass.replace(" ", "")
            smtp.login(email_user, clean_pass)
            smtp.send_message(msg)
        print(f" Email đã được gửi thành công tới {target_email}.")
    except Exception as e:
        print(f" Lỗi gửi mail: {e}")

if __name__ == "__main__":
    # Chạy thử nghiệm
    send_email(
        subject="Test Mail Bảo Mật",
        body=" file .env đã hoạt động!",
    )