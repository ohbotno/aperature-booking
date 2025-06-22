# Generated manually for EmailConfiguration model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('booking', '0030_maintenancevendor_maintenance_actual_cost_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=False, help_text='Enable this configuration as the active email settings')),
                ('name', models.CharField(help_text='Descriptive name for this email configuration', max_length=100)),
                ('description', models.TextField(blank=True, help_text='Optional description of this configuration')),
                ('email_backend', models.CharField(choices=[('django.core.mail.backends.smtp.EmailBackend', 'SMTP Email Backend'), ('django.core.mail.backends.console.EmailBackend', 'Console Email Backend (Development)'), ('django.core.mail.backends.filebased.EmailBackend', 'File-based Email Backend (Testing)'), ('django.core.mail.backends.locmem.EmailBackend', 'In-memory Email Backend (Testing)'), ('django.core.mail.backends.dummy.EmailBackend', 'Dummy Email Backend (No emails sent)')], default='django.core.mail.backends.smtp.EmailBackend', help_text='Django email backend to use', max_length=100)),
                ('email_host', models.CharField(help_text='SMTP server hostname (e.g., smtp.gmail.com)', max_length=255)),
                ('email_port', models.PositiveIntegerField(default=587, help_text='SMTP server port (587 for TLS, 465 for SSL, 25 for standard)')),
                ('email_use_tls', models.BooleanField(default=True, help_text='Use TLS (Transport Layer Security) encryption')),
                ('email_use_ssl', models.BooleanField(default=False, help_text='Use SSL (Secure Sockets Layer) encryption')),
                ('email_host_user', models.CharField(blank=True, help_text='SMTP server username/email address', max_length=255)),
                ('email_host_password', models.CharField(blank=True, help_text='SMTP server password (stored encrypted)', max_length=255)),
                ('default_from_email', models.EmailField(help_text="Default 'from' email address for outgoing emails", max_length=254)),
                ('server_email', models.EmailField(blank=True, help_text='Email address used for error messages from Django', max_length=254)),
                ('email_timeout', models.PositiveIntegerField(default=10, help_text='Timeout in seconds for SMTP connections')),
                ('email_file_path', models.CharField(blank=True, help_text='Directory path for file-based email backend', max_length=500)),
                ('is_validated', models.BooleanField(default=False, help_text='Whether this configuration has been successfully tested')),
                ('last_test_date', models.DateTimeField(blank=True, help_text='Last time this configuration was tested', null=True)),
                ('last_test_result', models.TextField(blank=True, help_text='Result of the last configuration test')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(help_text='User who created this configuration', on_delete=django.db.models.deletion.CASCADE, related_name='created_email_configs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Email Configuration',
                'verbose_name_plural': 'Email Configurations',
                'ordering': ['-is_active', '-updated_at'],
            },
        ),
    ]