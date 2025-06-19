
from flask import Flask, render_template, request
from scraper import get_latest_stock_news
from watchlist import load_watchlist
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
ticker_news_cache = {}

def update_watchlist_news():
    print("⏱️ Running watchlist scan...")
    for ticker in load_watchlist():
        try:
            news = get_latest_stock_news(ticker)
            ticker_news_cache[ticker] = news
        except Exception as e:
            print(f"Error updating {ticker}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(update_watchlist_news, 'interval', minutes=30)
scheduler.start()
update_watchlist_news()

@app.route("/", methods=["GET", "POST"])
def index():
    ticker = request.form.get("ticker", "").strip().upper() if request.method == "POST" else ""
    news = ticker_news_cache.get(ticker, []) if ticker else []
    return render_template("index.html", ticker=ticker, news=news, watchlist=ticker_news_cache)

if __name__ == "__main__":
    app.run(debug=True)
