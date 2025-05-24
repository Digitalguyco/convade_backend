from django.db import models
from django.utils import timezone
from accounts.models import User
from courses.models import Course
from tests.models import Test
import uuid


class NotificationTemplate(models.Model):
    """Templates for different types of notifications."""
    
    # Template types
    EMAIL = 'email'
    PUSH = 'push'
    SMS = 'sms'
    IN_APP = 'in_app'
    
    TEMPLATE_TYPES = [
        (EMAIL, 'Email'),
        (PUSH, 'Push Notification'),
        (SMS, 'SMS'),
        (IN_APP, 'In-App Notification'),
    ]
    
    # Notification categories
    TEST_REMINDER = 'test_reminder'
    TEST_RESULT = 'test_result'
    COURSE_UPDATE = 'course_update'
    ENROLLMENT = 'enrollment'
    BADGE_EARNED = 'badge_earned'
    ASSIGNMENT_DUE = 'assignment_due'
    SYSTEM_ALERT = 'system_alert'
    WELCOME = 'welcome'
    
    CATEGORIES = [
        (TEST_REMINDER, 'Test Reminder'),
        (TEST_RESULT, 'Test Result'),
        (COURSE_UPDATE, 'Course Update'),
        (ENROLLMENT, 'Enrollment'),
        (BADGE_EARNED, 'Badge Earned'),
        (ASSIGNMENT_DUE, 'Assignment Due'),
        (SYSTEM_ALERT, 'System Alert'),
        (WELCOME, 'Welcome'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORIES)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    
    # Template content
    subject = models.CharField(max_length=200, blank=True, null=True)  # For email/SMS
    title = models.CharField(max_length=200)  # For push/in-app
    body = models.TextField()
    html_body = models.TextField(blank=True, null=True)  # For email
    
    # Template variables (JSON list of available variables)
    variables = models.JSONField(default=list, blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)  # System templates can't be deleted
    
    # Scheduling
    send_immediately = models.BooleanField(default=True)
    delay_minutes = models.PositiveIntegerField(default=0)  # Delay before sending
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_templates')
    
    class Meta:
        db_table = 'notifications_template'
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
        unique_together = ['category', 'template_type']
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class Notification(models.Model):
    """Individual notifications sent to users."""
    
    # Notification status
    PENDING = 'pending'
    SENT = 'sent'
    DELIVERED = 'delivered'
    READ = 'read'
    FAILED = 'failed'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (SENT, 'Sent'),
        (DELIVERED, 'Delivered'),
        (READ, 'Read'),
        (FAILED, 'Failed'),
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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, related_name='notifications')
    
    # Content (can override template)
    title = models.CharField(max_length=200)
    message = models.TextField()
    html_message = models.TextField(blank=True, null=True)
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=NORMAL)
    
    # Context data
    context_data = models.JSONField(default=dict, blank=True)
    
    # Related objects
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, blank=True, null=True)
    
    # Action URL (for clickable notifications)
    action_url = models.URLField(blank=True, null=True)
    action_text = models.CharField(max_length=100, blank=True, null=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    # Tracking
    attempt_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_notification'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} -> {self.recipient.email}"
    
    @property
    def is_read(self):
        return self.status == self.READ
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def mark_as_read(self):
        """Mark notification as read."""
        if self.status != self.READ:
            self.status = self.READ
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])


class UserNotificationSettings(models.Model):
    """User preferences for notifications."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    
    # Global settings
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    in_app_notifications = models.BooleanField(default=True)
    
    # Category-specific settings
    test_reminders = models.BooleanField(default=True)
    test_results = models.BooleanField(default=True)
    course_updates = models.BooleanField(default=True)
    enrollment_notifications = models.BooleanField(default=True)
    badge_notifications = models.BooleanField(default=True)
    assignment_reminders = models.BooleanField(default=True)
    system_alerts = models.BooleanField(default=True)
    
    # Timing preferences
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(default='22:00')
    quiet_hours_end = models.TimeField(default='08:00')
    
    # Frequency settings
    digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='immediate'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_user_settings'
        verbose_name = 'User Notification Settings'
        verbose_name_plural = 'User Notification Settings'
    
    def __str__(self):
        return f"{self.user.full_name} - Notification Settings"


class NotificationLog(models.Model):
    """Log of notification delivery attempts."""
    
    # Delivery methods
    EMAIL = 'email'
    PUSH = 'push'
    SMS = 'sms'
    IN_APP = 'in_app'
    
    DELIVERY_METHODS = [
        (EMAIL, 'Email'),
        (PUSH, 'Push'),
        (SMS, 'SMS'),
        (IN_APP, 'In-App'),
    ]
    
    # Delivery status
    SUCCESS = 'success'
    FAILED = 'failed'
    BOUNCED = 'bounced'
    REJECTED = 'rejected'
    
    DELIVERY_STATUS = [
        (SUCCESS, 'Success'),
        (FAILED, 'Failed'),
        (BOUNCED, 'Bounced'),
        (REJECTED, 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='delivery_logs')
    
    # Delivery details
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS)
    
    # Recipient details
    recipient_email = models.EmailField(blank=True, null=True)
    recipient_phone = models.CharField(max_length=20, blank=True, null=True)
    device_token = models.TextField(blank=True, null=True)  # For push notifications
    
    # Delivery tracking
    external_id = models.CharField(max_length=200, blank=True, null=True)  # Provider tracking ID
    response_data = models.JSONField(default=dict, blank=True)
    error_code = models.CharField(max_length=50, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Timing
    attempted_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'notifications_delivery_log'
        verbose_name = 'Notification Delivery Log'
        verbose_name_plural = 'Notification Delivery Logs'
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['notification', 'delivery_method']),
            models.Index(fields=['delivery_status']),
        ]
    
    def __str__(self):
        return f"{self.notification.title} - {self.get_delivery_method_display()} - {self.get_delivery_status_display()}"


class NotificationBatch(models.Model):
    """Batch notifications for bulk sending."""
    
    # Batch status
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (CANCELLED, 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    
    # Target recipients
    target_users = models.ManyToManyField(User, blank=True, related_name='notification_batches')
    target_criteria = models.JSONField(default=dict, blank=True)  # For dynamic targeting
    
    # Batch settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    # Scheduling
    scheduled_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Context data for all notifications in batch
    context_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_batches')
    
    class Meta:
        db_table = 'notifications_batch'
        verbose_name = 'Notification Batch'
        verbose_name_plural = 'Notification Batches'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.total_recipients} recipients)"
