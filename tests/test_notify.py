from unittest.mock import patch, MagicMock
from watcher.notify import send_sms


def test_send_sms_connects_to_gmail_smtp():
    with patch("watcher.notify.smtplib.SMTP_SSL") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_sms("test message", "test@example.com", "testuser@gmail.com", "apppassword")

    mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 465)
    mock_smtp.login.assert_called_once_with("testuser@gmail.com", "apppassword")
    mock_smtp.sendmail.assert_called_once()
    _, to_addr, _ = mock_smtp.sendmail.call_args.args
    assert to_addr == "test@example.com"


def test_send_sms_message_in_body():
    with patch("watcher.notify.smtplib.SMTP_SSL") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_sms("SFO>LAX Thu5/14 $24", "7173799089@vtext.com", "me@gmail.com", "pw")

    _, _, raw_msg = mock_smtp.sendmail.call_args.args
    assert "SFO>LAX Thu5/14 $24" in raw_msg
