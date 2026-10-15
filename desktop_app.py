import os
import sys
import threading
import time
import uvicorn
import webview

# Import FastAPI app from server.py
from server import app
from config import config
import urllib.request

def start_backend_server():
    """Runs the FastAPI uvicorn server on localhost."""
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT, log_level="error")

def main():
    # 1. Start FastAPI server in a daemon background thread
    server_thread = threading.Thread(target=start_backend_server, daemon=True)
    server_thread.start()

    # Wait 1 second for the local server to start
    for _ in range(100):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{config.API_PORT}/api/health", timeout=1):
                break
        except OSError:
            time.sleep(.2)
    else:
        raise RuntimeError("Clip Assassin backend did not start. Check whether its port is already in use.")

    # 2. Create Native GUI Window via pywebview
    window = webview.create_window(
        title="Clip Assassin v2.1.1",
        url=f"http://127.0.0.1:{config.API_PORT}",
        width=1280,
        height=850,
        min_size=(1024, 700),
        resizable=True,
        background_color="#0A0915",
        text_select=True
    )

    # 3. Start Native Webview Loop
    webview.start(private_mode=True)

if __name__ == "__main__":
    main()
