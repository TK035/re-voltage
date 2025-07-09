import tweepy
def get_x_buzz_score(area, bearer_token):
    client = tweepy.Client(bearer_token = bearer_token)
    query = f"from:大阪 {area} 再開発"
    tweets = client.search_recent_tweets(query = query, max_results = 100)
    return len(tweets.data) if tweets.data else 0