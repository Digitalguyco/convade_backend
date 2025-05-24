from django.db import models
from django.utils import timezone
from accounts.models import User
from courses.models import Course, Lesson, Enrollment
from tests.models import Test, TestAttempt
import uuid


class UserActivity(models.Model):
    """Track detailed user activities for analytics."""
    
    # Activity types
    LOGIN = 'login'
    LOGOUT = 'logout'
    COURSE_VIEW = 'course_view'
    LESSON_VIEW = 'lesson_view'
    LESSON_COMPLETE = 'lesson_complete'
    TEST_START = 'test_start'
    TEST_COMPLETE = 'test_complete'
    ENROLLMENT = 'enrollment'
    BADGE_EARNED = 'badge_earned'
    PROFILE_UPDATE = 'profile_update'
    DOWNLOAD = 'download'
    SEARCH = 'search'
    
    ACTIVITY_TYPES = [
        (LOGIN, 'Login'),
        (LOGOUT, 'Logout'),
        (COURSE_VIEW, 'Course View'),
        (LESSON_VIEW, 'Lesson View'),
        (LESSON_COMPLETE, 'Lesson Complete'),
        (TEST_START, 'Test Start'),
        (TEST_COMPLETE, 'Test Complete'),
        (ENROLLMENT, 'Enrollment'),
        (BADGE_EARNED, 'Badge Earned'),
        (PROFILE_UPDATE, 'Profile Update'),
        (DOWNLOAD, 'Download'),
        (SEARCH, 'Search'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    
    # Related objects
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, blank=True, null=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, blank=True, null=True)
    
    # Activity metadata
    duration = models.PositiveIntegerField(default=0)  # Duration in seconds
    metadata = models.JSONField(default=dict, blank=True)  # Additional activity data
    
    # Request context
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    referrer = models.URLField(blank=True, null=True)
    
    # Device and location
    device_type = models.CharField(max_length=50, blank=True, null=True)
    browser = models.CharField(max_length=100, blank=True, null=True)
    os = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_user_activity'
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'activity_type', 'timestamp']),
            models.Index(fields=['course', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_activity_type_display()} at {self.timestamp}"


class CourseAnalytics(models.Model):
    """Analytics data for courses."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='analytics')
    
    # Enrollment metrics
    total_enrollments = models.PositiveIntegerField(default=0)
    active_enrollments = models.PositiveIntegerField(default=0)
    completed_enrollments = models.PositiveIntegerField(default=0)
    dropped_enrollments = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    total_views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    average_session_duration = models.PositiveIntegerField(default=0)  # Seconds
    total_study_time = models.PositiveIntegerField(default=0)  # Total minutes
    
    # Completion metrics
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    average_completion_time = models.PositiveIntegerField(default=0)  # Days
    
    # Performance metrics
    average_test_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Lesson analytics
    most_viewed_lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, blank=True, null=True, related_name='most_viewed_in')
    most_difficult_lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, blank=True, null=True, related_name='most_difficult_in')
    
    # Rating and feedback
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_ratings = models.PositiveIntegerField(default=0)
    
    # Revenue (if paid course)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    
    # Trend data (JSON arrays for charts)
    enrollment_trend = models.JSONField(default=list, blank=True)
    completion_trend = models.JSONField(default=list, blank=True)
    engagement_trend = models.JSONField(default=list, blank=True)
    
    # Update tracking
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_course_analytics'
        verbose_name = 'Course Analytics'
        verbose_name_plural = 'Course Analytics'
    
    def __str__(self):
        return f"Analytics for {self.course.title}"


class TestAnalytics(models.Model):
    """Analytics data for tests."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.OneToOneField(Test, on_delete=models.CASCADE, related_name='analytics')
    
    # Attempt metrics
    total_attempts = models.PositiveIntegerField(default=0)
    unique_test_takers = models.PositiveIntegerField(default=0)
    completed_attempts = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    highest_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    lowest_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Timing metrics
    average_completion_time = models.PositiveIntegerField(default=0)  # Seconds
    fastest_completion = models.PositiveIntegerField(default=0)  # Seconds
    slowest_completion = models.PositiveIntegerField(default=0)  # Seconds
    
    # Question analytics
    most_difficult_question = models.JSONField(default=dict, blank=True)
    easiest_question = models.JSONField(default=dict, blank=True)
    question_statistics = models.JSONField(default=list, blank=True)  # Per-question stats
    
    # Distribution data
    score_distribution = models.JSONField(default=list, blank=True)  # Score ranges and counts
    time_distribution = models.JSONField(default=list, blank=True)  # Time ranges and counts
    
    # Trend data
    performance_trend = models.JSONField(default=list, blank=True)
    attempt_trend = models.JSONField(default=list, blank=True)
    
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_test_analytics'
        verbose_name = 'Test Analytics'
        verbose_name_plural = 'Test Analytics'
    
    def __str__(self):
        return f"Analytics for {self.test.title}"


class SystemMetrics(models.Model):
    """System-wide metrics and KPIs."""
    
    # Metric types
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'
    
    PERIOD_TYPES = [
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
        (YEARLY, 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # User metrics
    total_users = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    returning_users = models.PositiveIntegerField(default=0)
    
    # Content metrics
    total_courses = models.PositiveIntegerField(default=0)
    new_courses = models.PositiveIntegerField(default=0)
    total_lessons = models.PositiveIntegerField(default=0)
    total_tests = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    total_enrollments = models.PositiveIntegerField(default=0)
    course_completions = models.PositiveIntegerField(default=0)
    test_attempts = models.PositiveIntegerField(default=0)
    badges_awarded = models.PositiveIntegerField(default=0)
    
    # Learning metrics
    total_study_time = models.PositiveIntegerField(default=0)  # Minutes
    average_session_duration = models.PositiveIntegerField(default=0)  # Seconds
    content_consumption_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Performance metrics
    overall_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    average_test_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    user_satisfaction = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Revenue metrics (if applicable)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    new_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    average_revenue_per_user = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Technical metrics
    page_load_time = models.DecimalField(max_digits=6, decimal_places=3, default=0.000)  # Seconds
    error_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0000)  # Percentage
    uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_system_metrics'
        verbose_name = 'System Metrics'
        verbose_name_plural = 'System Metrics'
        ordering = ['-period_start']
        unique_together = ['period_type', 'period_start']
        indexes = [
            models.Index(fields=['period_type', 'period_start']),
        ]
    
    def __str__(self):
        return f"{self.get_period_type_display()} metrics for {self.period_start.date()}"


class LearningPath(models.Model):
    """Personalized learning paths for users."""
    
    # Path status
    ACTIVE = 'active'
    COMPLETED = 'completed'
    PAUSED = 'paused'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (COMPLETED, 'Completed'),
        (PAUSED, 'Paused'),
        (CANCELLED, 'Cancelled'),
    ]
    
    # Path types
    RECOMMENDED = 'recommended'
    CUSTOM = 'custom'
    PREREQUISITE = 'prerequisite'
    SKILL_BASED = 'skill_based'
    
    PATH_TYPES = [
        (RECOMMENDED, 'AI Recommended'),
        (CUSTOM, 'Custom Created'),
        (PREREQUISITE, 'Prerequisite Path'),
        (SKILL_BASED, 'Skill-Based'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_paths')
    
    # Path details
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    path_type = models.CharField(max_length=20, choices=PATH_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE)
    
    # Path content
    courses = models.ManyToManyField(Course, through='LearningPathItem', related_name='learning_paths')
    
    # Progress tracking
    total_courses = models.PositiveIntegerField(default=0)
    completed_courses = models.PositiveIntegerField(default=0)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Estimates
    estimated_duration = models.PositiveIntegerField(default=0)  # Hours
    estimated_completion_date = models.DateField(blank=True, null=True)
    
    # Tracking
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # AI/recommendation metadata
    recommendation_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    recommendation_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_learning_path'
        verbose_name = 'Learning Path'
        verbose_name_plural = 'Learning Paths'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.user.full_name}"


class LearningPathItem(models.Model):
    """Individual items in a learning path."""
    
    # Item status
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    SKIPPED = 'skipped'
    
    STATUS_CHOICES = [
        (NOT_STARTED, 'Not Started'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (SKIPPED, 'Skipped'),
    ]
    
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='items')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    # Ordering
    order = models.PositiveIntegerField()
    
    # Item status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=NOT_STARTED)
    
    # Tracking
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Requirements
    is_required = models.BooleanField(default=True)
    prerequisite_items = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    class Meta:
        db_table = 'analytics_learning_path_item'
        verbose_name = 'Learning Path Item'
        verbose_name_plural = 'Learning Path Items'
        ordering = ['learning_path', 'order']
        unique_together = ['learning_path', 'course']
    
    def __str__(self):
        return f"{self.learning_path.name} - {self.course.title} (#{self.order})"


class UserLearningAnalytics(models.Model):
    """Detailed learning analytics for individual users."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='learning_analytics')
    
    # Learning behavior
    preferred_learning_time = models.JSONField(default=dict, blank=True)  # Hour-wise activity
    learning_streak = models.PositiveIntegerField(default=0)  # Current streak in days
    longest_streak = models.PositiveIntegerField(default=0)  # Longest streak ever
    
    # Content consumption
    total_courses_enrolled = models.PositiveIntegerField(default=0)
    total_courses_completed = models.PositiveIntegerField(default=0)
    total_lessons_viewed = models.PositiveIntegerField(default=0)
    total_tests_taken = models.PositiveIntegerField(default=0)
    
    # Time tracking
    total_learning_time = models.PositiveIntegerField(default=0)  # Minutes
    average_session_duration = models.PositiveIntegerField(default=0)  # Minutes
    last_learning_session = models.DateTimeField(blank=True, null=True)
    
    # Performance metrics
    average_test_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    improvement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Engagement metrics
    login_frequency = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Logins per week
    content_interaction_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Learning style analysis
    learning_style_scores = models.JSONField(default=dict, blank=True)  # Visual, auditory, etc.
    preferred_content_types = models.JSONField(default=list, blank=True)  # Video, text, etc.
    
    # Skill development
    skill_levels = models.JSONField(default=dict, blank=True)  # Skill -> level mapping
    skill_progress = models.JSONField(default=dict, blank=True)  # Skill progress tracking
    
    # Predictions and recommendations
    dropout_risk_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    next_course_recommendations = models.JSONField(default=list, blank=True)
    optimal_learning_schedule = models.JSONField(default=dict, blank=True)
    
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_user_learning_analytics'
        verbose_name = 'User Learning Analytics'
        verbose_name_plural = 'User Learning Analytics'
    
    def __str__(self):
        return f"Learning Analytics for {self.user.full_name}"
