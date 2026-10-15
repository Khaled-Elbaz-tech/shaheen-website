/* Ola Magdy — calm interactions. Vanilla JS. Respects prefers-reduced-motion. */
(function(){
"use strict";
var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
var doc = document.documentElement;

/* ---------- header state ---------- */
var header = document.getElementById('siteHeader');
function onScrollHeader(){
  header.classList.toggle('scrolled', window.scrollY > 40);
}
window.addEventListener('scroll', onScrollHeader, {passive:true});
onScrollHeader();

/* ---------- scroll progress hairline ---------- */
var bar = document.getElementById('progressBar');
function onScrollProgress(){
  var h = doc.scrollHeight - window.innerHeight;
  var v = h > 0 ? (window.scrollY / h) : 0;
  bar.style.transform = 'scaleX(' + v + ')';
}
window.addEventListener('scroll', onScrollProgress, {passive:true});
onScrollProgress();

/* ---------- mobile menu ---------- */
var menuBtn = document.getElementById('menuBtn');
var overlay = document.getElementById('menuOverlay');
var lastFocus = null;
function setMenu(open){
  lastFocus = lastFocus || document.activeElement;
  doc.classList.toggle('menu-open', open);
  document.body.classList.toggle('menu-open', open);
  overlay.hidden = !open;
  menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
  menuBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  if(open){
    var first = overlay.querySelector('a');
    if(first) first.focus();
  }else if(lastFocus && lastFocus.focus){
    lastFocus.focus(); lastFocus = null;
  }
}
menuBtn.addEventListener('click', function(){
  setMenu(overlay.hidden);
});
document.addEventListener('keydown', function(ev){
  if(ev.key === 'Escape' && !overlay.hidden) setMenu(false);
});
overlay.addEventListener('click', function(ev){
  if(ev.target.closest('a')) setMenu(false);
});

/* ---------- entrance reveals ---------- */
var rvEls = document.querySelectorAll('[data-rv]');
if('IntersectionObserver' in window && !reduce && rvEls.length){
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if(en.isIntersecting){ en.target.classList.add('in'); io.unobserve(en.target); }
    });
  }, {threshold:.12, rootMargin:'0px 0px -6% 0px'});
  rvEls.forEach(function(el){ io.observe(el); });
}else{
  rvEls.forEach(function(el){ el.classList.add('in'); });
}

/* ---------- lightbox ---------- */
var lb = document.getElementById('lightbox');
if(lb){
  var lbImg = lb.querySelector('.lb-img');
  var lbCap = lb.querySelector('.lb-cap');
  var lbCount = lb.querySelector('.lb-count');
  var items = [], idx = 0, opener = null;

  function collect(group){
    var scope = group ? document.querySelector('[data-lb-group="' + group + '"]') : document;
    return Array.prototype.slice.call(scope.querySelectorAll('[data-lb-item]'));
  }
  function show(i){
    idx = (i + items.length) % items.length;
    var it = items[idx];
    lbImg.src = it.getAttribute('data-full');
    lbImg.alt = it.getAttribute('data-alt') || '';
    lbCap.textContent = it.getAttribute('data-cap') || '';
    lbCount.textContent = (idx + 1) + ' / ' + items.length;
    [lb.querySelector('.lb-prev'), lb.querySelector('.lb-next')].forEach(function(b){
      b.style.display = items.length > 1 ? '' : 'none';
    });
  }
  function open(item){
    opener = document.activeElement;
    items = collect(item.getAttribute('data-lb-group'));
    lb.hidden = false;
    document.body.style.overflow = 'hidden';
    show(items.indexOf(item));
    lb.querySelector('.lb-close').focus();
  }
  function close(){
    lb.hidden = true;
    document.body.style.overflow = '';
    if(opener && opener.focus) opener.focus();
  }
  document.addEventListener('click', function(ev){
    var t = ev.target.closest('[data-lb-item]');
    if(t){ ev.preventDefault(); open(t); return; }
    var c = ev.target.closest('[data-lb]');
    if(c && lb.hidden === false){
      var act = c.getAttribute('data-lb');
      if(act === 'close') close();
      else if(act === 'prev') show(idx - 1);
      else if(act === 'next') show(idx + 1);
    }
  });
  document.addEventListener('keydown', function(ev){
    if(lb.hidden) return;
    if(ev.key === 'Escape') close();
    else if(ev.key === 'ArrowLeft') show(idx - 1);
    else if(ev.key === 'ArrowRight') show(idx + 1);
    else if(ev.key === 'Tab'){ /* focus trap */
      var f = lb.querySelectorAll('button');
      var first = f[0], last = f[f.length - 1];
      if(ev.shiftKey && document.activeElement === first){ ev.preventDefault(); last.focus(); }
      else if(!ev.shiftKey && document.activeElement === last){ ev.preventDefault(); first.focus(); }
    }
  });
  var tx = null;
  lb.addEventListener('touchstart', function(ev){ tx = ev.touches[0].clientX; }, {passive:true});
  lb.addEventListener('touchend', function(ev){
    if(tx === null) return;
    var dx = ev.changedTouches[0].clientX - tx;
    if(Math.abs(dx) > 48) show(idx + (dx < 0 ? 1 : -1));
    tx = null;
  }, {passive:true});
}

/* ---------- project index: search + filter ---------- */
var searchInput = document.getElementById('project-search');
if(searchInput){
  var cards = Array.prototype.slice.call(document.querySelectorAll('[data-idx-card]'));
  var chips = Array.prototype.slice.call(document.querySelectorAll('[data-chip]'));
  var status = document.querySelector('.idx-status');
  var noRes = document.querySelector('.no-results');
  var activeCat = 'All';
  function apply(){
    var q = searchInput.value.trim().toLowerCase();
    var n = 0;
    cards.forEach(function(card){
      var okCat = activeCat === 'All' || card.getAttribute('data-cat') === activeCat;
      var hay = card.getAttribute('data-search').toLowerCase();
      var okQ = !q || hay.indexOf(q) !== -1;
      var show = okCat && okQ;
      card.hidden = !show;
      if(show) n++;
    });
    if(noRes) noRes.hidden = n !== 0;
    if(status) status.textContent = n + (n === 1 ? ' project' : ' projects');
  }
  var deb = null;
  searchInput.addEventListener('input', function(){
    clearTimeout(deb); deb = setTimeout(apply, 120);
  });
  chips.forEach(function(chip){
    chip.addEventListener('click', function(){
      activeCat = chip.getAttribute('data-chip');
      chips.forEach(function(c){ c.setAttribute('aria-pressed', c === chip ? 'true' : 'false'); });
      apply();
    });
  });
  apply();
}
})();
