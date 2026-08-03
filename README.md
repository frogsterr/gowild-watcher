# GoWild Flight Watcher

Sends a formatted HTML email digest twice daily for Frontier Airlines GoWild round-trip flights departing from the Bay Area.

## What It Does

- Searches SFO, SJC, and OAK for GoWild flights to 17 destinations
- Filters for valid trip windows: Wednesday 5pm+ / Thursday 5pm+ / Friday out, Sunday / Monday / Tuesday back
- Sends one email per run with the top 3 cheapest deals at the top, then all flights grouped by destination
- New flights (not seen in a previous run) are highlighted with a **NEW** badge
- Deduplicates so a route/date combo is only marked new once

## Architecture

Frontier's booking site rate-limits bursts of requests (~14 in quick succession), and a
full sweep needs ~1,400 requests — far more than that in one shot. So fetching and emailing
are split into two GitHub Actions workflows:

- **Collector** (`collect.py`, every 5 minutes) — fetches a small batch (10 requests) and
  saves results to `state/sweep_state.json`, picking up where it left off. A full sweep
  takes ~12 hours. LAX, SAN, and SNA (`PRIORITY_DESTINATIONS` in `watcher/config.py`) are
  always swept last, so they're the freshest data of any destination at any point in time.
- **Digest** (`main.py`, 8am/6pm Pacific) — reads whatever's currently in the cache (no
  live searching) and sends the email. Most routes reflect data up to ~12 hours old;
  priority destinations are typically only a couple hours old.

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

Edit `watcher/config.py` and set `EMAIL_TO` to the address(es) you want to receive digests:

```python
EMAIL_TO = ["you@example.com", "someone-else@example.com"]
```

### 4. Trigger a test run

In GitHub: **Actions → GoWild Flight Watcher → Run workflow**

## Schedule

Runs at **8 AM** and **6 PM Pacific** daily via GitHub Actions through September 10, 2026.

## Destinations

LAX · SAN · SNA · SEA · PDX · YVR · SJU · HNL · OGG · KOA · LIH · ORD · MDW · DEN · JFK · LGA · MDT

## Requirements

Python 3.12, `requests`, `pytz` — installed automatically by GitHub Actions.
