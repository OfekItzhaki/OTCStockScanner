# OTC CE/Expert Tracker and News Summarizer

This project monitors OTC Markets Caveat Emptor (CE) and Expert Market (EM) stock listings, tracks daily entries and exits, fetches relevant news, summarizes it using AI, and sends alerts via Telegram and desktop notifications. It also integrates with Interactive Brokers (IBKR) to pull your portfolio watchlist tickers and fetch news for them.

---

## Features

- Downloads CE and Expert Market listings directly from OTC Markets FTP server daily.
- Tracks which stocks entered or exited CE/Expert status each day and logs changes in SQLite.
- Maintains a 7-day history of CE/Expert stocks.
- Fetches news for portfolio tickers and CE/Expert changed tickers.
- Summarizes news items using AI.
- Sends alerts via Telegram and desktop notifications.
- Logs activity and errors for troubleshooting.

---

## Getting Started

### Prerequisites

- Python 3.8+
- Interactive Brokers API (IBKR) access and API keys
- Telegram bot and chat setup (optional for alerts)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/otc-ce-expert-tracker.git
cd otc-ce-expert-tracker
```

2. Create and activate a Python virtual environment:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your secrets:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
IBKR_USERNAME=your_ibkr_username
IBKR_PASSWORD=your_ibkr_password
# Add any other environment variables your scripts require
```

---

## Usage

### Run the CE/Expert Monitor

This script downloads CE and Expert Market data, tracks entries/exits, and stores them in the database.

```bash
python ce_expert_monitor.py
```

### Run the News Fetcher and Summarizer

This script connects to IBKR, retrieves your portfolio tickers, adds CE/Expert entries and exits tickers, fetches news, summarizes it, and sends alerts.

```bash
python run_news_from_ibkr_watchlist.py
```

---

## Configuration

- `.env` file should contain all necessary API tokens and credentials.
- `monitor.log` contains logs for CE/Expert monitoring activities.
- `otc_status.db` stores ticker tracking data.
- `news_summaries.csv` stores news summaries with dates.

---

## Notes

- The CE/Expert data is downloaded from OTC Markets FTP server; make sure your network allows FTP connections.
- If the script cannot download today's data, it will fallback to yesterday’s data and notify accordingly.
- Alerts are sent both to Telegram and as desktop notifications.
- Make sure your IBKR API connection is correctly configured for read-only portfolio access.

---

## License

This project is licensed under the MIT License.

---

## Contact

For questions or support, please open an issue on GitHub or contact the maintainer.

