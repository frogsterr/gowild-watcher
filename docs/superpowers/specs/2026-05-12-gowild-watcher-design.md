# GoWild Flight Watcher — Design Spec
**Date:** 2026-05-12

## Overview

A GitHub Actions Python script that runs twice daily, searches Frontier Airlines for GoWild-eligible round-trip flights departing from the Bay Area, and sends SMS alerts via email-to-SMS when new flights appear plus a morning digest of all available options.

---

## Flight Search

**Source airports:** SFO, SJC, OAK

**Destinations:** LAX, SAN, SNA, SEA, PDX, YVR, SJU, HNL, OGG, KOA, LIH, ORD, DEN, JFK, LGA, MDT

**Route pairs:** ~16 destinations × 3 origins = 48 route pairs per run

**API endpoint:** `POST https://mtier.flyfrontier.com/flightavailabilityssv/FlightAvailabilitySimpleSearch`

**Lookout window:** Next 10 days from run date

**GoWild price filter:** Base fare < $5.00 on both outbound and return legs

**Weekend window (per trip):**
- Outbound: Thursday ≥ 17:00 local time **or** Friday any time
- Return: Sunday any time **or** Monday ≤ 20:00 local time
- Remote days covered: Friday (if Thu departure) and/or Monday (if Mon return)
- Both legs must independently satisfy GoWild pricing

---

## Notification System

**Channel:** Email-to-SMS via `7173799089@vtext.com` (Verizon gateway, free)

**SMTP:** Gmail with app password stored as GitHub secret (`GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`)

**Two notification types:**

1. **New flight alert** (both runs) — triggered when a route+date combo not in state is found:
   ```
   SFO>LAX Thu5/15 6p>Sun5/18 4p $24
   OAK>SEA Fri5/16 7a>Mon5/19 8p $30
   ```

2. **Morning digest** (8 AM run only) — all currently available round trips, one per SMS, no header text

**SMS limit:** 160 chars per message. Each flight is one line. Multiple SMS messages sent if needed.

---

## Deduplication & State

**State file:** `state/seen_flights.json` committed back to the repo after each run

**Key format:** `{origin}-{destination}-{outbound_date}-{return_date}` (e.g. `SFO-LAX-2026-05-15-2026-05-18`)

**Logic:**
- Load state at run start
- Compare found flights against state
- New keys → send new flight alert SMS, add to state
- Expired keys (outbound date passed) → remove from state
- Save + commit state after run

---

## GitHub Actions Schedule

```yaml
# Runs at 8 AM and 6 PM Pacific (UTC-7 in summer)
cron: '0 15,1 * * *'
```

**Secrets required:**
- `GMAIL_ADDRESS` — sender Gmail address
- `GMAIL_APP_PASSWORD` — Gmail app password (not account password)

---

## Error Handling

- API call failure → send error SMS: `GoWild watcher error: {short description}`
- Partial failure (some routes fail) → continue remaining routes, report error count in digest
- State commit failure → log warning, do not crash (next run will re-detect as "new")

---

## Project Structure

```
gowild-watcher/
├── .github/workflows/watcher.yml
├── watcher.py
├── state/
│   └── seen_flights.json
└── requirements.txt
```
