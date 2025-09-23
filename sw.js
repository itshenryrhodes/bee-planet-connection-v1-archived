/* Bee Planet Connection Service Worker
   Auto-versioned on each deploy via Jekyll timestamp.
   Strategy:
   - HTML: network-first (fresh content), fallback to cache when offline.
   - CSS/JS: stale-while-revalidate (fast on repeat visits, updates in background).
   - Images/fonts: cache-first with background refresh.
   - Everything tied to a deploy-specific CACHE_NAME, so new deploys invalidate old caches automatically.
*/

/* Jekyll injects the build time here (UTC). Every publish ⇒ new cache. */
const BUILD_TS = '{{ site.time | date: "%Y%m%d%H%M%S" }}';
const CACHE_NAME = `bpc-${BUILD_TS}`;

/* Precache a few critical URLs. Add more if needed. Use a version query so SW matches exactly this build. */
const PRECACHE = [
  `/?v=${BUILD_TS}`,
  `/index.html?v=${BUILD_TS}`,
  `/assets/css/site.css?v=${BUILD_TS}`,
  `/img/icons/logo-64.png?v=${BUILD_TS}`,
  `/manifest.webmanifest?v=${BUILD_TS}`
];

/* Utility: put a response clone into cache safely. */
async function putInCache(request, response) {
  try {
    const cache = await caches.open(CACHE_NAME);
    await cache.put(request, response.clone());
  } catch (_) { /* no-op */ }
}

/* Install: warm the cache with core assets. */
self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      try {
        await cache.addAll(PRECACHE);
      } catch (_) {
        // If any pre-cache fails (e.g., first deploy path mismatch), continue anyway.
      }
    })()
  );
  self.skipWaiting();
});

/* Activate: clean up old caches. */
self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => (k !== CACHE_NAME ? caches.delete(k) : undefined)));
      await self.clients.claim();
    })()
  );
});

/* Routing helpers */
function isHTML(req) {
  const accept = req.headers.get('accept') || '';
  return accept.includes('text/html');
}
function isCSS(req) {
  return req.destination === 'style' || req.url.endsWith('.css');
}
function isScript(req) {
  return req.destination === 'script' || req.url.endsWith('.js');
}
function isAsset(req) {
  return ['image', 'font'].includes(req.destination) ||
         /\.(png|jpe?g|webp|gif|svg|ico|woff2?|ttf|eot)$/.test(new URL(req.url).pathname);
}

/* Fetch handler:
   - HTML: Network-first.
   - CSS/JS: Stale-while-revalidate.
   - Images/Fonts: Cache-first.
   - Other: passthrough (attempt network, fall back to cache).
*/
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Only handle GET
  if (request.method !== 'GET') return;

  if (isHTML(request)) {
    // Network-first for documents
    event.respondWith((async () => {
      try {
        const net = await fetch(request, { cache: 'no-store' });
        // Cache a versioned copy (attach v to help isolation)
        const u = new URL(request.url);
        u.searchParams.set('v', BUILD_TS);
        await putInCache(u.toString(), net);
        return net.clone();
      } catch (_) {
        const cache = await caches.open(CACHE_NAME);
        const cached = await cache.match(request) || await cache.match('/');
        return cached || new Response('Offline', { status: 503, statusText: 'Offline' });
      }
    })());
    return;
  }

  if (isCSS(request) || isScript(request)) {
    // Stale-while-revalidate
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(request);
      const fetchPromise = fetch(request).then((resp) => {
        putInCache(request, resp);
        return resp.clone();
      }).catch(() => undefined);
      return cached || (await fetchPromise) || new Response('', { status: 504 });
    })());
    return;
  }

  if (isAsset(request)) {
    // Cache-first for images/fonts
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(request);
      if (cached) {
        // Refresh in background
        fetch(request).then((resp) => putInCache(request, resp)).catch(() => {});
        return cached;
      }
      try {
        const net = await fetch(request);
        await putInCache(request, net);
        return net.clone();
      } catch (_) {
        return new Response('', { status: 504 });
      }
    })());
    return;
  }

  // Default: try network, fall back to cache
  event.respondWith((async () => {
    try {
      return await fetch(request);
    } catch (_) {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(request);
      return cached || new Response('', { status: 504 });
    }
  })());
});

/* Optional: allow a page to tell SW to activate immediately */
self.addEventListener('message', (event) => {
  if (event && event.data === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
