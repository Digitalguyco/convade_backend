from django.contrib import admin
from .models import (
    CertificateTemplate, Certificate, CertificateIssuance,
    CertificateVerification, CertificateShare
)


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_number', 'recipient', 'course', 'status')
    search_fields = ('certificate_number', 'recipient__email')


@admin.register(CertificateIssuance)
class CertificateIssuanceAdmin(admin.ModelAdmin):
    list_display = ('course', 'status')
    search_fields = ('course__title',)


@admin.register(CertificateVerification)
class CertificateVerificationAdmin(admin.ModelAdmin):
    list_display = ('certificate',)
    search_fields = ('certificate__certificate_number',)


@admin.register(CertificateShare)
class CertificateShareAdmin(admin.ModelAdmin):
    list_display = ('certificate', 'platform')
    search_fields = ('certificate__certificate_number',)
