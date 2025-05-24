from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

app_name = 'accounts'

# Router for ViewSets (currently empty, but ready for future use)
router = DefaultRouter()

# Essential API URL patterns for secure registration system
urlpatterns = [
    # Core Authentication endpoints
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # Secure Registration endpoints
    path('auth/register/invitation/', views.InvitationRegistrationView.as_view(), name='invitation-register'),
    path('auth/register/code/', views.CodeRegistrationView.as_view(), name='code-register'),
    path('auth/verify-email/', views.EmailVerificationView.as_view(), name='verify-email'),
    path('auth/resend-verification/', views.ResendVerificationView.as_view(), name='resend-verification'),
    
    # Invitation Management (for admins/teachers)
    path('invitations/', views.InvitationListView.as_view(), name='invitation-list'),
    path('invitations/<uuid:pk>/', views.InvitationDetailView.as_view(), name='invitation-detail'),
    path('invitations/<uuid:invitation_id>/revoke/', views.revoke_invitation, name='invitation-revoke'),
    path('invitations/validate/<str:token>/', views.validate_invitation_token, name='invitation-validate'),
    
    # Registration Code Management (for admins/teachers)
    path('registration-codes/', views.RegistrationCodeListView.as_view(), name='registration-code-list'),
    path('registration-codes/<uuid:pk>/', views.RegistrationCodeDetailView.as_view(), name='registration-code-detail'),
    path('registration-codes/validate/<str:code>/', views.validate_registration_code, name='registration-code-validate'),
    
    # Essential User Management
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<uuid:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/current/', views.current_user, name='current-user'),
    
    # School Management
    path('schools/', views.SchoolListView.as_view(), name='school-list'),
    path('schools/<uuid:pk>/', views.SchoolDetailView.as_view(), name='school-detail'),
    
    # JWT Token Management
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Include router URLs (for future expansion)
    path('', include(router.urls)),
] 