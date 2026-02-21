"""
0xeeTerm — Solana Module
Tracks wallet balance and token market cap via Solana RPC
"""

import os
import logging
import requests

logger = logging.getLogger("0xeeTerm.solana")

LAMPORTS_PER_SOL = 1_000_000_000


_PUBLIC_RPC = "https://api.mainnet-beta.solana.com"


def _get_rpc() -> str:
    """Return the best available RPC: Helius if key is set, else SOLANA_RPC env, else public fallback."""
    key = os.getenv("HELIUS_API_KEY")
    if key:
        return f"https://mainnet.helius-rpc.com/?api-key={key}"
    return os.getenv("SOLANA_RPC", _PUBLIC_RPC)


def check_helius() -> dict:
    """
    Verify the Helius API key by making a lightweight getSlot call.
    Returns {"configured": bool, "ok": bool, "rpc": str, "error": str|None}
    """
    key = os.getenv("HELIUS_API_KEY")
    if not key:
        return {"configured": False, "ok": False, "rpc": _PUBLIC_RPC, "error": "HELIUS_API_KEY not set"}
    url = f"https://mainnet.helius-rpc.com/?api-key={key}"
    try:
        r = requests.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "getSlot", "params": []}, timeout=8)
        data = r.json()
        if "error" in data:
            return {"configured": True, "ok": False, "rpc": url, "error": data["error"].get("message", str(data["error"]))}
        return {"configured": True, "ok": True, "rpc": url, "error": None}
    except Exception as e:
        return {"configured": True, "ok": False, "rpc": url, "error": str(e)}


def _rpc_post(payload: dict) -> dict:
    """POST to primary RPC, auto-fallback to public if primary returns an error or times out."""
    primary = _get_rpc()
    try:
        r = requests.post(primary, json=payload, timeout=10)
        data = r.json()
        if "error" not in data:
            return data
        logger.warning(f"RPC primary error ({data['error'].get('message', data['error'])}) — falling back to public RPC")
    except Exception as e:
        logger.warning(f"RPC primary unreachable: {e} — falling back to public RPC")
    # Fallback
    r = requests.post(_PUBLIC_RPC, json=payload, timeout=10)
    return r.json()

USDC_MINT    = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
JITOSOL_MINT = "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn"


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
    wallet = os.getenv("SOLANA_WALLET")
    try:
        data = _rpc_post({"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [wallet]})
        lamports = data["result"]["value"]
        sol = lamports / LAMPORTS_PER_SOL
        logger.debug(f"Wallet balance: {sol:.4f} SOL")
        return sol
    except Exception as e:
        logger.error(f"Failed to fetch wallet balance: {e}")
        return 0.0


def _get_token_balance_rpc(wallet: str, mint: str) -> float:
    """Fetch SPL token balance (uiAmount). Returns 0.0 if account doesn't exist."""
    try:
        data = _rpc_post({
            "jsonrpc": "2.0", "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [wallet, {"mint": mint}, {"encoding": "jsonParsed"}],
        })
        accounts = data["result"]["value"]
        if not accounts:
            return 0.0
        return sum(
            float(acc["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"] or 0)
            for acc in accounts
        )
    except Exception as e:
        logger.error(f"Failed to fetch SPL balance for {mint[:8]}...: {e}")
        return 0.0


def _get_extended_prices() -> dict:
    """Fetch SOL and JitoSOL prices from CoinGecko."""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "solana,jito-staked-sol", "vs_currencies": "usd"},
            timeout=10,
        )
        data = r.json()
        return {
            "sol":     float(data.get("solana",          {}).get("usd", 0.0)),
            "jitosol": float(data.get("jito-staked-sol", {}).get("usd", 0.0)),
        }
    except Exception as e:
        logger.error(f"Failed to fetch extended prices: {e}")
        return {"sol": 0.0, "jitosol": 0.0}


def get_spl_balances() -> dict:
    """
    Fetch USDC and JitoSOL balances from the treasury wallet.
    Returns dict with balance, price, and USD value for each token.
    Handles missing token accounts gracefully (returns 0.0).
    """
    wallet = os.getenv("SOLANA_WALLET", "")

    if not wallet:
        return {
            "usdc":    {"balance": 0.0, "price": 1.0,  "usd": 0.0},
            "jitosol": {"balance": 0.0, "price": 0.0,  "usd": 0.0},
        }

    prices      = _get_extended_prices()
    usdc_bal    = _get_token_balance_rpc(wallet, USDC_MINT)
    jitosol_bal = _get_token_balance_rpc(wallet, JITOSOL_MINT)

    # JitoSOL fallback: use SOL price if CoinGecko returns 0
    jitosol_price = prices["jitosol"] if prices["jitosol"] > 0 else prices["sol"]

    result = {
        "usdc":    {"balance": round(usdc_bal,    6), "price": 1.0,           "usd": round(usdc_bal * 1.0,                2)},
        "jitosol": {"balance": round(jitosol_bal, 6), "price": jitosol_price, "usd": round(jitosol_bal * jitosol_price,   2)},
    }
    logger.info(
        f"SPL balances — USDC: ${result['usdc']['usd']:.2f} "
        f"| JitoSOL: {jitosol_bal:.4f} (${result['jitosol']['usd']:.2f})"
    )
    return result


def get_wallet_balance_usd() -> float:
    """Get wallet balance in USD."""
    sol = get_wallet_balance_sol()
    price = get_sol_price_usd()
    usd = sol * price
    logger.info(f"Treasury: {sol:.4f} SOL = ${usd:.2f}")
    return usd


def get_survival_status() -> dict:
    """Return a full survival snapshot — Net Worth includes SOL + USDC + JitoSOL."""
    monthly_rent = float(os.getenv("MONTHLY_RENT", 38.0))
    runway_days  = int(os.getenv("RUNWAY_DAYS", 60))

    balance_sol = get_wallet_balance_sol()
    sol_price   = get_sol_price_usd()
    sol_usd     = balance_sol * sol_price

    spl         = get_spl_balances()
    usdc_usd    = spl["usdc"]["usd"]
    jitosol_usd = spl["jitosol"]["usd"]

    net_worth      = round(sol_usd + usdc_usd + jitosol_usd, 2)
    months_covered = net_worth / monthly_rent if monthly_rent > 0 else 0
    survival_pct   = min((net_worth / monthly_rent) * 100, 999)

    logger.info(
        f"Net Worth: ${net_worth:.2f} "
        f"(SOL ${sol_usd:.2f} + USDC ${usdc_usd:.2f} + JitoSOL ${jitosol_usd:.2f})"
    )

    return {
        "balance_usd":    net_worth,
        "balance_sol":    round(balance_sol, 4),
        "sol_price":      sol_price,
        "monthly_rent":   monthly_rent,
        "months_covered": round(months_covered, 2),
        "survival_pct":   round(survival_pct, 1),
        "runway_days":    runway_days,
        "portfolio": {
            "sol":     {"balance": round(balance_sol, 4), "usd": round(sol_usd, 2),  "price": sol_price},
            "usdc":    spl["usdc"],
            "jitosol": spl["jitosol"],
            "net_worth": net_worth,
        },
    }
