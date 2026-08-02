import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

resp = requests.get(
    "https://booking.flyfrontier.com/Flight/InternalSelect",
    params={"o1": "LAX", "d1": "SFO", "dd1": "2026-08-10", "ADT": "1", "mon": "true", "promo": ""},
    headers=_HEADERS,
    timeout=30,
)
print("STATUS:", resp.status_code)
print("URL:", resp.url)
print("HEADERS:", dict(resp.headers))
print("BODY_SNIPPET:", resp.text[:1500])

import socket
try:
    print("EGRESS_IP_HOST:", socket.gethostbyname(socket.gethostname()))
except Exception as e:
    print("hostname lookup failed:", e)
try:
    ip_resp = requests.get("https://api.ipify.org?format=json", timeout=10)
    print("EGRESS_IP:", ip_resp.text)
except Exception as e:
    print("ipify failed:", e)
