import json
import os
import uuid
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from config import Config

class StorageManager:
    def __init__(self):
        self.reports_dir = Config.REPORTS_DIR
        self.users_file = Config.USERS_FILE
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure necessary directories exist"""
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
    
    def save_report(self, user_id, setup, questions, answers, results):
        """Save interview report"""
        report_id = str(uuid.uuid4())
        report_data = {
            'id': report_id,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'setup': setup,
            'questions': questions,
            'answers': answers,
            'results': results
        }
        
        # Save to user-specific reports file
        user_reports_file = os.path.join(self.reports_dir, f'{user_id}_reports.json')
        
        if os.path.exists(user_reports_file):
            with open(user_reports_file, 'r') as f:
                reports = json.load(f)
        else:
            reports = []
        
        reports.append(report_data)
        
        with open(user_reports_file, 'w') as f:
            json.dump(reports, f, indent=2)
        
        return report_id
    
    def get_user_reports(self, user_id):
        """Get all reports for a user"""
        user_reports_file = os.path.join(self.reports_dir, f'{user_id}_reports.json')
        
        if os.path.exists(user_reports_file):
            with open(user_reports_file, 'r') as f:
                reports = json.load(f)
            # Sort by date (newest first)
            return sorted(reports, key=lambda x: x['created_at'], reverse=True)
        
        return []
    
    def get_report(self, user_id, report_id):
        """Get specific report"""
        reports = self.get_user_reports(user_id)
        return next((report for report in reports if report['id'] == report_id), None)
    
    def get_recent_reports(self, user_id, limit=5):
        """Get recent reports for a user"""
        reports = self.get_user_reports(user_id)
        return reports[:limit]
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        reports = self.get_user_reports(user_id)
        
        if not reports:
            return {
                'total_interviews': 0,
                'average_score': 0,
                'best_score': 0,
                'total_questions_answered': 0,
                'favorite_domain': 'N/A'
            }
        
        total_interviews = len(reports)
        scores = [report['results']['overall_score'] for report in reports]
        average_score = (sum(scores) / len(scores))*10
        best_score = max(scores)*10
        
        total_questions = sum(len(report['questions']) for report in reports)
        
        # Find favorite domain
        domains = [report['setup']['domain'] for report in reports]
        favorite_domain = max(set(domains), key=domains.count) if domains else 'N/A'
        
        return {
            'total_interviews': total_interviews,
            'average_score': round(average_score, 1),
            'best_score': best_score,
            'total_questions_answered': total_questions,
            'favorite_domain': favorite_domain
        }
    
    def get_detailed_stats(self, user_id):
        """Get detailed statistics for charts and analysis"""
        reports = self.get_user_reports(user_id)
        
        if not reports:
            return {}
        
        # Score progression over time
        score_progression = []
        for report in reversed(reports):  # Chronological order
            score_progression.append({
                'date': report['created_at'][:10],  # YYYY-MM-DD
                'score': report['results']['overall_score']
            })
        
        # Category performance
        category_performance = {}
        for report in reports:
            for category, score in report['results'].get('category_scores', {}).items():
                if category not in category_performance:
                    category_performance[category] = []
                category_performance[category].append(score)
        
        # Average category scores
        avg_category_scores = {}
        for category, scores in category_performance.items():
            avg_category_scores[category] = round(sum(scores) / len(scores), 1)
        
        # Domain distribution
        domains = [report['setup']['domain'] for report in reports]
        domain_counts = {}
        for domain in domains:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        return {
            'score_progression': score_progression,
            'category_performance': avg_category_scores,
            'domain_distribution': domain_counts,
            'recent_scores': [report['results']['overall_score'] for report in reports[:10]]
        }
    
    def get_leaderboard(self, limit=10):
        """Get anonymous leaderboard"""
        all_reports = []
        
        # Collect all reports from all users
        for filename in os.listdir(self.reports_dir):
            if filename.endswith('_reports.json'):
                filepath = os.path.join(self.reports_dir, filename)
                with open(filepath, 'r') as f:
                    user_reports = json.load(f)
                    for report in user_reports:
                        all_reports.append({
                            'score': report['results']['overall_score'],
                            'domain': report['setup']['domain'],
                            'job_role': report['setup']['job_role'],
                            'date': report['created_at'][:10]
                        })
        
        # Sort by score and get top performers
        top_scores = sorted(all_reports, key=lambda x: x['score'], reverse=True)[:limit]
        
        # Anonymize the data
        leaderboard = []
        for i, entry in enumerate(top_scores):
            leaderboard.append({
                'rank': i + 1,
                'score': entry['score'],
                'domain': entry['domain'],
                'job_role': entry['job_role'],
                'date': entry['date'],
                'anonymous_id': f"User{i+1:03d}"
            })
        
        return leaderboard
    
    def generate_pdf_report(self, user_id, report_id):
        """Generate PDF report"""
        report = self.get_report(user_id, report_id)
        if not report:
            raise ValueError("Report not found")
        
        filename = f"report_{report_id}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        # Create PDF
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        
        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "Interview Report")
        
        # User info
        c.setFont("Helvetica", 12)
        y_position = height - 100
        
        c.drawString(50, y_position, f"Date: {report['created_at'][:10]}")
        y_position -= 20
        c.drawString(50, y_position, f"Job Role: {report['setup']['job_role']}")
        y_position -= 20
        c.drawString(50, y_position, f"Domain: {report['setup']['domain']}")
        y_position -= 20
        c.drawString(50, y_position, f"Interview Type: {report['setup']['interview_type']}")
        y_position -= 40
        
        # Results
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "Results Summary")
        y_position -= 30
        
        c.setFont("Helvetica", 12)
        results = report['results']
        c.drawString(50, y_position, f"Overall Score: {results['overall_score']}/10")
        y_position -= 20
        
        # Category scores
        for category, score in results.get('category_scores', {}).items():
            c.drawString(50, y_position, f"{category}: {score}/10")
            y_position -= 20
        
        y_position -= 20
        
        # Strengths and weaknesses
        if results.get('strengths'):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, "Strengths:")
            y_position -= 20
            c.setFont("Helvetica", 10)
            for strength in results['strengths']:
                c.drawString(70, y_position, f"• {strength}")
                y_position -= 15
            y_position -= 10
        
        if results.get('weaknesses'):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, "Areas for Improvement:")
            y_position -= 20
            c.setFont("Helvetica", 10)
            for weakness in results['weaknesses']:
                c.drawString(70, y_position, f"• {weakness}")
                y_position -= 15
        
        c.save()
        return filepath
