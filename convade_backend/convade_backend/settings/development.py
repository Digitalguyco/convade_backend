"""
Development settings for Convade LMS backend.
"""
from .base import *

# Debug settings
DEBUG = True

# Database - Using SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Additional development apps
INSTALLED_APPS += [
    'django_extensions',
    # 'debug_toolbar',  # Commented out for now
]

# MIDDLEWARE += [
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
# ]

# Debug toolbar configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Disable caching in development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Logging for development - commented out for now
# LOGGING['handlers']['console']['level'] = 'DEBUG'
# LOGGING['loggers']['convade']['level'] = 'DEBUG'

# Media files served by Django in development
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' 