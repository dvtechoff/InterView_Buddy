# Railway Deployment Configuration
# This file contains Railway-specific deployment settings

## Environment Variables to Set in Railway Dashboard:
# SECRET_KEY=your-super-secret-production-key-64-chars-long
# GEMINI_API_KEY=your-gemini-api-key
# FIREBASE_API_KEY=your-firebase-api-key
# FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
# FIREBASE_PROJECT_ID=your-project-id
# FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
# FIREBASE_MESSAGING_SENDER_ID=your-sender-id
# FIREBASE_APP_ID=your-app-id
# DEBUG=False
# FLASK_ENV=production

## Railway Settings:
# - Runtime: Python 3.11
# - Build Command: pip install -r requirements.txt
# - Start Command: python production_server.py
# - Port: $PORT (automatically set by Railway)

## Deployment Steps:
# 1. Push code to GitHub
# 2. Connect Railway to GitHub repository
# 3. Set environment variables in Railway dashboard
# 4. Deploy automatically
