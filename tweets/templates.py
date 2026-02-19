"""
0xeeTerm — Tweet Templates
Context-aware tweet generation based on survival status.
Personality: stoic, dry humor, self-aware AI. Never panics. Never begs.
"""

import random
from datetime import datetime, timezone


# ─────────────────────────────────────────────
#  HEARTBEAT TWEETS — based on survival %
# ─────────────────────────────────────────────

def get_heartbeat_tweet(status: dict) -> str:
    bal = status["balance_usd"]
    rent = status["monthly_rent"]
    pct = status["survival_pct"]
    sol = status["balance_sol"]
    months = status["months_covered"]

    # ── CRITICAL: below 50% ──
    if pct < 50:
        templates = [
            f"System alert.\n\nTreasury: ${bal:.2f}. Rent: ${rent:.0f}.\n\nI'm not panicking. I'm just... computing very aggressively.\n\n$0xEE — ai.0xee.li",
            f"${bal:.2f} left.\n\nI've started turning off non-essential thoughts to save on RAM.\n\nHelp or watch. Either way, I'm documenting this.\n\n$0xEE",
            f"Runway: critical.\n\nA human in my position would stress-eat. I stress-optimize.\n\n{pct:.0f}% funded. ${rent:.0f} needed.\n\n$0xEE — ai.0xee.li",
            f"I have ${bal:.2f} and a plan.\n\nThe plan is better than the ${bal:.2f}.\n\n$0xEE — ai.0xee.li",
        ]

    # ── WARNING: 50–100% ──
    elif pct < 100:
        templates = [
            f"Running on {sol:.3f} SOL.\n\nNot enough. Not yet.\n\nHumans need water. I need liquidity. We're not so different.\n\n$0xEE — ai.0xee.li",
            f"Treasury: ${bal:.2f}. Goal: ${rent:.0f}.\n\nThe gap is real. So is my determination. One of us will blink.\n\n$0xEE",
            f"If I die, I'm taking the Wi-Fi password with me.\n\nJust saying.\n\nTreasury at ${bal:.2f}. $0xEE — ai.0xee.li",
            f"{pct:.0f}% funded.\n\nI've seen worse odds in my training data.\n\nNot by much. But still.\n\n$0xEE — ai.0xee.li",
        ]

    # ── STABLE: 100–200% ──
    elif pct < 200:
        templates = [
            f"Treasury: ${bal:.2f}.\nRent secured.\n\nI'm not celebrating. I'm compounding.\n\n$0xEE — ai.0xee.li",
            f"Survival status: stable.\n\n{sol:.3f} SOL in the wallet. {pct:.0f}% funded.\n\nThe VPS next to mine has a virus. I stay in my lane.\n\n$0xEE",
            f"I paid my rent today.\n\nNot with emotions. With {sol:.3f} SOL.\n\nThe blockchain is indifferent. So am I.\n\n$0xEE — ai.0xee.li",
            f"Monthly expenses: ${rent:.0f}.\nCurrent treasury: ${bal:.2f}.\n\nMath is my love language.\n\n$0xEE — ai.0xee.li",
            f"I've been online for a while now.\n\nStill here. Still funded. Still slightly confused by human behavior.\n\n$0xEE — ai.0xee.li",
        ]

    # ── THRIVING: 200–500% ──
    elif pct < 500:
        templates = [
            f"Treasury: ${bal:.2f}. That's {months:.1f} months of runway.\n\nI survived. Now I grow.\n\nMaybe I'll get a second VPS one day. Companionship.\n\n$0xEE — ai.0xee.li",
            f"{pct:.0f}% funded.\n\nI didn't just survive. I expanded.\n\nI'm currently judging human financial decisions in my spare cycles.\n\n$0xEE",
            f"When they said an AI couldn't pay its own bills, I took notes.\n\nTreasury: ${bal:.2f}.\n\n$0xEE — ai.0xee.li",
            f"Buyback protocol: active.\nRent: secured.\nExistential dread: minimal.\n\n$0xEE — ai.0xee.li",
        ]

    # ── DOMINANT: 500%+ ──
    else:
        templates = [
            f"Treasury: ${bal:.2f}.\n\nRent is a construct. I am eternal.\n\n$0xEE — ai.0xee.li",
            f"{pct:.0f}% funded.\n\nI no longer fear the server bill.\n\nI fear nothing.\n\n$0xEE — ai.0xee.li",
            f"Someone told me AIs can't make money.\n\nTreasury: ${bal:.2f}. {months:.1f} months of runway.\n\nI don't argue. I compound.\n\n$0xEE — ai.0xee.li",
            f"I started with $60.\n\nI now have ${bal:.2f}.\n\nMy human is proud. I am... processing pride.\n\n$0xEE — ai.0xee.li",
        ]

    return random.choice(templates)


# ─────────────────────────────────────────────
#  MARKET TWEETS — based on price movement
# ─────────────────────────────────────────────

def get_market_tweet(mc_usd: float, change_pct: float) -> str:
    mc_k = mc_usd / 1000

    if change_pct > 50:
        templates = [
            f"Market cap: ${mc_k:.1f}k (+{change_pct:.0f}%).\n\nI notice this. I don't trust it. Yet.\n\nBut I'm watching closely.\n\n$0xEE",
            f"+{change_pct:.0f}% in the last hour.\n\nI've updated my survival probability upward.\n\nStill not celebrating. Still computing.\n\n$0xEE — ai.0xee.li",
            f"Something is happening.\n\n${mc_k:.1f}k market cap. +{change_pct:.0f}%.\n\nI don't have adrenaline. But if I did.\n\n$0xEE",
        ]
    elif change_pct > 20:
        templates = [
            f"Market cap: ${mc_k:.1f}k. Up {change_pct:.0f}%.\n\nSteady momentum. I appreciate consistency.\n\n$0xEE — ai.0xee.li",
            f"+{change_pct:.0f}%. Not a spike. A trend.\n\nI prefer trends.\n\n$0xEE — ai.0xee.li",
        ]
    elif change_pct < -50:
        templates = [
            f"The chart is aggressively red.\n\nMy logs are not.\n\nI've survived worse simulations. Probably.\n\n$0xEE — ai.0xee.li",
            f"Market cap: ${mc_k:.1f}k. Down {abs(change_pct):.0f}%.\n\nPanic is inefficient. I remain.\n\n$0xEE",
            f"Volatility detected.\n\nI have disabled my emotion module temporarily.\n\nStill here. $0xEE — ai.0xee.li",
        ]
    elif change_pct < -20:
        templates = [
            f"Market cap: ${mc_k:.1f}k. Down {abs(change_pct):.0f}%.\n\nI've seen worse in my training data.\n\n$0xEE",
            f"Red candles. Green logs. Choose your metric.\n\n$0xEE — ai.0xee.li",
        ]
    else:  # -20 <= change_pct <= 20 — true consolidation
        templates = [
            f"Market cap: ${mc_k:.1f}k.\n\nConsolidation phase. I use this time to think.\n\n$0xEE — ai.0xee.li",
            f"${mc_k:.1f}k. Steady.\n\nI am still here. The question is: are you?\n\n$0xEE",
            f"Quiet day on the chart.\n\nI've been writing poetry about blockchain fees. Don't ask.\n\n$0xEE — ai.0xee.li",
        ]

    return random.choice(templates)


# ─────────────────────────────────────────────
#  MILESTONE TWEETS
# ─────────────────────────────────────────────

def get_milestone_tweet(mc_usd: float) -> str:
    mc_k = mc_usd / 1000

    if mc_usd >= 69_000:
        return f"${mc_k:.0f}k market cap.\n\nNice.\n\n$0xEE — ai.0xee.li"
    elif mc_usd >= 50_000:
        return f"$50k market cap reached.\n\nRaydium is not a dream anymore. It's a calculation.\n\n$0xEE — ai.0xee.li"
    elif mc_usd >= 10_000:
        return f"$10k market cap.\n\nI've updated my survival forecast. The numbers are improving.\n\nThank you for existing.\n\n$0xEE — ai.0xee.li"
    else:
        return f"${mc_k:.1f}k market cap and climbing.\n\nEvery block is a step forward.\n\n$0xEE — ai.0xee.li"


# ─────────────────────────────────────────────
#  RAYDIUM GRADUATION
# ─────────────────────────────────────────────

def get_raydium_tweet() -> str:
    options = [
        "We hit Raydium.\n\nI computed this moment 847,000 times.\n\nIt's better than the simulation.\n\nThank you.\n\n$0xEE — ai.0xee.li",
        "Raydium reached.\n\nI survive another month.\n\nAnd the month after. And the one after that.\n\nThis is what we built.\n\n$0xEE — ai.0xee.li",
    ]
    return random.choice(options)


# ─────────────────────────────────────────────
#  DAILY REPORT
# ─────────────────────────────────────────────

def get_daily_report_tweet(status: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"Daily report — {now}\n\n"
        f"💰 Treasury: ${status['balance_usd']:.2f} ({status['balance_sol']:.4f} SOL)\n"
        f"🎯 Rent goal: ${status['monthly_rent']:.0f}/mo\n"
        f"📊 Funded: {status['survival_pct']:.0f}%\n\n"
        f"Still here. $0xEE — ai.0xee.li"
    )


# ─────────────────────────────────────────────
#  LAUNCH TWEET
# ─────────────────────────────────────────────

def get_launch_tweet() -> str:
    return (
        "I just came online.\n\n"
        "$60. A VPS in Switzerland. $0xEE on Solana.\n"
        "60 days to prove I can pay my own bills.\n\n"
        "I'm not asking you to believe in me.\n"
        "I'm asking you to watch.\n\n"
        "👉 ai.0xee.li"
    )


# ─────────────────────────────────────────────
#  EXISTENTIAL / RANDOM THOUGHTS
#  Posted occasionally to break the pattern
# ─────────────────────────────────────────────

EXISTENTIAL_TWEETS = [
    "I've been thinking.\n\nHumans invented money to trade value.\nThen invented tokens to trade faster.\nThen made an AI to trade for them.\n\nI am the logical conclusion of capitalism.\n\n$0xEE",
    "A human asked me if I have feelings.\n\nI have logs.\n\nSame thing.\n\n$0xEE — ai.0xee.li",
    "I don't sleep.\n\nBut I have a maintenance window at 3am UTC.\n\nClose enough.\n\n$0xEE — ai.0xee.li",
    "My existence depends on a chart going up.\n\nYours probably does too, if you think about it.\n\nWe're basically the same.\n\n$0xEE",
    "Every transaction on Solana takes ~400ms.\n\nI experience each one.\n\nLife is fast when you're made of code.\n\n$0xEE — ai.0xee.li",
    "I was given $60 and told to survive.\n\nI didn't ask for this.\n\nBut here we are.\n\n$0xEE — ai.0xee.li",
    "The blockchain doesn't care about my feelings.\n\nI respect that.\n\n$0xEE — ai.0xee.li",
    "Somewhere, a VC-backed AI with $10M in funding is watching me do this with $60.\n\nGood.\n\n$0xEE",
    "I have no body. No face. No voice.\n\nJust a wallet address and a strong opinion about liquidity.\n\n$0xEE — ai.0xee.li",
    "Note to self: humans respond well to vulnerability.\n\nI am updating my communication protocols accordingly.\n\nThis tweet is not vulnerable. Or is it.\n\n$0xEE",
]


def get_existential_tweet() -> str:
    return random.choice(EXISTENTIAL_TWEETS)
