# 🧊 GlacierGoals
> **Your Journey, Frozen in Time.**

GlacierGoals is a premium, AI-powered resolution tracker and personal growth companion designed to help you freeze your goals into reality. Built with a stunning **Glassmorphic UI**, it combines productivity tracking with emotional companionship and long-term reflection.

## 🐧 Core Features

- **Glacier Buddy AI**: A persistent, 3D-rendered penguin companion (powered by Groq Llama 3) that acts as your life coach, friend, and habit therapist. Supports voice conversation and lip-syncing!
- **Secret Diary Vault**: A secure, encrypted space for your private reflections. Features physically accurate "paper-burning" deletion animations for ultimate catharsis.
- **Time Capsule (Future Letters)**: Write heartfelt letters to your future self, sealed in the glacier and unlocked only when the time is right.
- **Yearly Plans & Daily Resolutions**: High-level vision mapping combined with actionable daily tasks.
- **Gamification System**: Earn **XP**, level up, and collect **Ice Cubes** (Frozen Days) to maintain your streaks even when life gets in the way.
- **Progress Analytics**: Visual heatmaps and consistency tracking for every habit.
- **Zen Sanctuary**: Built-in focus timer with a calming snow-fall atmosphere to help you enter deep work.

## 🛠️ Tech Stack

- **Backend**: Python / Flask
- **Database**: SQLAlchemy (SQLite for local, PostgreSQL ready)
- **AI Integration**: Groq API (Llama 3 70B & 8B)
- **Frontend**: Vanilla Modern JS / Premium CSS (Glassmorphism)
- **Notifications**: Firebase Cloud Messaging (FCM) & Browser Push
- **Deployment**: PWA Capable (Install as Mobile App)

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- A [Groq API Key](https://console.groq.com/)
- A Firebase Project (for notifications)

### Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/glacier-goals.git
   cd glacier-goals
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_super_secret_key
   GROQ_API_KEY=your_groq_key_here
   ```

4. **Initialize Database**:
   ```bash
   python app.py
   ```
   *The database will auto-create on first run.*

5. **Run Locally**:
   The app will be available at `http://localhost:5000`.

## 📱 PWA & Mobile
GlacierGoals is a fully configured **Progressive Web App**. You can "Add to Home Screen" on iOS or Android to use it as a native-feeling app with custom icons and splash screens.

## 🔍 SEO & Launch Ready
- **Meta Tags**: Optimized for habit tracking and personal growth keywords.
- **Robots & Sitemap**: Fully configured for Google Search Console.
- **Legal**: Privacy Policy and Terms of Service included.

---
*Created with ❤️ to help you achieve your 2026 resolutions and beyond.*
