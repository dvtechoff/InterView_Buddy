"""
Production server runner for Windows
Uses Waitress WSGI server which is Windows-compatible
"""
import os
from waitress import serve
from app import app

if __name__ == "__main__":
    # Set production environment
    os.environ['DEBUG'] = 'False'
    os.environ['FLASK_ENV'] = 'production'
    
    # Get port from environment (for deployment platforms)
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 Starting InterviewBuddy in PRODUCTION mode...")
    print(f"🌐 Server running on http://0.0.0.0:{port}")
    print("🔒 Debug mode: OFF")
    print("⚡ Using Waitress WSGI server")
    
    # Start production server
    serve(app, host='0.0.0.0', port=port, threads=4)
