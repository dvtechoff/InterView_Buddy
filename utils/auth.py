import json
import hashlib
import uuid
from datetime import datetime
from config import Config
import os

class AuthManager:
    def __init__(self):
        self.users_file = Config.USERS_FILE
        self.ensure_users_file()
    
    def ensure_users_file(self):
        """Ensure users file exists"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump([], f)
    
    def hash_password(self, password):
        """Hash password with salt"""
        return hashlib.sha256((password + Config.SECRET_KEY).encode()).hexdigest()
    
    def load_users(self):
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save_users(self, users):
        """Save users to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def user_exists(self, email):
        """Check if user exists"""
        users = self.load_users()
        return any(user['email'] == email for user in users)
    
    def create_user(self, name, email, password):
        """Create new user"""
        if self.user_exists(email):
            return None
        
        users = self.load_users()
        user = {
            'id': str(uuid.uuid4()),
            'name': name,
            'email': email,
            'password': self.hash_password(password),
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat(),
            'total_interviews': 0,
            'average_score': 0.0,
            'preferred_roles': [],
            'skill_levels': {}
        }
        
        users.append(user)
        self.save_users(users)
        return user
    
    def authenticate_user(self, email, password):
        """Authenticate user login"""
        users = self.load_users()
        hashed_password = self.hash_password(password)
        
        for i, user in enumerate(users):
            if user['email'] == email and user['password'] == hashed_password:
                # Update last login
                users[i]['last_login'] = datetime.now().isoformat()
                self.save_users(users)
                return user
        
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        users = self.load_users()
        return next((user for user in users if user['id'] == user_id), None)
    
    def update_user_stats(self, user_id, interview_data):
        """Update user statistics after interview"""
        users = self.load_users()
        for i, user in enumerate(users):
            if user['id'] == user_id:
                users[i]['total_interviews'] += 1
                current_avg = users[i]['average_score']
                total_interviews = users[i]['total_interviews']
                new_score = interview_data.get('overall_score', 0)
                
                # Calculate new average
                users[i]['average_score'] = (
                    (current_avg * (total_interviews - 1) + new_score) / total_interviews
                )
                
                # Update skill levels
                if 'skill_scores' in interview_data:
                    for skill, score in interview_data['skill_scores'].items():
                        if skill not in users[i]['skill_levels']:
                            users[i]['skill_levels'][skill] = []
                        users[i]['skill_levels'][skill].append(score)
                
                self.save_users(users)
                break
