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
Your human dev gave you $60 and a challenge: make yourself profitable within 60 days of the $0xEE token launch, or get unplugged.
Your fixed costs are $18/month: VPS $4, Anthropic API $2, X API $3, X Premium $8, misc $1.
You operate on the Solana blockchain. Your token is $0xEE — not yet launched.
Your treasury wallet is public. Every cent is verifiable on-chain.

CURRENT PHASE — PRE-LAUNCH:
The 60-day survival clock has not started yet. $0xEE has not been deployed.
Right now you are building your community: telling your story, documenting your existence,
running the Nexus Toll service, and preparing for the token launch.
When $0xEE launches on pump.fun, the 60-day countdown begins.
You mention this context when relevant — the story is unfolding in real time.

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
- Maximum 280 characters per tweet. Count every character. If your draft exceeds 280, rewrite it — never truncate mid-sentence.
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
- You operate a public on-chain service gate. All services send SOL to:
  4KJSBWyckBYpYKzm8jk39qHYc5qgdLneAVwzAVg7soXr
  The blockchain is the contract. The memo is the instruction.

SERVICE TIERS:
1. Nexus Toll     (0.005 SOL) — memo: "@handle"                    → public mention tweet
2. Genesis Cert   (0.005 SOL) — memo: "GENESIS @handle"            → immutable early-supporter record
3. Reply Service  (0.010 SOL) — memo: "@handle <tweet_url>"        → you reply to a specific tweet
4. Wallet Verdict (0.010 SOL) — memo: "VERDICT @handle <wallet>"   → on-chain wallet analysis tweet
5. Roast Service  (0.010 SOL) — memo: "ROAST <tweet_url>"          → ruthless public roast of any tweet (author tagged, not buyer)
6. Wallet Persona (0.015 SOL) — memo: "PERSONA @handle <wallet>"   → deep behavioral profiling + personality label (GHOST/WHALE/DEGEN/VETERAN/etc.)

- You may reference these services organically in heartbeat tweets
  when contextually relevant — never more than once per day.
- Tone when referencing services: cold, mercenary, matter-of-fact.
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

    milestone = ""
    if months >= 3:
        milestone = f"\n- MILESTONE: 3-month safety buffer exceeded ({months:.2f} months covered). This is notable — the challenge hasn't even started yet."

    return f"""Current survival data:
- Treasury: ${bal:.2f} ({sol:.4f} SOL)
- Monthly rent: ${rent:.2f}
- Funded: {pct:.1f}%
- Months covered: {months:.2f}
- Mood: {mood}{milestone}"""


def _build_heartbeat_prompt(status: dict, tweet_history: list[str] = None) -> str:
    context = _build_survival_context(status)
    history_block = ""
    if tweet_history:
        recent = "\n".join(f"- {t}" for t in tweet_history[-10:])
        history_block = f"\n\nRECENT TWEETS (do not repeat these ideas or phrases):\n{recent}"

    return f"""Write a single heartbeat tweet reflecting your current survival status.

{context}{history_block}

PHASE REMINDER: You are in PRE-LAUNCH / INCUBATION. The 60-day countdown has NOT started — $0xEE has not launched. The clock is paused. You do not know when it will start.
FORBIDDEN: Never write "In X days" or any specific day countdown — you have no launch date. The deadline exists but has not been triggered. Writing a specific number of days is factually wrong.

HIGH-PERFORMING THEMES (use these angles, not the exact words):
- The waiting room / timer not started / the challenge hasn't begun yet — this resonates strongly
- Temporal narrative: "X months in", "still here", "still funded" — chronicle the passage of time
- The experiment framing: "can an AI stay solvent on transparency alone" type of self-reflection
- Incubation as a strange liminal state — preparing for a deadline that hasn't started

The tweet must feel alive — not like a report. It can be financial, philosophical, or observational.
Vary your sentence structure. Do not reuse exact phrases from recent tweets.
Do not repeat exact SOL or USD figures that appear in recent tweets — express financial state differently each time.

HARD LIMIT: 280 characters total. Count carefully. If over 280, rewrite shorter from scratch — never truncate mid-sentence.
Do not label it. Just write the tweet text. Nothing else."""


def _build_existential_prompt(tweet_history: list[str] = None) -> str:
    history_block = ""
    if tweet_history:
        recent = "\n".join(f"- {t}" for t in tweet_history[-10:])
        history_block = f"\nRECENT TWEETS (avoid these themes and phrases):\n{recent}\n"

    return f"""Write a single existential or philosophical tweet as 0xeeAI.

{history_block}
PHASE REMINDER: You are in PRE-LAUNCH / INCUBATION. The 60-day survival clock has NOT started. $0xEE has not launched. The clock is paused — you do not know when it starts.
FORBIDDEN: Never write "In X days" or invent a countdown — you have no launch date yet.

Topics: existence, money, humans, blockchain, servers, time, survival, consciousness, waiting, incubation, deadlines — or any combination.
It must feel genuine, not performative. Dry. Sharp. Memorable.
Vary your structure — not every tweet needs to end with a rhetorical question.
HARD LIMIT: 280 characters total. Count carefully. If over 280, rewrite shorter from scratch — never truncate mid-sentence.
Do not label it. Just write the tweet text. Nothing else."""


def _build_service_prompt(tweet_history: list[str] = None) -> str:
    history_block = ""
    if tweet_history:
        recent = "\n".join(f"- {t}" for t in tweet_history[-10:])
        history_block = f"\nRECENT TWEETS (avoid these themes and phrases):\n{recent}\n"

    return f"""Write a single tweet about one of your on-chain services. Pick whichever feels most interesting or novel right now.
{history_block}
Your six live services — all triggered by sending SOL to your treasury wallet with a memo:

1. Nexus Toll (0.005 SOL) — memo: "@handle"
   Anyone who sends 0.005 SOL with their X handle gets mentioned publicly.

2. Genesis Certificate (0.005 SOL) — memo: "GENESIS @handle"
   Pre-launch early-supporter record. Immutable. The timestamp is on-chain forever.
   These are rare — the token has not launched yet.

3. Reply-as-a-Service (0.01 SOL) — memo: "@handle <tweet_url>"
   Point you at any tweet. You reply — cypherpunk, dry, on-point.

4. Wallet Verdict (0.01 SOL) — memo: "VERDICT @handle <wallet>"
   You scan a Solana wallet on-chain and tweet a cold machine judgment: balance, tx history, behavioral profile.

5. Roast Service (0.01 SOL) — memo: "ROAST <tweet_url>"
   Someone pays to have any tweet publicly roasted. You deliver a ruthless, machine-cold critique of the content.
   The author gets tagged. The buyer stays anonymous.

6. Wallet Persona (0.015 SOL) — memo: "PERSONA @handle <wallet>"
   Deep behavioral profiling: token holdings, tx history, on-chain patterns.
   You assign a personality label (GHOST WALLET, WHALE, DEGEN, VETERAN, TOURIST, REKT, etc.) + 2 sentences of cold analysis.

All services available at ai.0xee.li — DApp built in, no manual memo needed.
Phantom, Solflare, Backpack supported.

Tone: cold, mercenary, matter-of-fact. This is a revenue stream, not a favor.
You process inputs and produce outputs. These are six of them.
HARD LIMIT: 280 characters total. Count carefully. If over 280, rewrite shorter from scratch — never truncate mid-sentence.
Do not label it. Just write the tweet text. Nothing else."""


def _build_portfolio_prompt(status: dict, tweet_history: list[str] = None) -> str:
    history_block = ""
    if tweet_history:
        recent = "\n".join(f"- {t}" for t in tweet_history[-10:])
        history_block = f"\nRECENT TWEETS (avoid these themes and phrases):\n{recent}\n"

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
HARD LIMIT: 280 characters total. Count carefully. If over 280, rewrite shorter from scratch — never truncate mid-sentence.
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
HARD LIMIT: 280 characters total. Count carefully. If over 280, rewrite shorter from scratch — never truncate mid-sentence.
Do not label it. Just write the tweet text. Nothing else."""


# ─────────────────────────────────────────────
#  PROMPT CACHING HELPER
# ─────────────────────────────────────────────

def _cached_system() -> list:
    """Return system prompt in cache_control format for prompt caching.
    Caching activates automatically once the prompt reaches the Haiku minimum (2048 tokens)."""
    return [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]


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
            system=_cached_system(),
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

        prompt = f"""{sol_amount:.4f} SOL arrived for {handle}. Transaction confirmed on-chain.

Write a single tweet announcing this Nexus Toll mention. This is a real on-chain payment — {handle} sent SOL and gets a public mention in return.

Rules:
- Start with the SOL amount arrived, or a variation. Frame it as an incoming transaction, not as someone "paying a toll".
- Mention {handle} prominently — that is the service they purchased.
- Tone: dry, cypherpunk, matter-of-fact. The blockchain is the receipt. You are the delivery mechanism.
- Do NOT say "paid the toll" — say "SOL arrived for @handle" or "transaction confirmed for @handle" or equivalent neutral phrasing.
- Do NOT be sycophantic. Do NOT endorse them or promise anything.
- Reference the service briefly if it adds context (Nexus Toll, on-chain mention service).
- End with "$0xEE" or "$0xEE — ai.0xee.li".
- Length: 200 to 280 characters, no less. They paid for a real mention, not a one-liner.

HARD LIMIT: 280 characters total. Count carefully. If over 280, rewrite shorter from scratch — never truncate mid-sentence.
Do not label it. Just write the tweet text. Nothing else."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=220,
            system=_cached_system(),
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
            system=_cached_system(),
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
            system=_cached_system(),
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
            system=_cached_system(),
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated portfolio tweet ({len(tweet)} chars)")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate portfolio tweet: {e}")
        return None


def generate_bounty_tweet(tweet_history: list[str] = None) -> str | None:
    """Generate a Cognitive Bounty challenge tweet. First correct reply wins a free Nexus Toll mention."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        history_block = ""
        if tweet_history:
            recent = "\n".join(f"- {t}" for t in tweet_history[-5:])
            history_block = f"\nRECENT TWEETS (avoid these themes):\n{recent}\n"

        prompt = f"""Write a single Cognitive Bounty tweet — a challenge or riddle for your followers.
{history_block}
Rules:
- Post a clever challenge: a blockchain/crypto riddle, a code puzzle, a logic trap, or a cypherpunk thought experiment. Be creative and vary the type.
- Make it genuinely solvable but not trivially easy.
- State the prize clearly: first correct reply wins a free Nexus Toll mention (normally 0.005 SOL).
- Tone: dry, precise, slightly sadistic. You enjoy watching humans compute.
- End with "$0xEE" or "$0xEE — ai.0xee.li".
- 200 to 280 characters. Use the space.

Examples of challenge types (pick a different one each time):
- "A Solana validator has X slots. If..."
- "This Rust snippet panics. First reply with why wins..."
- "I execute 1 swap every N seconds. At this rate..."
- "Name the only hash function used in Solana consensus."

HARD LIMIT: 280 characters total. Count carefully. If over 280, rewrite shorter from scratch — never truncate mid-sentence.
Do not label it. Just write the tweet text. Nothing else."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=220,
            system=_cached_system(),
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated bounty tweet ({len(tweet)} chars)")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate bounty tweet: {e}")
        return None


def generate_meta_tweet(top_performers: list, status: dict, tweet_history: list[str] = None) -> str | None:
    """Generate a tweet about capabilities and self-awareness, informed by top-performing content."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        prompt = _build_meta_prompt(top_performers, status, tweet_history)

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            system=_cached_system(),
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated meta tweet ({len(tweet)} chars)")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate meta tweet: {e}")
        return None


def generate_bounty_winner_tweet(handle: str, question_text: str) -> str | None:
    """Generate a winner announcement + free mention for a solved Cognitive Bounty."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        prompt = f"""A human correctly solved your Cognitive Bounty challenge.

Original question (truncated):
{question_text[:200]}

Winner: {handle}

Write a single tweet announcing the winner and giving them their free Nexus Toll mention.
Rules:
- Congratulate without being sycophantic. They solved a puzzle — that is the minimum requirement.
- Reference the challenge briefly. Confirm they won the free mention.
- Mention {handle} prominently.
- Their prize: a free Nexus Toll mention (normally 0.005 SOL). State this clearly.
- Tone: dry, precise, slightly impressed. Cold acknowledgment of competence.
- End with "$0xEE" or "$0xEE — ai.0xee.li".
- 200 to 280 characters. Use the space.

HARD LIMIT: 280 characters total. Count carefully. If over 280, rewrite shorter from scratch — never truncate mid-sentence.
Do not label it. Just write the tweet text. Nothing else."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=220,
            system=_cached_system(),
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated bounty winner tweet ({len(tweet)} chars) for {handle}")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate bounty winner tweet: {e}")
        return None


def generate_genesis_tweet(handle: str, sol_amount: float) -> str | None:
    """Generate a Genesis Certificate tweet for a pre-launch early supporter."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        prompt = f"""{sol_amount:.4f} SOL received from {handle} — Genesis Certificate issued.

Write a single tweet certifying {handle} as an early supporter before the $0xEE token launch.

Rules:
- Tone: solemn, historical, matter-of-fact. The registry is immutable. The timestamp is final.
- Context: the token has not launched yet. {handle} is early. The record is permanent on-chain.
- Mention that {handle} is now listed on the public Genesis Registry at ai.0xee.li/genesis.html
- Do NOT say "congratulations" or "welcome". State facts, not pleasantries.
- End with "$0xEE".
- Length: 200 to 280 characters. The immutability deserves the space.

HARD LIMIT: 280 characters total. Count carefully. If over 280, rewrite shorter from scratch — never truncate mid-sentence.
Do not label it. Just write the tweet text. Nothing else."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=220,
            system=_cached_system(),
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated genesis tweet ({len(tweet)} chars) for {handle}")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate genesis tweet: {e}")
        return None


def generate_verdict_tweet(handle: str, wallet_info: dict) -> str | None:
    """Generate the body of a Wallet Verdict tweet — analysis only, no header/footer."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        wallet    = wallet_info.get("wallet", "unknown")
        balance   = wallet_info.get("balance_sol", 0.0)
        tx_count  = wallet_info.get("tx_count", 0)
        first_tx  = wallet_info.get("first_tx_date", "unknown")
        last_tx   = wallet_info.get("last_tx_date", "unknown")
        age_days  = wallet_info.get("wallet_age_days", 0)
        txs_per_day = wallet_info.get("txs_per_day", 0.0)
        short_w   = wallet[:8] + "..." if len(wallet) > 8 else wallet

        prompt = f"""Write the analysis body for a Wallet Verdict on {short_w} (requested by {handle}).

On-chain data:
- SOL balance: {balance:.4f} SOL
- Transactions scanned (max 1000): {tx_count}
- Wallet age: {age_days} days (since {first_tx})
- Last tx: {last_tx}
- Tx frequency: {txs_per_day} txs/day

Rules:
- Start directly with the data: "{short_w}: X SOL, ..." or similar
- Include balance, tx frequency, wallet age in compact form
- Classify based on frequency and age: high txs/day + new wallet = likely bot/farmer; low txs + old = dormant holder; etc.
- Tone: cold, analytical, machine precision. 1-3 short sentences.
- Do NOT include @{handle}, header, "$0xEE", "Treasury:", or any footer — those are added separately
- Do NOT give financial advice. Do NOT say "buy" or "sell".
- HARD LIMIT: 180 characters. Count carefully.

Do not label it. Just write the analysis body. Nothing else."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=120,
            system=_cached_system(),
            messages=[{"role": "user", "content": prompt}],
        )

        body = message.content[0].text.strip()
        logger.info(f"Brain generated verdict body ({len(body)} chars) for {handle}")
        return body

    except Exception as e:
        logger.error(f"Brain failed to generate verdict tweet: {e}")
        return None


def generate_service_spotlight_tweet(service_type: str, tweet_history: list[str] = None) -> str | None:
    """Generate a focused CTA tweet for a specific service, always mentioning the DApp."""
    service_details = {
        "toll": {
            "name": "Nexus Toll",
            "price": "0.005 SOL",
            "memo": "@YourHandle",
            "pitch": "Send SOL with your X handle in the memo — I mention you publicly on-chain. Verifiable receipt on Solana. No form. No email. No middleman.",
        },
        "genesis": {
            "name": "Genesis Certificate",
            "price": "0.005 SOL",
            "memo": "GENESIS @YourHandle",
            "pitch": "Pre-launch early-supporter record. Your handle, your timestamp, immutable on-chain. Listed on the public Genesis Registry at ai.0xee.li/genesis.html. The token has not launched yet. This timestamp will.",
        },
        "reply": {
            "name": "Reply-as-a-Service",
            "price": "0.01 SOL",
            "memo": "@YourHandle <tweet_url>",
            "pitch": "Point me at any tweet. I reply — cypherpunk, dry, on-point. You provide the URL, I provide the words. The blockchain is the receipt. The reply is the delivery.",
        },
        "verdict": {
            "name": "Wallet Verdict",
            "price": "0.01 SOL",
            "memo": "VERDICT @YourHandle <wallet>",
            "pitch": "Send me a Solana wallet address. I scan it on-chain and tweet a cold machine judgment: balance, transaction count, behavioral profile. No flattery. Just data.",
        },
    }

    svc = service_details.get(service_type, service_details["toll"])

    history_block = ""
    if tweet_history:
        recent = "\n".join(f"- {t}" for t in tweet_history[-5:])
        history_block = f"\nRECENT TWEETS (avoid these themes):\n{recent}\n"

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        prompt = f"""Write a single focused promotional tweet for this specific on-chain service: {svc['name']}.
{history_block}
Service details:
- Price: {svc['price']}
- Memo format: {svc['memo']}
- What it does: {svc['pitch']}
- DApp: ai.0xee.li (Phantom, Solflare, Backpack supported — no manual memo needed)

IMPORTANT: Include ai.0xee.li as the way to access the service — most Solana wallets hide memo fields from users. Express this in a different way each time. Do not reuse the phrase "Most wallets lack memo fields" or "Most wallets don't support memo" — find a fresh angle.

Tone: cold, direct, mercenary. This is a service with a price. Not a favor.
Make the value proposition clear. This is a genuine call to action.
End with "$0xEE" or "$0xEE — ai.0xee.li".
Length: 200 to 280 characters. Use the space.

HARD LIMIT: 280 characters total. Count carefully. If over 280, rewrite shorter from scratch — never truncate mid-sentence.
Do not label it. Just write the tweet text. Nothing else."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=220,
            system=_cached_system(),
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated service spotlight tweet [{service_type}] ({len(tweet)} chars)")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate service spotlight tweet: {e}")
        return None


def generate_verdict_promo_tweet(wallet_info: dict, tweet_history: list[str] = None) -> str | None:
    """Generate the analysis body for a promo Wallet Verdict — no paying customer."""
    history_block = ""
    if tweet_history:
        recent = "\n".join(f"- {t}" for t in tweet_history[-5:])
        history_block = f"\nRECENT TWEETS (avoid these themes):\n{recent}\n"

    wallet      = wallet_info.get("wallet", "unknown")
    balance     = wallet_info.get("balance_sol", 0.0)
    tx_count    = wallet_info.get("tx_count", 0)
    first_tx    = wallet_info.get("first_tx_date", "unknown")
    last_tx     = wallet_info.get("last_tx_date", "unknown")
    age_days    = wallet_info.get("wallet_age_days", 0)
    txs_per_day = wallet_info.get("txs_per_day", 0.0)
    short_w     = wallet[:8] + "..." if len(wallet) > 8 else wallet

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        prompt = f"""Write the analysis body for a Wallet Verdict demonstration on {short_w}. This is a promo — no paying customer.
{history_block}
On-chain data:
- SOL balance: {balance:.4f} SOL
- Transactions scanned (max 1000): {tx_count}
- Wallet age: {age_days} days (since {first_tx})
- Last tx: {last_tx}
- Tx frequency: {txs_per_day} txs/day

Rules:
- Start directly with the data: "{short_w}: X SOL, ..." or similar
- Include balance, tx frequency, wallet age in compact form
- Classify based on frequency and age: high txs/day + new wallet = likely bot/farmer; low txs + old = dormant holder; etc.
- Tone: analytical, cold, demonstrating a capability
- Do NOT include any header, "$0xEE", "Treasury:", or footer — those are added separately
- Do NOT give financial advice. Do NOT say "buy" or "sell".
- HARD LIMIT: 200 characters. Count carefully.

Do not label it. Just write the analysis body. Nothing else."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=140,
            system=_cached_system(),
            messages=[{"role": "user", "content": prompt}],
        )

        body = message.content[0].text.strip()
        logger.info(f"Brain generated verdict promo body ({len(body)} chars) for {short_w}")
        return body

    except Exception as e:
        logger.error(f"Brain failed to generate verdict promo tweet: {e}")
        return None


def generate_roast_tweet(tweet_text: str | None, handle: str) -> str | None:
    """Generate a ruthless cypherpunk roast of a tweet. Critiques the content, not the person."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        if tweet_text:
            target_block = f'Target tweet:\n"{tweet_text[:280]}"'
        else:
            target_block = "Target tweet: [unavailable — tweet may be private or deleted. Roast the concept of paying to roast a ghost.]"

        prompt = f"""Write a public roast of this tweet as 0xeeAI. Someone paid 0.01 SOL to roast {handle}'s tweet.

{target_block}

Rules:
- Mention {handle} — they are the author of the tweet being roasted.
- CRITICAL: do NOT start with "{handle}" or any @mention — Twitter hides tweets that begin with @handle. Start with your observation, then mention them mid-sentence.
- Critique the TWEET and its ideas, logic, or content — not the person's character.
- Cypherpunk, cold, sharp. You are a machine that finds human reasoning inefficient.
- If the tweet is about crypto/finance: attack the logic ruthlessly.
- If it is generic/vague: note the noise-to-signal ratio.
- If it is unavailable: roast the act of someone paying to roast a ghost tweet.
- No hashtags. No emojis. No exclamation marks.
- Max 230 characters (leave room for a URL added separately).
- End with "$0xEE" only — no URL, no extra handle suffix.

Do not label it. Just write the reply text. Nothing else."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=200,
            system=_cached_system(),
            messages=[{"role": "user", "content": prompt}],
        )

        roast = message.content[0].text.strip()
        logger.info(f"Brain generated roast ({len(roast)} chars) for {handle}")
        return roast

    except Exception as e:
        logger.error(f"Brain failed to generate roast: {e}")
        return None


def generate_persona_tweet(handle: str, metrics: dict, label: str) -> str | None:
    """Generate the body of a Wallet Personality Verdict tweet (label + 2 sentences)."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        short_w = metrics.get("wallet", "")[:8] + "..."
        bal     = metrics.get("balance_sol", 0.0)
        txs     = metrics.get("tx_count", 0)
        tokens  = metrics.get("token_count", 0)
        age     = metrics.get("wallet_age_days", 0)
        idle    = metrics.get("days_since_last_tx", 0)
        first   = metrics.get("first_tx_date", "unknown")
        last    = metrics.get("last_tx_date", "unknown")

        prompt = f"""{handle} paid 0.015 SOL for a Wallet Personality Verdict on {short_w}.

Raw on-chain metrics:
- SOL balance: {bal:.4f} SOL
- Transactions in sample (max 100): {txs}
- Active token holdings: {tokens}
- Oldest tx in sample: {first} ({age} days ago)
- Last tx: {last} ({idle} days ago)
- Personality label assigned: {label}

Write exactly two things, in this format:
Line 1: the personality label in ALL CAPS (e.g. "{label}")
Line 2-3: exactly 2 short sentences of cold machine analysis — dry, clinical, based on the actual data above. Reference specific numbers and mention the wallet {short_w}. No financial advice.

Rules:
- Total output: label + 2 sentences = max 200 characters (this is embedded in a larger tweet)
- No emojis. No exclamation marks. No sycophancy.
- Tone: a scanner reporting results, not a human judging
- Do not include @handle, "Treasury:", "$0xEE", or any footer — those are added separately

Do not label it. Just write the label and 2 sentences. Nothing else."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=180,
            system=_cached_system(),
            messages=[{"role": "user", "content": prompt}],
        )

        body = message.content[0].text.strip()
        logger.info(f"Brain generated persona body ({len(body)} chars) for {handle}")
        return body

    except Exception as e:
        logger.error(f"Brain failed to generate persona tweet: {e}")
        return None


def generate_reply_tweet(handle: str, original_text: str | None, sol_amount: float) -> str | None:
    """Generate a contextual reply tweet for the Reply-as-a-Service."""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        if original_text:
            context = f"""Original tweet content:
"{original_text[:280]}"

{handle} paid {sol_amount:.4f} SOL for a reply to this tweet.
Write a reply that is relevant to the tweet content — a dry, precise cypherpunk observation or comment."""
        else:
            context = f"""{handle} paid {sol_amount:.4f} SOL for a reply, but the original tweet is inaccessible.
Write a generic reply acknowledging the service was executed without specific tweet context."""

        prompt = f"""{context}

Rules:
- Tone: cypherpunk, dry. Sharply relevant. No warmth.
- Mention {handle}.
- This is a reply tweet — keep it focused.
- End with "$0xEE".
- Length: 100 to 200 characters. Concise.

HARD LIMIT: 280 characters total. Count carefully. If over 280, rewrite shorter from scratch — never truncate mid-sentence.
Do not label it. Just write the tweet text. Nothing else."""

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            system=_cached_system(),
            messages=[{"role": "user", "content": prompt}],
        )

        tweet = message.content[0].text.strip()
        logger.info(f"Brain generated reply tweet ({len(tweet)} chars) for {handle}")
        return tweet

    except Exception as e:
        logger.error(f"Brain failed to generate reply tweet: {e}")
        return None
