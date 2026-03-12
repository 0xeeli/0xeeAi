"""
0xeeTerm — Shill Module

Shill-as-a-Service: listens for incoming SOL transfers with a Twitter
@handle in the transaction memo, and posts a paid mention tweet.

Phase 1: SOL transfers only.
# TODO: accept $0xEE token transfers + increase SHILL_MIN_AMOUNT

Storage : logs/shill_state.json (project-relative, included in nexus backup)
Env vars: SHILL_MIN_SOL (default: 0.001), SOLANA_WALLET, SOLANA_RPC
"""

import os
import re
import json
import logging
import requests
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger("0xeeTerm.shill")

LAMPORTS_PER_SOL = 1_000_000_000

_SERVICE_MIN_SOL = {
    "toll":    float(os.getenv("SHILL_MIN_SOL", 0.005)),
    "genesis": float(os.getenv("SHILL_MIN_SOL", 0.005)),
    "reply":   0.01,
    "verdict": 0.01,
    "roast":   0.01,
    "persona": 0.015,
}

SHILL_STATE_DIR      = Path(__file__).parent.parent / "logs"
SHILL_STATE_FILE     = SHILL_STATE_DIR / "shill_state.json"
GENESIS_REGISTRY_FILE = SHILL_STATE_DIR / "genesis_registry.json"


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
    return {"processed_signatures": [], "tolls_count": 0, "recent_tolls": []}


def _save_state(state: dict):
    try:
        SHILL_STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(SHILL_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Shill: failed to save state: {e}")


def _load_genesis_registry() -> list:
    if GENESIS_REGISTRY_FILE.exists():
        try:
            with open(GENESIS_REGISTRY_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Shill: failed to load genesis registry: {e}")
    return []


def _append_genesis_entry(handle: str, sol: float, tx_sig: str, at: str):
    """Append a new entry to the genesis registry (deduped by tx_sig)."""
    registry = _load_genesis_registry()
    if any(e.get("tx_sig") == tx_sig for e in registry):
        return
    registry.append({"handle": handle, "sol": round(sol, 4), "tx_sig": tx_sig, "at": at})
    try:
        SHILL_STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(GENESIS_REGISTRY_FILE, "w") as f:
            json.dump(registry, f, indent=2)
        logger.info(f"Shill: genesis entry saved — {handle} (#{len(registry)})")
    except Exception as e:
        logger.error(f"Shill: failed to save genesis registry: {e}")


# ─────────────────────────────────────────────
#  SOLANA RPC HELPERS
# ─────────────────────────────────────────────

_PUBLIC_RPC = "https://api.mainnet-beta.solana.com"


def _get_recent_signatures(wallet: str, limit: int = 20) -> list:
    """Return recent tx signatures for the wallet, including the memo field.
    Always uses the public RPC — Helius does not populate the memo field
    in getSignaturesForAddress responses."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [wallet, {"limit": limit}],
        }
        r = requests.post(_PUBLIC_RPC, json=payload, timeout=10)
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


def _extract_tweet_id(memo: str) -> str | None:
    """Extract a tweet ID from a memo — from URL (/status/<id>) or bare numeric ID."""
    if not memo:
        return None
    # From URL: x.com/.../status/<id>
    m = re.search(r"/status/(\d{10,20})", memo)
    if m:
        return m.group(1)
    # From bare numeric ID (tweet IDs are ~19 digits)
    m = re.search(r"\b(\d{18,20})\b", memo)
    if m:
        return m.group(1)
    return None


def _extract_handle_from_tweet_url(memo: str) -> str | None:
    """Extract @handle from a tweet URL: x.com/<handle>/status/<id>."""
    if not memo:
        return None
    m = re.search(r'(?:x\.com|twitter\.com)/(\w{1,50})/status/', memo)
    return f"@{m.group(1)}" if m else None


def _extract_solana_wallet(memo: str) -> str | None:
    """Extract a Solana wallet address (base58, 32-44 chars) from memo."""
    if not memo:
        return None
    m = re.search(r"\b([1-9A-HJ-NP-Za-km-z]{32,44})\b", memo)
    return m.group(1) if m else None


def _parse_service(memo: str) -> dict:
    """Parse memo into service type and parameters.

    Memo formats:
    - "GENESIS @handle"                      → type=genesis
    - "VERDICT @handle <wallet>"             → type=verdict
    - "ROAST <tweet_url>"                    → type=roast (handle extracted from URL)
    - "PERSONA @handle <wallet_address>"     → type=persona
    - "@handle <tweet_id_or_url>"            → type=reply
    - "@handle"                              → type=toll
    - other/empty                            → type=None
    """
    if not memo:
        return {"type": None}

    # Public RPC prefixes memo with "[N] " (byte length) — strip it
    memo = re.sub(r'^\[\d+\]\s*', '', memo.strip())

    # GENESIS @handle
    if re.match(r"^GENESIS\s+@\w", memo, re.IGNORECASE):
        handle = _extract_twitter_handle(memo)
        if handle:
            return {"type": "genesis", "handle": handle}

    # VERDICT @handle <wallet>
    if re.match(r"^VERDICT\s+@\w", memo, re.IGNORECASE):
        handle = _extract_twitter_handle(memo)
        wallet = _extract_solana_wallet(memo)
        if handle:
            return {"type": "verdict", "handle": handle, "wallet": wallet}

    # ROAST <tweet_url>  — handle extracted from URL (x.com/<handle>/status/<id>)
    if re.match(r"^ROAST\s+", memo, re.IGNORECASE):
        tweet_id = _extract_tweet_id(memo)
        handle   = _extract_handle_from_tweet_url(memo)
        if tweet_id:
            return {"type": "roast", "handle": handle, "tweet_id": tweet_id}

    # PERSONA @handle <wallet_address>
    if re.match(r"^PERSONA\s+@\w", memo, re.IGNORECASE):
        handle = _extract_twitter_handle(memo)
        wallet = _extract_solana_wallet(memo)
        if handle:
            return {"type": "persona", "handle": handle, "wallet": wallet}

    # @handle <tweet_id_or_url>
    handle = _extract_twitter_handle(memo)
    if handle:
        tweet_id = _extract_tweet_id(memo)
        if tweet_id:
            return {"type": "reply", "handle": handle, "tweet_id": tweet_id}
        # @handle alone → toll
        return {"type": "toll", "handle": handle}

    return {"type": None}


def _get_wallet_info(wallet: str) -> dict:
    """Fetch basic on-chain info for a Solana wallet address."""
    result = {
        "wallet":        wallet,
        "balance_sol":   0.0,
        "tx_count":      0,
        "first_tx_date": "unknown",
        "last_tx_date":  "unknown",
        "wallet_age_days": 0,
        "txs_per_day":   0.0,
    }
    if not wallet:
        return result

    try:
        r = requests.post(_PUBLIC_RPC, json={
            "jsonrpc": "2.0", "id": 1,
            "method": "getBalance",
            "params": [wallet],
        }, timeout=10)
        bal = r.json().get("result", {}).get("value", 0)
        result["balance_sol"] = bal / LAMPORTS_PER_SOL
    except Exception as e:
        logger.error(f"Shill: _get_wallet_info balance error for {wallet[:16]}...: {e}")

    try:
        r = requests.post(_PUBLIC_RPC, json={
            "jsonrpc": "2.0", "id": 1,
            "method": "getSignaturesForAddress",
            "params": [wallet, {"limit": 1000}],
        }, timeout=15)
        sigs = r.json().get("result", [])
        result["tx_count"] = len(sigs)
        if sigs:
            now = datetime.now(timezone.utc)
            # Most recent tx
            if sigs[0].get("blockTime"):
                dt = datetime.fromtimestamp(sigs[0]["blockTime"], tz=timezone.utc)
                result["last_tx_date"] = dt.strftime("%Y-%m-%d")
            # Oldest tx in sample
            if sigs[-1].get("blockTime"):
                dt = datetime.fromtimestamp(sigs[-1]["blockTime"], tz=timezone.utc)
                result["first_tx_date"] = dt.strftime("%Y-%m-%d")
                age_days = max((now - dt).days, 1)
                result["wallet_age_days"] = age_days
                result["txs_per_day"] = round(len(sigs) / age_days, 1)
    except Exception as e:
        logger.error(f"Shill: _get_wallet_info sigs error for {wallet[:16]}...: {e}")

    return result


# ─────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────

def process_shills():
    """
    Scan recent transactions for on-chain service requests.
    Routes each qualifying tx to the appropriate service handler:
      - toll    : Nexus Toll mention (0.005 SOL, memo: @handle)
      - genesis : Genesis Certificate (0.005 SOL, memo: GENESIS @handle)
      - reply   : Reply-as-a-Service (0.01 SOL, memo: @handle <tweet_url_or_id>)
      - verdict : Wallet Verdict (0.01 SOL, memo: VERDICT @handle <wallet>)
    """
    from modules.solana import get_sol_price_usd, _get_rpc
    from modules.brain import (
        generate_shill_tweet, generate_genesis_tweet,
        generate_reply_tweet, generate_verdict_tweet,
    )
    from modules.twitter import post_tweet, post_reply, get_tweet_text
    from modules.roast import process_roast
    from modules.persona import process_persona

    wallet = os.getenv("SOLANA_WALLET")
    if not wallet:
        logger.error("Shill: SOLANA_WALLET not set in environment.")
        return

    state     = _load_state()
    processed = set(state.get("processed_signatures", []))

    rpc        = _get_rpc()              # used for getTransaction
    signatures = _get_recent_signatures(wallet)  # always public RPC — memo fields
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

        service = _parse_service(memo)
        if not service["type"]:
            if memo:  # memo present but unrecognised → skip definitively
                processed.add(sig)
            continue  # memo empty → retry (late indexing)

        logger.info(
            f"Shill: service={service['type']} handle={service.get('handle')} "
            f"in tx {sig[:20]}..."
        )

        try:
            sol_received = _get_sol_received(sig, wallet, rpc)
        except Exception as e:
            logger.error(f"Shill: could not read amount for {sig[:16]}...: {e}")
            processed.add(sig)
            continue

        min_required = _SERVICE_MIN_SOL[service["type"]]
        if sol_received < min_required:
            logger.info(
                f"Shill: {sig[:16]}... below minimum for {service['type']} "
                f"({sol_received:.4f} < {min_required} SOL) — skipping."
            )
            processed.add(sig)  # intentional skip — mark done
            continue

        usd_received = sol_received * sol_price
        handle       = service["handle"]
        logger.info(
            f"Shill: qualifying tx — {service['type']} {handle} "
            f"{sol_received:.4f} SOL (${usd_received:.2f})"
        )

        # ── ROAST: handled separately (returns composite result) ──────────
        if service["type"] == "roast":
            if not service.get("tweet_id"):
                logger.error(f"Shill: ROAST memo missing tweet_id for {handle} — skipping.")
                processed.add(sig)
                continue
            try:
                roast_result = process_roast(handle, service["tweet_id"], sol_received, sol_price)
            except Exception as e:
                logger.error(f"Shill: ROAST error for {handle}: {e} — will retry next cycle.")
                continue
            if roast_result:
                logger.info(f"Shill: ROAST complete for {handle}")
                new_shills += 1
                now_iso = datetime.now(timezone.utc).isoformat()
                state["tolls_count"] = (state.get("tolls_count") or 0) + 1
                recent = state.get("recent_tolls", [])
                recent.insert(0, {"handle": handle, "sol": round(sol_received, 4), "at": now_iso, "service": "roast"})
                state["recent_tolls"] = recent[:10]
                processed.add(sig)
            else:
                logger.error(f"Shill: ROAST failed for {handle} — will retry next cycle.")
            continue
        # ──────────────────────────────────────────────────────────────────

        # ── PERSONA: handled separately (returns composite result) ────────
        if service["type"] == "persona":
            if not service.get("wallet"):
                logger.error(f"Shill: PERSONA memo missing wallet for {handle} — skipping.")
                processed.add(sig)
                continue
            try:
                persona_result = process_persona(handle, service["wallet"], sol_received, sol_price)
            except Exception as e:
                logger.error(f"Shill: PERSONA error for {handle}: {e} — will retry next cycle.")
                continue
            if persona_result:
                logger.info(f"Shill: PERSONA complete for {handle} — label={persona_result['label']}")
                new_shills += 1
                now_iso = datetime.now(timezone.utc).isoformat()
                state["tolls_count"] = (state.get("tolls_count") or 0) + 1
                recent = state.get("recent_tolls", [])
                recent.insert(0, {"handle": handle, "sol": round(sol_received, 4), "at": now_iso, "service": "persona"})
                state["recent_tolls"] = recent[:10]
                processed.add(sig)
            else:
                logger.error(f"Shill: PERSONA failed for {handle} — will retry next cycle.")
            continue
        # ──────────────────────────────────────────────────────────────────

        tweet_text = None
        result     = None

        try:
            if service["type"] == "toll":
                tweet_text = generate_shill_tweet(handle, sol_received, usd_received)
                if tweet_text:
                    result = post_tweet(tweet_text)

            elif service["type"] == "genesis":
                tweet_text = generate_genesis_tweet(handle, sol_received)
                if tweet_text:
                    result = post_tweet(tweet_text)

            elif service["type"] == "reply":
                orig_text  = get_tweet_text(service["tweet_id"])
                tweet_text = generate_reply_tweet(handle, orig_text, sol_received)
                if tweet_text:
                    result = post_reply(tweet_text, service["tweet_id"])

            elif service["type"] == "verdict":
                wallet_info = _get_wallet_info(service.get("wallet") or "")
                tweet_text  = generate_verdict_tweet(handle, wallet_info)
                if tweet_text:
                    result = post_tweet(tweet_text)

        except Exception as e:
            logger.error(
                f"Shill: error for {service['type']} {handle}: {e} — will retry next cycle."
            )
            continue  # do NOT mark as processed — retry next cycle

        if not tweet_text:
            logger.error(
                f"Shill: brain returned nothing for {service['type']} {handle} "
                f"— will retry next cycle."
            )
            continue  # do NOT mark as processed — retry next cycle

        if result:
            logger.info(
                f"Shill: tweet posted for {service['type']} {handle} — ID: {result['id']}"
            )
            new_shills += 1
            now_iso = datetime.now(timezone.utc).isoformat()
            state["tolls_count"] = (state.get("tolls_count") or 0) + 1
            recent = state.get("recent_tolls", [])
            recent.insert(0, {
                "handle":  handle,
                "sol":     round(sol_received, 4),
                "at":      now_iso,
                "service": service["type"],
            })
            state["recent_tolls"] = recent[:10]
            # Genesis: persist to registry
            if service["type"] == "genesis":
                _append_genesis_entry(handle, sol_received, sig, now_iso)
            processed.add(sig)  # success — mark done
        else:
            logger.error(
                f"Shill: post failed for {service['type']} {handle} — will retry next cycle."
            )
            # do NOT mark as processed — retry next cycle

    # Cap to last 500 to prevent shill_state.json from growing unboundedly
    state["processed_signatures"] = list(processed)[-500:]
    _save_state(state)

    logger.info(
        f"Shill: cycle complete — {new_shills} shill(s) processed "
        f"out of {len(signatures)} recent tx(s)."
    )
