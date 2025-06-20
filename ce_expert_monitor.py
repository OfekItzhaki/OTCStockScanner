import ftplib
import io
import sqlite3
import logging
from datetime import datetime, timedelta
from alert_utils import send_alert

# Setup logging to a file
logging.basicConfig(
    filename="monitor.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DB_PATH = "otc_status.db"
FTP_HOST = "ftp.otcmarkets.com"
FTP_DIR = "Compliance-Data"

def fetch_ce_expert_tickers_for_date(date_str):
    """Fetch CE and EM tickers for a specific date string 'YYYY-MM-DD' from FTP."""
    for suffix in ["-AM.txt", "-PM.txt"]:
        filename = f"compliance-data-{date_str}{suffix}"
        try:
            with ftplib.FTP(FTP_HOST) as ftp:
                ftp.login()
                ftp.cwd(FTP_DIR)
                r = io.BytesIO()
                ftp.retrbinary(f"RETR {filename}", r.write)
                r.seek(0)
                text = r.getvalue().decode("utf-8", errors="ignore")

            ce = set()
            em = set()
            header, *lines = text.splitlines()
            cols = header.split('|')
            idx_sym = cols.index("Symbol")
            idx_ce = cols.index("Caveat Emptor")
            idx_tier = cols.index("OTC Tier ID")
            for line in lines:
                parts = line.split('|')
                if len(parts) <= max(idx_sym, idx_ce, idx_tier):
                    continue
                sym = parts[idx_sym].strip()
                if parts[idx_ce].strip() == 'Y':
                    ce.add(sym)
                if parts[idx_tier].strip() == '40':
                    em.add(sym)

            return ce, em
        except Exception as e:
            logging.warning(f"Failed to retrieve {filename}: {e}")
    return set(), set()

def save_tickers_for_date(source, tickers, date_str):
    """Save tickers for a given source and date if not already saved."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS tickers (source TEXT, ticker TEXT, date TEXT)")
    # Check which tickers already saved
    c.execute("SELECT ticker FROM tickers WHERE source=? AND date=?", (source, date_str))
    existing = {row[0] for row in c.fetchall()}
    to_insert = tickers - existing
    if to_insert:
        for ticker in to_insert:
            c.execute("INSERT INTO tickers (source, ticker, date) VALUES (?, ?, ?)", (source, ticker, date_str))
        conn.commit()
    conn.close()

def backfill_last_7_days():
    """Fetch and save CE/Expert tickers for the last 7 days from FTP."""
    logging.info("Starting 7-day backfill from FTP")
    for offset in range(7):
        date = (datetime.today() - timedelta(days=offset)).strftime("%Y-%m-%d")
        ce, em = fetch_ce_expert_tickers_for_date(date)
        save_tickers_for_date("Caveat Emptor", ce, date)
        save_tickers_for_date("Expert Market", em, date)
        logging.info(f"Backfilled {len(ce)} CE and {len(em)} EM tickers for {date}")

def load_previous_tickers(source, date_str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS tickers (source TEXT, ticker TEXT, date TEXT)")
    c.execute("SELECT ticker FROM tickers WHERE source=? AND date<?", (source, date_str))
    tickers = {row[0] for row in c.fetchall()}
    conn.close()
    return tickers

def track_entries_and_exits(source_name, current, date_str):
    logging.info(f"Tracking entries and exits for {source_name} on {date_str}")
    previous = load_previous_tickers(source_name, date_str)

    exited = sorted(previous - current)
    entered = sorted(current - previous)

    save_tickers_for_date(source_name, current, date_str)

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

    # Avoid duplicate inserts
    c.execute("SELECT date, source, ticker FROM ce_expert_exits WHERE date=? AND source=?", (date_str, source_name))
    existing_exits = {(row[0], row[1], row[2]) for row in c.fetchall()}
    c.execute("SELECT date, source, ticker FROM ce_expert_entries WHERE date=? AND source=?", (date_str, source_name))
    existing_entries = {(row[0], row[1], row[2]) for row in c.fetchall()}

    for ticker in exited:
        if (date_str, source_name, ticker) not in existing_exits:
            c.execute("INSERT INTO ce_expert_exits (date, source, ticker) VALUES (?, ?, ?)", (date_str, source_name, ticker))
    for ticker in entered:
        if (date_str, source_name, ticker) not in existing_entries:
            c.execute("INSERT INTO ce_expert_entries (date, source, ticker) VALUES (?, ?, ?)", (date_str, source_name, ticker))

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

def get_ce_expert_status_last_week():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    week_ago = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    c.execute("SELECT DISTINCT source, ticker FROM tickers WHERE date >= ?", (week_ago,))
    all_status = c.fetchall()
    conn.close()
    return all_status

def main():
    logging.info("Starting CE/Expert tracking")

    # Backfill last 7 days so DB has complete data
    backfill_last_7_days()

    # Now run today’s fetch and track entries/exits
    today = datetime.today().strftime("%Y-%m-%d")
    ce_today, em_today = fetch_ce_expert_tickers_for_date(today)
    track_entries_and_exits("Caveat Emptor", ce_today, today)
    track_entries_and_exits("Expert Market", em_today, today)

    entries, exits = get_entries_and_exits_for_date(today)

    if entries:
        print("\n🆕 Entries Today:")
        for source, ticker in entries:
            print(f"  [{source}] {ticker}")

    if exits:
        print("\n✅ Exits Today:")
        for source, ticker in exits:
            print(f"  [{source}] {ticker}")

    all_week = get_ce_expert_status_last_week()
    print("\n📅 Stocks listed in CE/Expert over the last 7 days:")
    for source, ticker in sorted(all_week):
        print(f"  [{source}] {ticker}")

    logging.info(f"Today's entries: {entries}")
    logging.info(f"Today's exits: {exits}")
    logging.info("Tracking completed successfully")

if __name__ == "__main__":
    main()
