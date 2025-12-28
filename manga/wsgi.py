# manga/wsgi.py

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
import cloudscraper
import hashlib
import json
import secrets

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
USERS_PATH = BASE_DIR / "users.json"


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_users() -> dict:
    if not USERS_PATH.exists():
        return {}
    try:
        return json.loads(USERS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_users(data: dict):
    USERS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


class UserIn(BaseModel):
    username: str
    password: str


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
        return PlainTextResponse(html)
    except Exception as e:
        return PlainTextResponse(f"ERROR: {e}", status_code=500)


@app.post("/create")
def create(user: UserIn):
    if not user.username or not user.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username and password required")

    users = load_users()
    if user.username in users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists")

    users[user.username] = {
        "password": _hash_password(user.password),
        "token": None
    }
    save_users(users)
    return JSONResponse({"ok": True, "msg": "user created"})


@app.post("/login")
def login(user: UserIn):
    users = load_users()
    if user.username not in users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    stored = users[user.username]
    if stored.get("password") != _hash_password(user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    token = secrets.token_hex(16)
    users[user.username]["token"] = token
    save_users(users)

    return JSONResponse({"ok": True, "token": token})


@app.get("/me")
def me(token: str = ""):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing token")
    users = load_users()
    for username, data in users.items():
        if data.get("token") == token:
            return {"username": username}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")