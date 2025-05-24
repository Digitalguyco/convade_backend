from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid


class UserManager(BaseUserManager):
    """Custom user manager for the User model."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for Convade LMS."""
    
    # User role choices
    STUDENT = 'student'
    TEACHER = 'teacher'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (TEACHER, 'Teacher'),
        (ADMIN, 'Admin'),
    ]
    
    # Account status choices
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
        (SUSPENDED, 'Suspended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ACTIVE)
    
    # School and academic information
    school_id = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[RegexValidator(
            regex=r'^[A-Z0-9]{4,20}$',
            message='School ID must be 4-20 alphanumeric characters'
        )]
    )
    grade_level = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    # Profile information
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message='Phone number must be valid format'
        )]
    )
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profiles/%Y/%m/', 
        blank=True, 
        null=True
    )
    bio = models.TextField(max_length=500, blank=True, null=True)
    
    # Authentication and verification
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_expires = models.DateTimeField(blank=True, null=True)
    
    # Social login
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    
    # Account management
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    last_activity = models.DateTimeField(default=timezone.now)
    
    # Preferences
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['school_id']),
            models.Index(fields=['status']),
            models.Index(fields=['date_joined']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_full_name(self):
        """Return the user's full name (method version for compatibility)."""
        return self.full_name
    
    @property
    def is_student(self):
        """Check if user is a student."""
        return self.role == self.STUDENT
    
    @property
    def is_teacher(self):
        """Check if user is a teacher."""
        return self.role == self.TEACHER
    
    @property
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == self.ADMIN
    
    def get_absolute_url(self):
        """Return the absolute URL for the user."""
        return f"/users/{self.id}/"
    
    def update_last_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


class School(models.Model):
    """Model for educational institutions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True, db_index=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Contact information
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    
    # School details
    established_date = models.DateField(blank=True, null=True)
    school_type = models.CharField(
        max_length=50,
        choices=[
            ('public', 'Public'),
            ('private', 'Private'),
            ('charter', 'Charter'),
            ('international', 'International'),
        ],
        default='public'
    )
    
    # Settings
    is_active = models.BooleanField(default=True)
    timezone = models.CharField(max_length=50, default='UTC')
    academic_year_start = models.DateField()
    academic_year_end = models.DateField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_school'
        verbose_name = 'School'
        verbose_name_plural = 'Schools'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class UserProfile(models.Model):
    """Extended profile information for users."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    school = models.ForeignKey(School, on_delete=models.CASCADE, blank=True, null=True)
    
    # Student-specific fields
    student_id = models.CharField(max_length=20, blank=True, null=True)
    enrollment_date = models.DateField(blank=True, null=True)
    graduation_date = models.DateField(blank=True, null=True)
    
    # Teacher-specific fields
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    hire_date = models.DateField(blank=True, null=True)
    subjects = models.JSONField(default=list, blank=True)  # List of subjects taught
    qualifications = models.TextField(blank=True, null=True)
    
    # Academic information
    current_year = models.CharField(max_length=20, blank=True, null=True)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, null=True)
    
    # Preferences and settings
    preferred_learning_style = models.CharField(
        max_length=20,
        choices=[
            ('visual', 'Visual'),
            ('auditory', 'Auditory'),
            ('kinesthetic', 'Kinesthetic'),
            ('reading', 'Reading/Writing'),
        ],
        blank=True,
        null=True
    )
    
    # Social links
    linkedin_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_user_profile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['employee_id']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} Profile"


class UserSession(models.Model):
    """Track user sessions for analytics and security."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50, blank=True, null=True)
    browser = models.CharField(max_length=100, blank=True, null=True)
    operating_system = models.CharField(max_length=100, blank=True, null=True)
    
    # Session timing
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'accounts_user_session'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address} ({self.created_at})"


class Invitation(models.Model):
    """Invitation system for secure user registration."""
    
    # Invitation status
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    EXPIRED = 'expired'
    REVOKED = 'revoked'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (EXPIRED, 'Expired'),
        (REVOKED, 'Revoked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Invitation details
    email = models.EmailField(db_index=True)
    role = models.CharField(max_length=10, choices=User.ROLE_CHOICES)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='invitations')
    
    # Invitation token and security
    token = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    
    # Who sent the invitation
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(blank=True, null=True)
    
    # The user who accepted (if any)
    accepted_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        related_name='accepted_invitations'
    )
    
    # Additional data for invitation
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'accounts_invitation'
        verbose_name = 'Invitation'
        verbose_name_plural = 'Invitations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['invited_by']),
        ]
        unique_together = ['email', 'school', 'status']  # Prevent duplicate pending invitations
    
    def __str__(self):
        return f"Invitation for {self.email} as {self.get_role_display()} at {self.school.name}"
    
    def is_valid(self):
        """Check if invitation is still valid."""
        return (
            self.status == self.PENDING and 
            self.expires_at > timezone.now()
        )
    
    def expire(self):
        """Mark invitation as expired."""
        self.status = self.EXPIRED
        self.save(update_fields=['status'])
    
    def revoke(self):
        """Revoke the invitation."""
        self.status = self.REVOKED
        self.save(update_fields=['status'])
    
    def accept(self, user):
        """Mark invitation as accepted by user."""
        self.status = self.ACCEPTED
        self.accepted_by = user
        self.accepted_at = timezone.now()
        self.save(update_fields=['status', 'accepted_by', 'accepted_at'])
    
    @classmethod
    def create_invitation(cls, email, role, school, invited_by, expires_in_days=7, **additional_data):
        """Create a new invitation with token."""
        import secrets
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Set expiration
        expires_at = timezone.now() + timezone.timedelta(days=expires_in_days)
        
        invitation = cls.objects.create(
            email=email,
            role=role,
            school=school,
            invited_by=invited_by,
            token=token,
            expires_at=expires_at,
            additional_data=additional_data
        )
        
        return invitation


class RegistrationCode(models.Model):
    """School-specific registration codes for student self-registration."""
    
    # Code status
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    EXPIRED = 'expired'
    
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
        (EXPIRED, 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Code details
    code = models.CharField(max_length=20, unique=True, db_index=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='registration_codes')
    
    # Usage restrictions
    role = models.CharField(max_length=10, choices=User.ROLE_CHOICES, default=User.STUDENT)
    max_uses = models.PositiveIntegerField(default=0)  # 0 = unlimited
    current_uses = models.PositiveIntegerField(default=0)
    
    # Status and timing
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ACTIVE)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    # Who created it
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_registration_codes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Additional settings
    grade_level = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'accounts_registration_code'
        verbose_name = 'Registration Code'
        verbose_name_plural = 'Registration Codes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['school', 'status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.school.name} ({self.get_status_display()})"
    
    def is_valid(self):
        """Check if registration code is valid for use."""
        if self.status != self.ACTIVE:
            return False
        
        if self.expires_at and self.expires_at < timezone.now():
            return False
        
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False
        
        return True
    
    def use_code(self):
        """Increment usage count when code is used."""
        self.current_uses += 1
        self.save(update_fields=['current_uses'])
        
        # Auto-expire if max uses reached
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            self.status = self.EXPIRED
            self.save(update_fields=['status'])
    
    @classmethod
    def generate_code(cls, school, created_by, length=8, **kwargs):
        """Generate a random registration code."""
        import secrets
        import string
        
        # Generate random code
        alphabet = string.ascii_uppercase + string.digits
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Ensure uniqueness
        while cls.objects.filter(code=code).exists():
            code = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        return cls.objects.create(
            code=code,
            school=school,
            created_by=created_by,
            **kwargs
        )
