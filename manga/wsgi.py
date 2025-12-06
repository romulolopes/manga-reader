# manga/wsgi.py

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from pathlib import Path
import requests
from urllib.parse import urlparse

app = FastAPI()

# Carrega o index.html da MESMA pasta
BASE_DIR = Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / "index.html"


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(HTML_PATH.read_text(encoding="utf-8"))


@app.get("/fetch", response_class=PlainTextResponse)
def fetch(url: str):

    headers = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36",
        "Referer": f"{urlparse(url).scheme}://{urlparse(url).hostname}/"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        return PlainTextResponse(r.text)
    except Exception as e:
        return PlainTextResponse(f"ERROR: {e}", status_code=500)
