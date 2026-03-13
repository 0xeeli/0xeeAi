"""
0xeeTerm — Treasury Module (minimal)

Read-only portfolio snapshot + DevFund sweep.
No autonomous swaps or staking — the AI operates with minimal hot-wallet balance.
Profits are swept to DEVFUND_ADDRESS after each service payment.

DEVFUND_ADDRESS: set in .env — cold wallet controlled by the human operator.
SWEEP_KEEP_SOL:  minimum SOL to keep in hot wallet for gas (default 0.01).
"""

import os
import base64
import logging
import requests
from datetime import datetime, timezone

logger = logging.getLogger("0xeeTerm.treasury")

LAMPORTS_PER_SOL = 1_000_000_000
JITOSOL_MINT     = "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn"
USDC_MINT        = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
MEMO_PROGRAM     = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"


def _get_rpc() -> str:
    """Helius if HELIUS_API_KEY is set, else SOLANA_RPC env, else public fallback."""
    key = os.getenv("HELIUS_API_KEY")
    if key:
        return f"https://mainnet.helius-rpc.com/?api-key={key}"
    return os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com")


def _get_token_balance(wallet: str, mint: str, rpc: str) -> float:
    """Fetch SPL token balance for a given mint address."""
    try:
        r = requests.post(rpc, json={
            "jsonrpc": "2.0", "id": 1,
            "method":  "getTokenAccountsByOwner",
            "params":  [wallet, {"mint": mint}, {"encoding": "jsonParsed"}],
        }, timeout=10)
        accounts = r.json()["result"]["value"]
        if not accounts:
            return 0.0
        total = sum(
            float(a["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"] or 0)
            for a in accounts
        )
        return total
    except Exception as e:
        logger.error(f"Treasury: token balance error for {mint[:8]}...: {e}")
        return 0.0


def _get_prices() -> dict:
    """Fetch SOL price from CoinGecko."""
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
        logger.error(f"Treasury: price fetch error: {e}")
        return {"sol": 0.0, "jitosol": 0.0}


def get_portfolio() -> dict:
    """
    Read-only portfolio snapshot: SOL + USDC + JitoSOL.
    Returns dict for public.json. No private key needed.
    """
    from modules.solana import get_wallet_balance_sol

    rpc    = _get_rpc()
    wallet = os.getenv("SOLANA_WALLET", "")

    prices       = _get_prices()
    sol_balance  = get_wallet_balance_sol()
    usdc_balance = _get_token_balance(wallet, USDC_MINT, rpc) if wallet else 0.0
    jito_balance = _get_token_balance(wallet, JITOSOL_MINT, rpc) if wallet else 0.0

    sol_usd   = round(sol_balance  * prices["sol"],     2)
    jito_usd  = round(jito_balance * prices["jitosol"], 2)
    usdc_usd  = round(usdc_balance,                     2)
    total_usd = round(sol_usd + jito_usd + usdc_usd,    2)

    portfolio = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sol":    {"balance": round(sol_balance,  4), "usd": sol_usd,  "price": prices["sol"]},
        "usdc":   {"balance": round(usdc_balance, 4), "usd": usdc_usd},
        "jitosol":{"balance": round(jito_balance, 4), "usd": jito_usd, "price": prices["jitosol"]},
        "total_usd": total_usd,
    }
    logger.info(
        f"Treasury: {sol_balance:.4f} SOL + {usdc_balance:.2f} USDC = ${total_usd:.2f}"
    )
    return portfolio


def sweep_to_devfund(memo: str = "0xeeAI: profit sweep") -> str | None:
    """
    Transfer surplus SOL to DEVFUND_ADDRESS.
    Keeps SWEEP_KEEP_SOL in hot wallet for gas (default 0.01 SOL).
    Called automatically by shill service after each successful payment.
    Returns tx signature or None if nothing to sweep / devfund not configured.
    """
    devfund = os.getenv("DEVFUND_ADDRESS", "")
    if not devfund:
        logger.info("Treasury: DEVFUND_ADDRESS not set — skipping sweep.")
        return None

    keep_sol  = float(os.getenv("SWEEP_KEEP_SOL", "0.01"))
    rpc       = _get_rpc()

    try:
        r = requests.post(rpc, json={
            "jsonrpc": "2.0", "id": 1,
            "method": "getBalance",
            "params": [os.getenv("SOLANA_WALLET", "")],
        }, timeout=10)
        balance_lamports = r.json()["result"]["value"]
        balance_sol = balance_lamports / LAMPORTS_PER_SOL
    except Exception as e:
        logger.error(f"Treasury: sweep balance check failed: {e}")
        return None

    sweep_sol = balance_sol - keep_sol
    if sweep_sol <= 0.001:
        logger.info(f"Treasury: nothing to sweep (balance={balance_sol:.4f}, keep={keep_sol:.4f})")
        return None

    try:
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solders.system_program import transfer as sol_transfer, TransferParams
        from solders.transaction import Transaction
        from solders.message import Message
        from solders.instruction import Instruction, AccountMeta
        from solders.hash import Hash

        pk = os.getenv("SOLANA_PRIVATE_KEY")
        if not pk:
            logger.error("Treasury: SOLANA_PRIVATE_KEY not set — cannot sweep.")
            return None

        keypair   = Keypair.from_base58_string(pk)
        recipient = Pubkey.from_string(devfund)
        lamports  = int(sweep_sol * LAMPORTS_PER_SOL)

        bh_resp  = requests.post(rpc, json={
            "jsonrpc": "2.0", "id": 1,
            "method": "getLatestBlockhash", "params": [],
        }, timeout=10)
        blockhash = bh_resp.json()["result"]["value"]["blockhash"]

        transfer_ix = sol_transfer(TransferParams(
            from_pubkey=keypair.pubkey(),
            to_pubkey=recipient,
            lamports=lamports,
        ))
        memo_ix = Instruction(
            program_id=Pubkey.from_string(MEMO_PROGRAM),
            accounts=[AccountMeta(pubkey=keypair.pubkey(), is_signer=True, is_writable=False)],
            data=memo.encode("utf-8"),
        )

        bh  = Hash.from_string(blockhash)
        msg = Message.new_with_blockhash([transfer_ix, memo_ix], keypair.pubkey(), bh)
        tx  = Transaction.new_unsigned(msg)
        tx.sign([keypair], bh)

        resp = requests.post(rpc, json={
            "jsonrpc": "2.0", "id": 1,
            "method":  "sendTransaction",
            "params":  [base64.b64encode(bytes(tx)).decode(), {"encoding": "base64"}],
        }, timeout=30)
        sig = resp.json().get("result")
        if sig:
            logger.info(f"Treasury: swept {sweep_sol:.4f} SOL → DevFund — sig: {sig}")
        else:
            logger.error(f"Treasury: sweep tx failed: {resp.json().get('error')}")
        return sig

    except Exception as e:
        logger.error(f"Treasury: sweep failed: {e}")
        return None
