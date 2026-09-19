/* ============================================================
   Service Worker — Academy Management System PWA
   ------------------------------------------------------------
   Provides:
     - Offline caching for static assets
     - Network-first for HTML pages
     - Cache-first for CSS/JS/images
   ============================================================ */

const CACHE_VERSION = 'academy-ms-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;

// Files to cache on install (pre-cache)
const PRECACHE_URLS = [
  '/',
  '/login',
  '/offline',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/charts.js',
  '/static/manifest.json',
];

// =====================================================
// INSTALL — pre-cache static assets
// =====================================================
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(PRECACHE_URLS).catch((err) => {
        console.warn('[SW] Precache failed for some URLs:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// =====================================================
// ACTIVATE — clean old caches
// =====================================================
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => !key.startsWith(CACHE_VERSION))
          .map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// =====================================================
// FETCH — smart caching strategy
// =====================================================
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin requests
  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;

  // Skip Supabase API calls (always fetch from network)
  if (url.pathname.startsWith('/api/')) return;

  // Static assets: Cache First
  if (
    url.pathname.startsWith('/static/') ||
    url.pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|woff2?|ttf|ico)$/)
  ) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(STATIC_CACHE).then((cache) => cache.put(request, clone));
          }
          return response;
        });
      })
    );
    return;
  }

  // HTML pages: Network First, fallback to cache, then offline page
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(DYNAMIC_CACHE).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => {
          return caches.match(request).then((cached) => {
            return cached || caches.match('/offline');
          });
        })
    );
    return;
  }

  // Everything else: Network First
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});

// =====================================================
// MESSAGE — skip waiting when asked
// =====================================================
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
