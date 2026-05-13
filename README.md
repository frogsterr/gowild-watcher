# GoWild Flight Watcher

Sends SMS alerts twice daily for Frontier Airlines GoWild round-trip flights departing from the Bay Area.

## What It Does

- Searches SFO, SJC, and OAK for GoWild flights to 17 destinations
- Filters for valid weekend windows: Thursday 5pm+ or Friday out, Sunday or Monday back
- Texts you when new flights appear (both runs) + a morning digest of all available trips
- Deduplicates so you only get alerted once per route/date combo

## SMS Format

```
SFO>LAX Thu5/21 8:48p>Sun5/24 7:29p $213
```

## Setup

### 1. Clone and push to GitHub

```bash
git clone <this-repo>
cd gowild-watcher
git remote add origin https://github.com/YOUR_USERNAME/gowild-watcher.git
git push -u origin master
```

### 2. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Value |
|--------|-------|
| `GMAIL_ADDRESS` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not your login password) |

To generate an App Password: Google Account → Security → 2-Step Verification → App passwords.

### 3. Configure your number

Edit `watcher/config.py` and set `SMS_TO` to your Verizon number:

```python
SMS_TO = "YOUR10DIGITNUMBER@vtext.com"
```

Other carriers:
- AT&T: `number@txt.att.net`
- T-Mobile: `number@tmomail.net`
- Sprint: `number@messaging.sprintpcs.com`

### 4. Trigger a test run

In GitHub: **Actions → GoWild Flight Watcher → Run workflow**

## Schedule

Runs at **8 AM** and **6 PM Pacific** daily via GitHub Actions through September 10, 2026.

## Destinations

LAX, SAN, SNA, SEA, PDX, YVR, SJU, HNL, OGG, KOA, LIH, ORD, MDW, DEN, JFK, LGA, MDT

## Requirements

Python 3.12, `requests`, `pytz` — installed automatically by GitHub Actions.
