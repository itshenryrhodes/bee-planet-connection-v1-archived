/* Bee Planet Connection – Service Worker
   Strategy:
   - Precache core shell (HTML/CSS/JS, icons, hero images).
   - Cache-first for static assets (CSS/JS/images).
   - Network-first for navigations (pages), fallback to cache if offline.
*/
const BPC_CACHE_VERSION = 'bpc-v1.1.0';
const BPC_STATIC_CACHE = `${BPC_CACHE_VERSION}-static`;
const BPC_PAGES_CACHE  = `${BPC_CACHE_VERSION}-pages`;

const CORE_ASSETS = [
  '/', '/index.html',
  '/blog.html', '/directory.html',
  '/about.html', '/contact.html',
  '/thanks.html', '/privacy.html',
  '/accessibility.html',
  '/assets/css/tokens-forest-honey.css',
  '/assets/css/site.css',
  '/assets/js/site.js',
  '/img/favicon-16.png',
  '/img/favicon-32.png',
  '/img/favicon.webp',
  '/img/favicon.svg',
  '/img/icon-192.png',
  '/img/icon-512.png',
  '/manifest.webmanifest',
  '/sitemap.xml', '/feed.xml',

  // Precache Pooh hero images
  '/img/pooh/pooh-hero.webp',
  '/img/pooh/pooh_091.webp',
  '/img/pooh/pooh_094-1.webp',
  '/img/pooh/pooh_103.webp',
  '/img/pooh/pooh_105.webp',
  '/img/pooh/pooh_112.webp',
  '/img/pooh/pooh_115.webp',
  '/img/pooh/pooh_131.webp',
  '/img/pooh/pooh_139.webp',
  '/img/pooh/pooh_143.webp',
  '/img/pooh/pooh_150.webp',
  '/img/pooh/pooh_16.webp',
  '/img/pooh/pooh_172.webp',
  '/img/pooh/pooh_174.webp',
  '/img/pooh/pooh_175.webp'
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

// Cache-first for static assets
async function cacheFirst(req) {
  const cache = await caches.open(BPC_STATIC_CACHE);
  const cached = await cache.match(req);
  if (cached) return cached;
  try {
    const res = await fetch(req);
    if (res && res.ok) cache.put(req, res.clone());
    return res;
  } catch (e) {
    return cached;
  }
}

// Network-first for HTML pages
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

  if (url.origin !== location.origin) return;

  if (request.mode === 'navigate' ||
      (request.headers.get('accept') || '').includes('text/html')) {
    event.respondWith(networkFirst(request));
    return;
  }

  if (/\.(?:css|js|png|jpg|jpeg|webp|svg|ico|xml|json)$/.test(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }
});
