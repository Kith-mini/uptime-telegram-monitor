import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_telegram_message(text: str, disable_preview: bool = True) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        
        print("[telegram] Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID (skipping send).")
        print(text)
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": disable_preview
    }

    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    return True
