/* توصيل DZ — Service Worker
   استراتيجية:
   - الصفحات (navigate): الشبكة أولاً، وعند انقطاع الاتصال نعرض صفحة offline
   - الملفات الثابتة: من الكاش أولاً مع تحديثها في الخلفية
   - لا نخزّن أي طلب API أو socket.io إطلاقاً (بيانات حيّة)
*/

const VERSION    = 'tawsil-v1';
const SHELL      = `${VERSION}-shell`;
const RUNTIME    = `${VERSION}-runtime`;
const OFFLINE_URL = '/offline';

const SHELL_ASSETS = [
  OFFLINE_URL,
  '/static/css/style.css',
  '/static/images/icon-192.png',
  '/static/images/icon-512.png',
  '/static/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL)
      .then((cache) => cache.addAll(SHELL_ASSETS).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => !k.startsWith(VERSION)).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // لا نتدخّل إطلاقاً في: غير GET، النطاقات الخارجية، socket.io، مسارات API
  if (req.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/socket.io')) return;
  if (url.pathname.startsWith('/api/')) return;

  // التنقّل بين الصفحات: الشبكة أولاً
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }

  // الملفات الثابتة: الكاش أولاً + تحديث صامت
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(req).then((cached) => {
        const network = fetch(req).then((res) => {
          if (res && res.status === 200) {
            const copy = res.clone();
            caches.open(RUNTIME).then((c) => c.put(req, copy));
          }
          return res;
        }).catch(() => cached);
        return cached || network;
      })
    );
  }
});

/* إشعار قادم من الخادم (يعمل حتى والتطبيق مغلق عند تفعيل Push لاحقاً) */
self.addEventListener('push', (event) => {
  let data = { title: 'توصيل DZ', body: 'عندك تحديث جديد' };
  try { if (event.data) data = event.data.json(); } catch (e) {}
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/static/images/icon-192.png',
      badge: '/static/images/icon-192.png',
      dir: 'rtl',
      lang: 'ar',
      vibrate: [120, 60, 120],
      data: { url: data.url || '/customer/dashboard' }
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
      for (const client of list) {
        if ('focus' in client) { client.navigate(target); return client.focus(); }
      }
      return clients.openWindow(target);
    })
  );
});
