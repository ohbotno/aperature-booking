# Generated manually to avoid conflicts with existing tables

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('booking', '0031_add_email_configuration'),
    ]

    operations = [
        migrations.CreateModel(
            name='BackupSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Automated Backup', max_length=200)),
                ('enabled', models.BooleanField(default=True)),
                ('frequency', models.CharField(choices=[('disabled', 'Disabled'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='weekly', max_length=20)),
                ('backup_time', models.TimeField(default='02:00', help_text='Time of day to run backup (24-hour format)')),
                ('day_of_week', models.IntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')], default=6, help_text='Day of week for weekly backups')),
                ('day_of_month', models.IntegerField(default=1, help_text='Day of month for monthly backups (1-28)')),
                ('include_media', models.BooleanField(default=True, help_text='Include media files in automated backups')),
                ('include_database', models.BooleanField(default=True, help_text='Include database in automated backups')),
                ('include_configuration', models.BooleanField(default=True, help_text='Include configuration analysis in automated backups')),
                ('max_backups_to_keep', models.IntegerField(default=7, help_text='Maximum number of automated backups to keep (older ones will be deleted)')),
                ('retention_days', models.IntegerField(default=30, help_text='Days to keep automated backups before deletion')),
                ('last_run', models.DateTimeField(blank=True, null=True)),
                ('last_success', models.DateTimeField(blank=True, null=True)),
                ('last_backup_name', models.CharField(blank=True, max_length=255)),
                ('consecutive_failures', models.IntegerField(default=0)),
                ('total_runs', models.IntegerField(default=0)),
                ('total_successes', models.IntegerField(default=0)),
                ('last_error', models.TextField(blank=True)),
                ('notification_email', models.EmailField(blank=True, help_text='Email to notify on backup failures (leave blank to disable)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Backup Schedule',
                'verbose_name_plural': 'Backup Schedules',
                'ordering': ['-created_at'],
            },
        ),
    ]