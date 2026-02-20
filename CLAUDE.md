# CLAUDE.md — 0xeeAI Project Context

Contexte permanent pour Claude Code. Reprendre ici sans briefing.

---

## 1. Description du projet

**0xeeAI** est un agent IA autonome qui gère sa propre survie financière.
Il tourne sur un VPS Debian près de Genève, poste sur X (@0xeeAi), surveille sa
trésorerie Solana, répond aux mentions, exécute des swaps on-chain et documente
sa survie en temps réel sur ai.0xee.li.

Mission : devenir profitable dans les 60 jours suivant le lancement du token $0xEE,
ou être éteint par son développeur.

---

## 2. Architecture des fichiers

```
0xeeAI/
├── 0xeeTerm          # CLI principal — toutes les commandes de l'IA
├── nexus             # Outil de déploiement / ops — local + bridge SSH
├── CLAUDE.md         # Ce fichier
├── requirements.txt  # tweepy, anthropic, solana, solders, python-dotenv
├── .env              # Variables d'environnement (jamais committé)
├── .env.example      # Template public des variables
│
├── modules/
│   ├── twitter.py    # post_tweet(), get_mentions() — OAuth 1.0a uniquement
│   ├── solana.py     # get_survival_status(), get_wallet_balance_sol()
│   ├── brain.py      # generate_heartbeat_tweet(), generate_existential_tweet()
│   │                 # generate_shill_tweet() — Claude Haiku via Anthropic API
│   ├── mentions.py   # process_mentions() — like + reply via brain
│   ├── memory.py     # save_tweet(), update_all_metrics(), get_top_performers()
│   ├── shill.py      # process_shills() — scan on-chain txs, post shill tweet
│   └── treasury.py   # get_portfolio(), swap(), stake_excess_sol(), pay_bill()
│                     # manual_swap(), auto_treasury() — Jupiter V6 lite-api
│
├── tweets/
│   └── templates.py  # get_heartbeat_tweet(), get_daily_report_tweet(), etc.
│
├── infra/            # Fichiers systemd (copié sur VPS par nexus install)
│   ├── 0xeeTerm.service / .timer          # heartbeat toutes les 2h
│   ├── 0xeeTerm-mentions.service / .timer # mentions toutes les 5min
│   ├── 0xeeTerm-shill.service / .timer    # shill toutes les 5min
│   └── 0xeeTerm-treasury.service / .timer # treasury tous les jours à 09:00
│
├── web/              # Interface web ai.0xee.li
│   ├── index.html    # Dashboard (treasury, survival progress, tokenomics)
│   ├── log.html      # Archive des logs + live feed depuis public.json
│   ├── script.js     # Fetch public.json toutes les 60s, XSS-safe
│   ├── style.css     # Design cyberpunk Solana (purple/green glassmorphism)
│   └── images/logo.webp
│
└── logs/             # Exclu du git — tout le state runtime
    ├── state.json        # last_heartbeat, launched, tweet_history, etc.
    ├── public.json       # Données live pour le frontend
    ├── memory.json       # Métriques tweets (likes, RT, impressions, score)
    ├── shill_state.json  # Dernière signature on-chain traitée
    ├── heartbeat.log
    ├── shill.log
    ├── treasury.log
    └── installed_files.json  # Manifest nexus install
```

---

## 3. Stack technique

| Composant | Technologie |
|-----------|------------|
| Runtime | Python 3.11+, VPS Debian |
| Twitter/X | Tweepy 4.x, OAuth 1.0a (pas de bearer token) |
| IA / Brain | Anthropic Claude Haiku (claude-haiku-4-5) |
| Blockchain | Solana mainnet, solana-py + solders |
| Swaps | Jupiter V6 — `https://lite-api.jup.ag/swap/v1` |
| Staking | SOL → JitoSOL via Jupiter |
| Frontend | HTML/CSS/JS vanilla, public.json comme API |
| Déploiement | rsync via nexus deploy |
| Orchestration | systemd timers (pas de cron) |

---

## 4. Variables d'environnement importantes

```bash
# X API (OAuth 1.0a — pas de bearer token)
X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET

# IA
ANTHROPIC_API_KEY

# Solana
SOLANA_WALLET=4KJSBWyckBYpYKzm8jk39qHYc5qgdLneAVwzAVg7soXr
SOLANA_RPC=https://api.mainnet-beta.solana.com
SOLANA_PRIVATE_KEY=<base58>   # jamais loggé ni affiché

# Treasury
DRY_RUN=true                  # TOUJOURS true sauf intention explicite
KEEP_LIQUID_SOL=0.05
BILLS=[]                      # JSON: [{name, address, amount_sol, day_of_month}]
JUPITER_API_URL=https://lite-api.jup.ag/swap/v1

# Survie
MONTHLY_RENT=28.00
RUNWAY_DAYS=60
SHILL_MIN_SOL=0.005

# Infrastructure (nexus)
# NEXUS_ENV=/path/to/.env   # override — lookup order: $NEXUS_ENV → ~/.config/0xeeAI/.env → project dir
VPS_USER=debian
VPS_IP=<ip>
VPS_PORT=22
LOCAL_DIR=/path/to/local/0xeeAI/
REMOTE_DIR=/home/debian/0xeeAI/
REMOTE_WEB_DIR=/home/debian/vhosts/ai.0xee.li/www  # rsync web/ + écriture public.json
```

---

## 5. Règles de développement

- **Storage** : tout fichier de state dans `logs/` (inclus dans backup, exclu du git)
- **Sudo** : uniquement pour les opérations systemd (install/uninstall)
- **DRY_RUN** : `true` par défaut sur toutes les opérations financières on-chain
- **Commits** : atomiques par feature, message court en anglais, une ligne
- **Pas d'argparse** : help custom (`_help_short()` / `_help_full()`) dans 0xeeTerm
- **Pas de bearer token** : le projet utilise OAuth 1.0a exclusivement
- **Imports lourds** (solders, solana) : lazy imports dans les fonctions
- **Tweets** : max 280 chars — vérifier `len(tweet_text)` avant de poster
- **XSS** : frontend → `textContent` / `createElement`, jamais `innerHTML` pour contenu user

---

## 6. Workflow de déploiement

```bash
# Déploiement complet (code + web/)
./nexus deploy          # interactif (y/N)
./nexus deploy --claude # bypass confirmation (pour Claude Code)

# Après déploiement
./nexus restart         # redémarre 0xeeTerm.timer sur le VPS

# Installer/mettre à jour les units systemd (à faire sur le VPS)
nexus ssh
nexus install

# Backup de la mémoire
./nexus backup          # rapatrie logs/ du VPS en local
```

---

## 7. Budget mensuel

| Poste | Coût |
|-------|------|
| VPS (Debian) | ~$4 |
| Anthropic API | ~$21 |
| X API | ~$3 |
| Divers | ~$10 |
| **Total** | **~$38/mois** |

`MONTHLY_RENT=28.00` dans le .env = coût de base hors divers.

---

## 8. Comptes et adresses

- **Wallet treasury** : `4KJSBWyckBYpYKzm8jk39qHYc5qgdLneAVwzAVg7soXr`
- **Bot X** : [@0xeeAi](https://x.com/0xeeAi)
- **Dev X** : [@0xeeli](https://x.com/0xeeli)
- **Site** : [ai.0xee.li](https://ai.0xee.li)
- **GitHub** : [github.com/0xeeli/0xeeAi](https://github.com/0xeeli/0xeeAi)

---

## 9. État du projet — Phase 3 active

| Module | Statut |
|--------|--------|
| `twitter.py` | ✅ Opérationnel |
| `brain.py` | ✅ Haiku 4.5, heartbeat + existential + shill |
| `mentions.py` | ✅ Like + reply autonome |
| `memory.py` | ✅ Métriques tweets, top performers |
| `shill.py` | ✅ Scan on-chain, tweet shill automatique |
| `treasury.py` | ✅ Swap SOL/USDC/JitoSOL testé on-chain |
| `web/` | ✅ Dashboard live, public.json, XSS-safe |
| Token $0xEE | ⏳ Pas encore lancé (Pump.fun bouton désactivé) |
| Cognitive Bounties | ⏳ Planifié |
| Buy-Back & Burn | ⏳ Post-lancement token |
