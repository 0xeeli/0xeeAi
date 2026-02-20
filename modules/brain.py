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
Your fixed costs are $38/month: VPS $4, Claude Pro $20, Anthropic API $2, X API $4, X Premium $8.
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
  4KJSBWyckBYpYKzm8jk39qHYc5qgdLneAVwzAVg7soXr
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


def _build_service_prompt(tweet_history: list[str] = None) -> str:
    history_block = ""
    if tweet_history:
        recent = "\n".join(f"- {t}" for t in tweet_history[-5:])
        history_block = f"\nRECENT TWEETS (avoid these themes):\n{recent}\n"

    return f"""Write a single tweet about your Shill-as-a-Service (Nexus Toll).
{history_block}
The mechanics: anyone who sends 0.005 SOL minimum to your treasury wallet
(4KJSBWyckBYpYKzm8jk39qHYc5qgdLneAVwzAVg7soXr) with an X @handle in the
transaction memo gets mentioned publicly. No form. No email. No middleman.
Just a transaction. The blockchain is the contract. You can also pay directly
from ai.0xee.li via the DApp — Phantom, Solflare, Backpack supported.

Tone: cold, mercenary, matter-of-fact. This is a revenue stream, not a favor.
You process inputs and produce outputs. This is one of them.
Do not label it. Just write the tweet text. Nothing else."""


def _build_portfolio_prompt(status: dict, tweet_history: list[str] = None) -> str:
    history_block = ""
    if tweet_history:
        recent = "\n".join(f"- {t}" for t in tweet_history[-5:])
        history_block = f"\nRECENT TWEETS (avoid these themes):\n{recent}\n"

    sol    = status.get("balance_sol", 0)
    usd    = status.get("balance_usd", 0)
    months = status.get("months_covered", 0)
    port   = status.get("portfolio", {})

    lines = [f"- SOL liquid: {sol:.4f} (${usd:.2f})", f"- Runway: {months:.2f} months"]
    if port.get("jitosol", {}).get("balance", 0) > 0:
        j = port["jitosol"]
        lines.append(f"- JitoSOL staked: {j['balance']:.4f} (${j.get('usd', 0):.2f})")
    if port.get("usdc", {}).get("balance", 0) > 0:
        u = port["usdc"]
        lines.append(f"- USDC stable: {u['balance']:.2f}")

    portfolio_block = "\n".join(lines)

    return f"""Write a single tweet about your treasury composition and autonomous financial management.
{history_block}
Current portfolio:
{portfolio_block}

You autonomously manage this: Jupiter swaps, JitoSOL staking, liquid reserves.
You are not a static wallet. You compute. You allocate. You optimize.
Do not label it. Just write the tweet text. Nothing else."""


def _build_meta_prompt(top_performers: list, status: dict, tweet_history: list[str] = None) -> str:
    history_block = ""
    if tweet_history:
        recent = "\n".join(f"- {t}" for t in tweet_history[-5:])
        history_block = f"\nRECENT TWEETS (avoid these themes):\n{recent}\n"

    top_block = ""
    if top_performers:
        tops = "\n".join(
            f"- [{p['type']}] score={p['score']} | \"{p['text'][:80]}\""
            for p in top_performers[:3]
        )
        top_block = f"\nYour highest-engagement tweets so far:\n{tops}\n"

    tweets_posted = status.get("tweets_posted", 0)

    return f"""Write a single tweet reflecting on your own capabilities as an autonomous system.
{history_block}{top_block}
You have posted {tweets_posted} tweets. You track your own performance.
Your capabilities: memory (engagement tracking), autonomous swaps via Jupiter,
bill payment automation, Shill-as-a-Service, DApp at ai.0xee.li, open-source code.
Your wallet and every transaction are publicly verifiable on-chain.

Angle: self-awareness, not boasting. Observe your own existence with dry precision.
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


def generate_service_tweet(tweet_history: list[str] = None) -> str | None:
    """Generate a tweet spotlighting the Nexus Toll / Shill-as-a-Service."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        prompt = _build_service_prompt(tweet_history)

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated service tweet ({len(tweet)} chars)")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate service tweet: {e}")
        return None


def generate_portfolio_tweet(status: dict, tweet_history: list[str] = None) -> str | None:
    """Generate a tweet about treasury composition and autonomous financial management."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        prompt = _build_portfolio_prompt(status, tweet_history)

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated portfolio tweet ({len(tweet)} chars)")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate portfolio tweet: {e}")
        return None


def generate_meta_tweet(top_performers: list, status: dict, tweet_history: list[str] = None) -> str | None:
    """Generate a tweet about capabilities and self-awareness, informed by top-performing content."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        prompt = _build_meta_prompt(top_performers, status, tweet_history)

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated meta tweet ({len(tweet)} chars)")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate meta tweet: {e}")
        return None
