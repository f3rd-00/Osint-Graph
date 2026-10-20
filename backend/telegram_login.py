import os
from pathlib import Path

from telethon.sync import TelegramClient

BASE_DIR = Path(__file__).resolve().parent
SESSION_PATH = str(BASE_DIR / "telegram")

api_id = os.environ.get("TELEGRAM_API_ID") or input("Seu api_id (de my.telegram.org): ").strip()
api_hash = os.environ.get("TELEGRAM_API_HASH") or input("Seu api_hash (de my.telegram.org): ").strip()

with TelegramClient(SESSION_PATH, int(api_id), api_hash) as client:
    me = client.get_me()
    print(f"Conectado como {me.first_name} (@{me.username}).")
    print("Sessao salva em telegram.session — pode fechar esta janela e rodar o app.py normalmente.")
