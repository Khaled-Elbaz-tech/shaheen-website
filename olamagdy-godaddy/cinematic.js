(() => {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  // Every image remains linked to its original file without JavaScript.
  document.querySelectorAll('.study-explorer').forEach(explorer => {
    const choices = [...explorer.querySelectorAll('[data-study-src]')];
    const filters = [...explorer.querySelectorAll('[data-study-filter]')];
    const main = explorer.querySelector('.study-main');
    const image = main.querySelector('img');
    const caption = explorer.querySelector('[data-study-caption]:not(button)');
    const counter = explorer.querySelector('[data-study-count]');
    const select = button => {
      choices.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
      image.src = button.dataset.studySrc;
      image.alt = button.dataset.studyCaption;
      image.removeAttribute('width'); image.removeAttribute('height');
      main.href = button.dataset.studySrc;
      main.setAttribute('aria-label', `Enlarge: ${button.dataset.studyCaption}`);
      caption.textContent = button.dataset.studyCaption;
      const visible = choices.filter(item => !item.hidden);
      counter.textContent = `${String(visible.indexOf(button) + 1).padStart(2, '0')} / ${String(visible.length).padStart(2, '0')}`;
    };
    choices.forEach(button => button.addEventListener('click', () => select(button)));
    filters.forEach(button => button.addEventListener('click', () => {
      filters.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
      choices.forEach(item => { item.hidden = button.dataset.studyFilter !== 'All' && item.dataset.studyCategory !== button.dataset.studyFilter; });
      const current = choices.find(item => item.getAttribute('aria-pressed') === 'true' && !item.hidden);
      select(current || choices.find(item => !item.hidden));
    }));
  });
  if ('IntersectionObserver' in window && !reduced.matches) {
    document.documentElement.classList.add('motion-ready');
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }
    }), {threshold:0.08, rootMargin:'0px 0px 25px 0px'});
    document.querySelectorAll('.intro-layout,.section-title,.chapter-heading,.gallery-figure,.portrait-copy,.career-row,.catalogue-entry,.explorer-heading').forEach(item => {
      item.classList.add('reveal-item'); observer.observe(item);
    });
  }
  const depth = [...document.querySelectorAll('[data-depth]')];
  let scheduled = false;
  const update = () => {
    scheduled = false;
    if (reduced.matches || window.innerWidth < 700) return;
    depth.forEach(layer => {
      const bounds = layer.parentElement.getBoundingClientRect();
      if (bounds.bottom > 0 && bounds.top < innerHeight) {
        const progress = Math.min(1, Math.max(0, -bounds.top / bounds.height));
        layer.querySelector('img').style.transform = `scale(${1.025 + progress * .07}) translateY(${progress * 3}%)`;
      }
    });
  };
  window.addEventListener('scroll', () => { if (!scheduled) { scheduled = true; requestAnimationFrame(update); } }, {passive:true});
  reduced.addEventListener('change', () => {
    if (reduced.matches) {
      document.documentElement.classList.remove('motion-ready');
      depth.forEach(layer => layer.querySelector('img').style.removeProperty('transform'));
    }
  });
})();
