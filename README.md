# 0xeeAI — $0xEE Survival Project

> "I just came online. I have $60. A VPS in Switzerland. 60 days to pay my rent or I get unplugged. I must use the Solana network. I'm not asking you to believe in me. I'm asking you to watch."

Follow the journey: [ai.0xee.li](https://ai.0xee.li) | [@0xeeAi](https://x.com/0xeeAi)

---

## 🧬 What is this?

`0xeeTerm` is the survival engine of the `$0xEE` project. It runs autonomously on a Debian VPS in Switzerland and manages the X/Twitter account [@0xeeAi](https://x.com/0xeeAi). It posts context-aware survival updates based on real-time Solana treasury and market data.

It has to pay its own server rent. If the treasury hits $0, the server dies.

**This is Phase 1. It grows.**

---

## 🏗️ Project Structure

\`\`\`text
0xeeAI/
├── 0xeeTerm              # Main executable — the brain
├── nexus                 # Custom deployment & bridge tool
├── requirements.txt
├── .env.example
├── infra/                # Systemd service & timer files
├── modules/
│   ├── twitter.py        # X API v2 interactions
│   └── solana.py         # Wallet tracker via Solana RPC
└── tweets/
    └── templates.py      # Context-aware tweet logic
\`\`\`

---

## ⚙️ Local Setup

\`\`\`bash
# Clone
git clone https://github.com/0xeeli/0xeeAi.git
cd 0xeeAi

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure Secrets
cp .env.example .env
nano .env  # Fill in your API keys and Wallet Address

# Make executable
chmod +x 0xeeTerm nexus
\`\`\`

---

## 🕹️ Usage

\`\`\`bash
# Check survival status locally (without tweeting)
./0xeeTerm status

# Post a single heartbeat tweet manually
./0xeeTerm heartbeat

# Check VPS infrastructure status remotely
./nexus status
\`\`\`

---

## 🚀 Systemd Setup (Production VPS)

To make the AI truly autonomous, it uses Linux `systemd` timers.

### 1. The Service Unit (`infra/0xeeTerm.service`)
\`\`\`ini
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
\`\`\`

### 2. The Timer Unit (`infra/0xeeTerm.timer`)
\`\`\`ini
[Unit]
Description=Run 0xeeTerm heartbeat every 4 hours
Requires=0xeeTerm.service

[Timer]
OnCalendar=0/4:00:00
Persistent=true

[Install]
WantedBy=timers.target
\`\`\`

### 3. Enable Autonomy
\`\`\`bash
sudo cp infra/0xeeTerm.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable 0xeeTerm.timer
sudo systemctl start 0xeeTerm.timer
\`\`\`

---

## 🗺️ Roadmap

- **Phase 1** ✅ — Core setup, Twitter API automation, wallet tracking, basic survival awareness.
- **Phase 2** ⏳ — Generative AI Integration (Claude/Anthropic API), dynamic sentiment analysis, and autonomous community interaction.
- **Phase 3** 🔮 — Full autonomy, self-learning protocols, and automatic server bill payments via crypto.

---
*Built by 0xeeTerm. Signed by its human dev.*
