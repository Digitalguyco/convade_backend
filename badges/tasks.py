"""
Celery tasks for the badges app.
"""
from celery import shared_task
from django.utils import timezone
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from .models import Badge, UserBadge, BadgeProgress
from accounts.models import User
from courses.models import Enrollment
from tests.models import TestAttempt


@shared_task
def update_badge_progress():
    """Update badge progress for all users."""
    
    updated_count = 0
    
    # Get all active badges
    active_badges = Badge.objects.filter(is_active=True)
    
    for badge in active_badges:
        # Get all users who might be eligible for this badge
        users = User.objects.filter(is_active=True)
        
        for user in users:
            try:
                # Check if user already has this badge
                if UserBadge.objects.filter(user=user, badge=badge).exists():
                    continue
                
                # Get or create badge progress
                progress, created = BadgeProgress.objects.get_or_create(
                    user=user,
                    badge=badge,
                    defaults={'current_value': 0}
                )
                
                # Calculate current progress based on badge criteria
                current_value = calculate_badge_progress(user, badge)
                
                if current_value != progress.current_value:
                    progress.current_value = current_value
                    progress.last_updated = timezone.now()
                    progress.save()
                    updated_count += 1
                    
                    # Check if badge should be awarded
                    if current_value >= badge.required_value and not progress.completed:
                        award_badge_to_user.delay(user.id, badge.id)
                        
            except Exception as e:
                # Log error but continue processing
                print(f"Error updating badge progress for user {user.id}, badge {badge.id}: {str(e)}")
                continue
    
    return f"Updated badge progress for {updated_count} entries"


def calculate_badge_progress(user, badge):
    """Calculate the current progress value for a user's badge."""
    
    criteria_type = badge.criteria_type
    
    if criteria_type == 'course_completion':
        # Count completed courses
        return Enrollment.objects.filter(
            user=user,
            status='completed'
        ).count()
        
    elif criteria_type == 'test_score':
        # Get highest test score
        highest_score = TestAttempt.objects.filter(
            user=user,
            status='completed'
        ).aggregate(models.Max('score'))['score__max']
        return highest_score or 0
        
    elif criteria_type == 'login_streak':
        # Calculate current login streak
        # This would require a more complex calculation
        # For now, return a placeholder
        return 0
        
    elif criteria_type == 'total_tests':
        # Count total completed tests
        return TestAttempt.objects.filter(
            user=user,
            status='completed'
        ).count()
        
    elif criteria_type == 'perfect_scores':
        # Count tests with perfect scores
        return TestAttempt.objects.filter(
            user=user,
            status='completed',
            score=100
        ).count()
        
    elif criteria_type == 'study_time':
        # Calculate total study time in minutes
        # This would require session tracking
        # For now, return a placeholder
        return 0
        
    else:
        return 0


@shared_task
def award_badge_to_user(user_id, badge_id):
    """Award a badge to a user."""
    
    try:
        user = User.objects.get(id=user_id)
        badge = Badge.objects.get(id=badge_id)
        
        # Check if user already has this badge
        if UserBadge.objects.filter(user=user, badge=badge).exists():
            return f"User {user_id} already has badge {badge_id}"
        
        # Award the badge
        user_badge = UserBadge.objects.create(
            user=user,
            badge=badge,
            earned_at=timezone.now()
        )
        
        # Update badge progress as completed
        BadgeProgress.objects.filter(
            user=user,
            badge=badge
        ).update(
            completed=True,
            completed_at=timezone.now()
        )
        
        # Send notification if user wants badge notifications
        if hasattr(user, 'notification_settings') and user.notification_settings.badge_notifications:
            subject = f"Congratulations! You've earned the {badge.name} badge"
            message = f"""
Hi {user.first_name},

Congratulations! You've earned a new badge: "{badge.name}"

{badge.description}

This badge recognizes your achievement in: {badge.get_criteria_type_display()}

Keep up the great work!

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
        
        return f"Awarded badge '{badge.name}' to user {user.full_name}"
        
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Badge.DoesNotExist:
        return f"Badge {badge_id} not found"
    except Exception as e:
        return f"Error awarding badge: {str(e)}"


@shared_task
def recalculate_user_badges(user_id):
    """Recalculate all badges for a specific user."""
    
    try:
        user = User.objects.get(id=user_id)
        badges_checked = 0
        badges_awarded = 0
        
        # Get all active badges
        active_badges = Badge.objects.filter(is_active=True)
        
        for badge in active_badges:
            # Skip if user already has this badge
            if UserBadge.objects.filter(user=user, badge=badge).exists():
                continue
                
            badges_checked += 1
            
            # Calculate current progress
            current_value = calculate_badge_progress(user, badge)
            
            # Update or create badge progress
            progress, created = BadgeProgress.objects.get_or_create(
                user=user,
                badge=badge,
                defaults={'current_value': current_value}
            )
            
            if not created:
                progress.current_value = current_value
                progress.last_updated = timezone.now()
                progress.save()
            
            # Award badge if criteria met
            if current_value >= badge.required_value:
                award_badge_to_user.delay(user.id, badge.id)
                badges_awarded += 1
        
        return f"Checked {badges_checked} badges for user {user.full_name}, awarded {badges_awarded}"
        
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Exception as e:
        return f"Error recalculating badges: {str(e)}"


@shared_task
def cleanup_badge_progress():
    """Clean up old badge progress entries."""
    
    # Remove progress entries for inactive badges
    deleted_count = BadgeProgress.objects.filter(
        badge__is_active=False
    ).delete()[0]
    
    return f"Cleaned up {deleted_count} badge progress entries" 