// sw-simple.js - Простой Service Worker для уведомлений
const CACHE_NAME = 'pwa-simple-v1';

self.addEventListener('install', (event) => {
    console.log('🛠️ Service Worker: Установка');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker: Активация');
    event.waitUntil(self.clients.claim());
});

// Обработка уведомлений
self.addEventListener('notificationclick', (event) => {
    console.log('🔔 Уведомление кликнуто');
    event.notification.close();

    // Сбрасываем бейдж при открытии
    if (navigator.clearAppBadge) {
        navigator.clearAppBadge();
    }

    event.waitUntil(
        clients.matchAll({type: 'window'}).then((clientList) => {
            for (const client of clientList) {
                if (client.url.includes('emiia.ai') && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow('/');
            }
        })
    );
});

// Простая обработка fetch
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                return response || fetch(event.request);
            })
    );
});
