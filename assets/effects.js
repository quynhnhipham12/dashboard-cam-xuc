(function () {
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function format(value, decimals, locale) {
    return value.toLocaleString(locale === "vi" ? "vi-VN" : "en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  }

  function writeText(el, text) {
    if (el.firstChild && el.firstChild.nodeType === 3) {
      el.firstChild.nodeValue = text;
    } else {
      el.textContent = text;
    }
  }

  function animate(el) {
    var target = parseFloat(el.getAttribute("data-target"));
    if (isNaN(target)) return;
    var decimals = parseInt(el.getAttribute("data-decimals") || "0", 10);
    var suffix = el.getAttribute("data-suffix") || "";
    var locale = el.getAttribute("data-locale") || "en";
    if (reduce) {
      writeText(el, format(target, decimals, locale) + suffix);
      return;
    }
    var start = performance.now();
    var duration = 1500;
    function tick(now) {
      var progress = Math.min((now - start) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      writeText(el, format(target * eased, decimals, locale) + suffix);
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  var scanQueued = false;
  function scan(resetKey) {
    if (scanQueued) return;
    scanQueued = true;
    requestAnimationFrame(function () {
      scanQueued = false;
      document.querySelectorAll("[data-target]").forEach(function (el) {
        var key = el.getAttribute("data-target");
        if (el.getAttribute("data-counted") !== key) {
          el.setAttribute("data-counted", key);
          animate(el);
        }
      });
    });
  }

  new MutationObserver(function () { scan(); }).observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["data-target"],
  });

  var active = null;
  document.addEventListener("pointermove", function (event) {
    var card = event.target && event.target.closest ? event.target.closest(".tilt") : null;
    if (active && active !== card) {
      active.style.transform = "";
      active = null;
    }
    if (!card || reduce) return;
    active = card;
    var rect = card.getBoundingClientRect();
    var x = (event.clientX - rect.left) / rect.width - 0.5;
    var y = (event.clientY - rect.top) / rect.height - 0.5;
    card.style.transform = "perspective(900px) rotateX(" + (-y * 9).toFixed(2) + "deg) rotateY(" + (x * 9).toFixed(2) + "deg) translateY(-6px)";
    card.style.setProperty("--mx", ((x + 0.5) * 100).toFixed(1) + "%");
    card.style.setProperty("--my", ((y + 0.5) * 100).toFixed(1) + "%");
  });

  if (reduce) return;

  var canvas = document.createElement("canvas");
  canvas.className = "sparkle-canvas";
  document.addEventListener("DOMContentLoaded", function () { document.body.appendChild(canvas); });
  var ctx = canvas.getContext("2d");
  var particles = [];
  var running = false;
  var palette = ["#7c5cff", "#ff5ca8", "#27e0ff", "#ffc65c", "#38f2b3", "#ffffff"];

  function resize() {
    var ratio = window.devicePixelRatio || 1;
    canvas.width = window.innerWidth * ratio;
    canvas.height = window.innerHeight * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  }
  resize();
  window.addEventListener("resize", resize);

  function spawn(x, y) {
    for (var i = 0; i < 2; i++) {
      particles.push({
        x: x,
        y: y,
        vx: (Math.random() - 0.5) * 1.6,
        vy: (Math.random() - 0.5) * 1.6 - 0.4,
        life: 1,
        size: 2 + Math.random() * 3.2,
        color: palette[Math.floor(Math.random() * palette.length)],
      });
    }
    if (!running) {
      running = true;
      requestAnimationFrame(loop);
    }
  }

  function loop() {
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    particles = particles.filter(function (p) { return p.life > 0; });
    particles.forEach(function (p) {
      p.x += p.vx;
      p.y += p.vy;
      p.life -= 0.025;
      ctx.globalAlpha = Math.max(p.life, 0);
      ctx.fillStyle = p.color;
      ctx.shadowColor = p.color;
      ctx.shadowBlur = 12;
      var radius = p.size * Math.max(p.life, 0);
      if (radius <= 0.05) return;
      ctx.beginPath();
      ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.globalAlpha = 1;
    if (particles.length) {
      requestAnimationFrame(loop);
    } else {
      running = false;
    }
  }

  var last = 0;
  document.addEventListener("pointermove", function (event) {
    var now = performance.now();
    if (now - last < 28) return;
    last = now;
    spawn(event.clientX, event.clientY);
  });
})();