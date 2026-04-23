const CACHE_NAME = 'glacier-cache-v8';
const urlsToCache = [
  '/',
  '/static/css/style.css?v=20',
  '/static/manifest.json'
];

// Install event — cache core assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache).catch(err => console.log('Cache error (ignored):', err));
      })
  );
  self.skipWaiting();
});

// Activate event — clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Fetch event — network first, fallback to cache
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || event.request.url.includes('/api/')) return;
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});

// ─── REAL PUSH NOTIFICATIONS ────────────────────────────────────────────────

// This fires when the server sends a push message
self.addEventListener('push', event => {
  let data = { title: '🧊 GlacierGoals', body: 'You have a new notification!' };
  try {
    if (event.data) {
      data = JSON.parse(event.data.text());
    }
  } catch(e) {}

  const options = {
    body: data.body,
    icon: data.icon || '/static/images/penguin_v2.jpg',
    badge: '/static/images/penguin_v2.jpg',
    vibrate: [200, 100, 200],
    data: { url: '/' },
    actions: [
      { action: 'open', title: '✅ Open App' },
      { action: 'close', title: '❌ Dismiss' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title || '🧊 GlacierGoals', options)
  );
});

// User tapped the notification — open the app
self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'close') return;
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(windowClients => {
      for (const client of windowClients) {
        if (client.url === '/' && 'focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow('/');
    })
  );
});
