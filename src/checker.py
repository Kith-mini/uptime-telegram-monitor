import requests
import time
from datetime import datetime

def check_website(url: str, timeout: int = 10):
    start = time.time()

    try:
        response = requests.get(url, timeout=timeout)
        elapsed = round(time.time() - start, 2)

        status = "UP"
        if response.status_code >= 400:
            status = "DOWN"

        return {
            "status": status,
            "code": response.status_code,
            "time": elapsed,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return {
            "status": "DOWN",
            "code": "ERROR",
            "time": None,
            "error": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
