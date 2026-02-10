from dotenv import load_dotenv
load_dotenv()

from telegram import send_telegram_message

send_telegram_message("✅ Test message from my Uptime Monitor project!")
print("Sent!")
