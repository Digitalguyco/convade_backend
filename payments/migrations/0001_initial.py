# Generated by Django 5.2.1 on 2025-05-24 01:53

import django.core.validators
import django.db.models.deletion
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Discount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(db_index=True, max_length=50, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('discount_type', models.CharField(choices=[('percentage', 'Percentage'), ('fixed_amount', 'Fixed Amount'), ('free_trial', 'Free Trial')], max_length=20)),
                ('discount_value', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('scope', models.CharField(choices=[('global', 'Global'), ('course_specific', 'Course Specific'), ('user_specific', 'User Specific'), ('first_time', 'First Time Users')], default='global', max_length=20)),
                ('max_uses', models.PositiveIntegerField(default=0)),
                ('max_uses_per_user', models.PositiveIntegerField(default=1)),
                ('current_uses', models.PositiveIntegerField(default=0)),
                ('valid_from', models.DateTimeField()),
                ('valid_until', models.DateTimeField()),
                ('minimum_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('is_stackable', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('applicable_courses', models.ManyToManyField(blank=True, related_name='discounts', to='courses.course')),
                ('applicable_users', models.ManyToManyField(blank=True, related_name='available_discounts', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_discounts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Discount',
                'verbose_name_plural': 'Discounts',
                'db_table': 'payments_discount',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('payment_type', models.CharField(choices=[('course_purchase', 'Course Purchase'), ('subscription', 'Subscription'), ('refund', 'Refund')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded'), ('partially_refunded', 'Partially Refunded')], default='pending', max_length=25)),
                ('provider', models.CharField(choices=[('stripe', 'Stripe'), ('paystack', 'Paystack'), ('paypal', 'PayPal'), ('bank_transfer', 'Bank Transfer')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('external_id', models.CharField(blank=True, max_length=200, null=True)),
                ('external_data', models.JSONField(blank=True, default=dict)),
                ('billing_name', models.CharField(blank=True, max_length=200, null=True)),
                ('billing_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('billing_address', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='courses.course')),
                ('discount', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='payments.discount')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Payment',
                'verbose_name_plural': 'Payments',
                'db_table': 'payments_payment',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DiscountUsage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('discount_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('used_at', models.DateTimeField(auto_now_add=True)),
                ('discount', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usages', to='payments.discount')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discount_usages', to=settings.AUTH_USER_MODEL)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discount_usages', to='payments.payment')),
            ],
            options={
                'verbose_name': 'Discount Usage',
                'verbose_name_plural': 'Discount Usages',
                'db_table': 'payments_discount_usage',
                'ordering': ['-used_at'],
            },
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('method_type', models.CharField(choices=[('credit_card', 'Credit Card'), ('debit_card', 'Debit Card'), ('bank_account', 'Bank Account'), ('paypal', 'PayPal'), ('mobile_money', 'Mobile Money')], max_length=20)),
                ('provider', models.CharField(max_length=50)),
                ('external_id', models.CharField(max_length=200)),
                ('last_four', models.CharField(blank=True, max_length=4, null=True)),
                ('brand', models.CharField(blank=True, max_length=50, null=True)),
                ('expiry_month', models.PositiveIntegerField(blank=True, null=True)),
                ('expiry_year', models.PositiveIntegerField(blank=True, null=True)),
                ('bank_name', models.CharField(blank=True, max_length=100, null=True)),
                ('account_holder_name', models.CharField(blank=True, max_length=200, null=True)),
                ('is_default', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_methods', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Payment Method',
                'verbose_name_plural': 'Payment Methods',
                'db_table': 'payments_payment_method',
                'ordering': ['-is_default', '-created_at'],
            },
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_method',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='payments.paymentmethod'),
        ),
        migrations.CreateModel(
            name='Refund',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('reason', models.CharField(choices=[('customer_request', 'Customer Request'), ('course_cancelled', 'Course Cancelled'), ('technical_issue', 'Technical Issue'), ('duplicate_payment', 'Duplicate Payment'), ('fraud', 'Fraud')], max_length=30)),
                ('refund_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('external_id', models.CharField(blank=True, max_length=200, null=True)),
                ('provider_response', models.JSONField(blank=True, default=dict)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('reason_details', models.TextField(blank=True, null=True)),
                ('admin_notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_refunds', to=settings.AUTH_USER_MODEL)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refunds', to='payments.payment')),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requested_refunds', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Refund',
                'verbose_name_plural': 'Refunds',
                'db_table': 'payments_refund',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('active', 'Active'), ('cancelled', 'Cancelled'), ('expired', 'Expired'), ('suspended', 'Suspended'), ('trial', 'Trial')], default='trial', max_length=20)),
                ('billing_cycle', models.CharField(choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly'), ('lifetime', 'Lifetime')], max_length=20)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('next_billing_date', models.DateTimeField(blank=True, null=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('trial_end_date', models.DateTimeField(blank=True, null=True)),
                ('external_id', models.CharField(blank=True, max_length=200, null=True)),
                ('provider', models.CharField(choices=[('stripe', 'Stripe'), ('paystack', 'Paystack'), ('paypal', 'PayPal'), ('bank_transfer', 'Bank Transfer')], max_length=20)),
                ('auto_renew', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='courses.course')),
                ('payment_method', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='payments.paymentmethod')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Subscription',
                'verbose_name_plural': 'Subscriptions',
                'db_table': 'payments_subscription',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('invoice_number', models.CharField(db_index=True, max_length=50, unique=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('sent', 'Sent'), ('paid', 'Paid'), ('overdue', 'Overdue'), ('cancelled', 'Cancelled')], default='draft', max_length=20)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=10)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('issue_date', models.DateField()),
                ('due_date', models.DateField()),
                ('paid_date', models.DateField(blank=True, null=True)),
                ('billing_name', models.CharField(max_length=200)),
                ('billing_email', models.EmailField(max_length=254)),
                ('billing_address', models.JSONField(default=dict)),
                ('line_items', models.JSONField(default=list)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to=settings.AUTH_USER_MODEL)),
                ('payment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invoice', to='payments.payment')),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='payments.subscription')),
            ],
            options={
                'verbose_name': 'Invoice',
                'verbose_name_plural': 'Invoices',
                'db_table': 'payments_invoice',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='discount',
            index=models.Index(fields=['code'], name='payments_di_code_968be1_idx'),
        ),
        migrations.AddIndex(
            model_name='discount',
            index=models.Index(fields=['valid_from', 'valid_until'], name='payments_di_valid_f_8dbd4e_idx'),
        ),
        migrations.AddIndex(
            model_name='discountusage',
            index=models.Index(fields=['discount', 'used_at'], name='payments_di_discoun_3fd6d1_idx'),
        ),
        migrations.AddIndex(
            model_name='discountusage',
            index=models.Index(fields=['user'], name='payments_di_user_id_0771ff_idx'),
        ),
        migrations.AddIndex(
            model_name='paymentmethod',
            index=models.Index(fields=['user', 'is_active'], name='payments_pa_user_id_e03dcf_idx'),
        ),
        migrations.AddIndex(
            model_name='paymentmethod',
            index=models.Index(fields=['external_id'], name='payments_pa_externa_18cd64_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['user', 'status'], name='payments_pa_user_id_01767a_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['external_id'], name='payments_pa_externa_e9415f_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['created_at'], name='payments_pa_created_b8a300_idx'),
        ),
        migrations.AddIndex(
            model_name='refund',
            index=models.Index(fields=['payment', 'status'], name='payments_re_payment_4444a0_idx'),
        ),
        migrations.AddIndex(
            model_name='refund',
            index=models.Index(fields=['status'], name='payments_re_status_715c3a_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['user', 'status'], name='payments_su_user_id_058311_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['next_billing_date'], name='payments_su_next_bi_574c1e_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['invoice_number'], name='payments_in_invoice_3fa711_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['user', 'status'], name='payments_in_user_id_a545de_idx'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['due_date'], name='payments_in_due_dat_9c830a_idx'),
        ),
    ]
