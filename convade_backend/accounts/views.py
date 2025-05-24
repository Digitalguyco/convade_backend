from django.shortcuts import render
from django.db import models
from rest_framework import generics, permissions, status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.conf import settings
from .models import User, School, UserProfile, UserSession, Invitation, RegistrationCode
from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    ChangePasswordSerializer, SchoolSerializer, UserProfileSerializer,
    UserSessionSerializer, UserDetailSerializer, InvitationSerializer,
    CreateInvitationSerializer, InvitationRegistrationSerializer,
    RegistrationCodeSerializer, CreateRegistrationCodeSerializer,
    CodeRegistrationSerializer, EmailVerificationSerializer,
    ResendVerificationSerializer
)
from django.utils import timezone


# NOTE: RegisterView removed - open registration is a security risk
# Use InvitationRegistrationView or CodeRegistrationView instead

class LoginView(APIView):
    """User login endpoint."""
    
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer
    
    @extend_schema(
        tags=['Authentication'],
        request=LoginSerializer,
        summary='User login',
        description='Authenticate user with email and password.',
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Create user session
        import secrets
        from datetime import timedelta
        session_key = secrets.token_hex(20)  # Generate unique session key
        expires_at = timezone.now() + timedelta(hours=24)  # Session expires in 24 hours
        
        UserSession.objects.create(
            user=user,
            session_key=session_key,
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            expires_at=expires_at,
        )
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class LogoutView(APIView):
    """User logout endpoint."""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.Serializer  # Empty serializer for logout
    
    @extend_schema(
        tags=['Authentication'],
        summary='User logout',
        description='Logout user and invalidate refresh token.',
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Deactivate user sessions
            UserSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
            
            return Response({'message': 'Successfully logged out'})
        except Exception as e:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(generics.UpdateAPIView):
    """Change user password endpoint."""
    
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        tags=['Authentication'],
        summary='Change password',
        description='Change user password with old password verification.',
    )
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully'})


class UserListView(generics.ListAPIView):
    """List users endpoint."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(tags=['Users'], summary='List users')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        elif user.role == 'school_admin':
            return User.objects.filter(school=user.school)
        else:
            return User.objects.filter(id=user.id)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """User detail, update, delete endpoint."""
    
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(tags=['Users'], summary='Get user details')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(tags=['Users'], summary='Update user')
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(tags=['Users'], summary='Partially update user')
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(tags=['Users'], summary='Delete user')
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        elif user.role == 'school_admin':
            return User.objects.filter(school=user.school)
        else:
            return User.objects.filter(id=user.id)


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile management endpoint."""
    
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        tags=['Users'],
        summary='Get current user profile',
        description='Retrieve the current authenticated user profile.',
    )
    def get_object(self):
        return self.request.user


# NOTE: UserProfileView removed - redundant with ProfileView
# Use ProfileView for user profile management


class SchoolListView(generics.ListCreateAPIView):
    """List and create schools endpoint."""
    
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(tags=['Schools'], summary='List schools')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(tags=['Schools'], summary='Create school')
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return School.objects.all()
        elif user.role == 'school_admin':
            return School.objects.filter(id=user.school.id)
        else:
            return School.objects.filter(id=user.school.id)


class SchoolDetailView(generics.RetrieveUpdateDestroyAPIView):
    """School detail, update, delete endpoint."""
    
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(tags=['Schools'], summary='Get school details')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(tags=['Schools'], summary='Update school')
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(tags=['Schools'], summary='Partially update school')
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(tags=['Schools'], summary='Delete school')
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return School.objects.all()
        elif user.role == 'school_admin':
            return School.objects.filter(id=user.school.id)
        else:
            return School.objects.filter(id=user.school.id)


# NOTE: UserSessionView removed - administrative feature not needed for secure registration
# Session management can be handled through Django admin


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@extend_schema(
    tags=['Users'],
    summary='Current user info',
    description='Get current authenticated user information.',
)
def current_user(request):
    """Get current user information."""
    serializer = UserDetailSerializer(request.user)
    return Response(serializer.data)


# NOTE: deactivate_session removed - administrative feature not needed for secure registration
# Session management can be handled through Django admin


# Secure Registration Views

class InvitationListView(generics.ListCreateAPIView):
    """List and create invitations."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateInvitationSerializer
        return InvitationSerializer
    
    @extend_schema(
        tags=['Invitations'],
        summary='List invitations',
        description='Get all invitations sent by the current user or their school.',
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Invitations'],
        summary='Create invitation',
        description='Send an invitation to register a new user.',
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        
        # Send invitation email
        self.send_invitation_email(invitation)
        
        return Response(
            InvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED
        )
    
    def get_queryset(self):
        user = self.request.user
        
        # Handle schema generation and anonymous users
        if getattr(self, 'swagger_fake_view', False):
            return Invitation.objects.none()
        
        if not user.is_authenticated:
            return Invitation.objects.none()
        
        if user.role == 'admin':
            return Invitation.objects.all()
        elif user.role == 'teacher':
            # Teachers can see invitations for their school
            return Invitation.objects.filter(school__userprofile__user=user)
        else:
            # Students typically can't see invitations
            return Invitation.objects.none()
    
    def send_invitation_email(self, invitation):
        """Send invitation email to the user."""
        try:
            registration_link = f"{settings.FRONTEND_URL}/register/invitation/{invitation.token}"
            
            send_mail(
                subject=f'Invitation to join {invitation.school.name} on Convade LMS',
                message=f'''
Hello,

You have been invited to join {invitation.school.name} as a {invitation.get_role_display()} on Convade LMS.

To complete your registration, please click the link below:
{registration_link}

This invitation will expire on {invitation.expires_at.strftime('%B %d, %Y at %I:%M %p')}.

If you have any questions, please contact your administrator.

Best regards,
The Convade LMS Team
                '''.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                fail_silently=True,
            )
        except Exception as e:
            # Log the error but don't fail the invitation creation
            print(f"Failed to send invitation email: {e}")


class InvitationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an invitation."""
    
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(tags=['Invitations'], summary='Get invitation details')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(tags=['Invitations'], summary='Update invitation')
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(tags=['Invitations'], summary='Delete invitation')
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Invitation.objects.all()
        elif user.role == 'teacher':
            return Invitation.objects.filter(
                models.Q(invited_by=user) | 
                models.Q(school__userprofile__user=user)
            )
        else:
            return Invitation.objects.filter(invited_by=user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@extend_schema(
    tags=['Invitations'],
    summary='Revoke invitation',
    description='Revoke a pending invitation.',
)
def revoke_invitation(request, invitation_id):
    """Revoke a pending invitation."""
    try:
        invitation = Invitation.objects.get(
            id=invitation_id,
            invited_by=request.user,
            status=Invitation.PENDING
        )
        invitation.revoke()
        return Response({'message': 'Invitation revoked successfully'})
    except Invitation.DoesNotExist:
        return Response(
            {'error': 'Invitation not found or cannot be revoked'}, 
            status=status.HTTP_404_NOT_FOUND
        )


class InvitationRegistrationView(generics.CreateAPIView):
    """Register using an invitation token."""
    
    serializer_class = InvitationRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        tags=['Authentication'],
        summary='Register via invitation',
        description='Complete registration using an invitation token.',
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate email verification token
        import secrets
        user.email_verification_token = secrets.token_urlsafe(32)
        user.save()
        
        # Send welcome and verification email
        self.send_welcome_email(user)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Registration successful. Please check your email to verify your account.'
        }, status=status.HTTP_201_CREATED)
    
    def send_welcome_email(self, user):
        """Send welcome and verification email."""
        try:
            verification_link = f"{settings.FRONTEND_URL}/verify-email/{user.email_verification_token}"
            
            send_mail(
                subject='Welcome to Convade LMS - Please verify your email',
                message=f'''
Welcome to Convade LMS, {user.first_name}!

Your account has been successfully created. To complete the setup, please verify your email address by clicking the link below:

{verification_link}

If you have any questions, please don't hesitate to contact us.

Best regards,
The Convade LMS Team
                '''.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send welcome email: {e}")


class RegistrationCodeListView(generics.ListCreateAPIView):
    """List and create registration codes."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateRegistrationCodeSerializer
        return RegistrationCodeSerializer
    
    @extend_schema(
        tags=['Registration Codes'],
        summary='List registration codes',
        description='Get all registration codes for the user\'s school.',
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Registration Codes'],
        summary='Create registration code',
        description='Create a new registration code for a school.',
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        
        # Handle schema generation and anonymous users
        if getattr(self, 'swagger_fake_view', False):
            return RegistrationCode.objects.none()
        
        if not user.is_authenticated:
            return RegistrationCode.objects.none()
        
        if user.role == 'admin':
            return RegistrationCode.objects.all()
        elif user.role == 'teacher':
            # Teachers can see codes for their school
            return RegistrationCode.objects.filter(school__userprofile__user=user)
        else:
            # Students typically can't see registration codes
            return RegistrationCode.objects.none()


class RegistrationCodeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a registration code."""
    
    queryset = RegistrationCode.objects.all()
    serializer_class = RegistrationCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(tags=['Registration Codes'], summary='Get registration code details')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(tags=['Registration Codes'], summary='Update registration code')
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(tags=['Registration Codes'], summary='Delete registration code')
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return RegistrationCode.objects.all()
        elif user.role == 'teacher':
            return RegistrationCode.objects.filter(school__userprofile__user=user)
        else:
            return RegistrationCode.objects.none()


class CodeRegistrationView(generics.CreateAPIView):
    """Register using a registration code."""
    
    serializer_class = CodeRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        tags=['Authentication'],
        summary='Register via code',
        description='Complete registration using a registration code.',
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate email verification token
        import secrets
        user.email_verification_token = secrets.token_urlsafe(32)
        user.save()
        
        # Send welcome and verification email
        self.send_welcome_email(user)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Registration successful. Please check your email to verify your account.'
        }, status=status.HTTP_201_CREATED)
    
    def send_welcome_email(self, user):
        """Send welcome and verification email."""
        try:
            verification_link = f"{settings.FRONTEND_URL}/verify-email/{user.email_verification_token}"
            
            send_mail(
                subject='Welcome to Convade LMS - Please verify your email',
                message=f'''
Welcome to Convade LMS, {user.first_name}!

Your account has been successfully created. To complete the setup, please verify your email address by clicking the link below:

{verification_link}

If you have any questions, please don't hesitate to contact us.

Best regards,
The Convade LMS Team
                '''.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send welcome email: {e}")


class EmailVerificationView(APIView):
    """Email verification endpoint."""
    
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailVerificationSerializer
    
    @extend_schema(
        tags=['Authentication'],
        request=EmailVerificationSerializer,
        summary='Verify email address',
        description='Verify user email address using verification token.',
    )
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'message': 'Email verified successfully',
            'user': UserSerializer(user).data
        })


class ResendVerificationView(APIView):
    """Resend email verification endpoint."""
    
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendVerificationSerializer
    
    @extend_schema(
        tags=['Authentication'],
        request=ResendVerificationSerializer,
        summary='Resend verification email',
        description='Resend email verification link to user.',
    )
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email
        self.send_verification_email(user)
        
        return Response({
            'message': 'Verification email sent successfully'
        })
    
    def send_verification_email(self, user):
        """Send verification email."""
        try:
            verification_link = f"{settings.FRONTEND_URL}/verify-email/{user.email_verification_token}"
            
            send_mail(
                subject='Verify your email address - Convade LMS',
                message=f'''
Hello {user.first_name},

Please verify your email address by clicking the link below:

{verification_link}

If you didn't request this verification, please ignore this email.

Best regards,
The Convade LMS Team
                '''.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send verification email: {e}")


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@extend_schema(
    tags=['Registration Codes'],
    summary='Validate registration code',
    description='Check if a registration code is valid without using it.',
)
def validate_registration_code(request, code):
    """Validate a registration code without using it."""
    try:
        reg_code = RegistrationCode.objects.get(code=code.upper())
        is_valid = reg_code.is_valid()
        
        return Response({
            'valid': is_valid,
            'school_name': reg_code.school.name if is_valid else None,
            'role': reg_code.get_role_display() if is_valid else None,
            'max_uses': reg_code.max_uses if is_valid else None,
            'current_uses': reg_code.current_uses if is_valid else None,
            'expires_at': reg_code.expires_at if is_valid else None,
        })
    except RegistrationCode.DoesNotExist:
        return Response({
            'valid': False,
            'message': 'Registration code not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@extend_schema(
    tags=['Invitations'],
    summary='Validate invitation token',
    description='Check if an invitation token is valid.',
)
def validate_invitation_token(request, token):
    """Validate an invitation token."""
    try:
        invitation = Invitation.objects.get(token=token)
        is_valid = invitation.is_valid()
        
        return Response({
            'valid': is_valid,
            'email': invitation.email if is_valid else None,
            'school_name': invitation.school.name if is_valid else None,
            'role': invitation.get_role_display() if is_valid else None,
            'expires_at': invitation.expires_at if is_valid else None,
        })
    except Invitation.DoesNotExist:
        return Response({
            'valid': False,
            'message': 'Invitation token not found'
        }, status=status.HTTP_404_NOT_FOUND)
