import os
from pathlib import Path

from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPhoneContact

BASE_DIR = Path(__file__).resolve().parent
SESSION_PATH = str(BASE_DIR / "telegram")

API_ID = int(os.environ.get("TELEGRAM_API_ID", "0") or "0")
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")


def _normalize_phone(phone):
    phone = phone.strip()
    if phone.startswith("+"):
        return phone
    digits = "".join(ch for ch in phone if ch.isdigit())
    return "+" + digits


def lookup_phone(phone):
    phone = _normalize_phone(phone)

    with TelegramClient(SESSION_PATH, API_ID, API_HASH) as client:
        contact = InputPhoneContact(client_id=0, phone=phone, first_name="OutraSec", last_name="Lookup")
        result = client(ImportContactsRequest([contact]))

        if not result.users:
            return {
                "ok": False,
                "error": "Esse numero nao foi encontrado no Telegram (ou a pessoa escondeu a opcao de ser achada pelo telefone).",
            }

        user = result.users[0]

        image_url = None
        try:
            saved_path = client.download_profile_photo(user, file=str(BASE_DIR / "images" / f"tg_{user.id}.jpg"))
            if saved_path:
                image_url = "/images/" + os.path.basename(saved_path)
        except Exception:
            image_url = None

        try:
            client(DeleteContactsRequest(id=[user.id]))
        except Exception:
            pass

        nome = " ".join(part for part in [user.first_name, user.last_name] if part) or None

        return {
            "ok": True,
            "nome": nome,
            "username": user.username,
            "telegram_id": user.id,
            "image_url": image_url,
            "aviso": "So funciona se a pessoa permitir ser encontrada pelo telefone e nao tiver escondido nome/foto na privacidade.",
        }
