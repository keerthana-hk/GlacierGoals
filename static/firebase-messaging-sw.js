importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyBCDDWJxWOhjQp7C94DJaah-sD-roGUUQg",
  authDomain: "glaciergoals-58aac.firebaseapp.com",
  projectId: "glaciergoals-58aac",
  storageBucket: "glaciergoals-58aac.firebasestorage.app",
  messagingSenderId: "747030101668",
  appId: "1:747030101668:web:3b8d7326b2c65365767031"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/static/images/blue_penguin_single.png'
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});
