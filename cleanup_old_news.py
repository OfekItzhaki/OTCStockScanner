import csv
from datetime import datetime, timedelta

CSV_FILE = "news_summaries.csv"
DAYS_TO_KEEP = 7  # Change this number as you want

def cleanup_csv():
    cutoff_date = datetime.now() - timedelta(days=DAYS_TO_KEEP)
    rows_to_keep = []

    try:
        with open(CSV_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                # row[0] is date in YYYY-MM-DD format
                try:
                    row_date = datetime.strptime(row[0], "%Y-%m-%d")
                    if row_date >= cutoff_date:
                        rows_to_keep.append(row)
                except Exception:
                    # If date parsing fails, keep row to avoid accidental data loss
                    rows_to_keep.append(row)
    except FileNotFoundError:
        print(f"{CSV_FILE} not found, nothing to clean.")
        return

    # Rewrite CSV with filtered rows
    with open(CSV_FILE, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows_to_keep)

    print(f"Cleanup done. Kept {len(rows_to_keep)} rows newer than {DAYS_TO_KEEP} days.")

if __name__ == "__main__":
    cleanup_csv()
