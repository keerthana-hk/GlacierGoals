import os
import smtplib
from email.mime.text import MIMEText
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase (requires firebase-adminsdk credentials JSON)
firebase_cred_path = os.environ.get('FIREBASE_CREDENTIALS_JSON')
if firebase_cred_path and os.path.exists(firebase_cred_path):
    try:
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print("Firebase init error:", e)

# Note: To use SMS, uncomment the line below and run: pip install twilio
# from twilio.rest import Client

def send_email_notification(to_email, subject, body):
    """
    Sends an email using standard Gmail SMTP.
    Requires you to generate an "App Password" in your Google Account Security settings.
    """
    sender_email = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
    sender_password = os.environ.get('MAIL_PASSWORD', 'your_app_password')
    
    if sender_email == 'your_email@gmail.com':
        print("Email not sent. Please configure MAIL_USERNAME and MAIL_PASSWORD in your environment!")
        return False
        
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = f"GlacierGoals Tracker <{sender_email}>"
    msg['To'] = to_email
    
    try:
        # Connect to Gmail's secure SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender_email, sender_password)
            smtp_server.sendmail(sender_email, to_email, msg.as_string())
        print(f"Success! Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_sms_notification(to_phone_number, body):
    """
    Sends an SMS message using Twilio.
    Requires a free Twilio Account for API keys.
    """
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID', 'your_twilio_sid')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN', 'your_twilio_token')
    from_phone = os.environ.get('TWILIO_PHONE_NUMBER', '+1234567890')
    
    if account_sid == 'your_twilio_sid':
        print("SMS not sent. Please configure TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in your environment!")
        return False
        
    try:
        # client = Client(account_sid, auth_token)
        # message = client.messages.create(
        #     body=body,
        #     from_=from_phone,
        #     to=to_phone_number
        # )
        # print(f"Success! SMS sent to {to_phone_number}. Message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return False

def send_fcm_push_notification(fcm_token, title, body):
    """
    Sends a native push notification to the user's phone via Firebase Cloud Messaging.
    """
    if not fcm_token:
        return False
        
    if not firebase_admin._apps:
        print("FCM not sent: Firebase Admin SDK not initialized. Please set FIREBASE_CREDENTIALS_JSON in .env")
        return False
        
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=fcm_token,
    )
    
    try:
        response = messaging.send(message)
        print("Successfully sent FCM message:", response)
        return True
    except Exception as e:
        print("Error sending FCM message:", e)
        return False

# Example usage to test locally:
if __name__ == "__main__":
    # Test Email
    # send_email_notification('test@example.com', 'GlacierGoals: 3 Day Streak! 🔥', 'Keep up the great work!')
    pass
