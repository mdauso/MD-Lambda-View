// MD-Lambda-View PWA Service Worker
// Bump CACHE_VERSION on every release to force update
const CACHE_VERSION = 'v7';
const CACHE_NAME = `mdlv-${CACHE_VERSION}`;

// App-shell files (same origin) — always pre-cached on install
const APP_SHELL = [
  './',
  './index.html',
  './2d.html',
  './3d.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-192.png',
  './icons/icon-maskable-512.png',
  './icons/logo-hero.png'
];

// CDN URLs — cached on first use (runtime cache)
const CDN_HOSTS = [
  'cdn.jsdelivr.net',
  'cdnjs.cloudflare.com',
  'unpkg.com',
  'cdn.plot.ly',
  'fonts.googleapis.com',
  'fonts.gstatic.com'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  const sameOrigin = url.origin === self.location.origin;
  const isCdn = CDN_HOSTS.some(h => url.hostname.endsWith(h));

  // Same-origin: cache-first (app shell)
  if (sameOrigin) {
    event.respondWith(
      caches.match(req).then(cached => cached || fetch(req).then(resp => {
        if (resp.ok) {
          const copy = resp.clone();
          caches.open(CACHE_NAME).then(c => c.put(req, copy));
        }
        return resp;
      }).catch(() => cached || new Response('Offline', { status: 503 })))
    );
    return;
  }

  // CDN: stale-while-revalidate
  if (isCdn) {
    event.respondWith(
      caches.match(req).then(cached => {
        const network = fetch(req).then(resp => {
          if (resp.ok) {
            const copy = resp.clone();
            caches.open(CACHE_NAME).then(c => c.put(req, copy));
          }
          return resp;
        }).catch(() => cached);
        return cached || network;
      })
    );
  }
});
