from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from .models import User, School, UserProfile, UserSession, Invitation, RegistrationCode


class SchoolSerializer(serializers.ModelSerializer):
    """Serializer for School model."""
    
    class Meta:
        model = School
        fields = [
            'id', 'name', 'code', 'address', 'city', 'state', 'country',
            'postal_code', 'phone', 'email', 'website', 'established_date',
            'school_type', 'timezone', 'academic_year_start', 'academic_year_end',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'school', 'student_id', 'enrollment_date', 'graduation_date',
            'employee_id', 'hire_date', 'subjects', 'qualifications',
            'current_year', 'gpa', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'preferred_learning_style',
            'linkedin_url', 'twitter_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with profile information."""
    
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'school_id', 'grade_level', 'department',
            'is_active', 'is_email_verified', 'date_joined', 'last_login',
            'profile'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    @extend_schema_field(serializers.CharField)
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'school_id'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password.')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for UserSession model."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserSession
        fields = [
            'user', 'user_email', 'session_key', 'ip_address',
            'user_agent', 'browser', 'operating_system', 'device_type',
            'is_active', 'created_at', 'last_activity', 'expires_at'
        ]
        read_only_fields = ['created_at', 'last_activity']


class UserDetailSerializer(UserSerializer):
    """Detailed serializer for User model with additional information."""
    
    sessions = UserSessionSerializer(many=True, read_only=True)
    total_courses = serializers.SerializerMethodField()
    completed_courses = serializers.SerializerMethodField()
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'sessions', 'total_courses', 'completed_courses'
        ]
    
    @extend_schema_field(serializers.IntegerField)
    def get_total_courses(self, obj):
        # TODO: Implement when course models are available
        return 0
    
    @extend_schema_field(serializers.IntegerField)
    def get_completed_courses(self, obj):
        # TODO: Implement when course models are available
        return 0


class InvitationSerializer(serializers.ModelSerializer):
    """Serializer for Invitation model."""
    
    invited_by_name = serializers.CharField(source='invited_by.full_name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'email', 'role', 'school', 'school_name', 'token', 'status',
            'invited_by', 'invited_by_name', 'created_at', 'expires_at',
            'accepted_at', 'accepted_by', 'additional_data', 'is_valid'
        ]
        read_only_fields = [
            'id', 'token', 'invited_by', 'created_at', 'accepted_at', 
            'accepted_by', 'is_valid'
        ]
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_valid(self, obj):
        return obj.is_valid()


class CreateInvitationSerializer(serializers.ModelSerializer):
    """Serializer for creating invitations."""
    
    expires_in_days = serializers.IntegerField(default=7, min_value=1, max_value=30)
    
    class Meta:
        model = Invitation
        fields = ['email', 'role', 'school', 'expires_in_days', 'additional_data']
    
    def validate_email(self, value):
        """Check if user with this email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value
    
    def validate(self, attrs):
        """Check for existing pending invitations."""
        email = attrs['email']
        school = attrs['school']
        
        # Check for existing pending invitation
        existing = Invitation.objects.filter(
            email=email,
            school=school,
            status=Invitation.PENDING
        ).exists()
        
        if existing:
            raise serializers.ValidationError(
                "A pending invitation already exists for this email at this school."
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create invitation with token."""
        expires_in_days = validated_data.pop('expires_in_days', 7)
        invited_by = self.context['request'].user
        
        return Invitation.create_invitation(
            invited_by=invited_by,
            expires_in_days=expires_in_days,
            **validated_data
        )


class InvitationRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for registration via invitation."""
    
    invitation_token = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'invitation_token', 'password', 'password_confirm',
            'first_name', 'last_name'
        ]
    
    def validate_invitation_token(self, value):
        """Validate invitation token and check if it's still valid."""
        try:
            invitation = Invitation.objects.get(token=value)
        except Invitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation token.")
        
        if not invitation.is_valid():
            raise serializers.ValidationError("Invitation has expired or is no longer valid.")
        
        # Check if user with this email already exists
        if User.objects.filter(email=invitation.email).exists():
            raise serializers.ValidationError("User with this email already exists.")
        
        self.invitation = invitation
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        """Create user from invitation."""
        validated_data.pop('password_confirm')
        validated_data.pop('invitation_token')
        password = validated_data.pop('password')
        
        # Create user with invitation details
        user = User.objects.create_user(
            email=self.invitation.email,
            role=self.invitation.role,
            **validated_data
        )
        user.set_password(password)
        
        # Link to school if available
        if hasattr(self.invitation.school, 'userprofile'):
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            user_profile.school = self.invitation.school
            user_profile.save()
        
        user.save()
        
        # Mark invitation as accepted
        self.invitation.accept(user)
        
        return user


class RegistrationCodeSerializer(serializers.ModelSerializer):
    """Serializer for RegistrationCode model."""
    
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    is_valid = serializers.SerializerMethodField()
    usage_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = RegistrationCode
        fields = [
            'id', 'code', 'school', 'school_name', 'role', 'max_uses',
            'current_uses', 'usage_percentage', 'status', 'expires_at',
            'created_by', 'created_by_name', 'created_at', 'grade_level',
            'department', 'is_valid'
        ]
        read_only_fields = [
            'id', 'code', 'created_by', 'created_at', 'current_uses', 'is_valid'
        ]
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_valid(self, obj):
        return obj.is_valid()
    
    @extend_schema_field(serializers.FloatField)
    def get_usage_percentage(self, obj):
        if obj.max_uses == 0:
            return 0.0
        return (obj.current_uses / obj.max_uses) * 100


class CreateRegistrationCodeSerializer(serializers.ModelSerializer):
    """Serializer for creating registration codes."""
    
    class Meta:
        model = RegistrationCode
        fields = [
            'school', 'role', 'max_uses', 'expires_at',
            'grade_level', 'department'
        ]
    
    def create(self, validated_data):
        """Create registration code with auto-generated code."""
        created_by = self.context['request'].user
        return RegistrationCode.generate_code(
            created_by=created_by,
            **validated_data
        )


class CodeRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for registration via registration code."""
    
    registration_code = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'registration_code', 'email', 'password', 'password_confirm',
            'first_name', 'last_name'
        ]
    
    def validate_registration_code(self, value):
        """Validate registration code and check if it's still valid."""
        try:
            code = RegistrationCode.objects.get(code=value.upper())
        except RegistrationCode.DoesNotExist:
            raise serializers.ValidationError("Invalid registration code.")
        
        if not code.is_valid():
            raise serializers.ValidationError("Registration code has expired or is no longer valid.")
        
        self.registration_code = code
        return value
    
    def validate_email(self, value):
        """Check if user with this email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        """Create user from registration code."""
        validated_data.pop('password_confirm')
        validated_data.pop('registration_code')
        password = validated_data.pop('password')
        
        # Create user with code details
        user = User.objects.create_user(
            role=self.registration_code.role,
            **validated_data
        )
        user.set_password(password)
        
        # Link to school and set additional fields from code
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        user_profile.school = self.registration_code.school
        if self.registration_code.grade_level:
            user.grade_level = self.registration_code.grade_level
        if self.registration_code.department:
            user.department = self.registration_code.department
        
        user.save()
        user_profile.save()
        
        # Use the registration code
        self.registration_code.use_code()
        
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification."""
    
    token = serializers.CharField()
    
    def validate_token(self, value):
        """Validate email verification token."""
        try:
            user = User.objects.get(
                email_verification_token=value,
                is_email_verified=False
            )
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired verification token.")
        
        self.user = user
        return value
    
    def save(self):
        """Mark user email as verified."""
        self.user.is_email_verified = True
        self.user.email_verification_token = None
        self.user.save(update_fields=['is_email_verified', 'email_verification_token'])
        return self.user


class ResendVerificationSerializer(serializers.Serializer):
    """Serializer for resending email verification."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Check if user exists and needs verification."""
        try:
            user = User.objects.get(email=value, is_email_verified=False)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "User not found or email already verified."
            )
        
        self.user = user
        return value
    
    def save(self):
        """Generate new verification token and return user."""
        import secrets
        self.user.email_verification_token = secrets.token_urlsafe(32)
        self.user.save(update_fields=['email_verification_token'])
        return self.user 