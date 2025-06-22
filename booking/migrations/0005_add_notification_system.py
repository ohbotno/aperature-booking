# Generated migration for notification system

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('booking', '0004_remove_bookingtemplate_unique_user_template_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('notification_type', models.CharField(choices=[('booking_confirmed', 'Booking Confirmed'), ('booking_cancelled', 'Booking Cancelled'), ('booking_reminder', 'Booking Reminder'), ('approval_request', 'Approval Request'), ('approval_decision', 'Approval Decision'), ('maintenance_alert', 'Maintenance Alert'), ('conflict_detected', 'Conflict Detected'), ('quota_warning', 'Quota Warning')], max_length=30)),
                ('subject_template', models.CharField(max_length=200)),
                ('html_template', models.TextField()),
                ('text_template', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('available_variables', models.JSONField(default=list, help_text='List of available template variables')),
            ],
            options={
                'db_table': 'booking_emailtemplate',
            },
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('booking_confirmed', 'Booking Confirmed'), ('booking_cancelled', 'Booking Cancelled'), ('booking_reminder', 'Booking Reminder'), ('approval_request', 'Approval Request'), ('approval_decision', 'Approval Decision'), ('maintenance_alert', 'Maintenance Alert'), ('conflict_detected', 'Conflict Detected'), ('quota_warning', 'Quota Warning')], max_length=30)),
                ('delivery_method', models.CharField(choices=[('email', 'Email'), ('sms', 'SMS'), ('in_app', 'In-App')], max_length=10)),
                ('is_enabled', models.BooleanField(default=True)),
                ('frequency', models.CharField(choices=[('immediate', 'Immediate'), ('daily_digest', 'Daily Digest'), ('weekly_digest', 'Weekly Digest')], default='immediate', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'booking_notificationpreference',
                'unique_together': {('user', 'notification_type', 'delivery_method')},
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('booking_confirmed', 'Booking Confirmed'), ('booking_cancelled', 'Booking Cancelled'), ('booking_reminder', 'Booking Reminder'), ('approval_request', 'Approval Request'), ('approval_decision', 'Approval Decision'), ('maintenance_alert', 'Maintenance Alert'), ('conflict_detected', 'Conflict Detected'), ('quota_warning', 'Quota Warning')], max_length=30)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=10)),
                ('delivery_method', models.CharField(choices=[('email', 'Email'), ('sms', 'SMS'), ('in_app', 'In-App')], max_length=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed'), ('read', 'Read')], default='pending', max_length=10)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('retry_count', models.PositiveIntegerField(default=0)),
                ('max_retries', models.PositiveIntegerField(default=3)),
                ('next_retry_at', models.DateTimeField(blank=True, null=True)),
                ('booking', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='booking.booking')),
                ('maintenance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='booking.maintenance')),
                ('resource', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='booking.resource')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'booking_notification',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['user', 'status'], name='booking_not_user_id_f8cea7_idx'),
                    models.Index(fields=['notification_type', 'status'], name='booking_not_notific_8b1e5e_idx'),
                    models.Index(fields=['created_at'], name='booking_not_created_5c1b8f_idx'),
                ],
            },
        ),
    ]