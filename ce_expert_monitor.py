import requests
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from alert_utils import send_alert
import logging

# Setup logging to a file
logging.basicConfig(
    filename="monitor.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DB_PATH = "otc_status.db"


def fetch_tickers_from_otc(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "lxml")
    tickers = set()
    for row in soup.select("table.table tbody tr"):
        cols = row.find_all("td")
        if cols and len(cols) > 1:
            tickers.add(cols[0].text.strip())
    return tickers


def load_previous_tickers(source):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS tickers (source TEXT, ticker TEXT, date TEXT)")
    today = datetime.today().strftime("%Y-%m-%d")
    c.execute("SELECT ticker FROM tickers WHERE source=? AND date<?", (source, today))
    tickers = {row[0] for row in c.fetchall()}
    conn.close()
    return tickers


def save_today_tickers(source, tickers):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.today().strftime("%Y-%m-%d")
    c.execute("DELETE FROM tickers WHERE source=? AND date=?", (source, today))
    for ticker in tickers:
        c.execute("INSERT INTO tickers (source, ticker, date) VALUES (?, ?, ?)", (source, ticker, today))
    conn.commit()
    conn.close()


def track_entries_and_exits(source_name, url):
    print(f"Tracking {source_name}...")

    today = datetime.today().strftime("%Y-%m-%d")
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    current = fetch_tickers_from_otc(url)
    previous = load_previous_tickers(source_name)

    exited = sorted(previous - current)
    entered = sorted(current - previous)

    save_today_tickers(source_name, current)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS ce_expert_entries (
            date TEXT, source TEXT, ticker TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ce_expert_exits (
            date TEXT, source TEXT, ticker TEXT
        )
    """)

    for ticker in exited:
        c.execute("INSERT INTO ce_expert_exits (date, source, ticker) VALUES (?, ?, ?)", (today, source_name, ticker))
    for ticker in entered:
        c.execute("INSERT INTO ce_expert_entries (date, source, ticker) VALUES (?, ?, ?)", (today, source_name, ticker))

    conn.commit()
    conn.close()

    if exited:
        message = f"\U0001F6A8 {source_name} EXIT ALERT:\n" + "\n".join(exited)
        print(message)
        send_alert(f"{source_name} Exit", message)
    if entered:
        message = f"\u26A0\uFE0F {source_name} ENTRY ALERT:\n" + "\n".join(entered)
        print(message)
        send_alert(f"{source_name} Entry", message)


def get_entries_and_exits_for_date(date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT source, ticker FROM ce_expert_entries WHERE date=?", (date,))
    entries = c.fetchall()
    c.execute("SELECT source, ticker FROM ce_expert_exits WHERE date=?", (date,))
    exits = c.fetchall()
    conn.close()
    return entries, exits


def main():
    logging.info("Starting CE/Expert tracking")
    try:
        track_entries_and_exits("Caveat Emptor", "https://www.otcmarkets.com/market-activity/caveat-emptor")
        track_entries_and_exits("Expert Market", "https://www.otcmarkets.com/market-activity/expert-market")

        # Optional log today's summary
        today = datetime.today().strftime("%Y-%m-%d")
        entries, exits = get_entries_and_exits_for_date(today)
        logging.info(f"Today's entries: {entries}")
        logging.info(f"Today's exits: {exits}")

        logging.info("Tracking completed successfully")
    except Exception as e:
        error_msg = f"Error in CE/Expert tracking: {e}"
        logging.exception(error_msg)
        send_alert("Monitor Error", error_msg)


if __name__ == "__main__":
    main()
