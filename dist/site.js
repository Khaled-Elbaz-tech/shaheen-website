/* Ola Magdy portfolio — cinematic interactions (vanilla, progressive enhancement) */
(function () {
  'use strict';
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var finePointer = window.matchMedia('(pointer: fine)');

  /* ---------- loader ---------- */
  var loader = document.getElementById('loader');
  function hideLoader() { if (loader) loader.classList.add('done'); }
  if (document.readyState === 'complete') { setTimeout(hideLoader, 350); }
  else {
    window.addEventListener('load', function () { setTimeout(hideLoader, 350); });
    setTimeout(hideLoader, 3200); /* safety */
  }

  /* ---------- scroll progress ---------- */
  var bar = document.getElementById('progressBar');
  var ticking = false;
  function progress() {
    ticking = false;
    if (!bar) return;
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    bar.style.transform = 'scaleX(' + (max > 0 ? (h.scrollTop / max) : 0) + ')';
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(progress); }
  }, { passive: true });
  progress();

  /* ---------- scroll reveals ---------- */
  if ('IntersectionObserver' in window && !reduced.matches) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('rv-on'); io.unobserve(en.target); }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px 30px 0px' });
    document.querySelectorAll('[data-rv]').forEach(function (el) { io.observe(el); });
  } else {
    document.querySelectorAll('[data-rv]').forEach(function (el) { el.classList.add('rv-on'); });
  }

  /* ---------- parallax ---------- */
  var layers = Array.prototype.slice.call(document.querySelectorAll('[data-parallax]'));
  var pScheduled = false;
  function parallax() {
    pScheduled = false;
    if (reduced.matches || window.innerWidth < 700 || !layers.length) return;
    var vh = window.innerHeight;
    layers.forEach(function (layer) {
      var f = parseFloat(layer.getAttribute('data-parallax')) || 0.2;
      var r = layer.parentElement.getBoundingClientRect();
      if (r.bottom > 0 && r.top < vh) {
        var p = Math.min(1, Math.max(0, -r.top / r.height));
        var img = layer.querySelector('img');
        if (img) img.style.transform = 'scale(1.08) translateY(' + (p * f * 100).toFixed(2) + '%)';
      }
    });
  }
  if (layers.length) {
    window.addEventListener('scroll', function () {
      if (!pScheduled) { pScheduled = true; requestAnimationFrame(parallax); }
    }, { passive: true });
    window.addEventListener('resize', parallax);
    parallax();
  }

  /* ---------- magnetic buttons ---------- */
  if (finePointer.matches && !reduced.matches) {
    document.querySelectorAll('[data-magnetic]').forEach(function (btn) {
      btn.addEventListener('pointermove', function (ev) {
        var r = btn.getBoundingClientRect();
        var x = (ev.clientX - r.left - r.width / 2) / r.width;
        var y = (ev.clientY - r.top - r.height / 2) / r.height;
        btn.style.transform = 'translate(' + (x * 10).toFixed(1) + 'px,' + (y * 8).toFixed(1) + 'px)';
      });
      btn.addEventListener('pointerleave', function () { btn.style.transform = ''; });
    });
  }

  /* ---------- study explorer ---------- */
  document.querySelectorAll('.explorer').forEach(function (exp) {
    var thumbs = Array.prototype.slice.call(exp.querySelectorAll('[data-exp-src]'));
    var filters = Array.prototype.slice.call(exp.querySelectorAll('[data-exp-filter]'));
    var main = exp.querySelector('.exp-main');
    var mainImg = main.querySelector('img');
    var caption = exp.querySelector('[data-exp-caption]');
    var count = exp.querySelector('[data-exp-count]');
    function visible() { return thumbs.filter(function (t) { return !t.hidden; }); }
    function select(btn) {
      thumbs.forEach(function (t) { t.setAttribute('aria-pressed', String(t === btn)); });
      mainImg.style.opacity = '0';
      var src = btn.getAttribute('data-exp-src');
      var cap = btn.getAttribute('data-exp-cap');
      setTimeout(function () {
        mainImg.src = src; mainImg.alt = cap; mainImg.removeAttribute('width'); mainImg.removeAttribute('height');
        mainImg.style.opacity = '1';
      }, 160);
      main.href = src;
      main.setAttribute('aria-label', 'Enlarge: ' + cap);
      if (caption) caption.textContent = cap;
      var vis = visible();
      if (count) count.textContent = String(vis.indexOf(btn) + 1).padStart(2, '0') + ' / ' + String(vis.length).padStart(2, '0');
      btn.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: reduced.matches ? 'auto' : 'smooth' });
    }
    thumbs.forEach(function (btn) { btn.addEventListener('click', function () { select(btn); }); });
    filters.forEach(function (f) {
      f.addEventListener('click', function () {
        filters.forEach(function (x) { x.setAttribute('aria-pressed', String(x === f)); });
        var cat = f.getAttribute('data-exp-filter');
        thumbs.forEach(function (t) {
          t.hidden = cat !== 'All' && t.getAttribute('data-exp-cat') !== cat;
        });
        var cur = thumbs.find(function (t) { return t.getAttribute('aria-pressed') === 'true' && !t.hidden; });
        select(cur || visible()[0]);
      });
    });
  });

  /* ---------- image viewer ---------- */
  var viewer = document.querySelector('.viewer');
  if (viewer && typeof viewer.showModal === 'function') {
    var vImg = viewer.querySelector('figure img');
    var vCap = viewer.querySelector('figcaption');
    var vOrig = viewer.querySelector('.viewer-original');
    var fig = viewer.querySelector('figure');
    var scale = 1, ox = 0, oy = 0, drag = null;
    function paint() { vImg.style.transform = 'translate(' + ox + 'px,' + oy + 'px) scale(' + scale + ')'; }
    function reset() { scale = 1; ox = 0; oy = 0; paint(); }
    function open(src, alt) {
      vImg.src = src; vImg.alt = alt; vCap.textContent = alt; vOrig.href = src; reset();
      viewer.showModal(); document.body.classList.add('viewer-open');
    }
    function zoom(d) {
      scale = Math.min(4, Math.max(1, scale + d));
      if (scale === 1) { ox = 0; oy = 0; }
      paint();
    }
    document.querySelectorAll('.enlarge-image').forEach(function (link) {
      link.addEventListener('click', function (ev) {
        if (ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.altKey) return;
        ev.preventDefault();
        var s = link.querySelector('img');
        open(link.href, s ? s.alt : '');
      });
    });
    viewer.querySelector('.viewer-close').addEventListener('click', function () { viewer.close(); });
    viewer.addEventListener('close', function () { document.body.classList.remove('viewer-open'); reset(); });
    viewer.querySelectorAll('[data-viewer]').forEach(function (b) {
      b.addEventListener('click', function () {
        var a = b.getAttribute('data-viewer');
        if (a === 'zin') zoom(0.5);
        else if (a === 'zout') zoom(-0.5);
        else if (a === 'reset') reset();
      });
    });
    viewer.addEventListener('keydown', function (ev) {
      if (ev.key === '+' || ev.key === '=') { ev.preventDefault(); zoom(0.5); }
      else if (ev.key === '-' || ev.key === '_') { ev.preventDefault(); zoom(-0.5); }
      else if (ev.key === '0') { reset(); }
    });
    vImg.addEventListener('dragstart', function (ev) { ev.preventDefault(); });
    fig.addEventListener('pointerdown', function (ev) {
      if (scale === 1 || ev.target !== vImg) return;
      drag = { px: ev.clientX, py: ev.clientY, ox: ox, oy: oy };
      fig.setPointerCapture(ev.pointerId);
    });
    fig.addEventListener('pointermove', function (ev) {
      if (!drag) return;
      var mx = vImg.clientWidth * (scale - 1) / 2;
      var my = vImg.clientHeight * (scale - 1) / 2;
      ox = Math.max(-mx, Math.min(mx, drag.ox + ev.clientX - drag.px));
      oy = Math.max(-my, Math.min(my, drag.oy + ev.clientY - drag.py));
      paint();
    });
    fig.addEventListener('pointerup', function () { drag = null; });
    fig.addEventListener('pointercancel', function () { drag = null; });
  }

  /* ---------- project index search ---------- */
  var search = document.getElementById('project-search');
  if (search) {
    var cards = Array.prototype.slice.call(document.querySelectorAll('[data-cat-entry]'));
    var empty = document.querySelector('.no-results');
    var status = document.querySelector('.search-status');
    var norm = function (t) { return t.toLocaleLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, ''); };
    search.addEventListener('input', function () {
      var q = norm(search.value.trim());
      var vis = 0;
      cards.forEach(function (c) {
        var hit = !q || norm((c.getAttribute('data-search') || '') + ' ' + c.textContent).indexOf(q) !== -1;
        c.hidden = !hit;
        if (hit) vis++;
      });
      if (empty) empty.hidden = vis > 0;
      if (status) status.textContent = q ? (vis + ' matching ' + (vis === 1 ? 'project' : 'projects')) : '';
    });
  }

  reduced.addEventListener('change', function () {
    if (reduced.matches) {
      document.querySelectorAll('[data-parallax] img').forEach(function (i) { i.style.removeProperty('transform'); });
    }
  });
})();
