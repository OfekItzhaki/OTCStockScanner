import snscrape.modules.twitter as sntwitter

def get_twitter_news(ticker, max_results=5):
    query = f"${ticker} since:2024-01-01"
    tweets = []
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i >= max_results:
            break
        tweets.append({
            "title": tweet.content[:80] + "...",
            "link": f"https://twitter.com/{tweet.user.username}/status/{tweet.id}",
            "summary": tweet.content
        })
    return tweets
