// sw-ios-fixed-v2.js - Service Worker с исправлением для множественных уведомлений iOS
const CACHE_NAME = 'pwa-ios-fixed-v2';

self.addEventListener('install', (event) => {
    console.log('🍎 iOS Fixed v2 Service Worker: Установка');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('🚀 iOS Fixed v2 Service Worker: Активация');
    event.waitUntil(self.clients.claim());
});

// Исправленная обработка уведомлений для iOS
self.addEventListener('notificationclick', (event) => {
    console.log('🔔 iOS Fixed: Уведомление кликнуто:', event.notification.tag);
    event.notification.close();

    // НЕ сбрасываем бейдж при клике
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

// Важно: очищаем старые уведомления при активации
self.addEventListener('activate', (event) => {
    event.waitUntil(
        self.registration.getNotifications().then(notifications => {
            console.log(`🗑️ Очистка старых уведомлений: ${notifications.length}`);
            notifications.forEach(notification => {
                notification.close();
            });
        })
    );
});

// Простое кэширование
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                return response || fetch(event.request);
            })
    );
});
