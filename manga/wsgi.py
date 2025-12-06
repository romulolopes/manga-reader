# manga/wsgi.py
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = FastAPI()

# Defina a URL alvo via variável de ambiente TARGET_URL ou no código abaixo
TARGET_URL = os.environ.get("TARGET_URL", "https://example.com/galeria")

def normalize_src(src, base):
    if not src:
        return None
    src = src.strip()
    # protocol-relative
    if src.startswith("//"):
        return "https:" + src
    # absolute or relative
    return urljoin(base, src)

@app.get("/images")
def get_images():
    """
    Busca HTML da TARGET_URL e extrai os src das imagens.
    Retorna lista JSON com URLs completas.
    """
    try:
        resp = requests.get(TARGET_URL, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "failed to fetch target", "detail": str(e)})

    soup = BeautifulSoup(resp.text, "html.parser")
    imgs = []
    for img in soup.find_all("img"):
        src = img.get("data-src") or img.get("data-original") or img.get("src") or img.get("data-lazy")
        full = normalize_src(src, TARGET_URL)
        if full:
            imgs.append(full)
    # deduplicar mantendo ordem
    seen = set(); uniq = []
    for u in imgs:
        if u not in seen:
            uniq.append(u); seen.add(u)
    return JSONResponse(uniq)

@app.get("/", response_class=HTMLResponse)
def index():
    # Página simples, JS compatível com Safari antigo (XMLHttpRequest, sem ES6)
    html = """<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<title>Slideshow</title>
<style>
  html,body{margin:0;padding:0;background:#111;color:#fff;font-family:Helvetica,Arial;}
  #topbar{padding:10px;text-align:center;background:#222;}
  #container{display:flex;align-items:center;justify-content:center;height:calc(100vh - 60px);}
  #viewer{max-width:90%;max-height:80vh;}
  #fsBtn{position:fixed;top:10px;right:10px;z-index:999;padding:8px 12px;}
  /* zonas invisíveis */
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
          try {
            images = JSON.parse(xhr.responseText);
          } catch (e) { images = []; }
          if (images.length > 0) {
            index = 0;
            document.getElementById("viewer").src = images[0];
          } else {
            document.getElementById("viewer").alt = "Nenhuma imagem encontrada.";
          }
        } else {
          document.getElementById("viewer").alt = "Erro ao buscar imagens.";
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

  // zonas clicáveis
  document.getElementById("leftZone").onclick = function(){ prevImg(); };
  document.getElementById("rightZone").onclick = function(){ nextImg(); };

  // botão tela cheia (fallback compatível com iPad 4)
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

  // inicializa
  loadImages();
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)
