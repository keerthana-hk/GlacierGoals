# 🚀 How to Create your Android App & Release on GitHub

Since you don't have the $25 Google Play fee, you can build your own Android APK for free and host it right here on GitHub.

### 1. Build the APK (Google's "Bubblewrap" tool)
The easiest way to turn your PWA into an APK is using **Bubblewrap**. 
1. Install it on your computer: `npm install -g @bubblewrap/cli`
2. Run the initialization: `bubblewrap init --manifest=https://glaciergoals.onrender.com/static/manifest.json`
3. Follow the prompts (use default settings).
4. Run the build command: `bubblewrap build`
5. This will generate a file named `app-release-signed.apk`.

### 2. Upload to GitHub Releases
1. Go to your repository on GitHub: `https://github.com/keerthana-hk/GlacierGoals`
2. Click on **"Releases"** (on the right sidebar).
3. Click **"Create a new release"**.
4. Set the tag to `v1.0.0` (or `latest`).
5. **CRITICAL**: Drag and drop your `app-release-signed.apk` file into the "Attach binaries" box.
6. Click **"Publish release"**.

### 3. All Done!
The "Download APK" buttons I added to your website will now automatically point to the latest file you uploaded. Anyone visiting your site can click "Download Android APK" and install it directly!

---
*Note: When people install the APK, Android might show a warning like "App from unknown source." This is normal for self-hosted apps. They just need to click "Install Anyway."* 🐧📦
