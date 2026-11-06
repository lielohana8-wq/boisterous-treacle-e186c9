/* GitHub sign-in for the admin pages (replaces Netlify Identity).
   Uses the same Netlify OAuth popup as Decap CMS and the same localStorage key, so signing in
   on any admin page also signs you in to the editor, and the other way round. */
(function () {
  var KEY = 'decap-cms-user';
  var REPO = 'lielohana8-wq/boisterous-treacle-e186c9';

  function stored() {
    try { var u = JSON.parse(localStorage.getItem(KEY) || 'null'); return u && u.token ? u : null; } catch (e) { return null; }
  }
  function save(u) { try { localStorage.setItem(KEY, JSON.stringify(u)); } catch (e) {} }

  function gh(path, token) {
    return fetch('https://api.github.com' + path, { headers: { authorization: 'token ' + token, accept: 'application/vnd.github+json' } })
      .then(function (r) { if (!r.ok) throw new Error('GitHub ' + r.status); return r.json(); });
  }

  // Resolves to the signed-in user if the token is still valid and can write to the repo, else null.
  function check() {
    var u = stored();
    if (!u) return Promise.resolve(null);
    return gh('/repos/' + REPO, u.token).then(function (repo) {
      if (!repo.permissions || !repo.permissions.push) throw new Error('no access');
      return u;
    }).catch(function () { logout(); return null; });
  }

  function popup() {
    return new Promise(function (resolve, reject) {
      var url = 'https://api.netlify.com/auth?provider=github&site_id=' + encodeURIComponent(location.hostname) + '&scope=repo';
      var w = 600, h = 680, left = screen.width / 2 - w / 2, top = screen.height / 2 - h / 2;
      var win = window.open(url, 'Netlify Authorization', 'width=' + w + ',height=' + h + ',top=' + top + ',left=' + left);
      if (!win) { reject(new Error('The sign-in window was blocked. Allow pop-ups for this site and try again.')); return; }
      function onMsg(e) {
        if (e.origin !== 'https://api.netlify.com' || typeof e.data !== 'string') return;
        if (e.data === 'authorizing:github') { win.postMessage(e.data, e.origin); return; }
        var m = e.data.match(/^authorization:github:(success|error):(.*)$/);
        if (!m) return;
        window.removeEventListener('message', onMsg);
        clearInterval(t);
        try { win.close(); } catch (x) {}
        var data = {}; try { data = JSON.parse(m[2]); } catch (x) {}
        if (m[1] === 'success' && data.token) resolve(data.token);
        else reject(new Error(data.message || data.error || 'Sign-in failed'));
      }
      window.addEventListener('message', onMsg);
      var t = setInterval(function () { if (win.closed) { clearInterval(t); window.removeEventListener('message', onMsg); reject(new Error('cancelled')); } }, 700);
    });
  }

  function login() {
    return popup().then(function (token) {
      return gh('/user', token).then(function (me) {
        var u = { token: token, backendName: 'github', login: me.login, name: me.name || me.login, avatar_url: me.avatar_url };
        save(u);
        return check().then(function (ok) {
          if (!ok) throw new Error('The GitHub account “' + me.login + '” has no write access to ' + REPO + '.');
          return ok;
        });
      });
    });
  }

  function logout() { try { localStorage.removeItem(KEY); } catch (e) {} }

  window.NMAuth = { check: check, login: login, logout: logout, token: function () { var u = stored(); return u && u.token; } };
})();
