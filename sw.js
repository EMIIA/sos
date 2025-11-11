// sw.js - Enhanced Service Worker with Push Notifications
const CACHE_NAME = 'pwa-spatial-push-v1';
const urlsToCache = [
  '/',
  '/vv.html',
  '/telegram-web-app.js',
  '/logo_wms.svg',
  '/vv.ico',
  '/vvjpg.jpg',
  '/vv.webmanifest',
  '/192x192.png'
];

// Установка
self.addEventListener('install', function(event) {
  console.log('🛠️ Service Worker: Установка с Push');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Активация
self.addEventListener('activate', function(event) {
  console.log('🚀 Service Worker: Активация');
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Push уведомления
self.addEventListener('push', function(event) {
  console.log('📨 Получено Push-сообщение', event);
  
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = {
      title: 'EMIIA.AI',
      body: 'Новое сообщение',
      icon: '/logo_wms.svg'
    };
  }

  const options = {
    body: data.body || 'Пространственный интеллект',
    icon: data.icon || '/logo_wms.svg',
    badge: '/vv.ico',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || 'https://sos.emiia.ai/vv1.html'
    },
    actions: [
      {
        action: 'open',
        title: 'Открыть'
      },
      {
        action: 'close',
        title: 'Закрыть'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'EMIIA.AI', options)
  );
});

// Клик по уведомлению
self.addEventListener('notificationclick', function(event) {
  console.log('🔔 Клик по уведомлению:', event.notification.tag);
  event.notification.close();

  event.waitUntil(
    clients.matchAll({type: 'window'}).then(function(clientList) {
      // Ищем открытое окно
      for (const client of clientList) {
        if (client.url.includes('emiia.ai') && 'focus' in client) {
          return client.focus();
        }
      }
      // Открываем новое окно
      if (clients.openWindow) {
        return clients.openWindow(event.notification.data.url || '/');
      }
    })
  );
});

// Закрытие уведомления
self.addEventListener('notificationclose', function(event) {
  console.log('❌ Уведомление закрыто:', event.notification.tag);
});

// Fetch events
self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        return response || fetch(event.request);
      })
  );
});
