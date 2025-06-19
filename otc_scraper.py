import feedparser

def get_otc_news(ticker):
    url = f"https://www.otcmarkets.com/stock/{ticker}/news/rss"
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"❌ Error parsing RSS feed for {ticker}: {e}")
        return []
    
    news_items = []
    for entry in feed.entries:
        news_items.append({
            "headline": entry.title,
            "link": entry.link,
            "summary": entry.get("summary", ""),
            "date": entry.get("published", "")
        })
    return news_items
