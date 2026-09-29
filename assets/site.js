// Progressive enhancements only: every page works without this file.
const root = document.documentElement;
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const motionPaused = () => reduceMotion || root.classList.contains('motion-paused');

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
          ctx.strokeStyle = `rgba(190, 170, 255, ${0.14 * (1 - d / 120)})`;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
      ctx.fillStyle = i % 7 === 0 ? 'rgba(255, 101, 94, 0.8)' : 'rgba(230, 225, 255, 0.55)';
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
