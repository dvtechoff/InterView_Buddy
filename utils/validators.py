import re
from config import Config

class ValidationHelper:
    def __init__(self):
        pass
    
    def validate_email(self, email):
        """Validate email format"""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        """Validate password strength"""
        if not password:
            return False
        return len(password) >= 8
    
    def validate_name(self, name):
        """Validate name"""
        if not name:
            return False
        return len(name.strip()) >= 2 and name.strip().replace(' ', '').isalpha()
    
    def validate_setup_data(self, setup_data):
        """Validate interview setup data"""
        required_fields = ['job_role', 'domain', 'interview_type', 'question_count', 'question_type']
        
        # Check required fields
        for field in required_fields:
            if field not in setup_data or not setup_data[field]:
                return False
        
        # Validate job role
        if setup_data['job_role'] not in Config.JOB_ROLES:
            return False
        
        # Validate domain
        valid_domains = []
        for domain_list in Config.DOMAINS.values():
            valid_domains.extend(domain_list)
        valid_domains.extend(Config.DOMAINS.keys())
        
        if setup_data['domain'] not in valid_domains:
            return False
        
        # Validate interview type
        if setup_data['interview_type'] not in Config.INTERVIEW_TYPES:
            return False
        
        # Validate question type
        if setup_data['question_type'] not in Config.QUESTION_TYPES:
            return False
        
        # Validate question count
        try:
            count = int(setup_data['question_count'])
            if count < Config.MIN_QUESTIONS_PER_SESSION or count > Config.MAX_QUESTIONS_PER_SESSION:
                return False
        except (ValueError, TypeError):
            return False
        
        return True
    
    def validate_question_answer(self, question_type, answer):
        """Validate question answer format"""
        if not answer or not answer.strip():
            return False
        
        if question_type == 'mcq':
            # MCQ answers should be A, B, C, or D
            return answer.upper() in ['A', 'B', 'C', 'D']
        
        if question_type == 'short':
            # Short answers should have minimum length
            return len(answer.strip()) >= 10
        
        return True
    
    def sanitize_input(self, text):
        """Sanitize user input"""
        if not text:
            return ""
        
        # Remove HTML tags and script content
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
        
        # Limit length
        if len(text) > 1000:
            text = text[:1000]
        
        return text.strip()
    
    def validate_file_upload(self, file):
        """Validate file upload (for future resume upload feature)"""
        if not file:
            return False, "No file provided"
        
        # Check file size (5MB limit)
        if file.content_length > 5 * 1024 * 1024:
            return False, "File size too large (max 5MB)"
        
        # Check file extension
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        filename = file.filename.lower()
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return False, "Invalid file type"
        
        return True, "Valid file"
