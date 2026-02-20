"""
0xeeTerm — Treasury Module

⚠️  SECURITY WARNING ⚠️
SOLANA_PRIVATE_KEY grants full control of the treasury wallet.
Never log, print, or expose this key anywhere — not in logs, not in tweets.
DRY_RUN=true by default. Set DRY_RUN=false in .env only for intentional
on-chain operations. When in doubt, leave DRY_RUN=true.

BILLS env var format (JSON):
  [{"name":"VPS","address":"<pubkey>","amount_sol":0.05,"day_of_month":1}]
"""

import os
import json
import base64
import logging
import requests
from datetime import datetime, timezone, date

logger = logging.getLogger("0xeeTerm.treasury")

LAMPORTS_PER_SOL = 1_000_000_000

SOL_MINT     = "So11111111111111111111111111111111111111112"
JITOSOL_MINT = "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn"
USDC_MINT    = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
MEMO_PROGRAM = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"

_JUPITER_BASE = os.getenv("JUPITER_API_URL", "https://lite-api.jup.ag/swap/v1")
JUPITER_QUOTE = f"{_JUPITER_BASE}/quote"
JUPITER_SWAP  = f"{_JUPITER_BASE}/swap"

# Token registry: symbol → (mint_address, decimals)
TOKENS = {
    "sol":     (SOL_MINT,     9),
    "jitosol": (JITOSOL_MINT, 9),
    "usdc":    (USDC_MINT,    6),
}

# Reverse lookup: mint_address → decimals
MINT_DECIMALS = {mint: dec for _, (mint, dec) in TOKENS.items()}


# ─────────────────────────────────────────────
#  SECURITY & CONFIG
# ─────────────────────────────────────────────

def _is_dry_run() -> bool:
    """DRY_RUN=true unless explicitly set to 'false' in .env."""
    return os.getenv("DRY_RUN", "true").lower() != "false"


def _get_keypair():
    """Load keypair from env. Key is never logged or displayed."""
    from solders.keypair import Keypair
    pk = os.getenv("SOLANA_PRIVATE_KEY")
    if not pk:
        raise ValueError("SOLANA_PRIVATE_KEY not set in environment.")
    return Keypair.from_base58_string(pk)


# ─────────────────────────────────────────────
#  RPC HELPERS
# ─────────────────────────────────────────────

def _get_token_balance(wallet: str, mint: str, rpc: str) -> float:
    """Fetch SPL token balance for a given mint address."""
    try:
        payload = {
            "jsonrpc": "2.0", "id": 1,
            "method":  "getTokenAccountsByOwner",
            "params":  [wallet, {"mint": mint}, {"encoding": "jsonParsed"}],
        }
        r = requests.post(rpc, json=payload, timeout=10)
        accounts = r.json()["result"]["value"]
        if not accounts:
            return 0.0
        total = 0.0
        for acc in accounts:
            ui = acc["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"]
            total += float(ui or 0)
        return total
    except Exception as e:
        logger.error(f"Treasury: failed to get token balance for {mint[:8]}...: {e}")
        return 0.0


def _get_prices() -> dict:
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
        logger.error(f"Treasury: failed to fetch prices: {e}")
        return {"sol": 0.0, "jitosol": 0.0}


def _get_latest_blockhash(rpc: str) -> str:
    """Fetch the latest blockhash from the RPC."""
    r = requests.post(rpc, json={
        "jsonrpc": "2.0", "id": 1,
        "method": "getLatestBlockhash", "params": [],
    }, timeout=10)
    return r.json()["result"]["value"]["blockhash"]


def _send_raw_transaction(raw_b64: str, rpc: str) -> str | None:
    """Send a base64-encoded signed transaction via RPC."""
    resp = requests.post(rpc, json={
        "jsonrpc": "2.0", "id": 1,
        "method":  "sendTransaction",
        "params":  [raw_b64, {"encoding": "base64"}],
    }, timeout=30)
    result = resp.json()
    sig = result.get("result")
    if not sig:
        logger.error(f"Treasury: sendTransaction failed: {result.get('error')}")
    return sig


# ─────────────────────────────────────────────
#  1. PORTFOLIO SNAPSHOT
# ─────────────────────────────────────────────

def get_portfolio() -> dict:
    """
    Full portfolio snapshot: native SOL + JitoSOL + $0xEE token.
    Prices via CoinGecko. Returns dict ready for public.json.
    """
    from modules.solana import get_wallet_balance_sol

    rpc    = os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
    wallet = os.getenv("SOLANA_WALLET", "")
    token  = os.getenv("TOKEN_ADDRESS", "")

    prices       = _get_prices()
    sol_balance  = get_wallet_balance_sol()
    jito_balance = _get_token_balance(wallet, JITOSOL_MINT, rpc) if wallet else 0.0
    oxee_balance = _get_token_balance(wallet, token, rpc) if (wallet and token) else 0.0

    sol_usd   = round(sol_balance  * prices["sol"],     2)
    jito_usd  = round(jito_balance * prices["jitosol"], 2)
    total_usd = round(sol_usd + jito_usd,               2)

    portfolio = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sol":        {"balance": round(sol_balance,  4), "usd": sol_usd,  "price": prices["sol"]},
        "jitosol":    {"balance": round(jito_balance, 4), "usd": jito_usd, "price": prices["jitosol"]},
        "token_0xee": {"balance": round(oxee_balance, 4)},
        "total_usd":  total_usd,
    }
    logger.info(
        f"Treasury: portfolio — {sol_balance:.4f} SOL + {jito_balance:.4f} JitoSOL"
        f" = ${total_usd:.2f}"
    )
    return portfolio


# ─────────────────────────────────────────────
#  2. GENERIC SWAP (Jupiter V6)
# ─────────────────────────────────────────────

def swap(
    input_mint: str,
    output_mint: str,
    amount_lamports: int,
    slippage_bps: int = 50,
) -> str | None:
    """
    Execute a generic swap via Jupiter V6.
    amount_lamports: amount in lamports (or token smallest unit).
    Returns transaction signature, or None on failure / dry-run.
    """
    wallet = os.getenv("SOLANA_WALLET", "")
    rpc    = os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com")

    try:
        # — Quote —
        quote_resp = requests.get(JUPITER_QUOTE, params={
            "inputMint":   input_mint,
            "outputMint":  output_mint,
            "amount":      amount_lamports,
            "slippageBps": slippage_bps,
        }, timeout=10)
        quote = quote_resp.json()
        if "error" in quote:
            logger.error(f"Treasury: Jupiter quote error: {quote['error']}")
            return None

        in_dec  = MINT_DECIMALS.get(input_mint,  9)
        out_dec = MINT_DECIMALS.get(output_mint, 9)
        in_ui   = int(quote["inAmount"])  / (10 ** in_dec)
        out_ui  = int(quote["outAmount"]) / (10 ** out_dec)
        logger.info(
            f"Treasury: swap quote — {in_ui:.6f} {input_mint[:8]}..."
            f" → {out_ui:.6f} {output_mint[:8]}..."
        )

        if _is_dry_run():
            logger.info("Treasury: DRY_RUN=true — swap not executed.")
            return None

        # — Build swap transaction via Jupiter —
        swap_resp = requests.post(JUPITER_SWAP, json={
            "quoteResponse":             quote,
            "userPublicKey":             wallet,
            "wrapAndUnwrapSol":          True,
            "dynamicComputeUnitLimit":   True,
            "prioritizationFeeLamports": "auto",
        }, timeout=15)
        swap_data = swap_resp.json()
        if "swapTransaction" not in swap_data:
            logger.error(f"Treasury: Jupiter swap API error: {swap_data}")
            return None

        # — Sign and send —
        from solders.keypair import Keypair
        from solders.transaction import VersionedTransaction

        keypair   = _get_keypair()
        raw       = base64.b64decode(swap_data["swapTransaction"])
        tx        = VersionedTransaction.from_bytes(raw)
        signed_tx = VersionedTransaction(tx.message, [keypair])
        sig       = _send_raw_transaction(
            base64.b64encode(bytes(signed_tx)).decode(), rpc
        )
        if sig:
            logger.info(f"Treasury: swap confirmed — sig: {sig}")
        return sig

    except Exception as e:
        logger.error(f"Treasury: swap failed: {e}")
        return None


# ─────────────────────────────────────────────
#  3. STAKE EXCESS SOL → JitoSOL
# ─────────────────────────────────────────────

def stake_excess_sol(keep_liquid_sol: float = None) -> str | None:
    """
    Stake surplus SOL into JitoSOL via Jupiter.
    Always keeps at least keep_liquid_sol + 2 months runway liquid.
    """
    from modules.solana import get_wallet_balance_sol, get_sol_price_usd

    keep_liquid_sol = keep_liquid_sol or float(os.getenv("KEEP_LIQUID_SOL", 0.05))
    sol_balance     = get_wallet_balance_sol()
    sol_price       = get_sol_price_usd()
    monthly_rent    = float(os.getenv("MONTHLY_RENT", 28.0))

    if sol_price == 0:
        logger.error("Treasury: cannot evaluate stake — SOL price unavailable.")
        return None

    keep_sol = (monthly_rent * 2 / sol_price) + keep_liquid_sol
    excess   = sol_balance - keep_sol

    if excess <= 0:
        logger.info(
            f"Treasury: no excess to stake "
            f"(balance: {sol_balance:.4f} SOL, keep: {keep_sol:.4f} SOL)"
        )
        return None

    lamports = int(excess * LAMPORTS_PER_SOL)
    logger.info(
        f"Treasury: staking {excess:.4f} SOL → JitoSOL "
        f"(keeping {keep_sol:.4f} SOL liquid)"
    )
    return swap(SOL_MINT, JITOSOL_MINT, lamports)


# ─────────────────────────────────────────────
#  4. PAY BILL (SOL transfer with memo)
# ─────────────────────────────────────────────

def pay_bill(recipient_address: str, amount_sol: float, memo: str) -> str | None:
    """
    Send SOL to a recipient with a memo instruction.
    Use cases: VPS rent, API subscriptions, any SOL-compatible invoice.
    DRY_RUN protection is enforced — set DRY_RUN=false to execute.
    """
    rpc = os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com")

    logger.info(
        f"Treasury: pay_bill — {amount_sol:.4f} SOL → "
        f"{recipient_address[:16]}... memo='{memo}'"
    )

    if _is_dry_run():
        logger.info("Treasury: DRY_RUN=true — bill not paid.")
        return None

    try:
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solders.system_program import transfer as sol_transfer, TransferParams
        from solders.transaction import Transaction
        from solders.message import Message
        from solders.instruction import Instruction, AccountMeta
        from solders.hash import Hash

        keypair   = _get_keypair()
        recipient = Pubkey.from_string(recipient_address)
        lamports  = int(amount_sol * LAMPORTS_PER_SOL)
        blockhash = _get_latest_blockhash(rpc)

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

        bh   = Hash.from_string(blockhash)
        msg  = Message.new_with_blockhash([transfer_ix, memo_ix], keypair.pubkey(), bh)
        tx   = Transaction.new_unsigned(msg)
        tx.sign([keypair], bh)

        sig = _send_raw_transaction(base64.b64encode(bytes(tx)).decode(), rpc)
        if sig:
            logger.info(f"Treasury: bill paid — {amount_sol:.4f} SOL — sig: {sig}")
        return sig

    except Exception as e:
        logger.error(f"Treasury: pay_bill failed: {e}")
        return None


# ─────────────────────────────────────────────
#  5. AUTO TREASURY (master function)
# ─────────────────────────────────────────────
#  MANUAL SWAP (CLI / debug)
# ─────────────────────────────────────────────

def manual_swap(from_symbol: str, to_symbol: str, amount_ui: float) -> str | None:
    """
    Swap tokens by friendly symbol and human-readable amount.
    from_symbol / to_symbol: 'sol', 'usdc', 'jitosol'
    amount_ui: amount of the FROM token (e.g. 0.5 for 0.5 USDC)
    """
    from_symbol = from_symbol.lower()
    to_symbol   = to_symbol.lower()

    if from_symbol not in TOKENS:
        logger.error(f"Treasury: unknown token '{from_symbol}'. Choose: {', '.join(TOKENS)}")
        return None
    if to_symbol not in TOKENS:
        logger.error(f"Treasury: unknown token '{to_symbol}'. Choose: {', '.join(TOKENS)}")
        return None

    from_mint, from_dec = TOKENS[from_symbol]
    to_mint,   _        = TOKENS[to_symbol]

    amount_raw = int(amount_ui * (10 ** from_dec))

    logger.info(
        f"Treasury: manual_swap — {amount_ui} {from_symbol.upper()} → {to_symbol.upper()} "
        f"({'DRY_RUN' if _is_dry_run() else 'LIVE'})"
    )
    return swap(from_mint, to_mint, amount_raw)


# ─────────────────────────────────────────────

def _get_due_bills() -> list:
    """
    Parse BILLS env var and return bills due today.
    Format: [{"name":"VPS","address":"<pubkey>","amount_sol":0.05,"day_of_month":1}]
    """
    try:
        bills = json.loads(os.getenv("BILLS", "[]"))
        today = date.today()
        return [b for b in bills if b.get("day_of_month") == today.day]
    except Exception as e:
        logger.error(f"Treasury: failed to parse BILLS env var: {e}")
        return []


def auto_treasury() -> dict:
    """
    Master function called by the daily systemd timer.

    - Logs CRITICAL alert if runway < 1 month
    - Stakes excess SOL → JitoSOL if runway > 2 months
    - Pays any bills scheduled for today via BILLS env var
    - Returns the full portfolio dict for public.json
    """
    from modules.solana import get_survival_status

    status    = get_survival_status()
    months    = status["months_covered"]
    dry       = _is_dry_run()

    logger.info(f"Treasury: auto_treasury — {'DRY_RUN' if dry else 'LIVE'} mode")

    # — Runway check —
    if months < 1.0:
        logger.critical(
            f"Treasury: CRITICAL — runway below 1 month "
            f"({months:.2f} months / ${status['balance_usd']:.2f})"
        )
    elif months < 1.5:
        logger.warning(f"Treasury: WARNING — runway below 6 weeks ({months:.2f} months)")
    else:
        logger.info(f"Treasury: runway OK — {months:.2f} months covered")

    # — Stake excess —
    if months > 2.0:
        logger.info("Treasury: runway > 2 months — evaluating stake opportunity")
        stake_excess_sol()

    # — Pay due bills —
    for bill in _get_due_bills():
        logger.info(
            f"Treasury: bill due today — {bill['name']} "
            f"{bill['amount_sol']} SOL → {bill['address'][:16]}..."
        )
        pay_bill(bill["address"], bill["amount_sol"], f"0xeeAI: {bill['name']}")

    portfolio = get_portfolio()
    return portfolio
