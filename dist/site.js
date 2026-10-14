/* Ola Magdy portfolio interactions — progressive enhancement.
   Core: loader, scroll progress, reveals, parallax, magnetic, viewer, search.
   GSAP (CDN) enhances hero scrub when available; everything works without it. */
(function () {
  'use strict';
  var RM = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var HOVER = window.matchMedia('(hover: hover)').matches;
  var body = document.body;

  /* ---------- loader ---------- */
  body.classList.add('loading');
  var loaded = false;
  function markLoaded() {
    if (loaded) return; loaded = true;
    body.classList.remove('loading');
    body.classList.add('loaded');
  }
  window.addEventListener('load', function () { setTimeout(markLoaded, RM ? 0 : 550); });
  setTimeout(markLoaded, 3500); // safety

  /* ---------- scroll progress ---------- */
  var bar = document.getElementById('progressBar');
  var ticking = false;
  function updateProgress() {
    ticking = false;
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var p = max > 0 ? (h.scrollTop || body.scrollTop) / max : 0;
    if (bar) bar.style.transform = 'scaleX(' + p.toFixed(4) + ')';
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(updateProgress); }
  }, { passive: true });
  updateProgress();

  /* ---------- scroll reveals ---------- */
  var revealEls = Array.prototype.slice.call(document.querySelectorAll('[data-reveal]'));
  if ('IntersectionObserver' in window && !RM) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---------- parallax (rAF, transform-safe) ---------- */
  var pEls = [];
  if (!RM) {
    document.querySelectorAll('[data-parallax]').forEach(function (el) {
      var inner = el.querySelector('img') || el;
      var scale = 1;
      try {
        var m = window.getComputedStyle(inner).transform;
        if (m && m !== 'none') {
          var v = m.match(/matrix\(([^)]+)\)/);
          if (v) { var n = v[1].split(',').map(parseFloat); scale = Math.sqrt(n[0] * n[0] + n[1] * n[1]) || 1; }
        }
      } catch (err) {}
      pEls.push({ box: el, inner: inner, speed: parseFloat(el.getAttribute('data-parallax')) || 0.2, scale: scale });
    });
  }
  var pTicking = false;
  function updateParallax() {
    pTicking = false;
    var vh = window.innerHeight;
    pEls.forEach(function (p) {
      var r = p.box.getBoundingClientRect();
      if (r.bottom < -vh || r.top > vh * 2) return;
      var y = (r.top + r.height / 2 - vh / 2) * p.speed;
      p.inner.style.transform = 'translate3d(0,' + y.toFixed(1) + 'px,0) scale(' + p.scale + ')';
    });
  }
  function requestParallax() {
    if (!pTicking && pEls.length) { pTicking = true; requestAnimationFrame(updateParallax); }
  }
  window.addEventListener('scroll', requestParallax, { passive: true });
  window.addEventListener('resize', requestParallax);
  requestParallax();

  /* ---------- GSAP enhancements (optional) ---------- */
  if (!RM && window.gsap && window.ScrollTrigger) {
    gsap.registerPlugin(ScrollTrigger);
    var heroContent = document.querySelector('.hero-content');
    if (heroContent) {
      gsap.to(heroContent, {
        y: -70, opacity: 0.25, ease: 'none',
        scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true }
      });
    }
    var pHeroContent = document.querySelector('.p-hero-content');
    if (pHeroContent) {
      gsap.to(pHeroContent, {
        y: -60, ease: 'none',
        scrollTrigger: { trigger: '.p-hero', start: 'top top', end: 'bottom top', scrub: true }
      });
    }
  }

  /* ---------- magnetic hover ---------- */
  if (!RM && HOVER) {
    document.querySelectorAll('[data-magnetic]').forEach(function (el) {
      var strength = 22;
      el.addEventListener('pointermove', function (ev) {
        var r = el.getBoundingClientRect();
        var x = ev.clientX - (r.left + r.width / 2);
        var y = ev.clientY - (r.top + r.height / 2);
        el.style.transition = 'transform .18s cubic-bezier(.16,1,.3,1)';
        el.style.transform = 'translate(' + (x / r.width * strength).toFixed(1) + 'px,' + (y / r.height * strength).toFixed(1) + 'px)';
      });
      el.addEventListener('pointerleave', function () {
        el.style.transition = 'transform .6s cubic-bezier(.16,1,.3,1)';
        el.style.transform = 'translate(0,0)';
      });
    });
  }

  /* ---------- image viewer (keeps direct-image fallback) ---------- */
  var viewer = document.querySelector('.image-viewer');
  if (viewer && typeof viewer.showModal === 'function') {
    var vImg = viewer.querySelector('img');
    var vCap = viewer.querySelector('figcaption');
    var vOrig = viewer.querySelector('.viewer-original');
    document.querySelectorAll('.enlarge-image').forEach(function (link) {
      link.addEventListener('click', function (event) {
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        var source = link.querySelector('img');
        vImg.src = link.href;
        vImg.alt = source ? source.alt : '';
        vCap.textContent = source ? source.alt : '';
        vOrig.href = link.href;
        viewer.showModal();
        body.classList.add('viewer-open');
      });
    });
    viewer.querySelector('.viewer-close').addEventListener('click', function () { viewer.close(); });
    viewer.addEventListener('close', function () { body.classList.remove('viewer-open'); });
    viewer.addEventListener('click', function (event) {
      if (event.target === viewer) viewer.close();
    });
  }

  /* ---------- project index search ---------- */
  var search = document.querySelector('#project-search');
  if (search) {
    var groups = Array.prototype.slice.call(document.querySelectorAll('[data-project-group]'));
    var status = document.querySelector('.search-status');
    var empty = document.querySelector('.register-empty');
    var normalize = function (t) { return t.toLocaleLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, ''); };
    search.addEventListener('input', function () {
      var q = normalize(search.value.trim());
      var visible = 0;
      groups.forEach(function (group) {
        var head = group.querySelector('.register-heading');
        var groupMatch = normalize(head ? head.textContent : '').indexOf(q) !== -1;
        var entries = Array.prototype.slice.call(group.querySelectorAll('.register-entries a'));
        entries.forEach(function (entry) {
          entry.hidden = q !== '' && !groupMatch && normalize(entry.textContent).indexOf(q) === -1;
        });
        group.hidden = !entries.some(function (en) { return !en.hidden; });
        if (!group.hidden) visible++;
      });
      if (empty) empty.hidden = visible > 0;
      if (status) status.textContent = q ? visible + ' matching ' + (visible === 1 ? 'collection' : 'collections') : '';
    });
  }
})();
