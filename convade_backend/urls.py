"""
URL configuration for Convade LMS backend.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from . import views

urlpatterns = [
    # Documentation routes
    path('', views.documentation_index, name='docs-index'),
    path('docs/', views.documentation_index, name='docs-home'),
    path('docs/api/', views.api_documentation, name='api-docs'),
    path('docs/setup/', views.documentation_readme, name='setup-docs'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/tests/', include('tests.urls')),
    
    # Social Authentication
    path('auth/', include('social_django.urls', namespace='social')),
    path('api/auth/', include('accounts.social_urls')),  # Custom social auth API endpoints
    
    # path('api/badges/', include('badges.urls')),
    # path('api/notifications/', include('notifications_app.urls')),
    # path('api/payments/', include('payments.urls')),
    # path('api/certifications/', include('certifications.urls')),
    # path('api/analytics/', include('analytics.urls')),
    # path('api/help/', include('helpcenter.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
