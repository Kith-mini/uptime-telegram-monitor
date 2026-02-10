from dotenv import load_dotenv
load_dotenv()

import time
from checker import check_website
from telegram import send_telegram_message

URLS = [
    "https://github.com",
    "https://google.com",
    "https://nonexist-test-12345.com"
]

CHECK_INTERVAL = 30
SLOW_THRESHOLD = 2.5

last_state = {}

def log(text):
    with open("logs/uptime.log", "a") as f:
        f.write(text + "\n")

def handle_result(url, result):
    prev = last_state.get(url)
    current = result["status"]

    message = None

    if prev is None:
        message = f"🟢 Monitoring started for {url}"

    elif prev != current:
        if current == "UP":
            message = f"✅ RECOVERED: {url}"
        else:
            message = f"🚨 DOWN: {url}"

    elif current == "UP" and result["time"] > SLOW_THRESHOLD:
        message = f"🐢 SLOW: {url}\nResponse: {result['time']}s"

    last_state[url] = current

    log_line = f"{result['timestamp']} | {url} | {current} | {result.get('time')}"
    log(log_line)

    if message:
        send_telegram_message(message)

def run():
    while True:
        for url in URLS:
            result = check_website(url)
            handle_result(url, result)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run()
