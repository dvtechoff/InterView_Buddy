"""
WSGI entry point for production deployment
This file is used by production WSGI servers like Gunicorn
"""
from app import app

# This is the WSGI application object that production servers will use
application = app

if __name__ == "__main__":
    # This should only run in development
    app.run(debug=False, host='0.0.0.0', port=5000)