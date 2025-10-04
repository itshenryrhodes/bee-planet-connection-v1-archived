---
permalink: /sw.js
layout: null
---

/* Bee Planet Connection Service Worker â€” auto-versioned */
const BUILD_TS = '{{ site.time | date: "%Y%m%d%H%M%S" }}';
const CACHE_NAME = `bpc-${BUILD_TS}`;

const PRECACHE = [
  `/?v=${BUILD_TS}`,
  `/index.html?v=${BUILD_TS}`,
  `/assets/css/site.css?v=${BUILD_TS}`,
  `/img/icons/logo-64.png?v=${BUILD_TS}`,
  `/manifest.webmanifest?v=${BUILD_TS}`
];

async function putInCache(request, response) {
  try { const cache = await caches.open(CACHE_NAME); await cache.put(request, response.clone()); } catch (_) {}
}

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    try { await cache.addAll(PRECACHE); } catch (_) {}
  })());
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((k) => (k !== CACHE_NAME ? caches.delete(k) : undefined)));
    await self.clients.claim();
  })());
});

function isHTML(req){ return (req.headers.get('accept')||'').includes('text/html'); }
function isCSS(req){ return req.destination === 'style' || req.url.endsWith('.css'); }
function isScript(req){ return req.destination === 'script' || req.url.endsWith('.js'); }
function isAsset(req){
  return ['image','font'].includes(req.destination) ||
    /\.(png|jpe?g|webp|gif|svg|ico|woff2?|ttf|eot)$/.test(new URL(req.url).pathname);
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  if (isHTML(request)) {
    // Network-first for documents
    event.respondWith((async () => {
      try {
        const net = await fetch(request, { cache: 'no-store' });
        const u = new URL(request.url); u.searchParams.set('v', BUILD_TS);
        await putInCache(u.toString(), net);
        return net.clone();
      } catch {
        const cache = await caches.open(CACHE_NAME);
        return (await cache.match(request)) || (await cache.match('/')) || new Response('Offline', { status: 503 });
      }
    })());
    return;
  }

  if (isCSS(request)) {
    // Network-first for CSS so style tweaks appear immediately
    event.respondWith((async () => {
      try {
        const net = await fetch(request, { cache: 'no-store' });
        await putInCache(request, net);
        return net.clone();
      } catch {
        const cache = await caches.open(CACHE_NAME);
        return (await cache.match(request)) || new Response('', { status: 504 });
      }
    })());
    return;
  }

  if (isScript(request)) {
    // Stale-while-revalidate for JS
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(request);
      const fetchPromise = fetch(request).then((resp) => { putInCache(request, resp); return resp.clone(); }).catch(()=>undefined);
      return cached || (await fetchPromise) || new Response('', { status: 504 });
    })());
    return;
  }

  if (isAsset(request)) {
    // Cache-first for images/fonts
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(request);
      if (cached) { fetch(request).then((resp)=>putInCache(request, resp)).catch(()=>{}); return cached; }
      try {
        const net = await fetch(request);
        await putInCache(request, net);
        return net.clone();
      } catch { return new Response('', { status: 504 }); }
    })());
    return;
  }

  // Default passthrough
  event.respondWith(fetch(request).catch(async () => {
    const cache = await caches.open(CACHE_NAME);
    return (await cache.match(request)) || new Response('', { status: 504 });
  }));
});

self.addEventListener('message', (event) => {
  if (event && event.data === 'SKIP_WAITING') self.skipWaiting();
});


