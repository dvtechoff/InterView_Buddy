// Interview functionality for InterviewBuddy

class InterviewManager {
    constructor() {
        this.listenersInitialized = false;
        this.currentQuestion = 0;
        this.totalQuestions = 0;
        this.questions = [];
        this.answers = {};
        this.startTime = null;
        this.questionStartTime = null;
        this.questionTimes = [];
        this.timer = null;
        this.autoSaveTimer = null;
        this.isNavigating = false; // Flag to track internal navigation
    }
    
    init(config) {
        this.totalQuestions = config.totalQuestions || 0;
        this.currentQuestion = config.currentQuestion || 0;
        this.questions = config.questions || [];
        
        // Check if this is a new interview by comparing question count or first question text
        const isNewInterview = this.isNewInterview(config);
        const headerSubmitBtn = document.getElementById('headerSubmitBtn');

        if (headerSubmitBtn) {
            headerSubmitBtn.addEventListener('click', () => this.showSubmitModal());
        }

        
        if (isNewInterview) {
            // Clear all previous interview data for new interview
            this.clearPreviousInterviewData();
        }
        
        // Restore timer state from localStorage or start new
        const savedStartTime = localStorage.getItem('interview_start_time');
        if (savedStartTime && !isNewInterview) {
            this.startTime = parseInt(savedStartTime);
        } else {
            this.startTime = Date.now();
            localStorage.setItem('interview_start_time', this.startTime.toString());
        }
        
        this.questionStartTime = Date.now();
        
        this.initializeEventListeners();
        this.bindDynamicInputs(); // Fix: Bind input listeners for first question
        this.startTimer();
        
        if (!isNewInterview) {
            this.loadSavedAnswers();
        }
        
        this.displayCurrentAnswer(); // Fix: Display saved answer for first question
        this.updateStats();
        this.setupAutoSave();
        
        console.log('Interview Manager initialized', config, 'New interview:', isNewInterview);
    }
    
    isNewInterview(config) {
        // Check if this is a new interview vs resuming existing one
        const lastInterviewId = localStorage.getItem('current_interview_id');
        const currentInterviewId = config.interviewId || 'unknown';
        
        // Also check if the first question is different (backup check)
        const lastFirstQuestion = localStorage.getItem('first_question_text');
        const currentFirstQuestion = config.questions && config.questions[0] ? config.questions[0].text : '';
        
        return lastInterviewId !== currentInterviewId || lastFirstQuestion !== currentFirstQuestion;
    }
    
    clearPreviousInterviewData() {
        // Clear all interview-related localStorage data
        localStorage.removeItem('interview_answers');
        localStorage.removeItem('interview_start_time');
        localStorage.removeItem('current_interview_id');
        localStorage.removeItem('first_question_text');
        
        // Store current interview identifiers
        const currentInterviewId = Date.now().toString(); // Simple unique ID
        const firstQuestionText = this.questions[0] ? this.questions[0].text : '';
        
        localStorage.setItem('current_interview_id', currentInterviewId);
        localStorage.setItem('first_question_text', firstQuestionText);
        
        // Reset answers object
        this.answers = {};
        
        console.log('Cleared previous interview data for new interview');
    }
    initializeEventListeners() {
        if (this.listenersInitialized) return; // Skip if already initialized
            this.listenersInitialized = true;
        // Navigation buttons
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const submitBtn = document.getElementById('submitBtn');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.previousQuestion());
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextQuestion());
        }
        
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.showSubmitModal());
        }
        
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'ArrowLeft':
                        e.preventDefault();
                        this.previousQuestion();
                        break;
                    case 'ArrowRight':
                        e.preventDefault();
                        this.nextQuestion();
                        break;
                    case 'Enter':
                        if (e.shiftKey) {
                            e.preventDefault();
                            this.submitInterview();
                        }
                        break;
                }
            }
        });

        // Submit confirmation
        const confirmSubmit = document.getElementById('confirmSubmit');
        if (confirmSubmit) {
            confirmSubmit.addEventListener('click', () => this.submitInterview());
        }
        
        // Prevent accidental page reload - but not for internal navigation
        this.beforeUnloadHandler = (e) => {
            // Only show warning if user is actually leaving the page, not navigating questions
            if (!this.isNavigating) {
                e.preventDefault();
                e.returnValue = 'Your interview progress will be lost. Are you sure you want to leave?';
                return e.returnValue;
            }
        };
        window.addEventListener('beforeunload', this.beforeUnloadHandler);
    }

    bindDynamicInputs(){
        // Question navigation buttons
        document.querySelectorAll('.question-nav-btn').forEach(btn => {
            // Remove existing listeners to prevent duplicates
            btn.replaceWith(btn.cloneNode(true));
        });
        
        // Re-add listeners to cloned elements
        document.querySelectorAll('.question-nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const questionIndex = parseInt(e.target.dataset.question);
                this.goToQuestion(questionIndex);
            });
        });
        
        // Answer inputs - remove and re-add listeners to prevent duplicates
        document.querySelectorAll('input[name="answer"]').forEach(input => {
            // Clone to remove existing listeners
            const newInput = input.cloneNode(true);
            input.parentNode.replaceChild(newInput, input);
            
            // Add fresh listener
            newInput.addEventListener('change', () => this.saveCurrentAnswer());
        });
        
        const answerTextarea = document.getElementById('answerTextarea');
        if (answerTextarea) {
            // Clone to remove existing listeners
            const newTextarea = answerTextarea.cloneNode(true);
            answerTextarea.parentNode.replaceChild(newTextarea, answerTextarea);
            
            // Add fresh listener
            newTextarea.addEventListener('input', () => {
                this.debouncedSave();
            });
        }
        
        // MCQ options click handling - remove and re-add listeners
        document.querySelectorAll('.mcq-option').forEach(option => {
            // Clone to remove existing listeners
            const newOption = option.cloneNode(true);
            option.parentNode.replaceChild(newOption, option);
        });
        
        // Re-add listeners to cloned MCQ options
        document.querySelectorAll('.mcq-option').forEach(option => {
            option.addEventListener('click', (e) => {
                if (e.target.type !== 'radio') {
                    const radio = option.querySelector('input[type="radio"]');
                    if (radio) {
                        radio.checked = true;
                        this.selectMCQOption(option);
                        this.saveCurrentAnswer();
                    }
                }
            });
        });
        

    }
    
    startTimer() {
        this.timer = setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            const timerDisplay = document.getElementById('timerDisplay');
            if (timerDisplay) {
                timerDisplay.textContent = this.formatTime(Math.floor(elapsed / 1000));
            }
        }, 1000);
    }
    
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    loadSavedAnswers() {
        // Load any previously saved answers
        const saved = InterviewBuddy.loadFromLocalStorage('interview_answers', {});
        this.answers = saved;
        
        // Restore current answer display
        this.displayCurrentAnswer();
    }
    
    displayCurrentAnswer() {
        const currentQ = this.questions[this.currentQuestion];
        if (!currentQ) return;
        
        const savedAnswer = this.answers[this.currentQuestion];
        if (!savedAnswer) return;
        
        if (currentQ.type === 'mcq') {
            const radio = document.querySelector(`input[name="answer"][value="${savedAnswer}"]`);
            if (radio) {
                radio.checked = true;
                this.selectMCQOption(radio.closest('.mcq-option'));
            }
        } else {
            const textarea = document.getElementById('answerTextarea');
            if (textarea) {
                textarea.value = savedAnswer;
            }
        }
    }
    
    selectMCQOption(option) {
        // Remove selection from all options
        document.querySelectorAll('.mcq-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        
        // Add selection to clicked option
        option.classList.add('selected');
    }
    
    saveCurrentAnswer(silent = false) {
        const currentQ = this.questions[this.currentQuestion];
        if (!currentQ) return;
        
        let answer = '';
        
        if (currentQ.type === 'mcq') {
            const selected = document.querySelector('input[name="answer"]:checked');
            answer = selected ? selected.value : '';
        } else {
            const textarea = document.getElementById('answerTextarea');
            answer = textarea ? textarea.value.trim() : '';
        }
        
        if (answer) {
            this.answers[this.currentQuestion] = answer;
                        
            // Save locally as backup
            InterviewBuddy.saveToLocalStorage('interview_answers', this.answers);

            if (!silent) {
                this.submitAnswer(this.currentQuestion, answer);
            }
            
            // Update save status
            this.showSaveStatus('saved');
        }
        
        this.updateStats();
        this.updateNavigationButtons();
    }
    
    setupAutoSave() {
        this.debouncedSave = InterviewBuddy.debounce(() => {
            this.saveCurrentAnswer(true);
        }, 1500);
    }
    
    showSaveStatus(status) {
        const saveStatus = document.getElementById('saveStatus');
        if (!saveStatus) return;
        
        switch (status) {
            case 'saving':
                saveStatus.innerHTML = '<i class="fas fa-spinner fa-spin text-warning me-1"></i>Saving...';
                break;
            case 'saved':
                saveStatus.innerHTML = '<i class="fas fa-check-circle text-success me-1"></i>Answer saved';
                break;
            case 'error':
                saveStatus.innerHTML = '<i class="fas fa-exclamation-triangle text-danger me-1"></i>Save failed';
                break;
        }
    }
    
    async submitAnswer(questionIndex, answer) {
        this.showSaveStatus('saving');
        
        try {
            const response = await fetch('/submit_answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question_index: questionIndex,
                    answer: answer
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSaveStatus('saved');
            } else {
                this.showSaveStatus('error');
            }
        } catch (error) {
            console.error('Error saving answer:', error);
            this.showSaveStatus('error');
        }
    }
    
    nextQuestion() {
        if (this.currentQuestion < this.totalQuestions - 1) {
            this.recordQuestionTime();
            this.navigateToQuestion(this.currentQuestion + 1);
        }
    }
    
    previousQuestion() {
        if (this.currentQuestion > 0) {
            this.recordQuestionTime();
            this.navigateToQuestion(this.currentQuestion - 1);
        }
    }
    
    goToQuestion(questionIndex) {
        if (questionIndex >= 0 && questionIndex < this.totalQuestions && questionIndex !== this.currentQuestion) {
            this.recordQuestionTime();
            this.navigateToQuestion(questionIndex);
        }
    }
    
    async navigateToQuestion(questionIndex) {
        // Set navigation flag to prevent beforeunload warning
        this.isNavigating = true;
        
        try {            
            // Update server with new current question
            const response = await fetch('/update_current_question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    current_question: questionIndex
                })
            });
            
            if (response.ok) {
                // Update current question locally
                this.currentQuestion = questionIndex;
                this.questionStartTime = Date.now();
                
                // Update the URL without page reload
                const newUrl = `${window.location.pathname}?q=${questionIndex}`;
                window.history.pushState({questionIndex}, '', newUrl);
                
                // Update the UI to show new question
                this.updateQuestionDisplay();
                this.updateNavigationButtons();
                this.updateStats();
                this.loadCurrentAnswer();
                
            } else {
                console.error('Failed to update current question on server');
                InterviewBuddy.showAlert('Failed to navigate to question', 'error');
            }
        } catch (error) {
            console.error('Navigation error:', error);
            InterviewBuddy.showAlert('Navigation error occurred', 'error');
        } finally {
            // Reset navigation flag
            this.isNavigating = false;
        }
    }
    

    updateQuestionDisplay() {
    const currentQ = this.questions[this.currentQuestion];
    if (!currentQ) return;

    // Update question counter in header
    const questionCounter = document.querySelector('.text-muted');
    if (questionCounter && questionCounter.textContent.includes('Question')) {
        questionCounter.textContent = `Question ${this.currentQuestion + 1} of this.totalQuestions`;
    }

    // Update progress text
    const progressText = document.getElementById('progressText');
    if (progressText) {
        progressText.textContent = `${this.currentQuestion + 1}/${this.totalQuestions}`;
    }

    // Update progress bar
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        const progress = ((this.currentQuestion + 1) / this.totalQuestions) * 100;
        progressBar.style.width = `${progress}%`;
    }

    // --- Render Question Dynamically ---
    const questionCard = document.getElementById('questionCard');
    if (questionCard) {
        questionCard.innerHTML = `
            <div class="card-body p-4">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div class="question-number">${this.currentQuestion + 1}</div>
                    <span class="badge bg-primary">${currentQ.category || 'General'}</span>
                </div>
                <div class="question-text mb-4">
                    <h5 class="fw-semibold">${currentQ.text}</h5>
                    ${currentQ.difficulty ? `<small class="text-muted"><i class="fas fa-layer-group me-1"></i>Difficulty: ${currentQ.difficulty}</small>` : ''}
                </div>
                <div class="answer-area" id="answerArea">
                    ${currentQ.type === 'mcq' ? this.renderMCQOptions(currentQ) : this.renderTextarea()}
                </div>
                <div class="mt-3">
                    <small class="text-muted" id="saveStatus">
                        <i class="fas fa-check-circle text-success me-1"></i>
                        Answer auto-saved
                    </small>
                </div>
            </div>
        `;
    }

    // Re-bind listeners for new inputs
    this.initializeEventListeners();

    // Restore saved answer (if any)
    this.bindDynamicInputs();
    this.displayCurrentAnswer();
}

renderMCQOptions(question) {
    return `
        <div class="mcq-options">
            ${question.options.map(opt => `
                <div class="mcq-option" data-value="${opt[0]}">
                    <input type="radio" name="answer" value="${opt[0]}" id="option${opt[0]}" class="me-2">
                    <label for="option${opt[0]}" class="mb-0">${opt}</label>
                </div>
            `).join('')}
        </div>
    `;
}

renderTextarea() {
    return `
        <div class="short-answer">
            <textarea class="form-control answer-textarea" placeholder="Type your answer here..." rows="6" id="answerTextarea"></textarea>
            <small class="form-text text-muted mt-2">
                <i class="fas fa-lightbulb me-1"></i>
                Provide detailed explanations and examples where possible
            </small>
        </div>
    `;
}


    
    updateNavigationButtons() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        
        if (prevBtn) {
            prevBtn.disabled = this.currentQuestion === 0;
        }
        
        if (nextBtn) {
            nextBtn.disabled = this.currentQuestion >= this.totalQuestions - 1;
        }
    }
    
    loadCurrentAnswer() {
        // Load the saved answer for current question
        const savedAnswer = this.answers[this.currentQuestion];
        if (!savedAnswer) return;
        
        const currentQuestion = this.questions[this.currentQuestion];
        if (!currentQuestion) return;
        
        if (currentQuestion.type === 'mcq') {
            const radio = document.querySelector(`input[name="answer"][value="${savedAnswer}"]`);
            if (radio) {
                radio.checked = true;
                this.selectMCQOption(radio.closest('.mcq-option'));
            }
        } else {
            const textarea = document.getElementById('answerTextarea');
            if (textarea) {
                textarea.value = savedAnswer;
            }
        }
    }
    
    recordQuestionTime() {
        if (this.questionStartTime) {
            const timeSpent = Date.now() - this.questionStartTime;
            this.questionTimes[this.currentQuestion] = timeSpent;
        }
    }
    
    updateStats() {
        const answeredCount = Object.keys(this.answers).length;
        const remainingCount = this.totalQuestions - answeredCount;
        
        // Update answered count
        const answeredElement = document.getElementById('answeredCount');
        if (answeredElement) {
            answeredElement.textContent = `${answeredCount}/${this.totalQuestions}`;
        }
        
        // Update remaining count
        const remainingElement = document.getElementById('remainingCount');
        if (remainingElement) {
            remainingElement.textContent = `${remainingCount}/${this.totalQuestions}`;
        }
        
        // Update average time
        if (this.questionTimes.length > 0) {
            const avgTime = this.questionTimes.reduce((a, b) => a + b, 0) / this.questionTimes.length;
            const avgElement = document.getElementById('avgTime');
            if (avgElement) {
                avgElement.textContent = this.formatTime(Math.floor(avgTime / 1000));
            }
        }
        
        // Update progress bar
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            const progress = ((this.currentQuestion + 1) / this.totalQuestions) * 100;
            progressBar.style.width = `${progress}%`;
        }
        
        // Update progress text
        const progressText = document.getElementById('progressText');
        if (progressText) {
            progressText.textContent = `${this.currentQuestion + 1}/${this.totalQuestions}`;
        }
        
        // Update navigation button states
        this.updateNavigationButtons();
        
        // Update question navigation grid
        this.updateQuestionGrid();
    }
    
    updateNavigationButtons() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        
        if (prevBtn) {
            prevBtn.disabled = this.currentQuestion === 0;
        }
        
        if (nextBtn) {
            nextBtn.disabled = this.currentQuestion === this.totalQuestions - 1;
        }
    }
    
    updateQuestionGrid() {
        document.querySelectorAll('.question-nav-btn').forEach((btn, index) => {
            btn.classList.remove('btn-primary', 'btn-outline-secondary', 'btn-success');
            
            if (index === this.currentQuestion) {
                btn.classList.add('btn-primary');
                btn.disabled = true;
            } else if (this.answers[index]) {
                btn.classList.add('btn-success');
                btn.disabled = false;
            } else {
                btn.classList.add('btn-outline-secondary');
                btn.disabled = false;
            }
        });
    }
    
    showSubmitModal() {
        const answeredCount = Object.keys(this.answers).length;
        
        // Update modal content
        const modalAnsweredCount = document.getElementById('modalAnsweredCount');
        if (modalAnsweredCount) {
            modalAnsweredCount.textContent = answeredCount;
        }
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('submitModal'));
        modal.show();
    }
    
    async submitInterview() {
        const submitBtn = document.getElementById('confirmSubmit');
        if (submitBtn) {
            InterviewBuddy.showLoading(submitBtn, 'Submitting...');
        }
        
        try {
            const response = await fetch('/complete_interview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Clear local storage and timer state
                InterviewBuddy.removeFromLocalStorage('interview_answers');
                localStorage.removeItem('interview_start_time');
                
                // Clear timer
                if (this.timer) {
                    clearInterval(this.timer);
                }
                
                // Remove beforeunload listener
                window.removeEventListener('beforeunload', this.beforeUnloadHandler);
                
                // Redirect to results
                InterviewBuddy.showAlert('Interview submitted successfully!', 'success');
                setTimeout(() => {
                    window.location.href = '/results';
                }, 1000);
            } else {
                throw new Error(result.error || 'Submission failed');
            }
        } catch (error) {
            console.error('Submission error:', error);
            InterviewBuddy.showAlert('Failed to submit interview. Please try again.', 'error');
            
            if (submitBtn) {
                InterviewBuddy.hideLoading(submitBtn);
            }
        }
    }
    
    // Cleanup method
    destroy() {
        if (this.timer) {
            clearInterval(this.timer);
        }
        
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        // Remove event listeners
        window.removeEventListener('beforeunload', this.beforeUnloadHandler);
    }
}


// Initialize global interview manager
window.InterviewManager = new InterviewManager();

// Auto-save on page unload
window.addEventListener('beforeunload', function() {
    if (window.InterviewManager) {
        window.InterviewManager.saveCurrentAnswer();
    }
});
