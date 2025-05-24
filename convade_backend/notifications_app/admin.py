from django.contrib import admin
from django.utils.html import format_html
from .models import (
    NotificationTemplate, Notification, UserNotificationSettings,
    NotificationBatch, NotificationLog
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for NotificationTemplate model."""
    
    list_display = ('name', 'template_type', 'is_active', 'created_at')
    list_filter = ('template_type', 'is_active', 'created_at')
    search_fields = ('name', 'subject', 'body')
    ordering = ('name',)
    
    fieldsets = (
        (None, {'fields': ('name', 'template_type')}),
        ('Content', {'fields': ('subject', 'body')}),
        ('Settings', {'fields': ('is_active',)}),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for Notification model."""
    
    list_display = ('title_short', 'recipient', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'message', 'recipient__email')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('template', 'recipient', 'status', 'priority')
        }),
        ('Content', {'fields': ('title', 'message')}),
        ('Settings', {
            'fields': ('scheduled_at', 'expires_at')
        }),
        ('Metadata', {'fields': ('metadata',)}),
    )
    
    readonly_fields = ('sent_at', 'read_at', 'created_at')
    
    def title_short(self, obj):
        return obj.title[:50] + "..." if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'


@admin.register(UserNotificationSettings)
class UserNotificationSettingsAdmin(admin.ModelAdmin):
    """Admin configuration for UserNotificationSettings model."""
    
    list_display = ('user', 'notifications_enabled', 'email_notifications', 'digest_frequency')
    list_filter = ('notifications_enabled', 'digest_frequency')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    ordering = ('user__email',)
    
    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Channels', {
            'fields': ('notifications_enabled', 'email_notifications', 'digest_frequency')
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_start', 'quiet_hours_end', 'timezone')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    """Admin configuration for NotificationBatch model."""
    
    list_display = ('name', 'status', 'total_recipients', 'sent_count', 'failed_count')
    list_filter = ('status', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('name', 'status')}),
        ('Content', {'fields': ('template', 'content_data')}),
        ('Schedule', {'fields': ('scheduled_at',)}),
        ('Status', {
            'fields': (
                'total_recipients', 'sent_count', 'failed_count'
            )
        }),
    )
    
    readonly_fields = (
        'total_recipients', 'sent_count', 'failed_count', 
        'created_at'
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """Admin configuration for NotificationLog model."""
    
    list_display = ('notification_title', 'delivery_method', 'delivery_status', 'attempted_at')
    list_filter = ('delivery_method', 'delivery_status', 'attempted_at')
    search_fields = ('notification__title', 'recipient_email')
    ordering = ('-attempted_at',)
    
    readonly_fields = ('attempted_at',)
    
    def notification_title(self, obj):
        return obj.notification.title[:50] + '...' if len(obj.notification.title) > 50 else obj.notification.title
    notification_title.short_description = 'Notification'

    def has_add_permission(self, request):
        return False  # Logs are created automatically
