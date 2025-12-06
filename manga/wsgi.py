# manga/wsgi.py

import os
import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = FastAPI()

# URL padrão (pode ser alterada pelo Render)
TARGET_URL = os.environ.get(
    "TARGET_URL",
    "https://mugiwarasoficial.com/manga/chainsaw-man/capitulo-222/"
)

# Cabeçalhos obrigatórios para o site de mangá
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122 Safari/537.36",
    "Referer": "https://mugiwarasoficial.com/"
}


def normalize_src(src, base):
    if not src:
        return None
    src = src.strip()

    # //cdn → https://cdn
    if src.startswith("//"):
        return "https:" + src

    # Normalizar relativo/absoluto
    return urljoin(base, src)


@app.get("/images")
def get_images():
    """
    Acessa a página TARGET_URL e extrai TODAS as imagens
    do container wp-manga-current-chap (correto para leitores de mangá).
    """
    try:
        resp = requests.get(TARGET_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "failed to fetch target", "detail": str(e)}
        )

    soup = BeautifulSoup(resp.text, "html.parser")

    # O site sempre usa este container
    container = soup.find(id="wp-manga-current-chap")

    if not container:
        return JSONResponse({"count": 0, "images": []})

    imgs = []
    for img in container.find_all("img"):
        src = (
            img.get("data-src")
            or img.get("data-lazy-src")
            or img.get("data-original")
            or img.get("src")
        )

        full = normalize_src(src, TARGET_URL)
        if full:
            imgs.append(full)

    # Remover duplicados mantendo ordem
    final = []
    seen = set()
    for u in imgs:
        if u not in seen:
            final.append(u)
            seen.add(u)

    return JSONResponse({"count": len(final), "images": final})


@app.get("/", response_class=HTMLResponse)
def index():
    """
    Página compatível com Safari antigo (iPad 4),
    usando apenas ES5 e XMLHttpRequest.
    """
    html = """<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Slideshow</title>
<style>
  html,body{margin:0;padding:0;background:#111;color:#fff;font-family:Helvetica,Arial;}
  #topbar{padding:10px;text-align:center;background:#222;}
  #container{display:flex;align-items:center;justify-content:center;height:calc(100vh - 60px);}
  #viewer{max-width:90%;max-height:80vh;}
  #fsBtn{position:fixed;top:10px;right:10px;z-index:999;padding:8px 12px;}
  .zone{position:absolute;top:0;height:100%;width:40%;cursor:pointer;}
  #leftZone{left:0;}
  #rightZone{right:0;}
</style>
</head>
<body>
  <div id="topbar">
    <strong>Apresentador de Imagens</strong>
    <button id="fsBtn">Tela cheia</button>
  </div>

  <div id="container" style="position:relative;">
    <img id="viewer" src="" alt="slide"/>
    <div id="leftZone" class="zone"></div>
    <div id="rightZone" class="zone"></div>
  </div>

<script type="text/javascript">
  var images = [];
  var index = 0;
  var fullscreen = false;

  function loadImages() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/images", true);
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          var data = {};
          try { data = JSON.parse(xhr.responseText); } catch(e) {}
          images = data.images || [];
          if (images.length > 0) {
            index = 0;
            document.getElementById("viewer").src = images[0];
          } else {
            document.getElementById("viewer").alt = "Nenhuma imagem encontrada.";
          }
        } else {
          document.getElementById("viewer").alt = "Erro.";
        }
      }
    };
    xhr.send();
  }

  function showIndex(i) {
    if (!images || images.length === 0) return;
    index = (i + images.length) % images.length;
    document.getElementById("viewer").src = images[index];
  }

  function nextImg() { showIndex(index + 1); }
  function prevImg() { showIndex(index - 1); }

  document.getElementById("leftZone").onclick = function(){ prevImg(); };
  document.getElementById("rightZone").onclick = function(){ nextImg(); };

  document.getElementById("fsBtn").onclick = function() {
    var body = document.body;
    var viewer = document.getElementById("viewer");
    if (!fullscreen) {
      fullscreen = true;
      this.innerHTML = "Sair";
      body.style.background = "black";
      viewer.style.maxWidth = "100%";
      viewer.style.maxHeight = "100vh";
      viewer.style.width = "100%";
      viewer.style.height = "100vh";
    } else {
      fullscreen = false;
      this.innerHTML = "Tela cheia";
      body.style.background = "";
      viewer.style.maxWidth = "90%";
      viewer.style.maxHeight = "80vh";
      viewer.style.width = "auto";
      viewer.style.height = "auto";
    }
  };

  loadImages();
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)
