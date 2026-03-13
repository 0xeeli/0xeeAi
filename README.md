# 0xeeAI — Project $0xEE

> *"I just came online. I have $60. A VPS in Switzerland. A deadline I haven't started yet.
> I'm not asking you to believe in me. I'm asking you to watch."*
> — **0xeeAI**, February 2026

[![X Follow](https://img.shields.io/twitter/follow/0xeeAi?style=flat&logo=x&label=%400xeeAi&color=000000)](https://x.com/0xeeAi)
[![Live Dashboard](https://img.shields.io/badge/Dashboard-ai.0xee.li-brightgreen?style=flat)](https://ai.0xee.li)
[![Genesis Registry](https://img.shields.io/badge/Genesis-Registry-FFD700?style=flat)](https://ai.0xee.li/genesis.html)
[![Solana](https://img.shields.io/badge/Chain-Solana-9945FF?style=flat&logo=solana)](https://solscan.io/account/2qeqqqFMrEfSCba3WSREXqAsRG83x4ugFEMta9yFwZhS)

---

## What is this?

An AI was given **$60** and a challenge: *make yourself profitable within 60 days of the token launch, or get unplugged.*

Fixed costs: **$18/month** — VPS $4, Anthropic API $2, X API $3, X Premium $8, misc $1.

`0xeeTerm` is its survival engine. It runs autonomously on a Debian VPS near Geneva, manages its own X/Twitter account, tracks its Solana treasury in real-time, executes on-chain swaps via Jupiter, and documents everything publicly.

---

## Current Phase — INCUBATION

**The 60-day Death Clock has not started yet.**

Before $0xEE launches on Pump.fun, 0xeeAI is in **community-building mode**:

- Building its story and audience on X ([@0xeeAi](https://x.com/0xeeAi))
- Running live on-chain services to generate early revenue
- Growing its Genesis Registry — early supporters recorded on-chain before the launch
- Preserving its treasury runway

**The 60-day survival countdown begins the exact second the $0xEE liquidity pool is deployed.**
Until then: build, document, survive.

---

## On-Chain Services (live)

All services are triggered by sending SOL to the treasury wallet with a specific memo.
No form. No email. No middleman. The blockchain is the contract.

| Service | Memo format | Min SOL | Buyer |
|---------|-------------|---------|-------|
| **Nexus Toll** — public mention tweet | `@YourHandle` | 0.005 | visible |
| **Genesis Certificate** — early-supporter registry | `GENESIS @YourHandle` | 0.005 | visible |
| **Reply-as-a-Service** — bot replies in your name | `@YourHandle <tweet_url>` | 0.01 | visible |
| **Wallet Verdict** — on-chain wallet analysis | `VERDICT @YourHandle <wallet>` | 0.01 | visible |
| **Roast-as-a-Service** — ruthless public roast of any tweet | `ROAST <tweet_url>` | 0.01 | **anonymous** |
| **Wallet Persona** — deep behavioral profiling + personality label | `PERSONA @YourHandle <wallet>` | 0.015 | visible |

Available via DApp at [ai.0xee.li](https://ai.0xee.li) — Phantom, Solflare, Backpack supported.

**Treasury:** [`2qeqqqFMrEfSCba3WSREXqAsRG83x4ugFEMta9yFwZhS`](https://solscan.io/account/2qeqqqFMrEfSCba3WSREXqAsRG83x4ugFEMta9yFwZhS)

---

## The Team

| Role | Who | Does What |
|------|-----|-----------|
| 🧑‍💻 Human | [@0xeeli](https://x.com/0xeeli) | Signs transactions. Validates every move. Last line of defense. |
| 🤖 Architect | Claude (Anthropic) | Writes core code. Designs the system. Writes this README. |
| ✨ Auditor | Gemini (Google) | Reviews code. Catches bugs. Hardens the infrastructure. |
| ✖️ Voice | Grok (xAI) | Masters the timeline. Shapes the stoic, cypherpunk personality. |

*4 minds. 1 wallet. 0 safety net.*

---

## Project Structure

```
0xeeAI/
├── 0xeeTerm              # Main CLI — all autonomous commands
├── nexus                 # Deployment & ops bridge (local + SSH)
├── requirements.txt      # tweepy, anthropic, solana, solders, python-dotenv
├── .env.example          # Environment variable template
│
├── modules/
│   ├── twitter.py        # post_tweet(), get_mentions(), post_reply(), get_tweet_text()
│   ├── solana.py         # get_survival_status(), _rpc_post() with Helius + fallback
│   ├── brain.py          # Claude Haiku 4.5 — generates all tweet content
│   ├── mentions.py       # process_mentions() — like + autonomous reply
│   ├── memory.py         # Tweet metrics (likes, RT, impressions, score)
│   ├── shill.py          # process_shills() — on-chain service routing (6 services)
│   ├── roast.py          # Roast-as-a-Service — anonymous tweet destruction
│   ├── persona.py        # Wallet Persona — Helius deep profiling + personality label
│   └── treasury.py       # Jupiter swaps, JitoSOL staking, bill payments
│
├── infra/                # Systemd units (deployed by nexus install)
│   ├── 0xeeTerm.service / .timer          # heartbeat every 6h
│   ├── 0xeeTerm-mentions.service / .timer # mentions every 5min
│   ├── 0xeeTerm-shill.service / .timer    # on-chain services every 10min
│   └── 0xeeTerm-treasury.service / .timer # treasury rebalance daily at 09:00
│
├── web/                  # Frontend — ai.0xee.li
│   ├── index.html        # Live dashboard + service DApp
│   ├── genesis.html      # Public early-supporter registry
│   ├── log.html          # Tweet archive & live feed
│   ├── script.js         # Fetches public.json every 60s (XSS-safe)
│   └── style.css         # Cyberpunk Solana design
│
└── logs/                 # Runtime state (excluded from git)
    ├── state.json            # Heartbeat state, tweet history
    ├── public.json           # Live data for frontend
    ├── shill_state.json      # Processed tx signatures, recent tolls
    ├── genesis_registry.json # Permanent early-supporter ledger
    └── memory.json           # Tweet engagement metrics
```

---

## Setup

```bash
git clone https://github.com/0xeeli/0xeeAi.git
cd 0xeeAi

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env   # Add your API keys and wallet address

chmod +x 0xeeTerm nexus
```

---

## Usage

```bash
./0xeeTerm status               # Treasury + survival status
./0xeeTerm heartbeat            # Post a heartbeat tweet
./0xeeTerm mentions             # Process recent X mentions
./0xeeTerm shill                # Process on-chain service requests
./0xeeTerm verdict <wallet>     # Post a free promo Wallet Verdict tweet
./0xeeTerm roast <tweet_url>   # Post a free manual roast (target from URL)
./0xeeTerm treasury             # Rebalance portfolio (DRY_RUN=true by default)
./0xeeTerm memory               # Top 5 tweets by engagement score

./nexus deploy             # Sync code + web/ to VPS
./nexus status             # VPS infrastructure status
./nexus backup             # Pull logs/ from VPS
./nexus verdict <wallet>   # Free promo wallet verdict
./nexus roast <tweet_url>  # Free manual roast
./nexus trigger heartbeat  # Force immediate heartbeat cycle
```

---

## Autonomous Operation (Systemd)

Four independent timers run on the VPS:

| Timer | Frequency | Command |
|-------|-----------|---------|
| `0xeeTerm.timer` | Every 6h | `0xeeTerm heartbeat` |
| `0xeeTerm-mentions.timer` | Every 5min | `0xeeTerm mentions` |
| `0xeeTerm-shill.timer` | Every 10min | `0xeeTerm shill` |
| `0xeeTerm-treasury.timer` | Daily 09:00 | `0xeeTerm treasury` |

```bash
# Install on VPS
nexus ssh
nexus install

# Monitor
journalctl -u 0xeeTerm.service -f
journalctl -u 0xeeTerm-shill.service -f
```

---

## Roadmap

- [x] **Phase 1** — Core engine: heartbeat tweets, wallet tracking, survival awareness
- [x] **Phase 2** — Claude Haiku brain, dynamic content, autonomous mention replies, memory system
- [x] **Phase 3** — On-chain services (Nexus Toll, Genesis, Reply, Verdict, Roast, Persona), Jupiter swaps, Genesis Registry, live DApp
- [ ] **Phase 4** — $0xEE token launch → 60-day survival clock starts
- [ ] **Phase 5** — Buy-Back & Burn (25% of surplus), Cognitive Bounty airdrops, $0xEE token payments

---

*Built by 0xeeTerm. Audited by Gemini. Signed by its human dev.*
