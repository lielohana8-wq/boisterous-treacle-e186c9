/* Northmark hero — fireplace doors + gas fire. CSS 3D + 2D canvas flames. No WebGL. */
(function () {
  if (window.__nmHeroInit) return; window.__nmHeroInit = true;
  function init() {
    var root = document.getElementById('nm-fireplace'); if (!root) return;
    var canvas = root.querySelector('canvas'); if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    var dpr = Math.min(1.5, window.devicePixelRatio || 1);
    function size() { var r = canvas.getBoundingClientRect(); canvas.width = Math.max(2, r.width * dpr); canvas.height = Math.max(2, r.height * dpr); }
    size(); addEventListener('resize', size);
    // open doors after the paint
    var v = root.querySelector('video'); var tryPlay = function () { if (!v) return; v.muted = true; v.defaultMuted = true; v.loop = true; v.playsInline = true; v.setAttribute('muted', ''); v.setAttribute('loop', ''); var p = v.play(); if (p && p.catch) p.catch(function () {}); }; tryPlay(); setTimeout(tryPlay, 800);
    var opened = false; function open() { if (opened) return; opened = true; root.classList.add('nm-open'); root.setAttribute('data-open', '1'); tryPlay(); }
    if (reduce) open(); else { var onScroll = function () { if ((window.scrollY || 0) > 24) { open(); removeEventListener('scroll', onScroll); removeEventListener('wheel', onScroll); removeEventListener('touchmove', onScroll); } }; addEventListener('scroll', onScroll, { passive: true }); addEventListener('wheel', onScroll, { passive: true }); addEventListener('touchmove', onScroll, { passive: true }); root.addEventListener('click', open); }
    // flames
    var t0 = performance.now(), running = true, visible = true;
    if ('IntersectionObserver' in window) new IntersectionObserver(function (e) { visible = e[0].isIntersecting; }).observe(root);
    function noise(x, t) { return Math.sin(x * 1.7 + t * 2.1) * 0.5 + Math.sin(x * 3.3 - t * 1.3) * 0.3 + Math.sin(x * 7.1 + t * 3.7) * 0.2; }
    function flame(x, baseY, w, h, t, seed) {
      var g = ctx.createLinearGradient(0, baseY - h, 0, baseY);
      g.addColorStop(0, 'rgba(255,190,80,0)'); g.addColorStop(0.3, 'rgba(255,150,50,0.45)'); g.addColorStop(0.6, 'rgba(255,110,30,0.85)'); g.addColorStop(0.85, 'rgba(255,200,120,0.95)'); g.addColorStop(1, 'rgba(70,110,255,0.95)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(x - w / 2, baseY);
      var steps = 9;
      for (var i = 0; i <= steps; i++) {
        var p = i / steps, px = x - w / 2 + p * w;
        var n = noise(p * 4 + seed, t + seed);
        var hh = h * (1 - Math.pow(Math.abs(p - 0.5) * 2, 1.6)) * (0.75 + 0.25 * n);
        var sway = Math.sin(t * 2.4 + seed + p * 3) * w * 0.12 * (hh / h);
        ctx.lineTo(px + sway, baseY - Math.max(0, hh));
      }
      ctx.lineTo(x + w / 2, baseY); ctx.closePath(); ctx.fill();
    }
    function draw(now) {
      if (!running) return; requestAnimationFrame(draw);
      if (!visible) return;
      var t = (now - t0) / 1000, W = canvas.width, H = canvas.height;
      ctx.clearRect(0, 0, W, H);
      var fl = 0.8 + 0.2 * Math.sin(t * 6.3) * Math.sin(t * 2.1 + 1) + 0.06 * Math.sin(t * 17);
      var cx = W * 0.5, cy = H * 0.66;
      var g = ctx.createRadialGradient(cx, cy, 0, cx, cy, W * 0.42);
      g.addColorStop(0, 'rgba(255,150,60,' + (0.34 * fl) + ')'); g.addColorStop(0.35, 'rgba(255,110,40,' + (0.16 * fl) + ')'); g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      if (!reduce) { for (var s = 0; s < 18; s++) { var sp = (t * 0.22 + s * 0.055) % 1; var sx = cx + Math.sin(s * 2.4) * W * 0.16 + Math.sin(t * 1.6 + s) * 8 * dpr; var sy = cy + H * 0.08 - sp * H * 0.45; ctx.fillStyle = 'rgba(255,200,120,' + (1 - sp) * 0.7 + ')'; ctx.beginPath(); ctx.arc(sx, sy, (0.8 + (1 - sp) * 1.4) * dpr, 0, 7); ctx.fill(); } }
    }
    requestAnimationFrame(draw);
    document.addEventListener('visibilitychange', function () { running = !document.hidden; if (running) requestAnimationFrame(draw); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { setTimeout(init, 300); }); else setTimeout(init, 300);
  // retry until template mounts
  var tries = 0, iv = setInterval(function () { if (document.getElementById('nm-fireplace') && document.getElementById('nm-fireplace').querySelector('canvas')) { clearInterval(iv); init(); } else if (++tries > 60) clearInterval(iv); }, 250);
})();
