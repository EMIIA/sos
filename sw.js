// sw-simple.js - Простой Service Worker для уведомлений
const CACHE_NAME = 'pwa-simple-v1';

self.addEventListener('install', function(event) {
    console.log('🛠️ Service Worker: Установка');
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    console.log('🚀 Service Worker: Активация');
    event.waitUntil(self.clients.claim());
});

// Обработка уведомлений (если будем использовать push)
self.addEventListener('notificationclick', function(event) {
    console.log('🔔 Уведомление кликнуто');
    event.notification.close();
    
    event.waitUntil(
        clients.matchAll({type: 'window'}).then(function(clientList) {
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
