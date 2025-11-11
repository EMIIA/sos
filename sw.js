// sw.js - Service Worker для PWA
const CACHE_NAME = 'pwa-spatial-v1';
const urlsToCache = [
  '/',
  '/vv.html',
  '/telegram-web-app.js',
  '/logo_wms.svg',
  '/vv.ico',
  '/vvjpg.jpg',
  '/vv.webmanifest'
];

// Установка и кэширование
self.addEventListener('install', function(event) {
  console.log('🛠️ Service Worker: Установка');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('📦 Кэшируем файлы');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('✅ Все файлы закэшированы');
        return self.skipWaiting();
      })
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
            console.log('🗑️ Удаляем старый кэш:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('✅ Service Worker активирован');
      return self.clients.claim();
    })
  );
});

// Перехват запросов
self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Возвращаем кэш или сетевой запрос
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

// Обработка push-уведомлений (для теста)
self.addEventListener('push', function(event) {
  console.log('📨 Получено push-уведомление');
  
  const options = {
    body: 'Пространственный интеллект готов к работе!',
    icon: '/logo_wms.svg',
    badge: '/vv.ico',
    vibrate: [200, 100, 200],
    data: {
      url: 'https://sos.emiia.ai/vv1.html?pwa=true'
    }
  };

  event.waitUntil(
    self.registration.showNotification('EMIIA.AI SIP', options)
  );
});

// Клик по уведомлению
self.addEventListener('notificationclick', function(event) {
  console.log('🔔 Клик по уведомлению');
  event.notification.close();
  
  event.waitUntil(
    clients.matchAll({type: 'window'}).then(function(clientList) {
      // Открываем/фокусируем окно
      for (const client of clientList) {
        if (client.url === event.notification.data.url && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(event.notification.data.url);
      }
    })
  );
});
