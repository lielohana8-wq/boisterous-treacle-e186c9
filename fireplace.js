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
    setTimeout(function () { root.classList.add('nm-open'); root.setAttribute('data-open', '1'); }, reduce ? 0 : 900);
    // flames
    var t0 = performance.now(), running = true, visible = true;
    if ('IntersectionObserver' in window) new IntersectionObserver(function (e) { visible = e[0].isIntersecting; }).observe(root);
    function noise(x, t) { return Math.sin(x * 1.7 + t * 2.1) * 0.5 + Math.sin(x * 3.3 - t * 1.3) * 0.3 + Math.sin(x * 7.1 + t * 3.7) * 0.2; }
    function flame(x, baseY, w, h, t, seed) {
      var g = ctx.createLinearGradient(0, baseY - h, 0, baseY);
      g.addColorStop(0, 'rgba(255,170,60,0)'); g.addColorStop(0.35, 'rgba(255,140,40,0.55)'); g.addColorStop(0.75, 'rgba(255,90,20,0.9)'); g.addColorStop(1, 'rgba(60,90,255,0.9)');
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
      // ember glow bed
      var bed = ctx.createRadialGradient(W / 2, H * 0.92, 0, W / 2, H * 0.92, W * 0.55);
      bed.addColorStop(0, 'rgba(255,120,40,' + (0.55 + 0.1 * Math.sin(t * 3)) + ')'); bed.addColorStop(0.5, 'rgba(200,60,10,0.25)'); bed.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = bed; ctx.fillRect(0, 0, W, H);
      ctx.globalCompositeOperation = 'lighter';
      var baseY = H * 0.84, n = reduce ? 7 : 14;
      for (var i = 0; i < n; i++) {
        var p = (i + 0.5) / n, x = W * (0.22 + p * 0.56);
        var h = H * (0.22 + 0.3 * (1 - Math.abs(p - 0.5) * 1.6)) * (0.85 + 0.15 * Math.sin(t * 5 + i));
        flame(x, baseY + (i % 2) * H * 0.02, W * 0.11, h * 1.15, reduce ? 0 : t, i * 1.37);
      }
      // hot core haze
      var haze = ctx.createRadialGradient(W / 2, baseY - H * 0.1, 0, W / 2, baseY - H * 0.1, W * 0.35);
      haze.addColorStop(0, 'rgba(255,200,120,0.28)'); haze.addColorStop(1, 'rgba(255,120,40,0)');
      ctx.fillStyle = haze; ctx.fillRect(0, 0, W, H);
      ctx.globalCompositeOperation = 'source-over';
      // sparks
      if (!reduce) { for (var s = 0; s < 14; s++) { var sp = (t * 0.35 + s * 0.071) % 1; var sx = W * (0.3 + 0.4 * ((s * 0.618) % 1)) + Math.sin(t * 2 + s) * 6 * dpr; var sy = baseY - sp * H * 0.7; ctx.fillStyle = 'rgba(255,190,110,' + (1 - sp) * 0.9 + ')'; ctx.fillRect(sx, sy, 2 * dpr, 2 * dpr); } }
    }
    requestAnimationFrame(draw);
    document.addEventListener('visibilitychange', function () { running = !document.hidden; if (running) requestAnimationFrame(draw); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { setTimeout(init, 300); }); else setTimeout(init, 300);
  // retry until template mounts
  var tries = 0, iv = setInterval(function () { if (document.getElementById('nm-fireplace') && document.getElementById('nm-fireplace').querySelector('canvas')) { clearInterval(iv); init(); } else if (++tries > 60) clearInterval(iv); }, 250);
})();
