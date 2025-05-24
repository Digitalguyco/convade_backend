"""
Django settings for convade_backend project.
This file imports environment-specific settings.
"""
import os
from decouple import config

# Determine which settings to use based on environment
ENVIRONMENT = config('ENVIRONMENT', default='development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'staging':
    from .production import *  # Use production settings with different configs
else:
    from .development import *
