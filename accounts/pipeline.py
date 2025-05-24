"""
Custom Social Authentication Pipeline for Convade LMS
"""
import requests
from django.core.files.base import ContentFile
from accounts.models import UserProfile


def save_profile_picture(strategy, details, user=None, *args, **kwargs):
    """
    Save profile picture from social auth provider
    """
    if user and hasattr(user, 'profile'):
        profile = user.profile
        
        # Get profile picture URL from different providers
        picture_url = None
        
        # Google
        if 'google-oauth2' in strategy.request.path:
            picture_url = kwargs.get('response', {}).get('picture')
        
        # GitHub  
        elif 'github' in strategy.request.path:
            picture_url = kwargs.get('response', {}).get('avatar_url')
        
        # LinkedIn
        elif 'linkedin' in strategy.request.path:
            picture_urls = kwargs.get('response', {}).get('pictureUrl', {})
            if picture_urls and 'displayImage' in picture_urls:
                picture_url = picture_urls['displayImage']
        
        # Facebook
        elif 'facebook' in strategy.request.path:
            picture_data = kwargs.get('response', {}).get('picture', {})
            if picture_data and 'data' in picture_data:
                picture_url = picture_data['data'].get('url')
        
        # Download and save profile picture
        if picture_url and not profile.profile_picture:
            try:
                response = requests.get(picture_url, timeout=10)
                if response.status_code == 200:
                    filename = f"profile_{user.id}.jpg"
                    profile.profile_picture.save(
                        filename,
                        ContentFile(response.content),
                        save=True
                    )
            except Exception as e:
                # Log the error but don't break the authentication flow
                print(f"Failed to save profile picture: {e}")
        
        # Update profile fields if empty
        if not profile.bio and details.get('bio'):
            profile.bio = details.get('bio', '')
        
        if not profile.location and details.get('location'):
            profile.location = details.get('location', '')
        
        profile.save()


def update_user_details(strategy, details, user=None, *args, **kwargs):
    """
    Update user details from social auth provider
    """
    if user:
        # Update first name if empty
        if not user.first_name and details.get('first_name'):
            user.first_name = details.get('first_name', '')
        
        # Update last name if empty  
        if not user.last_name and details.get('last_name'):
            user.last_name = details.get('last_name', '')
        
        # Update email if empty
        if not user.email and details.get('email'):
            user.email = details.get('email', '')
        
        user.save()


def create_user_profile(strategy, details, user=None, *args, **kwargs):
    """
    Ensure user has a profile after social auth
    """
    if user:
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created:
            # Set some default values for new social auth users
            profile.notification_preferences = {
                'email_notifications': True,
                'course_updates': True,
                'achievement_alerts': True,
            }
            profile.save() 