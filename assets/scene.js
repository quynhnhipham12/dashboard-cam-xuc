(function () {
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var canvas = document.createElement("canvas");
  canvas.id = "vl-scene";
  var ctx = canvas.getContext("2d");

  var NX = 56, NZ = 34, X0 = -27, DX = 0.98, Z0 = 3.4, DZ = 1.15;
  var ZMAX = Z0 + NZ * DZ;
  var COLOR_STEPS = 12, FOG_STEPS = 6;
  var PALETTE = [[255, 105, 160], [135, 160, 255], [64, 240, 188]];
  var W = 0, H = 0, dpr = 1, focal = 800;
  var mouse = { x: 0, y: 0, tx: 0, ty: 0 };
  var ripples = [];
  var particles = [];
  var sprites = [];
  var heights = new Float32Array((NX + 1) * (NZ + 1));
  var slowFrames = 0;
  var lowQuality = false;
  var lastTime = 0;

  function attach() { document.body.insertBefore(canvas, document.body.firstChild); }
  if (document.body) attach(); else document.addEventListener("DOMContentLoaded", attach);

  function colorAt(t) {
    t = Math.min(Math.max(t, 0), 0.999);
    var scaled = t * 2;
    var i = Math.floor(scaled);
    var f = scaled - i;
    var a = PALETTE[i], b = PALETTE[i + 1];
    return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
  }

  var colorTable = [];
  for (var c = 0; c < COLOR_STEPS; c++) colorTable.push(colorAt((c + 0.5) / COLOR_STEPS).map(Math.round));

  function makeSprite(rgb) {
    var size = 64;
    var off = document.createElement("canvas");
    off.width = off.height = size;
    var g = off.getContext("2d");
    var grad = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
    grad.addColorStop(0, "rgba(255,255,255,1)");
    grad.addColorStop(0.18, "rgba(" + rgb.join(",") + ",0.95)");
    grad.addColorStop(0.5, "rgba(" + rgb.join(",") + ",0.28)");
    grad.addColorStop(1, "rgba(" + rgb.join(",") + ",0)");
    g.fillStyle = grad;
    g.fillRect(0, 0, size, size);
    return off;
  }
  PALETTE.forEach(function (rgb) { sprites.push(makeSprite(rgb)); });

  function resetParticle(p, initial) {
    p.x = (Math.random() - 0.5) * 48;
    p.y = initial ? 0.6 + Math.random() * 9 : 0.4;
    p.z = Z0 + 1 + Math.random() * (ZMAX - Z0 - 3);
    p.vx = (Math.random() - 0.5) * 0.5;
    p.vy = 0.12 + Math.random() * 0.3;
    var r = Math.random();
    p.c = r < 0.45 ? 2 : (r < 0.8 ? 1 : 0);
    p.s = 0.65 + Math.random();
    return p;
  }
  for (var i = 0; i < 120; i++) particles.push(resetParticle({}, true));

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 1.25);
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    focal = Math.max(W * 0.6, H * 0.85);
  }
  resize();
  window.addEventListener("resize", resize);
  window.addEventListener("pointermove", function (e) {
    mouse.tx = (e.clientX / W - 0.5) * 2;
    mouse.ty = (e.clientY / H - 0.5) * 2;
  });

  var camX = 0, camH = 4.3, horizon = 0;

  window.addEventListener("pointerdown", function (e) {
    if (e.clientY <= horizon + 8) return;
    var z = focal * camH / (e.clientY - horizon);
    z = Math.min(Math.max(z, Z0 + 1), ZMAX - 2);
    var x = (e.clientX - W / 2) * z / focal + camX;
    ripples.push({ x: x, z: z, t0: performance.now() / 1000 });
    if (ripples.length > 6) ripples.shift();
  });

  function terrain(x, z, t) {
    var edge = Math.min(1, Math.abs(x) / 17);
    var amp = 0.5 + 1.6 * edge * edge;
    var h = amp * (0.62 * Math.sin(x * 0.42 + t * 0.9) * Math.cos(z * 0.33 - t * 0.7) + 0.38 * Math.sin(x * 0.19 - z * 0.27 + t * 0.55));
    h += 0.16 * Math.sin(z * 0.85 + t * 1.4);
    for (var k = 0; k < ripples.length; k++) {
      var r = ripples[k];
      var age = t - r.t0;
      if (age > 5) continue;
      var d = Math.sqrt((x - r.x) * (x - r.x) + (z - r.z) * (z - r.z));
      var ring = d - age * 6.2;
      h += 1.7 * Math.exp(-age * 0.75) * Math.exp(-(ring * ring) / 3.4);
    }
    return h;
  }

  var buckets = [];
  for (var b = 0; b < COLOR_STEPS * FOG_STEPS; b++) buckets.push([]);

  function addSegment(x1, y1, h1, x2, y2, h2, fogIndex) {
    if ((y1 > H + 60 && y2 > H + 60) || (x1 < -80 && x2 < -80) || (x1 > W + 80 && x2 > W + 80)) return;
    var ci = Math.floor(Math.min(Math.max(((h1 + h2) * 0.5 + 1.9) / 3.8, 0), 0.999) * COLOR_STEPS);
    buckets[ci * FOG_STEPS + fogIndex].push(x1, y1, x2, y2);
  }

  function draw(now) {
    var t = now / 1000;
    mouse.x += (mouse.tx - mouse.x) * 0.06;
    mouse.y += (mouse.ty - mouse.y) * 0.06;
    camX = mouse.x * 3.4;
    camH = 4.3 - mouse.y * 0.7;
    horizon = H * 0.47 + mouse.y * H * 0.022 - Math.min(window.scrollY, 1800) * 0.045;

    ctx.clearRect(0, 0, W, H);
    ctx.globalCompositeOperation = "source-over";
    var glow = ctx.createRadialGradient(W / 2, horizon, 0, W / 2, horizon, W * 0.62);
    glow.addColorStop(0, "rgba(139,108,255,0.30)");
    glow.addColorStop(0.45, "rgba(255,111,177,0.10)");
    glow.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, W, H);

    var zs = new Float32Array(NZ + 1);
    var row = NX + 1;
    for (var iz = 0; iz <= NZ; iz++) {
      var z = Z0 + iz * DZ;
      zs[iz] = z;
      for (var ix = 0; ix <= NX; ix++) heights[iz * row + ix] = terrain(X0 + ix * DX, z, t);
    }

    for (var bi = 0; bi < buckets.length; bi++) buckets[bi].length = 0;
    var xs = new Float32Array(NX + 1);
    var sxs = new Float32Array(NX + 1), sys = new Float32Array(NX + 1);
    var prevSx = null, prevSy = null;
    var colStep = lowQuality ? 2 : 1;
    for (var jz = 0; jz <= NZ; jz++) {
      var zz = zs[jz];
      var scale = focal / zz;
      var fog = Math.min(Math.max(1 - (zz - Z0) / (ZMAX - Z0), 0), 0.999);
      var fogIndex = Math.floor(fog * FOG_STEPS);
      var curSx = new Float32Array(NX + 1), curSy = new Float32Array(NX + 1);
      for (var kx = 0; kx <= NX; kx++) {
        var h = heights[jz * row + kx];
        curSx[kx] = W / 2 + (X0 + kx * DX - camX) * scale;
        curSy[kx] = horizon + (camH - h) * scale;
      }
      for (var sx = 0; sx < NX; sx++) addSegment(curSx[sx], curSy[sx], heights[jz * row + sx], curSx[sx + 1], curSy[sx + 1], heights[jz * row + sx + 1], fogIndex);
      if (prevSx) {
        for (var cx = 0; cx <= NX; cx += colStep) addSegment(prevSx[cx], prevSy[cx], heights[(jz - 1) * row + cx], curSx[cx], curSy[cx], heights[jz * row + cx], fogIndex);
      }
      prevSx = curSx;
      prevSy = curSy;
    }

    ctx.globalCompositeOperation = "lighter";
    ctx.lineCap = "round";
    for (var ci2 = 0; ci2 < COLOR_STEPS; ci2++) {
      var rgb = colorTable[ci2];
      for (var fi = 0; fi < FOG_STEPS; fi++) {
        var list = buckets[ci2 * FOG_STEPS + fi];
        if (!list.length) continue;
        ctx.beginPath();
        for (var q = 0; q < list.length; q += 4) {
          ctx.moveTo(list[q], list[q + 1]);
          ctx.lineTo(list[q + 2], list[q + 3]);
        }
        ctx.strokeStyle = "rgba(" + rgb[0] + "," + rgb[1] + "," + rgb[2] + "," + (0.07 + fi * 0.07).toFixed(3) + ")";
        ctx.lineWidth = 0.7 + fi * 0.26;
        ctx.stroke();
      }
    }

    var dt = Math.min(Math.max(now - lastTime, 0), 60) / 1000;
    var count = lowQuality ? 70 : particles.length;
    var proj = [];
    for (var pi = 0; pi < count; pi++) {
      var p = particles[pi];
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      if (p.y > 11 || p.x < -26 || p.x > 26) resetParticle(p, false);
      var s = focal / p.z;
      var px = W / 2 + (p.x - camX) * s;
      var py = horizon + (camH - p.y) * s;
      var pf = Math.min(Math.max(1 - (p.z - Z0) / (ZMAX - Z0), 0), 1);
      var size = Math.max(7, s * 0.4 * p.s);
      ctx.globalAlpha = 0.3 + 0.65 * pf;
      ctx.drawImage(sprites[p.c], px - size / 2, py - size / 2, size, size);
      proj.push(px, py, p.x, p.y, p.z, pf);
    }
    ctx.globalAlpha = 1;
    ctx.lineWidth = 0.9;
    for (var a = 0; a < count; a++) {
      for (var d = a + 1; d < count; d++) {
        var ox = proj[a * 6 + 2] - proj[d * 6 + 2], oy = proj[a * 6 + 3] - proj[d * 6 + 3], oz = proj[a * 6 + 4] - proj[d * 6 + 4];
        var dist = Math.sqrt(ox * ox + oy * oy + oz * oz);
        if (dist < 6.5) {
          var alpha = (1 - dist / 6.5) * 0.2 * Math.min(proj[a * 6 + 5], proj[d * 6 + 5]);
          ctx.strokeStyle = "rgba(190,200,255," + alpha.toFixed(3) + ")";
          ctx.beginPath();
          ctx.moveTo(proj[a * 6], proj[a * 6 + 1]);
          ctx.lineTo(proj[d * 6], proj[d * 6 + 1]);
          ctx.stroke();
        }
      }
    }
    ctx.globalCompositeOperation = "source-over";

    if (lastTime) {
      var frame = now - lastTime;
      slowFrames = frame > 36 ? slowFrames + 1 : Math.max(0, slowFrames - 1);
      if (slowFrames > 50) lowQuality = true;
    }
    lastTime = now;
  }

  if (reduce) {
    draw(2500);
    return;
  }

  function loop(now) {
    if (!document.hidden) draw(now);
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  setTimeout(function () {
    var t = performance.now() / 1000;
    ripples.push({ x: 0, z: 15, t0: t });
    setTimeout(function () { ripples.push({ x: 0, z: 15, t0: performance.now() / 1000 }); }, 380);
  }, 2500);
})();