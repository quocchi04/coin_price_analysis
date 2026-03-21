import smtplib
import os
from email.message import EmailMessage

def send_email(subject, body, to_email=None):
    # 1. Chi load dotenv khi thuc su can (O may ca nhan)
    # Tren GitHub no se tu vao ImportError va bo qua
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # 2. Lay thong tin tu bien moi truong
    # Quan trong: Ten bien nay phai giong het trong GitHub Secrets
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")
    default_receiver = os.getenv("RECEIVER_EMAIL")

    target_email = to_email if to_email else default_receiver

    if not email_user or not email_pass:
        print("Loi: Thieu cau hinh EMAIL_USER hoac EMAIL_PASS")
        return

    msg = EmailMessage()
    msg['From'] = email_user
    msg['To'] = target_email
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            # Xoa khoang trang mat khau
            clean_pass = str(email_pass).replace(" ", "")
            smtp.login(email_user, clean_pass)
            smtp.send_message(msg)
        print(f"Email gui thanh cong toi {target_email}")
    except Exception as e:
        print(f"Loi gui mail: {e}")