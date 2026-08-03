ORIGINS = ["SFO", "SJC", "OAK"]

DESTINATIONS = [
    "LAX",  # Los Angeles
    "SAN",  # San Diego
    "SNA",  # Orange County
    "SEA",  # Seattle
    "PDX",  # Portland
    "YVR",  # Vancouver
    "SJU",  # San Juan, PR
    "HNL",  # Honolulu
    "OGG",  # Maui
    "KOA",  # Kona
    "LIH",  # Kauai
    "ORD",  # Chicago O'Hare
    "MDW",  # Chicago Midway
    "DEN",  # Denver
    "JFK",  # New York JFK
    "LGA",  # New York LaGuardia
    "MDT",  # Harrisburg
]

# Swept last in each collector pass, so their cached data is always the
# freshest of any destination by the time a digest email goes out.
PRIORITY_DESTINATIONS = ["LAX", "SAN", "SNA"]

MAX_BASE_FARE = 5.00
LOOKAHEAD_DAYS = 10
EMAIL_TO = ["bs3612@columbia.edu", "fh2514@columbia.edu"]

# Collector: fetches this many (origin, destination, day) work items per
# invocation, staying comfortably under Frontier's observed ~14-request
# burst ceiling. Runs on a 5-minute cron (see .github/workflows/collector.yml).
COLLECTOR_BATCH_SIZE = 10
COLLECTOR_REQUEST_DELAY_SECONDS = 0.4
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SUNDAY = 6
MONDAY = 0
TUESDAY = 1
OUTBOUND_EVENING_HOUR = 17    # 5 PM — earliest Wed/Thu evening departure
OUTBOUND_THURSDAY_HOUR = 17   # kept for back-compat with filter
RETURN_MONDAY_HOUR = 20       # 8 PM
