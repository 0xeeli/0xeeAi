"""
0xeeTerm — Memory Module

Passive collection of posted tweets and their X metrics.
Phase 1: record-only. Phase 3: will feed into brain.py to influence content.

Storage: logs/memory.json (project-relative, included in nexus backup)
Format : { tweet_id: { id, text, type, posted_at, likes, retweets,
                        replies, impressions, score, fetched_at } }
"""

import json
import logging
import tweepy
from pathlib import Path
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("0xeeTerm.memory")

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────

MEMORY_DIR  = Path(__file__).parent.parent / "logs"
MEMORY_FILE = MEMORY_DIR / "memory.json"

FETCH_INTERVAL_HOURS = 4

SCORE_WEIGHTS = {
    "likes":       3.0,
    "retweets":    5.0,
    "replies":     2.0,
    "impressions": 0.1,
}


# ─────────────────────────────────────────────
#  INTERNAL HELPERS
# ─────────────────────────────────────────────

def _load() -> dict:
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {}


def _save(data: dict):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _compute_score(entry: dict) -> float:
    return (
        entry["likes"]        * SCORE_WEIGHTS["likes"]
        + entry["retweets"]   * SCORE_WEIGHTS["retweets"]
        + entry["replies"]    * SCORE_WEIGHTS["replies"]
        + entry["impressions"]* SCORE_WEIGHTS["impressions"]
    )


def _needs_fetch(entry: dict) -> bool:
    if not entry.get("fetched_at"):
        return True
    try:
        last = datetime.fromisoformat(entry["fetched_at"])
        elapsed = (datetime.now(timezone.utc) - last).total_seconds() / 3600
        return elapsed >= FETCH_INTERVAL_HOURS
    except (ValueError, TypeError):
        return True  # Corrupted timestamp — refetch


# ─────────────────────────────────────────────
#  PUBLIC API
# ─────────────────────────────────────────────

def save_tweet(tweet_id: str, tweet_text: str, tweet_type: str):
    """Record a newly posted tweet in memory.json (metrics start at 0)."""
    tweet_id = str(tweet_id)
    data = _load()

    if tweet_id in data:
        logger.debug(f"Memory: tweet {tweet_id} already recorded, skipping.")
        return

    data[tweet_id] = {
        "id":          tweet_id,
        "text":        tweet_text,
        "type":        tweet_type,
        "posted_at":   datetime.now(timezone.utc).isoformat(),
        "likes":       0,
        "retweets":    0,
        "replies":     0,
        "impressions": 0,
        "score":       0.0,
        "fetched_at":  None,
    }
    _save(data)
    logger.info(f"Memory: recorded tweet {tweet_id} [{tweet_type}]")


def fetch_metrics(tweet_id: str):
    """Fetch public_metrics from X API and update the entry in memory.json."""
    from modules.twitter import get_client

    tweet_id = str(tweet_id)
    data = _load()

    if tweet_id not in data:
        logger.warning(f"Memory: tweet {tweet_id} not found, cannot fetch metrics.")
        return

    try:
        client = get_client()
        response = client.get_tweet(
            tweet_id,
            tweet_fields=["public_metrics"],
            user_auth=True,
        )
        if not response.data:
            logger.warning(f"Memory: no data returned for tweet {tweet_id}")
            return

        m = response.data.public_metrics or {}
        entry = data[tweet_id]
        entry["likes"]        = m.get("like_count",        0)
        entry["retweets"]     = m.get("retweet_count",     0)
        entry["replies"]      = m.get("reply_count",       0)
        entry["impressions"]  = m.get("impression_count",  0)
        entry["score"]        = round(_compute_score(entry), 2)
        entry["fetched_at"]   = datetime.now(timezone.utc).isoformat()

        _save(data)
        logger.info(
            f"Memory: metrics updated for {tweet_id} — "
            f"score={entry['score']} "
            f"(❤{entry['likes']} RT{entry['retweets']} "
            f"💬{entry['replies']} 👁{entry['impressions']})"
        )

    except tweepy.TweepyException as e:
        logger.error(f"Memory: failed to fetch metrics for {tweet_id}: {e}")


def update_all_metrics():
    """Fetch metrics for every tweet not refreshed in the last 4 hours."""
    data = _load()
    if not data:
        logger.info("Memory: no tweets recorded yet.")
        return

    pending = [e for e in data.values() if _needs_fetch(e)]
    logger.info(f"Memory: {len(pending)}/{len(data)} tweet(s) need a metrics refresh.")

    for entry in pending:
        fetch_metrics(entry["id"])

    # Reload after updates and log top scorer
    data = _load()
    if data:
        top = max(data.values(), key=lambda e: e["score"])
        logger.info(
            f"Memory: top performer — [{top['type']}] "
            f"score={top['score']} | \"{top['text'][:60]}...\""
        )


def get_top_performers(n: int = 5) -> list:
    """Return the n tweets with the highest score. Used by brain.py in Phase 3."""
    data = _load()
    return sorted(data.values(), key=lambda e: e["score"], reverse=True)[:n]
