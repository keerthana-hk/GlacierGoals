const CACHE_NAME = 'glacier-cache-v4';
const urlsToCache = [
  '/',
  '/static/css/style.css?v=16',
  '/static/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        // We use catch to ensure the worker installs even if some resources fail to load offline.
        return cache.addAll(urlsToCache).catch(err => console.log('Cache addAll error (ignored):', err));
      })
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  // Only handle GET requests and ignore API/Avatar requests caching for now
  if(event.request.method !== 'GET' || event.request.url.includes('/api/')) return;

  event.respondWith(
    fetch(event.request).catch(error => {
        return caches.match(event.request);
    })
  );
});
