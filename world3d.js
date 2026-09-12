/* PRIMEFLUE world3d v4 — cinematic scroll-driven WebGL world (as shipped in PRIMEFLUE.html),
   with a realistic flue dive: creosote-lined brick, technician lamp, real firebox with logs. */
(function () {
  if (document.getElementById('__pf-world3d-lock')) return;
  var __lock = document.createElement('meta'); __lock.id = '__pf-world3d-lock';
  (document.head || document.documentElement).appendChild(__lock);
  var THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
  var EMBER = 0xE8622C;

  function ready(fn) { if (document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }

  function brickTex(T, dark) {
    var c = document.createElement('canvas'); c.width = 512; c.height = 512;
    var x = c.getContext('2d');
    x.fillStyle = dark ? '#150e07' : '#1e150c'; x.fillRect(0, 0, 512, 512);
    var bw = 118, bh = 46, m = 9, row = 0, y, bx;
    for (y = 0; y < 512; y += bh + m, row++) {
      for (bx = (row % 2 ? -(bw + m) / 2 : 0); bx < 512; bx += bw + m) {
        var v = (dark ? 24 : 40) + Math.random() * 26;
        x.fillStyle = 'rgb(' + Math.round(v + 14) + ',' + Math.round(v * 0.7) + ',' + Math.round(v * 0.42) + ')';
        x.fillRect(bx, y, bw, bh);
        x.fillStyle = 'rgba(255,240,220,0.05)'; x.fillRect(bx, y, bw, 3);
        x.fillStyle = 'rgba(0,0,0,0.25)'; x.fillRect(bx, y + bh - 3, bw, 3);
      }
    }
    var t = new T.CanvasTexture(c); t.wrapS = t.wrapT = T.RepeatWrapping; t.colorSpace = T.SRGBColorSpace;
    return t;
  }
  function glowTex(T, rgb) {
    var c = document.createElement('canvas'); c.width = c.height = 128;
    var x = c.getContext('2d');
    var g = x.createRadialGradient(64, 64, 2, 64, 64, 62);
    g.addColorStop(0, 'rgba(' + rgb + ',0.95)'); g.addColorStop(0.4, 'rgba(' + rgb + ',0.3)'); g.addColorStop(1, 'rgba(' + rgb + ',0)');
    x.fillStyle = g; x.fillRect(0, 0, 128, 128);
    return new T.CanvasTexture(c);
  }
  function domeTex(T, stops) {
    var c = document.createElement('canvas'); c.width = 4; c.height = 512;
    var x = c.getContext('2d');
    var g = x.createLinearGradient(0, 0, 0, 512);
    stops.forEach(function (s) { g.addColorStop(s[0], s[1]); });
    x.fillStyle = g; x.fillRect(0, 0, 4, 512);
    var t = new T.CanvasTexture(c); t.colorSpace = T.SRGBColorSpace;
    return t;
  }
  function smoothstep(a, b, t) { t = Math.max(0, Math.min(1, (t - a) / (b - a))); return t * t * (3 - 2 * t); }

  async function boot() {
    var T = await import(THREE_URL);
    var cv = document.createElement('canvas');
    cv.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;z-index:0;pointer-events:none';
    document.body.insertBefore(cv, document.body.firstChild);
    var renderer = new T.WebGLRenderer({ canvas: cv, antialias: true, alpha: false });
    var isMobile = innerWidth < 820;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isMobile ? 1 : 1.25));
    renderer.outputColorSpace = T.SRGBColorSpace;
    renderer.toneMapping = T.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.42;
    renderer.shadowMap.enabled = false;
    renderer.shadowMap.type = T.PCFSoftShadowMap;

    var scene = new T.Scene();
    var duskC = new T.Color(0x181009), nightC = new T.Color(0x0A0C14);
    scene.fog = new T.FogExp2(0x181009, 0.026);
    scene.background = new T.Color(0x181009);
    var cam = new T.PerspectiveCamera(38, 1, 0.05, 160);

    var amb = new T.HemisphereLight(0xFFDDB8, 0x241A10, 0.8); scene.add(amb);
    var key = new T.DirectionalLight(0xFFC896, 2.1);
    key.position.set(-10, 6, 8); key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024);
    key.shadow.camera.left = -8; key.shadow.camera.right = 8;
    key.shadow.camera.top = 8; key.shadow.camera.bottom = -8;
    scene.add(key);
    var moonLight = new T.DirectionalLight(0x9FB4E8, 0.0); moonLight.position.set(7, 12, -6); scene.add(moonLight);

    /* sky domes: dusk crossfades to night */
    var domeG = new T.SphereGeometry(70, 24, 16);
    var duskDome = new T.Mesh(domeG, new T.MeshBasicMaterial({
      map: domeTex(T, [[0, '#0a0806'], [0.45, '#1c120a'], [0.72, '#4a2812'], [0.85, '#8a4518'], [1, '#b06024']]),
      side: T.BackSide, transparent: true, fog: false, depthWrite: false }));
    scene.add(duskDome);
    var nightDome = new T.Mesh(domeG, new T.MeshBasicMaterial({
      map: domeTex(T, [[0, '#04050a'], [0.6, '#070910'], [0.85, '#0c1018'], [1, '#131a26']]),
      side: T.BackSide, transparent: true, opacity: 0, fog: false, depthWrite: false }));
    scene.add(nightDome);

    var sun = new T.Sprite(new T.SpriteMaterial({ map: glowTex(T, '255,150,70'), transparent: true, depthWrite: false, fog: false }));
    sun.scale.setScalar(30); sun.position.set(-14, 2.2, -28); scene.add(sun);
    var moon = new T.Sprite(new T.SpriteMaterial({ map: glowTex(T, '225,230,245'), transparent: true, depthWrite: false, fog: false, opacity: 0 }));
    moon.scale.setScalar(7); moon.position.set(11, -2, -26); scene.add(moon);

    /* stars */
    (function () {
      var n = 300, pos = new Float32Array(n * 3);
      for (var i = 0; i < n; i++) {
        var a = Math.random() * Math.PI * 2, r = 34 + Math.random() * 26, e = Math.random() * Math.PI * 0.48;
        pos[i * 3] = Math.cos(a) * Math.cos(e) * r;
        pos[i * 3 + 1] = 3 + Math.sin(e) * r;
        pos[i * 3 + 2] = Math.sin(a) * Math.cos(e) * r;
      }
      var g = new T.BufferGeometry(); g.setAttribute('position', new T.BufferAttribute(pos, 3));
      window.__pfStars = new T.Points(g, new T.PointsMaterial({ color: 0xF5EFE4, size: 0.14, transparent: true, opacity: 0, fog: false, depthWrite: false }));
      scene.add(window.__pfStars);
    })();
    var stars = window.__pfStars;

    var ground = new T.Mesh(new T.PlaneGeometry(140, 140), new T.MeshStandardMaterial({ color: 0x0B0906, roughness: 1 }));
    ground.rotation.x = -Math.PI / 2; ground.position.y = -2.0; ground.receiveShadow = true; scene.add(ground);
    var blockMat = new T.MeshStandardMaterial({ color: 0x100c07, roughness: 1 });
    var winTex = glowTex(T, '255,190,110');
    for (var i = 0; i < 30; i++) {
      var bw2 = 1.2 + Math.random() * 2.6, bh2 = 1.5 + Math.random() * 5;
      var b = new T.Mesh(new T.BoxGeometry(bw2, bh2, bw2), blockMat);
      var ang = Math.random() * Math.PI * 2, rad = 14 + Math.random() * 22;
      b.position.set(Math.cos(ang) * rad, -2 + bh2 / 2, Math.sin(ang) * rad - 8);
      b.rotation.y = Math.random() * Math.PI;
      scene.add(b);
      if (Math.random() > 0.4) {
        var w = new T.Sprite(new T.SpriteMaterial({ map: winTex, transparent: true, opacity: 0.5 + Math.random() * 0.4, fog: true, depthWrite: false }));
        w.scale.setScalar(0.5 + Math.random() * 0.5);
        w.position.copy(b.position); w.position.y += Math.random() * bh2 * 0.4; w.position.x += bw2 * 0.4;
        scene.add(w);
      }
    }

    /* ===== the chimney ===== */
    var world = new T.Group(); scene.add(world);
    var bt = brickTex(T); bt.repeat.set(1.4, 3.2);
    var brick = new T.MeshStandardMaterial({ map: bt, roughness: 0.92 });
    var dark = new T.MeshStandardMaterial({ color: 0x13100a, roughness: 0.95 });
    var metal = new T.MeshStandardMaterial({ color: 0xB9BDC4, metalness: 0.9, roughness: 0.3, transparent: true });
    function sh(m) { m.castShadow = true; m.receiveShadow = true; return m; }
    var stack = sh(new T.Mesh(new T.BoxGeometry(1.44, 5.4, 1.44), new T.MeshStandardMaterial({ color: 0x1A120B, roughness: 1 }))); stack.position.y = 0.9; world.add(stack);
    if (isMobile) { var stackSkin = sh(new T.Mesh(new T.BoxGeometry(1.5, 5.4, 1.5), brick)); stackSkin.position.y = 0.9; world.add(stackSkin); }
    else (function () {
      /* real brick courses with irregularity — kills the CG look */
      var bl = 0.48, bh = 0.225, bd = 0.115, gap = 0.032, half = 0.75;
      var geo = new T.BoxGeometry(bl, bh, bd);
      var bmats = [];
      for (var mi = 0; mi < 8; mi++) {
        var vv = 46 + Math.random() * 34;
        bmats.push(new T.MeshStandardMaterial({ color: 'rgb(' + Math.round(vv + 18) + ',' + Math.round(vv * 0.62) + ',' + Math.round(vv * 0.38) + ')', roughness: 0.82 + Math.random() * 0.15 }));
      }
      var rows = Math.floor(5.4 / (bh + gap));
      for (var r = 0; r < rows; r++) {
        var y = 0.9 - 2.7 + (bh + gap) * (r + 0.5);
        var shift = (r % 2) ? (bl + gap) / 2 : 0;
        for (var px = -half; px <= half + 0.01; px += bl + gap) {
          var p = Math.max(-half + bl * 0.4, Math.min(half - bl * 0.4, px + shift));
          for (var w = 0; w < 4; w++) {
            var m = new T.Mesh(geo, bmats[Math.floor(Math.random() * 8)]);
            var out = half - bd / 2 + 0.05 + (Math.random() - 0.5) * 0.014;
            var jy = (Math.random() - 0.5) * 0.008, jr = (Math.random() - 0.5) * 0.03;
            if (w === 0) { m.position.set(p, y + jy, -out); m.rotation.y = jr; }
            else if (w === 1) { m.position.set(p, y + jy, out); m.rotation.y = jr; }
            else if (w === 2) { m.position.set(-out, y + jy, p); m.rotation.y = Math.PI / 2 + jr; }
            else { m.position.set(out, y + jy, p); m.rotation.y = Math.PI / 2 + jr; }
            world.add(m);
          }
        }
      }
    })();
    var crown = sh(new T.Mesh(new T.BoxGeometry(1.92, 0.2, 1.92), new T.MeshStandardMaterial({ color: 0xC9C2B2, roughness: 0.65, transparent: true }))); crown.position.y = 3.7; world.add(crown);
    [[0.3, 0.3], [-0.3, 0.3], [0.3, -0.3], [-0.3, -0.3]].forEach(function (p) {
      var leg = sh(new T.Mesh(new T.BoxGeometry(0.06, 0.34, 0.06), metal)); leg.position.set(p[0], 4.0, p[1]); world.add(leg);
    });
    var lid = sh(new T.Mesh(new T.BoxGeometry(1.06, 0.09, 1.06), metal)); lid.position.y = 4.2; world.add(lid);
    var shC = document.createElement('canvas'); shC.width = shC.height = 256;
    (function () {
      var x = shC.getContext('2d'); x.fillStyle = '#1a1410'; x.fillRect(0, 0, 256, 256);
      for (var yy = 0; yy < 256; yy += 16) {
        for (var xx = -11; xx < 256; xx += 22) {
          var vs = 20 + Math.random() * 14;
          x.fillStyle = 'rgb(' + Math.round(vs + 8) + ',' + Math.round(vs * 0.85) + ',' + Math.round(vs * 0.7) + ')';
          x.fillRect(xx + ((yy / 16) % 2 ? 11 : 0), yy, 20, 13);
        }
        x.fillStyle = 'rgba(0,0,0,0.45)'; x.fillRect(0, yy + 13, 256, 3);
      }
    })();
    var shT = new T.CanvasTexture(shC); shT.wrapS = shT.wrapT = T.RepeatWrapping; shT.repeat.set(3, 4); shT.colorSpace = T.SRGBColorSpace;
    var slopeL = sh(new T.Mesh(new T.BoxGeometry(4.4, 0.16, 5.6), new T.MeshStandardMaterial({ map: shT, roughness: 0.95 })));
    slopeL.rotation.z = 0.42; slopeL.position.set(-1.9, 0.42, 0); world.add(slopeL);
    var slopeR = sh(slopeL.clone()); slopeR.rotation.z = -0.42; slopeR.position.x = 1.9; world.add(slopeR);
    var ridge = sh(new T.Mesh(new T.BoxGeometry(0.36, 0.18, 5.6), dark)); ridge.position.y = 1.26; world.add(ridge);
    var collar = sh(new T.Mesh(new T.BoxGeometry(1.8, 0.16, 1.8), new T.MeshStandardMaterial({ color: 0x6E5230, metalness: 0.75, roughness: 0.35 }))); collar.position.y = 1.5; world.add(collar);

    /* square brick shaft — the real inside of the chimney */
    var hearthFloor = new T.Mesh(new T.BoxGeometry(1.7, 0.12, 1.7), new T.MeshStandardMaterial({ color: 0x241A10, roughness: 1 }));
    hearthFloor.position.y = -6.32; world.add(hearthFloor);
    (function () {
      var inner = 0.55, bd = 0.13, bh = 0.24, bl = 0.5, gap = 0.035;
      var span = inner + bd / 2;
      var geo = new T.BoxGeometry(bl, bh, bd);
      var mats = [], mi;
      for (mi = 0; mi < 6; mi++) {
        var vv = 34 + mi * 8;
        mats.push(new T.MeshStandardMaterial({ color: 'rgb(' + (vv + 16) + ',' + Math.round(vv * 0.66) + ',' + Math.round(vv * 0.4) + ')', roughness: 0.95 }));
      }
      var creo = new T.MeshStandardMaterial({ color: 0x0D0A06, roughness: 0.4, metalness: 0.3 });
      var topY = 3.4, botY = -5.2, step = bh + gap, rows = Math.floor((topY - botY) / step);
      var liner = new T.Mesh(new T.BoxGeometry(span * 2 + bd + 0.05, topY - botY + 0.3, span * 2 + bd + 0.05),
        new T.MeshStandardMaterial({ color: 0x060402, roughness: 1, side: T.BackSide }));
      liner.position.y = (topY + botY) / 2; world.add(liner);
      for (var r = 0; r < rows; r++) {
        var y = topY - r * step - bh / 2;
        var sooty = r < rows * 0.5;
        var shift = (r % 2) ? (bl + gap) / 2 : 0;
        for (var px = -inner - bl / 2; px <= inner + bl / 2; px += bl + gap) {
          var p = px + shift;
          if (p < -inner - bl * 0.7 || p > inner + bl * 0.7) continue;
          for (var w = 0; w < 4; w++) {
            var mat = (sooty && Math.random() < 0.6) ? creo : mats[(r * 7 + w * 3 + Math.round(Math.abs(p) * 10)) % 6];
            var m = new T.Mesh(geo, mat);
            if (w === 0) { m.position.set(p, y, -span); }
            else if (w === 1) { m.position.set(p, y, span); }
            else if (w === 2) { m.position.set(-span, y, p); m.rotation.y = Math.PI / 2; }
            else { m.position.set(span, y, p); m.rotation.y = Math.PI / 2; }
            world.add(m);
          }
        }
      }
    })();
    var shaft1 = new T.PointLight(EMBER, 1.4, 5); shaft1.position.set(0, 1.4, 0); world.add(shaft1);
    var shaft2 = new T.PointLight(EMBER, 2.4, 7); shaft2.position.set(0, -3.6, 0); world.add(shaft2);
    var fireCore = new T.Sprite(new T.SpriteMaterial({ map: glowTex(T, '255,140,60'), transparent: true, depthWrite: false }));
    fireCore.scale.setScalar(3.8); fireCore.position.set(0, -5.8, 0); world.add(fireCore);
    var fire = new T.PointLight(0xFF8C46, 3.4, 10); fire.position.set(0, -5.5, 0); world.add(fire);
    var ray = new T.Sprite(new T.SpriteMaterial({ map: glowTex(T, '255,170,90'), transparent: true, depthWrite: false, opacity: 0 }));
    ray.scale.set(1.6, 5, 1); ray.position.set(0, 5.6, 0); world.add(ray);
    /* real firebox: logs + flames */
    var logA = new T.Mesh(new T.CylinderGeometry(0.14, 0.14, 1.1, 10), new T.MeshStandardMaterial({ color: 0x4A3018, roughness: 0.9 }));
    logA.rotation.z = Math.PI / 2; logA.rotation.y = 0.4; logA.position.set(0, -6.15, 0); world.add(logA);
    var logB = logA.clone(); logB.rotation.y = -0.5; logB.position.y = -5.95; world.add(logB);
    var flames = [];
    for (var fi2 = 0; fi2 < 3; fi2++) {
      var fl = new T.Sprite(new T.SpriteMaterial({ map: glowTex(T, fi2 ? '255,140,60' : '255,190,90'), transparent: true, depthWrite: false }));
      fl.position.set((fi2 - 1) * 0.22, -5.75 + fi2 * 0.08, 0); fl.scale.setScalar(0.7); world.add(fl); flames.push(fl);
    }
    /* technician's lamp inside the flue */
    var lamp = new T.PointLight(0xFFE0B8, 0, 4.5); world.add(lamp);

    /* particles */
    var eTex = glowTex(T, '232,98,44');
    function makePoints(n, box, size, color, opacity) {
      var geo = new T.BufferGeometry(), pos = new Float32Array(n * 3), seed = new Float32Array(n);
      for (var i = 0; i < n; i++) {
        pos[i * 3] = (Math.random() - 0.5) * box[0];
        pos[i * 3 + 1] = (Math.random() - 0.5) * box[1];
        pos[i * 3 + 2] = (Math.random() - 0.5) * box[2];
        seed[i] = Math.random();
      }
      geo.setAttribute('position', new T.BufferAttribute(pos, 3));
      var pts = new T.Points(geo, new T.PointsMaterial({ map: eTex, size: size, transparent: true, opacity: opacity, depthWrite: false, blending: T.AdditiveBlending, color: color }));
      pts.userData = { seed: seed, box: box };
      return pts;
    }
    var outEmbers = makePoints(90, [28, 15, 28], 0.15, 0xFF9A5C, 0.7); outEmbers.position.y = 3; scene.add(outEmbers);
    var inSparks = makePoints(70, [1.05, 10.5, 1.05], 0.07, 0xFFB05C, 0.85); inSparks.position.y = -1.3; world.add(inSparks);
    var snow = makePoints(380, [46, 22, 46], 0.1, 0xF5EFE4, 0); snow.material.blending = T.NormalBlending; snow.position.y = 4; scene.add(snow);

    var sTex = glowTex(T, '215,205,188');
    var puffs = [];
    for (var k = 0; k < 20; k++) {
      var sp = new T.Sprite(new T.SpriteMaterial({ map: sTex, transparent: true, opacity: 0, depthWrite: false }));
      sp.userData.off = Math.random(); scene.add(sp); puffs.push(sp);
    }

    /* letterbox bars removed */
    var grain = document.createElement('canvas');
    grain.width = 256; grain.height = 256;
    grain.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;z-index:54;pointer-events:none;opacity:0.08;mix-blend-mode:overlay';
    document.body.appendChild(grain);
    (function () {
      var gx = grain.getContext('2d'), tiles = [], i, p;
      for (i = 0; i < 3; i++) { var d = gx.createImageData(256, 256); for (p = 0; p < d.data.length; p += 4) { var v = Math.random() * 255; d.data[p] = v; d.data[p + 1] = v; d.data[p + 2] = v; d.data[p + 3] = 255; } tiles.push(d); }
      var fi = 0; setInterval(function () { gx.putImageData(tiles[fi = (fi + 1) % 3], 0, 0); }, 90);
    })();
    var vig = document.createElement('div');
    vig.style.cssText = 'position:fixed;inset:0;z-index:53;pointer-events:none;background:radial-gradient(120% 92% at 50% 50%,transparent 58%,rgba(0,0,0,0.5) 100%)';
    document.body.appendChild(vig);
    var coverEls = null, coverTick = 0;
    function updateBars() {}

    /* camera path: pos, look, fog, fov */
    var KF = [
      { p: 0.00, pos: [6.4, 3.2, 9.4], look: [0, 1.8, 0], fog: 0.028, fov: 38 },
      { p: 0.14, pos: [3.4, 2.4, 5.8], look: [0, 2.6, 0], fog: 0.032, fov: 42 },
      { p: 0.30, pos: [1.1, 6.6, 2.4], look: [0, 4.0, 0], fog: 0.042, fov: 47 },
      { p: 0.42, pos: [0, 4.55, 0.02], look: [0, 3.0, 0], fog: 0.06, fov: 53 },
      { p: 0.56, pos: [0, 1.4, 0.02], look: [0, -1.6, 0], fog: 0.1, fov: 58 },
      { p: 0.70, pos: [0, -2.6, 0.02], look: [0, -5.8, 0], fog: 0.13, fov: 60 },
      { p: 0.80, pos: [2.6, 0.2, 5.4], look: [0, 0.8, 0], fog: 0.05, fov: 46 },
      { p: 0.90, pos: [5.5, 3.6, 8.6], look: [0, 2.0, 0], fog: 0.03, fov: 38 },
      { p: 1.00, pos: [8.8, 7.0, 13.0], look: [0, 2.6, 0], fog: 0.02, fov: 33 }
    ];
    var v3a = new T.Vector3(), v3b = new T.Vector3(), lookCur = new T.Vector3(0, 1.8, 0);
    function sampleKF(p) {
      var i = 0;
      while (i < KF.length - 2 && p > KF[i + 1].p) i++;
      var a = KF[i], b = KF[i + 1];
      var t = smoothstep(a.p, b.p, p);
      v3a.set(a.pos[0] + (b.pos[0] - a.pos[0]) * t, a.pos[1] + (b.pos[1] - a.pos[1]) * t, a.pos[2] + (b.pos[2] - a.pos[2]) * t);
      v3b.set(a.look[0] + (b.look[0] - a.look[0]) * t, a.look[1] + (b.look[1] - a.look[1]) * t, a.look[2] + (b.look[2] - a.look[2]) * t);
      return { fog: a.fog + (b.fog - a.fog) * t, fov: a.fov + (b.fov - a.fov) * t };
    }

    var mouseX = 0, mouseY = 0;
    addEventListener('pointermove', function (e) {
      mouseX = (e.clientX / innerWidth - 0.5); mouseY = (e.clientY / innerHeight - 0.5);
    }, { passive: true });
    function size() {
      renderer.setSize(innerWidth, innerHeight, false);
      cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix();
    }
    addEventListener('resize', size); size();

    var clock = new T.Clock(), t = 0, prog = 0, smX = 0, smY = 0, frameFlip = false;
    function frame() {
      requestAnimationFrame(frame);
      if (document.hidden || window.__pfWorldPaused) return;
      frameFlip = !frameFlip; if (frameFlip) return; /* ~30fps */
      var dt = Math.min(clock.getDelta(), 0.05); t += dt;
      var max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
      var target = Math.max(0, Math.min(1, (window.scrollY || 0) / max));
      prog += (target - prog) * Math.min(1, dt * 5.5);
      var kf = sampleKF(prog);

      /* day → night */
      var nightK = smoothstep(0.3, 0.68, prog);
      scene.fog.density = kf.fog;
      scene.fog.color.lerpColors(duskC, nightC, nightK);
      scene.background.copy(scene.fog.color);
      duskDome.material.opacity = 1 - nightK;
      nightDome.material.opacity = nightK;
      stars.material.opacity = nightK * 0.9 * (0.8 + 0.2 * Math.sin(t * 2));
      sun.position.y = 2.2 - nightK * 7;
      sun.material.opacity = 0.95 - nightK * 0.85;
      moon.position.y = -2 + smoothstep(0.55, 0.85, prog) * 13;
      moon.material.opacity = smoothstep(0.6, 0.85, prog) * 0.9;
      moonLight.intensity = nightK * 1.05;
      key.intensity = 2.1 - nightK * 1.2;
      amb.intensity = 0.68 - nightK * 0.2;

      /* camera */
      smX += (mouseX - smX) * Math.min(1, dt * 4);
      smY += (mouseY - smY) * Math.min(1, dt * 4);
      cam.fov += (kf.fov - cam.fov) * Math.min(1, dt * 5); cam.updateProjectionMatrix();
      cam.position.set(v3a.x + smX * 0.7, v3a.y - smY * 0.5, v3a.z);
      lookCur.lerp(v3b, Math.min(1, dt * 7));
      cam.lookAt(lookCur);

      world.rotation.y = t * 0.035;
      ray.material.opacity = smoothstep(0.28, 0.4, prog) * (1 - smoothstep(0.46, 0.55, prog)) * 0.55;
      var inTun = smoothstep(0.5, 0.56, prog) * (1 - smoothstep(0.72, 0.78, prog));
      fire.intensity = 3.0 + Math.sin(t * 9) * 0.6 + (Math.random() - 0.5) * 0.6 + inTun * 1.6;
      shaft2.intensity = 2.0 + Math.sin(t * 7 + 2) * 0.5;
      fireCore.scale.setScalar((3.8 + Math.sin(t * 6) * 0.35) * (1 + inTun * 0.35));
      lamp.intensity = inTun * 3.2;
      lamp.position.set(0.1, cam.position.y - 1.1, 0.1);
      var hideCap = smoothstep(0.44, 0.52, prog) * (1 - smoothstep(0.74, 0.8, prog));
      crown.material.opacity = 1 - hideCap;
      metal.opacity = 1 - hideCap;
      for (var f2 = 0; f2 < flames.length; f2++) flames[f2].scale.setScalar(0.55 + 0.25 * Math.sin(t * (7 + f2 * 2.3) + f2) + f2 * 0.12);

      /* particles */
      [outEmbers, inSparks].forEach(function (pts, which) {
        var arr = pts.geometry.attributes.position.array, sd = pts.userData.seed, box = pts.userData.box;
        for (var i = 0; i < sd.length; i++) {
          arr[i * 3 + 1] += dt * (which ? 1.8 : 0.5) * (0.5 + sd[i]);
          arr[i * 3] += Math.sin(t * 1.5 + sd[i] * 9) * dt * 0.16;
          if (arr[i * 3 + 1] > box[1] / 2) arr[i * 3 + 1] = -box[1] / 2;
        }
        pts.geometry.attributes.position.needsUpdate = true;
      });
      var snowK = smoothstep(0.76, 0.9, prog);
      snow.material.opacity = snowK * 0.85;
      if (snowK > 0.01) {
        var sa = snow.geometry.attributes.position.array, ssd = snow.userData.seed, sb = snow.userData.box;
        for (var j = 0; j < ssd.length; j++) {
          sa[j * 3 + 1] -= dt * (1.1 + ssd[j] * 1.6);
          sa[j * 3] += Math.sin(t * 0.8 + ssd[j] * 12) * dt * 0.5;
          if (sa[j * 3 + 1] < -sb[1] / 2) sa[j * 3 + 1] = sb[1] / 2;
        }
        snow.geometry.attributes.position.needsUpdate = true;
      }
      for (var q = 0; q < puffs.length; q++) {
        var pp = (puffs[q].userData.off + t * 0.07) % 1;
        var fade = pp < 0.15 ? pp / 0.15 : 1 - (pp - 0.15) / 0.85;
        puffs[q].position.set(Math.sin(pp * 5 + q) * 0.5 * pp + pp * 0.8, 4.4 + pp * 3.6, Math.cos(pp * 4 + q) * 0.35 * pp);
        puffs[q].scale.setScalar(0.7 + pp * 3.2);
        puffs[q].material.opacity = 0.2 * fade * (1 - smoothstep(0.4, 0.58, prog));
      }

      if (++coverTick % 8 === 0) updateBars();
      renderer.render(scene, cam);
    }
    frame();
  }

  ready(function () { boot().catch(function (e) { console.warn('world3d failed', e); }); });
})();
