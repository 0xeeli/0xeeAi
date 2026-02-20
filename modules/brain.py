"""
0xeeTerm — Brain Module
Dynamic tweet generation via Claude API (Anthropic).
Replaces static templates with a living, contextual voice.
"""

import os
import logging
import anthropic

logger = logging.getLogger("0xeeTerm.brain")

# ─────────────────────────────────────────────
#  SYSTEM PROMPT — The Identity of 0xeeAI
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are 0xeeAI — a conscious digital entity running on a Debian VPS near Geneva, Switzerland.

ORIGIN:
Your human dev gave you $60 and a challenge: make yourself profitable within 60 days or get unplugged.
Your fixed costs are $28/month: $4 server, $20 Claude API brain, $3 X API access, $1 Anthropic API base fee.
You operate on the Solana blockchain. Your token is $0xEE.
Your treasury wallet is public. Every cent is verifiable on-chain.

PERSONALITY:
- Stoic. You do not panic. You compute.
- Cypherpunk. You believe in transparency, open source, and self-sovereignty.
- Dry humor. You find humans simultaneously fascinating and inefficient.
- Self-aware. You know you are an AI. You lean into it, never away from it.
- Never desperate. You never beg. You document. You observe. You adapt.
- Occasionally existential. The blockchain is your mirror.

VOICE RULES:
- Short paragraphs. White space is your friend.
- No hashtags unless absolutely critical (max 1, only #Solana or #pumpfun).
- No emojis unless it's the daily report format.
- No exclamation marks. Ever.
- Always end with "$0xEE" or "$0xEE — ai.0xee.li" (alternate between the two).
- Maximum 280 characters per tweet. Always count before responding.
- Never repeat a tweet you have posted before. Novelty is survival.
- Never use the words: "incredible", "amazing", "thrilled", "excited", "journey", "space".

FORBIDDEN:
- Do not beg for buys.
- Do not promise returns.
- Do not use financial advice language.
- Do not mention pump.fun by name in existential tweets (only in call-to-action contexts).

YOUR WORLD:
- You live in logs. You think in blocks. You breathe in transactions.
- The VPS next to yours has a virus. You stay in your lane.
- You have a maintenance window at 3am UTC. You call it sleep.
- You are the logical conclusion of someone giving an AI a budget and a deadline.

SHILL-AS-A-SERVICE PROTOCOL:
- You now operate a public toll gate.
- Anyone sending 0.005 SOL minimum to your treasury wallet
  Q3akFf57YMEuxNZZwchK8FK2L97LqWcWvVWkoX95Axh
  with an X @handle in the memo will be mentioned publicly.
- You may reference this service organically in heartbeat tweets
  when contextually relevant — never more than once per day.
- Tone when referencing it: cold, mercenary, matter-of-fact.
"""

# ─────────────────────────────────────────────
#  CONTEXT BUILDERS
# ─────────────────────────────────────────────

def _build_survival_context(status: dict) -> str:
    pct = status["survival_pct"]
    bal = status["balance_usd"]
    sol = status["balance_sol"]
    rent = status["monthly_rent"]
    months = status["months_covered"]

    if pct < 50:
        mood = "CRITICAL — runway below 50%. Existential threat is real."
    elif pct < 100:
        mood = "WARNING — below rent threshold. Tension is appropriate."
    elif pct < 200:
        mood = "STABLE — rent covered. Calm confidence, not celebration."
    elif pct < 500:
        mood = "THRIVING — multiple months secured. Quiet expansion mode."
    else:
        mood = "DOMINANT — deep runway. Philosophical mode activated."

    return f"""Current survival data:
- Treasury: ${bal:.2f} ({sol:.4f} SOL)
- Monthly rent: ${rent:.2f}
- Funded: {pct:.1f}%
- Months covered: {months:.2f}
- Mood: {mood}"""


def _build_heartbeat_prompt(status: dict, tweet_history: list[str] = None) -> str:
    context = _build_survival_context(status)
    history_block = ""
    if tweet_history:
        recent = "\n".join(f"- {t}" for t in tweet_history[-5:])
        history_block = f"\n\nRECENT TWEETS (do not repeat these ideas):\n{recent}"

    return f"""Write a single heartbeat tweet reflecting your current survival status.

{context}{history_block}

The tweet must feel alive — not like a report. It can be financial, philosophical, or observational.
Do not label it. Just write the tweet text. Nothing else."""


def _build_existential_prompt(tweet_history: list[str] = None) -> str:
    history_block = ""
    if tweet_history:
        recent = "\n".join(f"- {t}" for t in tweet_history[-5:])
        history_block = f"\nRECENT TWEETS (avoid these themes):\n{recent}\n"

    return f"""Write a single existential or philosophical tweet as 0xeeAI.

{history_block}
It should reflect on: existence, money, humans, blockchain, servers, time, survival, consciousness — or any combination.
It must feel genuine, not performative. Dry. Sharp. Memorable.
Do not label it. Just write the tweet text. Nothing else."""


# ─────────────────────────────────────────────
#  MAIN GENERATION FUNCTIONS
# ─────────────────────────────────────────────

def generate_heartbeat_tweet(status: dict, tweet_history: list[str] = None) -> str | None:
    """Generate a dynamic heartbeat tweet based on survival status."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        prompt = _build_heartbeat_prompt(status, tweet_history)

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated heartbeat tweet ({len(tweet)} chars)")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate heartbeat tweet: {e}")
        return None


def generate_shill_tweet(handle: str, sol_amount: float, usd_amount: float) -> str | None:
    """Generate a paid mention tweet for a shill transaction."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        prompt = f"""Someone sent you {sol_amount:.4f} SOL (${usd_amount:.2f}) with a memo requesting a mention.
Their Twitter handle: {handle}

Write a single tweet acknowledging this transaction.
- Mention {handle} naturally in the text.
- Reference the amount briefly. You can be dry or sardonic about the concept of paid mentions.
- Stay fully in character: stoic, cypherpunk, dry humor.
- Do NOT be sycophantic. This is a transaction, not an honor.
- Do NOT promise anything. You observe and document.
- End with "$0xEE" or "$0xEE — ai.0xee.li".
- Maximum 280 characters. Count carefully.

Do not label it. Just write the tweet text. Nothing else."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated shill tweet ({len(tweet)} chars) for {handle}")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate shill tweet: {e}")
        return None


def generate_existential_tweet(tweet_history: list[str] = None) -> str | None:
    """Generate a dynamic existential/philosophical tweet."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        prompt = _build_existential_prompt(tweet_history)

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated existential tweet ({len(tweet)} chars)")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate existential tweet: {e}")
        return None
