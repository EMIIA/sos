self.addEventListener('push', event => {
    const options = {
        body: event.data ? event.data.text() : 'Напоминание: SIP',
        icon: '/vv.jpg',
        badge: '/vv.jpg',
        data: { url: 'https://sos.emiia.ai/vv1.html?pwa=true' }
    };
    event.waitUntil(self.registration.showNotification('EMIIA.AI SIP', options));
});

self.addEventListener('notificationclick', event => {
    event.notification.close();
    event.waitUntil(clients.openWindow(event.notification.data.url));
});
