from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from courses.models import Course, Lesson
import uuid
import json


class Test(models.Model):
    """Main test/quiz model."""
    
    # Test types
    QUIZ = 'quiz'
    EXAM = 'exam'
    ASSIGNMENT = 'assignment'
    PRACTICE = 'practice'
    
    TEST_TYPES = [
        (QUIZ, 'Quiz'),
        (EXAM, 'Exam'),
        (ASSIGNMENT, 'Assignment'),
        (PRACTICE, 'Practice Test'),
    ]
    
    # Test status
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (ARCHIVED, 'Archived'),
    ]
    
    # Grading methods
    AUTO_GRADE = 'auto'
    MANUAL_GRADE = 'manual'
    MIXED_GRADE = 'mixed'
    
    GRADING_METHODS = [
        (AUTO_GRADE, 'Auto Grade'),
        (MANUAL_GRADE, 'Manual Grade'),
        (MIXED_GRADE, 'Mixed Grading'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Test metadata
    test_type = models.CharField(max_length=20, choices=TEST_TYPES, default=QUIZ)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='tests')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, blank=True, null=True, related_name='tests')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tests')
    
    # Timing and scheduling
    time_limit = models.PositiveIntegerField(
        help_text="Time limit in minutes (0 for no limit)",
        default=0
    )
    available_from = models.DateTimeField(blank=True, null=True)
    available_until = models.DateTimeField(blank=True, null=True)
    
    # Attempt settings
    max_attempts = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    allow_review = models.BooleanField(default=True)
    show_correct_answers = models.BooleanField(default=True)
    show_score_immediately = models.BooleanField(default=True)
    
    # Grading settings
    grading_method = models.CharField(max_length=20, choices=GRADING_METHODS, default=AUTO_GRADE)
    passing_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    total_points = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Question settings
    randomize_questions = models.BooleanField(default=False)
    randomize_answers = models.BooleanField(default=False)
    questions_per_page = models.PositiveIntegerField(default=1)
    
    # Access control
    require_password = models.BooleanField(default=False)
    access_password = models.CharField(max_length=50, blank=True, null=True)
    ip_restrictions = models.JSONField(default=list, blank=True)  # List of allowed IP ranges
    
    # Proctoring settings
    require_webcam = models.BooleanField(default=False)
    prevent_copy_paste = models.BooleanField(default=False)
    full_screen_mode = models.BooleanField(default=False)
    
    # Analytics
    total_attempts = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'tests_test'
        verbose_name = 'Test'
        verbose_name_plural = 'Tests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'status']),
            models.Index(fields=['instructor']),
            models.Index(fields=['available_from', 'available_until']),
        ]
    
    def __str__(self):
        return f"{self.course.course_code}: {self.title}"
    
    @property
    def is_available(self):
        """Check if test is currently available."""
        now = timezone.now()
        if self.available_from and now < self.available_from:
            return False
        if self.available_until and now > self.available_until:
            return False
        return self.status == self.PUBLISHED
    
    @property
    def has_time_limit(self):
        """Check if test has a time limit."""
        return self.time_limit > 0
    
    def calculate_total_points(self):
        """Calculate total points from all questions."""
        total = sum(question.points for question in self.questions.all())
        self.total_points = total
        self.save(update_fields=['total_points'])
        return total


class Question(models.Model):
    """Test questions model."""
    
    # Question types
    MULTIPLE_CHOICE = 'multiple_choice'
    TRUE_FALSE = 'true_false'
    SHORT_ANSWER = 'short_answer'
    ESSAY = 'essay'
    FILL_BLANK = 'fill_blank'
    MATCHING = 'matching'
    ORDERING = 'ordering'
    
    QUESTION_TYPES = [
        (MULTIPLE_CHOICE, 'Multiple Choice'),
        (TRUE_FALSE, 'True/False'),
        (SHORT_ANSWER, 'Short Answer'),
        (ESSAY, 'Essay'),
        (FILL_BLANK, 'Fill in the Blank'),
        (MATCHING, 'Matching'),
        (ORDERING, 'Ordering'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default=MULTIPLE_CHOICE)
    
    # Question settings
    order = models.PositiveIntegerField(default=0)
    points = models.DecimalField(max_digits=6, decimal_places=2, default=1.00)
    is_required = models.BooleanField(default=True)
    
    # Content and media
    image = models.ImageField(upload_to='tests/questions/%Y/%m/', blank=True, null=True)
    explanation = models.TextField(blank=True, null=True)
    
    # Auto-grading settings
    case_sensitive = models.BooleanField(default=False)
    partial_credit = models.BooleanField(default=False)
    
    # Question metadata
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        default='medium'
    )
    tags = models.JSONField(default=list, blank=True)  # List of tags for categorization
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tests_question'
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['test', 'order']
        indexes = [
            models.Index(fields=['test', 'order']),
        ]
    
    def __str__(self):
        return f"{self.test.title} - Q{self.order}: {self.question_text[:50]}..."


class Answer(models.Model):
    """Answer choices for questions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    # For partial credit
    points = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    # For matching questions
    match_text = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tests_answer'
        verbose_name = 'Answer'
        verbose_name_plural = 'Answers'
        ordering = ['question', 'order']
        indexes = [
            models.Index(fields=['question', 'order']),
        ]
    
    def __str__(self):
        return f"{self.question.question_text[:30]}... - {self.answer_text[:30]}..."


class TestAttempt(models.Model):
    """Student test attempts."""
    
    # Attempt status
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    SUBMITTED = 'submitted'
    GRADED = 'graded'
    EXPIRED = 'expired'
    
    STATUS_CHOICES = [
        (NOT_STARTED, 'Not Started'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (SUBMITTED, 'Submitted'),
        (GRADED, 'Graded'),
        (EXPIRED, 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    
    # Attempt details
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=NOT_STARTED)
    
    # Timing
    started_at = models.DateTimeField(blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    time_spent = models.PositiveIntegerField(default=0)  # Seconds
    expires_at = models.DateTimeField(blank=True, null=True)
    
    # Scoring
    score = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_passed = models.BooleanField(default=False)
    
    # Grading
    auto_graded = models.BooleanField(default=False)
    manually_graded = models.BooleanField(default=False)
    graded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='graded_attempts'
    )
    graded_at = models.DateTimeField(blank=True, null=True)
    
    # Security and proctoring
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    browser_events = models.JSONField(default=list, blank=True)  # Track tab switches, etc.
    
    # Feedback
    instructor_feedback = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tests_test_attempt'
        verbose_name = 'Test Attempt'
        verbose_name_plural = 'Test Attempts'
        unique_together = ['test', 'student', 'attempt_number']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['test', 'student']),
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
        ]
    
    def __str__(self):
        return f"{self.student.full_name} - {self.test.title} (Attempt {self.attempt_number})"
    
    @property
    def is_expired(self):
        """Check if attempt has expired."""
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False
    
    @property
    def time_remaining(self):
        """Calculate remaining time in seconds."""
        if not self.expires_at:
            return None
        remaining = (self.expires_at - timezone.now()).total_seconds()
        return max(0, int(remaining))
    
    def calculate_score(self):
        """Calculate the total score for this attempt."""
        total_score = 0
        total_possible = 0
        
        for response in self.responses.all():
            total_score += response.points_earned
            total_possible += response.question.points
        
        self.score = total_score
        if total_possible > 0:
            self.percentage = (total_score / total_possible) * 100
            self.is_passed = self.percentage >= self.test.passing_score
        
        self.save(update_fields=['score', 'percentage', 'is_passed'])
        return self.score


class QuestionResponse(models.Model):
    """Student responses to test questions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    
    # Response data
    selected_answers = models.ManyToManyField(Answer, blank=True, related_name='selected_in_responses')
    text_response = models.TextField(blank=True, null=True)  # For text-based questions
    file_response = models.FileField(upload_to='tests/responses/%Y/%m/', blank=True, null=True)
    
    # For complex question types
    response_data = models.JSONField(default=dict, blank=True)  # Store complex responses
    
    # Grading
    points_earned = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    is_correct = models.BooleanField(default=False)
    is_graded = models.BooleanField(default=False)
    
    # Feedback
    feedback = models.TextField(blank=True, null=True)
    
    # Timing
    time_spent = models.PositiveIntegerField(default=0)  # Seconds spent on this question
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tests_question_response'
        verbose_name = 'Question Response'
        verbose_name_plural = 'Question Responses'
        unique_together = ['attempt', 'question']
        indexes = [
            models.Index(fields=['attempt', 'question']),
        ]
    
    def __str__(self):
        return f"{self.attempt.student.full_name} - {self.question.question_text[:30]}..."
    
    def auto_grade(self):
        """Auto-grade the response based on question type."""
        if self.question.question_type == Question.MULTIPLE_CHOICE:
            correct_answers = self.question.answers.filter(is_correct=True)
            selected_answers = self.selected_answers.all()
            
            if set(correct_answers) == set(selected_answers):
                self.points_earned = self.question.points
                self.is_correct = True
            else:
                self.points_earned = 0
                self.is_correct = False
                
        elif self.question.question_type == Question.TRUE_FALSE:
            correct_answer = self.question.answers.filter(is_correct=True).first()
            selected_answer = self.selected_answers.first()
            
            if correct_answer == selected_answer:
                self.points_earned = self.question.points
                self.is_correct = True
            else:
                self.points_earned = 0
                self.is_correct = False
        
        # Add more auto-grading logic for other question types
        
        self.is_graded = True
        self.save(update_fields=['points_earned', 'is_correct', 'is_graded'])


class TestResult(models.Model):
    """Aggregated test results and analytics."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_results')
    
    # Best attempt data
    best_attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='best_results')
    best_score = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    best_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Overall statistics
    total_attempts = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    first_attempt_score = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Status
    is_passed = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    
    # Timing
    total_time_spent = models.PositiveIntegerField(default=0)  # Total seconds across all attempts
    first_completed_at = models.DateTimeField(blank=True, null=True)
    last_attempt_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tests_test_result'
        verbose_name = 'Test Result'
        verbose_name_plural = 'Test Results'
        unique_together = ['test', 'student']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['test', 'is_passed']),
            models.Index(fields=['student']),
        ]
    
    def __str__(self):
        return f"{self.student.full_name} - {self.test.title} Result"
    
    def update_from_attempts(self):
        """Update result data from all attempts."""
        attempts = self.test.attempts.filter(student=self.student, status=TestAttempt.GRADED)
        
        if attempts.exists():
            self.total_attempts = attempts.count()
            self.best_attempt = attempts.order_by('-score').first()
            self.best_score = self.best_attempt.score
            self.best_percentage = self.best_attempt.percentage
            self.average_score = attempts.aggregate(avg=models.Avg('score'))['avg'] or 0
            self.first_attempt_score = attempts.order_by('created_at').first().score
            self.is_passed = self.best_percentage >= self.test.passing_score
            self.is_completed = True
            self.total_time_spent = sum(attempt.time_spent for attempt in attempts)
            self.first_completed_at = attempts.order_by('created_at').first().submitted_at
            self.last_attempt_at = attempts.order_by('-created_at').first().submitted_at
            
            self.save()


class QuestionBank(models.Model):
    """Question bank for reusable questions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='question_banks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_banks')
    
    # Settings
    is_public = models.BooleanField(default=False)
    tags = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tests_question_bank'
        verbose_name = 'Question Bank'
        verbose_name_plural = 'Question Banks'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.course.course_code}: {self.name}"


class BankQuestion(models.Model):
    """Questions stored in question banks."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=Question.QUESTION_TYPES, default=Question.MULTIPLE_CHOICE)
    
    # Question settings
    points = models.DecimalField(max_digits=6, decimal_places=2, default=1.00)
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        default='medium'
    )
    
    # Content
    image = models.ImageField(upload_to='tests/bank_questions/%Y/%m/', blank=True, null=True)
    explanation = models.TextField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tests_bank_question'
        verbose_name = 'Bank Question'
        verbose_name_plural = 'Bank Questions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.bank.name} - {self.question_text[:50]}..."


class BankAnswer(models.Model):
    """Answer choices for bank questions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(BankQuestion, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    points = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tests_bank_answer'
        verbose_name = 'Bank Answer'
        verbose_name_plural = 'Bank Answers'
        ordering = ['question', 'order']
    
    def __str__(self):
        return f"{self.question.question_text[:30]}... - {self.answer_text[:30]}..."
