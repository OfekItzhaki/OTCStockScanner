
import os

WATCHLIST_FILE = "watchlist.txt"

def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return []
    with open(WATCHLIST_FILE, "r") as f:
        return [line.strip().upper() for line in f if line.strip()]
