// sw-ios-fixed.js - Service Worker с iOS фиксами
const CACHE_NAME = 'pwa-ios-fixed-v1';

self.addEventListener('install', (event) => {
    console.log('🍎 iOS Service Worker: Установка');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('🚀 iOS Service Worker: Активация');
    event.waitUntil(self.clients.claim());
});

// Упрощенная обработка уведомлений для iOS
self.addEventListener('notificationclick', (event) => {
    console.log('🔔 iOS: Уведомление кликнуто');
    event.notification.close();

    // На iOS НЕ сбрасываем бейдж при клике
    event.waitUntil(
        clients.matchAll({type: 'window'}).then((clientList) => {
            // Пытаемся найти открытое окно
            for (const client of clientList) {
                if (client.url.includes('emiia.ai') && 'focus' in client) {
                    return client.focus();
                }
            }
            // Открываем новое окно если приложение закрыто
            if (clients.openWindow) {
                return clients.openWindow('/');
            }
        })
    );
});

// Простое кэширование для iOS
self.addEventListener('fetch', (event) => {
    // На iOS кэшируем только основные ресурсы
    if (event.request.url.includes('/vv.html') || 
        event.request.url.includes('/logo_wms.svg') ||
        event.request.url.includes('/icons/')) {
        
        event.respondWith(
            caches.match(event.request)
                .then((response) => {
                    return response || fetch(event.request);
                })
        );
    } else {
        // Для остальных запросов - сеть
        event.respondWith(fetch(event.request));
    }
});
