import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getMessaging, getToken, onMessage } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-messaging.js";

const firebaseConfig = {
  apiKey: "AIzaSyBCDDWJxWOhjQp7C94DJaah-sD-roGUUQg",
  authDomain: "glaciergoals-58aac.firebaseapp.com",
  projectId: "glaciergoals-58aac",
  storageBucket: "glaciergoals-58aac.firebasestorage.app",
  messagingSenderId: "747030101668",
  appId: "1:747030101668:web:3b8d7326b2c65365767031"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

export async function requestNotificationPermission() {
    try {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            console.log('Notification permission granted.');
            // Get the token from FCM
            const currentToken = await getToken(messaging, { 
                vapidKey: 'BE_rEo8x630K3NCzt1I2OM_w2HJ-QW05pdNdjVbLn9qkXkbJrw8Ym2PeBQJgtzO2z42VZtLMMy_UqGdn2JWqH98' 
            });
            
            if (currentToken) {
                console.log('FCM Token generated. Sending to server...');
                // Ensure this connects to the newly added Flask route
                await fetch('/api/save-fcm-token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: currentToken })
                });
                alert("Push Notifications enabled!");
            } else {
                console.log('No registration token available. Request permission to generate one.');
            }
        } else {
            console.log('Notification permission denied.');
        }
    } catch (err) {
        console.error('An error occurred while retrieving token. ', err);
    }
}
window.requestNotificationPermission = requestNotificationPermission;

// Intercept push notifications if the user is actively viewing the web app
onMessage(messaging, (payload) => {
    console.log('Message received in foreground: ', payload);
    // Refresh the local notification bell UI automatically
    if(typeof loadNotifications === 'function') {
        loadNotifications();
    }
});
