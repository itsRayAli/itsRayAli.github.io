// Progressive enhancements only: every page works without this file.
const root = document.documentElement;
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const motionPaused = () => reduceMotion || root.classList.contains('motion-paused');

// Theme: the <head> script already applied the saved or system theme.
// The toggle saves an explicit choice; without one, follow OS changes live.
const themeToggle = document.querySelector('[data-theme-toggle]');
const themeMeta = document.querySelector('meta[name="theme-color"]');
const applyTheme = (theme) => {
  root.dataset.theme = theme;
  if (themeMeta) themeMeta.content = theme === 'light' ? '#faf8fd' : '#0e0c1d';
  if (themeToggle) themeToggle.setAttribute('aria-label', `Switch to ${theme === 'light' ? 'dark' : 'light'} theme`);
  root.dispatchEvent(new Event('themechange'));
};
applyTheme(root.dataset.theme === 'light' ? 'light' : 'dark');
themeToggle?.addEventListener('click', () => {
  const next = root.dataset.theme === 'light' ? 'dark' : 'light';
  try { localStorage.setItem('theme', next); } catch { /* private mode: choice lasts this page only */ }
  applyTheme(next);
});
matchMedia('(prefers-color-scheme: light)').addEventListener('change', (event) => {
  let saved = null;
  try { saved = localStorage.getItem('theme'); } catch { /* ignore */ }
  if (!saved) applyTheme(event.matches ? 'light' : 'dark');
});

// Header: switch to a solid glass bar once the page scrolls.
const header = document.querySelector('[data-header]');
if (header) {
  const onScroll = () => header.classList.toggle('is-scrolled', scrollY > 12);
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

// Scroll reveal.
const revealables = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window && !reduceMotion) {
  const io = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add('is-visible');
      io.unobserve(entry.target);
    }
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  revealables.forEach((el) => io.observe(el));
} else {
  revealables.forEach((el) => el.classList.add('is-visible'));
}

// Hero headline: cycle through the rotating words once, ending on the last.
const rotator = document.querySelector('[data-rotate]');
if (rotator && !reduceMotion) {
  const words = JSON.parse(rotator.dataset.rotate);
  let index = 0;
  const next = () => {
    if (index >= words.length - 1) return;
    if (motionPaused()) { setTimeout(next, 600); return; }
    rotator.classList.add('is-out');
    setTimeout(() => {
      index += 1;
      rotator.textContent = words[index];
      rotator.classList.remove('is-out');
      setTimeout(next, 1900);
    }, 350);
  };
  setTimeout(next, 2200);
}

// Particle constellation behind the hero.
const canvas = document.querySelector('[data-particles]');
if (canvas && canvas.getContext) {
  const ctx = canvas.getContext('2d');
  const hero = canvas.closest('[data-hero]') || document.body;
  const pointer = { x: -9999, y: -9999 };
  let width = 0, height = 0, points = [], frame = null, onScreen = true;
  // Colours come from CSS custom properties so they follow the theme.
  let colors = {};
  const readColors = () => {
    const css = getComputedStyle(root);
    colors = {
      line: css.getPropertyValue('--particle-line').trim(),
      lineAlpha: parseFloat(css.getPropertyValue('--particle-line-alpha')) || 0.14,
      dot: css.getPropertyValue('--particle-dot').trim(),
      accent: css.getPropertyValue('--particle-accent').trim(),
    };
  };
  readColors();
  root.addEventListener('themechange', () => { readColors(); draw(); });

  const resize = () => {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    const rect = canvas.getBoundingClientRect();
    width = rect.width; height = rect.height;
    canvas.width = width * dpr; canvas.height = height * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const count = Math.round(Math.min(80, (width * height) / 15000));
    points = Array.from({ length: count }, () => ({
      x: Math.random() * width, y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
      r: Math.random() * 1.3 + 0.5,
    }));
    draw();
  };

  const draw = () => {
    ctx.clearRect(0, 0, width, height);
    for (let i = 0; i < points.length; i++) {
      const a = points[i];
      for (let j = i + 1; j < points.length; j++) {
        const b = points[j];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < 120) {
          ctx.strokeStyle = `rgba(${colors.line}, ${colors.lineAlpha * (1 - d / 120)})`;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
      ctx.fillStyle = i % 7 === 0 ? colors.accent : colors.dot;
      ctx.beginPath(); ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2); ctx.fill();
    }
  };

  const step = () => {
    for (const p of points) {
      const dx = p.x - pointer.x, dy = p.y - pointer.y, d = Math.hypot(dx, dy);
      if (d < 110 && d > 0) { p.x += (dx / d) * 0.8; p.y += (dy / d) * 0.8; }
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = width; else if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height; else if (p.y > height) p.y = 0;
    }
    draw();
    frame = requestAnimationFrame(step);
  };

  const sync = () => {
    const shouldRun = onScreen && !document.hidden && !motionPaused();
    if (shouldRun && frame === null) frame = requestAnimationFrame(step);
    if (!shouldRun && frame !== null) { cancelAnimationFrame(frame); frame = null; }
  };

  hero.addEventListener('pointermove', (event) => {
    const rect = canvas.getBoundingClientRect();
    pointer.x = event.clientX - rect.left; pointer.y = event.clientY - rect.top;
  });
  hero.addEventListener('pointerleave', () => { pointer.x = pointer.y = -9999; });
  document.addEventListener('visibilitychange', sync);
  root.addEventListener('motionchange', sync);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(([entry]) => { onScreen = entry.isIntersecting; sync(); }).observe(canvas);
  }
  let resizeTimer;
  addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(resize, 150); });
  resize();
  sync();
}

// Pause / resume all decorative motion.
const toggle = document.querySelector('[data-motion-toggle]');
if (toggle) {
  toggle.addEventListener('click', () => {
    const paused = root.classList.toggle('motion-paused');
    toggle.setAttribute('aria-pressed', String(paused));
    toggle.textContent = paused ? 'Resume motion' : 'Pause motion';
    root.dispatchEvent(new Event('motionchange'));
  });
}

// Contact form: compose a mailto draft (nothing is sent or stored by the site).
const form = document.querySelector('#contact-form');
if (form) {
  const service = new URLSearchParams(location.search).get('service');
  if (service && [...form.elements.service.options].some((o) => o.value === service)) {
    form.elements.service.value = service;
  }
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    const subject = `Portfolio enquiry: ${form.elements.service.selectedOptions[0].text}`;
    const body = `Hi Ray,\n\n${data.get('message')}\n\n${data.get('name')}\n${data.get('email')}`;
    location.href = `mailto:${form.dataset.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    document.querySelector('#form-status').textContent = 'Your email app should open with a draft. If it doesn’t, use the email address on this page. Your message has not been sent by this website.';
  });
}

// Lightbox: open project screenshots in-page instead of a new tab.
// Without JS (or <dialog> support) the links still open the original image.
const lightboxLinks = [...document.querySelectorAll('[data-lightbox]')];
if (lightboxLinks.length && typeof HTMLDialogElement === 'function') {
  const dialog = document.createElement('dialog');
  dialog.className = 'lightbox';
  dialog.setAttribute('aria-label', 'Screenshot viewer');
  // Static markup only; captions and alt text are set with textContent/properties below.
  dialog.innerHTML = `
    <figure class="lightbox-figure">
      <div class="lightbox-stage"><img class="lightbox-img" alt=""></div>
      <figcaption class="lightbox-caption" aria-live="polite">
        <span class="lightbox-text"></span>
        <span class="lightbox-count"></span>
        <button class="lightbox-zoom" type="button" aria-pressed="false">Zoom in</button>
        <a class="lightbox-original" target="_blank" rel="noopener noreferrer">Open original <span aria-hidden="true">↗</span><span class="sr-only"> (opens in a new tab)</span></a>
      </figcaption>
    </figure>
    <button class="lightbox-btn lightbox-close" type="button" aria-label="Close viewer" autofocus>✕</button>
    <button class="lightbox-btn lightbox-prev" type="button" aria-label="Previous screenshot">←</button>
    <button class="lightbox-btn lightbox-next" type="button" aria-label="Next screenshot">→</button>`;
  document.body.append(dialog);

  const img = dialog.querySelector('.lightbox-img');
  const text = dialog.querySelector('.lightbox-text');
  const count = dialog.querySelector('.lightbox-count');
  const original = dialog.querySelector('.lightbox-original');
  const prev = dialog.querySelector('.lightbox-prev');
  const next = dialog.querySelector('.lightbox-next');
  const stage = dialog.querySelector('.lightbox-stage');
  const zoomBtn = dialog.querySelector('.lightbox-zoom');
  const multiple = lightboxLinks.length > 1;
  prev.hidden = next.hidden = !multiple;
  let index = 0;
  let opener = null;
  let zoomed = false;

  // Zoom: grow the image so it fills the available height (wide screenshots
  // become readable and scroll sideways), keeping the point under the cursor
  // or finger in view. `at` is a 0–1 position within the image, if known.
  const setZoom = (on, at = { x: 0.5, y: 0.5 }) => {
    // Measure the fitted size before switching modes (zoom removes the fit limits).
    const fitW = img.getBoundingClientRect().width;
    zoomed = on;
    dialog.classList.toggle('is-zoomed', on);
    zoomBtn.setAttribute('aria-pressed', String(on));
    zoomBtn.textContent = on ? 'Fit to screen' : 'Zoom in';
    if (!on) { img.style.width = ''; return; }
    const stageH = parseFloat(getComputedStyle(stage).maxHeight) || innerHeight * 0.7;
    const byHeight = img.naturalWidth * (stageH / img.naturalHeight);
    const target = Math.min(img.naturalWidth, Math.max(byHeight, fitW * 1.6));
    img.style.width = `${Math.round(target)}px`;
    requestAnimationFrame(() => {
      stage.scrollLeft = at.x * stage.scrollWidth - stage.clientWidth / 2;
      stage.scrollTop = at.y * stage.scrollHeight - stage.clientHeight / 2;
    });
  };

  const show = (i) => {
    setZoom(false);
    index = (i + lightboxLinks.length) % lightboxLinks.length;
    const link = lightboxLinks[index];
    img.classList.add('is-loading');
    img.onload = img.onerror = () => img.classList.remove('is-loading');
    img.src = link.dataset.full || link.href;
    img.alt = link.querySelector('img')?.alt || '';
    text.textContent = link.dataset.caption || '';
    count.textContent = multiple ? `${index + 1} / ${lightboxLinks.length}` : '';
    original.href = link.href;
    // Warm the cache for the neighbours so arrowing through feels instant.
    if (multiple) {
      for (const n of [index - 1, index + 1]) {
        const neighbour = lightboxLinks[(n + lightboxLinks.length) % lightboxLinks.length];
        new Image().src = neighbour.dataset.full || neighbour.href;
      }
    }
  };

  lightboxLinks.forEach((link, i) => link.addEventListener('click', (event) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return; // allow "open in new tab"
    event.preventDefault();
    opener = link;
    show(i);
    dialog.showModal();
  }));

  img.addEventListener('click', (event) => {
    const r = img.getBoundingClientRect();
    setZoom(!zoomed, { x: (event.clientX - r.left) / r.width, y: (event.clientY - r.top) / r.height });
  });
  zoomBtn.addEventListener('click', () => setZoom(!zoomed));
  prev.addEventListener('click', () => show(index - 1));
  next.addEventListener('click', () => show(index + 1));
  dialog.querySelector('.lightbox-close').addEventListener('click', () => dialog.close());
  // Clicking anywhere except the image and the controls closes the viewer
  // (the figure spans the full width, so "outside" can't just mean the backdrop).
  dialog.addEventListener('click', (event) => {
    if (swiped) { swiped = false; return; } // the click that ends a swipe isn't a close
    if (event.target.closest('.lightbox-stage, button, a')) return;
    dialog.close();
  });
  dialog.addEventListener('keydown', (event) => {
    if (!multiple || zoomed) return; // arrows scroll the zoomed image instead
    if (event.key === 'ArrowLeft') { event.preventDefault(); show(index - 1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); show(index + 1); }
  });
  // Swipe left/right on touch screens.
  let startX = null;
  let swiped = false;
  dialog.addEventListener('pointerdown', (event) => { swiped = false; if (event.pointerType !== 'mouse') startX = event.clientX; });
  dialog.addEventListener('pointerup', (event) => {
    // While zoomed, horizontal drags scroll the image instead of changing it.
    if (startX === null || !multiple || zoomed) { startX = null; return; }
    const dx = event.clientX - startX;
    startX = null;
    if (Math.abs(dx) > 50) { swiped = true; show(index + (dx < 0 ? 1 : -1)); }
  });
  dialog.addEventListener('close', () => { setZoom(false); opener?.focus(); opener = null; });
}
