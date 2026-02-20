"""
0xeeTerm — Shill Module

Shill-as-a-Service: listens for incoming SOL transfers with a Twitter
@handle in the transaction memo, and posts a paid mention tweet.

Phase 1: SOL transfers only.
# TODO: accept $0xEE token transfers + increase SHILL_MIN_AMOUNT

Storage : ~/.local/share/0xeeAI/shill_state.json
Env vars: SHILL_MIN_SOL (default: 0.001), SOLANA_WALLET, SOLANA_RPC
"""

import os
import re
import json
import logging
import requests
from pathlib import Path

logger = logging.getLogger("0xeeTerm.shill")

LAMPORTS_PER_SOL = 1_000_000_000

SHILL_STATE_DIR  = Path.home() / ".local" / "share" / "0xeeAI"
SHILL_STATE_FILE = SHILL_STATE_DIR / "shill_state.json"


# ─────────────────────────────────────────────
#  STATE
# ─────────────────────────────────────────────

def _load_state() -> dict:
    if SHILL_STATE_FILE.exists():
        try:
            with open(SHILL_STATE_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Shill: failed to load state: {e}")
    return {"processed_signatures": []}


def _save_state(state: dict):
    try:
        SHILL_STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(SHILL_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Shill: failed to save state: {e}")


# ─────────────────────────────────────────────
#  SOLANA RPC HELPERS
# ─────────────────────────────────────────────

def _get_recent_signatures(wallet: str, rpc: str, limit: int = 20) -> list:
    """Return recent tx signatures for the wallet, including the memo field."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [wallet, {"limit": limit}],
        }
        r = requests.post(rpc, json=payload, timeout=10)
        return r.json().get("result", [])
    except Exception as e:
        logger.error(f"Shill: failed to fetch signatures: {e}")
        return []


def _get_sol_received(signature: str, wallet: str, rpc: str) -> float:
    """Return how many SOL our wallet received in this transaction (0 if outgoing)."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                signature,
                {"encoding": "json", "maxSupportedTransactionVersion": 0},
            ],
        }
        r = requests.post(rpc, json=payload, timeout=10)
        data = r.json().get("result")
        if not data:
            return 0.0

        accounts = data["transaction"]["message"]["accountKeys"]
        pre  = data["meta"]["preBalances"]
        post = data["meta"]["postBalances"]

        for i, account in enumerate(accounts):
            if account == wallet:
                delta = post[i] - pre[i]
                return delta / LAMPORTS_PER_SOL if delta > 0 else 0.0

        return 0.0

    except Exception as e:
        logger.error(f"Shill: failed to parse tx {signature[:16]}...: {e}")
        return 0.0


# ─────────────────────────────────────────────
#  MEMO PARSING
# ─────────────────────────────────────────────

def _extract_twitter_handle(memo: str) -> str | None:
    """Extract the first @handle from a memo string."""
    if not memo:
        return None
    match = re.search(r"@(\w{1,50})", memo)
    return f"@{match.group(1)}" if match else None


# ─────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────

def process_shills():
    """
    Scan recent transactions for paid shill requests.
    For each new qualifying tx: generate a mention tweet and post it.
    """
    from modules.solana import get_sol_price_usd
    from modules.brain import generate_shill_tweet
    from modules.twitter import post_tweet

    rpc     = os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
    wallet  = os.getenv("SOLANA_WALLET")
    min_sol = float(os.getenv("SHILL_MIN_SOL", 0.001))

    if not wallet:
        logger.error("Shill: SOLANA_WALLET not set in environment.")
        return

    state     = _load_state()
    processed = set(state.get("processed_signatures", []))

    signatures = _get_recent_signatures(wallet, rpc)
    if not signatures:
        logger.info("Shill: no recent transactions found.")
        return

    sol_price  = get_sol_price_usd()
    new_shills = 0

    for entry in signatures:
        sig  = entry.get("signature")
        memo = entry.get("memo") or ""
        err  = entry.get("err")

        # Skip failed txs and already-processed signatures
        if err or not sig or sig in processed:
            continue

        handle = _extract_twitter_handle(memo)
        if not handle:
            processed.add(sig)
            continue

        logger.info(f"Shill: memo with handle {handle} found in tx {sig[:20]}...")

        try:
            sol_received = _get_sol_received(sig, wallet, rpc)
        except Exception as e:
            logger.error(f"Shill: could not read amount for {sig[:16]}...: {e}")
            processed.add(sig)
            continue

        if sol_received < min_sol:
            logger.info(
                f"Shill: {sig[:16]}... below minimum "
                f"({sol_received:.4f} < {min_sol} SOL) — skipping."
            )
            processed.add(sig)
            continue

        usd_received = sol_received * sol_price
        logger.info(
            f"Shill: qualifying tx — {handle} "
            f"{sol_received:.4f} SOL (${usd_received:.2f})"
        )

        try:
            tweet_text = generate_shill_tweet(handle, sol_received, usd_received)
        except Exception as e:
            logger.error(f"Shill: brain error for {handle}: {e}")
            processed.add(sig)
            continue

        if not tweet_text:
            logger.error(f"Shill: brain returned nothing for {handle} — skipping.")
            processed.add(sig)
            continue

        try:
            result = post_tweet(tweet_text)
            if result:
                logger.info(f"Shill: tweet posted for {handle} — ID: {result['id']}")
                new_shills += 1
            else:
                logger.error(f"Shill: post_tweet failed for {handle}.")
        except Exception as e:
            logger.error(f"Shill: failed to post tweet for {handle}: {e}")

        processed.add(sig)

    state["processed_signatures"] = list(processed)
    _save_state(state)

    logger.info(
        f"Shill: cycle complete — {new_shills} shill(s) processed "
        f"out of {len(signatures)} recent tx(s)."
    )
