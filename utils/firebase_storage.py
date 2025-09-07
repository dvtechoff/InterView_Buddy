import json
import os
import uuid
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from utils.firebase_config import firebase_config
from firebase_admin import storage
import io
import base64

class FirebaseStorageManager:
    def __init__(self):
        self.db = firebase_config.get_db()
        self.reports_collection = self.db.collection('reports')
        self.interviews_collection = self.db.collection('interviews')
        self.questions_collection = self.db.collection('questions')
    
    def save_report(self, user_id, setup, questions, answers, results):
        """Save interview report to Firestore"""
        try:
            report_id = str(uuid.uuid4())
            report_data = {
                'id': report_id,
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'setup': setup,
                'questions': questions,
                'answers': answers,
                'results': results,
                'type': 'interview_report'
            }
            
            # Save to Firestore
            self.reports_collection.document(report_id).set(report_data)
            print(f"✅ Report saved successfully: {report_id} for user: {user_id}")
            
            return report_id
            
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_user_reports(self, user_id):
        """Get all reports for a user from Firestore"""
        try:
            # First try simple query without ordering to test basic functionality
            reports_query = self.reports_collection.where('user_id', '==', user_id)
            reports = []
            
            print(f"🔍 Fetching reports for user: {user_id}")
            
            for doc in reports_query.stream():
                report_data = doc.to_dict()
                reports.append(report_data)
                print(f"📄 Found report: {report_data.get('id', 'unknown')} created at {report_data.get('created_at', 'unknown')}")
            
            # Sort by created_at in Python instead of Firestore to avoid index issues
            reports.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            print(f"📊 Total reports found: {len(reports)}")
            return reports
            
            return reports
            
        except Exception as e:
            print(f"Error getting user reports: {e}")
            return []
    
    def get_report(self, user_id, report_id):
        """Get specific report from Firestore"""
        try:
            report_doc = self.reports_collection.document(report_id).get()
            
            if report_doc.exists:
                report_data = report_doc.to_dict()
                # Verify the report belongs to the user
                if report_data.get('user_id') == user_id:
                    return report_data
            
            return None
            
        except Exception as e:
            print(f"Error getting report: {e}")
            return None
    
    def get_recent_reports(self, user_id, limit=5):
        """Get recent reports for a user"""
        try:
            # Get all reports for user first, then sort in Python to avoid index requirement
            reports_query = self.reports_collection.where('user_id', '==', user_id)
            
            reports = []
            for doc in reports_query.stream():
                reports.append(doc.to_dict())
            
            # Sort by created_at in Python and limit
            reports.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return reports[:limit]
            
        except Exception as e:
            print(f"Error getting recent reports: {e}")
            return []
    
    def get_user_stats(self, user_id):
        """Get user statistics from Firestore"""
        try:
            reports = self.get_user_reports(user_id)
            
            if not reports:
                return {
                    'total_interviews': 0,
                    'average_score': 0,
                    'best_score': 0,
                    'total_questions_answered': 0,
                    'favorite_domain': 'N/A',
                    'recent_performance': []
                }
            
            total_interviews = len(reports)
            scores = [report['results']['overall_score'] for report in reports if 'results' in report and 'overall_score' in report['results']]
            
            if scores:
                average_score = (sum(scores) / len(scores)) * 10
                best_score = max(scores) * 10
            else:
                average_score = 0
                best_score = 0
            
            total_questions = sum(len(report.get('questions', [])) for report in reports)
            
            # Find favorite domain
            domains = [report['setup']['domain'] for report in reports if 'setup' in report and 'domain' in report['setup']]
            favorite_domain = max(set(domains), key=domains.count) if domains else 'N/A'
            
            # Recent performance (last 10 interviews)
            recent_performance = []
            for report in reports[:10]:
                if 'results' in report and 'overall_score' in report['results']:
                    recent_performance.append({
                        'date': report['created_at'],
                        'score': report['results']['overall_score'] * 10,
                        'domain': report.get('setup', {}).get('domain', 'Unknown')
                    })
            
            return {
                'total_interviews': total_interviews,
                'average_score': round(average_score, 1),
                'best_score': round(best_score, 1),
                'total_questions_answered': total_questions,
                'favorite_domain': favorite_domain,
                'recent_performance': recent_performance
            }
            
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {
                'total_interviews': 0,
                'average_score': 0,
                'best_score': 0,
                'total_questions_answered': 0,
                'favorite_domain': 'N/A',
                'recent_performance': []
            }
    
    def get_detailed_stats(self, user_id):
        """Get detailed user statistics for charts and analytics"""
        try:
            reports = self.get_user_reports(user_id)
            
            if not reports:
                return {
                    'total_interviews': 0,
                    'average_score': 0,
                    'best_score': 0,
                    'total_questions_answered': 0,
                    'favorite_domain': 'N/A',
                    'recent_performance': [],
                    'recent_scores': [],  # Add this for the performance chart
                    'domain_breakdown': {},
                    'monthly_progress': [],
                    'skill_analysis': {}
                }
            
            # Basic stats
            total_interviews = len(reports)
            scores = [report['results']['overall_score'] for report in reports if 'results' in report and 'overall_score' in report['results']]
            
            if scores:
                average_score = sum(scores) / len(scores)  # Score is already 0-10
                best_score = max(scores)  # Score is already 0-10
            else:
                average_score = 0
                best_score = 0
            
            total_questions = sum(len(report.get('questions', [])) for report in reports)
            
            # Domain breakdown
            domains = [report['setup']['domain'] for report in reports if 'setup' in report and 'domain' in report['setup']]
            domain_breakdown = {}
            for domain in set(domains):
                domain_breakdown[domain] = domains.count(domain)
            
            favorite_domain = max(domain_breakdown, key=domain_breakdown.get) if domain_breakdown else 'N/A'
            
            # Recent performance (last 10 interviews)
            recent_performance = []
            for report in reports[:10]:
                if 'results' in report and 'overall_score' in report['results']:
                    recent_performance.append({
                        'date': report['created_at'][:10],  # Just the date part
                        'score': round(report['results']['overall_score'], 1),  # Score is already 0-10
                        'domain': report.get('setup', {}).get('domain', 'Unknown')
                    })
            
            # Monthly progress (group by month)
            monthly_progress = {}
            for report in reports:
                if 'created_at' in report and 'results' in report:
                    month = report['created_at'][:7]  # YYYY-MM format
                    if month not in monthly_progress:
                        monthly_progress[month] = {'count': 0, 'total_score': 0}
                    monthly_progress[month]['count'] += 1
                    monthly_progress[month]['total_score'] += report['results'].get('overall_score', 0)  # Score is already 0-10
            
            # Convert monthly progress to list
            monthly_list = []
            for month, data in sorted(monthly_progress.items()):
                monthly_list.append({
                    'month': month,
                    'interviews': data['count'],
                    'average_score': round(data['total_score'] / data['count'], 1) if data['count'] > 0 else 0
                })
            
            # Extract scores for the performance chart
            recent_scores = [perf['score'] for perf in recent_performance]
            
            return {
                'total_interviews': total_interviews,
                'average_score': round(average_score, 1),
                'best_score': round(best_score, 1),
                'total_questions_answered': total_questions,
                'favorite_domain': favorite_domain,
                'recent_performance': recent_performance,
                'recent_scores': recent_scores,  # Add this for the performance chart
                'domain_breakdown': domain_breakdown,
                'monthly_progress': monthly_list[-6:],  # Last 6 months
                'skill_analysis': {}
            }
            
        except Exception as e:
            print(f"Error getting detailed stats: {e}")
            return {
                'total_interviews': 0,
                'average_score': 0,
                'best_score': 0,
                'total_questions_answered': 0,
                'favorite_domain': 'N/A',
                'recent_performance': [],
                'recent_scores': [],  # Add this for the performance chart
                'domain_breakdown': {},
                'monthly_progress': [],
                'skill_analysis': {}
            }
    
    def save_interview_session(self, user_id, interview_id, session_data):
        """Save interview session data to Firestore"""
        try:
            session_doc = {
                'user_id': user_id,
                'interview_id': interview_id,
                'session_data': session_data,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            
            self.interviews_collection.document(interview_id).set(session_doc)
            return True
            
        except Exception as e:
            print(f"Error saving interview session: {e}")
            return False
    
    def get_interview_session(self, interview_id):
        """Get interview session data from Firestore"""
        try:
            session_doc = self.interviews_collection.document(interview_id).get()
            
            if session_doc.exists:
                return session_doc.to_dict()
            
            return None
            
        except Exception as e:
            print(f"Error getting interview session: {e}")
            return None
    
    def update_interview_session(self, interview_id, session_data):
        """Update interview session data in Firestore"""
        try:
            self.interviews_collection.document(interview_id).update({
                'session_data': session_data,
                'last_updated': datetime.now().isoformat()
            })
            return True
            
        except Exception as e:
            print(f"Error updating interview session: {e}")
            return False
    
    def delete_interview_session(self, interview_id):
        """Delete interview session from Firestore"""
        try:
            self.interviews_collection.document(interview_id).delete()
            return True
            
        except Exception as e:
            print(f"Error deleting interview session: {e}")
            return False
    
    def save_questions_cache(self, cache_key, questions):
        """Save generated questions to Firestore cache"""
        try:
            questions_doc = {
                'cache_key': cache_key,
                'questions': questions,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now().timestamp() + 3600)  # 1 hour expiry
            }
            
            self.questions_collection.document(cache_key).set(questions_doc)
            return True
            
        except Exception as e:
            print(f"Error saving questions cache: {e}")
            return False
    
    def get_questions_cache(self, cache_key):
        """Get cached questions from Firestore"""
        try:
            questions_doc = self.questions_collection.document(cache_key).get()
            
            if questions_doc.exists:
                data = questions_doc.to_dict()
                # Check if not expired
                if data.get('expires_at', 0) > datetime.now().timestamp():
                    return data.get('questions', [])
            
            return None
            
        except Exception as e:
            print(f"Error getting questions cache: {e}")
            return None
    
    def generate_pdf_report(self, user_id, report_id):
        """Generate PDF report and return file path"""
        try:
            # Get the report data first
            report_doc = self.reports_collection.document(report_id).get()
            
            if not report_doc.exists:
                raise ValueError("Report not found")
            
            report_data = report_doc.to_dict()
            
            # Verify the report belongs to the user
            if report_data.get('user_id') != user_id:
                raise ValueError("Report not found for this user")
            
            # Create data directory if it doesn't exist
            data_dir = os.path.join(os.getcwd(), 'data', 'reports')
            os.makedirs(data_dir, exist_ok=True)
            
            # Create PDF file path
            filename = f"report_{report_id}.pdf"
            filepath = os.path.join(data_dir, filename)
            
            # Create PDF
            doc = canvas.Canvas(filepath, pagesize=letter)
            width, height = letter
            
            # Title
            doc.setFont("Helvetica-Bold", 20)
            doc.drawString(50, height - 50, "Interview Report")
            
            # Basic info
            doc.setFont("Helvetica", 12)
            y_position = height - 100
            
            # Format date nicely
            created_at = report_data.get('created_at', 'N/A')
            if created_at != 'N/A':
                try:
                    date_str = created_at[:10]  # Just the date part
                except:
                    date_str = created_at
            else:
                date_str = 'N/A'
            
            doc.drawString(50, y_position, f"Date: {date_str}")
            y_position -= 20
            
            setup = report_data.get('setup', {})
            doc.drawString(50, y_position, f"Domain: {setup.get('domain', 'N/A')}")
            y_position -= 20
            doc.drawString(50, y_position, f"Role: {setup.get('role', 'N/A')}")
            y_position -= 20
            doc.drawString(50, y_position, f"Experience: {setup.get('experience', 'N/A')}")
            y_position -= 20
            doc.drawString(50, y_position, f"Interview Type: {setup.get('interview_type', 'N/A')}")
            y_position -= 40
            
            # Overall score
            results = report_data.get('results', {})
            overall_score = results.get('overall_score', 0)
            doc.setFont("Helvetica-Bold", 14)
            doc.drawString(50, y_position, f"Overall Score: {overall_score:.1f}/10")
            y_position -= 40
            
            # Category scores if available
            category_scores = results.get('category_scores', {})
            if category_scores:
                doc.setFont("Helvetica-Bold", 12)
                doc.drawString(50, y_position, "Category Scores:")
                y_position -= 20
                doc.setFont("Helvetica", 11)
                for category, score in category_scores.items():
                    doc.drawString(70, y_position, f"{category}: {score:.1f}/10")
                    y_position -= 18
                y_position -= 20
            
            # Strengths and weaknesses
            strengths = results.get('strengths', [])
            if strengths:
                doc.setFont("Helvetica-Bold", 12)
                doc.drawString(50, y_position, "Strengths:")
                y_position -= 20
                doc.setFont("Helvetica", 10)
                for strength in strengths:
                    if y_position < 100:  # Start new page if needed
                        doc.showPage()
                        y_position = height - 50
                    doc.drawString(70, y_position, f"• {strength}")
                    y_position -= 15
                y_position -= 10
            
            weaknesses = results.get('weaknesses', [])
            if weaknesses:
                if y_position < 150:  # Start new page if needed
                    doc.showPage()
                    y_position = height - 50
                doc.setFont("Helvetica-Bold", 12)
                doc.drawString(50, y_position, "Areas for Improvement:")
                y_position -= 20
                doc.setFont("Helvetica", 10)
                for weakness in weaknesses:
                    if y_position < 100:  # Start new page if needed
                        doc.showPage()
                        y_position = height - 50
                    doc.drawString(70, y_position, f"• {weakness}")
                    y_position -= 15
                y_position -= 20
            
            # Questions and answers
            questions = report_data.get('questions', [])
            answers = report_data.get('answers', [])
            
            if questions and answers:
                if y_position < 200:  # Start new page if needed
                    doc.showPage()
                    y_position = height - 50
                
                doc.setFont("Helvetica-Bold", 12)
                doc.drawString(50, y_position, "Questions & Answers:")
                y_position -= 30
                
                doc.setFont("Helvetica", 10)
                for i, (question, answer) in enumerate(zip(questions, answers)):
                    if y_position < 120:  # Start new page if needed
                        doc.showPage()
                        y_position = height - 50
                    
                    # Question
                    doc.setFont("Helvetica-Bold", 10)
                    question_text = f"Q{i+1}: {question}"
                    if len(question_text) > 90:
                        question_text = question_text[:87] + "..."
                    doc.drawString(50, y_position, question_text)
                    y_position -= 20
                    
                    # Answer
                    doc.setFont("Helvetica", 9)
                    answer_text = f"Answer: {answer}"
                    if len(answer_text) > 100:
                        answer_text = answer_text[:97] + "..."
                    doc.drawString(70, y_position, answer_text)
                    y_position -= 30
            
            doc.save()
            return filepath
            
        except Exception as e:
            print(f"Error generating PDF report: {e}")
            raise
    
    def delete_report(self, user_id, report_id):
        """Delete a specific report"""
        try:
            report_doc = self.reports_collection.document(report_id).get()
            
            if report_doc.exists:
                report_data = report_doc.to_dict()
                # Verify the report belongs to the user
                if report_data.get('user_id') == user_id:
                    self.reports_collection.document(report_id).delete()
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting report: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired interview sessions"""
        try:
            # Get sessions older than 24 hours
            cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)
            
            expired_sessions = self.interviews_collection.where(
                'created_at', '<', datetime.fromtimestamp(cutoff_time).isoformat()
            ).stream()
            
            for session in expired_sessions:
                session.reference.delete()
            
            return True
            
        except Exception as e:
            print(f"Error cleaning up expired sessions: {e}")
            return False
