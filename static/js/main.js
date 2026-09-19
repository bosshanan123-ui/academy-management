/* =====================================================
   main.js — shared front-end helpers
   ===================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss flash messages after 5 seconds
  document.querySelectorAll('.flash').forEach((el) => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s ease';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  // Class -> Section filtering on any page with #classSelect and #sectionSelect
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
      // Reset selection if current option is hidden
      const current = sectionSelect.selectedOptions[0];
      if (current && current.hidden) sectionSelect.value = '';
    };

    classSelect.addEventListener('change', filterSections);
    filterSections();
  }

  // Class -> Section filtering for the timetable page (different IDs)
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

  // Confirmation dialogs for dangerous actions
  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (e) => {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });
});
/* =====================================================
   main.js — shared front-end helpers + PWA
   ===================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss flash messages after 5 seconds
  document.querySelectorAll('.flash').forEach((el) => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s ease';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  // Class -> Section filtering
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

  // Timetable class -> section
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

  // Confirm dialogs
  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (e) => {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });
});

/* =====================================================
   PWA — Service Worker Registration
   ===================================================== */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/static/sw.js', { scope: '/' })
      .then((registration) => {
        console.log('[PWA] Service Worker registered:', registration.scope);
      })
      .catch((err) => {
        console.warn('[PWA] Service Worker registration failed:', err);
      });
  });
}

/* =====================================================
   PWA — Install Prompt Banner
   ===================================================== */
let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;

  // Show custom install banner after 3 seconds
  setTimeout(() => {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) banner.style.display = 'flex';
  }, 3000);
});

document.addEventListener('click', async (e) => {
  if (e.target.closest('#pwa-install-btn')) {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log('[PWA] User choice:', outcome);
    deferredPrompt = null;
    const banner = document.getElementById('pwa-install-banner');
    if (banner) banner.style.display = 'none';
  }

  if (e.target.closest('#pwa-dismiss-btn')) {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) banner.style.display = 'none';
    localStorage.setItem('pwa-banner-dismissed', '1');
  }
});

window.addEventListener('appinstalled', () => {
  console.log('[PWA] App installed');
  deferredPrompt = null;
  const banner = document.getElementById('pwa-install-banner');
  if (banner) banner.style.display = 'none';
});
