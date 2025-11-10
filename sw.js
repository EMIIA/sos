// /sw.js
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'EMIIA.AI SIP',
    icon: '/192x192.png',
    badge: '/192x192.png',
    vibrate: [200, 100, 200],
    data: { url: 'https://sos.emiia.ai/vv1.html' }
  };
  event.waitUntil(self.registration.showNotification('EMIIA.AI SIP', options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data.url));
});
