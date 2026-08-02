import smtplib
from email.mime.text import MIMEText


def send_email(
    subject: str, html_body: str, to: str | list[str], gmail_address: str, gmail_app_password: str
) -> None:
    recipients = [to] if isinstance(to, str) else list(to)
    msg = MIMEText(html_body, "html")
    msg["From"] = gmail_address
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_address, gmail_app_password)
        smtp.sendmail(gmail_address, recipients, msg.as_string())
