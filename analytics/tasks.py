"""
Celery tasks for the analytics app.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Count, Avg, Sum, Max
from django.core.mail import send_mail
from django.conf import settings
from .models import UserActivity, UserLearningAnalytics, SystemMetrics
from accounts.models import User
from courses.models import Course, Enrollment
from tests.models import TestAttempt
from badges.models import UserBadge


@shared_task
def generate_daily_reports():
    """Generate daily analytics reports."""
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Generate system metrics for yesterday
    metrics = calculate_daily_metrics(yesterday)
    
    # Create or update system metrics record
    system_metrics, created = SystemMetrics.objects.get_or_create(
        period_type='daily',
        period_start=timezone.datetime.combine(yesterday, timezone.datetime.min.time()).replace(tzinfo=timezone.get_current_timezone()),
        period_end=timezone.datetime.combine(yesterday, timezone.datetime.max.time()).replace(tzinfo=timezone.get_current_timezone()),
        defaults=metrics
    )
    
    if not created:
        # Update existing record
        for key, value in metrics.items():
            setattr(system_metrics, key, value)
        system_metrics.save()
    
    return f"Generated daily report for {yesterday}"


def calculate_daily_metrics(target_date):
    """Calculate metrics for a specific date."""
    
    start_datetime = timezone.datetime.combine(target_date, timezone.datetime.min.time()).replace(tzinfo=timezone.get_current_timezone())
    end_datetime = timezone.datetime.combine(target_date, timezone.datetime.max.time()).replace(tzinfo=timezone.get_current_timezone())
    
    # User metrics
    total_users = User.objects.filter(date_joined__lte=end_datetime).count()
    new_users = User.objects.filter(
        date_joined__gte=start_datetime,
        date_joined__lte=end_datetime
    ).count()
    
    # Active users (logged in that day)
    active_users = User.objects.filter(
        last_login__gte=start_datetime,
        last_login__lte=end_datetime
    ).count()
    
    # Content metrics
    total_courses = Course.objects.filter(created_at__lte=end_datetime).count()
    new_courses = Course.objects.filter(
        created_at__gte=start_datetime,
        created_at__lte=end_datetime
    ).count()
    
    # Enrollment metrics
    total_enrollments = Enrollment.objects.filter(enrolled_at__lte=end_datetime).count()
    new_enrollments = Enrollment.objects.filter(
        enrolled_at__gte=start_datetime,
        enrolled_at__lte=end_datetime
    ).count()
    
    course_completions = Enrollment.objects.filter(
        completed_at__gte=start_datetime,
        completed_at__lte=end_datetime
    ).count()
    
    # Test metrics
    test_attempts = TestAttempt.objects.filter(
        started_at__gte=start_datetime,
        started_at__lte=end_datetime
    ).count()
    
    # Badge metrics
    badges_awarded = UserBadge.objects.filter(
        earned_at__gte=start_datetime,
        earned_at__lte=end_datetime
    ).count()
    
    # Calculate averages
    avg_test_score = TestAttempt.objects.filter(
        submitted_at__gte=start_datetime,
        submitted_at__lte=end_datetime,
        status='completed'
    ).aggregate(avg_score=Avg('score'))['avg_score'] or 0
    
    # Calculate completion rate
    total_enrollments_with_activity = Enrollment.objects.filter(
        enrolled_at__lte=end_datetime
    ).count()
    
    total_completions = Enrollment.objects.filter(
        status='completed',
        completed_at__lte=end_datetime
    ).count()
    
    completion_rate = (total_completions / total_enrollments_with_activity * 100) if total_enrollments_with_activity > 0 else 0
    
    return {
        'total_users': total_users,
        'new_users': new_users,
        'active_users': active_users,
        'returning_users': 0,  # Would need more complex calculation
        'total_courses': total_courses,
        'new_courses': new_courses,
        'total_lessons': 0,  # Would need lesson model
        'total_tests': 0,  # Total tests, not attempts
        'total_enrollments': total_enrollments,
        'course_completions': course_completions,
        'test_attempts': test_attempts,
        'badges_awarded': badges_awarded,
        'total_study_time': 0,  # Would need session tracking
        'average_session_duration': 0,  # Would need session tracking
        'content_consumption_rate': 0.00,  # Would need detailed tracking
        'overall_completion_rate': round(completion_rate, 2),
        'average_test_score': round(avg_test_score, 2),
        'user_satisfaction': 0.00,  # Would need feedback system
    }


@shared_task
def update_user_learning_analytics():
    """Update learning analytics for all users."""
    
    updated_count = 0
    
    # Get all active users
    active_users = User.objects.filter(is_active=True)
    
    for user in active_users:
        try:
            # Get or create learning analytics record
            analytics, created = UserLearningAnalytics.objects.get_or_create(
                user=user,
                defaults={
                    'total_courses_enrolled': 0,
                    'total_courses_completed': 0,
                    'total_lessons_viewed': 0,
                    'total_tests_taken': 0,
                    'total_learning_time': 0,
                    'average_session_duration': 0,
                    'average_test_score': 0.0,
                    'improvement_rate': 0.0,
                    'completion_rate': 0.0,
                    'login_frequency': 0.0,
                    'learning_streak': 0,
                    'longest_streak': 0,
                }
            )
            
            # Update analytics
            enrollments = Enrollment.objects.filter(user=user)
            analytics.total_courses_enrolled = enrollments.count()
            analytics.total_courses_completed = enrollments.filter(status='completed').count()
            
            # Test analytics
            test_attempts = TestAttempt.objects.filter(user=user, status='completed')
            analytics.total_tests_taken = test_attempts.count()
            
            if test_attempts.exists():
                analytics.average_test_score = test_attempts.aggregate(
                    avg_score=Avg('score')
                )['avg_score'] or 0.0
            
            # Completion rate
            if analytics.total_courses_enrolled > 0:
                analytics.completion_rate = (
                    analytics.total_courses_completed / analytics.total_courses_enrolled * 100
                )
            
            # Update last learning session
            latest_activity = UserActivity.objects.filter(user=user).order_by('-timestamp').first()
            if latest_activity:
                analytics.last_learning_session = latest_activity.timestamp
            
            analytics.save()
            updated_count += 1
            
        except Exception as e:
            print(f"Error updating analytics for user {user.id}: {str(e)}")
            continue
    
    return f"Updated learning analytics for {updated_count} users"


@shared_task
def generate_weekly_reports():
    """Generate weekly analytics reports."""
    
    today = timezone.now().date()
    last_week_start = today - timedelta(days=7)
    last_week_end = today - timedelta(days=1)
    
    # Calculate weekly metrics
    start_datetime = timezone.datetime.combine(last_week_start, timezone.datetime.min.time()).replace(tzinfo=timezone.get_current_timezone())
    end_datetime = timezone.datetime.combine(last_week_end, timezone.datetime.max.time()).replace(tzinfo=timezone.get_current_timezone())
    
    # Aggregate daily metrics for the week
    daily_metrics = SystemMetrics.objects.filter(
        period_type='daily',
        period_start__gte=start_datetime,
        period_end__lte=end_datetime
    )
    
    if daily_metrics.exists():
        weekly_metrics = {
            'period_type': 'weekly',
            'period_start': start_datetime,
            'period_end': end_datetime,
            'total_users': daily_metrics.last().total_users if daily_metrics.exists() else 0,
            'new_users': sum(m.new_users for m in daily_metrics),
            'active_users': daily_metrics.aggregate(avg_active=Avg('active_users'))['avg_active'] or 0,
            'total_courses': daily_metrics.last().total_courses if daily_metrics.exists() else 0,
            'new_courses': sum(m.new_courses for m in daily_metrics),
            'course_completions': sum(m.course_completions for m in daily_metrics),
            'test_attempts': sum(m.test_attempts for m in daily_metrics),
            'badges_awarded': sum(m.badges_awarded for m in daily_metrics),
            'average_test_score': daily_metrics.aggregate(avg_score=Avg('average_test_score'))['avg_score'] or 0,
            'overall_completion_rate': daily_metrics.aggregate(avg_completion=Avg('overall_completion_rate'))['avg_completion'] or 0,
        }
        
        # Create weekly metrics record
        SystemMetrics.objects.create(**weekly_metrics)
    
    return f"Generated weekly report for {last_week_start} to {last_week_end}"


@shared_task
def log_user_activity(user_id, activity_type, metadata=None):
    """Log user activity for analytics."""
    
    try:
        user = User.objects.get(id=user_id)
        
        UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            metadata=metadata or {},
            timestamp=timezone.now()
        )
        
        return f"Logged activity {activity_type} for user {user.email}"
        
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Exception as e:
        return f"Error logging activity: {str(e)}"


@shared_task
def cleanup_old_analytics():
    """Clean up old analytics data."""
    
    # Keep only last 2 years of user activities
    cutoff_date = timezone.now() - timedelta(days=730)
    
    deleted_activities = UserActivity.objects.filter(
        timestamp__lt=cutoff_date
    ).delete()[0]
    
    # Keep only last year of daily metrics
    daily_cutoff = timezone.now() - timedelta(days=365)
    
    deleted_daily = SystemMetrics.objects.filter(
        period_type='daily',
        period_start__lt=daily_cutoff
    ).delete()[0]
    
    return f"Cleaned up {deleted_activities} activities and {deleted_daily} daily metrics"


@shared_task
def send_analytics_digest():
    """Send weekly analytics digest to administrators."""
    
    # Get the latest weekly metrics
    latest_weekly = SystemMetrics.objects.filter(
        period_type='weekly'
    ).order_by('-period_start').first()
    
    if not latest_weekly:
        return "No weekly metrics available"
    
    # Get admin users
    admin_users = User.objects.filter(role='admin', is_active=True)
    
    if not admin_users.exists():
        return "No admin users found"
    
    subject = f"Weekly Analytics Digest - {latest_weekly.period_start.strftime('%B %d, %Y')}"
    
    message = f"""
Weekly Analytics Report
Period: {latest_weekly.period_start.strftime('%B %d')} - {latest_weekly.period_end.strftime('%B %d, %Y')}

📊 User Metrics:
- Total Users: {latest_weekly.total_users}
- New Users: {latest_weekly.new_users}
- Average Active Users: {latest_weekly.active_users:.0f}

📚 Course Metrics:
- Total Courses: {latest_weekly.total_courses}
- New Courses: {latest_weekly.new_courses}
- Course Completions: {latest_weekly.course_completions}

📝 Test & Assessment:
- Test Attempts: {latest_weekly.test_attempts}
- Average Test Score: {latest_weekly.average_test_score:.1f}%

🏆 Achievements:
- Badges Awarded: {latest_weekly.badges_awarded}

📈 Performance:
- Overall Completion Rate: {latest_weekly.overall_completion_rate:.1f}%

Best regards,
Convade LMS Analytics System
    """
    
    sent_count = 0
    for admin in admin_users:
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [admin.email],
                fail_silently=True
            )
            sent_count += 1
        except Exception as e:
            print(f"Failed to send digest to {admin.email}: {str(e)}")
    
    return f"Sent analytics digest to {sent_count} administrators" 