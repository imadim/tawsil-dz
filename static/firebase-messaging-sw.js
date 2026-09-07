/* Service Worker لإشعارات Firebase.
   لا يُهيَّأ بمفاتيح وهمية — الإشعارات الأساسية تعمل عبر /sw.js و Socket.IO.
   عند امتلاك مشروع Firebase حقيقي، ضع إعداداته مكان القيم أدناه. */

const FB = {
  apiKey: "",
  authDomain: "",
  projectId: "",
  storageBucket: "",
  messagingSenderId: "",
  appId: ""
};

if (FB.apiKey) {
  importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js');
  importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js');
  firebase.initializeApp(FB);
}

const messaging = FB.apiKey ? firebase.messaging() : null;

if (messaging) messaging.onBackgroundMessage((payload) => {
  console.log('Background Message:', payload);
  
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/static/images/logo.png',
    badge: '/static/images/badge.png'
  };
  
  self.registration.showNotification(notificationTitle, notificationOptions);
});