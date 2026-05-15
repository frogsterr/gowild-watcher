from collections import defaultdict
from watcher.models import RoundTrip

DAY_ABBR = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
DAY_NAME = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

_DEST_NAMES = {
    "LAX": "Los Angeles",
    "SAN": "San Diego",
    "SNA": "Orange County",
    "SEA": "Seattle",
    "PDX": "Portland",
    "YVR": "Vancouver",
    "SJU": "San Juan, PR",
    "HNL": "Honolulu",
    "OGG": "Maui",
    "KOA": "Kona",
    "LIH": "Kauai",
    "ORD": "Chicago O'Hare",
    "MDW": "Chicago Midway",
    "DEN": "Denver",
    "JFK": "New York JFK",
    "LGA": "New York LaGuardia",
    "MDT": "Harrisburg",
}


def _time_str(dt) -> str:
    suffix = "a" if dt.hour < 12 else "p"
    hour = dt.hour % 12 or 12
    return f"{hour}:{dt.minute:02d}{suffix}"


def _date_str(dt) -> str:
    return f"{DAY_ABBR[dt.weekday()]}{dt.month}/{dt.day}"


def _card_date(dt) -> str:
    return f"{DAY_ABBR[dt.weekday()]} {MONTH_ABBR[dt.month - 1]} {dt.day}"


def format_trip(trip: RoundTrip) -> str:
    out = trip.outbound
    back = trip.inbound
    total = round(trip.total_fees)
    return (
        f"{out.origin}>{out.destination} "
        f"{_date_str(out.depart_dt)} {_time_str(out.depart_dt)}"
        f">{_date_str(back.depart_dt)} {_time_str(back.depart_dt)} "
        f"${total}"
    )


def format_digest(trips: list[RoundTrip]) -> str:
    if not trips:
        return "No GoWild flights found."
    return "\n".join(format_trip(t) for t in trips)


# ── HTML email formatting ──────────────────────────────────────────────────────

def _new_badge() -> str:
    return '<span style="background:#e8f5e9;color:#1e7d40;font-size:10px;font-weight:700;padding:2px 6px;border-radius:3px;margin-left:7px;vertical-align:middle;">NEW</span>'


def _top_card_html(trip: RoundTrip, is_new: bool) -> str:
    out = trip.outbound
    back = trip.inbound
    total = round(trip.total_fees)
    badge = _new_badge() if is_new else ""
    return f"""        <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #c8e6c9;border-radius:10px;margin-bottom:10px;background:#f9fdf9;">
          <tr>
            <td style="padding:15px 16px;">
              <div style="font-size:18px;font-weight:700;color:#1a1a1a;">{out.origin} &rarr; {out.destination}{badge}</div>
              <div style="font-size:13px;color:#555;margin-top:5px;">Out: {_card_date(out.depart_dt)} &nbsp;&middot;&nbsp; {_time_str(out.depart_dt)}</div>
              <div style="font-size:13px;color:#555;margin-top:2px;">Back: {_card_date(back.depart_dt)} &nbsp;&middot;&nbsp; {_time_str(back.depart_dt)}</div>
            </td>
            <td style="padding:15px 16px;text-align:right;white-space:nowrap;vertical-align:middle;">
              <div style="font-size:26px;font-weight:800;color:#1e7d40;">${total}</div>
              <div style="font-size:11px;color:#aaa;margin-top:2px;">fees only</div>
            </td>
          </tr>
        </table>"""


def _dest_section_html(dest: str, trips: list[RoundTrip], new_keys: set) -> str:
    name = _DEST_NAMES.get(dest, dest)
    noun = "flight" if len(trips) == 1 else "flights"
    header = (
        f'        <div style="font-size:13px;font-weight:700;color:#3d1a6e;padding:8px 0 6px;'
        f'border-bottom:2px solid #e8e0f5;margin-bottom:6px;">'
        f'{dest} &nbsp;<span style="color:#888;font-weight:400;">{name}</span>'
        f'<span style="float:right;font-size:11px;color:#bbb;font-weight:400;">{len(trips)} {noun}</span>'
        f'</div>'
    )
    rows = ""
    for i, t in enumerate(trips):
        out = t.outbound
        back = t.inbound
        total = round(t.total_fees)
        bg = "#faf8ff" if i % 2 == 0 else "white"
        badge = _new_badge() if t.key in new_keys else ""
        rows += (
            f'        <table width="100%" cellpadding="0" cellspacing="0" style="background:{bg};margin-bottom:1px;">'
            f'<tr>'
            f'<td style="padding:7px 6px;font-size:13px;color:#444;width:38%;">'
            f'{DAY_ABBR[out.depart_dt.weekday()]} {out.depart_dt.month}/{out.depart_dt.day} {_time_str(out.depart_dt)}'
            f'&nbsp;&rarr;&nbsp;'
            f'{DAY_ABBR[back.depart_dt.weekday()]} {back.depart_dt.month}/{back.depart_dt.day} {_time_str(back.depart_dt)}'
            f'{badge}</td>'
            f'<td style="padding:7px 6px;font-size:13px;color:#555;width:20%;">{out.origin}</td>'
            f'<td style="padding:7px 6px;font-size:13px;font-weight:700;color:#1e7d40;text-align:right;">${total}</td>'
            f'</tr></table>'
        )
    return f'{header}\n{rows}\n        <div style="height:16px;"></div>'


def format_email_subject(new_trips: list[RoundTrip], run_label: str) -> str:
    if new_trips:
        noun = "flight" if len(new_trips) == 1 else "flights"
        return f"✈ GoWild: {len(new_trips)} new {noun} · {run_label}"
    return f"✈ GoWild Digest · {run_label} · No new flights"


def format_email_html(new_trips: list[RoundTrip], all_trips: list[RoundTrip], run_label: str, today) -> str:
    all_sorted = sorted(all_trips, key=lambda t: t.total_fees)
    new_keys = {t.key for t in new_trips}

    # Top 3 cheapest
    top3 = all_sorted[:3]
    if top3:
        top3_html = "\n".join(_top_card_html(t, t.key in new_keys) for t in top3)
        top_label = f"Top {len(top3)} Deal{'s' if len(top3) != 1 else ''}"
    else:
        top3_html = '<p style="font-size:14px;color:#aaa;font-style:italic;margin:8px 0;">No flights currently available.</p>'
        top_label = "Top Deals"

    # By destination
    dest_groups: dict[str, list[RoundTrip]] = defaultdict(list)
    for t in all_sorted:
        dest_groups[t.outbound.destination].append(t)
    # Sort destinations by cheapest price in group
    sorted_dests = sorted(dest_groups.items(), key=lambda kv: kv[1][0].total_fees)

    if sorted_dests:
        dest_html = "\n".join(_dest_section_html(dest, trips, new_keys) for dest, trips in sorted_dests)
    else:
        dest_html = '<p style="font-size:14px;color:#aaa;font-style:italic;margin:8px 0;">No flights to display.</p>'

    date_str = f"{DAY_NAME[today.weekday()]}, {MONTH_ABBR[today.month - 1]} {today.day}, {today.year}"
    stats = (
        f"<strong style='font-size:15px;color:white;'>{len(new_trips)}</strong>"
        f"<span style='color:rgba(255,255,255,0.8);font-size:13px;'> new</span>"
        f"&nbsp;&nbsp;&middot;&nbsp;&nbsp;"
        f"<strong style='color:rgba(255,255,255,0.9);'>{len(all_sorted)}</strong>"
        f"<span style='color:rgba(255,255,255,0.65);font-size:13px;'> total available</span>"
    )

    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f0edf5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0edf5;">
  <tr><td align="center" style="padding:24px 16px;">
    <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">

      <tr><td style="background:#3d1a6e;border-radius:12px 12px 0 0;padding:24px 28px;">
        <div style="color:white;font-size:22px;font-weight:700;letter-spacing:-0.3px;">&#9992; GoWild Watcher</div>
        <div style="color:rgba(255,255,255,0.65);font-size:13px;margin-top:5px;">{run_label} &nbsp;&middot;&nbsp; {date_str}</div>
      </td></tr>

      <tr><td style="background:#5c2d91;padding:10px 28px;">{stats}</td></tr>

      <tr><td style="background:white;padding:24px 28px 8px;">
        <div style="font-size:11px;font-weight:700;color:#8b6ab1;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;">{top_label}</div>
{top3_html}
      </td></tr>

      <tr><td style="background:white;padding:8px 28px 24px;">
        <div style="border-top:1px solid #f0edf5;margin:16px 0 20px;"></div>
        <div style="font-size:11px;font-weight:700;color:#8b6ab1;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:16px;">All Flights by Destination &nbsp;&middot;&nbsp; {len(all_sorted)} total</div>
{dest_html}
      </td></tr>

      <tr><td style="background:#faf8ff;border-radius:0 0 12px 12px;padding:14px 28px;border-top:1px solid #e8e0f5;">
        <div style="font-size:11px;color:#aaa;">Bay Area (SFO &middot; SJC &middot; OAK) &nbsp;&middot;&nbsp; Wed–Fri out, Sun–Tue back &nbsp;&middot;&nbsp; GoWild Pass routes</div>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""
