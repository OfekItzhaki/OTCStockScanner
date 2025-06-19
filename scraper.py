import pandas as pd
from otc_scraper import get_otc_news_rss as get_otc_news

try:
    from yahoo_scraper import get_yahoo_news
except ImportError:
    def get_yahoo_news(ticker): return []

try:
    from reddit_scraper import get_reddit_mentions
except ImportError:
    def get_reddit_mentions(ticker): return []

# try:
#     from twitter_scraper import get_twitter_news
# except ImportError:
#     def get_twitter_news(ticker): return []

def get_all_news(ticker, include_sources=None):
    all_news = []

    source_map = {
        "OTCMarkets": lambda: get_otc_news(ticker),
        # "Twitter": lambda: get_twitter_news(ticker),
        # "YahooFinance": lambda: get_yahoo_news(ticker),
        # "Reddit": lambda: get_reddit_mentions(ticker),
    }

    for name, fetch_func in source_map.items():
        if include_sources and name not in include_sources:
            continue
        try:
            items = fetch_func()
            for item in items:
                item.setdefault("title", item.get("headline", "Untitled"))
                item.setdefault("summary", "")
                item.setdefault("date", "")
                item["source"] = name
                all_news.append(item)
        except Exception as e:
            print(f"⚠️ Failed fetching from {name} for {ticker}: {e}")

    df = pd.DataFrame(all_news)
    df.drop_duplicates(subset=["title"], inplace=True)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df[df["date"].notnull()]
        df.sort_values(by="date", ascending=False, inplace=True)

    return df.to_dict(orient="records")
