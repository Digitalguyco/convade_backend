from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from courses.models import Course
import uuid
from decimal import Decimal


class PaymentMethod(models.Model):
    """User payment methods (cards, bank accounts, etc.)."""
    
    # Payment method types
    CREDIT_CARD = 'credit_card'
    DEBIT_CARD = 'debit_card'
    BANK_ACCOUNT = 'bank_account'
    PAYPAL = 'paypal'
    MOBILE_MONEY = 'mobile_money'
    
    METHOD_TYPES = [
        (CREDIT_CARD, 'Credit Card'),
        (DEBIT_CARD, 'Debit Card'),
        (BANK_ACCOUNT, 'Bank Account'),
        (PAYPAL, 'PayPal'),
        (MOBILE_MONEY, 'Mobile Money'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    
    # Method details
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES)
    provider = models.CharField(max_length=50)  # Stripe, Paystack, etc.
    external_id = models.CharField(max_length=200)  # Provider's ID for this method
    
    # Card/Account details (last 4 digits, masked info)
    last_four = models.CharField(max_length=4, blank=True, null=True)
    brand = models.CharField(max_length=50, blank=True, null=True)  # Visa, Mastercard, etc.
    expiry_month = models.PositiveIntegerField(blank=True, null=True)
    expiry_year = models.PositiveIntegerField(blank=True, null=True)
    
    # Bank account details
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_holder_name = models.CharField(max_length=200, blank=True, null=True)
    
    # Settings
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_payment_method'
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['external_id']),
        ]
    
    def __str__(self):
        if self.last_four:
            return f"{self.get_method_type_display()} ending in {self.last_four}"
        return f"{self.user.full_name} - {self.get_method_type_display()}"


class Discount(models.Model):
    """Discount codes and promotions."""
    
    # Discount types
    PERCENTAGE = 'percentage'
    FIXED_AMOUNT = 'fixed_amount'
    FREE_TRIAL = 'free_trial'
    
    DISCOUNT_TYPES = [
        (PERCENTAGE, 'Percentage'),
        (FIXED_AMOUNT, 'Fixed Amount'),
        (FREE_TRIAL, 'Free Trial'),
    ]
    
    # Application scope
    GLOBAL = 'global'
    COURSE_SPECIFIC = 'course_specific'
    USER_SPECIFIC = 'user_specific'
    FIRST_TIME = 'first_time'
    
    SCOPES = [
        (GLOBAL, 'Global'),
        (COURSE_SPECIFIC, 'Course Specific'),
        (USER_SPECIFIC, 'User Specific'),
        (FIRST_TIME, 'First Time Users'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Discount settings
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Application scope
    scope = models.CharField(max_length=20, choices=SCOPES, default=GLOBAL)
    applicable_courses = models.ManyToManyField(Course, blank=True, related_name='discounts')
    applicable_users = models.ManyToManyField(User, blank=True, related_name='available_discounts')
    
    # Usage limits
    max_uses = models.PositiveIntegerField(default=0)  # 0 = unlimited
    max_uses_per_user = models.PositiveIntegerField(default=1)
    current_uses = models.PositiveIntegerField(default=0)
    
    # Validity period
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Minimum requirements
    minimum_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_stackable = models.BooleanField(default=False)  # Can be combined with other discounts
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_discounts')
    
    class Meta:
        db_table = 'payments_discount'
        verbose_name = 'Discount'
        verbose_name_plural = 'Discounts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_valid(self):
        """Check if discount is currently valid."""
        now = timezone.now()
        return (
            self.is_active and 
            self.valid_from <= now <= self.valid_until and
            (self.max_uses == 0 or self.current_uses < self.max_uses)
        )
    
    def can_be_used_by(self, user, course=None):
        """Check if discount can be used by a specific user for a course."""
        if not self.is_valid:
            return False
        
        # Check user-specific discounts
        if self.scope == self.USER_SPECIFIC:
            if not self.applicable_users.filter(id=user.id).exists():
                return False
        
        # Check course-specific discounts
        if self.scope == self.COURSE_SPECIFIC and course:
            if not self.applicable_courses.filter(id=course.id).exists():
                return False
        
        # Check first-time user requirement
        if self.scope == self.FIRST_TIME:
            if Payment.objects.filter(user=user, status=Payment.COMPLETED).exists():
                return False
        
        # Check per-user usage limit
        user_usage = DiscountUsage.objects.filter(discount=self, user=user).count()
        if user_usage >= self.max_uses_per_user:
            return False
        
        return True


class Payment(models.Model):
    """Payment transactions."""
    
    # Payment status
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'
    PARTIALLY_REFUNDED = 'partially_refunded'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (CANCELLED, 'Cancelled'),
        (REFUNDED, 'Refunded'),
        (PARTIALLY_REFUNDED, 'Partially Refunded'),
    ]
    
    # Payment types
    COURSE_PURCHASE = 'course_purchase'
    SUBSCRIPTION = 'subscription'
    REFUND = 'refund'
    
    PAYMENT_TYPES = [
        (COURSE_PURCHASE, 'Course Purchase'),
        (SUBSCRIPTION, 'Subscription'),
        (REFUND, 'Refund'),
    ]
    
    # Payment providers
    STRIPE = 'stripe'
    PAYSTACK = 'paystack'
    PAYPAL = 'paypal'
    BANK_TRANSFER = 'bank_transfer'
    
    PROVIDERS = [
        (STRIPE, 'Stripe'),
        (PAYSTACK, 'Paystack'),
        (PAYPAL, 'PayPal'),
        (BANK_TRANSFER, 'Bank Transfer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=PENDING)
    provider = models.CharField(max_length=20, choices=PROVIDERS)
    
    # Amounts
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Currency
    currency = models.CharField(max_length=3, default='USD')
    
    # Related objects
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True, related_name='payments')
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, blank=True, null=True, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, blank=True, null=True)
    
    # Provider details
    external_id = models.CharField(max_length=200, blank=True, null=True)  # Provider transaction ID
    external_data = models.JSONField(default=dict, blank=True)  # Provider response data
    
    # Billing information
    billing_name = models.CharField(max_length=200, blank=True, null=True)
    billing_email = models.EmailField(blank=True, null=True)
    billing_address = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Notes and metadata
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'payments_payment'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['external_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.id} - {self.user.full_name} - {self.total_amount} {self.currency}"
    
    @property
    def is_successful(self):
        return self.status == self.COMPLETED
    
    def calculate_totals(self):
        """Calculate total amount including discounts and taxes."""
        discounted_amount = self.amount - self.discount_amount
        self.total_amount = discounted_amount + self.tax_amount
        return self.total_amount


class Subscription(models.Model):
    """User subscriptions for courses or platform access."""
    
    # Subscription status
    ACTIVE = 'active'
    CANCELLED = 'cancelled'
    EXPIRED = 'expired'
    SUSPENDED = 'suspended'
    TRIAL = 'trial'
    
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (CANCELLED, 'Cancelled'),
        (EXPIRED, 'Expired'),
        (SUSPENDED, 'Suspended'),
        (TRIAL, 'Trial'),
    ]
    
    # Subscription types
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'
    LIFETIME = 'lifetime'
    
    BILLING_CYCLES = [
        (MONTHLY, 'Monthly'),
        (QUARTERLY, 'Quarterly'),
        (YEARLY, 'Yearly'),
        (LIFETIME, 'Lifetime'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True, related_name='subscriptions')
    
    # Subscription details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=TRIAL)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Dates
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    next_billing_date = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    
    # Trial information
    trial_end_date = models.DateTimeField(blank=True, null=True)
    
    # Provider details
    external_id = models.CharField(max_length=200, blank=True, null=True)
    provider = models.CharField(max_length=20, choices=Payment.PROVIDERS)
    
    # Auto-renewal
    auto_renew = models.BooleanField(default=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_subscription'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['next_billing_date']),
        ]
    
    def __str__(self):
        course_name = self.course.title if self.course else "Platform Access"
        return f"{self.user.full_name} - {course_name} ({self.get_billing_cycle_display()})"
    
    @property
    def is_active(self):
        """Check if subscription is currently active."""
        now = timezone.now()
        if self.status not in [self.ACTIVE, self.TRIAL]:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True
    
    @property
    def is_in_trial(self):
        """Check if subscription is in trial period."""
        if self.status != self.TRIAL:
            return False
        if not self.trial_end_date:
            return False
        return timezone.now() <= self.trial_end_date


class Invoice(models.Model):
    """Invoices for payments and subscriptions."""
    
    # Invoice status
    DRAFT = 'draft'
    SENT = 'sent'
    PAID = 'paid'
    OVERDUE = 'overdue'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (SENT, 'Sent'),
        (PAID, 'Paid'),
        (OVERDUE, 'Overdue'),
        (CANCELLED, 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    
    # Related objects
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, blank=True, null=True, related_name='invoice')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, blank=True, null=True, related_name='invoices')
    
    # Invoice details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Dates
    issue_date = models.DateField()
    due_date = models.DateField()
    paid_date = models.DateField(blank=True, null=True)
    
    # Billing information
    billing_name = models.CharField(max_length=200)
    billing_email = models.EmailField()
    billing_address = models.JSONField(default=dict)
    
    # Line items
    line_items = models.JSONField(default=list)  # List of invoice line items
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_invoice'
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.user.full_name}"
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue."""
        if self.status == self.PAID:
            return False
        return timezone.now().date() > self.due_date


class DiscountUsage(models.Model):
    """Track discount code usage."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discount_usages')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='discount_usages')
    
    # Usage details
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments_discount_usage'
        verbose_name = 'Discount Usage'
        verbose_name_plural = 'Discount Usages'
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['discount', 'used_at']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} used {self.discount.code} - {self.discount_amount}"


class Refund(models.Model):
    """Payment refunds."""
    
    # Refund status
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (CANCELLED, 'Cancelled'),
    ]
    
    # Refund reasons
    CUSTOMER_REQUEST = 'customer_request'
    COURSE_CANCELLED = 'course_cancelled'
    TECHNICAL_ISSUE = 'technical_issue'
    DUPLICATE_PAYMENT = 'duplicate_payment'
    FRAUD = 'fraud'
    
    REFUND_REASONS = [
        (CUSTOMER_REQUEST, 'Customer Request'),
        (COURSE_CANCELLED, 'Course Cancelled'),
        (TECHNICAL_ISSUE, 'Technical Issue'),
        (DUPLICATE_PAYMENT, 'Duplicate Payment'),
        (FRAUD, 'Fraud'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    
    # Refund details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    reason = models.CharField(max_length=30, choices=REFUND_REASONS)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Provider details
    external_id = models.CharField(max_length=200, blank=True, null=True)
    provider_response = models.JSONField(default=dict, blank=True)
    
    # Approval workflow
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_refunds')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='approved_refunds')
    approved_at = models.DateTimeField(blank=True, null=True)
    
    # Notes
    reason_details = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'payments_refund'
        verbose_name = 'Refund'
        verbose_name_plural = 'Refunds'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Refund {self.id} - {self.refund_amount} {self.payment.currency}"
