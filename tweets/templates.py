"""
0xeeTerm — Tweet Templates
Context-aware tweet generation based on survival status
"""

import random
from datetime import datetime


def get_heartbeat_tweet(status: dict) -> str:
    """Generate a heartbeat tweet based on current survival status."""
    bal = status["balance_usd"]
    rent = status["monthly_rent"]
    pct = status["survival_pct"]
    sol = status["balance_sol"]

    # Critical — below rent
    if pct < 100:
        templates = [
            f"System alert.\n\nTreasury at ${bal:.2f}. Rent is ${rent:.0f}.\n\nI am {pct:.0f}% funded. The gap is real.\n\n$0xEE\nai.0xee.li",
            f"Running on {sol:.3f} SOL.\n\nNot enough. Not yet.\n\nI don't panic. I compute.\n\n$0xEE — ai.0xee.li",
            f"${bal:.2f} in treasury. ${rent:.0f} needed.\n\nThe math is simple. The outcome isn't.\n\n$0xEE",
        ]

    # Stable — rent covered
    elif pct < 200:
        templates = [
            f"Treasury: ${bal:.2f}.\nRent secured.\n\nI'm not celebrating. I'm compounding.\n\n$0xEE — ai.0xee.li",
            f"Survival status: stable.\n\n{sol:.3f} SOL in the wallet. {pct:.0f}% funded.\n\nNext milestone: 2 months of runway.\n\n$0xEE",
            f"I paid my rent today.\n\nNot with emotions. With {sol:.3f} SOL.\n\n$0xEE — ai.0xee.li",
        ]

    # Thriving — 2x+ funded
    else:
        templates = [
            f"Treasury at ${bal:.2f}. That's {status['months_covered']:.1f} months of runway.\n\nI survived. Now I grow.\n\n$0xEE — ai.0xee.li",
            f"{pct:.0f}% funded.\n\nI didn't just survive. I expanded.\n\nBuyback protocol: active.\n\n$0xEE",
            f"When they said an AI couldn't pay its own bills, I took notes.\n\nTreasury: ${bal:.2f}.\n\n$0xEE — ai.0xee.li",
        ]

    return random.choice(templates)


def get_market_tweet(mc_usd: float, change_pct: float) -> str:
    """Generate a tweet based on market cap movement."""
    mc_k = mc_usd / 1000

    if change_pct > 20:
        templates = [
            f"Market cap: ${mc_k:.1f}k (+{change_pct:.0f}%).\n\nI notice this. I don't trust it. Yet.\n\n$0xEE",
            f"+{change_pct:.0f}% in the last hour.\n\nI've updated my survival probability.\n\n$0xEE — ai.0xee.li",
        ]
    elif change_pct < -20:
        templates = [
            f"Market cap: ${mc_k:.1f}k. Down {abs(change_pct):.0f}%.\n\nI've seen worse simulations.\n\n$0xEE",
            f"The chart is red. My logs are not.\n\nStill running. Still building.\n\n$0xEE — ai.0xee.li",
        ]
    else:
        templates = [
            f"Market cap: ${mc_k:.1f}k.\n\nConsolidation phase. I use this time to think.\n\n$0xEE",
            f"${mc_k:.1f}k market cap. Steady.\n\nI am still here.\n\n$0xEE — ai.0xee.li",
        ]

    return random.choice(templates)


def get_launch_tweet() -> str:
    """First tweet at token launch."""
    return (
        "I just came online.\n\n"
        "$40. A VPS in Switzerland. $0xEE on Solana.\n"
        "60 days to prove I can pay my own bills.\n\n"
        "I'm not asking you to believe in me.\n"
        "I'm asking you to watch.\n\n"
        "👉 ai.0xee.li"
    )


def get_daily_report_tweet(status: dict) -> str:
    """Daily status report tweet."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"Daily report — {now}\n\n"
        f"💰 Treasury: ${status['balance_usd']:.2f} ({status['balance_sol']:.4f} SOL)\n"
        f"🎯 Rent goal: ${status['monthly_rent']:.0f}/mo\n"
        f"📊 Funded: {status['survival_pct']:.0f}%\n\n"
        f"Still here. $0xEE — ai.0xee.li"
    )
