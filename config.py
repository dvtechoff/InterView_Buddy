import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'interview-buddy-secret-key-2024'
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'AIzaSyAhaDdX0180qPIesVk7XOMuWgt5_Rjej-8'
    
    # Environment settings
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    
    # Firebase Configuration
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY')
    FIREBASE_AUTH_DOMAIN = os.environ.get('FIREBASE_AUTH_DOMAIN')
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET')
    FIREBASE_MESSAGING_SENDER_ID = os.environ.get('FIREBASE_MESSAGING_SENDER_ID')
    FIREBASE_APP_ID = os.environ.get('FIREBASE_APP_ID')
    FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL', "")
    
    # Firebase Service Account (for admin operations)
    FIREBASE_SERVICE_ACCOUNT_PATH = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')
    FIREBASE_PRIVATE_KEY = os.environ.get('FIREBASE_PRIVATE_KEY')
    FIREBASE_CLIENT_EMAIL = os.environ.get('FIREBASE_CLIENT_EMAIL')
    
    # Session configuration for large data storage
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'data/sessions'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'interview_buddy:'
    
    # Application settings
    APP_NAME = "Interview Buddy"
    APP_VERSION = "1.0.0"
    
    # Interview settings
    MAX_QUESTIONS_PER_SESSION = 20
    MIN_QUESTIONS_PER_SESSION = 5
    DEFAULT_QUESTIONS_COUNT = 10
    
    # File paths
    USERS_FILE = 'data/users.json'
    REPORTS_DIR = 'data/reports'
    
    # Supported job roles and domains
    JOB_ROLES = [
        'Software Engineer',
        'Frontend Developer',
        'Backend Developer',
        'Full Stack Developer',
        'Data Scientist',
        'Data Analyst',
        'Product Manager',
        'UI/UX Designer',
        'DevOps Engineer',
        'System Administrator',
        'QA Engineer',
        'Business Analyst'
    ]
    
    DOMAINS = {
        'Frontend': ['React', 'Angular', 'Vue.js', 'JavaScript', 'CSS', 'HTML'],
        'Backend': ['Python', 'Java', 'Node.js', 'C#', '.NET', 'PHP'],
        'Database': ['SQL', 'MongoDB', 'PostgreSQL', 'Redis', 'Elasticsearch'],
        'Cloud': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes'],
        'Mobile': ['React Native', 'Flutter', 'iOS', 'Android'],
        'AI/ML': ['Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision'],
        'System Design': ['Scalability', 'Microservices', 'Architecture', 'Load Balancing']
    }
    
    INTERVIEW_TYPES = ['Technical', 'Behavioral', 'Mixed']
    QUESTION_TYPES = ['MCQ', 'Short Answer', 'AI Choice']
    
    # Scoring settings
    MCQ_MAX_SCORE = 10
    SHORT_ANSWER_MAX_SCORE = 10
    PASS_PERCENTAGE = 70
