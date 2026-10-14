/* Ola Magdy CMS — UI behaviour: sidebar, tabs, image picker, slides, confirms, table filters */
(function () {
  'use strict';

  /* ---- collapsible sidebar (mobile) ---- */
  var toggle = document.getElementById('sidebarToggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var open = document.body.classList.toggle('nav-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.getElementById('scrim').addEventListener('click', function () {
      document.body.classList.remove('nav-open');
      toggle.setAttribute('aria-expanded', 'false');
    });
  }

  /* ---- tabs ---- */
  document.querySelectorAll('[data-tabs]').forEach(function (wrap) {
    var btns = wrap.querySelectorAll('.tab-btn');
    var panels = wrap.querySelectorAll('.tab-panel');
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        btns.forEach(function (x) { x.classList.remove('active'); x.setAttribute('aria-selected', 'false'); });
        panels.forEach(function (p) { p.classList.remove('active'); });
        b.classList.add('active'); b.setAttribute('aria-selected', 'true');
        var p = wrap.querySelector('#' + b.getAttribute('data-tab'));
        if (p) p.classList.add('active');
      });
    });
  });

  /* ---- confirm dialogs ---- */
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (ev) {
      if (!confirm(el.getAttribute('data-confirm'))) ev.preventDefault();
    });
  });

  /* ---- table search / filter ---- */
  document.querySelectorAll('[data-table-filter]').forEach(function (input) {
    var target = document.getElementById(input.getAttribute('data-table-filter'));
    if (!target) return;
    input.addEventListener('input', function () {
      var q = input.value.toLowerCase();
      target.querySelectorAll('tbody tr').forEach(function (tr) {
        tr.style.display = tr.textContent.toLowerCase().indexOf(q) === -1 ? 'none' : '';
      });
    });
  });
  document.querySelectorAll('[data-table-cat]').forEach(function (sel) {
    var target = document.getElementById(sel.getAttribute('data-table-cat'));
    if (!target) return;
    sel.addEventListener('change', function () {
      var v = sel.value;
      target.querySelectorAll('tbody tr').forEach(function (tr) {
        var show = !v || tr.getAttribute('data-cat') === v || tr.getAttribute('data-status') === v;
        tr.style.display = show ? '' : 'none';
      });
    });
  });

  /* ---- image picker modal ---- */
  var pickerState = null;
  window.openPicker = function (opts) {
    // opts: {target: hiddenInputId(s), multi: bool, onPick: fn}
    pickerState = opts;
    var m = document.getElementById('pickerModal');
    m.classList.add('open');
    m.querySelector('[data-picker-search]').value = '';
    filterPicker('');
  };
  window.closePicker = function () {
    document.getElementById('pickerModal').classList.remove('open');
    pickerState = null;
  };
  function filterPicker(q) {
    q = q.toLowerCase();
    document.querySelectorAll('#pickerModal .picker-item').forEach(function (it) {
      it.style.display = it.getAttribute('data-key').toLowerCase().indexOf(q) === -1 ? 'none' : '';
    });
  }
  document.addEventListener('input', function (ev) {
    if (ev.target && ev.target.hasAttribute('data-picker-search')) filterPicker(ev.target.value);
  });
  document.addEventListener('click', function (ev) {
    var it = ev.target.closest ? ev.target.closest('.picker-item') : null;
    if (it && pickerState) {
      var key = it.getAttribute('data-key');
      if (pickerState.multi) {
        it.classList.toggle('sel');
      } else {
        document.querySelectorAll('#pickerModal .picker-item').forEach(function (x) { x.classList.remove('sel'); });
        it.classList.add('sel');
        if (pickerState.onPick) pickerState.onPick(key);
        window.closePicker();
      }
      return;
    }
    if (ev.target && ev.target.id === 'pickerModal') window.closePicker();
    var mc = ev.target.closest ? ev.target.closest('[data-picker-confirm]') : null;
    if (mc && pickerState && pickerState.multi) {
      var keys = [];
      document.querySelectorAll('#pickerModal .picker-item.sel').forEach(function (x) { keys.push(x.getAttribute('data-key')); });
      if (pickerState.onPick) pickerState.onPick(keys);
      window.closePicker();
    }
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && pickerState) window.closePicker();
  });

  /* ---- slide editor: add / remove slides, image chips ---- */
  var slideTpl = document.getElementById('slideTemplate');
  window.addSlide = function () {
    var wrap = document.getElementById('slidesWrap');
    var idx = wrap.querySelectorAll('.slide').length;
    var html = slideTpl.innerHTML.replace(/__IDX__/g, idx);
    var div = document.createElement('div');
    div.className = 'slide';
    div.setAttribute('data-slide', idx);
    div.innerHTML = html;
    wrap.appendChild(div);
    renumberSlides();
  };
  window.removeSlide = function (btn) {
    if (!confirm('Remove this chapter?')) return;
    btn.closest('.slide').remove();
    renumberSlides();
  };
  function renumberSlides() {
    document.querySelectorAll('#slidesWrap .slide').forEach(function (s, i) {
      s.setAttribute('data-slide', i);
      var h = s.querySelector('.slide-head h3');
      if (h) h.textContent = 'Chapter ' + (i + 1);
      s.querySelectorAll('[name]').forEach(function (inp) {
        inp.name = inp.name.replace(/slides\[\d+\]/, 'slides[' + i + ']');
      });
    });
  }
  window.pickSlideImages = function (btn) {
    var slide = btn.closest('.slide');
    var idx = slide.getAttribute('data-slide');
    openPicker({
      multi: true,
      onPick: function (keys) {
        keys.forEach(function (k) {
          if (slide.querySelector('input[value="' + k + '"][name^="slides[' + idx + '][images]"]')) return;
          addImageChip(slide, idx, k);
        });
      }
    });
  };
  function addImageChip(slide, idx, key) {
    var box = slide.querySelector('.slide-images');
    var span = document.createElement('span');
    span.className = 'img-chip';
    span.innerHTML = '<input type="hidden" name="slides[' + idx + '][images][]" value="' + key.replace(/"/g, '&quot;') + '">' + key +
      ' <button type="button" onclick="this.parentElement.remove()" aria-label="Remove">×</button>';
    box.appendChild(span);
  }
  window.removeImgChip = function (btn) { btn.parentElement.remove(); };

  /* ---- single hero/image pickers (pages, seo, project hero) ---- */
  window.pickSingle = function (hiddenId, previewId) {
    openPicker({
      multi: false,
      onPick: function (key) {
        document.getElementById(hiddenId).value = key;
        var pv = previewId && document.getElementById(previewId);
        if (pv) { pv.src = '../dist/assets/' + key + '.webp'; pv.style.display = ''; }
      }
    });
  };
})();
