/* PRIMEFLUE — <chimney-3d> interactive model + <ember-field> particle overlay */
(function () {
  var THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
  var EMBER = 0xE8622C;
  var reduced = false; /* brand site: motion is part of the product */

  function brickTex(T) {
    var c = document.createElement('canvas'); c.width = 256; c.height = 256;
    var x = c.getContext('2d');
    x.fillStyle = '#20170d'; x.fillRect(0, 0, 256, 256);
    var bw = 62, bh = 25, m = 5, row = 0, y, bx;
    for (y = 0; y < 256; y += bh + m, row++) {
      for (bx = (row % 2 ? -(bw + m) / 2 : 0); bx < 256; bx += bw + m) {
        var v = 42 + Math.random() * 26;
        x.fillStyle = 'rgb(' + Math.round(v + 12) + ',' + Math.round(v * 0.74) + ',' + Math.round(v * 0.46) + ')';
        x.fillRect(bx, y, bw, bh);
        x.fillStyle = 'rgba(245,239,228,0.05)'; x.fillRect(bx, y, bw, 2);
      }
    }
    var t = new T.CanvasTexture(c); t.wrapS = t.wrapT = T.RepeatWrapping; t.colorSpace = T.SRGBColorSpace;
    return t;
  }
  function smokeTex(T) {
    var c = document.createElement('canvas'); c.width = c.height = 64;
    var x = c.getContext('2d');
    var g = x.createRadialGradient(32, 32, 2, 32, 32, 30);
    g.addColorStop(0, 'rgba(232,224,208,0.5)'); g.addColorStop(1, 'rgba(232,224,208,0)');
    x.fillStyle = g; x.fillRect(0, 0, 64, 64);
    return new T.CanvasTexture(c);
  }

  class Chimney3D extends HTMLElement {
    connectedCallback() {
      if (this._init) return; this._init = true;
      if (!this.style.display) this.style.display = 'block';
      this._activeIdx = 0; this._vis = false;
      var self = this;
      this._boot().catch(function () { self.setAttribute('data-failed', '1'); });
    }
    disconnectedCallback() {
      this._dead = true;
      if (this._ro) this._ro.disconnect();
      if (this._io) this._io.disconnect();
    }
    setActive(i) { this._activeIdx = i; if (this._sync) this._sync(); }
    async _boot() {
      var T = await import(THREE_URL);
      if (this._dead) return;
      var self = this;
      var cine = this.hasAttribute('cinematic'), introT = 0;
      var renderer = new T.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.25));
      renderer.outputColorSpace = T.SRGBColorSpace;
      var cv = renderer.domElement;
      cv.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;touch-action:pan-y;cursor:grab';
      this.appendChild(cv);

      var scene = new T.Scene();
      var cam = new T.PerspectiveCamera(34, 1, 0.1, 80);
      if (cine) { cam.position.set(0.2, 1.9, 14.2); cam.lookAt(0, 2.2, 0); }
      else { cam.position.set(5.8, 3.6, 8.6); cam.lookAt(0, 1.15, 0); }
      scene.add(new T.AmbientLight(0xFFE8D0, 0.55));
      var key = new T.DirectionalLight(0xFFF2E0, 1.6); key.position.set(4, 8, 5); scene.add(key);
      var rim = new T.DirectionalLight(0x7E90C8, 0.4); rim.position.set(-6, 3, -5); scene.add(rim);

      var pivot = new T.Group(); scene.add(pivot);
      var g = new T.Group(); pivot.add(g); g.rotation.y = -0.45;

      var bt = brickTex(T); bt.repeat.set(1.3, 3);
      var brick = new T.MeshStandardMaterial({ map: bt, roughness: 0.94 });
      var dark = new T.MeshStandardMaterial({ color: 0x14100a, roughness: 1 });
      var metal = new T.MeshStandardMaterial({ color: 0xB9BDC4, metalness: 0.85, roughness: 0.35 });
      var clay = new T.MeshStandardMaterial({ color: 0x8a5f3a, roughness: 0.8 });

      var stack = new T.Mesh(new T.BoxGeometry(1.5, 5.2, 1.5), brick); stack.position.y = 0.8; g.add(stack);
      var crown = new T.Mesh(new T.BoxGeometry(1.92, 0.2, 1.92), new T.MeshStandardMaterial({ color: 0xCFC8BB, roughness: 0.7 })); crown.position.y = 3.5; g.add(crown);
      var flue = new T.Mesh(new T.CylinderGeometry(0.36, 0.36, 0.55, 24), clay); flue.position.y = 3.85; g.add(flue);
      [[0.3, 0.3], [-0.3, 0.3], [0.3, -0.3], [-0.3, -0.3]].forEach(function (p) {
        var leg = new T.Mesh(new T.BoxGeometry(0.06, 0.34, 0.06), metal);
        leg.position.set(p[0], 4.26, p[1]); g.add(leg);
      });
      var lid = new T.Mesh(new T.BoxGeometry(1.06, 0.09, 1.06), metal); lid.position.y = 4.46; g.add(lid);

      if (self.hasAttribute('anatomy')) {
        var slopeL = new T.Mesh(new T.BoxGeometry(1.9, 0.13, 2.5), dark);
        slopeL.rotation.z = 0.42; slopeL.position.set(-0.85, 0.78, 0); g.add(slopeL);
        var slopeR = slopeL.clone(); slopeR.rotation.z = -0.42; slopeR.position.x = 0.85; g.add(slopeR);
        var ridge = new T.Mesh(new T.BoxGeometry(0.34, 0.15, 2.5), new T.MeshStandardMaterial({ color: 0x1e1810, roughness: 1 })); ridge.position.y = 1.16; g.add(ridge);
      }
      var collar = new T.Mesh(new T.BoxGeometry(1.8, 0.16, 1.8), new T.MeshStandardMaterial({ color: 0x7a5a34, metalness: 0.7, roughness: 0.4 })); collar.position.y = 1.52; g.add(collar);
      var ringM = null, ringGlow = null;
      if (cine) {
        ringM = new T.Mesh(new T.TorusGeometry(2.75, 0.028, 12, 90), new T.MeshBasicMaterial({ color: 0xFF9A5C, transparent: true, opacity: 0 }));
        ringM.position.set(0, 2.15, -1.7); scene.add(ringM);
        ringGlow = new T.Sprite(new T.SpriteMaterial({ map: smokeTex(T), transparent: true, opacity: 0, depthWrite: false, color: 0xE8622C }));
        ringGlow.scale.setScalar(8.5); ringGlow.position.set(0, 2.15, -2.4); scene.add(ringGlow);
        var floorGlow = new T.Mesh(new T.CircleGeometry(3.6, 40), new T.MeshBasicMaterial({ map: smokeTex(T), transparent: true, opacity: 0.16, color: 0xE8622C, depthWrite: false }));
        floorGlow.rotation.x = -Math.PI / 2; floorGlow.position.y = -1.86; scene.add(floorGlow);
      }

      var hearth = new T.Mesh(new T.BoxGeometry(2.3, 0.16, 1.3), new T.MeshStandardMaterial({ color: 0x241c11, roughness: 1 })); hearth.position.set(0, -1.76, 0.3); g.add(hearth);
      var fbFrame = new T.Mesh(new T.BoxGeometry(1.0, 0.9, 0.12), dark); fbFrame.position.set(0, -1.22, 0.72); g.add(fbFrame);
      var glow = new T.Mesh(new T.PlaneGeometry(0.78, 0.66), new T.MeshBasicMaterial({ color: 0xFF8C46 }));
      glow.position.set(0, -1.24, 0.79); g.add(glow);
      var fire = new T.PointLight(EMBER, 2, 7); fire.position.set(0, -1.0, 1.4); g.add(fire);
      var topGlow = new T.PointLight(EMBER, 0.7, 3.5); topGlow.position.set(0, 4.05, 0); g.add(topGlow);

      var st = smokeTex(T), puffs = [], i;
      for (i = 0; i < 16; i++) {
        var sm = new T.SpriteMaterial({ map: st, transparent: true, opacity: 0, depthWrite: false });
        var sp = new T.Sprite(sm); sp.userData.off = Math.random(); g.add(sp); puffs.push(sp);
      }

      var partPos = [
        [0, 4.6, 0],        // 1 cap
        [0, 3.52, 1.0],     // 2 crown
        [0, 3.95, 0.48],    // 3 liner
        [0.82, 2.45, 0.82], // 4 masonry
        [0.94, 1.6, 0.94],  // 5 flashing
        [0, -0.5, 0.82],    // 6 damper
        [0, -1.24, 0.95]    // 7 firebox
      ];
      var markers = !self.hasAttribute('anatomy') ? [] : partPos.map(function (p) {
        var m = new T.Mesh(new T.SphereGeometry(0.11, 18, 18), new T.MeshBasicMaterial({ color: EMBER }));
        m.position.set(p[0], p[1], p[2]); m.userData.base = 1; g.add(m);
        return m;
      });
      this._sync = function () {
        markers.forEach(function (m, j) {
          var a = j === self._activeIdx;
          m.material.color.setHex(a ? 0xFFB05C : EMBER);
          m.userData.base = a ? 1.6 : 1;
        });
      };
      this._sync();

      var tilt = 0.06, dragging = false, px = 0, py = 0, moved = 0, idleT = 10, smX = 0, smY = 0;
      if (cine) this.addEventListener('pointermove', function (e) {
        var r = self.getBoundingClientRect();
        smX += (((e.clientX - r.left) / r.width - 0.5) - smX) * 0.08;
        smY += (((e.clientY - r.top) / r.height - 0.5) - smY) * 0.08;
      }, { passive: true });
      cv.addEventListener('pointerdown', function (e) {
        dragging = true; moved = 0; px = e.clientX; py = e.clientY;
        try { cv.setPointerCapture(e.pointerId); } catch (err) {}
        cv.style.cursor = 'grabbing';
      });
      cv.addEventListener('pointermove', function (e) {
        if (!dragging) return;
        var dx = e.clientX - px, dy = e.clientY - py; px = e.clientX; py = e.clientY;
        moved += Math.abs(dx) + Math.abs(dy);
        g.rotation.y += dx * 0.006;
        tilt = Math.max(-0.2, Math.min(0.35, tilt + dy * 0.0025));
        idleT = 0;
      });
      cv.addEventListener('pointerup', function (e) {
        dragging = false; cv.style.cursor = 'grab';
        if (moved < 7 && !cine) pick(e);
      });
      var ray = new T.Raycaster(); ray.params.Points = { threshold: 0.2 };
      var v2 = new T.Vector2();
      function pick(e) {
        var r = cv.getBoundingClientRect();
        v2.x = ((e.clientX - r.left) / r.width) * 2 - 1;
        v2.y = -((e.clientY - r.top) / r.height) * 2 + 1;
        ray.setFromCamera(v2, cam);
        var hits = ray.intersectObjects(markers, false);
        if (hits.length) {
          var idx = markers.indexOf(hits[0].object);
          self._activeIdx = idx; self._sync();
          self.dispatchEvent(new CustomEvent('part-select', { detail: { index: idx }, bubbles: true }));
        }
      }

      var size = function () {
        var w = self.clientWidth || 320, h = self.clientHeight || 320;
        renderer.setSize(w, h, false);
        cam.aspect = w / h; cam.updateProjectionMatrix();
      };
      this._ro = new ResizeObserver(size); this._ro.observe(this); size();
      this._io = new IntersectionObserver(function (en) { self._vis = en[0].isIntersecting; if (self.hasAttribute('data-pauses-world')) window.__pfWorldPaused = self._vis; });
      this._io.observe(this);

      var clock = new T.Clock(), t = 0;
      var tick = function () {
        if (self._dead) return;
        requestAnimationFrame(tick);
        if (!self._vis) return;
        var dt = Math.min(clock.getDelta(), 0.05); t += dt; idleT += dt;
        if (cine) {
          introT += dt;
          var desk = (self.clientWidth || 1000) > 760;
          var k1r = Math.min(1, introT / 2.6), k1 = 1 - Math.pow(1 - k1r, 3);
          var k2r = Math.min(1, Math.max(0, (introT - 2.9) / 2.5)), k2 = k2r * k2r * (3 - 2 * k2r);
          var drift = introT > 5.4 ? Math.sin(t * 0.24) * 0.22 : 0;
          var ex = desk ? 4.7 : 0.3, ey = desk ? 2.3 : 2.7, ez = desk ? 7.3 : 10.2;
          cam.position.set(0.2 + (ex - 0.2) * k2 + drift, 1.9 + (ey - 1.9) * k2 - smY * 0.4, 14.2 + (10.4 - 14.2) * k1 + (ez - 10.4) * k2);
          cam.lookAt(0.55 * k2 + smX * 0.3, 2.2 + ((desk ? 1.55 : 1.9) - 2.2) * k2, 0);
          g.position.x = desk ? k2 * 1.05 : 0;
          if (ringM) {
            var rPulse = 0.55 + 0.3 * Math.sin(t * 1.6);
            ringM.material.opacity = k1 * (1 - k2 * 0.85) * rPulse;
            ringGlow.material.opacity = k1 * (1 - k2 * 0.9) * 0.4;
            ringM.scale.setScalar(0.92 + k1 * 0.08);
          }
        }
        if (!dragging && idleT > 2.5 && !reduced) g.rotation.y += dt * (cine ? 0.09 : 0.14);
        pivot.rotation.x += (tilt - pivot.rotation.x) * 0.1;
        fire.intensity = 1.8 + Math.sin(t * 9) * 0.35 + (Math.random() - 0.5) * 0.35;
        glow.material.color.setHSL(0.06, 0.95, 0.55 + Math.sin(t * 7) * 0.06);
        markers.forEach(function (m, j) {
          var pulse = j === self._activeIdx ? 1 + 0.14 * Math.sin(t * 4.5) : 1;
          m.scale.setScalar(m.userData.base * pulse);
        });
        for (var k = 0; k < puffs.length; k++) {
          var p = (puffs[k].userData.off + t * 0.1) % 1;
          var fade = p < 0.15 ? p / 0.15 : 1 - (p - 0.15) / 0.85;
          puffs[k].position.set(Math.sin(p * 6 + k) * 0.3 * p, 4.7 + p * 2.4, Math.cos(p * 5 + k) * 0.2 * p);
          puffs[k].scale.setScalar(0.5 + p * 1.9);
          puffs[k].material.opacity = reduced ? 0 : 0.26 * fade;
        }
        renderer.render(scene, cam);
      };
      tick();
    }
  }

  class EmberField extends HTMLElement {
    connectedCallback() {
      if (this._i || reduced) return; this._i = true;
      this.style.pointerEvents = 'none';
      var cv = document.createElement('canvas');
      cv.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
      this.appendChild(cv);
      var x = cv.getContext('2d'), self = this;
      var W = 0, H = 0, ps = [];
      function spawn(anywhere) {
        return { x: Math.random() * W, y: anywhere ? Math.random() * H : H + 12,
          r: 0.8 + Math.random() * 2.0, v: 13 + Math.random() * 28,
          sw: 10 + Math.random() * 36, ph: Math.random() * 7, a: 0.18 + Math.random() * 0.42 };
      }
      function size() {
        W = self.clientWidth; H = self.clientHeight; cv.width = W; cv.height = H;
        var n = Math.max(18, Math.min(50, Math.round(W / 36)));
        ps = []; for (var i = 0; i < n; i++) ps.push(spawn(true));
      }
      var ro = new ResizeObserver(size); ro.observe(this); size();
      var vis = true;
      var io = new IntersectionObserver(function (en) { vis = en[0].isIntersecting; }); io.observe(this);
      var last = performance.now();
      function tick(now) {
        if (!self.isConnected) { ro.disconnect(); io.disconnect(); return; }
        requestAnimationFrame(tick);
        if (!vis) { last = now; return; }
        var dt = Math.min((now - last) / 1000, 0.05); last = now;
        x.clearRect(0, 0, W, H);
        for (var i = 0; i < ps.length; i++) {
          var p = ps[i];
          p.y -= p.v * dt; p.ph += dt;
          if (p.y < -12) { ps[i] = spawn(false); continue; }
          var fl = 0.65 + 0.35 * Math.sin(p.ph * 6 + i);
          x.globalAlpha = p.a * fl;
          x.fillStyle = '#FF8C46';
          x.beginPath();
          x.arc(p.x + Math.sin(p.ph * 0.9) * p.sw * 0.25, p.y, p.r, 0, 7);
          x.fill();
        }
        x.globalAlpha = 1;
      }
      requestAnimationFrame(tick);
    }
  }

  if (!customElements.get('chimney-3d')) customElements.define('chimney-3d', Chimney3D);
  if (!customElements.get('ember-field')) customElements.define('ember-field', EmberField);
})();
