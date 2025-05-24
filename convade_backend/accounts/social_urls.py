"""
Social Authentication URLs for Convade LMS API
"""
from django.urls import path
from . import social_views

urlpatterns = [
    # Social Auth API endpoints
    path('social-login/', social_views.SocialLoginView.as_view(), name='social-login'),
    path('social-providers/', social_views.SocialProvidersView.as_view(), name='social-providers'),
    path('social-disconnect/<str:provider>/', social_views.SocialDisconnectView.as_view(), name='social-disconnect'),
    path('social-connect/<str:provider>/', social_views.SocialConnectView.as_view(), name='social-connect'),
] 