import smtplib
from email.mime.text import MIMEText


def send_sms(message: str, to: str, gmail_address: str, gmail_app_password: str) -> None:
    msg = MIMEText(message)
    msg["From"] = gmail_address
    msg["To"] = to
    msg["Subject"] = ""
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_address, gmail_app_password)
        smtp.sendmail(gmail_address, to, msg.as_string())
