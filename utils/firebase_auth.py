import json
import uuid
from datetime import datetime
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError
from utils.firebase_config import firebase_config
from config import Config
import re

class FirebaseAuthManager:
    def __init__(self):
        self.db = firebase_config.get_db()
        self.auth_admin = firebase_config.get_auth_admin()
        self.auth_client = firebase_config.get_auth_client()
        self.users_collection = self.db.collection('users')
    
    def create_user(self, name, email, password):
        """Create new user in Firebase Auth and Firestore"""
        try:
            # Validate email format
            if not self._is_valid_email(email):
                return {'success': False, 'message': 'Invalid email format'}
            
            # Validate password strength
            if len(password) < 6:
                return {'success': False, 'message': 'Password must be at least 6 characters long'}
            
            # Create user in Firebase Auth
            user_record = self.auth_admin.create_user(
                email=email,
                password=password,
                display_name=name
            )
            
            # Create user profile in Firestore
            user_profile = {
                'id': user_record.uid,
                'name': name,
                'email': email,
                'created_at': datetime.now().isoformat(),
                'last_login': datetime.now().isoformat(),
                'total_interviews': 0,
                'average_score': 0.0,
                'preferred_roles': [],
                'skill_levels': {},
                'profile_completed': False
            }
            
            self.users_collection.document(user_record.uid).set(user_profile)
            
            return {'success': True, 'user': user_profile}
            
        except FirebaseError as e:
            error_message = str(e)
            if 'EMAIL_EXISTS' in error_message:
                return {'success': False, 'message': 'Email already exists'}
            elif 'WEAK_PASSWORD' in error_message:
                return {'success': False, 'message': 'Password is too weak'}
            else:
                return {'success': False, 'message': f'Registration failed: {error_message}'}
        except Exception as e:
            return {'success': False, 'message': f'An error occurred: {str(e)}'}
    
    def authenticate_user(self, email, password):
        """Authenticate user using Firebase Auth"""
        try:
            # Sign in with email and password using pyrebase
            user = self.auth_client.sign_in_with_email_and_password(email, password)
            
            # Get user profile from Firestore
            user_doc = self.users_collection.document(user['localId']).get()
            
            if user_doc.exists:
                user_profile = user_doc.to_dict()
                
                # Update last login
                self.users_collection.document(user['localId']).update({
                    'last_login': datetime.now().isoformat()
                })
                
                # Add Firebase token to user profile
                user_profile['firebase_token'] = user['idToken']
                user_profile['refresh_token'] = user['refreshToken']
                
                return {'success': True, 'user': user_profile}
            else:
                return {'success': False, 'message': 'User profile not found'}
                
        except Exception as e:
            error_message = str(e)
            if 'INVALID_PASSWORD' in error_message or 'EMAIL_NOT_FOUND' in error_message:
                return {'success': False, 'message': 'Invalid email or password'}
            elif 'TOO_MANY_ATTEMPTS_TRY_LATER' in error_message:
                return {'success': False, 'message': 'Too many failed attempts. Please try again later'}
            else:
                return {'success': False, 'message': f'Login failed: {error_message}'}
    
    def get_user_by_id(self, user_id):
        """Get user profile by ID from Firestore"""
        try:
            user_doc = self.users_collection.document(user_id).get()
            if user_doc.exists:
                return user_doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def update_user_profile(self, user_id, profile_data):
        """Update user profile in Firestore"""
        try:
            self.users_collection.document(user_id).update(profile_data)
            return True
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False
    
    def update_user_stats(self, user_id, interview_data):
        """Update user statistics after interview"""
        try:
            user_doc = self.users_collection.document(user_id).get()
            if not user_doc.exists:
                return False
            
            user_data = user_doc.to_dict()
            
            # Update statistics
            total_interviews = user_data.get('total_interviews', 0) + 1
            current_avg = user_data.get('average_score', 0)
            new_score = interview_data.get('overall_score', 0)
            
            # Calculate new average
            new_average = (current_avg * (total_interviews - 1) + new_score) / total_interviews
            
            # Update skill levels
            skill_levels = user_data.get('skill_levels', {})
            if 'skill_scores' in interview_data:
                for skill, score in interview_data['skill_scores'].items():
                    if skill in skill_levels:
                        # Average with existing score
                        skill_levels[skill] = (skill_levels[skill] + score) / 2
                    else:
                        skill_levels[skill] = score
            
            # Update user document
            self.users_collection.document(user_id).update({
                'total_interviews': total_interviews,
                'average_score': new_average,
                'skill_levels': skill_levels,
                'last_interview': datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            print(f"Error updating user stats: {e}")
            return False
    
    def verify_token(self, token):
        """Verify Firebase ID token"""
        try:
            decoded_token = self.auth_admin.verify_id_token(token)
            return decoded_token
        except Exception as e:
            print(f"Token verification failed: {e}")
            return None
    
    def refresh_token(self, refresh_token):
        """Refresh Firebase token"""
        try:
            user = self.auth_client.refresh(refresh_token)
            return user['idToken']
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return None
    
    def reset_password(self, email):
        """Send password reset email"""
        try:
            self.auth_client.send_password_reset_email(email)
            return {'success': True, 'message': 'Password reset email sent'}
        except Exception as e:
            return {'success': False, 'message': f'Failed to send reset email: {str(e)}'}
    
    def delete_user(self, user_id):
        """Delete user account"""
        try:
            # Delete from Firebase Auth
            self.auth_admin.delete_user(user_id)
            
            # Delete from Firestore
            self.users_collection.document(user_id).delete()
            
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def _is_valid_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def user_exists(self, email):
        """Check if user exists by email"""
        try:
            self.auth_admin.get_user_by_email(email)
            return True
        except auth.UserNotFoundError:
            return False
        except Exception:
            return False
