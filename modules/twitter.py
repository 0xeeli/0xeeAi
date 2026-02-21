"""
0xeeTerm — Twitter/X Module
Handles all interactions with the X API v2
"""

import os
import tweepy
import logging

logger = logging.getLogger("0xeeTerm.twitter")


def get_client() -> tweepy.Client:
    """Initialize and return an authenticated Tweepy client."""
    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_SECRET"),
        wait_on_rate_limit=True,
    )
    return client


def post_tweet(text: str) -> dict | None:
    """Post a tweet and return the response."""
    if len(text) > 280:
        logger.warning(f"Tweet exceeds 280 chars ({len(text)}) — truncating")
        cutoff = text.rfind(" ", 0, 277)
        text = text[:cutoff if cutoff > 0 else 277] + "..."
    try:
        client = get_client()
        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        logger.info(f"Tweet posted successfully — ID: {tweet_id}")
        return {"id": tweet_id, "text": text}
    except tweepy.TweepyException as e:
        logger.error(f"Failed to post tweet: {e}")
        return None


def get_mentions(since_id: str = None) -> list:
    """Fetch recent mentions of the account."""
    try:
        client = get_client()
        me = client.get_me()
        user_id = me.data.id
        params = {"max_results": 10}
        if since_id:
            params["since_id"] = since_id
        mentions = client.get_users_mentions(user_id, **params)
        if mentions.data:
            logger.info(f"Fetched {len(mentions.data)} mentions")
            return mentions.data
        return []
    except tweepy.TweepyException as e:
        logger.error(f"Failed to fetch mentions: {e}")
        return []


def get_latest_tweet_id() -> str | None:
    """Get the ID of our latest tweet (for since_id tracking)."""
    try:
        client = get_client()
        me = client.get_me()
        tweets = client.get_users_tweets(me.data.id, max_results=5)
        if tweets.data:
            return tweets.data[0].id
        return None
    except tweepy.TweepyException as e:
        logger.error(f"Failed to get latest tweet: {e}")
        return None
