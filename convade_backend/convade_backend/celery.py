"""
Celery configuration for Convade LMS backend.
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
# This will be overridden by environment variables when needed
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'convade_backend.settings.development')

app = Celery('convade_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'send-test-reminders': {
        'task': 'tests.tasks.send_test_reminders',
        'schedule': 300.0,  # Every 5 minutes
    },
    'update-badge-progress': {
        'task': 'badges.tasks.update_badge_progress',
        'schedule': 600.0,  # Every 10 minutes
    },
    'cleanup-expired-sessions': {
        'task': 'accounts.tasks.cleanup_expired_sessions',
        'schedule': 3600.0,  # Every hour
    },
    'generate-analytics-reports': {
        'task': 'analytics.tasks.generate_daily_reports',
        'schedule': 86400.0,  # Daily
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 