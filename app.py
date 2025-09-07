from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file, send_from_directory
from functools import wraps
import os
import json
from datetime import datetime
from utils.firebase_auth import FirebaseAuthManager
from utils.firebase_storage import FirebaseStorageManager
from utils.ai_helper import AIHelper
from utils.validators import ValidationHelper
from config import Config
from flask_session import Session


app = Flask(__name__)
app.config.from_object(Config)

# Initialize server-side sessions to handle large data
Session(app)

# Create session directory if it doesn't exist
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Initialize utilities with Firebase
auth_manager = FirebaseAuthManager()
storage_manager = FirebaseStorageManager()
ai_helper = AIHelper()
validator = ValidationHelper()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_interview_questions():
    """Load questions from Firebase session"""
    if 'interview_id' not in session:
        return None
    
    # Try to get from Firebase first
    session_data = storage_manager.get_interview_session(session['interview_id'])
    if session_data and 'questions' in session_data.get('session_data', {}):
        return session_data['session_data']['questions']
    
    # Fallback to local file for backward compatibility
    questions_file = f"data/sessions/questions_{session['interview_id']}.json"
    if os.path.exists(questions_file):
        with open(questions_file, 'r') as f:
            return json.load(f)
    return None

def cleanup_interview_files():
    """Clean up temporary interview files"""
    if 'interview_id' in session:
        # Clean up Firebase session
        storage_manager.delete_interview_session(session['interview_id'])
        
        # Clean up local files (for backward compatibility)
        questions_file = f"data/sessions/questions_{session['interview_id']}.json"
        if os.path.exists(questions_file):
            os.remove(questions_file)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                               'favicon.svg', mimetype='image/svg+xml')

@app.route('/')
def landing():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if validator.validate_email(email) and validator.validate_password(password):
            result = auth_manager.authenticate_user(email, password)
            if result['success']:
                user = result['user']
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                session['firebase_token'] = user.get('firebase_token')
                return redirect(url_for('dashboard'))
            else:
                flash(result['message'], 'error')
        else:
            flash('Please enter valid email and password', 'error')
    
    return render_template('auth/login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not validator.validate_name(name):
            flash('Please enter a valid name', 'error')
        elif not validator.validate_email(email):
            flash('Please enter a valid email', 'error')
        elif not validator.validate_password(password):
            flash('Password must be at least 8 characters long', 'error')
        elif password != confirm_password:
            flash('Passwords do not match', 'error')
        else:
            result = auth_manager.create_user(name, email, password)
            if result['success']:
                user = result['user']
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                flash('Account created successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash(result['message'], 'error')
    
    return render_template('auth/signup.html')

@app.route('/logout')
def logout():
    # Clean up temporary files before logout
    cleanup_interview_files()
    session.clear()
    return redirect(url_for('landing'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_stats = storage_manager.get_user_stats(session['user_id'])
    recent_reports = storage_manager.get_recent_reports(session['user_id'], limit=5)
    return render_template('dashboard/dashboard.html', 
                         stats=user_stats, 
                         recent_reports=recent_reports,
                         config=Config)

@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    if request.method == 'POST':
        setup_data = {
            'job_role': request.form.get('job_role'),
            'domain': request.form.get('domain'),
            'interview_type': request.form.get('interview_type'),
            'question_count': int(request.form.get('question_count', Config.DEFAULT_QUESTIONS_COUNT)),
            'question_type': request.form.get('question_type'),
            'difficulty': request.form.get('difficulty', 'Medium')
        }
        
        # Validate setup data
        if validator.validate_setup_data(setup_data):
            session['interview_setup'] = setup_data
            return redirect(url_for('loading'))
        else:
            flash('Please fill all required fields correctly', 'error')
    
    return render_template('dashboard/setup.html', config=Config)

@app.route('/loading')
@login_required
def loading():
    if 'interview_setup' not in session:
        return redirect(url_for('setup'))
    return render_template('dashboard/loading.html')

@app.route('/generate_questions', methods=['POST'])
@login_required
def generate_questions():
    if 'interview_setup' not in session:
        return jsonify({'error': 'No interview setup found'}), 400
    
    setup = session['interview_setup']
    
    try:
        # Clean up any previous interview files
        cleanup_interview_files()
        
        questions = ai_helper.generate_questions(setup)
        
        # Store questions in Firebase and local file as backup
        interview_id = f"{session['user_id']}_{int(datetime.now().timestamp())}"
        
        # Save to Firebase
        session_data = {
            'questions': questions,
            'setup': setup,
            'user_answers': {},
            'current_question': 0
        }
        storage_manager.save_interview_session(session['user_id'], interview_id, session_data)
        
        # Backup to local file
        questions_file = f"data/sessions/questions_{interview_id}.json"
        os.makedirs(os.path.dirname(questions_file), exist_ok=True)
        with open(questions_file, 'w') as f:
            json.dump(questions, f)
        
        # Clear all previous interview data and start fresh
        session['interview_id'] = interview_id
        session['current_question'] = 0
        session['user_answers'] = {}
        
        # Clear any previous results or report IDs
        session.pop('report_id', None)
        session.pop('interview_results', None)
        
        return jsonify({'success': True, 'questions_count': len(questions)})
    except Exception as e:
        return jsonify({'error': f'Failed to generate questions: {str(e)}'}), 500

@app.route('/interview')
@login_required
def interview():
    questions = load_interview_questions()
    if not questions:
        return redirect(url_for('setup'))
    
    current_q = session.get('current_question', 0)
    interview_id = session.get('interview_id', 'unknown')
    
    return render_template('dashboard/interview.html', 
                         questions=questions,
                         current_question=current_q,
                         total_questions=len(questions),
                         interview_id=interview_id)

@app.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    data = request.json
    question_index = data.get('question_index')
    answer = data.get('answer')
    
    if 'user_answers' not in session:
        session['user_answers'] = {}
    
    session['user_answers'][str(question_index)] = answer
    session.modified = True
    
    # Update Firebase session data
    if 'interview_id' in session:
        session_data = storage_manager.get_interview_session(session['interview_id'])
        if session_data:
            session_data['session_data']['user_answers'] = session['user_answers']
            session_data['session_data']['current_question'] = session.get('current_question', 0)
            storage_manager.update_interview_session(session['interview_id'], session_data['session_data'])
    
    return jsonify({'success': True})

@app.route('/next_question', methods=['POST'])
@login_required
def next_question():
    current = session.get('current_question', 0)
    questions = load_interview_questions()
    total = len(questions) if questions else 0
    
    if current < total - 1:
        session['current_question'] = current + 1
        return jsonify({'success': True, 'next_question': current + 1})
    else:
        return jsonify({'success': True, 'completed': True})

@app.route('/previous_question', methods=['POST'])
@login_required
def previous_question():
    current = session.get('current_question', 0)
    
    if current > 0:
        session['current_question'] = current - 1
        return jsonify({'success': True, 'previous_question': current - 1})
    else:
        return jsonify({'success': False, 'message': 'Already at first question'})

@app.route('/update_current_question', methods=['POST'])
@login_required
def update_current_question():
    data = request.json
    new_question = data.get('current_question')
    
    if new_question is not None:
        questions = load_interview_questions()
        total = len(questions) if questions else 0
        if 0 <= new_question < total:
            session['current_question'] = new_question
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Invalid question index'})

@app.route('/complete_interview', methods=['POST'])
@login_required
def complete_interview():
    questions = load_interview_questions()
    if not questions or 'user_answers' not in session:
        print("❌ Interview data not found - questions or answers missing")
        return jsonify({'error': 'Interview data not found'}), 400
    
    print(f"🎯 Completing interview for user: {session.get('user_id')}")
    print(f"📊 Questions count: {len(questions)}")
    print(f"📝 Answers count: {len(session['user_answers'])}")
    
    try:
        # Evaluate answers using AI
        print("🤖 Evaluating answers with AI...")
        results = ai_helper.evaluate_answers(
            questions,
            session['user_answers'],
            session['interview_setup']
        )
        print("✅ AI evaluation completed")
        
        # Save the report
        print("💾 Saving report to Firebase...")
        report_id = storage_manager.save_report(
            session['user_id'],
            session['interview_setup'],
            questions,
            session['user_answers'],
            results
        )
        
        if not report_id:
            print("❌ Failed to save report - no report ID returned")
            return jsonify({'error': 'Failed to save report'}), 500
        
        print(f"✅ Report saved with ID: {report_id}")
        
        # Store only result ID in session, not the full results
        session['report_id'] = report_id
        
        # Clean up temporary files
        cleanup_interview_files()
        
        return jsonify({'success': True, 'report_id': report_id})
    except Exception as e:
        print(f"❌ Error in complete_interview: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to evaluate interview: {str(e)}'}), 500

@app.route('/results')
@login_required
def results():
    if 'report_id' not in session:
        return redirect(url_for('dashboard'))
    
    # Load results from saved report
    report = storage_manager.get_report(session['user_id'], session['report_id'])
    if not report:
        flash('Results not found', 'error')
        return redirect(url_for('dashboard'))
    
    results = report.get('results', {})
    setup = report.get('setup', {})
    
    return render_template('dashboard/results.html', 
                         results=results,
                         setup=setup)

@app.route('/reports')
@login_required
def reports():
    print(f"📋 Fetching reports for user: {session.get('user_id')}")
    user_reports = storage_manager.get_user_reports(session['user_id'])
    print(f"📊 Reports retrieved: {len(user_reports)}")
    for i, report in enumerate(user_reports):
        print(f"  Report {i+1}: ID={report.get('id', 'N/A')}, Created={report.get('created_at', 'N/A')}")
    return render_template('dashboard/reports.html', reports=user_reports)

@app.route('/report/<report_id>')
@login_required
def view_report(report_id):
    report = storage_manager.get_report(session['user_id'], report_id)
    if not report:
        flash('Report not found', 'error')
        return redirect(url_for('reports'))
    
    return render_template('dashboard/results.html', 
                         results=report['results'],
                         setup=report['setup'],
                         report_date=report['created_at'])

@app.route('/download_report/<report_id>')
@login_required
def download_report(report_id):
    try:
        pdf_path = storage_manager.generate_pdf_report(session['user_id'], report_id)
        return send_file(pdf_path, as_attachment=True, 
                        download_name=f'interview_report_{report_id}.pdf')
    except Exception as e:
        flash('Error generating PDF report', 'error')
        return redirect(url_for('reports'))

@app.route('/api/stats')
@login_required
def api_stats():
    stats = storage_manager.get_detailed_stats(session['user_id'])
    return jsonify(stats)

@app.route('/debug/session')
@login_required  
def debug_session():
    """Debug route to check session data"""
    session_info = {
        'user_id': session.get('user_id'),
        'user_name': session.get('user_name'),
        'user_email': session.get('user_email'),
        'session_keys': list(session.keys())
    }
    
    print("🔍 Debug Session Info:")
    for key, value in session_info.items():
        print(f"  {key}: {value}")
    
    return jsonify(session_info)

@app.route('/debug/reports')
@login_required
def debug_reports():
    """Debug route to check reports data"""
    user_id = session.get('user_id')
    print(f"🔍 Debug Reports for user: {user_id}")
    
    if not user_id:
        return jsonify({'error': 'No user_id in session'})
    
    try:
        reports = storage_manager.get_user_reports(user_id)
        return jsonify({
            'user_id': user_id,
            'reports_count': len(reports),
            'reports': reports
        })
    except Exception as e:
        print(f"❌ Debug reports error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    # Ensure data directories exist
    os.makedirs('data/reports', exist_ok=True)
    
    # Get port from environment variable (for deployment platforms)
    port = int(os.environ.get('PORT', 5000))
    
    if Config.DEBUG:
        # Development server
        app.run(debug=True, host='127.0.0.1', port=port)
    else:
        # Production server (basic - use proper WSGI server for production)
        app.run(debug=False, host='0.0.0.0', port=port)
