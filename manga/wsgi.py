import os
import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from urllib.parse import urlparse
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
HTML_PATH = BASE_DIR / "templates" / "index.html"


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(HTML_PATH.read_text(encoding="utf-8"))


@app.get("/fetch", response_class=PlainTextResponse)
def fetch(url: str):

    # Fake browser headers (sem isso o site bloqueia)
    headers = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/120.0 Safari/537.36",
        "Referer": f"{urlparse(url).scheme}://{urlparse(url).hostname}/"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return PlainTextResponse(r.text)
    except Exception as e:
        return PlainTextResponse(f"ERROR: {e}", status_code=500)
