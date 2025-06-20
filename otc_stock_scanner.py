from ibkr_connection import connect_ibkr, IBKRConnectionError
from ce_expert_monitor import (
    fetch_ce_expert_tickers,
    track_entries_and_exits,
    get_entries_and_exits_for_date
)
from scraper import get_all_news
from summarizer import summarize_text
from alert_utils import send_alert
import os
import csv
from datetime import datetime, timedelta

CSV_FILE = "news_summaries.csv"
MAX_AGE_DAYS = 7

def clean_old_news():
    if not os.path.exists(CSV_FILE):
        return
    rows = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            try:
                date = datetime.strptime(row[0], "%Y-%m-%d")
                if datetime.now() - date <= timedelta(days=MAX_AGE_DAYS):
                    rows.append(row)
            except:
                continue
    with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def append_to_csv(row):
    write_header = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Date", "Ticker", "Title", "Summary"])
        writer.writerow(row)

try:
    ib = connect_ibkr(read_only=True)
except IBKRConnectionError as e:
    print(e)
    exit(1)

try:
    positions = ib.positions()
    portfolio_tickers = list({pos.contract.symbol for pos in positions if pos.contract.symbol})
    print(f"Portfolio tickers: {portfolio_tickers}")

    combined_tickers = set(portfolio_tickers)

    # Fetch current CE/Expert tickers live from OTC Markets FTP
    try:
        ce_today, em_today = fetch_ce_expert_tickers()

        # Track entries and exits (updates DB and sends alerts)
        track_entries_and_exits("Caveat Emptor", ce_today)
        track_entries_and_exits("Expert Market", em_today)

        ce_expert_tickers = ce_today.union(em_today)
        print(f"Current CE/Expert tickers (live): {sorted(ce_expert_tickers)}")

        # Get today's entries and exits from DB for reporting
        today = datetime.today().strftime("%Y-%m-%d")
        entries, exits = get_entries_and_exits_for_date(today)

        if exits:
            exited_tickers = ", ".join(sorted({ticker for (_, ticker) in exits}))
            print(f"CE/Expert Exits Today: {exited_tickers}")
        else:
            print("CE/Expert Exits Today: []")

        if entries:
            entered_tickers = ", ".join(sorted({ticker for (_, ticker) in entries}))
            print(f"CE/Expert Entries Today: {entered_tickers}")
        else:
            print("CE/Expert Entries Today: []")

        combined_tickers.update(ce_expert_tickers)

    except Exception as e:
        print("⚠️ Failed loading or tracking CE/Expert tickers:", e)

    if not combined_tickers:
        print("❌ No tickers found.")
        exit(1)

    print(f"\n📈 Pulling news for {len(combined_tickers)} tickers...\n")
    clean_old_news()

    for ticker in combined_tickers:
        print(f"🔎 {ticker}")
        news = get_all_news(ticker, include_sources=["OTCMarkets"])
        if not news:
            print("  No news found.")
            continue

        for item in news[:3]:
            print(f"  📰 {item['title']}")
            summary_text = summarize_text(item.get("summary", ""), ticker=ticker) if item.get("summary") else "(No summary)"
            print(f"  🧠 {summary_text}")

            append_to_csv([datetime.now().strftime("%Y-%m-%d"), ticker, item["title"], summary_text])

            send_alert(
                title=f"{ticker} - {item['title']}",
                message=summary_text
            )

except Exception as e:
    print(f"❌ Error while processing: {e}")
finally:
    ib.disconnect()
