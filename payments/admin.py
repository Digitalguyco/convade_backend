from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Payment, PaymentMethod, Discount, DiscountUsage, 
    Subscription, Invoice, Refund
)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for Payment model."""
    
    list_display = ('user', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency', 'provider', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentMethod model."""
    
    list_display = ('user', 'method_type', 'provider', 'is_default', 'is_active', 'created_at')
    list_filter = ('method_type', 'provider', 'is_default', 'is_active')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    """Admin configuration for Discount model."""
    
    list_display = ('code', 'discount_type', 'discount_value', 'valid_from', 'valid_until', 'is_active')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_until')
    search_fields = ('code', 'name')
    ordering = ('-created_at',)


@admin.register(DiscountUsage)
class DiscountUsageAdmin(admin.ModelAdmin):
    """Admin configuration for DiscountUsage model."""
    
    list_display = ('discount', 'user', 'payment', 'used_at')
    list_filter = ('discount', 'used_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'discount__code')
    ordering = ('-used_at',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin configuration for Subscription model."""
    
    list_display = ('user', 'status', 'price', 'billing_cycle', 'next_billing_date')
    list_filter = ('status', 'billing_cycle', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin configuration for Invoice model."""
    
    list_display = ('invoice_number', 'user', 'status', 'total_amount', 'currency', 'due_date')
    list_filter = ('status', 'currency', 'due_date')
    search_fields = ('invoice_number', 'user__email', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """Admin configuration for Refund model."""
    
    list_display = ('payment', 'refund_amount', 'status', 'reason', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('payment__user__email', 'reason')
    ordering = ('-created_at',)
