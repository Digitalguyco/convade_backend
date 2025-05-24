"""
Social Authentication API Views for Convade LMS
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from django.contrib.auth import authenticate, login
from django.conf import settings
from social_django.models import UserSocialAuth
from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthException
from accounts.models import User
from drf_spectacular.utils import extend_schema, OpenApiResponse
import requests


class SocialProvidersResponseSerializer(serializers.Serializer):
    """Response serializer for social providers endpoint."""
    providers = serializers.ListField(child=serializers.DictField())
    total = serializers.IntegerField()
    message = serializers.CharField()


class SocialLoginRequestSerializer(serializers.Serializer):
    """Request serializer for social login."""
    provider = serializers.CharField()
    code = serializers.CharField()
    redirect_uri = serializers.CharField()


class SocialLoginResponseSerializer(serializers.Serializer):
    """Response serializer for social login."""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.DictField()


class SocialConnectResponseSerializer(serializers.Serializer):
    """Response serializer for social connect."""
    auth_url = serializers.CharField()
    message = serializers.CharField()


class SocialDisconnectResponseSerializer(serializers.Serializer):
    """Response serializer for social disconnect."""
    message = serializers.CharField()


class SocialProvidersView(APIView):
    """
    Get available social authentication providers
    """
    permission_classes = [AllowAny]
    serializer_class = SocialProvidersResponseSerializer
    
    @extend_schema(
        summary="Get available social authentication providers",
        description="Returns a list of configured social authentication providers",
        responses={
            200: SocialProvidersResponseSerializer,
        }
    )
    def get(self, request):
        """Return list of configured social auth providers"""
        providers = []
        
        # Google OAuth2 - Only provider we support
        if settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY:
            providers.append({
                'name': 'google-oauth2',
                'display_name': 'Google',
                'icon': 'fab fa-google',
                'color': '#db4437',
                'auth_url': '/auth/login/google-oauth2/'
            })
        
        return Response({
            'providers': providers,
            'total': len(providers),
            'message': 'Convade LMS supports secure login with Google'
        })


class SocialLoginView(APIView):
    """
    Handle social authentication login
    """
    permission_classes = [AllowAny]
    serializer_class = SocialLoginRequestSerializer
    
    @extend_schema(
        summary="Social authentication login",
        description="Exchange social auth code for JWT tokens",
        request=SocialLoginRequestSerializer,
        responses={
            200: SocialLoginResponseSerializer,
            400: OpenApiResponse(description="Bad request"),
            401: OpenApiResponse(description="Authentication failed"),
        }
    )
    def post(self, request):
        """
        Exchange social auth code for JWT tokens
        """
        serializer = SocialLoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        provider = serializer.validated_data['provider']
        code = serializer.validated_data['code']
        redirect_uri = serializer.validated_data['redirect_uri']
        
        try:
            # Get user from social auth
            user = self._authenticate_social_user(provider, code, redirect_uri)
            
            if user:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token
                
                # Get user profile data
                profile_data = {}
                if hasattr(user, 'profile'):
                    profile = user.profile
                    profile_data = {
                        'bio': profile.bio,
                        'location': profile.location,
                        'profile_picture': profile.profile_picture.url if profile.profile_picture else None,
                    }
                
                return Response({
                    'access': str(access_token),
                    'refresh': str(refresh),
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'profile': profile_data
                    }
                })
            else:
                return Response({
                    'error': 'Authentication failed'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            return Response({
                'error': f'Social authentication failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _authenticate_social_user(self, provider, code, redirect_uri):
        """
        Authenticate user using social auth backend
        """
        # This is a simplified implementation
        # In production, you'd want to use the social-auth-app-django
        # backend system properly
        
        # For now, return None - this needs to be implemented
        # based on your frontend architecture
        return None


class SocialConnectView(APIView):
    """
    Connect Google account to existing user
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SocialConnectResponseSerializer
    
    @extend_schema(
        summary="Connect social account",
        description="Connect a Google account to the current user",
        responses={
            200: SocialConnectResponseSerializer,
            400: OpenApiResponse(description="Bad request"),
        }
    )
    def post(self, request, provider):
        """Connect a Google account to the current user"""
        
        # Only Google is supported
        if provider != 'google-oauth2':
            return Response({
                'error': f'Provider {provider} not supported. Only Google OAuth2 is available.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already has Google connected
        existing_social = UserSocialAuth.objects.filter(
            user=request.user,
            provider='google-oauth2'
        ).first()
        
        if existing_social:
            return Response({
                'error': 'You already have a Google account connected'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Return URL for Google connection
        auth_url = f"{settings.FRONTEND_URL}/auth/google-oauth2/?connect=true"
        
        return Response({
            'auth_url': auth_url,
            'message': 'Redirect to Google to connect your account'
        })


class SocialDisconnectView(APIView):
    """
    Disconnect social account from user
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SocialDisconnectResponseSerializer
    
    @extend_schema(
        summary="Disconnect social account",
        description="Disconnect a social account from the current user",
        responses={
            200: SocialDisconnectResponseSerializer,
            400: OpenApiResponse(description="Bad request"),
            404: OpenApiResponse(description="Social account not found"),
        }
    )
    def delete(self, request, provider):
        """Disconnect a social account from the current user"""
        
        try:
            social_auth = UserSocialAuth.objects.get(
                user=request.user,
                provider=provider
            )
            
            # Don't allow disconnecting if it's the only auth method and no password set
            if not request.user.has_usable_password():
                other_social_accounts = UserSocialAuth.objects.filter(
                    user=request.user
                ).exclude(id=social_auth.id).count()
                
                if other_social_accounts == 0:
                    return Response({
                        'error': 'Cannot disconnect your only authentication method. Please set a password first.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            social_auth.delete()
            
            return Response({
                'message': f'Successfully disconnected {provider} account'
            })
            
        except UserSocialAuth.DoesNotExist:
            return Response({
                'error': f'No {provider} account connected'
            }, status=status.HTTP_404_NOT_FOUND) 