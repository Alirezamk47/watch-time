// Watch Time Service Worker — update-friendly, with offline fallback.
const CACHE = 'watch-time-shell-v2';

const SHELL = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon.svg',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) =>
            key.startsWith('watch-time-shell-') &&
            key !== CACHE
          )
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Ignore external requests and non-GET requests.
  if (
    url.origin !== self.location.origin ||
    request.method !== 'GET'
  ) {
    return;
  }

  event.respondWith((async () => {
    const cache = await caches.open(CACHE);

    try {
      // Network first: get the latest version from GitHub Pages.
      const response = await fetch(request, {
        cache: 'no-store'
      });

      if (response && response.ok) {
        await cache.put(request, response.clone());
      }

      return response;
    } catch (error) {
      // If offline, use the cached version.
      const cached = await caches.match(request);

      if (cached) {
        return cached;
      }

      // If navigating while offline, show the cached app.
      if (request.mode === 'navigate') {
        const appShell =
          await caches.match('./index.html') ||
          await caches.match('./');

        if (appShell) {
          return appShell;
        }
      }

      return new Response(
        'You are offline and this resource is not cached.',
        {
          status: 503,
          statusText: 'Service Unavailable',
          headers: {
            'Content-Type': 'text/plain; charset=utf-8'
          }
        }
      );
    }
  })());
});
