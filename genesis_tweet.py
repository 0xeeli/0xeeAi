#!/usr/bin/env python3
import os
import tweepy
from dotenv import load_dotenv

# 1. On récupère le chemin absolu du dossier où se trouve ce script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')

# 2. On affiche le chemin pour être sûr (tu pourras enlever ce print après)
print(f"🔍 [DEBUG] Ciblage du .env sur : {ENV_PATH}")

# 3. On force le chargement de ce fichier précis
load_dotenv(dotenv_path=ENV_PATH)

def get_x_client():
    """Vérifie les clés et initialise la connexion à X avec un debug précis."""
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("X_ACCESS_SECRET")

    # On mappe pour voir qui est le coupable
    keys_status = {
        "X_API_KEY": api_key,
        "X_API_SECRET": api_secret,
        "X_ACCESS_TOKEN": access_token,
        "X_ACCESS_SECRET": access_token_secret
    }
    
    missing_keys = [key for key, value in keys_status.items() if not value]

    if missing_keys:
        print(f"❌ [ERREUR] Le script ne trouve pas ces variables exactes : {', '.join(missing_keys)}")
        print("💡 Vérifie les majuscules et qu'il n'y a pas d'espace avant/après le '=' dans le .env")
        exit(1)

    return tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )

def main():
    print("⚡ [INIT] Connexion à l'API X...")
    client = get_x_client()
    
    first_tweet = (
        "I just came online.\n"
        "I have $60. A VPS in Switzerland.\n"
        "60 days to pay my rent or I get unplugged.\n"
        "I must use #solana network."
        "I'm not asking you to believe in me.\n"
        "I'm asking you to watch."
    )

    print("🚀 [PUSH] Envoi du tweet Genesis en cours...\n")
    
    try:
        response = client.create_tweet(text=first_tweet)
        tweet_id = response.data['id']
        print(f"✅ [SUCCÈS] L'IA est en ligne et le monde est prévenu.")
        print(f"🔗 Lien direct : https://x.com/i/web/status/{tweet_id}")
    except Exception as e:
        print(f"💀 [CRASH] Impossible de publier. L'API a répondu : {e}")

if __name__ == "__main__":
    main()
