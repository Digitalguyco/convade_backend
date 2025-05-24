"""
Celery tasks for the tests app.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import Test, TestAttempt
from accounts.models import User


@shared_task
def send_test_reminders():
    """Send reminders for upcoming tests."""
    
    # Find tests that start in the next 24 hours
    tomorrow = timezone.now() + timedelta(days=1)
    upcoming_tests = Test.objects.filter(
        start_date__lte=tomorrow,
        start_date__gte=timezone.now(),
        is_active=True
    )
    
    reminder_count = 0
    
    for test in upcoming_tests:
        # Get users who are enrolled in the course but haven't taken the test
        enrolled_users = test.course.enrollments.filter(
            status='active'
        ).exclude(
            user__test_attempts__test=test
        ).values_list('user', flat=True)
        
        for user_id in enrolled_users:
            try:
                user = User.objects.get(id=user_id)
                
                # Check if user wants test reminders
                if hasattr(user, 'notification_settings') and user.notification_settings.test_reminders:
                    subject = f"Reminder: {test.title} starts tomorrow"
                    message = f"""
Hi {user.first_name},

This is a reminder that the test "{test.title}" is scheduled to start tomorrow at {test.start_date}.

Course: {test.course.title}
Duration: {test.duration} minutes
Attempts allowed: {test.max_attempts}

Good luck with your test!

Best regards,
Convade LMS Team
                    """
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=True
                    )
                    
                    reminder_count += 1
                    
            except User.DoesNotExist:
                continue
    
    return f"Sent {reminder_count} test reminders"


@shared_task
def process_test_submission(test_attempt_id):
    """Process a test submission in the background."""
    
    try:
        attempt = TestAttempt.objects.get(id=test_attempt_id)
        
        # Calculate final score if not already calculated
        if attempt.status == 'in_progress':
            attempt.calculate_score()
            attempt.status = 'completed'
            attempt.submitted_at = timezone.now()
            attempt.save()
            
            # Send result notification if user wants it
            user = attempt.user
            if hasattr(user, 'notification_settings') and user.notification_settings.test_results:
                subject = f"Test Results: {attempt.test.title}"
                message = f"""
Hi {user.first_name},

Your test results for "{attempt.test.title}" are now available.

Score: {attempt.score}%
Status: {'Passed' if attempt.passed else 'Failed'}
Completion Time: {attempt.submitted_at}

You can view detailed results in your dashboard.

Best regards,
Convade LMS Team
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True
                )
        
        return f"Processed test attempt {test_attempt_id}"
        
    except TestAttempt.DoesNotExist:
        return f"Test attempt {test_attempt_id} not found"


@shared_task
def cleanup_expired_test_attempts():
    """Clean up expired test attempts."""
    
    # Find attempts that are still 'in_progress' but have exceeded the time limit
    expired_attempts = TestAttempt.objects.filter(
        status='in_progress',
        started_at__lt=timezone.now() - timedelta(hours=24)  # Cleanup after 24 hours
    )
    
    count = 0
    for attempt in expired_attempts:
        # Auto-submit expired attempts
        attempt.status = 'expired'
        attempt.submitted_at = timezone.now()
        attempt.calculate_score()  # Calculate score based on answered questions
        attempt.save()
        count += 1
    
    return f"Cleaned up {count} expired test attempts" 