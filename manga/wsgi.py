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
MANGAS_PATH = BASE_DIR / "mangas.json"
LOGIN_PATH = BASE_DIR / "login.html"
AUTH_JS_PATH = BASE_DIR / "auth.js"
AUTH_CSS_PATH = BASE_DIR / "auth.css"


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


def load_mangas() -> dict:
    if not MANGAS_PATH.exists():
        return {}
    try:
        return json.loads(MANGAS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_mangas(data: dict):
    MANGAS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def username_from_token(token: str):
    if not token:
        return None
    users = load_users()
    for username, data in users.items():
        if data.get("token") == token:
            return username
    return None


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


@app.get("/login", response_class=HTMLResponse)
def login_page():
    if LOGIN_PATH.exists():
        return HTMLResponse(LOGIN_PATH.read_text(encoding="utf-8"))
    return HTMLResponse("<html><body><h3>Login page missing</h3></body></html>")


@app.get("/auth.js")
def serve_auth_js():
    if AUTH_JS_PATH.exists():
        return PlainTextResponse(AUTH_JS_PATH.read_text(encoding="utf-8"), media_type="application/javascript")
    return PlainTextResponse("", status_code=404)


@app.get("/auth.css")
def serve_auth_css():
    if AUTH_CSS_PATH.exists():
        return PlainTextResponse(AUTH_CSS_PATH.read_text(encoding="utf-8"), media_type="text/css")
    return PlainTextResponse("", status_code=404)


@app.post("/manga/save")
def save_manga(payload: dict, token: str = ""):
    username = username_from_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")

    name = payload.get('name')
    url = payload.get('url')
    chapter = payload.get('chapter')
    index = payload.get('index')

    if not name or not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name and url required")

    mangas = load_mangas()
    user_list = mangas.get(username, [])

    # replace if exists by name
    found = False
    for m in user_list:
        if m.get('name') == name:
            m.update({'url': url, 'chapter': chapter, 'index': index})
            found = True
            break
    if not found:
        user_list.append({'name': name, 'url': url, 'chapter': chapter, 'index': index})

    mangas[username] = user_list
    save_mangas(mangas)
    return JSONResponse({'ok': True, 'msg': 'saved'})


@app.get("/manga/list")
def list_manga(token: str = ""):
    username = username_from_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    mangas = load_mangas()
    return JSONResponse({'ok': True, 'mangas': mangas.get(username, [])})


@app.get("/manga/get")
def get_manga(name: str, token: str = ""):
    username = username_from_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    mangas = load_mangas()
    for m in mangas.get(username, []):
        if m.get('name') == name:
            return JSONResponse({'ok': True, 'manga': m})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='not found')