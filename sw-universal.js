// sw-universal.js - Универсальный Service Worker для всех платформ
const CACHE_NAME = 'pwa-universal-v1';

self.addEventListener('install', (event) => {
    console.log('🌍 Universal Service Worker: Установка');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('🚀 Universal Service Worker: Активация');
    event.waitUntil(self.clients.claim());
});

// Универсальная обработка уведомлений
self.addEventListener('notificationclick', (event) => {
    console.log('🔔 Уведомление кликнуто:', event.notification.tag);
    event.notification.close();

    // Сбрасываем бейдж при открытии
    if (navigator.clearAppBadge) {
        navigator.clearAppBadge().catch(err => {
            console.log('❌ Ошибка сброса бейджа:', err);
        });
    }

    // Открываем/фокусируем приложение
    event.waitUntil(
        clients.matchAll({type: 'window'}).then((clientList) => {
            // Ищем открытое окно
            for (const client of clientList) {
                if (client.url.includes('emiia.ai') && 'focus' in client) {
                    return client.focus();
                }
            }
            // Открываем новое окно если нет открытых
            if (clients.openWindow) {
                return clients.openWindow(event.notification.data?.url || '/');
            }
        })
    );
});

// Обработка закрытия уведомления
self.addEventListener('notificationclose', (event) => {
    console.log('📪 Уведомление закрыто:', event.notification.tag);
});

// Простой кэширование
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                return response || fetch(event.request);
            })
    );
});
