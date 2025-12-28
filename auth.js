<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>

<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">

<title>Leitor de Imagens</title>

<style>
  html,body {
    margin:0; padding:0; background:#111; color:white;
    font-family:Helvetica,Arial;
    height:100%; overflow:hidden;
  }

  /* MENU CONFIG */
  #configMenu {
    position:fixed; top:0; left:0; width:100%; height:100%;
    background:#000d; display:flex; flex-direction:column;
    justify-content:center; align-items:center; z-index:999;
    backdrop-filter: blur(3px);
  }
  #configMenu input {
    margin:8px 0; padding:8px; width:80%; font-size:18px;
  }
  
  /* Container para os botões do menu */
  .menu-actions {
    display: flex;
    gap: 15px;
    margin-top: 15px;
  }

  #startBtn, #cancelBtn {
    padding:10px 18px; font-size:18px; 
    border: none; cursor: pointer; color: white;
    border-radius: 4px;
  }

  #startBtn { background: #007bff; } /* Azul */
  #cancelBtn { background: #555; }   /* Cinza */

  /* Botão reabrir menu (canto inferior) */
  #menuBtn {
    position:fixed; left:10px; bottom:10px;
    padding:10px 14px; background:#444; 
    color:white; cursor:pointer; z-index:1000;
    border-radius:8px; border:none;
  }

  #container {
    display:flex; align-items:center; justify-content:center;
    height:100vh; position:relative;
    display:none;
  }

  #viewer {
    max-width:90%;
    max-height:80vh;
  }

  .zone {
    position:absolute; top:0; height:100%; width:40%; cursor:pointer;
  }
  #leftZone { left:0; }
  #rightZone { right:0; }

  #fsBtn {
    position:fixed; top:10px; right:10px; z-index:1000;
    padding:6px 10px; background:#333; color:white; display:none; border:none; border-radius:4px;
  }
</style>
</head>
<body>

<div id="configMenu">
  <h2>Configuração</h2>

  <input id="baseUrl" type="text" placeholder="URL base" value="https://mugiwarasoficial.com/manga/manga-one-piece/">
  <input id="chapterNum" type="number" placeholder="Capítulo" value="1168">

  <div class="menu-actions">
      <button id="startBtn">Carregar / Iniciar</button>
      <button id="cancelBtn">Cancelar</button>
  </div>

  <p id="saveStatus" style="font-size:12px; color:#aaa; margin-top:15px;"></p>
</div>

<input id="urlBox" type="text" style="display:none">

<button id="fsBtn">Tela cheia</button>
<button id="menuBtn">Configuração</button>

<div id="container">
  <img id="viewer" src="" alt="Aguardando…" />
  <div id="leftZone" class="zone"></div>
  <div id="rightZone" class="zone"></div>
</div>


<script>
var images = [];
var index = 0;
var fullscreen = false;
var pendingPageIndex = 0; 

/* ------------------------------
      VERIFICAÇÃO DE LOGIN
--------------------------------*/
function verificarLogin() {
    var token = localStorage.getItem("token") || 
                localStorage.getItem("access_token") || 
                localStorage.getItem("user");
    return (token !== null && token !== "");
}

/* ------------------------------
      PERSISTÊNCIA DE DADOS
--------------------------------*/
function saveState() {
    //if (!verificarLogin()) return;

    var b = document.getElementById("baseUrl").value;
    var c = document.getElementById("chapterNum").value;
    
    localStorage.setItem("manga_baseUrl", b);
    localStorage.setItem("manga_chapterNum", c);
    localStorage.setItem("manga_pageIndex", index);
}

function loadState() {
    //if (!verificarLogin()) {
    //    document.getElementById("saveStatus").innerText = "Login necessário para salvar progresso.";
    //    return;
    //}

    document.getElementById("saveStatus").innerText = "Progresso sincronizado.";

    var savedBase = localStorage.getItem("manga_baseUrl");
    var savedChap = localStorage.getItem("manga_chapterNum");
    var savedPage = localStorage.getItem("manga_pageIndex");

    if (savedBase) document.getElementById("baseUrl").value = savedBase;
    if (savedChap) document.getElementById("chapterNum").value = savedChap;
    
    if (savedPage) pendingPageIndex = parseInt(savedPage, 10);
}

window.addEventListener('DOMContentLoaded', (event) => {
    loadState();
});

/* ------------------------------
      FUNÇÃO DE EXTRAÇÃO
--------------------------------*/
function extractImagesFromHTML(html, baseURL) {
  var tmp = document.createElement("div");
  tmp.innerHTML = html;
  var list = tmp.querySelectorAll("img.wp-manga-chapter-img");
  var arr = [];
  var base = document.createElement("a");
  base.href = baseURL;

  for (var i = 0; i < list.length; i++) {
    var src = list[i].getAttribute("data-src") || list[i].getAttribute("src");
    if (!src) continue;
    src = src.trim();
    if (src.startsWith("http")) { arr.push(src); continue; }
    if (src.startsWith("//")) { arr.push("https:" + src); continue; }
    if (src.startsWith("/")) { arr.push(base.protocol + "//" + base.host + src); continue; }
    arr.push(base.protocol + "//" + base.host + "/" + src);
  }
  return arr;
}

/* ------------------------------
          CARREGAR
--------------------------------*/
function loadChapter() {
  var url = document.getElementById("urlBox").value;
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "/fetch?url=" + encodeURIComponent(url), true);

  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4) {
      if (xhr.status >= 200 && xhr.status < 300) {
        var html = xhr.responseText;
        images = extractImagesFromHTML(html, url);

        if (images.length > 0) {
          if (pendingPageIndex > 0 && pendingPageIndex < images.length) {
              index = pendingPageIndex;
              pendingPageIndex = 0; 
          } else {
              index = 0;
          }
          document.getElementById("viewer").src = images[index];
          
          saveState(); 

        } else {
          document.getElementById("viewer").alt = "Nenhuma imagem encontrada.";
        }
      } else {
        document.getElementById("viewer").alt = "Erro ao carregar.";
      }
    }
  };
  xhr.send();
}

/* Navegação */
function showIndex(i) {
  if (!images.length) return;
  index = (i + images.length) % images.length;
  document.getElementById("viewer").src = images[index];
  saveState();
}

function nextImg() {
  if (!images.length) return;
  if (index < images.length - 1) {
    showIndex(index + 1);
    return;
  }

  // Próximo Capítulo
  let chapterInput = document.getElementById("chapterNum");
  let current = parseInt(chapterInput.value, 10) || 0;
  chapterInput.value = current + 1;

  let b = document.getElementById("baseUrl").value.trim();
  if (!b.endsWith("/")) b += "/";
  let finalURL = b + "capitulo-" + chapterInput.value;

  document.getElementById("urlBox").value = finalURL;
  
  pendingPageIndex = 0;
  index = 0; 
  saveState();
  loadChapter();
}

function prevImg() { showIndex(index - 1); }

document.getElementById("leftZone").onclick = prevImg;
document.getElementById("rightZone").onclick = nextImg;

/* Fullscreen */
document.getElementById("fsBtn").onclick = function() {
  var v = document.getElementById("viewer");
  if (!fullscreen) {
    fullscreen = true;
    this.innerHTML = "Sair";
    v.style.maxWidth = "100%";
    v.style.maxHeight = "100vh";
    document.body.style.background = "#fff";
    document.getElementById("container").style.background = "#fff";
  } else {
    fullscreen = false;
    this.innerHTML = "Tela cheia";
    v.style.maxWidth = "90%";
    v.style.maxHeight = "80vh";
    document.body.style.background = "#111";
    document.getElementById("container").style.background = "#111";
  }
};

/* -----------------------------------------
   BOTÕES DO MENU
------------------------------------------*/

// 1. INICIAR / CARREGAR
document.getElementById("startBtn").onclick = function() {
  let b = document.getElementById("baseUrl").value.trim();
  let c = document.getElementById("chapterNum").value.trim();
  if (!b.endsWith("/")) b += "/";
  let finalURL = b +'capitulo-'+ c ;

  document.getElementById("urlBox").value = finalURL;
  document.getElementById("configMenu").style.display = "none";
  document.getElementById("container").style.display = "flex";
  document.getElementById("fsBtn").style.display = "block";

  saveState();
  loadChapter();
};

// 2. CANCELAR / FECHAR (Novo)
document.getElementById("cancelBtn").onclick = function() {
  // Apenas esconde o menu, mantendo o estado atual do leitor
  document.getElementById("configMenu").style.display = "none";
  
  // Se já houver imagens carregadas, mostra o container
  if (images.length > 0) {
      document.getElementById("container").style.display = "flex";
      document.getElementById("fsBtn").style.display = "block";
  }
};

document.getElementById("menuBtn").onclick = function () {
  document.getElementById("configMenu").style.display = "flex";
};
</script>

<link rel="stylesheet" href="auth.css">
<script src="auth.js"></script>

</body>
</html>