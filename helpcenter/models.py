from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
import uuid


class HelpCategory(models.Model):
    """Categories for organizing help articles and FAQs."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    
    # Category hierarchy
    parent_category = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        related_name='subcategories'
    )
    
    # Display settings
    icon = models.CharField(max_length=50, blank=True, null=True)  # CSS icon class
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    sort_order = models.PositiveIntegerField(default=0)
    
    # Visibility
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_help_categories')
    
    class Meta:
        db_table = 'helpcenter_category'
        verbose_name = 'Help Category'
        verbose_name_plural = 'Help Categories'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def full_path(self):
        """Get the full category path."""
        if self.parent_category:
            return f"{self.parent_category.full_path} > {self.name}"
        return self.name


class Article(models.Model):
    """Help articles and documentation."""
    
    # Article types
    GUIDE = 'guide'
    TUTORIAL = 'tutorial'
    FAQ = 'faq'
    TROUBLESHOOTING = 'troubleshooting'
    FEATURE_OVERVIEW = 'feature_overview'
    
    ARTICLE_TYPES = [
        (GUIDE, 'Guide'),
        (TUTORIAL, 'Tutorial'),
        (FAQ, 'FAQ'),
        (TROUBLESHOOTING, 'Troubleshooting'),
        (FEATURE_OVERVIEW, 'Feature Overview'),
    ]
    
    # Publication status
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    UNDER_REVIEW = 'under_review'
    
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (ARCHIVED, 'Archived'),
        (UNDER_REVIEW, 'Under Review'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    
    # Content
    summary = models.CharField(max_length=500, blank=True, null=True)
    content = models.TextField()
    
    # Organization
    category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE, related_name='articles')
    article_type = models.CharField(max_length=30, choices=ARTICLE_TYPES, default=GUIDE)
    tags = models.JSONField(default=list, blank=True)  # List of tags
    
    # Publication
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    is_featured = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True, null=True)
    meta_keywords = models.CharField(max_length=500, blank=True, null=True)
    
    # Difficulty and target audience
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    target_audience = models.JSONField(default=list, blank=True)  # student, teacher, admin
    
    # Reading time and metrics
    estimated_read_time = models.PositiveIntegerField(default=0)  # Minutes
    view_count = models.PositiveIntegerField(default=0)
    helpful_votes = models.PositiveIntegerField(default=0)
    not_helpful_votes = models.PositiveIntegerField(default=0)
    
    # Related articles
    related_articles = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    # Multimedia
    featured_image = models.ImageField(upload_to='help/images/%Y/%m/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    attachments = models.JSONField(default=list, blank=True)  # List of file attachments
    
    # Versioning
    version = models.CharField(max_length=20, default='1.0')
    last_reviewed_date = models.DateTimeField(blank=True, null=True)
    
    # Authors and contributors
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_articles')
    contributors = models.ManyToManyField(User, blank=True, related_name='contributed_articles')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'helpcenter_article'
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
        ordering = ['-is_pinned', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_published(self):
        return self.status == self.PUBLISHED
    
    @property
    def helpfulness_score(self):
        """Calculate helpfulness score percentage."""
        total_votes = self.helpful_votes + self.not_helpful_votes
        if total_votes == 0:
            return 0
        return round((self.helpful_votes / total_votes) * 100, 1)


class FAQ(models.Model):
    """Frequently Asked Questions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.CharField(max_length=500)
    answer = models.TextField()
    
    # Organization
    category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE, related_name='faqs')
    tags = models.JSONField(default=list, blank=True)
    
    # Display settings
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Metrics
    view_count = models.PositiveIntegerField(default=0)
    helpful_votes = models.PositiveIntegerField(default=0)
    not_helpful_votes = models.PositiveIntegerField(default=0)
    
    # Related content
    related_articles = models.ManyToManyField(Article, blank=True, related_name='related_faqs')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_faqs')
    
    class Meta:
        db_table = 'helpcenter_faq'
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['sort_order', '-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return self.question
    
    @property
    def helpfulness_score(self):
        """Calculate helpfulness score percentage."""
        total_votes = self.helpful_votes + self.not_helpful_votes
        if total_votes == 0:
            return 0
        return round((self.helpful_votes / total_votes) * 100, 1)


class SupportTicket(models.Model):
    """Support tickets for user assistance."""
    
    # Ticket status
    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    WAITING_FOR_USER = 'waiting_for_user'
    WAITING_FOR_STAFF = 'waiting_for_staff'
    RESOLVED = 'resolved'
    CLOSED = 'closed'
    
    STATUS_CHOICES = [
        (OPEN, 'Open'),
        (IN_PROGRESS, 'In Progress'),
        (WAITING_FOR_USER, 'Waiting for User'),
        (WAITING_FOR_STAFF, 'Waiting for Staff'),
        (RESOLVED, 'Resolved'),
        (CLOSED, 'Closed'),
    ]
    
    # Priority levels
    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'
    URGENT = 'urgent'
    
    PRIORITY_CHOICES = [
        (LOW, 'Low'),
        (NORMAL, 'Normal'),
        (HIGH, 'High'),
        (URGENT, 'Urgent'),
    ]
    
    # Ticket categories
    TECHNICAL_ISSUE = 'technical_issue'
    ACCOUNT_ISSUE = 'account_issue'
    COURSE_RELATED = 'course_related'
    PAYMENT_ISSUE = 'payment_issue'
    FEATURE_REQUEST = 'feature_request'
    GENERAL_INQUIRY = 'general_inquiry'
    BUG_REPORT = 'bug_report'
    
    CATEGORY_CHOICES = [
        (TECHNICAL_ISSUE, 'Technical Issue'),
        (ACCOUNT_ISSUE, 'Account Issue'),
        (COURSE_RELATED, 'Course Related'),
        (PAYMENT_ISSUE, 'Payment Issue'),
        (FEATURE_REQUEST, 'Feature Request'),
        (GENERAL_INQUIRY, 'General Inquiry'),
        (BUG_REPORT, 'Bug Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Ticket details
    subject = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=NORMAL)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=OPEN)
    
    # People involved
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='assigned_tickets'
    )
    
    # Additional context
    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    system_info = models.JSONField(default=dict, blank=True)  # Browser, OS, etc.
    
    # Attachments
    attachments = models.JSONField(default=list, blank=True)  # List of attached files
    
    # Resolution
    resolution = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='resolved_tickets'
    )
    
    # Satisfaction
    satisfaction_rating = models.PositiveIntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    satisfaction_feedback = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_response_at = models.DateTimeField(blank=True, null=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'helpcenter_support_ticket'
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket_number']),
            models.Index(fields=['requester', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Ticket #{self.ticket_number}: {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        super().save(*args, **kwargs)
    
    def generate_ticket_number(self):
        """Generate unique ticket number."""
        from django.utils.crypto import get_random_string
        prefix = "TIC"
        timestamp = timezone.now().strftime('%y%m%d')
        random_suffix = get_random_string(4, '0123456789')
        return f"{prefix}-{timestamp}-{random_suffix}"
    
    @property
    def is_open(self):
        return self.status in [self.OPEN, self.IN_PROGRESS, self.WAITING_FOR_USER, self.WAITING_FOR_STAFF]
    
    @property
    def response_time(self):
        """Calculate first response time in hours."""
        if self.first_response_at:
            delta = self.first_response_at - self.created_at
            return round(delta.total_seconds() / 3600, 2)
        return None
    
    @property
    def resolution_time(self):
        """Calculate resolution time in hours."""
        if self.resolved_at:
            delta = self.resolved_at - self.created_at
            return round(delta.total_seconds() / 3600, 2)
        return None


class TicketMessage(models.Model):
    """Messages within support tickets."""
    
    # Message types
    USER_MESSAGE = 'user_message'
    STAFF_REPLY = 'staff_reply'
    SYSTEM_NOTE = 'system_note'
    STATUS_CHANGE = 'status_change'
    
    MESSAGE_TYPES = [
        (USER_MESSAGE, 'User Message'),
        (STAFF_REPLY, 'Staff Reply'),
        (SYSTEM_NOTE, 'System Note'),
        (STATUS_CHANGE, 'Status Change'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    
    # Message details
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    content = models.TextField()
    
    # Author
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_messages')
    is_internal = models.BooleanField(default=False)  # Internal staff notes
    
    # Attachments
    attachments = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'helpcenter_ticket_message'
        verbose_name = 'Ticket Message'
        verbose_name_plural = 'Ticket Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
        ]
    
    def __str__(self):
        return f"Message in {self.ticket.ticket_number} by {self.author.full_name}"


class HelpSearch(models.Model):
    """Track help center search queries for analytics."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.CharField(max_length=500)
    results_count = models.PositiveIntegerField(default=0)
    
    # User context
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='help_searches')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Results interaction
    clicked_results = models.JSONField(default=list, blank=True)  # List of clicked article IDs
    was_helpful = models.BooleanField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'helpcenter_search'
        verbose_name = 'Help Search'
        verbose_name_plural = 'Help Searches'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['query']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Search: {self.query} ({self.results_count} results)"


class ContentRating(models.Model):
    """User ratings for help content."""
    
    # Rating types
    ARTICLE_RATING = 'article'
    FAQ_RATING = 'faq'
    
    CONTENT_TYPES = [
        (ARTICLE_RATING, 'Article'),
        (FAQ_RATING, 'FAQ'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_id = models.UUIDField()  # ID of the rated content
    
    # Rating details
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_ratings')
    is_helpful = models.BooleanField()  # True for helpful, False for not helpful
    feedback = models.TextField(blank=True, null=True)  # Optional feedback
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'helpcenter_content_rating'
        verbose_name = 'Content Rating'
        verbose_name_plural = 'Content Ratings'
        unique_together = ['content_type', 'content_id', 'user']
        indexes = [
            models.Index(fields=['content_type', 'content_id']),
        ]
    
    def __str__(self):
        helpful_text = "Helpful" if self.is_helpful else "Not Helpful"
        return f"{self.get_content_type_display()} rating: {helpful_text}"


class KnowledgeBase(models.Model):
    """Knowledge base collections for organizing content."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=200, unique=True)
    
    # Organization
    categories = models.ManyToManyField(HelpCategory, related_name='knowledge_bases')
    
    # Settings
    is_public = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Access control
    allowed_roles = models.JSONField(default=list, blank=True)  # List of allowed user roles
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_knowledge_bases')
    
    class Meta:
        db_table = 'helpcenter_knowledge_base'
        verbose_name = 'Knowledge Base'
        verbose_name_plural = 'Knowledge Bases'
        ordering = ['name']
    
    def __str__(self):
        return self.name
