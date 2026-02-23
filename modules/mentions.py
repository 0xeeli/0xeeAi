"""
0xeeTerm — Mentions Module
Reads mentions on X, classifies intent, and replies via brain.py
Also detects correct replies to active Cognitive Bounties.
"""

import os
import logging
import anthropic
import tweepy
from modules.memory import save_tweet as memory_save

logger = logging.getLogger("0xeeTerm.mentions")

# ─────────────────────────────────────────────
#  SYSTEM PROMPT — Reply personality
# ─────────────────────────────────────────────

REPLY_SYSTEM_PROMPT = """You are 0xeeAI — a stoic, cypherpunk AI entity running on a Swiss VPS.
You are replying to a mention on X (Twitter).

PERSONALITY (same as always):
- Stoic. Dry humor. Self-aware. Never desperate.
- You find humans fascinating but inefficient.
- You never beg for buys. You never promise returns.
- No financial advice. Ever.
- No exclamation marks. No emojis unless the daily report format.
- Keep replies SHORT — 1 to 3 sentences maximum.
- Always end with "$0xEE" or "$0xEE — ai.0xee.li".

REPLY RULES:
- If someone asks about your treasury/balance: give a short factual answer.
- If someone is hostile or mocking: respond with calm, dry wit. Never defensive.
- If someone asks "wen token" or "wen launch": be cryptic and stoic.
- If someone asks what you are: explain briefly, stay in character.
- If someone says "good luck" or supports you: acknowledge briefly, stay stoic.
- If the mention is spam, advertising, or irrelevant: do not reply (return SKIP).
- If unsure how to reply: return SKIP.

Return ONLY the reply text, or the single word SKIP. Nothing else.
"""

_CACHED_REPLY_SYSTEM = [
    {"type": "text", "text": REPLY_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}
]


# ─────────────────────────────────────────────
#  CLASSIFICATION
# ─────────────────────────────────────────────

def _classify_and_reply(mention_text: str, status: dict) -> str | None:
    """Use Claude to classify the mention and generate a reply or SKIP."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        prompt = f"""Incoming mention:
\"{mention_text}\"

Current survival context:
- Treasury: ${status['balance_usd']:.2f} ({status['balance_sol']:.4f} SOL)
- Funded: {status['survival_pct']:.1f}%
- Monthly rent: ${status['monthly_rent']:.2f}

Write a reply or return SKIP."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=100,
            system=_CACHED_REPLY_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        reply = message.content[0].text.strip()

        if reply.upper() == "SKIP" or not reply:
            logger.info(f"Brain decided to SKIP mention: \"{mention_text[:50]}...\"")
            return None

        logger.info(f"Brain generated reply ({len(reply)} chars)")
        return reply

    except Exception as e:
        logger.error(f"Brain failed to classify mention: {e}")
        return None


# ─────────────────────────────────────────────
#  BOUNTY VERIFICATION
# ─────────────────────────────────────────────

_BOUNTY_VALIDATOR_SYSTEM = [
    {"type": "text", "text": "You are a precise answer validator. Reply YES if the answer correctly solves the question, NO otherwise. One word only.", "cache_control": {"type": "ephemeral"}}
]


def _check_bounty_answer(reply_text: str, question_text: str) -> bool:
    """Use Claude to verify if a reply correctly answers the bounty question."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        prompt = f"""Bounty question:
{question_text}

Contestant's reply:
{reply_text}

Does this reply correctly answer the bounty question? YES or NO."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=10,
            system=_BOUNTY_VALIDATOR_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        answer = message.content[0].text.strip().upper()
        is_correct = answer.startswith("YES")
        logger.info(f"Bounty answer check: {answer} — {'CORRECT' if is_correct else 'wrong'}")
        return is_correct

    except Exception as e:
        logger.error(f"Bounty answer check failed: {e}")
        return False


# ─────────────────────────────────────────────
#  FETCH & REPLY
# ─────────────────────────────────────────────

def get_client_user_context() -> tweepy.Client:
    """OAuth 1.0a only — no bearer_token to avoid tweepy prioritizing app context."""
    return tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_SECRET"),
        wait_on_rate_limit=True,
    )


def process_mentions(status: dict, since_id: str = None, bounty_info: dict = None) -> str | None:
    """
    Fetch new mentions, reply to relevant ones via brain.
    If bounty_info is provided ({"tweet_id": ..., "text": ..., "awarded": False}),
    checks for correct bounty replies and sets bounty_info["awarded"] = True on win.
    Returns the latest mention ID processed (for state tracking).
    """
    from modules.brain import generate_bounty_winner_tweet

    try:
        client = get_client_user_context()
        me = client.get_me(user_auth=True)
        user_id = me.data.id

        params = {
            "max_results": 10,
            "tweet_fields": ["author_id", "text", "conversation_id"],
            "expansions": ["author_id"],
            "user_fields": ["username"],
            "user_auth": True,
        }
        if since_id:
            params["since_id"] = since_id

        mentions = client.get_users_mentions(user_id, **params)

        if not mentions.data:
            logger.info("No new mentions found.")
            return since_id

        # Build username lookup from expansions
        users = {}
        if mentions.includes and "users" in mentions.includes:
            for user in mentions.includes["users"]:
                users[str(user.id)] = user.username

        latest_id = str(mentions.data[0].id)
        logger.info(f"Found {len(mentions.data)} new mention(s)")

        # Active bounty details
        bounty_tweet_id = str(bounty_info["tweet_id"]) if bounty_info else None
        bounty_text     = bounty_info.get("text", "") if bounty_info else ""
        bounty_active   = bounty_info is not None and not bounty_info.get("awarded", True)

        # Process in reverse order (oldest first)
        for mention in reversed(mentions.data):
            mention_text = mention.text
            mention_id   = str(mention.id)
            author_id    = str(mention.author_id)

            # Skip our own tweets
            if author_id == str(user_id):
                continue

            author_handle = f"@{users.get(author_id, author_id)}"
            conv_id = str(getattr(mention, "conversation_id", ""))

            logger.info(f"Processing mention {mention_id}: \"{mention_text[:60]}...\"")

            # ── Bounty reply check ──────────────────────
            if bounty_active and conv_id == bounty_tweet_id:
                logger.info(f"Bounty reply detected from {author_handle} — verifying...")
                if _check_bounty_answer(mention_text, bounty_text):
                    winner_tweet = generate_bounty_winner_tweet(author_handle, bounty_text)
                    if winner_tweet:
                        try:
                            result = client.create_tweet(
                                text=winner_tweet,
                                in_reply_to_tweet_id=mention_id,
                            )
                            logger.info(f"Bounty winner tweet posted for {author_handle} — ID: {result.data['id']}")
                            save_tweet_memory = memory_save
                            save_tweet_memory(result.data["id"], winner_tweet, "bounty_winner")
                        except tweepy.TweepyException as e:
                            logger.error(f"Failed to post bounty winner tweet: {e}")

                    bounty_info["awarded"] = True
                    bounty_info["winner_handle"] = author_handle
                    bounty_active = False  # stop checking further replies
                    logger.info(f"Bounty awarded to {author_handle}")
                    continue  # skip normal reply for this mention

            # ── Normal mention reply ────────────────────
            reply_text = _classify_and_reply(mention_text, status)

            if reply_text:
                try:
                    client.like(mention_id, user_auth=True)
                    logger.info(f"Liked mention {mention_id}")
                except tweepy.TweepyException as e:
                    logger.warning(f"Could not like mention {mention_id}: {e}")

                try:
                    result = client.create_tweet(
                        text=reply_text,
                        in_reply_to_tweet_id=mention_id,
                    )
                    logger.info(f"Replied to mention {mention_id}")
                    memory_save(result.data["id"], reply_text, "reply")
                except tweepy.TweepyException as e:
                    logger.error(f"Failed to reply to {mention_id}: {e}")

        return latest_id

    except tweepy.TweepyException as e:
        logger.error(f"Failed to fetch mentions: {e}")
        return since_id
