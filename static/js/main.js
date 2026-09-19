/* =====================================================
   Academy MS — main.js
   Shared front-end helpers + Theme + Clock + PWA
   ===================================================== */

document.addEventListener('DOMContentLoaded', () => {
  /* -----------------------------------------------
     1. Auto-dismiss flash messages
     ----------------------------------------------- */
  document.querySelectorAll('.flash').forEach((el) => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s ease';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  /* -----------------------------------------------
     2. Class -> Section filtering (Student form)
     ----------------------------------------------- */
  const classSelect = document.getElementById('classSelect');
  const sectionSelect = document.getElementById('sectionSelect');
  if (classSelect && sectionSelect) {
    const filterSections = () => {
      const cid = classSelect.value;
      Array.from(sectionSelect.options).forEach((opt) => {
        if (!opt.value) return;
        const belongs = opt.dataset.classId === cid;
        opt.hidden = !belongs;
        opt.disabled = !belongs;
      });
      const current = sectionSelect.selectedOptions[0];
      if (current && current.hidden) sectionSelect.value = '';
    };
    classSelect.addEventListener('change', filterSections);
    filterSections();
  }

  /* -----------------------------------------------
     3. Class -> Section filtering (Timetable)
     ----------------------------------------------- */
  const ttClass = document.getElementById('ttClassSelect');
  const ttSection = document.getElementById('ttSectionSelect');
  if (ttClass && ttSection) {
    const filter = () => {
      const cid = ttClass.value;
      Array.from(ttSection.options).forEach((opt) => {
        if (!opt.value) return;
        const belongs = opt.dataset.classId === cid;
        opt.hidden = !belongs;
        opt.disabled = !belongs;
      });
    };
    ttClass.addEventListener('change', filter);
    filter();
  }

  /* -----------------------------------------------
     4. Confirm dialogs
     ----------------------------------------------- */
  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (e) => {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  /* -----------------------------------------------
     5. Live Clock
     ----------------------------------------------- */
  const clockEl = document.getElementById('clockTime');
  if (clockEl) {
    const tick = () => {
      const now = new Date();
      const hh = String(now.getHours()).padStart(2, '0');
      const mm = String(now.getMinutes()).padStart(2, '0');
      clockEl.textContent = `${hh}:${mm}`;
    };
    tick();
    setInterval(tick, 30000);
  }

  /* -----------------------------------------------
     6. Theme Switcher
     ----------------------------------------------- */
  const swatches = document.querySelectorAll('.theme-switcher .swatch');
  const savedTheme = localStorage.getItem('academy-theme') || 'blue';

  // Mark active swatch
  swatches.forEach((s) => {
    if (s.dataset.themeValue === savedTheme) s.classList.add('active');
  });

  swatches.forEach((s) => {
    s.addEventListener('click', () => {
      const theme = s.dataset.themeValue;
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('academy-theme', theme);
      swatches.forEach((x) => x.classList.remove('active'));
      s.classList.add('active');
    });
  });

  /* -----------------------------------------------
     7. Dark / Light Mode Toggle
     ----------------------------------------------- */
  const modeToggle = document.getElementById('modeToggle');
  if (modeToggle) {
    const thumb = modeToggle.querySelector('.mode-thumb');
    const applyMode = (mode) => {
      if (mode === 'dark') {
        document.documentElement.setAttribute('data-mode', 'dark');
        thumb.textContent = '☾';
      } else {
        document.documentElement.removeAttribute('data-mode');
        thumb.textContent = '☀';
      }
    };
    applyMode(localStorage.getItem('academy-mode') || 'light');

    modeToggle.addEventListener('click', () => {
      const isDark = document.documentElement.getAttribute('data-mode') === 'dark';
      const next = isDark ? 'light' : 'dark';
      applyMode(next);
      localStorage.setItem('academy-mode', next);
    });
  }

  /* -----------------------------------------------
     8. FAB toggle (if present)
     ----------------------------------------------- */
  const fab = document.querySelector('.fab-container .fab');
  if (fab) {
    fab.addEventListener('click', () => {
      fab.parentElement.classList.toggle('open');
    });
  }

  /* -----------------------------------------------
     9. Dropdown toggle on click (for mobile)
     ----------------------------------------------- */
  document.querySelectorAll('[data-dropdown]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const dd = btn.closest('.dropdown');
      if (dd) dd.classList.toggle('open');
    });
  });
  document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown.open').forEach((d) => d.classList.remove('open'));
  });

  /* -----------------------------------------------
     10. Modal helpers
     ----------------------------------------------- */
  document.querySelectorAll('[data-modal-open]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const target = document.querySelector(btn.dataset.modalOpen);
      if (target) target.classList.add('open');
    });
  });
  document.querySelectorAll('[data-modal-close]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal');
      if (modal) modal.classList.remove('open');
    });
  });
});


/* =====================================================
   PWA — Service Worker Registration (optional)
   ===================================================== */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/static/sw.js', { scope: '/' })
      .then((reg) => console.log('[PWA] SW registered:', reg.scope))
      .catch((err) => console.warn('[PWA] SW registration failed:', err));
  });
}


/* =====================================================
   PWA — Install Prompt Banner (optional)
   ===================================================== */
let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  setTimeout(() => {
    const b = document.getElementById('pwa-install-banner');
    if (b) b.style.display = 'flex';
  }, 3000);
});

document.addEventListener('click', async (e) => {
  if (e.target.closest('#pwa-install-btn')) {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    const b = document.getElementById('pwa-install-banner');
    if (b) b.style.display = 'none';
  }
  if (e.target.closest('#pwa-dismiss-btn')) {
    const b = document.getElementById('pwa-install-banner');
    if (b) b.style.display = 'none';
  }
});
