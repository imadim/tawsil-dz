// Firebase configuration
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "delivery-dz.firebaseapp.com",
  projectId: "delivery-dz",
  storageBucket: "delivery-dz.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Request permission and get token
function requestNotificationPermission() {
    return Notification.requestPermission().then((permission) => {
        if (permission === 'granted') {
            console.log('✅ Notification permission granted');
            return messaging.getToken({
                vapidKey: 'YOUR_VAPID_KEY'  // Get from Firebase Console
            });
        } else {
            console.log('❌ Notification permission denied');
            return null;
        }
    }).then((token) => {
        if (token) {
            console.log('FCM Token:', token);
            // Send token to server
            registerFCMToken(token);
        }
    }).catch((err) => {
        console.error('Error getting token:', err);
    });
}

function registerFCMToken(token) {
    fetch('/api/fcm/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: token })
    })
    .then(response => response.json())
    .then(data => {
        console.log('✅ FCM token registered');
    })
    .catch(error => {
        console.error('❌ Error registering token:', error);
    });
}

// Handle foreground messages
messaging.onMessage((payload) => {
    console.log('Message received:', payload);
    
    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/static/images/logo.png'
    };
    
    new Notification(notificationTitle, notificationOptions);
});

// Auto-request permission on page load
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/firebase-messaging-sw.js')
        .then((registration) => {
            console.log('✅ Service Worker registered');
            messaging.useServiceWorker(registration);
            requestNotificationPermission();
        })
        .catch((err) => {
            console.error('❌ Service Worker registration failed:', err);
        });
}