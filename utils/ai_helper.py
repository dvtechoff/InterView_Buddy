import google.generativeai as genai
import json
import re
import random
from config import Config

class AIHelper:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.behavioral_questions = self._get_behavioral_questions()
    
    def _get_behavioral_questions(self):
        """Get comprehensive list of behavioral interview questions"""
        return {
            "leadership": [
                "Tell me about a time when you had to lead a team through a difficult project.",
                "Describe a situation where you had to make a difficult decision that affected your team.",
                "Give me an example of when you had to motivate a team member who was underperforming.",
                "Tell me about a time when you had to delegate tasks to team members.",
                "Describe a situation where you had to lead by example.",
            ],
            "teamwork": [
                "Tell me about a time when you had to work with a difficult team member.",
                "Describe a situation where you had to collaborate with people from different departments.",
                "Give me an example of when you went above and beyond to help a colleague.",
                "Tell me about a successful team project you were part of and your role in it.",
                "Describe a time when your team faced a major challenge and how you contributed to solving it.",
            ],
            "conflict_resolution": [
                "Tell me about a time when you had a disagreement with a colleague and how you resolved it.",
                "Describe a situation where you had to mediate between two conflicting parties.",
                "Give me an example of when you had to deal with a difficult customer or stakeholder.",
                "Tell me about a time when you received criticism and how you handled it.",
                "Describe a situation where you had to give constructive feedback to someone.",
            ],
            "problem_solving": [
                "Tell me about a time when you faced a complex problem and how you solved it.",
                "Describe a situation where you had to think outside the box to find a solution.",
                "Give me an example of when you had to work with limited resources to achieve a goal.",
                "Tell me about a time when you had to quickly adapt to unexpected changes.",
                "Describe a situation where you identified a process improvement opportunity.",
            ],
            "communication": [
                "Tell me about a time when you had to explain a complex technical concept to a non-technical audience.",
                "Describe a situation where you had to persuade someone to see your point of view.",
                "Give me an example of when you had to deliver bad news to a client or stakeholder.",
                "Tell me about a time when you had to present to senior management.",
                "Describe a situation where miscommunication caused problems and how you handled it.",
            ],
            "adaptability": [
                "Tell me about a time when you had to adapt to significant changes in your workplace.",
                "Describe a situation where you had to learn a new skill quickly.",
                "Give me an example of when you had to work outside your comfort zone.",
                "Tell me about a time when a project's requirements changed midway through.",
                "Describe how you handle working under pressure and tight deadlines.",
            ],
            "initiative": [
                "Tell me about a time when you took initiative to improve something at work.",
                "Describe a situation where you identified and solved a problem before it became critical.",
                "Give me an example of when you went beyond your job responsibilities.",
                "Tell me about a project you started from scratch.",
                "Describe a time when you suggested a new idea or process improvement.",
            ],
            "failure_learning": [
                "Tell me about a time when you failed at something and what you learned from it.",
                "Describe a situation where you made a mistake and how you handled it.",
                "Give me an example of when you received negative feedback and how you responded.",
                "Tell me about a goal you didn't achieve and why.",
                "Describe a time when you had to admit you were wrong.",
            ],
            "time_management": [
                "Tell me about a time when you had to manage multiple priorities.",
                "Describe how you handle competing deadlines.",
                "Give me an example of when you had to work on a project with a very tight timeline.",
                "Tell me about a time when you had to say no to a request to focus on priorities.",
                "Describe your approach to managing long-term projects with multiple milestones.",
            ],
            "ethics_integrity": [
                "Tell me about a time when you had to make an ethical decision at work.",
                "Describe a situation where you witnessed unethical behavior and how you handled it.",
                "Give me an example of when you had to maintain confidentiality in a difficult situation.",
                "Tell me about a time when you had to choose between company profit and doing the right thing.",
                "Describe a situation where you had to deliver on a promise despite difficulties.",
            ]
        }
    
    def generate_questions(self, setup_data):
        """Generate interview questions based on setup"""
        job_role = setup_data['job_role']
        domain = setup_data['domain']
        interview_type = setup_data['interview_type']
        question_count = setup_data['question_count']
        question_type = setup_data['question_type']
        difficulty = setup_data.get('difficulty', 'Medium')
        
        # For behavioral interviews, force short answer type and use predefined questions
        if interview_type.lower() == 'behavioral':
            setup_data['question_type'] = 'Short Answer'  # Force short answer for behavioral
            return self._get_behavioral_interview_questions(setup_data)
        
        prompt = self._build_question_prompt(
            job_role, domain, interview_type, question_count, 
            question_type, difficulty
        )
        
        try:
            response = self.model.generate_content(prompt)
            questions = self._parse_questions_response(response.text, question_type)
            return questions[:question_count]  # Ensure exact count
        except Exception as e:
            # Fallback to sample questions if AI fails
            return self._get_fallback_questions(setup_data)
    
    def _build_question_prompt(self, job_role, domain, interview_type, 
                              question_count, question_type, difficulty):
        """Build prompt for question generation"""
        
        # Enhanced prompt for behavioral interviews
        if interview_type.lower() == 'behavioral':
            prompt = f"""
Generate {question_count} behavioral interview questions for a {job_role} position.

Focus on these key behavioral areas:
- Leadership and management
- Teamwork and collaboration
- Problem-solving and decision-making
- Communication skills
- Adaptability and change management
- Conflict resolution
- Initiative and innovation
- Learning from failure
- Time management and prioritization
- Ethics and integrity

Use the STAR method framework (Situation, Task, Action, Result) for question structure.
Questions should start with phrases like:
- "Tell me about a time when..."
- "Describe a situation where..."
- "Give me an example of..."
- "Can you walk me through..."

Format your response as a JSON array where each question has:
- "text": The question text (STAR-format behavioral question)
- "type": "short"
- "category": The behavioral skill being tested
- "difficulty": "{difficulty}"

Example:
{{
  "text": "Tell me about a time when you had to lead a team through a difficult project. What was the situation, what did you do, and what was the outcome?",
  "type": "short",
  "category": "Leadership",
  "difficulty": "{difficulty}"
}}

Generate {question_count} diverse behavioral questions now:
            """
        else:
            prompt = f"""
Generate {question_count} {difficulty.lower()} level {interview_type.lower()} interview questions 
for a {job_role} position focusing on {domain}.

Requirements:
- Question type: {question_type}
- Difficulty: {difficulty}
- Professional and relevant to the role
- Include practical scenarios where applicable

Format your response as a JSON array where each question has:
- "text": The question text
- "type": "mcq" or "short"
- "options": Array of 4 options (for MCQ only, format as "A. option", "B. option", etc.)
- "correct_answer": The correct answer (for MCQ: "A", "B", "C", or "D")
- "category": The skill category this question tests
- "difficulty": The difficulty level

For MCQ questions, ensure options are realistic and the correct answer is not obvious.
For short answer questions, provide questions that test practical knowledge and problem-solving.

Example MCQ:
{{
  "text": "Which design pattern is most suitable for creating a single instance of a class?",
  "type": "mcq",
  "options": ["A. Factory Pattern", "B. Singleton Pattern", "C. Observer Pattern", "D. Strategy Pattern"],
  "correct_answer": "B",
  "category": "Design Patterns",
  "difficulty": "Medium"
}}

Example Short Answer:
{{
  "text": "Explain the difference between REST and GraphQL APIs, including their advantages and use cases.",
  "type": "short",
  "category": "API Design",
  "difficulty": "Medium"
}}

Generate the questions now:
            """
        return prompt
    
    def _get_behavioral_interview_questions(self, setup_data):
        """Generate behavioral interview questions from predefined list"""
        question_count = setup_data['question_count']
        difficulty = setup_data.get('difficulty', 'Medium')
        
        # Collect questions from all categories
        all_questions = []
        for category, questions in self.behavioral_questions.items():
            for question_text in questions:
                all_questions.append({
                    "text": question_text,
                    "type": "short",  # Always short answer for behavioral questions
                    "category": category.replace('_', ' ').title(),
                    "difficulty": difficulty
                })
        
        # Shuffle and select the required number
        random.shuffle(all_questions)
        selected_questions = all_questions[:question_count]
        
        # Ensure all questions are short answer type (no MCQ options)
        for question in selected_questions:
            question["type"] = "short"
            # Remove any MCQ-related fields if they exist
            question.pop("options", None)
            question.pop("correct_answer", None)
        
        return selected_questions
    
    def _parse_questions_response(self, response_text, question_type):
        """Parse AI response into structured questions"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                questions_json = json_match.group(0)
                questions = json.loads(questions_json)
                
                # Validate and clean questions
                valid_questions = []
                for q in questions:
                    if self._validate_question(q):
                        valid_questions.append(q)
                
                return valid_questions
        except:
            pass
        
        # Fallback parsing
        return self._parse_fallback(response_text, question_type)
    
    def _validate_question(self, question):
        """Validate question structure"""
        required_fields = ['text', 'type', 'category']
        
        if not all(field in question for field in required_fields):
            return False
        
        if question['type'] == 'mcq':
            return 'options' in question and 'correct_answer' in question
        
        return True
    
    def _parse_fallback(self, response_text, question_type):
        """Fallback parsing method"""
        # Simple parsing for when JSON extraction fails
        questions = []
        lines = response_text.split('\n')
        
        current_question = {}
        for line in lines:
            line = line.strip()
            if line.startswith('Q') or line.startswith(('1.', '2.', '3.')):
                if current_question and 'text' in current_question:
                    questions.append(current_question)
                current_question = {
                    'text': line,
                    'type': 'short' if question_type == 'Short Answer' else 'mcq',
                    'category': 'General',
                    'difficulty': 'Medium'
                }
            elif line.startswith(('A.', 'B.', 'C.', 'D.')):
                if 'options' not in current_question:
                    current_question['options'] = []
                current_question['options'].append(line)
        
        if current_question and 'text' in current_question:
            questions.append(current_question)
        
        return questions
    
    def _get_fallback_questions(self, setup_data):
        """Provide fallback questions if AI generation fails"""
        interview_type = setup_data.get('interview_type', '').lower()
        
        # Use behavioral questions for behavioral interviews
        if interview_type == 'behavioral':
            return self._get_behavioral_interview_questions(setup_data)
        
        fallback_questions = {
            'Software Engineer': [
                {
                    "text": "What is the time complexity of binary search?",
                    "type": "mcq",
                    "options": ["A. O(n)", "B. O(log n)", "C. O(n log n)", "D. O(1)"],
                    "correct_answer": "B",
                    "category": "Algorithms",
                    "difficulty": "Medium"
                },
                {
                    "text": "Explain the difference between stack and heap memory allocation.",
                    "type": "short",
                    "category": "Memory Management",
                    "difficulty": "Medium"
                }
            ],
            'Data Scientist': [
                {
                    "text": "What is overfitting in machine learning?",
                    "type": "short",
                    "category": "Machine Learning",
                    "difficulty": "Medium"
                },
                {
                    "text": "Which algorithm is best for classification with small datasets?",
                    "type": "mcq",
                    "options": ["A. Random Forest", "B. SVM", "C. Neural Networks", "D. Linear Regression"],
                    "correct_answer": "B",
                    "category": "Machine Learning",
                    "difficulty": "Medium"
                }
            ]
        }
        
        job_role = setup_data['job_role']
        questions = fallback_questions.get(job_role, fallback_questions['Software Engineer'])
        return questions * (setup_data['question_count'] // len(questions) + 1)
    
    def evaluate_answers(self, questions, user_answers, setup_data):
        """Evaluate user answers using AI"""
        results = {
            'questions_results': [],
            'overall_score': 0,
            'category_scores': {},
            'strengths': [],
            'weaknesses': [],
            'recommendations': [],
            'suggested_resources': []
        }
        
        total_score = 0
        category_scores = {}
        all_resources = []
        
        for i, question in enumerate(questions):
            question_result = self._evaluate_single_question(
                question, user_answers.get(str(i), ''), setup_data
            )
            results['questions_results'].append(question_result)
            total_score += question_result['score']
            
            # Collect resources from each question
            if question_result.get('suggested_resources'):
                all_resources.extend(question_result['suggested_resources'])
            
            category = question.get('category', 'General')
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(question_result['score'])
        
        # Calculate averages
        results['overall_score'] = round(total_score / len(questions), 1) if questions else 0
        
        for category, scores in category_scores.items():
            results['category_scores'][category] = round(sum(scores) / len(scores), 1)
        
        # Remove duplicate resources and limit to top recommendations
        unique_resources = list(dict.fromkeys(all_resources))  # Preserve order while removing duplicates
        results['suggested_resources'] = unique_resources[:8]  # Limit to 8 total resources
        
        # Generate insights
        results['strengths'], results['weaknesses'] = self._analyze_performance(
            results['category_scores']
        )
        results['recommendations'] = self._generate_recommendations(
            results['weaknesses'], setup_data
        )
        
        return results
    
    def _evaluate_single_question(self, question, user_answer, setup_data):
        """Evaluate a single question with detailed analysis"""
        result = {
            'question': question['text'],
            'user_answer': user_answer,
            'correct_answer': question.get('correct_answer', ''),
            'score': 0,
            'feedback': '',
            'category': question.get('category', 'General'),
            'detailed_analysis': {
                'clarity': {'score': 0, 'feedback': ''},
                'correctness': {'score': 0, 'feedback': ''},
                'completeness': {'score': 0, 'feedback': ''}
            },
            'suggested_resources': []
        }
        
        if question['type'] == 'mcq':
            correct_answer = question.get('correct_answer', '')
            if user_answer == correct_answer:
                result['score'] = Config.MCQ_MAX_SCORE
                result['feedback'] = 'Correct! Well done.'
                result['detailed_analysis']['correctness'] = {
                    'score': 10, 
                    'feedback': 'Answer is technically correct.'
                }
            else:
                result['score'] = 0
                result['feedback'] = f'Incorrect. The correct answer is {correct_answer}.'
                result['detailed_analysis']['correctness'] = {
                    'score': 0, 
                    'feedback': f'Selected wrong option. The correct answer is {correct_answer}.'
                }
                # Add resources for MCQ
                result['suggested_resources'] = self._get_resources_for_category(
                    question.get('category', 'General'), setup_data
                )
        else:
            # Use AI to evaluate short answers with detailed analysis
            evaluation_result = self._evaluate_short_answer_detailed(
                question, user_answer, setup_data
            )
            result.update(evaluation_result)
        
        return result
    
    def _evaluate_short_answer_detailed(self, question, user_answer, setup_data):
        """Evaluate short answer with detailed analysis using AI"""
        if not user_answer.strip():
            return {
                'score': 0,
                'feedback': "No answer provided.",
                'detailed_analysis': {
                    'clarity': {'score': 0, 'feedback': 'No answer to evaluate.'},
                    'correctness': {'score': 0, 'feedback': 'No answer to evaluate.'},
                    'completeness': {'score': 0, 'feedback': 'No answer to evaluate.'}
                },
                'suggested_resources': self._get_resources_for_category(
                    question.get('category', 'General'), setup_data
                )
            }
        
        interview_type = setup_data.get('interview_type', '').lower()
        
        if interview_type == 'behavioral':
            # Detailed evaluation for behavioral questions
            prompt = f"""
Evaluate this behavioral interview answer for a {setup_data['job_role']} position:

Question: {question['text']}
Answer: {user_answer}
Category: {question.get('category', 'General')}

Provide detailed analysis in these areas:

1. CLARITY (0-10): How clearly is the answer communicated?
   - Is the language clear and professional?
   - Is the structure logical and easy to follow?
   - Are the examples specific and well-explained?

2. CORRECTNESS (0-10): How accurate and relevant is the content?
   - Does the answer address the question asked?
   - Are the examples relevant to the behavioral competency?
   - Does it demonstrate the required skills/behavior?

3. COMPLETENESS (0-10): How comprehensive is the answer?
   - Does it follow the STAR method (Situation, Task, Action, Result)?
   - Are all aspects of the question addressed?
   - Does it show learning and self-reflection?

4. OVERALL SCORE (0-10): Overall quality of the answer

5. SUGGESTED RESOURCES: Learning materials to improve in this area

Format your response EXACTLY as:
CLARITY_SCORE: [0-10]
CLARITY_FEEDBACK: [Detailed feedback on communication clarity]

CORRECTNESS_SCORE: [0-10] 
CORRECTNESS_FEEDBACK: [Detailed feedback on relevance and accuracy]

COMPLETENESS_SCORE: [0-10]
COMPLETENESS_FEEDBACK: [Detailed feedback on comprehensiveness and STAR structure]

OVERALL_SCORE: [0-10]
OVERALL_FEEDBACK: [Comprehensive feedback summary]

SUGGESTED_RESOURCES: [Comma-separated list of 3-4 specific learning resources]
            """
        else:
            # Detailed evaluation for technical questions
            prompt = f"""
Evaluate this technical interview answer for a {setup_data['job_role']} position:

Question: {question['text']}
Answer: {user_answer}
Category: {question.get('category', 'General')}
Domain: {setup_data.get('domain', '')}

Provide detailed analysis in these areas:

1. CLARITY (0-10): How clearly is the technical concept explained?
   - Is the explanation easy to understand?
   - Are technical terms used appropriately?
   - Is the structure logical?

2. CORRECTNESS (0-10): How technically accurate is the answer?
   - Are the technical facts correct?
   - Are the concepts properly understood?
   - Are there any technical errors?

3. COMPLETENESS (0-10): How comprehensive is the answer?
   - Are all aspects of the question addressed?
   - Are examples or use cases provided?
   - Is sufficient technical depth shown?

4. OVERALL SCORE (0-10): Overall quality of the technical answer

5. SUGGESTED RESOURCES: Learning materials to improve in this technical area

Format your response EXACTLY as:
CLARITY_SCORE: [0-10]
CLARITY_FEEDBACK: [Detailed feedback on explanation clarity]

CORRECTNESS_SCORE: [0-10]
CORRECTNESS_FEEDBACK: [Detailed feedback on technical accuracy]

COMPLETENESS_SCORE: [0-10]
COMPLETENESS_FEEDBACK: [Detailed feedback on comprehensiveness]

OVERALL_SCORE: [0-10]
OVERALL_FEEDBACK: [Comprehensive technical feedback summary]

SUGGESTED_RESOURCES: [Comma-separated list of 3-4 specific learning resources]
            """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Parse the structured response
            return self._parse_detailed_evaluation(response_text)
        except Exception as e:
            # Fallback evaluation
            return self._fallback_detailed_evaluation(user_answer, question, setup_data)
    
    def _parse_detailed_evaluation(self, response_text):
        """Parse AI response into structured evaluation"""
        try:
            # Extract scores and feedback
            clarity_score = int(re.search(r'CLARITY_SCORE:\s*(\d+)', response_text).group(1))
            clarity_feedback = re.search(r'CLARITY_FEEDBACK:\s*(.*?)(?=\n\w+_SCORE:|$)', response_text, re.DOTALL).group(1).strip()
            
            correctness_score = int(re.search(r'CORRECTNESS_SCORE:\s*(\d+)', response_text).group(1))
            correctness_feedback = re.search(r'CORRECTNESS_FEEDBACK:\s*(.*?)(?=\n\w+_SCORE:|$)', response_text, re.DOTALL).group(1).strip()
            
            completeness_score = int(re.search(r'COMPLETENESS_SCORE:\s*(\d+)', response_text).group(1))
            completeness_feedback = re.search(r'COMPLETENESS_FEEDBACK:\s*(.*?)(?=\n\w+_SCORE:|$)', response_text, re.DOTALL).group(1).strip()
            
            overall_score = int(re.search(r'OVERALL_SCORE:\s*(\d+)', response_text).group(1))
            overall_feedback = re.search(r'OVERALL_FEEDBACK:\s*(.*?)(?=\nSUGGESTED_RESOURCES:|$)', response_text, re.DOTALL).group(1).strip()
            
            resources_text = re.search(r'SUGGESTED_RESOURCES:\s*(.*?)$', response_text, re.DOTALL).group(1).strip()
            # Clean up the resources text and split properly
            resources_text = re.sub(r'\d+\.\s*', '', resources_text)  # Remove numbering
            suggested_resources = [r.strip() for r in resources_text.split(',') if r.strip() and len(r.strip()) > 10]
            
            return {
                'score': min(overall_score, Config.SHORT_ANSWER_MAX_SCORE),
                'feedback': overall_feedback,
                'detailed_analysis': {
                    'clarity': {'score': clarity_score, 'feedback': clarity_feedback},
                    'correctness': {'score': correctness_score, 'feedback': correctness_feedback},
                    'completeness': {'score': completeness_score, 'feedback': completeness_feedback}
                },
                'suggested_resources': suggested_resources[:4]  # Limit to 4 resources
            }
        except Exception as e:
            # Fallback if parsing fails
            return {
                'score': 5,
                'feedback': response_text[:500] + "..." if len(response_text) > 500 else response_text,
                'detailed_analysis': {
                    'clarity': {'score': 5, 'feedback': 'Moderate clarity in explanation.'},
                    'correctness': {'score': 5, 'feedback': 'Generally accurate content.'},
                    'completeness': {'score': 5, 'feedback': 'Adequately comprehensive answer.'}
                },
                'suggested_resources': ['Study materials for improvement']
            }
    
    def _fallback_detailed_evaluation(self, user_answer, question, setup_data):
        """Fallback evaluation when AI fails"""
        answer_length = len(user_answer.strip())
        
        if answer_length < 20:
            return {
                'score': 2,
                'feedback': "Answer is too brief. Provide more detailed explanation.",
                'detailed_analysis': {
                    'clarity': {'score': 3, 'feedback': 'Answer is too short to assess clarity properly.'},
                    'correctness': {'score': 2, 'feedback': 'Insufficient content to evaluate accuracy.'},
                    'completeness': {'score': 1, 'feedback': 'Answer lacks sufficient detail and examples.'}
                },
                'suggested_resources': self._get_resources_for_category(
                    question.get('category', 'General'), setup_data
                )
            }
        elif answer_length < 100:
            return {
                'score': 5,
                'feedback': "Good start, but could be more comprehensive.",
                'detailed_analysis': {
                    'clarity': {'score': 6, 'feedback': 'Clear but could be more detailed.'},
                    'correctness': {'score': 5, 'feedback': 'Generally on track but needs more depth.'},
                    'completeness': {'score': 4, 'feedback': 'Missing important details and examples.'}
                },
                'suggested_resources': self._get_resources_for_category(
                    question.get('category', 'General'), setup_data
                )
            }
        else:
            return {
                'score': 7,
                'feedback': "Good detailed answer with room for improvement.",
                'detailed_analysis': {
                    'clarity': {'score': 7, 'feedback': 'Well-structured and clear explanation.'},
                    'correctness': {'score': 7, 'feedback': 'Demonstrates good understanding.'},
                    'completeness': {'score': 6, 'feedback': 'Comprehensive with minor gaps.'}
                },
                'suggested_resources': self._get_resources_for_category(
                    question.get('category', 'General'), setup_data
                )
            }
    
    def _get_resources_for_category(self, category, setup_data):
        """Get suggested learning resources based on category and setup"""
        interview_type = setup_data.get('interview_type', '').lower()
        domain = setup_data.get('domain', '').lower()
        
        resources = []
        
        if interview_type == 'behavioral':
            behavioral_resources = {
                'leadership': [
                    "Book: 'The Leadership Challenge' by Kouzes and Posner",
                    "Course: Leadership Fundamentals on LinkedIn Learning",
                    "Article: Harvard Business Review's Leadership section",
                    "Podcast: 'Leadership in Action' by McKinsey"
                ],
                'teamwork': [
                    "Book: 'Team of Teams' by General Stanley McChrystal",
                    "Course: Teamwork Skills on Coursera",
                    "Article: 'The Five Dysfunctions of a Team' summary",
                    "Workshop: Virtual team collaboration best practices"
                ],
                'communication': [
                    "Book: 'Crucial Conversations' by Kerry Patterson",
                    "Course: Business Communication on edX",
                    "Practice: Toastmasters International public speaking",
                    "Guide: STAR method interview technique training"
                ],
                'conflict resolution': [
                    "Book: 'Getting to Yes' by Roger Fisher",
                    "Course: Conflict Resolution Skills on Udemy",
                    "Article: Harvard Negotiation Project resources",
                    "Practice: Mediation and negotiation simulations"
                ],
                'problem solving': [
                    "Book: 'Thinking, Fast and Slow' by Daniel Kahneman",
                    "Course: Critical Thinking and Problem Solving on Coursera",
                    "Method: Design thinking methodology training",
                    "Practice: Case study analysis and frameworks"
                ]
            }
            
            category_key = category.lower().replace(' ', '_')
            resources = behavioral_resources.get(category_key, [
                "Book: 'Emotional Intelligence 2.0' by Travis Bradberry",
                "Course: Professional Skills Development on LinkedIn Learning",
                "Practice: STAR method behavioral interview preparation",
                "Resource: Indeed Career Guide for behavioral interviews"
            ])
        else:
            # Technical resources
            technical_resources = {
                'algorithms': [
                    "Platform: LeetCode for coding practice",
                    "Book: 'Cracking the Coding Interview' by Gayle McDowell",
                    "Course: Algorithms Specialization on Coursera",
                    "Resource: GeeksforGeeks algorithm tutorials"
                ],
                'data structures': [
                    "Course: Data Structures and Algorithms on edX",
                    "Book: 'Introduction to Algorithms' by CLRS",
                    "Practice: HackerRank data structures challenges",
                    "Visualization: VisuAlgo.net for interactive learning"
                ],
                'system design': [
                    "Book: 'Designing Data-Intensive Applications' by Martin Kleppmann",
                    "Course: System Design Interview prep on Educative",
                    "Resource: High Scalability blog and case studies",
                    "Practice: System design interview questions on Pramp"
                ],
                'python': [
                    "Documentation: Official Python documentation and tutorials",
                    "Book: 'Effective Python' by Brett Slatkin",
                    "Course: Python for Everybody Specialization on Coursera",
                    "Practice: Real Python tutorials and exercises"
                ],
                'javascript': [
                    "Resource: MDN Web Docs JavaScript Guide",
                    "Book: 'You Don\'t Know JS' series by Kyle Simpson",
                    "Course: Modern JavaScript from Beginner to Advanced",
                    "Practice: JavaScript30 challenge by Wes Bos"
                ],
                'machine learning': [
                    "Course: Machine Learning by Andrew Ng on Coursera",
                    "Book: 'Hands-On Machine Learning' by Aurélien Géron",
                    "Platform: Kaggle Learn micro-courses",
                    "Practice: Scikit-learn tutorials and examples"
                ]
            }
            
            category_key = category.lower().replace(' ', '_')
            if category_key in technical_resources:
                resources = technical_resources[category_key]
            elif domain in technical_resources:
                resources = technical_resources[domain]
            else:
                resources = [
                    f"Documentation: Official {domain} documentation",
                    f"Course: {category} fundamentals on online learning platforms",
                    f"Practice: {category} coding challenges and exercises",
                    f"Community: Join {domain} developer communities and forums"
                ]
        
        return resources[:4]  # Return maximum 4 resources
    
    def _fallback_short_answer_score(self, answer):
        """Fallback scoring for short answers"""
        if len(answer.strip()) < 20:
            return 3, "Answer is too brief. Provide more detailed explanation."
        elif len(answer.strip()) < 50:
            return 6, "Good start, but could be more comprehensive."
        else:
            return 8, "Good detailed answer!"
    
    def _analyze_performance(self, category_scores):
        """Analyze performance to identify strengths and weaknesses"""
        strengths = []
        weaknesses = []
        
        for category, score in category_scores.items():
            if score >= 8:
                strengths.append(f"Strong in {category}")
            elif score < 6:
                weaknesses.append(f"Need improvement in {category}")
        
        return strengths, weaknesses
    
    def _generate_recommendations(self, weaknesses, setup_data):
        """Generate recommendations based on weaknesses"""
        recommendations = []
        interview_type = setup_data.get('interview_type', '').lower()
        
        for weakness in weaknesses:
            # Behavioral-specific recommendations
            if interview_type == 'behavioral' or any(term in weakness.lower() for term in ['leadership', 'teamwork', 'communication', 'conflict', 'adaptability']):
                if "leadership" in weakness.lower():
                    recommendations.append("Practice STAR method examples demonstrating leadership initiatives and team management")
                elif "teamwork" in weakness.lower():
                    recommendations.append("Prepare examples of successful collaboration and team conflict resolution")
                elif "communication" in weakness.lower():
                    recommendations.append("Practice explaining complex ideas clearly and concisely using the STAR framework")
                elif "conflict" in weakness.lower():
                    recommendations.append("Develop examples showing diplomatic problem-solving and stakeholder management")
                elif "adaptability" in weakness.lower():
                    recommendations.append("Prepare stories showing flexibility, learning agility, and change management")
                elif "problem solving" in weakness.lower():
                    recommendations.append("Practice structuring problem-solving examples with clear situation, actions, and results")
                elif "initiative" in weakness.lower():
                    recommendations.append("Develop examples of proactive problem identification and innovative solutions")
                else:
                    recommendations.append("Practice behavioral interview techniques using the STAR method (Situation, Task, Action, Result)")
            # Technical-specific recommendations
            elif "algorithms" in weakness.lower():
                recommendations.append("Practice coding problems on platforms like LeetCode or HackerRank")
            elif "system design" in weakness.lower():
                recommendations.append("Study system design patterns and practice designing scalable systems")
            elif "machine learning" in weakness.lower():
                recommendations.append("Review ML fundamentals and practice with datasets on Kaggle")
            elif "javascript" in weakness.lower():
                recommendations.append("Practice JavaScript concepts and modern ES6+ features")
            elif "python" in weakness.lower():
                recommendations.append("Strengthen Python programming skills with real-world projects")
            elif "database" in weakness.lower() or "sql" in weakness.lower():
                recommendations.append("Practice SQL queries and database design concepts")
            elif "api" in weakness.lower():
                recommendations.append("Learn about REST API design and implementation best practices")
            else:
                recommendations.append(f"Focus on improving your knowledge in {weakness.split()[-1] if weakness.split() else 'core concepts'}")
        
        if not recommendations:
            if interview_type == 'behavioral':
                recommendations.append("Continue practicing behavioral examples using the STAR method!")
                recommendations.append("Develop more diverse examples covering different competency areas")
            else:
                recommendations.append("Continue practicing to maintain your strong performance!")
                recommendations.append("Try challenging yourself with harder difficulty levels")
        
        # Add general recommendations based on setup
        job_role = setup_data.get('job_role', '')
        if 'engineer' in job_role.lower():
            if interview_type == 'behavioral':
                recommendations.append("Practice explaining technical decisions in business context")
            else:
                recommendations.append("Practice explaining technical concepts in simple terms")
        if 'manager' in job_role.lower():
            recommendations.append("Focus on leadership and project management scenarios")
        
        return recommendations[:4]  # Limit to 4 recommendations
