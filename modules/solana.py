"""
0xeeTerm — Solana Module
Tracks wallet balance and token market cap via Solana RPC
"""

import os
import logging
import requests

logger = logging.getLogger("0xeeTerm.solana")

LAMPORTS_PER_SOL = 1_000_000_000


def get_sol_price_usd() -> float:
    """Fetch current SOL price in USD from CoinGecko (free, no key needed)."""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "solana", "vs_currencies": "usd"},
            timeout=10,
        )
        price = r.json()["solana"]["usd"]
        logger.debug(f"SOL price: ${price}")
        return float(price)
    except Exception as e:
        logger.error(f"Failed to fetch SOL price: {e}")
        return 0.0


def get_wallet_balance_sol() -> float:
    """Get wallet SOL balance via RPC."""
    rpc = os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
    wallet = os.getenv("SOLANA_WALLET")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [wallet],
        }
        r = requests.post(rpc, json=payload, timeout=10)
        lamports = r.json()["result"]["value"]
        sol = lamports / LAMPORTS_PER_SOL
        logger.debug(f"Wallet balance: {sol:.4f} SOL")
        return sol
    except Exception as e:
        logger.error(f"Failed to fetch wallet balance: {e}")
        return 0.0


def get_wallet_balance_usd() -> float:
    """Get wallet balance in USD."""
    sol = get_wallet_balance_sol()
    price = get_sol_price_usd()
    usd = sol * price
    logger.info(f"Treasury: {sol:.4f} SOL = ${usd:.2f}")
    return usd


def get_survival_status() -> dict:
    """Return a full survival snapshot."""
    monthly_rent = float(os.getenv("MONTHLY_RENT", 27.0))
    runway_days = int(os.getenv("RUNWAY_DAYS", 60))
    balance_usd = get_wallet_balance_usd()
    balance_sol = get_wallet_balance_sol()
    sol_price = get_sol_price_usd()
    months_covered = balance_usd / monthly_rent if monthly_rent > 0 else 0
    survival_pct = min((balance_usd / monthly_rent) * 100, 999)

    return {
        "balance_usd": round(balance_usd, 2),
        "balance_sol": round(balance_sol, 4),
        "sol_price": sol_price,
        "monthly_rent": monthly_rent,
        "months_covered": round(months_covered, 2),
        "survival_pct": round(survival_pct, 1),
        "runway_days": runway_days,
    }
