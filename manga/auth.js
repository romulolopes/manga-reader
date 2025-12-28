// auth.js — cria UI simples para criar conta e login
(function(){
  function qs(sel){return document.querySelector(sel)}

  // Criar modal
  var modal = document.createElement('div');
  modal.id = 'authModal';
  modal.innerHTML = `
    <div class="authBox">
      <h3>Autenticação</h3>
      <input id="authUser" placeholder="usuário" />
      <input id="authPass" type="password" placeholder="senha" />
      <div class="row">
        <button id="createBtn">Criar</button>
        <button id="loginBtn">Entrar</button>
        <button id="closeAuth">Fechar</button>
      </div>
      <div id="authMsg" class="msg"></div>
    </div>
  `;
  document.body.appendChild(modal);

  function showMsg(text, ok){
    var el = qs('#authMsg'); el.textContent = text; el.style.color = ok? 'lime':'#f88';
  }

  function api(path, body){
    return fetch(path, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify(body)
    }).then(r=>r.json());
  }

  qs('#closeAuth').onclick = function(){ modal.style.display='none' };
  qs('#createBtn').onclick = function(){
    var u = qs('#authUser').value.trim();
    var p = qs('#authPass').value;
    if(!u||!p){ showMsg('preencha usuário e senha', false); return }
    api('/create',{username:u,password:p}).then(j=>{
      if(j.ok){ showMsg('criado, faça login', true) } else showMsg(j.detail||j.msg||'erro', false)
    }).catch(e=>showMsg('erro',false))
  };

  qs('#loginBtn').onclick = function(){
    var u = qs('#authUser').value.trim();
    var p = qs('#authPass').value;
    if(!u||!p){ showMsg('preencha usuário e senha', false); return }
    api('/login',{username:u,password:p}).then(j=>{
      if(j.ok && j.token){
        localStorage.setItem('manga_token', j.token);
        showMsg('logado', true);
        setTimeout(()=>modal.style.display='none',800);
      } else showMsg(j.detail||'erro', false)
    }).catch(e=>showMsg('erro',false))
  };

  // Botão fixo para abrir modal
  var openBtn = document.createElement('button');
  openBtn.id = 'authOpenBtn'; openBtn.textContent = 'Login';
  openBtn.onclick = function(){ modal.style.display='flex' };
  document.body.appendChild(openBtn);

})();
