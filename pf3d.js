/* PRIMEFLUE pf3d — site-wide 3D motion layer: 3D scroll reveals, hover tilt, hero parallax, ambient sparks */
(function () {
  if (document.getElementById('__pf-pf3d-lock')) return;
  var __lock = document.createElement('meta'); __lock.id = '__pf-pf3d-lock';
  (document.head || document.documentElement).appendChild(__lock);
  var reduced = false; /* brand site: motion is part of the product */
  var finePointer = window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  function ready(fn) { if (document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  function whenSections(fn) {
    var n = 0;
    var iv = setInterval(function () {
      if (document.querySelectorAll('section[data-screen-label]').length || n++ > 60) { clearInterval(iv); setTimeout(fn, 150); }
    }, 150);
  }

  /* 1 — 3D scroll reveal: sections rise + un-tilt into place */
  function reveal3D() {
    var io = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target; io.unobserve(el);
        el.style.opacity = '';
        el.style.transformOrigin = 'center top';
        el.animate([
          { opacity: 0.001, transform: 'perspective(1100px) translateY(48px) rotateX(7deg) scale(0.985)' },
          { opacity: 1, transform: 'none' }
        ], { duration: 750, easing: 'cubic-bezier(.2,.7,.25,1)' });
      });
    }, { threshold: 0.07 });
    document.querySelectorAll('section[data-screen-label], footer[data-screen-label]').forEach(function (sec) {
      if (sec.getBoundingClientRect().top > innerHeight * 0.88) { sec.style.opacity = '0'; io.observe(sec); }
    });
  }

  /* 2 — hover tilt: cards lean toward the cursor in 3D */
  function tiltCards() {
    if (!finePointer) return;
    var cands = [], seen = 0;
    document.querySelectorAll('section [data-screen-label], section div, section a').forEach(function (el) {
      if (cands.length >= 48 || seen++ > 4000) return;
      if (el.closest('nav') || el.querySelector('canvas') || el.querySelector('chimney-3d')) return;
      var w = el.clientWidth, h = el.clientHeight;
      if (w < 220 || w > 780 || h < 150 || h > 920) return;
      var cs = getComputedStyle(el);
      var bordered = cs.borderStyle.indexOf('solid') > -1 && parseFloat(cs.borderTopWidth) > 0;
      var floated = cs.boxShadow !== 'none';
      if (!bordered && !floated) return;
      if (el.parentElement && cands.indexOf(el.parentElement) > -1) return;
      cands.push(el);
    });
    cands.forEach(function (el) {
      var raf = 0;
      el.addEventListener('pointerenter', function () { el.style.transition = 'transform .14s ease-out'; el.style.willChange = 'transform'; });
      el.addEventListener('pointermove', function (e) {
        if (raf) return;
        raf = requestAnimationFrame(function () {
          raf = 0;
          var r = el.getBoundingClientRect();
          var rx = ((e.clientY - r.top) / r.height - 0.5) * -5.5;
          var ry = ((e.clientX - r.left) / r.width - 0.5) * 6.5;
          el.style.transform = 'perspective(900px) rotateX(' + rx.toFixed(2) + 'deg) rotateY(' + ry.toFixed(2) + 'deg) translateZ(8px)';
        });
      });
      el.addEventListener('pointerleave', function () {
        el.style.transition = 'transform .45s cubic-bezier(.2,.7,.3,1)';
        el.style.transform = '';
        el.style.willChange = '';
      });
    });
  }

  /* 3 — hero parallax: hero image drifts slower than the page */
  function parallax() {
    var targets = [];
    var heroBg = document.querySelector('header image-slot');
    if (heroBg) {
      var wrap = heroBg.closest('div');
      if (wrap) { var hd = wrap.closest('header'); if (hd) hd.style.overflow = 'clip'; targets.push({ el: wrap, f: 0.05, scale: 1.07 }); }
    }
    if (!targets.length) return;
    var vis = true, ticking = false;
    var io = new IntersectionObserver(function (en) { vis = en[0].isIntersecting; });
    io.observe(targets[0].el);
    function apply() {
      ticking = false;
      targets.forEach(function (t) {
        var y = Math.min(scrollY * t.f, 24);
        t.el.style.transform = 'translateY(' + y.toFixed(1) + 'px) scale(' + t.scale + ')';
      });
    }
    addEventListener('scroll', function () {
      if (!vis || ticking) return;
      ticking = true; requestAnimationFrame(apply);
    }, { passive: true });
    apply();
  }

  /* 4 — ambient sparks: sparse ember drift over the whole page */
  function sparks() {
    var cv = document.createElement('canvas');
    cv.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;z-index:45;pointer-events:none';
    document.body.appendChild(cv);
    var x = cv.getContext('2d'), W = 0, H = 0, ps = [];
    function spawn(any) {
      return { x: Math.random() * W, y: any ? Math.random() * H : H + 8,
        r: 0.6 + Math.random() * 1.3, v: 9 + Math.random() * 16,
        sw: 8 + Math.random() * 26, ph: Math.random() * 7, a: 0.1 + Math.random() * 0.2 };
    }
    function size() {
      W = cv.width = innerWidth; H = cv.height = innerHeight;
      var n = Math.max(10, Math.min(22, Math.round(W / 90)));
      ps = []; for (var i = 0; i < n; i++) ps.push(spawn(true));
    }
    addEventListener('resize', size); size();
    var last = performance.now(), hidden = false;
    document.addEventListener('visibilitychange', function () { hidden = document.hidden; last = performance.now(); });
    function tick(now) {
      requestAnimationFrame(tick);
      if (hidden) return;
      var dt = Math.min((now - last) / 1000, 0.05); last = now;
      x.clearRect(0, 0, W, H);
      for (var i = 0; i < ps.length; i++) {
        var p = ps[i];
        p.y -= p.v * dt; p.ph += dt;
        if (p.y < -10) { ps[i] = spawn(false); continue; }
        x.globalAlpha = p.a * (0.65 + 0.35 * Math.sin(p.ph * 5 + i));
        x.fillStyle = '#FF8C46';
        x.beginPath();
        x.arc(p.x + Math.sin(p.ph * 0.8) * p.sw * 0.25, p.y, p.r, 0, 7);
        x.fill();
      }
      x.globalAlpha = 1;
    }
    requestAnimationFrame(tick);
  }

  ready(function () {
    whenSections(function () {
      try { reveal3D(); } catch (e) {}
      try { tiltCards(); } catch (e) {}
      try { parallax(); } catch (e) {}
      try { sparks(); } catch (e) {}
    });
  });
})();
