"""
Celery tasks for the accounts app.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
from django.conf import settings
from .models import User, RegistrationCode


@shared_task
def cleanup_expired_sessions():
    """Clean up expired sessions."""
    
    # Delete expired sessions
    deleted_count = Session.objects.filter(
        expire_date__lt=timezone.now()
    ).delete()[0]
    
    return f"Cleaned up {deleted_count} expired sessions"


@shared_task
def cleanup_expired_registration_codes():
    """Clean up expired registration codes."""
    
    # Mark expired codes as expired
    expired_codes = RegistrationCode.objects.filter(
        expires_at__lt=timezone.now(),
        status='active'
    )
    
    count = expired_codes.update(status='expired')
    
    return f"Marked {count} registration codes as expired"


@shared_task
def cleanup_expired_email_verifications():
    """Clean up expired email verification tokens."""
    
    # This would clean up email verification tokens if the model existed
    # For now, this is a placeholder task
    return "Email verification cleanup task - no model implemented yet"


@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new user."""
    
    try:
        user = User.objects.get(id=user_id)
        
        subject = "Welcome to Convade LMS!"
        message = f"""
Hi {user.first_name},

Welcome to Convade LMS! We're excited to have you join our learning community.

Your account has been successfully created with the following details:
- Email: {user.email}
- Role: {user.get_role_display()}

Here are some things you can do to get started:

1. Complete your profile by adding a profile picture and bio
2. Explore available courses in your dashboard
3. Set up your notification preferences
4. Join course discussions and connect with other learners

If you have any questions or need assistance, don't hesitate to reach out to our support team.

Happy learning!

Best regards,
The Convade LMS Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True
        )
        
        return f"Welcome email sent to {user.email}"
        
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Exception as e:
        return f"Error sending welcome email: {str(e)}"


@shared_task
def send_password_reset_email(user_id, reset_token):
    """Send password reset email."""
    
    try:
        user = User.objects.get(id=user_id)
        
        # Construct reset URL (this would typically use your frontend URL)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"
        
        subject = "Password Reset Request"
        message = f"""
Hi {user.first_name},

You requested a password reset for your Convade LMS account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours for security reasons.

If you didn't request this password reset, please ignore this email.

Best regards,
The Convade LMS Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True
        )
        
        return f"Password reset email sent to {user.email}"
        
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Exception as e:
        return f"Error sending password reset email: {str(e)}"


@shared_task
def update_user_activity():
    """Update user activity statistics."""
    
    # This could track things like:
    # - Last login times
    # - Activity streaks
    # - Learning time
    
    active_users = User.objects.filter(
        is_active=True,
        last_login__gte=timezone.now() - timedelta(days=30)
    )
    
    updated_count = 0
    
    for user in active_users:
        # Update user's last activity if needed
        # This is a placeholder for more complex activity tracking
        if hasattr(user, 'profile'):
            user.profile.save()  # This would trigger any activity calculations
            updated_count += 1
    
    return f"Updated activity for {updated_count} users"


@shared_task
def send_account_verification_reminder(user_id):
    """Send reminder to verify account."""
    
    try:
        user = User.objects.get(id=user_id)
        
        if user.is_email_verified:
            return f"User {user.email} is already verified"
        
        subject = "Please verify your email address"
        message = f"""
Hi {user.first_name},

We noticed that you haven't verified your email address yet. 

Please verify your email to:
- Access all course features
- Receive important notifications
- Ensure account security

You can request a new verification email from your account settings.

Best regards,
The Convade LMS Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True
        )
        
        return f"Verification reminder sent to {user.email}"
        
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Exception as e:
        return f"Error sending verification reminder: {str(e)}"


@shared_task
def cleanup_inactive_users():
    """Clean up users who never verified their email after 7 days."""
    
    cutoff_date = timezone.now() - timedelta(days=7)
    
    # Find users who registered but never verified email
    inactive_users = User.objects.filter(
        is_email_verified=False,
        date_joined__lt=cutoff_date,
        is_active=True
    )
    
    # Deactivate these users instead of deleting
    count = inactive_users.update(is_active=False)
    
    return f"Deactivated {count} unverified users" 