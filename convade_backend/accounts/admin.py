from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import User, School, UserProfile, UserSession, Invitation, RegistrationCode


class UserProfileInline(admin.StackedInline):
    """Inline admin interface for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    extra = 0
    fields = (
        'school', 'student_id', 'employee_id', 'current_year', 'gpa',
        'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
        'preferred_learning_style', 'linkedin_url', 'twitter_url'
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced admin interface for User model."""
    
    inlines = (UserProfileInline,)
    
    list_display = (
        'email', 'first_name', 'last_name', 'role', 'status',
        'is_email_verified', 'school_display', 'date_joined', 'last_login'
    )
    list_filter = (
        'role', 'status', 'is_email_verified', 'is_active', 'is_staff',
        'date_joined', 'last_login'
    )
    search_fields = ('email', 'first_name', 'last_name', 'school_id')
    readonly_fields = ('id', 'date_joined', 'last_login', 'last_activity')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth', 'bio')
        }),
        ('Academic info', {
            'fields': ('role', 'status', 'school_id', 'grade_level', 'department')
        }),
        ('Email verification', {
            'fields': ('is_email_verified', 'email_verification_token')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('date_joined', 'last_login', 'last_activity')
        }),
        ('Preferences', {
            'fields': ('timezone', 'language', 'notifications_enabled', 'email_notifications'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role'),
        }),
    )
    
    ordering = ('email',)
    
    def school_display(self, obj):
        """Display school information."""
        if hasattr(obj, 'profile') and obj.profile.school:
            return obj.profile.school.name
        return obj.school_id or '-'
    school_display.short_description = 'School'


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    """Admin interface for School model."""
    
    list_display = (
        'name', 'code', 'school_type', 'city', 'state', 'country',
        'user_count', 'created_at'
    )
    list_filter = ('school_type', 'country', 'state', 'created_at')
    search_fields = ('name', 'code', 'city', 'email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'user_count')
    
    fieldsets = (
        (None, {'fields': ('name', 'code')}),
        ('Contact Information', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code', 'phone', 'email', 'website')
        }),
        ('School Details', {
            'fields': ('established_date', 'school_type', 'timezone')
        }),
        ('Academic Year', {
            'fields': ('academic_year_start', 'academic_year_end')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'user_count'),
            'classes': ('collapse',)
        }),
    )
    
    def user_count(self, obj):
        """Count users associated with this school."""
        return User.objects.filter(profile__school=obj).count()
    user_count.short_description = 'Total Users'


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    """Admin interface for Invitation model."""
    
    list_display = (
        'email', 'role', 'school', 'status', 'invited_by',
        'is_valid_display', 'expires_at', 'created_at'
    )
    list_filter = ('status', 'role', 'school', 'created_at', 'expires_at')
    search_fields = ('email', 'school__name', 'invited_by__email')
    readonly_fields = (
        'id', 'token', 'created_at', 'accepted_at', 'accepted_by', 'is_valid_display'
    )
    
    fieldsets = (
        (None, {
            'fields': ('email', 'role', 'school', 'invited_by')
        }),
        ('Token & Status', {
            'fields': ('token', 'status', 'is_valid_display')
        }),
        ('Timing', {
            'fields': ('created_at', 'expires_at', 'accepted_at')
        }),
        ('Acceptance', {
            'fields': ('accepted_by',)
        }),
        ('Additional Data', {
            'fields': ('additional_data',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['revoke_invitations', 'extend_expiration']
    
    def is_valid_display(self, obj):
        """Display invitation validity with color coding."""
        if obj.is_valid():
            return format_html('<span style="color: green;">✅ Valid</span>')
        else:
            return format_html('<span style="color: red;">❌ Invalid</span>')
    is_valid_display.short_description = 'Status'
    
    def revoke_invitations(self, request, queryset):
        """Action to revoke selected invitations."""
        updated = 0
        for invitation in queryset.filter(status=Invitation.PENDING):
            invitation.revoke()
            updated += 1
        self.message_user(request, f'{updated} invitations revoked.')
    revoke_invitations.short_description = 'Revoke selected invitations'
    
    def extend_expiration(self, request, queryset):
        """Action to extend expiration by 7 days."""
        updated = 0
        for invitation in queryset.filter(status=Invitation.PENDING):
            invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
            invitation.save()
            updated += 1
        self.message_user(request, f'{updated} invitations extended.')
    extend_expiration.short_description = 'Extend expiration by 7 days'


@admin.register(RegistrationCode)
class RegistrationCodeAdmin(admin.ModelAdmin):
    """Admin interface for RegistrationCode model."""
    
    list_display = (
        'code', 'school', 'role', 'usage_display', 'status',
        'is_valid_display', 'expires_at', 'created_at'
    )
    list_filter = ('status', 'role', 'school', 'created_at', 'expires_at')
    search_fields = ('code', 'school__name', 'created_by__email')
    readonly_fields = (
        'id', 'code', 'current_uses', 'created_at', 'is_valid_display', 'usage_display'
    )
    
    fieldsets = (
        (None, {
            'fields': ('code', 'school', 'role', 'created_by')
        }),
        ('Usage Settings', {
            'fields': ('max_uses', 'current_uses', 'usage_display')
        }),
        ('Status & Timing', {
            'fields': ('status', 'is_valid_display', 'expires_at', 'created_at')
        }),
        ('Academic Settings', {
            'fields': ('grade_level', 'department'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['deactivate_codes', 'reset_usage']
    
    def usage_display(self, obj):
        """Display usage statistics with progress bar."""
        if obj.max_uses == 0:
            return f"{obj.current_uses} / ∞"
        
        percentage = (obj.current_uses / obj.max_uses) * 100
        color = 'green' if percentage < 50 else 'orange' if percentage < 80 else 'red'
        
        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 20px; border-radius: 3px; text-align: center; color: white; line-height: 20px;">'
            '{}/{}</div></div>',
            percentage, color, obj.current_uses, obj.max_uses
        )
    usage_display.short_description = 'Usage'
    
    def is_valid_display(self, obj):
        """Display code validity with color coding."""
        if obj.is_valid():
            return format_html('<span style="color: green;">✅ Valid</span>')
        else:
            return format_html('<span style="color: red;">❌ Invalid</span>')
    is_valid_display.short_description = 'Status'
    
    def deactivate_codes(self, request, queryset):
        """Action to deactivate selected codes."""
        updated = queryset.filter(status=RegistrationCode.ACTIVE).update(
            status=RegistrationCode.INACTIVE
        )
        self.message_user(request, f'{updated} codes deactivated.')
    deactivate_codes.short_description = 'Deactivate selected codes'
    
    def reset_usage(self, request, queryset):
        """Action to reset usage count."""
        updated = queryset.update(current_uses=0)
        self.message_user(request, f'{updated} codes usage reset.')
    reset_usage.short_description = 'Reset usage count'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin interface for UserSession model."""
    
    list_display = (
        'user', 'ip_address', 'browser', 'device_type',
        'is_active', 'created_at', 'last_activity'
    )
    list_filter = ('is_active', 'browser', 'device_type', 'created_at', 'last_activity')
    search_fields = ('user__email', 'ip_address', 'user_agent')
    readonly_fields = ('session_key', 'created_at', 'last_activity')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'session_key', 'is_active')
        }),
        ('Connection Info', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Device Details', {
            'fields': ('browser', 'operating_system', 'device_type')
        }),
        ('Timing', {
            'fields': ('created_at', 'last_activity', 'expires_at')
        }),
    )
    
    actions = ['deactivate_sessions']
    
    def deactivate_sessions(self, request, queryset):
        """Action to deactivate selected sessions."""
        updated = queryset.filter(is_active=True).update(is_active=False)
        self.message_user(request, f'{updated} sessions deactivated.')
    deactivate_sessions.short_description = 'Deactivate selected sessions'


# Customize admin site headers
admin.site.site_header = "Convade LMS Administration"
admin.site.site_title = "Convade LMS Admin"
admin.site.index_title = "Welcome to Convade LMS Administration"
