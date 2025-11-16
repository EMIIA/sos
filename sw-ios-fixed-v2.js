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

// Обработка сообщений от главного потока для сброса бейджа
self.addEventListener('message', (event) => {
    console.log('📨 Service Worker получил сообщение:', event.data);
    
    if (event.data && event.data.type === 'CLEAR_BADGE') {
        console.log('🔄 Сброс бейджа из Service Worker');
        
        // Сброс бейджа
        if (self.setAppBadge) {
            self.setAppBadge(0).then(() => {
                console.log('✅ Бейдж сброшен из Service Worker');
            }).catch(error => {
                console.log('❌ Ошибка сброса бейджа:', error);
            });
        }
        
        // Очистка всех уведомлений
        event.waitUntil(
            self.registration.getNotifications().then(notifications => {
                console.log(`🗑️ Очистка ${notifications.length} уведомлений`);
                notifications.forEach(notification => {
                    notification.close();
                });
            })
        );
    }
});

// Исправленная обработка уведомлений для iOS
self.addEventListener('notificationclick', (event) => {
    console.log('🔔 iOS Fixed: Уведомление кликнуто:', event.notification.tag);
    event.notification.close();

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

// Очистка старых уведомлений при активации
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
