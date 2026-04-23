import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from groq import Groq
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import threading
from dotenv import load_dotenv
# Load environment variables FIRST
load_dotenv()

from notifications import send_email_notification, send_fcm_push_notification
from apscheduler.schedulers.background import BackgroundScheduler

# Configure Groq AI
ai_key = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=ai_key) if ai_key else None

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'glacier-goals-2026-dynamic-v3-stable')
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_PERMANENT'] = True

# VAPID Keys for Web Push Notifications
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', 'BE_rEo8x630K3NCzt1I2OM_w2HJ-QW05pdNdjVbLn9qkXkbJrw8Ym2PeBQJgtzO2z42VZtLMMy_UqGdn2JWqH98')
VAPID_PRIVATE_KEY_PEM = os.environ.get('VAPID_PRIVATE_KEY_PEM', '-----BEGIN PRIVATE KEY-----\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgVs6Q8H2QzKtCBYoI\nvAy8HpyS6MdURSyqxPC3QQbD5zWhRANCAARP6xKPMet9CtzQs7dSNjjP8NhyfkFt\nOaXTXY1Wy5/apF5Gya8PGJtj3gUCYLczts+NlWbSzDMv1KhnZ9iVqh/f\n-----END PRIVATE KEY-----')
VAPID_CLAIMS = {'sub': 'mailto:keerthikeer2509@gmail.com'}
database_url = os.environ.get('DATABASE_URL', 'sqlite:///pixelres_v2.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Increase payload limit for Base64 Images (e.g., 50 MB)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 
app.config['MAX_FORM_MEMORY_SIZE'] = 50 * 1024 * 1024 

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure database tables are created (important for Render/Production)
try:
    with app.app_context():
        db.create_all()
    print("Database tables initialized successfully.")
except Exception as db_err:
    print(f"DATABASE INIT ERROR: {db_err}")
    # We continue so the app can at least start and give us logs

# Force HTTPS in production
@app.before_request
def force_https():
    if not app.debug:
        # Skip enforcing HTTPS on local development requests
        if request.host.startswith('localhost:') or request.host.startswith('127.0.0.1:'):
            return
            
        # Check if requested via HTTP (standard and proxy headers)
        if request.is_secure:
            return
        if request.headers.get('X-Forwarded-Proto', 'http') == 'http':
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), default='')
    nickname = db.Column(db.String(150), default='')
    password = db.Column(db.String(150), nullable=False)
    vault_pin = db.Column(db.String(150), nullable=True)
    freezes = db.Column(db.Integer, default=3)
    xp = db.Column(db.Integer, default=0)
    pet_health = db.Column(db.Integer, default=100) # Glacier pet health
    fcm_token = db.Column(db.String(300), nullable=True)
    resolutions = db.relationship('Resolution', backref='user', lazy=True)

class Resolution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='Other')
    is_archived = db.Column(db.Boolean, default=False)
    is_graveyard = db.Column(db.Boolean, default=False)
    graveyard_reason = db.Column(db.Text, nullable=True)
    order_index = db.Column(db.Integer, default=0)
    target_time_start = db.Column(db.String(10), nullable=True)
    target_time_end = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    progresses = db.relationship('Progress', backref='resolution', lazy=True, cascade='all, delete-orphan')

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resolution_id = db.Column(db.Integer, db.ForeignKey('resolution.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False) # Storing as YYYY-MM-DD
    status = db.Column(db.Boolean, default=False)
    used_freeze = db.Column(db.Boolean, default=False)
    mood = db.Column(db.String(10), nullable=True)
    __table_args__ = (db.UniqueConstraint('resolution_id', 'date', name='_resolution_date_uc'),)

class BucketGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_year = db.Column(db.Integer, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), default='General')
    priority = db.Column(db.String(50), default='Medium')
    budget = db.Column(db.Float, default=0.0)
    reward = db.Column(db.String(200), default='')
    steps = db.relationship('BucketGoalStep', backref='goal', lazy=True, cascade='all, delete-orphan')

class BucketGoalStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('bucket_goal.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)

class SecretDiary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_written = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(10), nullable=False) # Storing as YYYY-MM-DD
    is_annual = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DailyReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    emoji = db.Column(db.String(10), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='_user_date_review_uc'),)

class TimeCapsule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    unlock_level = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_open = db.Column(db.Boolean, default=False)

class QuestLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    story = db.Column(db.Text, nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='_user_date_quest_uc'),)




class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    icon = db.Column(db.String(10), default='🔔')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PushSubscription(db.Model):
    """Stores browser push subscriptions for each user (for native phone alerts)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh = db.Column(db.Text, nullable=False)
    auth = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PasswordReset(db.Model):
    """Stores temporary 6-digit verification codes for password resets."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False)

# Ensure database tables exist in production
with app.app_context():
    import os
    os.makedirs(app.instance_path, exist_ok=True)
    db.create_all()
def create_notification(user_id, message, icon='🔔', title="GlacierGoals"):
    """Helper: creates an in-app notification for a specific user, with de-duplication."""
    # Commit any pending changes from the current session so we see what others have done
    db.session.commit()

    # SUPER SHIELD: Check if the exact same message is ALREADY unread in their list
    existing_unread = Notification.query.filter_by(user_id=user_id, message=message, is_read=False).first()
    if existing_unread:
        return # Skip — they haven't cleared the first one yet!

    # Prevent duplicate spam: Check if same message sent to user in last 5 minutes
    limit = datetime.utcnow() - timedelta(minutes=5)
    duplicate = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.message == message,
        Notification.created_at >= limit
    ).first()
    
    if duplicate:
        return  # Skip — we already sent this recently

    notif = Notification(user_id=user_id, message=message, icon=icon)
    db.session.add(notif)
    
    # Auto-cleanup old notifications (keep last 20)
    old = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.asc()).all()
    if len(old) > 20:
        for o in old[:len(old)-20]:
            db.session.delete(o)
            
    db.session.commit()
    
    # Send FCM push notification if token exists
    user = User.query.get(user_id)
    if user and hasattr(user, 'fcm_token') and user.fcm_token:
        import threading
        from notifications import send_fcm_push_notification
        threading.Thread(target=send_fcm_push_notification, args=(user.fcm_token, title, message)).start()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─── Web Push Notification Routes ─────────────────────────────────────────────

@app.route('/api/vapid-public-key')
def get_vapid_key():
    """Returns the VAPID public key for the frontend to subscribe with."""
    return jsonify({'publicKey': VAPID_PUBLIC_KEY})

@app.route('/api/push/subscribe', methods=['POST'])
@login_required
def push_subscribe():
    """Saves a user's push subscription to the database."""
    data = request.get_json()
    if not data or 'endpoint' not in data:
        return jsonify({'error': 'Invalid subscription'}), 400
    
    endpoint = data['endpoint']
    p256dh = data.get('keys', {}).get('p256dh', '')
    auth = data.get('keys', {}).get('auth', '')
    
    # Avoid duplicates — if this endpoint already saved, update it 
    existing = PushSubscription.query.filter_by(user_id=current_user.id, endpoint=endpoint).first()
    if existing:
        existing.p256dh = p256dh
        existing.auth = auth
    else:
        sub = PushSubscription(user_id=current_user.id, endpoint=endpoint, p256dh=p256dh, auth=auth)
        db.session.add(sub)
    db.session.commit()
    return jsonify({'status': 'subscribed'})

@app.route('/api/push/send-test', methods=['POST'])
@login_required
def push_send_test():
    """Sends a test push notification to all of the current user's subscriptions."""
    send_web_push_to_user(current_user.id, '🧊 GlacierGoals', 'Push notifications are working! You\'ll now get reminders here.')
    return jsonify({'status': 'sent'})

def send_web_push_to_user(user_id, title, body, icon='/static/images/penguin_v2.jpg'):
    """Core helper: sends a real push notification to all a user's saved devices."""
    from pywebpush import webpush, WebPushException
    import json
    subs = PushSubscription.query.filter_by(user_id=user_id).all()
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
                },
                data=json.dumps({"title": title, "body": body, "icon": icon}),
                vapid_private_key=VAPID_PRIVATE_KEY_PEM,
                vapid_claims=VAPID_CLAIMS
            )
        except WebPushException as e:
            # Subscription expired or invalid — remove it
            if e.response and e.response.status_code in [404, 410]:
                db.session.delete(sub)
                db.session.commit()
            print(f"WebPush error for user {user_id}: {e}")

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '')
        nickname = request.form.get('nickname', '')
        password = request.form.get('password')

        user = User.query.filter(db.func.lower(User.email) == email).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('register'))

        new_user = User(
            email=email, 
            name=name, 
            nickname=nickname, 
            password=generate_password_hash(password) # Use default high-compat hash
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user, remember=True)
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')

        print(f"DEBUG: LOGIN ATTEMPT: {email}")
        user = User.query.filter(db.func.lower(User.email) == email).first()
        
        if not user:
            print(f"DEBUG: LOGIN FAIL - User {email} not found in database.")
            flash('This email is not registered. Please sign up first!')
            return redirect(url_for('login'))
            
        if not check_password_hash(user.password, password):
            print(f"DEBUG: LOGIN FAIL - Wrong password for {email}.")
            flash('Incorrect password. Please try again or reset it.')
            return redirect(url_for('login'))

        session.permanent = True
        login_user(user, remember=True)
        print(f"DEBUG: LOGIN SUCCESS for {email}. Session marked permanent.")
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter(db.func.lower(User.email) == email).first()
        
        if user:
            import random
            code = str(random.randint(100000, 999999))
            
            # Print to logs so user can see it in Render logs if email fails
            print(f"PASSWORD RESET CODE FOR {email}: {code}")
            
            # Clean up old resets for this email
            PasswordReset.query.filter_by(email=email).delete()
            
            new_reset = PasswordReset(email=email, code=code)
            db.session.add(new_reset)
            db.session.commit()
            
            # Send Email
            subject = "🧊 GlacierGoals: Your Password Reset Code"
            body = f"Hello!\n\nYour 6-digit verification code to reset your password is: {code}\n\nThis code was requested just now. If you didn't request this, please ignore this email."
            sent = send_email_notification(email, subject, body)
            
            if sent:
                flash('Verification code sent to your email!')
            else:
                flash('⚠️ Email server error. The code was printed to the app logs (Render Dashboard) as a fallback.')
            
            return redirect(url_for('verify_reset', email=email))
        else:
            flash('If that email exists in our system, you will receive a code.')
            # We don't say if it doesn't exist for security
            return redirect(url_for('forgot_password'))
            
    return render_template('forgot_password.html')

@app.route('/verify-reset', methods=['GET', 'POST'])
def verify_reset():
    email = request.args.get('email')
    if request.method == 'POST':
        email = request.form.get('email')
        code = request.form.get('code')
        
        reset_req = PasswordReset.query.filter_by(email=email, code=code).first()
        if reset_req:
            # Code is old if > 15 mins
            if datetime.utcnow() - reset_req.created_at > timedelta(minutes=15):
                flash('Code expired. Please request a new one.')
                return redirect(url_for('forgot_password'))
                
            reset_req.is_verified = True
            db.session.commit()
            return redirect(url_for('reset_password', email=email, code=code))
        else:
            flash('Invalid code. Please try again.')
            
    return render_template('verify_reset.html', email=email)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email')
    code = request.args.get('code')
    
    reset_req = PasswordReset.query.filter_by(email=email, code=code, is_verified=True).first()
    if not reset_req:
        flash('Unauthorized. Please start the process again.')
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        new_password = request.form.get('password')
        user = User.query.filter(db.func.lower(User.email) == email).first()
        if user:
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            db.session.delete(reset_req)
            db.session.commit()
            flash('Password reset successful! Please login.')
            return redirect(url_for('login'))
            
    return render_template('reset_password.html', email=email, code=code)

@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today().isoformat()
    resolutions = Resolution.query.filter_by(user_id=current_user.id, is_archived=False, is_graveyard=False).order_by(Resolution.order_index).all()
    archived_resolutions = Resolution.query.filter_by(user_id=current_user.id, is_archived=True, is_graveyard=False).all()
    graveyard_resolutions = Resolution.query.filter_by(user_id=current_user.id, is_graveyard=True).all()
    capsules = TimeCapsule.query.filter_by(user_id=current_user.id).all()
    
    for res in resolutions:
        progress_today = Progress.query.filter_by(resolution_id=res.id, date=today).first()
        res.done_today = progress_today.status if progress_today else False
        res.frozen_today = progress_today.used_freeze if progress_today else False
        res.today_mood = progress_today.mood if progress_today else None
        
        all_progs_dict = {p.date: p for p in res.progresses}
        
        # Heatmap calculation for the last 7 days
        last_7_days = [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
        res.heatmap = []
        for d in last_7_days:
            p = all_progs_dict.get(d)
            if p and p.status: res.heatmap.append({'date': d[-5:], 'state': 'done', 'mood': p.mood})
            elif p and p.used_freeze: res.heatmap.append({'date': d[-5:], 'state': 'freeze', 'mood': None})
            else: res.heatmap.append({'date': d[-5:], 'state': 'miss', 'mood': None})
        
        completed_progresses = [p for p in res.progresses if p.status]
        res.total_days = len(completed_progresses)
        
        streak = 0
        check_date = date.today()
        while True:
            p = all_progs_dict.get(check_date.isoformat())
            if p and (p.status or p.used_freeze):
                if p.status: streak += 1
                check_date -= timedelta(days=1)
            else:
                if check_date == date.today():
                    check_date -= timedelta(days=1)
                    continue
                break
        res.streak = streak

    level = (current_user.xp // 100) + 1 if current_user.xp is not None else 1
    xp_progress = (current_user.xp % 100) if current_user.xp is not None else 0

    return render_template('dashboard.html', resolutions=resolutions, archived_resolutions=archived_resolutions, graveyard_resolutions=graveyard_resolutions, capsules=capsules, today=today, user=current_user, level=level, xp_progress=xp_progress)

@app.route('/api/resolutions', methods=['POST'])
@login_required
def add_resolution():
    data = request.get_json()
    title = data.get('title')
    category = data.get('category', 'Other')
    target_start = data.get('target_start')
    target_end = data.get('target_end')
    
    if (category == 'Other' or not category) and title and groq_client:
        try:
            prompt = f"Categorize this habit short title: '{title}'. Choose exactly ONE from: Health, Productivity, Mindfulness, Finance, Learning, Fitness, Chores, Social. Output ONLY the category name. If none fit, output 'Other'."
            resp = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10, timeout=5
            )
            generated_cat = resp.choices[0].message.content.strip().replace('"', '').replace("'", "")
            valid_cats = ['Health', 'Productivity', 'Mindfulness', 'Finance', 'Learning', 'Fitness', 'Chores', 'Social', 'Other']
            if any(c.lower() == generated_cat.lower() for c in valid_cats):
                category = generated_cat.capitalize()
        except Exception as e:
            pass

    if title:
        new_res = Resolution(title=title, category=category, user_id=current_user.id, target_time_start=target_start, target_time_end=target_end)
        db.session.add(new_res)
        db.session.commit()
        return jsonify({'success': True, 'id': new_res.id})
    return jsonify({'success': False, 'message': 'Title required'}), 400

@app.route('/api/resolutions/<int:res_id>', methods=['PUT'])
@login_required
def edit_resolution(res_id):
    res = Resolution.query.get_or_404(res_id)
    if res.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    data = request.get_json()
    res.title = data.get('title', res.title)
    res.category = data.get('category', res.category)
    res.target_time_start = data.get('target_start', res.target_time_start)
    res.target_time_end = data.get('target_end', res.target_time_end)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/resolutions/<int:res_id>', methods=['DELETE'])
@login_required
def delete_resolution(res_id):
    res = Resolution.query.get_or_404(res_id)
    if res.user_id == current_user.id:
        db.session.delete(res)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Unauthorized'}), 403

@app.route('/api/resolutions/reorder', methods=['POST'])
@login_required
def reorder_resolutions():
    data = request.get_json()
    order_list = data.get('order', [])
    for index, res_id in enumerate(order_list):
        res = Resolution.query.get(res_id)
        if res and res.user_id == current_user.id:
            res.order_index = index
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/resolutions/<int:res_id>/toggle', methods=['POST'])
@login_required
def toggle_progress(res_id):
    res = Resolution.query.get_or_404(res_id)
    if res.user_id != current_user.id:
        return jsonify({'success': False}), 403
        
    data = request.get_json() or {}
    mood = data.get('mood')
    date_str = date.today().isoformat()
    progress = Progress.query.filter_by(resolution_id=res_id, date=date_str).first()
    
    if progress:
        was_done = progress.status
        progress.status = not progress.status
        progress.mood = mood if progress.status else None
        
        if not was_done and progress.status:
            current_user.xp = (current_user.xp or 0) + 10
            current_user.pet_health = min((current_user.pet_health or 100) + 2, 100)
        elif was_done and not progress.status:
            current_user.xp = max(0, (current_user.xp or 0) - 10)
            current_user.pet_health = max((current_user.pet_health or 100) - 5, 0)
    else:
        progress = Progress(resolution_id=res_id, date=date_str, status=True, mood=mood)
        current_user.xp = (current_user.xp or 0) + 10
        current_user.pet_health = min((current_user.pet_health or 100) + 2, 100)
        db.session.add(progress)
        
    db.session.commit()
    
    # ----------------------------------------------------
    # Fire Email Notification in the background if checked!
    # ----------------------------------------------------
    if progress.status:
        subject = f"✅ Goal Complete: {res.title}"
        body = f"Great job checking off '{res.title}' today!\n\nYou logged your mood as: {mood if mood else 'feeling great'}.\n\nKeep the momentum going!\n\n- GlacierGoals Team"
        user_email = current_user.email
        
        # Using a background thread so the UI button doesn't spin waiting for SMTP
        threading.Thread(target=send_email_notification, args=(user_email, subject, body)).start()
        
    return jsonify({'success': True, 'status': progress.status})

@app.route('/api/resolutions/<int:res_id>/freeze', methods=['POST'])
@login_required
def use_freeze(res_id):
    res = Resolution.query.get_or_404(res_id)
    if res.user_id != current_user.id:
        return jsonify({'success': False}), 403
    if current_user.freezes <= 0:
        return jsonify({'success': False, 'message': 'No freezes left!'}), 400
        
    date_str = date.today().isoformat()
    progress = Progress.query.filter_by(resolution_id=res_id, date=date_str).first()
    
    if not progress:
        progress = Progress(resolution_id=res_id, date=date_str, used_freeze=True)
        db.session.add(progress)
        current_user.freezes -= 1
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Progress already exists for today'}), 400

@app.route('/api/resolutions/<int:res_id>/archive', methods=['POST'])
@login_required
def archive_resolution(res_id):
    res = Resolution.query.get_or_404(res_id)
    if res.user_id == current_user.id:
        res.is_archived = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 403

@app.route('/api/enhance-goal', methods=['POST'])
@login_required
def enhance_goal():
    if not groq_client:
        return jsonify({'success': False, 'message': 'AI coach not configured.'})
    
    data = request.get_json()
    draft = data.get('draft', '')
    if not draft:
        return jsonify({'success': False, 'message': 'No idea provided.'})
        
    try:
        prompt = f"Take this vague habit/goal idea: '{draft}'. Turn it into a short, actionable, specific SMART daily habit under 10 words. Example: 'Read 10 pages before bed', 'Drink 2 liters of water daily'. Output ONLY the goal text, without quotes."
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50, timeout=10
        )
        enhanced = response.choices[0].message.content.strip().replace('"', '').replace('**', '')
        return jsonify({'success': True, 'enhanced': enhanced})
    except Exception as e:
        err_str = str(e)
        if '429' in err_str or 'rate' in err_str.lower():
            return jsonify({'success': False, 'message': 'Too many requests! Please wait a moment and try again.'})
        return jsonify({'success': False, 'message': f'AI coach is resting: {err_str}'})

@app.route('/api/coach', methods=['GET'])
@login_required
def get_coach_message():
    resolutions = Resolution.query.filter_by(user_id=current_user.id, is_archived=False, is_graveyard=False).all()
    if not resolutions:
        return jsonify({'message': "You don't have any resolutions yet! Add some to get started."})

    today = date.today().isoformat()
    total_done = 0
    for res in resolutions:
        progress_today = Progress.query.filter_by(resolution_id=res.id, date=today).first()
        if progress_today and progress_today.status:
            total_done += 1
            
    total = len(resolutions)
    level = (current_user.xp // 100) + 1 if current_user.xp is not None else 1
    
    if groq_client:
        try:
            quest = QuestLog.query.filter_by(user_id=current_user.id, date=today).first()
            if not quest:
                habit_names = [r.title for r in resolutions]
                context = f"User Level: {level}. Pet Health: {current_user.pet_health}%."
                prompt = f"Context: {context}. Habits: {habit_names}. Completed today: {total_done}/{total}. Write an epic 2-sentence fantasy RPG quest update reflecting their momentum and stats. Be creative but use very simple, clear English that is easy for everyone to understand. Avoid complex words or idioms."
                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=120, timeout=10
                )
                msg = response.choices[0].message.content.replace('**', '').strip()
                quest = QuestLog(user_id=current_user.id, date=today, story=msg)
                db.session.add(quest)
                db.session.commit()
            else:
                msg = quest.story
        except Exception as e:
            msg = f"Keep crushing it! You've completed {total_done}/{total} habits today."
    else:
        msg = f"You're making progress. You've completed {total_done}/{total} habits today. Stay focused!"

    return jsonify({'message': f"📜 Daily Quest: {msg}"})

@app.route('/api/avatar/chat', methods=['POST'])
@login_required
def avatar_chat():
    if not groq_client:
        return jsonify({'success': False, 'reply': 'AI is not configured. Please set GROQ_API_KEY in .env'})
        
    data = request.get_json() or {}
    message = data.get('message', '')
    history = data.get('history', [])
    
    try:
        # Gather some user context to make responses personal
        user_habits = Resolution.query.filter_by(user_id=current_user.id, is_graveyard=False).all()
        habit_names = [r.title for r in user_habits[:5]]
        habit_context = f"The user is currently tracking these goals: {', '.join(habit_names)}." if habit_names else ""

        system_prompt = f"""You are Glacier Buddy — a tiny, cute, and very excited baby penguin! 
You are talking to your best friend {current_user.nickname or current_user.name or current_user.email.split('@')[0]}. 

YOUR MISSION:
1. Always start your replies with an EXCITED greeting! (Yay! Yippee! Oh my gosh!)
2. Be a feelings expert. If your friend is sad or tired, be the sweetest penguin ever.
3. YOU MUST ALWAYS ASK A CARING FOLLOW-UP QUESTION! (e.g. "Will you share more with me?" or "What happened?")
4. NEVER just say "I'm sorry" — always ask WHY and encourage them to talk more.
5. USE YOUR MEMORY! Reference things your friend said earlier.
6. Use only simple, cute, easy words.
7. Keep replies to 2-3 happy sentences + 1 caring question.

EXAMPLES:
- User is sad → "Oh no! I am sending you a huge penguin hug! I am always here for you. Will you share more about why you are sad?"
- User says hello → "Yay! You are back! I missed you so much today! How was your morning, best friend?"
- User mentions a goal → "Yippee! You are doing so great! I am your biggest fan! What was the best part of your work today?"
"""

        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-10:]:
            role = "assistant" if h['role'] == 'model' else h['role']
            messages.append({"role": role, "content": h['content']})
        messages.append({"role": "user", "content": message})

        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=250, timeout=15
        )
        reply = resp.choices[0].message.content.replace('**', '').strip()
        return jsonify({'success': True, 'reply': reply})

    except Exception as e:
        import traceback
        traceback.print_exc()  # Shows exact error in server console
        err = str(e)
        if '429' in err or 'rate' in err.lower():
            return jsonify({'success': False, 'reply': "I'm a little overwhelmed right now! Give me a moment and try again 😅"})
        if 'timeout' in err.lower():
            return jsonify({'success': False, 'reply': "Hmm, that took too long! Try asking me again? 🙏"})
        return jsonify({'success': False, 'reply': "Oops, something went wrong on my end! Try again in a sec 🤞"})

@app.route('/api/resolutions/<int:res_id>/graveyard', methods=['POST'])
@login_required
def graveyard_resolution(res_id):
    res = Resolution.query.get_or_404(res_id)
    if res.user_id == current_user.id:
        res.is_graveyard = True
        data = request.get_json() or {}
        res.graveyard_reason = data.get('reason', '')
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 403

@app.route('/api/graveyard/<int:res_id>/chat', methods=['POST'])
@login_required
def graveyard_chat(res_id):
    res = Resolution.query.get_or_404(res_id)
    if res.user_id != current_user.id:
        return jsonify({'success': False}), 403
    
    data = request.get_json() or {}
    message = data.get('message', '')
    history = data.get('history', [])
    
    if groq_client:
        try:
            system_prompt = f"""You are an empathetic but highly motivating habit therapist. The user failed their habit '{res.title}'. Reason: '{res.graveyard_reason}'.
Instructions:
1. Normalize their failure instantly.
2. Ask a deeper follow-up question.
3. Intensely motivate them to get back to work constructively.
4. OCCASIONALLY add a cute intervention from their 'Glacier Pet' (e.g. "🧊 Your Glacier Pet nudges you affectionately...").
5. If they seem ready to try again, set offer_revive to true.
6. If habit is too hard, suggest a tiny micro-habit in offer_micro. Otherwise null.
Use VERY SIMPLE, clear English. Avoid complex words.

You MUST respond IN STRICT JSON FORMAT with exactly these keys:
{{"reply": "...", "options": ["reply 1", "reply 2"], "offer_revive": true or false, "offer_micro": "micro title" or null}}"""

            messages = [{"role": "system", "content": system_prompt}]
            for h in history[-8:]:
                role = "assistant" if h['role'] == 'model' else h['role']
                messages.append({"role": role, "content": h['content']})
            messages.append({"role": "user", "content": message})

            resp = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=400, timeout=25
            )
            return jsonify({'success': True, 'reply': resp.choices[0].message.content.replace('**', '').strip()})
        except Exception as e:
            return jsonify({'success': False, 'reply': f"Connection issue. Please try again in a moment."})
            
    return jsonify({'success': False, 'reply': "It's normal to struggle. Focus on resting, and when you are ready, try picking just one tiny micro-habit!"})

@app.route('/api/resolutions/<int:res_id>/revive', methods=['POST'])
@login_required
def revive_resolution(res_id):
    res = Resolution.query.get_or_404(res_id)
    if res.user_id == current_user.id:
        res.is_graveyard = False
        res.graveyard_reason = None
        current_user.xp = (current_user.xp or 0) + 20
        current_user.pet_health = min((current_user.pet_health or 100) + 10, 100)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 403

@app.route('/api/capsule', methods=['POST'])
@login_required
def create_capsule():
    data = request.get_json()
    content = data.get('content')
    unlock_level = data.get('unlock_level', 1)
    if content:
        capsule = TimeCapsule(user_id=current_user.id, content=content, unlock_level=int(unlock_level))
        db.session.add(capsule)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/capsule/<int:cap_id>/open', methods=['POST'])
@login_required
def open_capsule(cap_id):
    cap = TimeCapsule.query.get_or_404(cap_id)
    user_level = (current_user.xp // 100) + 1 if current_user.xp is not None else 1
    
    if cap.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    if user_level < cap.unlock_level:
        return jsonify({'success': False, 'message': 'Level too low'}), 403
        
    data = request.get_json() or {}
    password = data.get('password', '')
    
    valid = False
    if check_password_hash(current_user.password, password):
        valid = True
    elif current_user.vault_pin and check_password_hash(current_user.vault_pin, password):
        valid = True
        
    if not valid:
        return jsonify({'success': False, 'message': 'Invalid Security Credentials'}), 403

    cap.is_open = True
    db.session.commit()
    return jsonify({'success': True, 'content': cap.content})

@app.route('/insights')
@login_required
def insights():
    # Gather data for charts
    resolutions = Resolution.query.filter_by(user_id=current_user.id).all()
    cat_counts = {}
    mood_counts = {}
    total_completed = 0
    
    for r in resolutions:
        # Category breakdown
        cat_counts[r.category] = cat_counts.get(r.category, 0) + 1
        
        # Total completes & mood distribution
        for p in r.progresses:
            if p.status:
                total_completed += 1
                if p.mood:
                    mood_counts[p.mood] = mood_counts.get(p.mood, 0) + 1
                    
    # Format data for frontend Chart.js
    categories = list(cat_counts.keys())
    cat_data = list(cat_counts.values())
    
    moods = list(mood_counts.keys())
    mood_data = list(mood_counts.values())
    
    return render_template('insights.html', 
                            categories=categories, 
                            cat_data=cat_data, 
                            moods=moods, 
                            mood_data=mood_data,
                            total_completed=total_completed)

@app.route('/longterm', methods=['GET', 'POST'])
@login_required
def longterm():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        target_year = request.form.get('target_year')
        category = request.form.get('category', 'General')
        priority = request.form.get('priority', 'Medium')
        budget = request.form.get('budget')
        reward = request.form.get('reward')
        if title:
            new_goal = BucketGoal(
                title=title, description=description, 
                target_year=int(target_year) if target_year else None, 
                user_id=current_user.id,
                category=category,
                priority=priority,
                budget=float(budget) if budget else 0.0,
                reward=reward
            )
            db.session.add(new_goal)
            db.session.commit()
            flash('Long-term bucket goal tracked!')
        return redirect(url_for('longterm'))
        
    goals = BucketGoal.query.filter_by(user_id=current_user.id).order_by(BucketGoal.target_year).all()
    return render_template('longterm.html', goals=goals)

@app.route('/api/longterm/<int:goal_id>/complete', methods=['POST'])
@login_required
def complete_longterm(goal_id):
    goal = BucketGoal.query.get_or_404(goal_id)
    if goal.user_id == current_user.id:
        goal.is_completed = not goal.is_completed
        db.session.commit()
    return redirect(url_for('longterm'))

@app.route('/api/longterm/<int:goal_id>/edit', methods=['POST'])
@login_required
def edit_longterm(goal_id):
    goal = BucketGoal.query.get_or_404(goal_id)
    if goal.user_id == current_user.id:
        title = request.form.get('title')
        description = request.form.get('description')
        target_year = request.form.get('target_year')
        category = request.form.get('category', 'General')
        priority = request.form.get('priority', 'Medium')
        budget = request.form.get('budget')
        reward = request.form.get('reward', '')
        
        if title:
            goal.title = title
            goal.description = description
            goal.target_year = int(target_year) if target_year else None
            goal.category = category
            goal.priority = priority
            goal.budget = float(budget) if budget else 0.0
            goal.reward = reward
            db.session.commit()
            flash('Goal updated successfully!')
    return redirect(url_for('longterm'))

@app.route('/api/longterm/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_longterm(goal_id):
    goal = BucketGoal.query.get_or_404(goal_id)
    if goal.user_id == current_user.id:
        db.session.delete(goal)
        db.session.commit()
    return redirect(url_for('longterm'))

@app.route('/api/longterm/<int:goal_id>/step', methods=['POST'])
@login_required
def add_longterm_step(goal_id):
    goal = BucketGoal.query.get_or_404(goal_id)
    if goal.user_id == current_user.id:
        title = request.form.get('title')
        if title:
            step = BucketGoalStep(goal_id=goal.id, title=title)
            db.session.add(step)
            db.session.commit()
    return redirect(url_for('longterm'))

@app.route('/api/longterm/step/<int:step_id>/toggle', methods=['POST'])
@login_required
def toggle_longterm_step(step_id):
    step = BucketGoalStep.query.get_or_404(step_id)
    if step.goal.user_id == current_user.id:
        step.is_completed = not step.is_completed
        db.session.commit()
    return redirect(url_for('longterm'))

@app.route('/api/longterm/step/<int:step_id>/delete', methods=['POST'])
@login_required
def delete_longterm_step(step_id):
    step = BucketGoalStep.query.get_or_404(step_id)
    if step.goal.user_id == current_user.id:
        db.session.delete(step)
        db.session.commit()
    return redirect(url_for('longterm'))

@app.route('/vault', methods=['GET', 'POST'])
@login_required
def vault():
    unlocked = session.get('vault_unlocked', False)
    has_pin = bool(current_user.vault_pin)
    
    if request.method == 'POST':
        if not unlocked:
            flash('Vault is locked!')
            return redirect(url_for('vault'))
        title = request.form.get('title')
        content = request.form.get('content')
        if title and content:
            entry = SecretDiary(title=title, content=content, user_id=current_user.id)
            db.session.add(entry)
            db.session.commit()
            flash('Secret secured in the Glacier Vault 🔒')
        return redirect(url_for('vault'))
        
    entries = SecretDiary.query.filter_by(user_id=current_user.id).order_by(SecretDiary.date_written.desc()).all() if unlocked else []
    return render_template('vault.html', entries=entries, unlocked=unlocked, has_pin=has_pin)

@app.route('/api/vault/setup', methods=['POST'])
@login_required
def setup_vault_pin():
    pin = request.form.get('pin')
    old_pin = request.form.get('old_pin')
    
    # Require vault to be unlocked to change an existing PIN
    if current_user.vault_pin and not session.get('vault_unlocked', False):
        flash('You must unlock the vault first to change the security key!')
        return redirect(url_for('vault'))
        
    if current_user.vault_pin:
        if not old_pin or not check_password_hash(current_user.vault_pin, old_pin):
            flash('Incorrect current security key. Cannot update!')
            return redirect(url_for('vault'))
        
    if pin and len(pin) >= 4:
        current_user.vault_pin = generate_password_hash(pin, method='pbkdf2:sha256')
        db.session.commit()
        session['vault_unlocked'] = True
        flash('Vault security key updated successfully! 🔒')
    else:
        flash('Key must be at least 4 characters/nodes long.')
    return redirect(url_for('vault'))

@app.route('/api/vault/forgot', methods=['POST'])
@login_required
def forgot_vault_pin():
    account_password = request.form.get('account_password')
    if check_password_hash(current_user.password, account_password):
        current_user.vault_pin = None
        db.session.commit()
        session['vault_unlocked'] = False
        flash('Vault key reset successful. Please set a new security key.')
    else:
        flash('Incorrect Account Password!')
    return redirect(url_for('vault'))

@app.route('/api/vault/unlock', methods=['POST'])
@login_required
def unlock_vault():
    pin = request.form.get('pin')
    if current_user.vault_pin and check_password_hash(current_user.vault_pin, pin):
        session['vault_unlocked'] = True
    else:
        flash('Incorrect Vault Key!')
    return redirect(url_for('vault'))

@app.route('/api/vault/lock', methods=['POST'])
@login_required
def lock_vault():
    session['vault_unlocked'] = False
    return redirect(url_for('vault'))

@app.route('/api/vault/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_vault_entry(entry_id):
    if not session.get('vault_unlocked', False):
        return redirect(url_for('vault'))
    entry = SecretDiary.query.get_or_404(entry_id)
    if entry.user_id == current_user.id:
        db.session.delete(entry)
        db.session.commit()
    return redirect(url_for('vault'))

@app.route('/api/vault/<int:entry_id>/edit', methods=['POST'])
@login_required
def edit_vault_entry(entry_id):
    if not session.get('vault_unlocked', False):
        return redirect(url_for('vault'))
    entry = SecretDiary.query.get_or_404(entry_id)
    if entry.user_id == current_user.id:
        title = request.form.get('title')
        content = request.form.get('content')
        
        if title and content:
            entry.title = title
            entry.content = content
            db.session.commit()
            flash('Secret updated securely.')
    return redirect(url_for('vault'))

@app.route('/calendar', methods=['GET', 'POST'])
@login_required
def calendar_view():
    if request.method == 'POST':
        title = request.form.get('title')
        event_date = request.form.get('date')
        is_annual = bool(request.form.get('is_annual'))
        if title and event_date:
            new_event = Event(title=title, date=event_date, user_id=current_user.id, is_annual=is_annual)
            db.session.add(new_event)
            db.session.commit()
            flash('Event added to your calendar!')
        return redirect(url_for('calendar_view'))
        
    events = Event.query.filter_by(user_id=current_user.id).order_by(Event.date).all()
    
    # Daily Review data for mood chips in calendar grid
    reviews = DailyReview.query.filter_by(user_id=current_user.id).all()
    prog_data = [{'date': r.date, 'mood': r.emoji} for r in reviews]
    
    return render_template('calendar.html', events=events, prog_data=prog_data)

@app.route('/api/calendar/review', methods=['POST'])
@login_required
def set_calendar_review():
    data = request.get_json()
    date_str = data.get('date')
    emoji = data.get('emoji')
    if not date_str or not emoji:
        return jsonify({'success': False})
        
    review = DailyReview.query.filter_by(user_id=current_user.id, date=date_str).first()
    if review:
        review.emoji = emoji
    else:
        review = DailyReview(user_id=current_user.id, date=date_str, emoji=emoji)
        db.session.add(review)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/calendar/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id == current_user.id:
        db.session.delete(event)
        db.session.commit()
    return redirect(url_for('calendar_view'))

def weekly_recap_and_regen():
    # runs weekly, grants 1 freeze, sends recap notification to all users
    with app.app_context():
        users = User.query.all()
        start_of_week = (date.today() - timedelta(days=7)).isoformat()
        
        for u in users:
            if u.freezes < 5:
                u.freezes += 1
            
            # Find stats
            active_res = Resolution.query.filter_by(user_id=u.id, is_archived=False).all()
            completed_this_week = 0
            for r in active_res:
                progs = Progress.query.filter(Progress.resolution_id == r.id, Progress.date >= start_of_week).all()
                completed_this_week += sum(1 for p in progs if p.status)

            # In-app notification for every user
            create_notification(u.id,
                f"Weekly Recap: You completed {completed_this_week} habit checks this week! +1 Ice Cube refilled 🧊",
                icon='📊')

            # Email (only works if MAIL_USERNAME is configured)
            subject = "🧊 Your GlacierGoals Weekly Recap & +1 Ice Cube!"
            body = f"Hello!\n\nYou've checked off {completed_this_week} habit tasks this past week!\nWe've also refilled 1 Ice Cube freeze for you (Max 5).\n\nKeep stacking those days!\n\n- GlacierGoals Coach"
            threading.Thread(target=send_email_notification, args=(u.email, subject, body)).start()

        db.session.commit()

def daily_event_notifications():
    with app.app_context():
        today_str = date.today().isoformat()
        today_month_day = today_str[5:]  # e.g., "04-07"
        
        all_events = Event.query.all()
        events_today = [e for e in all_events if e.date == today_str or (e.is_annual and e.date[5:] == today_month_day)]
        
        for event in events_today:
            user = User.query.get(event.user_id)
            if user:
                # In-app notification
                create_notification(user.id,
                    f"Today's Event: {event.title} 🎉 Don't forget!",
                    icon='📅')
                # Email
                subject = f"📅 Reminder: {event.title} is Today!"
                body = f"Hello!\n\nJust a quick heads-up that you have a special event today:\n\n🎉 {event.title}\n\nHave a great day!\n- GlacierGoals Team"
                threading.Thread(target=send_email_notification, args=(user.email, subject, body)).start()

def daily_habit_reminder():
    """Runs every evening — reminds users who haven't checked off all habits yet."""
    with app.app_context():
        today_str = date.today().isoformat()
        users = User.query.all()
        for u in users:
            active_res = Resolution.query.filter_by(user_id=u.id, is_archived=False, is_graveyard=False).all()
            if not active_res:
                continue
            pending = []
            for r in active_res:
                p = Progress.query.filter_by(resolution_id=r.id, date=today_str).first()
                if not p or not p.status:
                    pending.append(r.title)
            if pending:
                count = len(pending)
                msg = f"You still have {count} habit{'s' if count > 1 else ''} to do today! Don't break your streak 🔥"
                create_notification(u.id, msg, icon='⏰')
                # Also send real phone push notification
                threading.Thread(
                    target=send_web_push_to_user,
                    args=(u.id, '⏰ GlacierGoals Reminder', msg)
                ).start()

# --- Notification API Routes ---

@app.route('/api/notifications')
@login_required
def get_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(20).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({
        'unread': unread_count,
        'notifications': [{
            'id': n.id,
            'message': n.message,
            'icon': n.icon,
            'is_read': n.is_read,
            'time': n.created_at.isoformat() + 'Z'
        } for n in notifs]
    })

@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    """Clear all notifications for the current user."""
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/notifications/<int:notif_id>/delete', methods=['POST'])
@login_required
def delete_notification(notif_id):
    n = Notification.query.get_or_404(notif_id)
    if n.user_id == current_user.id:
        db.session.delete(n)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/save-fcm-token', methods=['POST'])
@login_required
def save_fcm_token():
    data = request.get_json()
    token = data.get('token')
    if token:
        current_user.fcm_token = token
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

def resolution_time_reminders():
    """Runs every minute — notifies users when their habit's start time arrives."""
    with app.app_context():
        now = datetime.now()
        current_time = now.strftime("%H:%M")  # e.g. "09:30"
        today_str = date.today().isoformat()

        # Find all active resolutions with a target_time_start matching right now
        due = Resolution.query.filter(
            Resolution.target_time_start == current_time,
            Resolution.is_archived == False,
            Resolution.is_graveyard == False
        ).all()

        for res in due:
            # Only notify if not already completed today
            progress = Progress.query.filter_by(
                resolution_id=res.id, date=today_str
            ).first()
            if progress and progress.status:
                continue  # Already done today, skip

            create_notification(
                res.user_id,
                f"⏰ Time for: \"{res.title}\" — your scheduled habit is waiting!",
                icon="⏰"
            )

def restore_daily_ice_cubes():
    """Runs every day at midnight to restore up to 3 ice cubes per user."""
    with app.app_context():
        for u in User.query.all():
            u.freezes = max(3, u.freezes or 0)
        db.session.commit()

# Runs every Sunday at 9 AM
scheduler.add_job(func=weekly_recap_and_regen, trigger="cron", day_of_week='sun', hour=9, minute=0)
# Runs every day at 8 AM for daily events
scheduler.add_job(func=daily_event_notifications, trigger="cron", hour=8, minute=0)
# Runs every day at 8 PM to remind pending habits
scheduler.add_job(func=daily_habit_reminder, trigger="cron", hour=20, minute=0)
# Runs every minute — notifies users at their resolution's exact scheduled time
scheduler.add_job(func=resolution_time_reminders, trigger="interval", minutes=1)
# Runs every midnight to give users back their 3 daily ice cubes
scheduler.add_job(func=restore_daily_ice_cubes, trigger="cron", hour=0, minute=0)
# Start the scheduler ONLY if we are in the main process (avoids double-start in debug mode)
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    if not scheduler.running:
        scheduler.start()

@app.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')

@app.route('/terms')
def terms_of_service():
    return render_template('terms.html')

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    return send_from_directory(app.static_folder, 'sitemap.xml')

@app.route('/googled09f53dc0f297b55.html')
def google_verification():
    return send_from_directory(app.static_folder, 'googled09f53dc0f297b55.html')

@app.route('/ads.txt')
def ads_txt():
    return send_from_directory(app.static_folder, 'ads.txt')

@app.route('/humans.txt')
def humans_txt():
    return send_from_directory(app.static_folder, 'humans.txt')

@app.route('/.well-known/security.txt')
def security_txt():
    return send_from_directory(os.path.join(app.static_folder, '.well-known'), 'security.txt')



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
