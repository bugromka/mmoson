/* ММОСО’Н — поведение страницы.
   Без зависимостей: появление при скролле, счётчики, меню, лайтбокс. */
(function () {
  'use strict';

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. Появление элементов ---------- */
  const fadeEls = document.querySelectorAll('.fade-in');

  function showAll() {
    fadeEls.forEach((el) => el.classList.add('visible'));
  }

  if (reduceMotion || !('IntersectionObserver' in window)) {
    showAll();
  } else {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const el = entry.target;
          const siblings = Array.from(el.parentElement.children).filter((n) =>
            n.classList.contains('fade-in')
          );
          const index = Math.max(0, siblings.indexOf(el));
          el.style.transitionDelay = Math.min(index * 60, 300) + 'ms';
          el.classList.add('visible');
          io.unobserve(el);
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -60px 0px' }
    );
    fadeEls.forEach((el) => io.observe(el));
    /* Страховка: если наблюдатель почему-то не сработал, контент не должен остаться невидимым */
    window.setTimeout(() => {
      fadeEls.forEach((el) => {
        if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add('visible');
      });
    }, 1200);
  }

  /* ---------- 2. Счётчики в карточках параметров ---------- */
  const counters = document.querySelectorAll('[data-count]');

  function formatNumber(value) {
    return value.toLocaleString('ru-RU').replace(/\u00A0/g, ' ');
  }

  function animateCounter(el) {
    const target = parseFloat(el.dataset.count);
    const suffix = el.dataset.suffix || '';
    if (!isFinite(target)) return;

    if (reduceMotion) {
      el.textContent = formatNumber(target) + suffix;
      return;
    }

    const duration = 1200;
    const start = performance.now();

    function frame(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(target * eased);
      el.textContent = formatNumber(current) + suffix;
      if (progress < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  if (counters.length) {
    if (!('IntersectionObserver' in window) || reduceMotion) {
      counters.forEach((c) => {
        c.textContent = formatNumber(parseFloat(c.dataset.count)) + (c.dataset.suffix || '');
      });
    } else {
      const counterObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            animateCounter(entry.target);
            counterObserver.unobserve(entry.target);
          });
        },
        { threshold: 0.5 }
      );
      counters.forEach((c) => counterObserver.observe(c));
    }
  }

  /* ---------- 3. Мобильное меню ---------- */
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.getElementById('nav-links');

  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      const open = navLinks.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', String(open));
    });
    navLinks.addEventListener('click', (e) => {
      if (e.target.closest('a')) {
        navLinks.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ---------- 4. Подсветка активного пункта меню ---------- */
  const sections = Array.from(document.querySelectorAll('main section[id]'));
  const linkMap = new Map();
  document.querySelectorAll('.nav-links a').forEach((a) => {
    const id = a.getAttribute('href').replace('#', '');
    linkMap.set(id, a);
  });

  if ('IntersectionObserver' in window && sections.length) {
    const navObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const link = linkMap.get(entry.target.id);
          if (!link) return;
          if (entry.isIntersecting) {
            document.querySelectorAll('.nav-links a.active').forEach((a) => a.classList.remove('active'));
            link.classList.add('active');
          }
        });
      },
      { rootMargin: '-45% 0px -45% 0px', threshold: 0 }
    );
    sections.forEach((s) => navObserver.observe(s));
  }

  /* ---------- 5. Лайтбокс для иллюстраций ---------- */
  const lightbox = document.getElementById('lightbox');
  const lightboxImg = document.getElementById('lightbox-img');
  const lightboxCaption = document.getElementById('lightbox-caption');
  const lightboxClose = lightbox ? lightbox.querySelector('.lightbox-close') : null;
  let lastFocused = null;

  function openLightbox(item) {
    /* В одностраничной сборке data-full может отсутствовать: тогда полноразмерной
       служит сама картинка карточки — она уже встроена в файл. */
    const inner = item.querySelector('img');
    const full = item.dataset.full || (inner ? inner.src : '');
    const title = item.dataset.title || (inner ? inner.alt : '');
    if (!lightbox || !full) return;
    lastFocused = item;
    lightboxImg.src = full;
    lightboxImg.alt = title;
    lightboxCaption.textContent = title;
    lightbox.classList.add('open');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    if (lightboxClose) lightboxClose.focus();
  }

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.classList.remove('open');
    lightbox.setAttribute('aria-hidden', 'true');
    lightboxImg.src = '';
    document.body.style.overflow = '';
    if (lastFocused) lastFocused.focus();
  }

  document.querySelectorAll('.gallery-item').forEach((item) => {
    item.addEventListener('click', () => openLightbox(item));
  });

  if (lightbox) {
    lightbox.addEventListener('click', (e) => {
      if (e.target === lightbox || e.target === lightboxClose) closeLightbox();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && lightbox.classList.contains('open')) closeLightbox();
    });
  }

  /* ---------- 6. Плавная прокрутка с поправкой на липкую навигацию ---------- */
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (!id || id === '#') return;
      const target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      const offset = window.innerWidth > 900 ? 84 : 110;
      const top = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: reduceMotion ? 'auto' : 'smooth' });
      history.replaceState(null, '', id);
    });
  });
})();
