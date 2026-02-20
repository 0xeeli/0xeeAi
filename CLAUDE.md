Crée un fichier CLAUDE.md à la racine du projet 0xeeAI.

Ce fichier doit contenir tout ce dont Claude Code a besoin 
pour reprendre le contexte immédiatement sans briefing :

1. Description du projet
2. Architecture complète des fichiers et leur rôle
3. Stack technique (Python, Tweepy, Anthropic, Solana, Jupiter)
4. Variables d'environnement importantes et leur usage
5. Règles de développement :
   - Stockage logs/ pour tout fichier de state
   - Pas de sudo sauf systemd
   - DRY_RUN=true par défaut sur toutes les ops financières
   - Git commits atomiques par feature
   - Tester la syntaxe Python avant commit
6. Workflow de déploiement : nexus deploy → nexus restart
7. Budget mensuel actuel : $38/mois
8. Wallet treasury : Q3akFf57YMEuxNZZwchK8FK2L97LqWcWvVWkoX95Axh
9. Comptes X : @0xeeAi (bot) / @0xeeli (dev)
10. État Phase 3 en cours : memory.py, shill.py, treasury.py

Git commit "docs: add CLAUDE.md for persistent Claude Code context"
