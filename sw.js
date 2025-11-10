// 📄 Файл: sw.js

self.addEventListener('push', function(event) {
  const data = event.data ? event.data.json() : {};
  
  const options = {
    body: data.body || 'EMIIA.AI SIP',
    icon: data.icon || 'https://sos.emiia.ai/192x192.png',
    badge: 'https://sos.emiia.ai/192x192.png',
    vibrate: [200, 100, 200],
    data: {
      click_action: data.click_action || 'https://sos.emiia.ai/vv1.html',
      url: data.click_action || 'https://sos.emiia.ai/vv1.html'
    },
    actions: [
      {
        action: 'open',
        title: 'Открыть'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(
      data.title || 'EMIIA.AI SIP',
      options
    )
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = event.notification.data.url;
  
  event.waitUntil(
    clients.openWindow(url)
  );
});
