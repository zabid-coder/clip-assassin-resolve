"""Source launcher: wait for the backend before opening the browser."""
import json
import threading
import time
import urllib.request
import webbrowser
import uvicorn
from config import config


def main():
    url = f"http://127.0.0.1:{config.API_PORT}"
    def open_when_ready():
        for _ in range(100):
            try:
                with urllib.request.urlopen(url + "/api/health", timeout=1) as response:
                    if json.load(response).get("success"):
                        webbrowser.open(url)
                        return
            except (OSError, ValueError):
                time.sleep(.2)
    threading.Thread(target=open_when_ready, daemon=True).start()
    uvicorn.run("server:app", host=config.API_HOST, port=config.API_PORT)


if __name__ == "__main__":
    main()
