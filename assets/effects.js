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

  function scanCounters() {
    document.querySelectorAll("[data-target]").forEach(function (el) {
      var key = el.getAttribute("data-target");
      if (el.getAttribute("data-counted") !== key) {
        el.setAttribute("data-counted", key);
        animate(el);
      }
    });
  }

  var hovering = false;
  var activeLink = null;

  function dockParts() {
    var dock = document.querySelector(".nav-dock");
    if (!dock) return null;
    return { dock: dock, glow: dock.querySelector(".nav-glow"), nav: dock.querySelector(".nav") };
  }

  function placeGlow(link) {
    var parts = dockParts();
    if (!parts || !parts.glow) return;
    if (!link) {
      parts.glow.style.opacity = "0";
      return;
    }
    var dockRect = parts.dock.getBoundingClientRect();
    var linkRect = link.getBoundingClientRect();
    parts.glow.style.width = linkRect.width + "px";
    parts.glow.style.transform = "translateX(" + (linkRect.left - dockRect.left) + "px)";
    parts.glow.style.opacity = "1";
  }

  function refreshActive() {
    var parts = dockParts();
    if (!parts || !parts.nav) return;
    var links = [].slice.call(parts.nav.querySelectorAll(".nav-link"));
    var current = null;
    links.forEach(function (link) {
      var id = (link.getAttribute("href") || "").replace("#", "");
      var section = id ? document.getElementById(id) : null;
      if (section && section.getBoundingClientRect().top <= window.innerHeight * 0.42) current = link;
    });
    links.forEach(function (link) { link.classList.toggle("is-active", link === current); });
    activeLink = current;
    if (!hovering) placeGlow(current);
  }

  var queued = false;
  function schedule() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () {
      queued = false;
      scanCounters();
      refreshActive();
    });
  }

  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["data-target"] });
  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);

  document.addEventListener("pointerover", function (event) {
    var link = event.target && event.target.closest ? event.target.closest(".nav-link") : null;
    var inDock = event.target && event.target.closest ? event.target.closest(".nav-dock") : null;
    if (inDock) hovering = true;
    if (link) placeGlow(link);
  });
  document.addEventListener("pointerout", function (event) {
    var dock = event.target && event.target.closest ? event.target.closest(".nav-dock") : null;
    if (dock && !(event.relatedTarget && dock.contains(event.relatedTarget))) {
      hovering = false;
      placeGlow(activeLink);
    }
  });
  document.addEventListener("click", function (event) {
    var link = event.target && event.target.closest ? event.target.closest(".nav-link") : null;
    if (!link) return;
    link.classList.remove("pulse");
    void link.offsetWidth;
    link.classList.add("pulse");
    setTimeout(function () { link.classList.remove("pulse"); }, 750);
  });

  var activeCard = null;
  document.addEventListener("pointermove", function (event) {
    var card = event.target && event.target.closest ? event.target.closest(".tilt") : null;
    if (activeCard && activeCard !== card) {
      activeCard.style.transform = "";
      activeCard = null;
    }
    if (!card || reduce) return;
    activeCard = card;
    var rect = card.getBoundingClientRect();
    var x = (event.clientX - rect.left) / rect.width - 0.5;
    var y = (event.clientY - rect.top) / rect.height - 0.5;
    card.style.transform = "perspective(900px) rotateX(" + (-y * 10).toFixed(2) + "deg) rotateY(" + (x * 10).toFixed(2) + "deg) translateY(-6px)";
    card.style.setProperty("--mx", ((x + 0.5) * 100).toFixed(1) + "%");
    card.style.setProperty("--my", ((y + 0.5) * 100).toFixed(1) + "%");
  });

  document.addEventListener("pointermove", function (event) {
    if (reduce || window.scrollY > 900) return;
    var logo = document.querySelector(".hero-logo");
    if (!logo) return;
    var x = event.clientX / window.innerWidth - 0.5;
    var y = event.clientY / window.innerHeight - 0.5;
    logo.style.transform = "perspective(1100px) rotateY(" + (x * 12).toFixed(2) + "deg) rotateX(" + (-y * 9).toFixed(2) + "deg)";
  });

  if (reduce) return;

  var canvas = document.createElement("canvas");
  canvas.className = "sparkle-canvas";
  var ctx = canvas.getContext("2d");
  function attach() { document.body.appendChild(canvas); }
  if (document.body) attach(); else document.addEventListener("DOMContentLoaded", attach);

  var particles = [];
  var running = false;
  var palette = ["#8b6cff", "#ff6fb1", "#4fd8ff", "#ffc65c", "#38f2b3", "#ffffff"];

  function resize() {
    var ratio = window.devicePixelRatio || 1;
    canvas.width = window.innerWidth * ratio;
    canvas.height = window.innerHeight * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  }
  resize();
  window.addEventListener("resize", resize);

  function spawn(x, y, count, speed, size) {
    for (var i = 0; i < count; i++) {
      var angle = Math.random() * Math.PI * 2;
      var velocity = (0.4 + Math.random()) * speed;
      particles.push({
        x: x,
        y: y,
        vx: Math.cos(angle) * velocity,
        vy: Math.sin(angle) * velocity - 0.2,
        life: 1,
        decay: 0.02 + Math.random() * 0.02,
        size: size * (0.6 + Math.random() * 0.9),
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
      p.vx *= 0.985;
      p.vy *= 0.985;
      p.life -= p.decay;
      var radius = p.size * Math.max(p.life, 0);
      if (radius <= 0.05) return;
      ctx.globalAlpha = Math.max(p.life, 0);
      ctx.fillStyle = p.color;
      ctx.shadowColor = p.color;
      ctx.shadowBlur = 12;
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
    if (now - last < 34) return;
    last = now;
    spawn(event.clientX, event.clientY, 1, 1.1, 2.6);
  });
  document.addEventListener("pointerdown", function (event) {
    spawn(event.clientX, event.clientY, 22, 3.4, 3.4);
  });
})();