/* Offline cache for the simak web companion. Bump CACHE on every deploy so
   old assets never linger. */
var CACHE = 'simak-v0.3.2';
var ASSETS = [
  './',
  'index.html',
  'style.css',
  'app.js',
  'data.js',
  'manifest.webmanifest',
  'icon.png'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      // Fetch each asset with a per-cache query and cache: 'reload'. A plain
      // addAll can be answered by a previous worker's cache-first fetch
      // handler or by the HTTP cache, which would fill the NEW cache with
      // the OLD assets and strand the update again.
      return Promise.all(ASSETS.map(function (asset) {
        return fetch(asset + '?sw=' + CACHE, { cache: 'reload' }).then(function (response) {
          if (!response.ok) throw new Error('precache failed: ' + asset);
          return cache.put(asset, response);
        });
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (key) {
        if (key !== CACHE) return caches.delete(key);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (event) {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then(function (hit) {
      return hit || fetch(event.request).then(function (response) {
        if (response.ok && event.request.url.indexOf(self.location.origin) === 0) {
          var copy = response.clone();
          caches.open(CACHE).then(function (cache) { cache.put(event.request, copy); });
        }
        return response;
      });
    })
  );
});
