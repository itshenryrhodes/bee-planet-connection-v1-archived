/* Bee Planet Connection – Service Worker
   Strategy:
   - Precache core shell (HTML/CSS/JS/feeds).
   - Cache-first for static assets (CSS/JS/images).
   - Network-first for navigations (pages), fallback to cache if offline.
*/
const BPC_CACHE_VERSION = 'bpc-v1.0.0';
const BPC_STATIC_CACHE = `${BPC_CACHE_VERSION}-static`;
const BPC_PAGES_CACHE  = `${BPC_CACHE_VERSION}-pages`;

const CORE_ASSETS = [
  '/',                      // shell
  '/index.html',
  '/blog.html',
  '/directory.html',
  '/about.html',
  '/contact.html',
  '/thanks.html',
  '/privacy.html',
  '/accessibility.html',
  '/assets/css/tokens-forest-honey.css',
  '/assets/css/site.css',
  '/assets/js/site.js',
  '/img/favicon-16.png',
  '/img/favicon-32.png',
  '/img/favicon.webp',
  '/img/icon-192.png',
  '/img/icon-512.png',
  '/manifest.webmanifest',
  '/sitemap.xml',
  '/feed.xml'
];

// Install: precache core assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(BPC_STATIC_CACHE).then(cache => cache.addAll(CORE_ASSETS))
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys
        .filter(k => !k.startsWith(BPC_CACHE_VERSION))
        .map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// Helper: cache-first for static assets
async function cacheFirst(req) {
  const cache = await caches.open(BPC_STATIC_CACHE);
  const cached = await cache.match(req);
  if (cached) return cached;
  try {
    const res = await fetch(req);
    if (res && res.ok) cache.put(req, res.clone());
    return res;
  } catch (e) {
    return cached; // last resort
  }
}

// Helper: network-first for pages (HTML)
async function networkFirst(req) {
  const cache = await caches.open(BPC_PAGES_CACHE);
  try {
    const res = await fetch(req);
    if (res && res.ok) cache.put(req, res.clone());
    return res;
  } catch (e) {
    const cached = await cache.match(req);
    return cached || caches.match('/index.html');
  }
}

// Fetch handler
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle same-origin requests
  if (url.origin !== location.origin) return;

  // HTML navigations -> network-first
  if (request.mode === 'navigate' ||
      (request.headers.get('accept') || '').includes('text/html')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Static assets: CSS/JS/Images/Web Manifest -> cache-first
  if (/\.(?:css|js|png|jpg|jpeg|webp|svg|ico|xml|json)$/.test(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }
});
