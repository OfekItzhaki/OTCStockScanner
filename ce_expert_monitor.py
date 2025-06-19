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


def get_exiting_ce_expert_tickers(db_path="otc_data.db"):
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

 # Example: assuming `ce_expert_status` has fields (ticker, date, is_ce, is_expert)
    query = f"""
    SELECT today.ticker
    FROM ce_expert_status today
    JOIN ce_expert_status yesterday
        ON today.ticker = yesterday.ticker
    WHERE
        today.date = ?
        AND yesterday.date = ?
        AND (yesterday.is_ce = 1 OR yesterday.is_expert = 1)
        AND (today.is_ce = 0 AND today.is_expert = 0)
    """
    cur.execute(query, (today, yesterday))
    tickers = [row[0] for row in cur.fetchall()]
    con.close()
    return tickers

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

def check_for_exits(source_name, url):
    print(f"Checking {source_name} list...")
    current = fetch_tickers_from_otc(url)
    previous = load_previous_tickers(source_name)
    exited = sorted(previous - current)
    save_today_tickers(source_name, current)

    if exited:
        message = f"🚨 {source_name} EXIT ALERT:\n" + "\n".join(exited)
        print(message)
        send_alert(f"{source_name} Exit", message)
    else:
        print(f"No exits from {source_name}.")

def main():
    logging.info("Starting CE/Expert monitoring")
    try:
        check_for_exits("Caveat Emptor", "https://www.otcmarkets.com/market-activity/caveat-emptor")
        check_for_exits("Expert Market", "https://www.otcmarkets.com/market-activity/expert-market")
        logging.info("Monitoring completed successfully")
    except Exception as e:
        error_msg = f"Error in CE/Expert monitor: {e}"
        logging.exception(error_msg)
        send_alert("Monitor Error", error_msg)

if __name__ == "__main__":
    main()
