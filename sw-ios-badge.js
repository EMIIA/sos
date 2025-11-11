// sw-ios-badge.js - Service Worker для iOS бейджей
self.addEventListener('install', (event) => {
    console.log('📱 iOS Badge Service Worker: Установка');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('🚀 iOS Badge Service Worker: Активация');
    event.waitUntil(self.clients.claim());
});

// Обработка кликов по уведомлениям - сбрасываем бейдж
self.addEventListener('notificationclick', (event) => {
    console.log('🔔 Уведомление кликнуто - сбрасываем бейдж');
    event.notification.close();

    // Сбрасываем бейдж при открытии уведомления
    if (navigator.clearAppBadge) {
        navigator.clearAppBadge().then(() => {
            console.log('✅ Бейдж сброшен после клика');
        });
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

// Фоновая синхронизация для обновления бейджей
self.addEventListener('sync', (event) => {
    if (event.tag === 'update-badges') {
        console.log('🔄 Фоновая синхронизация бейджей');
        event.waitUntil(updateBadgesFromServer());
    }
});

async function updateBadgesFromServer() {
    // Здесь можно получить количество новых уведомлений с сервера
    // и обновить бейдж соответственно
    console.log('Проверка новых уведомлений для бейджа...');
}
