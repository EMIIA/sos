// sw-auto.js - Service Worker для автоматических уведомлений
const CACHE_NAME = 'pwa-auto-v1';

self.addEventListener('install', (event) => {
    console.log('🔔 Auto Service Worker: Установка');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('🚀 Auto Service Worker: Активация');
    event.waitUntil(self.clients.claim());
});

// Обработка кликов по уведомлениям - НЕ сбрасываем бейдж!
self.addEventListener('notificationclick', (event) => {
    console.log('🔔 Уведомление кликнуто (бейдж НЕ сбрасывается)');
    event.notification.close();

    // НЕ сбрасываем бейдж при клике - только при закрытии приложения
    // navigator.clearAppBadge() вызывается только при полном закрытии PWA

    event.waitUntil(
        clients.matchAll({type: 'window'}).then((clientList) => {
            for (const client of clientList) {
                if (client.url.includes('emiia.ai') && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(event.notification.data?.url || '/');
            }
        })
    );
});

// Фоновая синхронизация для проверки новых уведомлений
self.addEventListener('sync', (event) => {
    if (event.tag === 'check-notifications') {
        console.log('🔄 Фоновая проверка уведомлений');
        event.waitUntil(checkForNotifications());
    }
});

async function checkForNotifications() {
    // Здесь можно добавить логику проверки новых уведомлений с сервера
    console.log('Проверка новых данных для уведомлений...');
    
    // Имитация получения новых уведомлений
    if (Math.random() > 0.7) {
        const notificationOptions = {
            body: 'Обновление данных завершено',
            icon: '/icons/icon-192x192.png',
            badge: '/icons/badge-72x72.png',
            tag: 'background-sync',
            data: { type: 'background' }
        };
        
        await self.registration.showNotification('EMIIA.AI', notificationOptions);
    }
}

// Периодическая фоновая синхронизация
self.addEventListener('periodicsync', (event) => {
    if (event.tag === 'periodic-notification-check') {
        console.log('⏰ Периодическая проверка уведомлений');
        event.waitUntil(checkForNotifications());
    }
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
