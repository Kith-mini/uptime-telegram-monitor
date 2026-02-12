#!/usr/bin/env python3

import os
import time
import argparse
from datetime import datetime
from collections import deque

from dotenv import load_dotenv

from checker import check_website
from telegram import send_telegram_message

load_dotenv()

URLS_RAW = os.getenv("URLS", "https://github.com").strip()
URLS = [u.strip() for u in URLS_RAW.split(",") if u.strip()]

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
TIMEOUT = int(os.getenv("TIMEOUT", "10"))

SLOW_THRESHOLD = float(os.getenv("SLOW_THRESHOLD", "2.5"))
HISTORY_SIZE = int(os.getenv("HISTORY_SIZE", "5"))

# slow alert cooldown (seconds)
SLOW_COOLDOWN = int(os.getenv("SLOW_COOLDOWN", "600"))  # 10 min

STATE = {}   # per-url state
HISTORY = {} # per-url deque history


def ensure_logs_dir():
    os.makedirs("logs", exist_ok=True)


def log(line: str):
    ensure_logs_dir()
    with open("logs/uptime.log", "a") as f:
        f.write(line + "\n")
    print(line)


def fmt_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    mins = seconds // 60
    if mins < 60:
        return f"{mins}m"
    hrs = mins // 60
    rem_m = mins % 60
    return f"{hrs}h {rem_m}m"


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def status_emoji(status: str) -> str:
    return "🟢" if status == "UP" else "🔴"


def build_down_message(url: str, result: dict) -> str:
    code = result.get("code")
    err = result.get("error")
    extra = f"Code: {code}"
    if err:
        extra += f"\nError: {err}"

    return (
        f"❌ DOWN\n"
        f"{url}\n"
        f"{extra}\n"
        f"🕒 {result.get('timestamp', now_ts())}"
    )


def build_up_message(url: str, result: dict, downtime_s: int) -> str:
    rt = result.get("time")
    rt_text = f"{rt}s" if rt is not None else "N/A"
    return (
        f"✅ RECOVERED\n"
        f"{url}\n"
        f"⏱ Response: {rt_text}\n"
        f"📉 Downtime: {fmt_duration(downtime_s)}\n"
        f"🕒 {result.get('timestamp', now_ts())}"
    )


def build_slow_message(url: str, result: dict) -> str:
    rt = result.get("time")
    return (
        f"⚠️ SLOW\n"
        f"{url}\n"
        f"⏱ Response: {rt}s (threshold {SLOW_THRESHOLD}s)\n"
        f"🕒 {result.get('timestamp', now_ts())}"
    )


def add_history(url: str, status: str):
    if url not in HISTORY:
        HISTORY[url] = deque(maxlen=HISTORY_SIZE)
    HISTORY[url].appendleft(f"{now_ts()} {status_emoji(status)} {status}")


def send_history_if_needed(url: str):
    # Optional: you can send history on status change
    # Keep it simple: just log it to file
    hist = HISTORY.get(url, [])
    if hist:
        log(f"[HISTORY] {url} :: " + " | ".join(hist))


def handle_result(url: str, result: dict, allow_telegram: bool = True):
    status = result.get("status", "DOWN")
    add_history(url, status)

    prev = STATE.get(url, {}).get("status")
    last_slow_sent = STATE.get(url, {}).get("last_slow_sent", 0)
    down_since = STATE.get(url, {}).get("down_since", None)

    # Log line
    rt = result.get("time")
    code = result.get("code")
    log_line = f"{result.get('timestamp', now_ts())} | {url} | {status} | {rt} | {code}"
    log(log_line)

    # First time init
    if prev is None:
        STATE[url] = {"status": status, "last_slow_sent": 0, "down_since": None}
        if allow_telegram:
            send_telegram_message(f"🚀 Uptime Monitor Started\nMonitoring: {url}")
        return

    # Status change: UP <-> DOWN
    if prev != status:
        if status == "DOWN":
            # mark down start
            STATE[url]["down_since"] = int(time.time())
            if allow_telegram:
                send_telegram_message(build_down_message(url, result))
        else:
            # recovered
            start_down = STATE[url].get("down_since")
            downtime_s = 0
            if start_down:
                downtime_s = int(time.time()) - start_down
            STATE[url]["down_since"] = None
            if allow_telegram:
                send_telegram_message(build_up_message(url, result, downtime_s))

        # update state status
        STATE[url]["status"] = status
        send_history_if_needed(url)
        return

    # Same status (UP): check slow alert with cooldown
    if status == "UP":
        rt = result.get("time")
        if rt is not None and rt >= SLOW_THRESHOLD:
            now = int(time.time())
            if now - int(last_slow_sent) >= SLOW_COOLDOWN:
                STATE[url]["last_slow_sent"] = now
                if allow_telegram:
                    send_telegram_message(build_slow_message(url, result))


def check_once(allow_telegram: bool = False) -> int:
    # returns exit code: 0 ok, 1 if any DOWN
    any_down = False
    for url in URLS:
        result = check_website(url, timeout=TIMEOUT)
        handle_result(url, result, allow_telegram=allow_telegram)
        if result.get("status") != "UP":
            any_down = True
    return 1 if any_down else 0


def run_forever():
    log("=== Uptime Monitor loop started ===")
    while True:
        for url in URLS:
            result = check_website(url, timeout=TIMEOUT)
            handle_result(url, result, allow_telegram=True)
        time.sleep(CHECK_INTERVAL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Run one check and exit (no Telegram).")
    args = parser.parse_args()

    if not URLS:
        print("No URLS found. Set URLS in .env (comma-separated).")
        raise SystemExit(2)

    if args.check:
        # ✅ IMPORTANT: CI mode = no Telegram (no secrets)
        raise SystemExit(check_once(allow_telegram=False))

    run_forever()


if __name__ == "__main__":
    main()
