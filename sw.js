// Установка
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open('emiia-ai-v1').then(cache => {
            return cache.addAll([
                '/',
                '/vv.html',
                '/logo_wms.svg',
                '/vv.jpg'
            ]);
        })
    );
});

// Активация
self.addEventListener('activate', event => {
    event.waitUntil(self.clients.claim());
});

// Пуш-уведомление
self.addEventListener('push', event => {
    const options = {
        body: event.data ? event.data.text() : 'Новое уведомление от EMIIA.AI',
        icon: '/vv.jpg',
        badge: '/vv.jpg',
        vibrate: [200, 100, 200],
        data: {
            url: 'https://sos.emiia.ai/vv1.html'
        },
        actions: [
            {
                action: 'open',
                title: 'Открыть'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('EMIIA.AI SIP', options)
    );
});

// Клик по уведомлению
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    if (event.action === 'open') {
        event.waitUntil(
            clients.openWindow(event.notification.data.url)
        );
    }
});
