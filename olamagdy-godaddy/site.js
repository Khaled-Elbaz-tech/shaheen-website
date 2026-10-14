// Keyboard-accessible image viewing, zoom and pointer panning.
const viewer = document.querySelector('.image-viewer');
if (viewer && typeof viewer.showModal === 'function') {
  const image = viewer.querySelector('figure img');
  const caption = viewer.querySelector('figcaption');
  const original = viewer.querySelector('.viewer-original');
  const items = [...document.querySelectorAll('[data-study-src]')].map(button => ({src:button.dataset.studySrc, alt:button.dataset.studyCaption}));
  const figure = viewer.querySelector('figure');
  let index = 0, scale = 1, x = 0, y = 0, drag = null;
  const paint = () => { image.style.transform = `translate(${x}px, ${y}px) scale(${scale})`; };
  const reset = () => { scale = 1; x = y = 0; paint(); };
  const show = item => { image.src = item.src; image.alt = item.alt; caption.textContent = item.alt; original.href = item.src; reset(); };
  const step = delta => { if (!items.length) return; index = (index + delta + items.length) % items.length; show(items[index]); };
  const zoom = delta => { scale = Math.min(4,Math.max(1,scale + delta)); if (scale === 1) x = y = 0; paint(); };
  document.querySelectorAll('.enlarge-image').forEach(link => link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    const source = link.querySelector('img');
    const path = new URL(link.href).pathname;
    index = Math.max(0,items.findIndex(item => item.src === path));
    show({src:link.href,alt:source.alt});
    viewer.showModal(); document.body.classList.add('viewer-open');
  }));
  viewer.querySelector('.viewer-close').addEventListener('click', () => viewer.close());
  viewer.addEventListener('close', () => { document.body.classList.remove('viewer-open'); reset(); });
  viewer.querySelectorAll('[data-viewer-action]').forEach(button => button.addEventListener('click', () => {
    const action = button.dataset.viewerAction;
    if (action === 'previous') step(-1);
    if (action === 'next') step(1);
    if (action === 'in') zoom(.5);
    if (action === 'out') zoom(-.5);
    if (action === 'reset') reset();
  }));
  viewer.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); step(-1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); step(1); }
    if (event.key === '+' || event.key === '=') { event.preventDefault(); zoom(.5); }
    if (event.key === '-') { event.preventDefault(); zoom(-.5); }
    if (event.key === '0') reset();
  });
  image.addEventListener('dragstart', event => event.preventDefault());
  figure.addEventListener('pointerdown', event => {
    if (scale === 1 || event.target !== image) return;
    drag = {px:event.clientX,py:event.clientY,x,y};
    figure.setPointerCapture(event.pointerId);
  });
  figure.addEventListener('pointermove', event => {
    if (!drag) return;
    const maxX = image.clientWidth * (scale-1) / 2;
    const maxY = image.clientHeight * (scale-1) / 2;
    x = Math.max(-maxX,Math.min(maxX,drag.x + event.clientX-drag.px));
    y = Math.max(-maxY,Math.min(maxY,drag.y + event.clientY-drag.py)); paint();
  });
  figure.addEventListener('pointerup', () => { drag = null; });
  figure.addEventListener('pointercancel', () => { drag = null; });
}

// Each project and programme remains searchable as an individual entry.
const search = document.querySelector('#project-search');
if (search) {
  const entries = [...document.querySelectorAll('[data-project-entry]')];
  const additional = document.querySelector('.additional-records');
  const status = document.querySelector('.search-status');
  const empty = document.querySelector('.register-empty');
  const normalize = text => text.toLocaleLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  search.addEventListener('input', () => {
    const query = normalize(search.value.trim());
    let visible = 0;
    for (const entry of entries) {
      entry.hidden = !normalize(entry.textContent + ' ' + (entry.dataset.search || '')).includes(query);
      if (!entry.hidden) visible++;
    }
    if (additional) additional.hidden = ![...additional.querySelectorAll('[data-project-entry]')].some(entry => !entry.hidden);
    empty.hidden = visible > 0;
    status.textContent = query ? `${visible} matching ${visible === 1 ? 'entry' : 'entries'}` : '';
  });
}
