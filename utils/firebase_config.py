import firebase_admin
from firebase_admin import credentials, firestore, auth
import pyrebase
import os
import json
from config import Config

class FirebaseConfig:
    def __init__(self):
        self.firebase_config = {
            "apiKey": os.environ.get('FIREBASE_API_KEY'),
            "authDomain": os.environ.get('FIREBASE_AUTH_DOMAIN'),
            "projectId": os.environ.get('FIREBASE_PROJECT_ID'),
            "storageBucket": os.environ.get('FIREBASE_STORAGE_BUCKET'),
            "messagingSenderId": os.environ.get('FIREBASE_MESSAGING_SENDER_ID'),
            "appId": os.environ.get('FIREBASE_APP_ID'),
            "databaseURL": os.environ.get('FIREBASE_DATABASE_URL', "")
        }
        
        self.service_account_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')
        self._init_admin_sdk()
        self._init_client_sdk()
    
    def _init_admin_sdk(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            firebase_admin.get_app()
        except ValueError:
            # Initialize with service account
            if self.service_account_path and os.path.exists(self.service_account_path):
                cred = credentials.Certificate(self.service_account_path)
                firebase_admin.initialize_app(cred)
            else:
                # Use environment variables for credentials
                cred_dict = {
                    "type": "service_account",
                    "project_id": os.environ.get('FIREBASE_PROJECT_ID'),
                    "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
                    "private_key": os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
                    "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
                    "client_id": os.environ.get('FIREBASE_CLIENT_ID'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": os.environ.get('FIREBASE_CLIENT_X509_CERT_URL')
                }
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        self.auth_admin = auth
    
    def _init_client_sdk(self):
        """Initialize Pyrebase for client-side auth"""
        self.firebase_client = pyrebase.initialize_app(self.firebase_config)
        self.auth_client = self.firebase_client.auth()
    
    def get_db(self):
        """Get Firestore database instance"""
        return self.db
    
    def get_auth_admin(self):
        """Get Firebase Auth Admin instance"""
        return self.auth_admin
    
    def get_auth_client(self):
        """Get Firebase Auth Client instance"""
        return self.auth_client

# Global Firebase instance
firebase_config = FirebaseConfig()
