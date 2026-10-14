// Full-size drawings keep their direct-image fallback without JavaScript.
const viewer = document.querySelector('.image-viewer');
if (viewer && typeof viewer.showModal === 'function') {
  const image = viewer.querySelector('img');
  const caption = viewer.querySelector('figcaption');
  const original = viewer.querySelector('.viewer-original');
  document.querySelectorAll('.enlarge-image').forEach(link => {
    link.addEventListener('click', event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      const source = link.querySelector('img');
      image.src = link.href;
      image.alt = source.alt;
      caption.textContent = source.alt;
      original.href = link.href;
      viewer.showModal();
      document.body.classList.add('viewer-open');
    });
  });
  viewer.querySelector('.viewer-close').addEventListener('click', () => viewer.close());
  viewer.addEventListener('close', () => document.body.classList.remove('viewer-open'));
}

// Search preserves the hierarchy between collections and their programmes.
const search = document.querySelector('#project-search');
if (search) {
  const groups = [...document.querySelectorAll('[data-project-group]')];
  const status = document.querySelector('.search-status');
  const empty = document.querySelector('.register-empty');
  const normalize = text => text.toLocaleLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  search.addEventListener('input', () => {
    const query = normalize(search.value.trim());
    let visible = 0;
    for (const group of groups) {
      const groupMatch = normalize(group.querySelector('.register-heading').textContent).includes(query);
      const entries = [...group.querySelectorAll('.register-entries a')];
      entries.forEach(entry => { entry.hidden = !groupMatch && !normalize(entry.textContent).includes(query); });
      group.hidden = !entries.some(entry => !entry.hidden);
      if (!group.hidden) visible++;
    }
    empty.hidden = visible > 0;
    status.textContent = query ? `${visible} matching ${visible === 1 ? 'collection' : 'collections'}` : '';
  });
}
