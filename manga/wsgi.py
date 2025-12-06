# manga/wsgi.py

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from pathlib import Path
import requests
from urllib.parse import urlparse
from fastapi.middleware.cors import CORSMiddleware

import cloudscraper

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Carrega o index.html da MESMA pasta
BASE_DIR = Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / "index.html"


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(HTML_PATH.read_text(encoding="utf-8"))


@app.get("/fetch", response_class=PlainTextResponse)
def fetch(url: str):

    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "android",
            "mobile": True
        }
    )

    try:
        html = scraper.get(url).text
        print(html)
        return PlainTextResponse(html)
    except Exception as e:
        return PlainTextResponse(f"ERROR: {e}", status_code=500)