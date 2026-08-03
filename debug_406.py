import time
import requests

_BOOKING_URL = "https://booking.flyfrontier.com/Flight/InternalSelect"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

import socket
try:
    ip_resp = requests.get("https://api.ipify.org?format=json", timeout=10)
    print("EGRESS_IP:", ip_resp.text)
except Exception as e:
    print("ipify failed:", e)

# Simulate the production request pattern: sequential days, same route, 0.4s pacing
from datetime import date, timedelta
begin = date(2026, 8, 15)
for i in range(20):
    d = begin + timedelta(days=i)
    params = {"o1": "SFO", "d1": "LAX", "dd1": d.strftime("%Y-%m-%d"), "ADT": "1", "mon": "true", "promo": ""}
    t0 = time.time()
    resp = requests.get(_BOOKING_URL, params=params, headers=_HEADERS, timeout=30)
    elapsed = time.time() - t0
    print(f"[{i}] date={d} status={resp.status_code} elapsed={elapsed:.2f}s len={len(resp.text)} server={resp.headers.get('Server')} x-served-by={resp.headers.get('X-Served-By')}")
    if resp.status_code != 200:
        print(f"    BODY: {resp.text[:400]!r}")
        print(f"    HEADERS: {dict(resp.headers)}")
    time.sleep(0.4)
