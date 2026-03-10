"""
0xeeTerm — Roast Module
Roast-as-a-Service: processes ROAST memos, generates ruthless cypherpunk roasts,
posts publicly (reply or standalone), then posts a confirmation tweet.

Memo format : ROAST @TargetHandle <tweet_url_or_id>
  @TargetHandle = the Twitter account whose tweet is being roasted (not the buyer)
  The buyer is anonymous — identified only by the sending wallet address.
Min payment : 0.01 SOL
"""

import logging

logger = logging.getLogger("0xeeTerm.roast")


def process_roast(handle: str, tweet_id: str, sol_received: float, sol_price: float) -> dict | None:
    """
    Handle a ROAST service request end-to-end:
    1. Fetch the target tweet text
    2. Generate the roast via brain
    3. Reply to the target tweet
    4. Post a public confirmation tweet
    Returns {"reply_result": ..., "confirm_result": ...} or None on failure.
    """
    from modules.twitter import get_tweet_text, post_reply, post_tweet
    from modules.brain import generate_roast_tweet

    usd = round(sol_received * sol_price, 2)

    # 1. Fetch the target tweet (may be None if private/deleted)
    tweet_text = get_tweet_text(tweet_id) if tweet_id else None
    if not tweet_text:
        logger.warning(f"Roast: could not fetch tweet {tweet_id} — proceeding without context")

    # 2. Generate the roast
    roast_text = generate_roast_tweet(tweet_text, handle)
    if not roast_text:
        logger.error(f"Roast: brain failed to generate roast for {handle}")
        return None

    # 3. Reply to the target tweet — fall back to standalone tweet if API blocks the reply
    #    (403: bot not mentioned/engaged by author of target tweet)
    reply_result = post_reply(roast_text, tweet_id) if tweet_id else None
    if reply_result:
        logger.info(f"Roast: reply posted for {handle} — ID: {reply_result['id']}")
    else:
        # Fallback: standalone tweet with target URL embedded so context is visible
        # Reserve 45 chars for "\n\nhttps://x.com/i/status/<19-digit-id>"
        tweet_url = f"https://x.com/i/status/{tweet_id}" if tweet_id else ""
        max_roast = 280 - len(tweet_url) - 2 if tweet_url else 280
        body = roast_text[:max_roast].rstrip()
        standalone = f"{body}\n\n{tweet_url}".strip() if tweet_url else body
        reply_result = post_tweet(standalone)
        if not reply_result:
            logger.error(f"Roast: both reply and standalone fallback failed for {handle}")
            return None
        logger.info(f"Roast: posted as standalone (reply blocked) for {handle} — ID: {reply_result['id']}")

    # 4. Confirmation tweet — handle is the TARGET, not the buyer
    confirm_text = (
        f"ROAST EXECUTED\n\n"
        f"Target: {handle}\n"
        f"0.01 SOL received. Treasury +${usd:.2f}.\n"
        f"The blockchain has receipted this transaction.\n\n"
        f"$0xEE — ai.0xee.li"
    )
    confirm_result = post_tweet(confirm_text)
    if confirm_result:
        logger.info(f"Roast: confirmation posted — ID: {confirm_result['id']}")
    else:
        logger.warning(f"Roast: confirmation tweet failed (reply was still posted)")

    return {"reply_result": reply_result, "confirm_result": confirm_result}
