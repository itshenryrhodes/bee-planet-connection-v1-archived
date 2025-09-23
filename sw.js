// sw.js — self-destruct & cache purge
self.addEventListener('install', (event) => {
  // Take control immediately
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    // Delete all caches
    const names = await caches.keys();
    await Promise.all(names.map((n) => caches.delete(n)));

    // Unregister this SW
    await self.registration.unregister();

    // Force-refresh all open tabs
    const clientsList = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const client of clientsList) {
      try {
        const url = new URL(client.url);
        url.searchParams.set('nocache', Date.now().toString());
        client.navigate(url.toString());
      } catch (_) {}
    }

    // Claim control during this cycle (then we're gone)
    await self.clients.claim();
  })());
});

// Always go to network (no caching)
self.addEventListener('fetch', (event) => {
  event.respondWith(fetch(event.request));
});
