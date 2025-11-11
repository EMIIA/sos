// sw-push.js - Service Worker для Push уведомлений и бейджей
const CACHE_NAME = 'pwa-push-v1';

// Установка
self.addEventListener('install', (event) => {
  console.log('🛠️ Push Service Worker: Установка');
  self.skipWaiting();
});

// Активация
self.addEventListener('activate', (event) => {
  console.log('🚀 Push Service Worker: Активация');
  event.waitUntil(self.clients.claim());
});

// Обработка PUSH сообщений
self.addEventListener('push', (event) => {
  console.log('📨 Получено Push сообщение', event);
  
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = {
      title: 'EMIIA.AI',
      body: 'Новое уведомление',
      badgeCount: 1
    };
  }

  const badgeCount = data.badgeCount || 1;
  const title = data.title || 'EMIIA.AI';
  const body = data.body || 'Пространственный интеллект';

  const options = {
    body: body,
    icon: '/192x192.png',
    badge: '/badge-72.png',
    tag: data.tag || 'general',
    renotify: true,
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/',
      badgeCount: badgeCount,
      timestamp: Date.now()
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
    Promise.all([
      self.registration.showNotification(title, options),
      setBadge(badgeCount)
    ])
  );
});

// Клик по уведомлению
self.addEventListener('notificationclick', (event) => {
  console.log('🔔 Клик по уведомлению');
  event.notification.close();

  const urlToOpen = event.notification.data.url || '/';

  // Сбрасываем бейдж при открытии
  setBadge(0);

  event.waitUntil(
    clients.matchAll({type: 'window'}).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes('emiia.ai') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// Управление бейджами
async function setBadge(count) {
  try {
    if (navigator.setAppBadge) {
      await navigator.setAppBadge(count);
      console.log(`🔴 Бейдж установлен: ${count}`);
    } else if (self.registration && self.registration.setAppBadge) {
      await self.registration.setAppBadge(count);
    }
  } catch (error) {
    console.log('❌ Ошибка установки бейджа:', error);
  }
}

// Fetch events
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        return response || fetch(event.request);
      })
  );
});
