# GoWild Flight Watcher

Sends a formatted HTML email digest twice daily for Frontier Airlines GoWild round-trip flights departing from the Bay Area.

## What It Does

- Searches SFO, SJC, and OAK for GoWild flights to 17 destinations
- Filters for valid trip windows: Wednesday 5pm+ / Thursday 5pm+ / Friday out, Sunday / Monday / Tuesday back
- Sends one email per run with the top 3 cheapest deals at the top, then all flights grouped by destination
- New flights (not seen in a previous run) are highlighted with a **NEW** badge
- Deduplicates so a route/date combo is only marked new once — but prices always reflect the latest live data

## Email Format

Each run produces a single HTML email with:

1. **Top 3 Deals** — the 3 cheapest available flights as cards, sorted by price
2. **All Flights by Destination** — every available trip grouped by destination, sorted cheapest-first within each group

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
| `GMAIL_ADDRESS` | Your Gmail address (used to send) |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not your login password) |

To generate an App Password: Google Account → Security → 2-Step Verification → App passwords.

### 3. Configure your email

Edit `watcher/config.py` and set `EMAIL_TO` to the address you want to receive digests:

```python
EMAIL_TO = "you@example.com"
```

### 4. Trigger a test run

In GitHub: **Actions → GoWild Flight Watcher → Run workflow**

## Schedule

Runs at **8 AM** and **6 PM Pacific** daily via GitHub Actions through September 10, 2026.

## Destinations

LAX · SAN · SNA · SEA · PDX · YVR · SJU · HNL · OGG · KOA · LIH · ORD · MDW · DEN · JFK · LGA · MDT

## Requirements

Python 3.12, `requests`, `pytz` — installed automatically by GitHub Actions.
