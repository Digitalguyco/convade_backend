from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User, School
import uuid


class Category(models.Model):
    """Course categories for organization."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # Font icon class
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class Course(models.Model):
    """Main course model."""
    
    # Course status choices
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (ARCHIVED, 'Archived'),
    ]
    
    # Difficulty levels
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    
    DIFFICULTY_CHOICES = [
        (BEGINNER, 'Beginner'),
        (INTERMEDIATE, 'Intermediate'),
        (ADVANCED, 'Advanced'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500)
    
    # Course metadata
    course_code = models.CharField(max_length=20, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_courses')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='courses')
    
    # Course content
    thumbnail = models.ImageField(upload_to='courses/thumbnails/%Y/%m/', blank=True, null=True)
    intro_video = models.FileField(upload_to='courses/videos/%Y/%m/', blank=True, null=True)
    syllabus = models.FileField(upload_to='courses/syllabi/%Y/%m/', blank=True, null=True)
    
    # Course settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=BEGINNER)
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Duration and scheduling
    estimated_duration = models.PositiveIntegerField(
        help_text="Estimated duration in hours",
        validators=[MinValueValidator(1), MaxValueValidator(1000)]
    )
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    enrollment_start = models.DateTimeField(blank=True, null=True)
    enrollment_end = models.DateTimeField(blank=True, null=True)
    
    # Capacity and enrollment
    max_students = models.PositiveIntegerField(default=100)
    allow_self_enrollment = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    
    # Course requirements
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    required_materials = models.TextField(blank=True, null=True)
    
    # Learning objectives
    learning_objectives = models.JSONField(default=list, blank=True)
    
    # Grading
    passing_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    certificate_enabled = models.BooleanField(default=True)
    
    # SEO and discoverability
    meta_keywords = models.CharField(max_length=500, blank=True, null=True)
    meta_description = models.CharField(max_length=160, blank=True, null=True)
    
    # Analytics and tracking
    view_count = models.PositiveIntegerField(default=0)
    enrollment_count = models.PositiveIntegerField(default=0)
    completion_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'courses_course'
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course_code']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['instructor']),
            models.Index(fields=['published_at']),
        ]
    
    def __str__(self):
        return f"{self.course_code}: {self.title}"
    
    @property
    def is_enrollment_open(self):
        """Check if enrollment is currently open."""
        now = timezone.now()
        if self.enrollment_start and now < self.enrollment_start:
            return False
        if self.enrollment_end and now > self.enrollment_end:
            return False
        return True
    
    @property
    def is_active(self):
        """Check if course is currently active."""
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return self.status == self.PUBLISHED
    
    @property
    def available_slots(self):
        """Calculate available enrollment slots."""
        return max(0, self.max_students - self.enrollment_count)
    
    @property
    def completion_rate(self):
        """Calculate course completion rate."""
        if self.enrollment_count == 0:
            return 0
        return round((self.completion_count / self.enrollment_count) * 100, 2)


class Module(models.Model):
    """Course modules/chapters."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Module ordering and structure
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    
    # Duration
    estimated_duration = models.PositiveIntegerField(
        help_text="Estimated duration in minutes",
        default=60
    )
    
    # Prerequisites
    unlock_after = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        help_text="Module that must be completed before this one"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_module'
        verbose_name = 'Module'
        verbose_name_plural = 'Modules'
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
        indexes = [
            models.Index(fields=['course', 'order']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - Module {self.order}: {self.title}"


class Lesson(models.Model):
    """Individual lessons within modules."""
    
    # Lesson types
    VIDEO = 'video'
    TEXT = 'text'
    QUIZ = 'quiz'
    ASSIGNMENT = 'assignment'
    DOWNLOAD = 'download'
    LIVE_SESSION = 'live_session'
    
    LESSON_TYPES = [
        (VIDEO, 'Video'),
        (TEXT, 'Text/Article'),
        (QUIZ, 'Quiz'),
        (ASSIGNMENT, 'Assignment'),
        (DOWNLOAD, 'Downloadable Resource'),
        (LIVE_SESSION, 'Live Session'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default=TEXT)
    
    # Content
    content = models.TextField(blank=True, null=True)  # For text lessons
    video_file = models.FileField(upload_to='courses/lessons/videos/%Y/%m/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)  # For external videos
    attachment = models.FileField(upload_to='courses/lessons/files/%Y/%m/', blank=True, null=True)
    
    # Lesson settings
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    is_free_preview = models.BooleanField(default=False)
    
    # Duration and timing
    duration = models.PositiveIntegerField(
        help_text="Duration in minutes",
        default=10
    )
    
    # Live session specific
    live_session_date = models.DateTimeField(blank=True, null=True)
    live_session_url = models.URLField(blank=True, null=True)
    
    # Tracking
    view_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_lesson'
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['module', 'order']
        unique_together = ['module', 'order']
        indexes = [
            models.Index(fields=['module', 'order']),
        ]
    
    def __str__(self):
        return f"{self.module.title} - Lesson {self.order}: {self.title}"


class Enrollment(models.Model):
    """Student enrollment in courses."""
    
    # Enrollment status
    PENDING = 'pending'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    DROPPED = 'dropped'
    SUSPENDED = 'suspended'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending Approval'),
        (ACTIVE, 'Active'),
        (COMPLETED, 'Completed'),
        (DROPPED, 'Dropped'),
        (SUSPENDED, 'Suspended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    
    # Enrollment details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(blank=True, null=True)
    
    # Progress tracking
    progress_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    last_accessed = models.DateTimeField(blank=True, null=True)
    
    # Grading
    current_grade = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    final_grade = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Time tracking
    total_study_time = models.PositiveIntegerField(default=0)  # Minutes
    
    # Certificate
    certificate_issued = models.BooleanField(default=False)
    certificate_date = models.DateTimeField(blank=True, null=True)
    
    # Payment (if applicable)
    payment_completed = models.BooleanField(default=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_enrollment'
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        unique_together = ['student', 'course']
        ordering = ['-enrollment_date']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['enrollment_date']),
        ]
    
    def __str__(self):
        return f"{self.student.full_name} enrolled in {self.course.title}"
    
    @property
    def is_passed(self):
        """Check if student has passed the course."""
        return self.final_grade and self.final_grade >= self.course.passing_score


class LessonProgress(models.Model):
    """Track student progress through individual lessons."""
    
    # Completion status
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (NOT_STARTED, 'Not Started'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
    ]
    
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    
    # Progress tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=NOT_STARTED)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    # Video/content consumption
    watch_time = models.PositiveIntegerField(default=0)  # Seconds
    completion_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00
    )
    
    # Notes and bookmarks
    notes = models.TextField(blank=True, null=True)
    is_bookmarked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_lesson_progress'
        verbose_name = 'Lesson Progress'
        verbose_name_plural = 'Lesson Progress'
        unique_together = ['enrollment', 'lesson']
        indexes = [
            models.Index(fields=['enrollment', 'status']),
            models.Index(fields=['lesson']),
        ]
    
    def __str__(self):
        return f"{self.enrollment.student.full_name} - {self.lesson.title}"


class Announcement(models.Model):
    """Course announcements from instructors."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Settings
    is_urgent = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    send_email = models.BooleanField(default=False)
    
    # Targeting
    target_all_students = models.BooleanField(default=True)
    target_students = models.ManyToManyField(User, blank=True, related_name='targeted_announcements')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_announcement'
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.course.title}: {self.title}"
