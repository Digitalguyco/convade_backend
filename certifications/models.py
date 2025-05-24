from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from accounts.models import User
from courses.models import Course, Enrollment
from tests.models import TestResult
import uuid
import hashlib


class CertificateTemplate(models.Model):
    """Templates for certificate generation."""
    
    # Template types
    COURSE_COMPLETION = 'course_completion'
    TEST_ACHIEVEMENT = 'test_achievement'
    SKILL_CERTIFICATION = 'skill_certification'
    PARTICIPATION = 'participation'
    
    TEMPLATE_TYPES = [
        (COURSE_COMPLETION, 'Course Completion'),
        (TEST_ACHIEVEMENT, 'Test Achievement'),
        (SKILL_CERTIFICATION, 'Skill Certification'),
        (PARTICIPATION, 'Participation'),
    ]
    
    # Certificate formats
    PDF = 'pdf'
    IMAGE = 'image'
    HTML = 'html'
    
    FORMAT_CHOICES = [
        (PDF, 'PDF'),
        (IMAGE, 'Image (PNG/JPG)'),
        (HTML, 'HTML'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES)
    
    # Template design
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default=PDF)
    template_file = models.FileField(
        upload_to='certificates/templates/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'html', 'png', 'jpg', 'jpeg'])],
        blank=True,
        null=True
    )
    
    # Template content (HTML/CSS for dynamic generation)
    html_template = models.TextField(blank=True, null=True)
    css_styles = models.TextField(blank=True, null=True)
    
    # Layout configuration
    layout_config = models.JSONField(default=dict, blank=True)  # Font sizes, positions, etc.
    
    # Template variables
    available_variables = models.JSONField(default=list, blank=True)  # Available template variables
    
    # Branding
    logo = models.ImageField(upload_to='certificates/logos/', blank=True, null=True)
    signature_image = models.ImageField(upload_to='certificates/signatures/', blank=True, null=True)
    background_image = models.ImageField(upload_to='certificates/backgrounds/', blank=True, null=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    require_approval = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_certificate_templates')
    
    class Meta:
        db_table = 'certifications_template'
        verbose_name = 'Certificate Template'
        verbose_name_plural = 'Certificate Templates'
        ordering = ['template_type', 'name']
        indexes = [
            models.Index(fields=['template_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class Certificate(models.Model):
    """Individual certificates issued to users."""
    
    # Certificate status
    DRAFT = 'draft'
    PENDING_APPROVAL = 'pending_approval'
    ISSUED = 'issued'
    REVOKED = 'revoked'
    EXPIRED = 'expired'
    
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PENDING_APPROVAL, 'Pending Approval'),
        (ISSUED, 'Issued'),
        (REVOKED, 'Revoked'),
        (EXPIRED, 'Expired'),
    ]
    
    # Certificate types (matching template types)
    COURSE_COMPLETION = 'course_completion'
    TEST_ACHIEVEMENT = 'test_achievement'
    SKILL_CERTIFICATION = 'skill_certification'
    PARTICIPATION = 'participation'
    
    CERTIFICATE_TYPES = [
        (COURSE_COMPLETION, 'Course Completion'),
        (TEST_ACHIEVEMENT, 'Test Achievement'),
        (SKILL_CERTIFICATION, 'Skill Certification'),
        (PARTICIPATION, 'Participation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certificate_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Recipient information
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    
    # Certificate details
    certificate_type = models.CharField(max_length=30, choices=CERTIFICATE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    template = models.ForeignKey(CertificateTemplate, on_delete=models.CASCADE, related_name='certificates')
    
    # Content
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Related objects
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True, related_name='certificates')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, blank=True, null=True, related_name='certificates')
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, blank=True, null=True, related_name='certificates')
    
    # Achievement details
    completion_date = models.DateField()
    achievement_data = models.JSONField(default=dict, blank=True)  # Scores, grades, etc.
    
    # Certificate metadata
    issuer_name = models.CharField(max_length=200)
    issuer_title = models.CharField(max_length=100, blank=True, null=True)
    institution_name = models.CharField(max_length=200)
    
    # Validity
    issue_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(blank=True, null=True)
    
    # Verification
    verification_code = models.CharField(max_length=100, unique=True, db_index=True)
    digital_signature = models.TextField(blank=True, null=True)  # Digital signature hash
    
    # File storage
    certificate_file = models.FileField(upload_to='certificates/issued/%Y/%m/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='certificates/thumbnails/%Y/%m/', blank=True, null=True)
    
    # Sharing and privacy
    is_public = models.BooleanField(default=False)
    allow_sharing = models.BooleanField(default=True)
    share_on_social = models.BooleanField(default=False)
    
    # Download tracking
    download_count = models.PositiveIntegerField(default=0)
    last_downloaded = models.DateTimeField(blank=True, null=True)
    
    # Approval workflow
    issued_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='issued_certificates'
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='approved_certificates'
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    
    # Revocation
    revoked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='revoked_certificates'
    )
    revoked_at = models.DateTimeField(blank=True, null=True)
    revocation_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'certifications_certificate'
        verbose_name = 'Certificate'
        verbose_name_plural = 'Certificates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['certificate_number']),
            models.Index(fields=['verification_code']),
            models.Index(fields=['course']),
            models.Index(fields=['issue_date']),
        ]
    
    def __str__(self):
        return f"Certificate {self.certificate_number} - {self.recipient.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_number:
            self.certificate_number = self.generate_certificate_number()
        if not self.verification_code:
            self.verification_code = self.generate_verification_code()
        super().save(*args, **kwargs)
    
    def generate_certificate_number(self):
        """Generate unique certificate number."""
        timestamp = timezone.now().strftime('%Y%m%d')
        user_id = str(self.recipient.id)[-6:]
        course_code = self.course.course_code[:3].upper() if self.course else 'GEN'
        return f"CERT-{timestamp}-{course_code}-{user_id}"
    
    def generate_verification_code(self):
        """Generate unique verification code."""
        data = f"{self.recipient.id}-{self.course.id if self.course else ''}-{timezone.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16].upper()
    
    @property
    def is_valid(self):
        """Check if certificate is currently valid."""
        if self.status != self.ISSUED:
            return False
        if self.expiry_date and timezone.now().date() > self.expiry_date:
            return False
        return True
    
    @property
    def is_expired(self):
        """Check if certificate has expired."""
        if not self.expiry_date:
            return False
        return timezone.now().date() > self.expiry_date
    
    def revoke(self, revoked_by, reason):
        """Revoke the certificate."""
        self.status = self.REVOKED
        self.revoked_by = revoked_by
        self.revoked_at = timezone.now()
        self.revocation_reason = reason
        self.save(update_fields=['status', 'revoked_by', 'revoked_at', 'revocation_reason'])


class CertificateIssuance(models.Model):
    """Track certificate issuance events and batch operations."""
    
    # Issuance types
    INDIVIDUAL = 'individual'
    BATCH = 'batch'
    AUTOMATIC = 'automatic'
    
    ISSUANCE_TYPES = [
        (INDIVIDUAL, 'Individual'),
        (BATCH, 'Batch'),
        (AUTOMATIC, 'Automatic'),
    ]
    
    # Issuance status
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issuance_type = models.CharField(max_length=20, choices=ISSUANCE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    
    # Batch details
    batch_name = models.CharField(max_length=200, blank=True, null=True)
    total_certificates = models.PositiveIntegerField(default=0)
    successful_issuances = models.PositiveIntegerField(default=0)
    failed_issuances = models.PositiveIntegerField(default=0)
    
    # Related objects
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True, related_name='certificate_issuances')
    template = models.ForeignKey(CertificateTemplate, on_delete=models.CASCADE, related_name='issuances')
    certificates = models.ManyToManyField(Certificate, blank=True, related_name='issuance_events')
    
    # Target criteria for batch issuance
    target_criteria = models.JSONField(default=dict, blank=True)  # Criteria for auto-selection
    
    # Processing details
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    error_log = models.TextField(blank=True, null=True)
    
    # Audit trail
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_issuances')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'certifications_issuance'
        verbose_name = 'Certificate Issuance'
        verbose_name_plural = 'Certificate Issuances'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['course']),
        ]
    
    def __str__(self):
        if self.batch_name:
            return f"Batch: {self.batch_name}"
        return f"Issuance {self.id} - {self.get_issuance_type_display()}"


class CertificateVerification(models.Model):
    """Track certificate verification attempts."""
    
    # Verification methods
    CODE_LOOKUP = 'code_lookup'
    QR_SCAN = 'qr_scan'
    URL_ACCESS = 'url_access'
    API_REQUEST = 'api_request'
    
    VERIFICATION_METHODS = [
        (CODE_LOOKUP, 'Code Lookup'),
        (QR_SCAN, 'QR Code Scan'),
        (URL_ACCESS, 'URL Access'),
        (API_REQUEST, 'API Request'),
    ]
    
    # Verification results
    VALID = 'valid'
    INVALID = 'invalid'
    EXPIRED = 'expired'
    REVOKED = 'revoked'
    NOT_FOUND = 'not_found'
    
    VERIFICATION_RESULTS = [
        (VALID, 'Valid'),
        (INVALID, 'Invalid'),
        (EXPIRED, 'Expired'),
        (REVOKED, 'Revoked'),
        (NOT_FOUND, 'Not Found'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certificate = models.ForeignKey(
        Certificate, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        related_name='verification_attempts'
    )
    
    # Verification details
    verification_method = models.CharField(max_length=20, choices=VERIFICATION_METHODS)
    verification_result = models.CharField(max_length=20, choices=VERIFICATION_RESULTS)
    
    # Query details
    query_value = models.CharField(max_length=200)  # The code/URL that was checked
    
    # Request details
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    referrer = models.URLField(blank=True, null=True)
    
    # Geolocation (if available)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    verified_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'certifications_verification'
        verbose_name = 'Certificate Verification'
        verbose_name_plural = 'Certificate Verifications'
        ordering = ['-verified_at']
        indexes = [
            models.Index(fields=['certificate', 'verified_at']),
            models.Index(fields=['verification_result']),
            models.Index(fields=['query_value']),
        ]
    
    def __str__(self):
        return f"Verification of {self.query_value} - {self.get_verification_result_display()}"


class CertificateShare(models.Model):
    """Track certificate sharing activities."""
    
    # Share platforms
    LINKEDIN = 'linkedin'
    TWITTER = 'twitter'
    FACEBOOK = 'facebook'
    EMAIL = 'email'
    DIRECT_LINK = 'direct_link'
    DOWNLOAD = 'download'
    
    SHARE_PLATFORMS = [
        (LINKEDIN, 'LinkedIn'),
        (TWITTER, 'Twitter'),
        (FACEBOOK, 'Facebook'),
        (EMAIL, 'Email'),
        (DIRECT_LINK, 'Direct Link'),
        (DOWNLOAD, 'Download'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE, related_name='shares')
    platform = models.CharField(max_length=20, choices=SHARE_PLATFORMS)
    
    # Share details
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificate_shares')
    recipient_email = models.EmailField(blank=True, null=True)  # For email shares
    message = models.TextField(blank=True, null=True)  # Optional message
    
    # Tracking
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'certifications_share'
        verbose_name = 'Certificate Share'
        verbose_name_plural = 'Certificate Shares'
        ordering = ['-shared_at']
        indexes = [
            models.Index(fields=['certificate', 'shared_at']),
            models.Index(fields=['platform']),
        ]
    
    def __str__(self):
        return f"{self.certificate.certificate_number} shared on {self.get_platform_display()}"
