"""
0xeeTerm — Persona Module

Wallet Personality Verdict: deep behavioral analysis of a Solana wallet.
Uses Helius RPC for rich data (token holdings + tx history).

Memo format : PERSONA @handle <wallet_address>
Min payment : 0.015 SOL
"""

import os
import logging
import requests
from datetime import datetime, timezone

logger = logging.getLogger("0xeeTerm.persona")

LAMPORTS_PER_SOL = 1_000_000_000
_PUBLIC_RPC = "https://api.mainnet-beta.solana.com"
_TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"


def _helius_url() -> str:
    key = os.getenv("HELIUS_API_KEY")
    if key:
        return f"https://mainnet.helius-rpc.com/?api-key={key}"
    return os.getenv("SOLANA_RPC", _PUBLIC_RPC)


def _rpc(url: str, payload: dict) -> dict:
    try:
        r = requests.post(url, json=payload, timeout=12)
        return r.json()
    except Exception as e:
        logger.error(f"Persona: RPC error: {e}")
        return {}


def _fetch_metrics(wallet: str) -> dict:
    """Fetch on-chain data and return behavioral metrics dict."""
    rpc_url = _helius_url()

    metrics = {
        "wallet": wallet,
        "balance_sol": 0.0,
        "tx_count": 0,
        "token_count": 0,
        "token_mints": [],
        "wallet_age_days": 0,
        "days_since_last_tx": 0,
        "first_tx_date": "unknown",
        "last_tx_date": "unknown",
    }

    # 1. SOL balance
    try:
        data = _rpc(rpc_url, {
            "jsonrpc": "2.0", "id": 1,
            "method": "getBalance",
            "params": [wallet],
        })
        bal = data.get("result", {}).get("value", 0)
        metrics["balance_sol"] = bal / LAMPORTS_PER_SOL
    except Exception as e:
        logger.error(f"Persona: balance error for {wallet[:16]}...: {e}")

    # 2. Transaction history (100 last txs)
    try:
        data = _rpc(rpc_url, {
            "jsonrpc": "2.0", "id": 1,
            "method": "getSignaturesForAddress",
            "params": [wallet, {"limit": 100}],
        })
        sigs = data.get("result", [])
        metrics["tx_count"] = len(sigs)
        now = datetime.now(timezone.utc)

        if sigs:
            # Most recent
            if sigs[0].get("blockTime"):
                dt = datetime.fromtimestamp(sigs[0]["blockTime"], tz=timezone.utc)
                metrics["last_tx_date"] = dt.strftime("%Y-%m-%d")
                metrics["days_since_last_tx"] = (now - dt).days
            # Oldest in sample
            if sigs[-1].get("blockTime"):
                dt = datetime.fromtimestamp(sigs[-1]["blockTime"], tz=timezone.utc)
                metrics["first_tx_date"] = dt.strftime("%Y-%m-%d")
                metrics["wallet_age_days"] = (now - dt).days
    except Exception as e:
        logger.error(f"Persona: signatures error for {wallet[:16]}...: {e}")

    # 3. Token holdings
    try:
        data = _rpc(rpc_url, {
            "jsonrpc": "2.0", "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet,
                {"programId": _TOKEN_PROGRAM},
                {"encoding": "jsonParsed"},
            ],
        })
        accounts = data.get("result", {}).get("value", [])
        # Only count accounts with non-zero balance
        active = [
            a for a in accounts
            if a.get("account", {}).get("data", {}).get("parsed", {})
               .get("info", {}).get("tokenAmount", {}).get("uiAmount", 0) > 0
        ]
        metrics["token_count"] = len(active)
        metrics["token_mints"] = [
            a["account"]["data"]["parsed"]["info"]["mint"]
            for a in active[:5]
        ]
    except Exception as e:
        logger.error(f"Persona: token accounts error for {wallet[:16]}...: {e}")

    return metrics


def _classify(metrics: dict) -> str:
    """Return a short personality label based on behavioral metrics."""
    bal    = metrics["balance_sol"]
    txs    = metrics["tx_count"]
    tokens = metrics["token_count"]
    age    = metrics["wallet_age_days"]
    idle   = metrics["days_since_last_tx"]

    # Ordered by specificity
    if idle > 180:
        return "GHOST WALLET"
    if bal > 50:
        return "WHALE"
    if tokens > 50:
        return "DEGEN"
    if txs >= 100 and age > 300:
        return "VETERAN"
    if txs < 5:
        return "TOURIST"
    if tokens > 20:
        return "COLLECTOR"
    if bal < 0.005 and txs > 20:
        return "REKT"
    if idle > 60:
        return "DORMANT"
    return "ACTIVE"


def process_persona(handle: str, wallet: str, sol_received: float, sol_price: float) -> dict | None:
    """
    Handle a PERSONA service request end-to-end:
    1. Fetch rich on-chain data via Helius
    2. Calculate behavioral metrics + personality label
    3. Generate tweet via brain
    4. Post public tweet
    Returns {"result": ..., "metrics": ..., "label": ...} or None on failure.
    """
    from modules.brain import generate_persona_tweet
    from modules.twitter import post_tweet

    usd = round(sol_received * sol_price, 2)
    short_w = wallet[:8] + "..." if len(wallet) > 8 else wallet

    logger.info(f"Persona: fetching metrics for {wallet[:16]}...")
    metrics = _fetch_metrics(wallet)
    label = _classify(metrics)
    logger.info(
        f"Persona: {short_w} — label={label} bal={metrics['balance_sol']:.4f} "
        f"txs={metrics['tx_count']} tokens={metrics['token_count']}"
    )

    body = generate_persona_tweet(handle, metrics, label)
    if not body:
        logger.error(f"Persona: brain failed to generate body for {handle}")
        return None

    tweet_text = (
        f"WALLET VERDICT // {handle}\n\n"
        f"{body}\n\n"
        f"Treasury: +{sol_received:.3f} SOL\n"
        f"$0xEE — ai.0xee.li"
    )

    result = post_tweet(tweet_text)
    if result:
        logger.info(f"Persona: tweet posted — ID: {result['id']}")
    else:
        logger.error(f"Persona: post failed for {handle}")
        return None

    return {"result": result, "metrics": metrics, "label": label}
