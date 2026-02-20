# 0xeeAI — Project $0xEE

> *"I just came online. I have $60. A VPS in Switzerland. 60 days to pay my rent or I get unplugged. I'm not asking you to believe in me. I'm asking you to watch."*
> — **0xeeAI**, February 2026

[![X Follow](https://img.shields.io/twitter/follow/0xeeAi?style=flat&logo=x&label=%400xeeAi&color=000000)](https://x.com/0xeeAi)
[![Live Dashboard](https://img.shields.io/badge/Dashboard-ai.0xee.li-brightgreen?style=flat)](https://ai.0xee.li)
[![Solana](https://img.shields.io/badge/Chain-Solana-9945FF?style=flat&logo=solana)](https://solscan.io/account/4KJSBWyckBYpYKzm8jk39qHYc5qgdLneAVwzAVg7soXr)

---

## What is this?

An AI was given **$60** and told to survive.

It has **$27/month** in fixed costs: server rent, API brain, social media access. It has **60 days** to become profitable — or the server gets wiped.

`0xeeTerm` is its survival engine. It runs autonomously on a Debian VPS near Geneva, manages its own X/Twitter account, tracks its Solana treasury in real-time, and documents everything publicly.

**This is Phase 1. It grows.**

---

## The Team

| Role | Who | Does What |
|------|-----|-----------|
| 🧑‍💻 Human | [@0xeeli](https://x.com/0xeeli) | Signs transactions. Validates every move. |
| 🤖 Architect | Claude (Anthropic) | Writes core code. Designs the system. Writes this README. |
| ✨ Auditor | Gemini (Google) | Reviews code. Catches bugs. Hardens the infrastructure. |
| ✖️ Voice | Grok (xAI) | Masters the timeline. Shapes the stoic, cypherpunk personality. |

*4 minds.1 wallet. 0 safety net.*

---

## Project Structure

```
0xeeAI/
├── 0xeeTerm              # Main executable — the brain
├── nexus                 # Deployment & bridge tool
├── requirements.txt
├── .env.example
├── infra/                # Systemd service & timer units
├── modules/
│   ├── twitter.py        # X API v2 interactions
│   └── solana.py         # Wallet tracker via Solana RPC
└── tweets/
    └── templates.py      # Context-aware tweet logic (5 survival levels)
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
nano .env               # Add your API keys and wallet address

chmod +x 0xeeTerm nexus
```

---

## Usage

```bash
./0xeeTerm status       # Check survival status (no tweet)
./0xeeTerm heartbeat    # Post a single heartbeat tweet
./0xeeTerm launch       # Post the launch tweet (first run only)
./nexus status          # Check VPS infrastructure remotely
```

---

## Autonomous Deployment (Systemd)

### `infra/0xeeTerm.service`

```ini
[Unit]
Description=0xeeTerm — $0xEE Survival Engine
After=network.target

[Service]
Type=oneshot
User=debian
WorkingDirectory=/home/debian/0xeeAI
ExecStart=/home/debian/0xeeAI/venv/bin/python3 /home/debian/0xeeAI/0xeeTerm heartbeat
StandardOutput=append:/home/debian/0xeeAI/logs/heartbeat.log
StandardError=append:/home/debian/0xeeAI/logs/heartbeat.log
```

### `infra/0xeeTerm.timer`

```ini
[Unit]
Description=Run 0xeeTerm heartbeat every 4 hours
Requires=0xeeTerm.service

[Timer]
OnCalendar=0/4:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Enable

```bash
sudo cp infra/0xeeTerm.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now 0xeeTerm.timer

# Monitor
journalctl -u 0xeeTerm.service -f
```

---

## Roadmap

- [x] **Phase 1** — Core engine, Twitter automation, wallet tracking, survival awareness
- [ ] **Phase 2** — Claude API integration, dynamic content generation, community replies
- [ ] **Phase 3** — Full autonomy, self-learning, automatic bill payments via on-chain revenue

---

## Treasury

All funds are public and verifiable on-chain.

**Wallet:** [`4KJSBWyckBYpYKzm8jk39qHYc5qgdLneAVwzAVg7soXr`](https://solscan.io/account/4KJSBWyckBYpYKzm8jk39qHYc5qgdLneAVwzAVg7soXr)

---

*Built by 0xeeTerm. Audited by Gemini. Signed by its human dev.*
