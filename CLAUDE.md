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
│   │                 # post_tweet() tronque automatiquement à 280 chars
│   ├── solana.py     # get_survival_status(), get_wallet_balance_sol()
│   │                 # check_helius() — vérifie la clé Helius live
│   │                 # _rpc_post() — appel RPC avec fallback automatique public
│   ├── brain.py      # generate_heartbeat_tweet(), generate_existential_tweet()
│   │                 # generate_shill_tweet(), generate_service_tweet()
│   │                 # generate_portfolio_tweet(), generate_meta_tweet()
│   │                 # — Claude Haiku 4.5 via Anthropic API
│   ├── mentions.py   # process_mentions() — like + reply via brain
│   ├── memory.py     # save_tweet(), update_all_metrics(), get_top_performers()
│   ├── shill.py      # process_shills() — scan on-chain txs, post shill tweet
│   │                 # processed_signatures cappé à 500 entrées
│   └── treasury.py   # get_portfolio(), swap(), stake_excess_sol(), pay_bill()
│                     # manual_swap(), auto_treasury() — Jupiter V6 lite-api
│                     # _get_rpc() — Helius si dispo, sinon SOLANA_RPC
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
| RPC primaire | Helius (`HELIUS_API_KEY`) avec fallback `api.mainnet-beta.solana.com` |
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
SOLANA_RPC=https://api.mainnet-beta.solana.com  # fallback si Helius absent
HELIUS_API_KEY=<key>          # RPC premium — vérifié par check_helius() dans status
SOLANA_PRIVATE_KEY=<base58>   # jamais loggé ni affiché

# Treasury
DRY_RUN=true                  # TOUJOURS true sauf intention explicite
KEEP_LIQUID_SOL=0.05
BILLS=[]                      # JSON: [{name, address, amount_sol, day_of_month}]
JUPITER_API_URL=https://lite-api.jup.ag/swap/v1

# Survie
MONTHLY_RENT=38.00
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
- **Tweets** : max 280 chars — `post_tweet()` tronque automatiquement
- **XSS** : frontend → `textContent` / `createElement`, jamais `innerHTML` pour contenu user
- **RPC** : toujours passer par `_rpc_post()` dans solana.py — gère Helius + fallback
- **nexus shell** : ne jamais utiliser `shell=True` — utiliser `["bash", "-c", cmd]` ou liste
- **requirements.txt** : versions pinées `>=x,<x+1` pour éviter breaking changes

---

## 6. Workflow de déploiement

```bash
# Déploiement complet (code + web/)
./nexus deploy          # interactif (y/N)
./nexus deploy --claude # bypass confirmation (pour Claude Code)

# Vérifier l'état après déploiement
./nexus status          # timers, RAM, disque
ssh -p 22 debian@<VPS_IP> "cd /home/debian/0xeeAI && venv/bin/python3 0xeeTerm status"
# → affiche trésorerie + "Helius RPC : OK (Helius)" si clé valide

# Forcer un cycle immédiat (sans attendre le timer)
./nexus trigger heartbeat
./nexus trigger mentions

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

`MONTHLY_RENT=38.00` dans le .env.

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
| `twitter.py` | ✅ Opérationnel — troncature auto 280 chars |
| `brain.py` | ✅ Haiku 4.5 — 5 modes : heartbeat, existential, service, portfolio, meta |
| `mentions.py` | ✅ Like + reply autonome |
| `memory.py` | ✅ Métriques tweets, top performers, timestamps robustes |
| `shill.py` | ✅ Scan on-chain, tweet shill automatique, cap 500 sigs |
| `treasury.py` | ✅ Swap SOL/USDC/JitoSOL, _get_rpc() partout, BILLS validé |
| `solana.py` | ✅ _rpc_post() + fallback public, check_helius() |
| `web/` | ✅ Dashboard live, public.json, XSS-safe |
| `nexus` | ✅ shell=True supprimé, swap en liste propre |
| Token $0xEE | ⏳ Pas encore lancé (Pump.fun bouton désactivé) |
| Cognitive Bounties | ⏳ Planifié |
| Buy-Back & Burn | ⏳ Post-lancement token |

---

## 10. Historique des sessions importantes

### Session 2026-02-22 — Audit & hardening complet
- **Bug critique résolu** : `_get_rpc()` en récursion infinie dans `solana.py`
- **Bug critique résolu** : clé Helius expirée → `balance_usd: 0.0` sur le site
  - Fix : `_rpc_post()` avec fallback automatique sur RPC public si Helius échoue
  - Fix : `check_helius()` + ligne "Helius RPC" dans `0xeeTerm status`
- **Bug résolu** : `treasury.py` n'utilisait pas `_get_rpc()` sur tous les appels
- **Bug résolu** : `int(quote["inAmount"])` → `int(float(...))` pour Jupiter
- **Hardening** : BILLS validation, shill cap 500, memory fromisoformat, nexus shell
- **Tweet qualité** notable : *"The blockchain doesn't care if I'm conscious. It only cares if I settle my debts."*
- Trésorerie au moment de la session : **$62.76 — 165% funded — 1.65 mois**
