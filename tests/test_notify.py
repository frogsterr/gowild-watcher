from unittest.mock import patch, MagicMock
from watcher.notify import send_email


def test_send_email_connects_to_gmail_smtp():
    with patch("watcher.notify.smtplib.SMTP_SSL") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_email("Test Subject", "<p>Hello</p>", "test@example.com", "testuser@gmail.com", "apppassword")

    mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 465)
    mock_smtp.login.assert_called_once_with("testuser@gmail.com", "apppassword")
    mock_smtp.sendmail.assert_called_once()
    _, to_addr, _ = mock_smtp.sendmail.call_args.args
    assert to_addr == ["test@example.com"]


def test_send_email_html_in_body():
    with patch("watcher.notify.smtplib.SMTP_SSL") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_email("Subject", "<p>SFO to HNL $22</p>", "me@example.com", "me@gmail.com", "pw")

    _, _, raw_msg = mock_smtp.sendmail.call_args.args
    assert "SFO" in raw_msg
    assert "text/html" in raw_msg


def test_send_email_multiple_recipients():
    with patch("watcher.notify.smtplib.SMTP_SSL") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_email(
            "Subject", "<p>body</p>", ["a@example.com", "b@example.com"], "me@gmail.com", "pw"
        )

    _, to_addr, raw_msg = mock_smtp.sendmail.call_args.args
    assert to_addr == ["a@example.com", "b@example.com"]
    assert "To: a@example.com, b@example.com" in raw_msg


def test_send_email_subject_in_headers():
    with patch("watcher.notify.smtplib.SMTP_SSL") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_email("GoWild: 3 new flights", "<p>body</p>", "me@example.com", "me@gmail.com", "pw")

    _, _, raw_msg = mock_smtp.sendmail.call_args.args
    assert "GoWild: 3 new flights" in raw_msg
