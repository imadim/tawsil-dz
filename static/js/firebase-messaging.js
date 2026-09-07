/* ============================================================
   إشعارات Firebase (اختيارية)
   ------------------------------------------------------------
   الإشعارات الأساسية في التطبيق تعمل عبر Socket.IO و Service Worker
   الخاص بالـ PWA (‎/sw.js‎) — انظر base.html. هذا الملف يضيف Firebase
   فقط لمن يريد إشعارات Push تصل والتطبيق مغلق تماماً لأيام.

   لا يفعل شيئاً ما لم تُضبط مفاتيح حقيقية في window.FIREBASE_CONFIG.
   الكود القديم كان يستدعي messaging.useServiceWorker() وهي دالة
   أُزيلت من Firebase 9، فكان يرمي خطأ في كل صفحة.
   ============================================================ */

(function () {
    'use strict';

    const cfg = window.FIREBASE_CONFIG;

    // بلا إعدادات حقيقية لا نحمّل شيئاً — ولا نرمي أخطاء في الطرفية
    if (!cfg || !cfg.apiKey || String(cfg.apiKey).startsWith('YOUR_')) {
        return;
    }
    if (typeof firebase === 'undefined' || !firebase.messaging) {
        console.warn('Firebase SDK غير محمّل — تُستعمل إشعارات Socket.IO وحدها');
        return;
    }
    if (!('serviceWorker' in navigator) || !('Notification' in window)) {
        return;
    }

    try {
        firebase.initializeApp(cfg);
        const messaging = firebase.messaging();

        navigator.serviceWorker.register('/firebase-messaging-sw.js')
            .then(function (registration) {
                if (Notification.permission !== 'granted') return null;
                // الطريقة الحديثة: تمرير التسجيل إلى getToken مباشرة
                return messaging.getToken({
                    vapidKey: cfg.vapidKey,
                    serviceWorkerRegistration: registration
                });
            })
            .then(function (token) {
                if (!token) return;
                return fetch('/api/push/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: token })
                }).catch(function () { /* التسجيل اختياري */ });
            })
            .catch(function (err) {
                console.warn('تعذّر تفعيل إشعارات Firebase:', err && err.message);
            });

        messaging.onMessage(function (payload) {
            const n = (payload && payload.notification) || {};
            if (typeof showToast === 'function') {
                showToast(n.title || 'توصيل DZ', n.body || '');
            }
        });
    } catch (err) {
        console.warn('تعذّر تهيئة Firebase:', err && err.message);
    }
})();
