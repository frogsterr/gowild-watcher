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

MAX_BASE_FARE = 5.00
LOOKAHEAD_DAYS = 10
EMAIL_TO = ["bs3612@columbia.edu", "fh2514@columbia.edu"]
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SUNDAY = 6
MONDAY = 0
TUESDAY = 1
OUTBOUND_EVENING_HOUR = 17    # 5 PM — earliest Wed/Thu evening departure
OUTBOUND_THURSDAY_HOUR = 17   # kept for back-compat with filter
RETURN_MONDAY_HOUR = 20       # 8 PM
