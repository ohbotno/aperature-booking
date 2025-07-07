# booking/models.py
"""
Core models for the Aperture Booking.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperture-booking.org/commercial
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import uuid
import json


class AboutPage(models.Model):
    """Admin-configurable about page content."""
    title = models.CharField(max_length=200, default="About Our Lab")
    content = models.TextField(
        help_text="Main content for the about page. HTML is allowed."
    )
    facility_name = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    operating_hours = models.TextField(
        blank=True,
        help_text="Describe your normal operating hours"
    )
    policies_url = models.URLField(
        blank=True,
        help_text="Link to detailed policies document"
    )
    emergency_contact = models.CharField(max_length=200, blank=True)
    safety_information = models.TextField(
        blank=True,
        help_text="Important safety information for lab users"
    )
    image = models.ImageField(
        upload_to='about_page/',
        blank=True,
        null=True,
        help_text="Optional image to display alongside the content"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only one AboutPage can be active at a time"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_aboutpage'
        verbose_name = "About Page"
        verbose_name_plural = "About Pages"

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"

    def save(self, *args, **kwargs):
        if self.is_active:
            AboutPage.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active(cls):
        """Get the currently active about page."""
        return cls.objects.filter(is_active=True).first()


class LabSettings(models.Model):
    """Lab customization settings for the free version."""
    
    lab_name = models.CharField(
        max_length=100, 
        default="Aperture Booking",
        help_text="Name of your lab or facility (displayed throughout the application)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only one LabSettings instance can be active at a time"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Lab Settings"
        verbose_name_plural = "Lab Settings"
        db_table = "booking_labsettings"
    
    def __str__(self):
        return f"Lab Settings: {self.lab_name}"
    
    def save(self, *args, **kwargs):
        if self.is_active:
            LabSettings.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active(cls):
        """Get the currently active lab settings."""
        return cls.objects.filter(is_active=True).first()
    
    @classmethod
    def get_lab_name(cls):
        """Get the current lab name, with fallback to default."""
        settings = cls.get_active()
        return settings.lab_name if settings else "Aperture Booking"


class NotificationPreference(models.Model):
    """User notification preferences."""
    NOTIFICATION_TYPES = [
        ('booking_confirmed', 'Booking Confirmed'),
        ('booking_cancelled', 'Booking Cancelled'), 
        ('booking_reminder', 'Booking Reminder'),
        ('booking_overridden', 'Booking Overridden'),
        ('approval_request', 'Approval Request'),
        ('approval_decision', 'Approval Decision'),
        ('maintenance_alert', 'Maintenance Alert'),
        ('conflict_detected', 'Conflict Detected'),
        ('quota_warning', 'Quota Warning'),
        ('waitlist_joined', 'Joined Waiting List'),
        ('waitlist_availability', 'Waiting List Slot Available'),
        ('waitlist_cancelled', 'Left Waiting List'),
        ('access_request_submitted', 'Access Request Submitted'),
        ('access_request_approved', 'Access Request Approved'),
        ('access_request_rejected', 'Access Request Rejected'),
        ('training_request_submitted', 'Training Request Submitted'),
        ('training_request_scheduled', 'Training Scheduled'),
        ('training_request_completed', 'Training Completed'),
        ('training_request_cancelled', 'Training Cancelled'),
    ]
    
    DELIVERY_METHODS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'In-App'),
        ('push', 'Push Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS)
    is_enabled = models.BooleanField(default=True)
    frequency = models.CharField(max_length=20, default='immediate', choices=[
        ('immediate', 'Immediate'),
        ('daily_digest', 'Daily Digest'),
        ('weekly_digest', 'Weekly Digest'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_notificationpreference'
        unique_together = ['user', 'notification_type', 'delivery_method']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()} via {self.get_delivery_method_display()}"


class PushSubscription(models.Model):
    """User push notification subscription details."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500)
    p256dh_key = models.CharField(max_length=100, help_text="Public key for encryption")
    auth_key = models.CharField(max_length=50, help_text="Authentication secret")
    user_agent = models.CharField(max_length=200, blank=True, help_text="Browser/device info")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_pushsubscription'
        unique_together = ['user', 'endpoint']
    
    def __str__(self):
        return f"{self.user.username} - {self.endpoint[:50]}..."
    
    def to_dict(self):
        """Convert subscription to dictionary format for pywebpush."""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh_key,
                "auth": self.auth_key
            }
        }


class Notification(models.Model):
    """Individual notification instances."""
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NotificationPreference.NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    delivery_method = models.CharField(max_length=20, choices=NotificationPreference.DELIVERY_METHODS)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Related objects
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, null=True, blank=True)
    resource = models.ForeignKey('Resource', on_delete=models.CASCADE, null=True, blank=True)
    maintenance = models.ForeignKey('Maintenance', on_delete=models.CASCADE, null=True, blank=True)
    access_request = models.ForeignKey('AccessRequest', on_delete=models.CASCADE, null=True, blank=True)
    training_request = models.ForeignKey('TrainingRequest', on_delete=models.CASCADE, null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Retry logic
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'booking_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['notification_type', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username} ({self.status})"
    
    def mark_as_sent(self):
        """Mark notification as sent."""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])
    
    def mark_as_read(self):
        """Mark notification as read."""
        self.status = 'read'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at', 'updated_at'])
    
    def mark_as_failed(self, reason=None):
        """Mark notification as failed and handle retry logic."""
        self.status = 'failed'
        self.retry_count += 1
        if self.retry_count < self.max_retries:
            # Exponential backoff: 5min, 15min, 45min
            delay_minutes = 5 * (3 ** (self.retry_count - 1))
            self.next_retry_at = timezone.now() + timedelta(minutes=delay_minutes)
            self.status = 'pending'  # Reset to pending for retry
        
        # Store the failure reason in metadata
        if reason:
            if 'failure_reasons' not in self.metadata:
                self.metadata['failure_reasons'] = []
            self.metadata['failure_reasons'].append({
                'reason': reason,
                'timestamp': timezone.now().isoformat(),
                'retry_count': self.retry_count
            })
        
        self.save(update_fields=['status', 'retry_count', 'next_retry_at', 'metadata', 'updated_at'])
    
    def can_retry(self):
        """Check if notification can be retried."""
        return (
            self.retry_count < self.max_retries and
            self.next_retry_at and
            timezone.now() >= self.next_retry_at
        )


class EmailTemplate(models.Model):
    """Email templates for different notification types."""
    name = models.CharField(max_length=100, unique=True)
    notification_type = models.CharField(max_length=30, choices=NotificationPreference.NOTIFICATION_TYPES)
    subject_template = models.CharField(max_length=200)
    html_template = models.TextField()
    text_template = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Template variables documentation
    available_variables = models.JSONField(default=list, help_text="List of available template variables")
    
    class Meta:
        db_table = 'booking_emailtemplate'
    
    def __str__(self):
        return f"{self.name} ({self.get_notification_type_display()})"
    
    def render_subject(self, context):
        """Render subject with context variables."""
        from django.template import Template, Context
        template = Template(self.subject_template)
        return template.render(Context(context))
    
    def render_html(self, context):
        """Render HTML content with context variables."""
        from django.template import Template, Context
        template = Template(self.html_template)
        return template.render(Context(context))
    
    def render_text(self, context):
        """Render text content with context variables."""
        from django.template import Template, Context
        template = Template(self.text_template)
        return template.render(Context(context))


class PasswordResetToken(models.Model):
    """Password reset tokens for users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'booking_passwordresettoken'
    
    def is_expired(self):
        """Check if token is expired (1 hour)."""
        return timezone.now() > self.created_at + timedelta(hours=1)
    
    def __str__(self):
        return f"Password reset token for {self.user.username}"


class EmailVerificationToken(models.Model):
    """Email verification tokens for user registration."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'booking_emailverificationtoken'
    
    def is_expired(self):
        """Check if token is expired (24 hours)."""
        return timezone.now() > self.created_at + timedelta(hours=24)
    
    def __str__(self):
        return f"Verification token for {self.user.username}"


class Faculty(models.Model):
    """Academic faculties."""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_faculty'
        verbose_name_plural = 'Faculties'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class College(models.Model):
    """Academic colleges within faculties."""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='colleges')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_college'
        unique_together = [['faculty', 'code'], ['faculty', 'name']]
        ordering = ['faculty__name', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.faculty.name})"


class Department(models.Model):
    """Academic departments within colleges."""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10)
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='departments')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_department'
        unique_together = [['college', 'code'], ['college', 'name']]
        ordering = ['college__faculty__name', 'college__name', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.college.name})"


class UserProfile(models.Model):
    """Extended user profile with role and group information."""
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('researcher', 'Researcher'),
        ('academic', 'Academic'),
        ('technician', 'Technician'),
        ('sysadmin', 'System Administrator'),
    ]
    
    STUDENT_LEVEL_CHOICES = [
        ('undergraduate', 'Undergraduate'),
        ('postgraduate', 'Postgraduate'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    
    # Academic structure
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Research/academic group
    group = models.CharField(max_length=100, blank=True, help_text="Research group or class")
    
    # Role-specific fields
    student_id = models.CharField(max_length=50, blank=True, null=True, help_text="Student ID number")
    student_level = models.CharField(
        max_length=20, 
        choices=STUDENT_LEVEL_CHOICES, 
        blank=True, 
        null=True,
        help_text="Academic level (for students only)"
    )
    staff_number = models.CharField(max_length=50, blank=True, null=True, help_text="Staff ID number")
    
    # Contact and system fields
    phone = models.CharField(max_length=20, blank=True)
    training_level = models.PositiveIntegerField(default=1)
    is_inducted = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    first_login = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="Timestamp of user's first login"
    )
    
    # Timezone and localization
    timezone = models.CharField(
        max_length=50, 
        default='UTC',
        help_text="User's preferred timezone"
    )
    date_format = models.CharField(
        max_length=20,
        choices=[
            ('DD/MM/YYYY', 'DD/MM/YYYY (European)'),
            ('MM/DD/YYYY', 'MM/DD/YYYY (US)'),
            ('YYYY-MM-DD', 'YYYY-MM-DD (ISO)'),
            ('DD-MM-YYYY', 'DD-MM-YYYY'),
            ('DD.MM.YYYY', 'DD.MM.YYYY (German)'),
        ],
        default='DD/MM/YYYY',
        help_text="Preferred date format"
    )
    time_format = models.CharField(
        max_length=10,
        choices=[
            ('24h', '24-hour (13:30)'),
            ('12h', '12-hour (1:30 PM)'),
        ],
        default='24h',
        help_text="Preferred time format"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_userprofile'

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role})"
    
    def clean(self):
        """Validate the user profile data."""
        super().clean()
        
        # Validate academic hierarchy
        if self.department and not self.college:
            raise ValidationError("College is required when department is specified.")
        if self.college and not self.faculty:
            raise ValidationError("Faculty is required when college is specified.")
        if self.department and self.department.college != self.college:
            raise ValidationError("Department must belong to the selected college.")
        if self.college and self.college.faculty != self.faculty:
            raise ValidationError("College must belong to the selected faculty.")
        
        # Role-specific validations
        if self.role == 'student':
            if not self.student_level:
                raise ValidationError("Student level is required for student role.")
        else:
            # Clear student-specific fields for non-students
            if self.student_level:
                raise ValidationError("Student level should only be set for student role.")
        
        # Staff role validations
        staff_roles = ['researcher', 'academic', 'technician', 'sysadmin']
        if self.role in staff_roles:
            if not self.staff_number:
                raise ValidationError(f"Staff number is required for {self.get_role_display()} role.")
        else:
            # Clear staff-specific fields for non-staff
            if self.staff_number:
                raise ValidationError("Staff number should only be set for staff roles.")

    @property
    def can_book_priority(self):
        """Check if user has priority booking privileges."""
        return self.role in ['academic', 'technician', 'sysadmin']

    @property
    def can_create_recurring(self):
        """Check if user can create recurring bookings."""
        return self.role in ['researcher', 'academic', 'technician', 'sysadmin']
    
    @property
    def academic_path(self):
        """Get full academic path as string."""
        parts = []
        if self.faculty:
            parts.append(self.faculty.name)
        if self.college:
            parts.append(self.college.name)
        if self.department:
            parts.append(self.department.name)
        return " > ".join(parts) if parts else "Not specified"
    
    def get_timezone(self):
        """Get user's timezone as a pytz timezone object."""
        import pytz
        try:
            return pytz.timezone(self.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            return pytz.UTC
    
    def to_user_timezone(self, dt):
        """Convert a datetime to user's timezone."""
        if not dt:
            return dt
        
        user_tz = self.get_timezone()
        
        # If datetime is naive, assume it's in UTC
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, pytz.UTC)
        
        return dt.astimezone(user_tz)
    
    def from_user_timezone(self, dt):
        """Convert a datetime from user's timezone to UTC."""
        if not dt:
            return dt
        
        user_tz = self.get_timezone()
        
        # If datetime is naive, assume it's in user's timezone
        if timezone.is_naive(dt):
            dt = user_tz.localize(dt)
        
        return dt.astimezone(pytz.UTC)
    
    def format_datetime(self, dt):
        """Format datetime according to user preferences."""
        if not dt:
            return ""
        
        # Convert to user timezone
        user_dt = self.to_user_timezone(dt)
        
        # Format date
        date_formats = {
            'DD/MM/YYYY': '%d/%m/%Y',
            'MM/DD/YYYY': '%m/%d/%Y',
            'YYYY-MM-DD': '%Y-%m-%d',
            'DD-MM-YYYY': '%d-%m-%Y',
            'DD.MM.YYYY': '%d.%m.%Y',
        }
        date_format = date_formats.get(self.date_format, '%d/%m/%Y')
        
        # Format time
        time_format = '%H:%M' if self.time_format == '24h' else '%I:%M %p'
        
        return user_dt.strftime(f"{date_format} {time_format}")
    
    def format_date(self, dt):
        """Format date according to user preferences."""
        if not dt:
            return ""
        
        user_dt = self.to_user_timezone(dt)
        
        date_formats = {
            'DD/MM/YYYY': '%d/%m/%Y',
            'MM/DD/YYYY': '%m/%d/%Y',
            'YYYY-MM-DD': '%Y-%m-%d',
            'DD-MM-YYYY': '%d-%m-%Y',
            'DD.MM.YYYY': '%d.%m.%Y',
        }
        date_format = date_formats.get(self.date_format, '%d/%m/%Y')
        
        return user_dt.strftime(date_format)
    
    def format_time(self, dt):
        """Format time according to user preferences."""
        if not dt:
            return ""
        
        user_dt = self.to_user_timezone(dt)
        time_format = '%H:%M' if self.time_format == '24h' else '%I:%M %p'
        
        return user_dt.strftime(time_format)
    
    @classmethod
    def get_available_timezones(cls):
        """Get list of common timezones for selection."""
        import pytz
        
        # Common timezones that institutions might use
        common_timezones = [
            'UTC',
            'Europe/London',
            'Europe/Paris',
            'Europe/Berlin',
            'Europe/Rome',
            'Europe/Madrid',
            'Europe/Amsterdam',
            'Europe/Brussels',
            'Europe/Vienna',
            'Europe/Prague',
            'Europe/Warsaw',
            'Europe/Stockholm',
            'Europe/Helsinki',
            'Europe/Athens',
            'US/Eastern',
            'US/Central',
            'US/Mountain',
            'US/Pacific',
            'America/New_York',
            'America/Chicago',
            'America/Denver',
            'America/Los_Angeles',
            'America/Toronto',
            'America/Vancouver',
            'Australia/Sydney',
            'Australia/Melbourne',
            'Australia/Perth',
            'Asia/Tokyo',
            'Asia/Shanghai',
            'Asia/Singapore',
            'Asia/Hong_Kong',
            'Asia/Seoul',
            'Asia/Mumbai',
            'Asia/Dubai',
        ]
        
        # Return as choices for forms
        return [(tz, tz.replace('_', ' ')) for tz in common_timezones]


class Resource(models.Model):
    """Bookable resources (robots, instruments, rooms, etc.)."""
    RESOURCE_TYPES = [
        ('robot', 'Robot'),
        ('instrument', 'Instrument'),
        ('room', 'Room'),
        ('safety_cabinet', 'Safety Cabinet'),
        ('equipment', 'Generic Equipment'),
    ]
    
    name = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200)
    capacity = models.PositiveIntegerField(default=1)
    required_training_level = models.PositiveIntegerField(default=1)
    requires_induction = models.BooleanField(default=False)
    max_booking_hours = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='resources/', blank=True, null=True, help_text="Resource image")
    
    # Sign-off checklist configuration
    requires_checkout_checklist = models.BooleanField(
        default=False,
        help_text="Require users to complete a checklist before checking out"
    )
    checkout_checklist_title = models.CharField(
        max_length=200,
        blank=True,
        default="Pre-Checkout Safety Checklist",
        help_text="Title displayed on the checkout checklist"
    )
    checkout_checklist_description = models.TextField(
        blank=True,
        help_text="Instructions or description shown above the checklist"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_resource'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_resource_type_display()})"

    def is_available_for_user(self, user_profile):
        """Check if resource is available for a specific user."""
        # System administrators bypass all restrictions
        if user_profile.role == 'sysadmin':
            return self.is_active
            
        if not self.is_active:
            return False
        if self.requires_induction and not user_profile.is_inducted:
            return False
        if user_profile.training_level < self.required_training_level:
            return False
        return True
    
    def user_has_access(self, user):
        """Check if user has explicit access to this resource."""
        from django.db.models import Q
        from django.utils import timezone
        
        # System administrators always have full access
        try:
            if hasattr(user, 'userprofile') and user.userprofile.role == 'sysadmin':
                return True
        except:
            pass
        
        return ResourceAccess.objects.filter(
            resource=self,
            user=user,
            is_active=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).exists()
    
    def can_user_view_calendar(self, user):
        """Check if user can view the resource calendar."""
        if self.user_has_access(user):
            return True
        
        try:
            return user.userprofile.role in ['technician', 'sysadmin']
        except:
            return False
    
    def get_approval_progress(self, user):
        """Get approval progress information for a user."""
        from django.utils import timezone
        
        progress = {
            'has_access': self.user_has_access(user),
            'stages': []
        }
        
        try:
            user_profile = user.userprofile
        except:
            return progress
        
        # System administrators have automatic access to all resources
        if user_profile.role == 'sysadmin':
            progress['has_access'] = True
            progress['stages'] = [{
                'name': 'System Administrator Access',
                'key': 'sysadmin',
                'required': True,
                'completed': True,
                'status': 'completed',
                'icon': 'bi-shield-check',
                'description': 'Full access granted as System Administrator'
            }]
            progress['overall'] = {
                'total_stages': 1,
                'completed_stages': 1,
                'percentage': 100,
                'all_completed': True
            }
            progress['next_step'] = None
            return progress
        
        # Stage 1: Lab Induction (one-time user requirement)
        induction_stage = {
            'name': 'Lab Induction',
            'key': 'induction',
            'required': True,  # Always required for lab access
            'completed': user_profile.is_inducted,
            'status': 'completed' if user_profile.is_inducted else 'pending',
            'icon': 'bi-shield-check',
            'description': 'One-time general laboratory safety induction'
        }
        progress['stages'].append(induction_stage)
        
        # Stage 2: Equipment-Specific Training Requirements
        required_training = ResourceTrainingRequirement.objects.filter(resource=self)
        training_completed = []
        training_pending = []
        
        for req in required_training:
            user_training = UserTraining.objects.filter(
                user=user,
                course=req.training_course,
                status='completed'
            ).first()
            
            if user_training and user_training.is_valid:
                training_completed.append(req.training_course.title)
            else:
                training_pending.append(req.training_course.title)
        
        training_stage = {
            'name': 'Equipment Training',
            'key': 'training',
            'required': len(required_training) > 0,
            'completed': len(training_pending) == 0 and len(required_training) > 0,
            'status': 'completed' if len(training_pending) == 0 and len(required_training) > 0 else ('not_required' if len(required_training) == 0 else 'pending'),
            'icon': 'bi-mortarboard',
            'description': f'Equipment-specific training: {len(training_completed)} of {len(required_training)} courses completed',
            'details': {
                'completed': training_completed,
                'pending': training_pending,
                'total_required': len(required_training)
            }
        }
        progress['stages'].append(training_stage)
        
        # Stage 3: Risk Assessment
        required_assessments = RiskAssessment.objects.filter(resource=self, is_mandatory=True)
        assessment_completed = []
        assessment_pending = []
        
        for assessment in required_assessments:
            user_assessment = UserRiskAssessment.objects.filter(
                user=user,
                risk_assessment=assessment,
                status='approved'
            ).first()
            
            if user_assessment:
                assessment_completed.append(assessment.title)
            else:
                assessment_pending.append(assessment.title)
        
        risk_stage = {
            'name': 'Risk Assessment',
            'key': 'risk_assessment',
            'required': len(required_assessments) > 0,
            'completed': len(assessment_pending) == 0 and len(required_assessments) > 0,
            'status': 'completed' if len(assessment_pending) == 0 and len(required_assessments) > 0 else ('not_required' if len(required_assessments) == 0 else 'pending'),
            'icon': 'bi-clipboard-check',
            'description': f'{len(assessment_completed)} of {len(required_assessments)} risk assessments completed',
            'details': {
                'completed': assessment_completed,
                'pending': assessment_pending,
                'total_required': len(required_assessments)
            }
        }
        progress['stages'].append(risk_stage)
        
        # Stage 4: Administrative Approval
        pending_request = AccessRequest.objects.filter(
            resource=self,
            user=user,
            status='pending'
        ).first()
        
        approved_request = AccessRequest.objects.filter(
            resource=self,
            user=user,
            status='approved'
        ).first()
        
        admin_stage = {
            'name': 'Administrative Approval',
            'key': 'admin_approval',
            'required': True,
            'completed': progress['has_access'],
            'status': 'completed' if progress['has_access'] else ('pending' if pending_request else 'not_started'),
            'icon': 'bi-person-check',
            'description': 'Final approval by lab administrator',
            'details': {
                'has_pending_request': bool(pending_request),
                'request_date': pending_request.created_at if pending_request else None,
                'approved_date': approved_request.reviewed_at if approved_request else None
            }
        }
        progress['stages'].append(admin_stage)
        
        # Calculate overall progress
        required_stages = [s for s in progress['stages'] if s['required']]
        completed_stages = [s for s in required_stages if s['completed']]
        
        progress['overall'] = {
            'total_stages': len(required_stages),
            'completed_stages': len(completed_stages),
            'percentage': int((len(completed_stages) / len(required_stages)) * 100) if required_stages else 100,
            'all_completed': len(completed_stages) == len(required_stages) and len(required_stages) > 0
        }
        
        # Find the next pending stage for guidance
        next_pending_stage = None
        for stage in progress['stages']:
            if stage['required'] and not stage['completed']:
                next_pending_stage = stage
                break
        
        progress['next_step'] = next_pending_stage
        
        return progress


class ResourceAccess(models.Model):
    """User access permissions to specific resources."""
    ACCESS_TYPES = [
        ('view', 'View Only'),
        ('book', 'View and Book'),
        ('manage', 'Full Management'),
    ]
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='access_permissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_access')
    access_type = models.CharField(max_length=10, choices=ACCESS_TYPES, default='book')
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_access')
    granted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiration date")
    
    class Meta:
        db_table = 'booking_resourceaccess'
        unique_together = ['resource', 'user']
        ordering = ['-granted_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.resource.name} ({self.get_access_type_display()})"
    
    @property
    def is_expired(self):
        """Check if access has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if access is currently valid."""
        return self.is_active and not self.is_expired


class TrainingRequest(models.Model):
    """Requests for training on specific resources."""
    STATUS_CHOICES = [
        ('pending', 'Training Pending'),
        ('scheduled', 'Training Scheduled'),
        ('completed', 'Training Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_requests')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='training_requests')
    requested_level = models.PositiveIntegerField(help_text="Training level being requested")
    current_level = models.PositiveIntegerField(help_text="User's current training level")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Training details
    justification = models.TextField(help_text="Why training is needed")
    training_date = models.DateTimeField(null=True, blank=True, help_text="Scheduled training date")
    completed_date = models.DateTimeField(null=True, blank=True, help_text="When training was completed")
    
    # Review information
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_training_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_trainingrequest'
        ordering = ['-created_at']
        unique_together = ['user', 'resource', 'status']  # Prevent duplicate pending requests
    
    def __str__(self):
        return f"{self.user.username} requesting level {self.requested_level} training for {self.resource.name}"
    
    def complete_training(self, reviewed_by, completed_date=None):
        """Mark training as completed and update user's training level."""
        self.status = 'completed'
        self.completed_date = completed_date or timezone.now()
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.save()
        
        # Update user's training level
        user_profile = self.user.userprofile
        if user_profile.training_level < self.requested_level:
            user_profile.training_level = self.requested_level
            user_profile.save()
        
        # Send notification
        try:
            from .notifications import training_request_notifications
            training_request_notifications.training_request_completed(self)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send training completion notification: {e}")
    
    def schedule_training(self, training_date, reviewed_by, notes=""):
        """Schedule training for the user."""
        self.status = 'scheduled'
        self.training_date = training_date
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
        
        # Send notification
        try:
            from .notifications import training_request_notifications
            training_request_notifications.training_request_scheduled(self, training_date)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send training scheduled notification: {e}")
    
    def cancel_training(self, cancelled_by, reason=""):
        """Cancel the training request."""
        if self.status not in ['pending', 'scheduled']:
            raise ValueError("Can only cancel pending or scheduled training")
        
        self.status = 'cancelled'
        self.reviewed_by = cancelled_by
        self.reviewed_at = timezone.now()
        self.review_notes = reason
        self.save()
        
        # Send notification
        try:
            from .notifications import training_request_notifications
            training_request_notifications.training_request_cancelled(self, cancelled_by, reason)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send training cancellation notification: {e}")


class AccessRequest(models.Model):
    """Requests for resource access."""
    REQUEST_TYPES = [
        ('view', 'View Only'),
        ('book', 'View and Book'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='access_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_requests')
    access_type = models.CharField(max_length=10, choices=REQUEST_TYPES, default='book')
    justification = models.TextField(help_text="Why do you need access to this resource?")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Approval workflow
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_access_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Duration request
    requested_duration_days = models.PositiveIntegerField(null=True, blank=True, help_text="Requested access duration in days")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_accessrequest'
        ordering = ['-created_at']
        unique_together = ['resource', 'user', 'status']  # Prevent duplicate pending requests
    
    def __str__(self):
        return f"{self.user.username} requesting {self.get_access_type_display()} access to {self.resource.name}"
    
    def approve(self, reviewed_by, review_notes="", expires_in_days=None):
        """Approve the access request and create ResourceAccess."""
        if self.status != 'pending':
            raise ValueError("Can only approve pending requests")
        
        # Create the access permission
        expires_at = None
        if expires_in_days or self.requested_duration_days:
            days = expires_in_days or self.requested_duration_days
            expires_at = timezone.now() + timedelta(days=days)
        
        ResourceAccess.objects.update_or_create(
            resource=self.resource,
            user=self.user,
            defaults={
                'access_type': self.access_type,
                'granted_by': reviewed_by,
                'is_active': True,
                'expires_at': expires_at,
                'notes': f"Approved via request: {review_notes}" if review_notes else "Approved via access request"
            }
        )
        
        # Update request status
        self.status = 'approved'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.review_notes = review_notes
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_notes', 'updated_at'])
        
        # Send notification
        try:
            from .notifications import access_request_notifications
            access_request_notifications.access_request_approved(self, reviewed_by)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send access request approval notification: {e}")
    
    def reject(self, reviewed_by, review_notes=""):
        """Reject the access request."""
        if self.status != 'pending':
            raise ValueError("Can only reject pending requests")
        
        self.status = 'rejected'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.review_notes = review_notes
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_notes', 'updated_at'])
        
        # Send notification
        try:
            from .notifications import access_request_notifications
            access_request_notifications.access_request_rejected(self, reviewed_by, review_notes)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send access request rejection notification: {e}")
    
    def cancel(self):
        """Cancel the access request."""
        if self.status != 'pending':
            raise ValueError("Can only cancel pending requests")
        
        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])
    
    def get_approval_requirements(self):
        """Get all requirements that must be met before approval."""
        requirements = {
            'training': [],
            'risk_assessments': [],
            'responsible_persons': []
        }
        
        # Get required training courses
        training_requirements = self.resource.training_requirements.filter(
            is_mandatory=True
        ).select_related('training_course')
        
        for req in training_requirements:
            # Check if access type requires this training
            if not req.required_for_access_types or self.access_type in req.required_for_access_types:
                requirements['training'].append(req.training_course)
        
        # Get required risk assessments
        risk_assessments = self.resource.risk_assessments.filter(
            is_mandatory=True,
            is_active=True
        )
        requirements['risk_assessments'] = list(risk_assessments)
        
        # Get responsible persons who can approve
        responsible_persons = self.resource.responsible_persons.filter(
            is_active=True,
            can_approve_access=True
        ).select_related('user')
        requirements['responsible_persons'] = list(responsible_persons)
        
        return requirements
    
    def check_user_compliance(self):
        """Check if user meets all requirements for access."""
        compliance = {
            'training_complete': True,
            'risk_assessments_complete': True,
            'missing_training': [],
            'missing_assessments': [],
            'can_approve': False
        }
        
        requirements = self.get_approval_requirements()
        
        # Check training requirements
        for training_course in requirements['training']:
            user_training = UserTraining.objects.filter(
                user=self.user,
                training_course=training_course,
                status='completed',
                passed=True
            ).first()
            
            if not user_training or not user_training.is_valid:
                compliance['training_complete'] = False
                compliance['missing_training'].append(training_course)
        
        # Check risk assessment requirements
        for risk_assessment in requirements['risk_assessments']:
            user_assessment = UserRiskAssessment.objects.filter(
                user=self.user,
                risk_assessment=risk_assessment,
                status='approved'
            ).first()
            
            if not user_assessment or not user_assessment.is_valid:
                compliance['risk_assessments_complete'] = False
                compliance['missing_assessments'].append(risk_assessment)
        
        # Check if there are responsible persons who can approve
        compliance['can_approve'] = len(requirements['responsible_persons']) > 0
        
        return compliance
    
    def get_required_actions(self):
        """Get list of actions user must complete before approval."""
        compliance = self.check_user_compliance()
        actions = []
        
        # Training actions
        for training in compliance['missing_training']:
            actions.append({
                'type': 'training',
                'title': f"Complete {training.title}",
                'description': f"You must complete the '{training.title}' training course before accessing this resource.",
                'training_course': training,
                'url': f"/training/{training.id}/enroll/"
            })
        
        # Risk assessment actions
        for assessment in compliance['missing_assessments']:
            actions.append({
                'type': 'risk_assessment',
                'title': f"Complete {assessment.title}",
                'description': f"You must complete the '{assessment.title}' risk assessment before accessing this resource.",
                'risk_assessment': assessment,
                'url': f"/assessments/{assessment.id}/start/"
            })
        
        return actions
    
    def can_be_approved_by(self, user):
        """Check if a specific user can approve this request."""
        # Check if user is a responsible person for this resource
        responsible = ResourceResponsible.objects.filter(
            resource=self.resource,
            user=user,
            is_active=True,
            can_approve_access=True
        ).exists()
        
        if responsible:
            return True
        
        # Check if user is a technician or sysadmin (global approval rights)
        try:
            user_profile = user.userprofile
            return user_profile.role in ['technician', 'sysadmin']
        except:
            return False
    
    def get_potential_approvers(self):
        """Get list of users who can approve this request."""
        approvers = []
        
        # Get responsible persons
        responsible_persons = ResourceResponsible.objects.filter(
            resource=self.resource,
            is_active=True,
            can_approve_access=True
        ).select_related('user', 'user__userprofile')
        
        for rp in responsible_persons:
            approvers.append({
                'user': rp.user,
                'role': rp.get_role_type_display(),
                'reason': f"{rp.get_role_type_display()} for {self.resource.name}"
            })
        
        # Get technicians and sysadmins
        global_approvers = UserProfile.objects.filter(
            role__in=['technician', 'sysadmin'],
            user__is_active=True
        ).select_related('user')
        
        for profile in global_approvers:
            approvers.append({
                'user': profile.user,
                'role': profile.get_role_display(),
                'reason': f"Global {profile.get_role_display()} permissions"
            })
        
        return approvers


class BookingTemplate(models.Model):
    """Templates for frequently used booking configurations."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booking_templates')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    title_template = models.CharField(max_length=200)
    description_template = models.TextField(blank=True)
    duration_hours = models.PositiveIntegerField(default=1)
    duration_minutes = models.PositiveIntegerField(default=0)
    preferred_start_time = models.TimeField(null=True, blank=True)
    shared_with_group = models.BooleanField(default=False)
    notes_template = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)  # Visible to other users
    use_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_bookingtemplate'
        ordering = ['-use_count', 'name']
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.name} - {self.resource.name}"

    @property
    def duration(self):
        """Return total duration as timedelta."""
        return timedelta(hours=self.duration_hours, minutes=self.duration_minutes)

    def create_booking_from_template(self, start_time, user=None):
        """Create a new booking from this template."""
        booking_user = user or self.user
        end_time = start_time + self.duration
        
        booking = Booking(
            resource=self.resource,
            user=booking_user,
            title=self.title_template,
            description=self.description_template,
            start_time=start_time,
            end_time=end_time,
            shared_with_group=self.shared_with_group,
            notes=self.notes_template,
        )
        
        # Increment use count
        self.use_count += 1
        self.save(update_fields=['use_count'])
        
        return booking

    def is_accessible_by_user(self, user):
        """Check if user can access this template."""
        if self.user == user:
            return True
        if self.is_public:
            return True
        # Check if same group
        try:
            user_profile = user.userprofile
            template_user_profile = self.user.userprofile
            if (user_profile.group and user_profile.group == template_user_profile.group):
                return True
        except:
            pass
        return False


class Booking(models.Model):
    """Individual booking records."""
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_recurring = models.BooleanField(default=False)
    recurring_pattern = models.JSONField(null=True, blank=True)
    shared_with_group = models.BooleanField(default=False)
    attendees = models.ManyToManyField(User, through='BookingAttendee', related_name='attending_bookings')
    notes = models.TextField(blank=True)
    template_used = models.ForeignKey(BookingTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings_created')
    
    # Booking dependencies
    prerequisite_bookings = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependent_bookings', help_text="Bookings that must be completed before this one")
    dependency_type = models.CharField(max_length=20, choices=[
        ('sequential', 'Sequential (must complete in order)'),
        ('parallel', 'Parallel (can run concurrently after prerequisites)'),
        ('conditional', 'Conditional (depends on outcome of prerequisites)')
    ], default='sequential', help_text="How this booking depends on prerequisites")
    dependency_conditions = models.JSONField(default=dict, blank=True, help_text="Additional dependency conditions")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bookings')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Check-in/Check-out fields
    checked_in_at = models.DateTimeField(null=True, blank=True, help_text="When user actually checked in")
    checked_out_at = models.DateTimeField(null=True, blank=True, help_text="When user actually checked out")
    actual_start_time = models.DateTimeField(null=True, blank=True, help_text="Actual usage start time")
    actual_end_time = models.DateTimeField(null=True, blank=True, help_text="Actual usage end time")
    no_show = models.BooleanField(default=False, help_text="User did not show up for booking")
    auto_checked_out = models.BooleanField(default=False, help_text="System automatically checked out user")
    check_in_reminder_sent = models.BooleanField(default=False)
    check_out_reminder_sent = models.BooleanField(default=False)

    class Meta:
        db_table = 'booking_booking'
        ordering = ['start_time']
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('start_time')),
                name='booking_end_after_start'
            )
        ]

    def __str__(self):
        return f"{self.title} - {self.resource.name} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"

    def clean(self):
        """Validate booking constraints."""
        # Ensure timezone-aware datetimes
        if self.start_time and timezone.is_naive(self.start_time):
            self.start_time = timezone.make_aware(self.start_time)
        if self.end_time and timezone.is_naive(self.end_time):
            self.end_time = timezone.make_aware(self.end_time)
        
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("End time must be after start time.")
            
            # Skip time validation for existing bookings (updates/cancellations)
            if self.pk is not None:
                return
            
            # Check if user is sysadmin - they bypass time restrictions
            is_sysadmin = False
            try:
                if hasattr(self.user, 'userprofile') and self.user.userprofile.role == 'sysadmin':
                    is_sysadmin = True
            except:
                pass
            
            # Only apply time restrictions for non-sysadmin users on new bookings
            if not is_sysadmin:
                # Allow booking up to 5 minutes in the past to account for form submission time
                if self.start_time < timezone.now() - timedelta(minutes=5):
                    raise ValidationError("Cannot book in the past.")
                
                # Check booking window (9 AM - 6 PM) - more lenient check
                if self.start_time.hour < 9 or self.start_time.hour >= 18:
                    raise ValidationError("Booking start time must be between 09:00 and 18:00.")
                    
                if self.end_time.hour > 18 or (self.end_time.hour == 18 and self.end_time.minute > 0):
                    raise ValidationError("Booking must end by 18:00.")
                
                # Check max booking hours if set
                if self.resource and self.resource.max_booking_hours:
                    duration_hours = (self.end_time - self.start_time).total_seconds() / 3600
                    if duration_hours > self.resource.max_booking_hours:
                        raise ValidationError(f"Booking exceeds maximum allowed hours ({self.resource.max_booking_hours}h).")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def duration(self):
        """Return booking duration as timedelta."""
        return self.end_time - self.start_time

    @property
    def can_be_cancelled(self):
        """Check if booking can be cancelled."""
        return self.status in ['pending', 'approved'] and self.start_time > timezone.now()
    
    @property
    def is_checked_in(self):
        """Check if user is currently checked in."""
        return self.checked_in_at is not None and self.checked_out_at is None
    
    @property
    def can_check_in(self):
        """Check if user can check in now."""
        if self.status not in ['approved', 'confirmed']:
            return False
        if self.checked_in_at is not None:  # Already checked in
            return False
        
        now = timezone.now()
        # Allow check-in up to 15 minutes before scheduled start and until end time
        early_checkin_buffer = timedelta(minutes=15)
        return (now >= self.start_time - early_checkin_buffer) and (now <= self.end_time)
    
    @property
    def can_check_out(self):
        """Check if user can check out now."""
        return self.is_checked_in
    
    @property
    def is_overdue_checkin(self):
        """Check if user is overdue for check-in."""
        if self.checked_in_at is not None or self.no_show:
            return False
        
        now = timezone.now()
        # Consider overdue if 15 minutes past start time
        overdue_threshold = self.start_time + timedelta(minutes=15)
        return now > overdue_threshold
    
    @property
    def is_overdue_checkout(self):
        """Check if user is overdue for check-out."""
        if not self.is_checked_in:
            return False
        
        now = timezone.now()
        # Consider overdue if 15 minutes past end time
        overdue_threshold = self.end_time + timedelta(minutes=15)
        return now > overdue_threshold
    
    @property
    def actual_duration(self):
        """Get actual usage duration."""
        if self.actual_start_time and self.actual_end_time:
            return self.actual_end_time - self.actual_start_time
        return None
    
    @property
    def checkin_status(self):
        """Get human-readable check-in status."""
        if self.no_show:
            return "No Show"
        elif self.checked_out_at:
            if self.auto_checked_out:
                return "Auto Checked Out"
            else:
                return "Checked Out"
        elif self.checked_in_at:
            return "Checked In"
        elif self.can_check_in:
            return "Ready to Check In"
        elif self.is_overdue_checkin:
            return "Overdue Check In"
        else:
            return "Not Started"
    
    def check_in(self, user=None, actual_start_time=None):
        """Check in to the booking."""
        if not self.can_check_in:
            raise ValueError("Cannot check in at this time")
        
        now = timezone.now()
        self.checked_in_at = now
        self.actual_start_time = actual_start_time or now
        self.save(update_fields=['checked_in_at', 'actual_start_time', 'updated_at'])
        
        # Create check-in event
        CheckInOutEvent.objects.create(
            booking=self,
            event_type='check_in',
            user=user or self.user,
            timestamp=now,
            actual_time=self.actual_start_time
        )
    
    def check_out(self, user=None, actual_end_time=None):
        """Check out of the booking."""
        if not self.can_check_out:
            raise ValueError("Cannot check out - not checked in")
        
        now = timezone.now()
        self.checked_out_at = now
        self.actual_end_time = actual_end_time or now
        
        # Mark as completed if past end time
        if now >= self.end_time:
            self.status = 'completed'
        
        self.save(update_fields=['checked_out_at', 'actual_end_time', 'status', 'updated_at'])
        
        # Create check-out event
        CheckInOutEvent.objects.create(
            booking=self,
            event_type='check_out',
            user=user or self.user,
            timestamp=now,
            actual_time=self.actual_end_time
        )
    
    def mark_no_show(self, user=None):
        """Mark booking as no-show."""
        if self.checked_in_at is not None:
            raise ValueError("Cannot mark as no-show - user already checked in")
        
        self.no_show = True
        self.status = 'completed'  # Mark as completed with no-show
        self.save(update_fields=['no_show', 'status', 'updated_at'])
        
        # Create no-show event
        CheckInOutEvent.objects.create(
            booking=self,
            event_type='no_show',
            user=user or self.user,
            timestamp=timezone.now()
        )
    
    def auto_check_out(self):
        """Automatically check out user at end time."""
        if not self.is_checked_in:
            return False
        
        now = timezone.now()
        self.checked_out_at = now
        self.actual_end_time = self.end_time  # Use scheduled end time for auto checkout
        self.auto_checked_out = True
        self.status = 'completed'
        
        self.save(update_fields=[
            'checked_out_at', 'actual_end_time', 'auto_checked_out', 'status', 'updated_at'
        ])
        
        # Create auto check-out event
        CheckInOutEvent.objects.create(
            booking=self,
            event_type='auto_check_out',
            user=self.user,
            timestamp=now,
            actual_time=self.actual_end_time
        )
        
        return True
    
    def has_conflicts(self):
        """Check for booking conflicts."""
        conflicts = Booking.objects.filter(
            resource=self.resource,
            status__in=['approved', 'pending'],
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(pk=self.pk)
        
        return conflicts.exists()
    
    @property
    def can_start(self):
        """Check if booking can start based on dependencies."""
        if not self.prerequisite_bookings.exists():
            return True
        
        # Check dependency fulfillment based on type
        if self.dependency_type == 'sequential':
            # All prerequisites must be completed in order
            prerequisites = self.prerequisite_bookings.all().order_by('start_time')
            for prerequisite in prerequisites:
                if prerequisite.status != 'completed':
                    return False
        
        elif self.dependency_type == 'parallel':
            # All prerequisites must be at least approved and started
            for prerequisite in self.prerequisite_bookings.all():
                if prerequisite.status not in ['approved', 'completed'] or not prerequisite.checked_in_at:
                    return False
        
        elif self.dependency_type == 'conditional':
            # Check conditional requirements from dependency_conditions
            conditions = self.dependency_conditions.get('required_outcomes', [])
            for condition in conditions:
                prerequisite_id = condition.get('booking_id')
                required_status = condition.get('status', 'completed')
                try:
                    prerequisite = self.prerequisite_bookings.get(id=prerequisite_id)
                    if prerequisite.status != required_status:
                        return False
                except Booking.DoesNotExist:
                    return False
        
        return True
    
    @property
    def dependency_status(self):
        """Get human-readable dependency status."""
        if not self.prerequisite_bookings.exists():
            return "No dependencies"
        
        if self.can_start:
            return "Dependencies satisfied"
        
        # Count dependency statuses
        prerequisites = self.prerequisite_bookings.all()
        total = prerequisites.count()
        completed = prerequisites.filter(status='completed').count()
        in_progress = prerequisites.filter(
            status='approved',
            checked_in_at__isnull=False,
            checked_out_at__isnull=True
        ).count()
        
        if completed == total:
            return "All dependencies completed"
        elif completed + in_progress == total:
            return f"Dependencies in progress ({completed}/{total} completed)"
        else:
            pending = total - completed - in_progress
            return f"Waiting for dependencies ({completed} completed, {in_progress} in progress, {pending} pending)"
    
    def get_blocking_dependencies(self):
        """Get list of prerequisite bookings that are blocking this one."""
        if self.can_start:
            return []
        
        blocking = []
        for prerequisite in self.prerequisite_bookings.all():
            if self.dependency_type == 'sequential' and prerequisite.status != 'completed':
                blocking.append(prerequisite)
            elif self.dependency_type == 'parallel' and (
                prerequisite.status not in ['approved', 'completed'] or not prerequisite.checked_in_at
            ):
                blocking.append(prerequisite)
            elif self.dependency_type == 'conditional':
                conditions = self.dependency_conditions.get('required_outcomes', [])
                for condition in conditions:
                    if (condition.get('booking_id') == prerequisite.id and 
                        prerequisite.status != condition.get('status', 'completed')):
                        blocking.append(prerequisite)
        
        return blocking
    
    def add_prerequisite(self, prerequisite_booking, dependency_type='sequential', conditions=None):
        """Add a prerequisite booking dependency."""
        if prerequisite_booking == self:
            raise ValidationError("A booking cannot depend on itself")
        
        # Check for circular dependencies
        if self.would_create_circular_dependency(prerequisite_booking):
            raise ValidationError("Adding this prerequisite would create a circular dependency")
        
        # Validate timing for sequential dependencies
        if dependency_type == 'sequential' and self.start_time <= prerequisite_booking.end_time:
            raise ValidationError("Sequential dependencies must start after the prerequisite ends")
        
        self.prerequisite_bookings.add(prerequisite_booking)
        self.dependency_type = dependency_type
        if conditions:
            self.dependency_conditions.update(conditions)
        self.save(update_fields=['dependency_type', 'dependency_conditions'])
    
    def would_create_circular_dependency(self, new_prerequisite):
        """Check if adding a prerequisite would create a circular dependency."""
        def has_dependency_path(booking, target, visited=None):
            if visited is None:
                visited = set()
            
            if booking.id in visited:
                return False  # Already checked this path
            
            visited.add(booking.id)
            
            for dependent in booking.dependent_bookings.all():
                if dependent == target:
                    return True
                if has_dependency_path(dependent, target, visited.copy()):
                    return True
            
            return False
        
        return has_dependency_path(new_prerequisite, self)
    
    def save_as_template(self, template_name, template_description="", is_public=False):
        """Save this booking as a template for future use."""
        template = BookingTemplate.objects.create(
            user=self.user,
            name=template_name,
            description=template_description,
            resource=self.resource,
            title_template=self.title,
            description_template=self.description,
            duration_hours=self.duration.seconds // 3600,
            duration_minutes=(self.duration.seconds % 3600) // 60,
            preferred_start_time=self.start_time.time(),
            shared_with_group=self.shared_with_group,
            notes_template=self.notes,
            is_public=is_public,
        )
        return template


class CheckInOutEvent(models.Model):
    """Track check-in/check-out events for audit purposes."""
    EVENT_TYPES = [
        ('check_in', 'Check In'),
        ('check_out', 'Check Out'),
        ('no_show', 'No Show'),
        ('auto_check_out', 'Auto Check Out'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='checkin_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="User who performed the action")
    timestamp = models.DateTimeField(help_text="When the event occurred")
    actual_time = models.DateTimeField(null=True, blank=True, help_text="Actual start/end time if different from timestamp")
    notes = models.TextField(blank=True)
    
    # Additional tracking fields
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location_data = models.JSONField(default=dict, blank=True, help_text="GPS or location data if available")
    
    class Meta:
        db_table = 'booking_checkinoutevent'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['booking', 'event_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.booking.title} by {self.user.username}"


class UsageAnalytics(models.Model):
    """Aggregated usage analytics for resources."""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='usage_analytics')
    date = models.DateField()
    
    # Booking statistics
    total_bookings = models.PositiveIntegerField(default=0)
    completed_bookings = models.PositiveIntegerField(default=0)
    no_show_bookings = models.PositiveIntegerField(default=0)
    cancelled_bookings = models.PositiveIntegerField(default=0)
    
    # Time statistics (in minutes)
    total_booked_minutes = models.PositiveIntegerField(default=0)
    total_actual_minutes = models.PositiveIntegerField(default=0)
    total_wasted_minutes = models.PositiveIntegerField(default=0)  # Booked but not used
    
    # Efficiency metrics
    utilization_rate = models.FloatField(default=0.0, help_text="Actual usage / Total available time")
    efficiency_rate = models.FloatField(default=0.0, help_text="Actual usage / Booked time")
    no_show_rate = models.FloatField(default=0.0, help_text="No shows / Total bookings")
    
    # Timing statistics
    avg_early_checkin_minutes = models.FloatField(default=0.0)
    avg_late_checkin_minutes = models.FloatField(default=0.0)
    avg_early_checkout_minutes = models.FloatField(default=0.0)
    avg_late_checkout_minutes = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_usageanalytics'
        unique_together = ['resource', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.resource.name} - {self.date} (Utilization: {self.utilization_rate:.1%})"


class BookingAttendee(models.Model):
    """Through model for booking attendees."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'booking_bookingattendee'
        unique_together = ('booking', 'user')

    def __str__(self):
        return f"{self.user.get_full_name()} attending {self.booking.title}"


class WaitingListEntry(models.Model):
    """Waiting list entries for when resources are unavailable."""
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('notified', 'Notified of Availability'),
        ('booked', 'Successfully Booked'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='waiting_list_entries')
    resource = models.ForeignKey('Resource', on_delete=models.CASCADE, related_name='waiting_list_entries')
    
    # Desired booking details
    desired_start_time = models.DateTimeField(help_text="Preferred start time")
    desired_end_time = models.DateTimeField(help_text="Preferred end time")
    title = models.CharField(max_length=200, help_text="Proposed booking title")
    description = models.TextField(blank=True, help_text="Proposed booking description")
    
    # Flexibility options
    flexible_start = models.BooleanField(default=False, help_text="Can start at different time")
    flexible_duration = models.BooleanField(default=False, help_text="Can use shorter duration")
    min_duration_minutes = models.PositiveIntegerField(default=60, help_text="Minimum acceptable duration in minutes")
    max_wait_days = models.PositiveIntegerField(default=7, help_text="Maximum days willing to wait")
    
    # Priority and ordering
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    auto_book = models.BooleanField(default=False, help_text="Automatically book when slot becomes available")
    notification_hours_ahead = models.PositiveIntegerField(default=24, help_text="Hours ahead to notify of availability")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    position = models.PositiveIntegerField(default=1, help_text="Position in waiting list")
    times_notified = models.PositiveIntegerField(default=0)
    last_notification_sent = models.DateTimeField(null=True, blank=True)
    
    # Booking outcomes
    resulting_booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='waiting_list_entry')
    availability_window_start = models.DateTimeField(null=True, blank=True, help_text="When slot became available")
    availability_window_end = models.DateTimeField(null=True, blank=True, help_text="Until when slot is available")
    response_deadline = models.DateTimeField(null=True, blank=True, help_text="Deadline to respond to availability")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When this entry expires")
    
    class Meta:
        db_table = 'booking_waitinglistentry'
        ordering = ['priority', 'position', 'created_at']
        indexes = [
            models.Index(fields=['resource', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['priority', 'position']),
            models.Index(fields=['desired_start_time']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} waiting for {self.resource.name} at {self.desired_start_time}"
    
    def clean(self):
        """Validate waiting list entry."""
        if self.desired_start_time >= self.desired_end_time:
            raise ValidationError("End time must be after start time.")
        
        if self.min_duration_minutes > (self.desired_end_time - self.desired_start_time).total_seconds() / 60:
            raise ValidationError("Minimum duration cannot be longer than desired duration.")
        
        if self.desired_start_time < timezone.now():
            raise ValidationError("Cannot add to waiting list for past time slots.")
    
    def save(self, *args, **kwargs):
        # Set expiration if not already set
        if not self.expires_at:
            self.expires_at = self.desired_start_time + timedelta(days=self.max_wait_days)
        
        # Set position if new entry
        if not self.pk:
            last_position = WaitingListEntry.objects.filter(
                resource=self.resource,
                status='waiting'
            ).aggregate(max_pos=models.Max('position'))['max_pos'] or 0
            self.position = last_position + 1
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if waiting list entry has expired."""
        return self.expires_at and timezone.now() > self.expires_at
    
    @property
    def time_remaining(self):
        """Get time remaining until expiration."""
        if not self.expires_at:
            return None
        remaining = self.expires_at - timezone.now()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)
    
    @property
    def can_auto_book(self):
        """Check if this entry can be auto-booked."""
        return (
            self.auto_book and 
            self.status == 'waiting' and 
            not self.is_expired
        )
    
    def find_available_slots(self, days_ahead=7):
        """Find available time slots that match this waiting list entry."""
        from datetime import datetime, timedelta
        
        search_start = max(self.desired_start_time, timezone.now())
        search_end = search_start + timedelta(days=days_ahead)
        
        slots = []
        current_time = search_start
        desired_duration = self.desired_end_time - self.desired_start_time
        min_duration = timedelta(minutes=self.min_duration_minutes)
        
        while current_time < search_end:
            # Check for conflicts in this time slot
            slot_end = current_time + desired_duration
            
            conflicts = Booking.objects.filter(
                resource=self.resource,
                status__in=['approved', 'pending'],
                start_time__lt=slot_end,
                end_time__gt=current_time
            )
            
            maintenance_conflicts = Maintenance.objects.filter(
                resource=self.resource,
                start_time__lt=slot_end,
                end_time__gt=current_time
            )
            
            if not conflicts.exists() and not maintenance_conflicts.exists():
                # Found available slot
                slots.append({
                    'start_time': current_time,
                    'end_time': slot_end,
                    'duration': desired_duration,
                    'matches_preference': current_time == self.desired_start_time
                })
                
                # If flexible duration, also check for shorter slots
                if self.flexible_duration and desired_duration > min_duration:
                    shorter_end = current_time + min_duration
                    slots.append({
                        'start_time': current_time,
                        'end_time': shorter_end,
                        'duration': min_duration,
                        'matches_preference': False
                    })
            
            # Move to next time slot (increment by 30 minutes)
            current_time += timedelta(minutes=30)
        
        return slots
    
    def notify_of_availability(self, available_slots):
        """Send notification about available slots."""
        self.status = 'notified'
        self.times_notified += 1
        self.last_notification_sent = timezone.now()
        self.response_deadline = timezone.now() + timedelta(hours=self.notification_hours_ahead)
        
        # Store available slots in a temporary field or send in notification
        self.save(update_fields=['status', 'times_notified', 'last_notification_sent', 'response_deadline'])
        
        # Send notification (this would integrate with the notification system)
        from booking.notifications import notification_service
        notification_service.create_notification(
            user=self.user,
            notification_type='waitlist_availability',
            title=f'Resource Available: {self.resource.name}',
            message=f'Your requested resource {self.resource.name} is now available. You have {self.notification_hours_ahead} hours to book.',
            priority='high',
            metadata={
                'waiting_list_entry_id': self.id,
                'available_slots': available_slots,
                'response_deadline': self.response_deadline.isoformat()
            }
        )
    
    def create_booking_from_slot(self, slot):
        """Create a booking from an available slot."""
        if self.status != 'waiting':
            raise ValidationError("Can only create booking from waiting entry")
        
        booking = Booking.objects.create(
            resource=self.resource,
            user=self.user,
            title=self.title,
            description=self.description,
            start_time=slot['start_time'],
            end_time=slot['end_time'],
            status='approved'  # Auto-approve from waiting list
        )
        
        self.resulting_booking = booking
        self.status = 'booked'
        self.save(update_fields=['resulting_booking', 'status'])
        
        # Remove user from waiting list for this resource at this time
        self._reorder_waiting_list()
        
        return booking
    
    def cancel_waiting(self):
        """Cancel this waiting list entry."""
        self.status = 'cancelled'
        self.save(update_fields=['status'])
        self._reorder_waiting_list()
    
    def _reorder_waiting_list(self):
        """Reorder waiting list positions after removal."""
        entries = WaitingListEntry.objects.filter(
            resource=self.resource,
            status='waiting',
            position__gt=self.position
        ).order_by('position')
        
        for i, entry in enumerate(entries):
            entry.position = self.position + i
            entry.save(update_fields=['position'])
    
    @classmethod
    def check_expired_entries(cls):
        """Mark expired waiting list entries and reorder lists."""
        expired_entries = cls.objects.filter(
            status='waiting',
            expires_at__lt=timezone.now()
        )
        
        for entry in expired_entries:
            entry.status = 'expired'
            entry.save(update_fields=['status'])
            entry._reorder_waiting_list()
    
    @classmethod
    def find_opportunities(cls, resource=None):
        """Find booking opportunities for waiting list entries."""
        filters = {'status': 'waiting'}
        if resource:
            filters['resource'] = resource
        
        waiting_entries = cls.objects.filter(**filters).order_by('priority', 'position')
        opportunities = []
        
        for entry in waiting_entries:
            if not entry.is_expired:
                slots = entry.find_available_slots()
                if slots:
                    opportunities.append({
                        'entry': entry,
                        'slots': slots
                    })
        
        return opportunities


class ApprovalRule(models.Model):
    """Rules for booking approval workflows with advanced conditional logic."""
    APPROVAL_TYPES = [
        ('auto', 'Automatic Approval'),
        ('single', 'Single Level Approval'),
        ('tiered', 'Tiered Approval'),
        ('quota', 'Quota Based'),
        ('conditional', 'Conditional Approval'),
    ]
    
    CONDITION_TYPES = [
        ('time_based', 'Time-Based Conditions'),
        ('usage_based', 'Usage-Based Conditions'),
        ('training_based', 'Training-Based Conditions'),
        ('role_based', 'Role-Based Conditions'),
        ('resource_based', 'Resource-Based Conditions'),
        ('custom', 'Custom Logic'),
    ]
    
    name = models.CharField(max_length=200)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='approval_rules')
    approval_type = models.CharField(max_length=20, choices=APPROVAL_TYPES)
    user_roles = models.JSONField(default=list)  # Roles that this rule applies to
    approvers = models.ManyToManyField(User, related_name='approval_rules', blank=True)
    conditions = models.JSONField(default=dict)  # Additional conditions
    
    # Advanced conditional logic
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPES, default='role_based')
    conditional_logic = models.JSONField(default=dict, help_text="Advanced conditional rules")
    fallback_rule = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, help_text="Rule to apply if conditions not met")
    
    # Rule metadata
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True, help_text="Detailed description of when this rule applies")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_approvalrule'
        ordering = ['priority', 'name']

    def __str__(self):
        return f"{self.name} - {self.resource.name}"

    def applies_to_user(self, user_profile):
        """Check if this approval rule applies to a specific user."""
        if not self.is_active:
            return False
        if not self.user_roles:
            return True
        return user_profile.role in self.user_roles
    
    def evaluate_conditions(self, booking_request, user_profile):
        """Evaluate complex conditional logic for approval."""
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        if self.condition_type == 'time_based':
            return self._evaluate_time_conditions(booking_request, user_profile)
        elif self.condition_type == 'usage_based':
            return self._evaluate_usage_conditions(booking_request, user_profile)
        elif self.condition_type == 'training_based':
            return self._evaluate_training_conditions(booking_request, user_profile)
        elif self.condition_type == 'role_based':
            return self._evaluate_role_conditions(booking_request, user_profile)
        elif self.condition_type == 'resource_based':
            return self._evaluate_resource_conditions(booking_request, user_profile)
        elif self.condition_type == 'custom':
            return self._evaluate_custom_conditions(booking_request, user_profile)
        
        return {'approved': False, 'reason': 'Unknown condition type'}
    
    def _evaluate_time_conditions(self, booking_request, user_profile):
        """Evaluate time-based conditions."""
        logic = self.conditional_logic
        
        # Check booking advance time
        if 'min_advance_hours' in logic:
            advance_hours = (booking_request.get('start_time') - timezone.now()).total_seconds() / 3600
            if advance_hours < logic['min_advance_hours']:
                return {'approved': False, 'reason': f'Must book at least {logic["min_advance_hours"]} hours in advance'}
        
        # Check maximum advance booking
        if 'max_advance_days' in logic:
            advance_days = (booking_request.get('start_time') - timezone.now()).days
            if advance_days > logic['max_advance_days']:
                return {'approved': False, 'reason': f'Cannot book more than {logic["max_advance_days"]} days in advance'}
        
        # Check booking duration limits
        if 'max_duration_hours' in logic:
            duration = booking_request.get('duration_hours', 0)
            if duration > logic['max_duration_hours']:
                return {'approved': False, 'reason': f'Booking duration cannot exceed {logic["max_duration_hours"]} hours'}
        
        # Check time of day restrictions
        if 'allowed_hours' in logic:
            start_hour = booking_request.get('start_time').hour
            end_hour = booking_request.get('end_time').hour
            allowed_start, allowed_end = logic['allowed_hours']
            if start_hour < allowed_start or end_hour > allowed_end:
                return {'approved': False, 'reason': f'Bookings only allowed between {allowed_start}:00 and {allowed_end}:00'}
        
        return {'approved': True, 'reason': 'Time conditions met'}
    
    def _evaluate_usage_conditions(self, booking_request, user_profile):
        """Evaluate usage-based conditions."""
        logic = self.conditional_logic
        
        # Check monthly usage quota
        if 'monthly_hour_limit' in logic:
            from datetime import datetime
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Get user's bookings this month for this resource
            monthly_bookings = Booking.objects.filter(
                user=user_profile.user,
                resource=self.resource,
                start_time__gte=current_month,
                status__in=['approved', 'confirmed']
            )
            
            total_hours = sum([
                (b.end_time - b.start_time).total_seconds() / 3600 
                for b in monthly_bookings
            ])
            
            requested_hours = booking_request.get('duration_hours', 0)
            if total_hours + requested_hours > logic['monthly_hour_limit']:
                return {
                    'approved': False, 
                    'reason': f'Monthly usage limit of {logic["monthly_hour_limit"]} hours would be exceeded'
                }
        
        # Check consecutive booking limits
        if 'max_consecutive_days' in logic:
            # Implementation for consecutive booking checking
            pass
        
        return {'approved': True, 'reason': 'Usage conditions met'}
    
    def _evaluate_training_conditions(self, booking_request, user_profile):
        """Evaluate training-based conditions."""
        logic = self.conditional_logic
        
        # Check required certifications
        if 'required_certifications' in logic:
            for cert_code in logic['required_certifications']:
                try:
                    training = UserTraining.objects.get(
                        user=user_profile.user,
                        training_course__code=cert_code,
                        status='completed',
                        passed=True
                    )
                    if training.is_expired:
                        return {
                            'approved': False, 
                            'reason': f'Required certification {cert_code} has expired'
                        }
                except UserTraining.DoesNotExist:
                    return {
                        'approved': False, 
                        'reason': f'Required certification {cert_code} not found'
                    }
        
        # Check minimum training level
        if 'min_training_level' in logic:
            if user_profile.training_level < logic['min_training_level']:
                return {
                    'approved': False, 
                    'reason': f'Minimum training level {logic["min_training_level"]} required'
                }
        
        return {'approved': True, 'reason': 'Training conditions met'}
    
    def _evaluate_role_conditions(self, booking_request, user_profile):
        """Evaluate role-based conditions."""
        logic = self.conditional_logic
        
        # Check role hierarchy
        if 'role_hierarchy' in logic:
            role_levels = logic['role_hierarchy']
            user_level = role_levels.get(user_profile.role, 0)
            required_level = logic.get('min_role_level', 0)
            
            if user_level < required_level:
                return {
                    'approved': False, 
                    'reason': f'Insufficient role level for this resource'
                }
        
        return {'approved': True, 'reason': 'Role conditions met'}
    
    def _evaluate_resource_conditions(self, booking_request, user_profile):
        """Evaluate resource-based conditions."""
        logic = self.conditional_logic
        
        # Check resource availability
        if 'check_conflicts' in logic and logic['check_conflicts']:
            # Enhanced conflict checking beyond basic validation
            pass
        
        return {'approved': True, 'reason': 'Resource conditions met'}
    
    def _evaluate_custom_conditions(self, booking_request, user_profile):
        """Evaluate custom conditional logic."""
        logic = self.conditional_logic
        
        # Support for custom Python expressions (with safety limitations)
        if 'expression' in logic:
            # This would require careful implementation for security
            # For now, return a basic evaluation
            pass
        
        return {'approved': True, 'reason': 'Custom conditions met'}
    
    def get_applicable_rule(self, booking_request, user_profile):
        """Get the most appropriate rule based on conditions."""
        if not self.applies_to_user(user_profile):
            return None
        
        if self.approval_type == 'conditional':
            evaluation = self.evaluate_conditions(booking_request, user_profile)
            if not evaluation['approved']:
                # Try fallback rule
                if self.fallback_rule:
                    return self.fallback_rule.get_applicable_rule(booking_request, user_profile)
                return None
        
        return self


class ResourceResponsible(models.Model):
    """Defines who is responsible for approving access to specific resources."""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='responsible_persons')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='responsible_resources')
    role_type = models.CharField(max_length=50, choices=[
        ('primary', 'Primary Responsible'),
        ('secondary', 'Secondary Responsible'),
        ('trainer', 'Authorized Trainer'),
        ('safety_officer', 'Safety Officer'),
    ], default='primary')
    can_approve_access = models.BooleanField(default=True)
    can_approve_training = models.BooleanField(default=True)
    can_conduct_assessments = models.BooleanField(default=True)
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_responsibilities')
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'booking_resourceresponsible'
        unique_together = ['resource', 'user', 'role_type']
        ordering = ['role_type', 'assigned_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.resource.name} ({self.get_role_type_display()})"
    
    def can_approve_request(self, request_type='access'):
        """Check if this person can approve a specific request type."""
        from django.utils import timezone
        
        # Check if this person can directly approve
        if request_type == 'access' and self.can_approve_access and self.is_active:
            return True
        elif request_type == 'training' and self.can_approve_training and self.is_active:
            return True
        elif request_type == 'assessment' and self.can_conduct_assessments and self.is_active:
            return True
        
        return False
    
    def get_current_approvers(self, request_type='access'):
        """Get list of users who can currently approve."""
        from django.utils import timezone
        approvers = []
        
        # Add this person if they can approve
        if self.can_approve_request(request_type):
            approvers.append({
                'user': self.user,
                'type': 'primary',
                'responsible': self
            })
        
        return approvers




class ApprovalStatistics(models.Model):
    """Track approval workflow statistics for analytics."""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='approval_stats')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_stats')
    
    # Statistics period
    period_start = models.DateField()
    period_end = models.DateField()
    period_type = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], default='monthly')
    
    # Approval counts
    access_requests_received = models.IntegerField(default=0)
    access_requests_approved = models.IntegerField(default=0)
    access_requests_rejected = models.IntegerField(default=0)
    access_requests_pending = models.IntegerField(default=0)
    
    # Training statistics
    training_requests_received = models.IntegerField(default=0)
    training_sessions_conducted = models.IntegerField(default=0)
    training_completions = models.IntegerField(default=0)
    training_failures = models.IntegerField(default=0)
    
    # Risk assessment statistics
    assessments_created = models.IntegerField(default=0)
    assessments_reviewed = models.IntegerField(default=0)
    assessments_approved = models.IntegerField(default=0)
    assessments_rejected = models.IntegerField(default=0)
    
    # Response time metrics (in hours)
    avg_response_time_hours = models.FloatField(default=0.0)
    min_response_time_hours = models.FloatField(default=0.0)
    max_response_time_hours = models.FloatField(default=0.0)
    
    # Additional metrics
    overdue_items = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_approvalstatistics'
        unique_together = ['resource', 'approver', 'period_start', 'period_type']
        ordering = ['-period_start', 'resource', 'approver']
    
    def __str__(self):
        return f"{self.resource.name} - {self.approver.get_full_name()} ({self.period_start})"
    
    @property
    def approval_rate(self):
        """Calculate approval rate percentage."""
        total = self.access_requests_approved + self.access_requests_rejected
        if total == 0:
            return 0
        return (self.access_requests_approved / total) * 100
    
    @property
    def training_success_rate(self):
        """Calculate training success rate percentage."""
        total = self.training_completions + self.training_failures
        if total == 0:
            return 0
        return (self.training_completions / total) * 100
    
    @property
    def assessment_approval_rate(self):
        """Calculate assessment approval rate percentage."""
        total = self.assessments_approved + self.assessments_rejected
        if total == 0:
            return 0
        return (self.assessments_approved / total) * 100
    
    @classmethod
    def generate_statistics(cls, resource=None, approver=None, period_type='monthly', period_start=None):
        """Generate statistics for a given period."""
        from django.utils import timezone
        from datetime import timedelta, date
        from django.db.models import Avg, Min, Max
        
        if period_start is None:
            period_start = timezone.now().date().replace(day=1)  # Start of current month
        
        # Calculate period end based on type
        if period_type == 'daily':
            period_end = period_start
        elif period_type == 'weekly':
            period_end = period_start + timedelta(days=6)
        elif period_type == 'monthly':
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1, day=1) - timedelta(days=1)
        elif period_type == 'quarterly':
            quarter_start_month = ((period_start.month - 1) // 3) * 3 + 1
            period_start = period_start.replace(month=quarter_start_month, day=1)
            period_end = period_start.replace(month=quarter_start_month + 2, day=1)
            if period_end.month == 12:
                period_end = period_end.replace(year=period_end.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                period_end = period_end.replace(month=period_end.month + 1, day=1) - timedelta(days=1)
        elif period_type == 'yearly':
            period_start = period_start.replace(month=1, day=1)
            period_end = period_start.replace(year=period_start.year + 1, month=1, day=1) - timedelta(days=1)
        
        # Filter queryset
        queryset_filters = {
            'created_at__date__range': [period_start, period_end]
        }
        
        if resource:
            queryset_filters['resource'] = resource
        if approver:
            queryset_filters['reviewed_by'] = approver
        
        # Access request statistics
        access_requests = AccessRequest.objects.filter(**queryset_filters)
        access_requests_received = access_requests.count()
        access_requests_approved = access_requests.filter(status='approved').count()
        access_requests_rejected = access_requests.filter(status='rejected').count()
        access_requests_pending = access_requests.filter(status='pending').count()
        
        # Training statistics
        training_filters = queryset_filters.copy()
        if 'reviewed_by' in training_filters:
            training_filters['instructor'] = training_filters.pop('reviewed_by')
        
        training_records = UserTraining.objects.filter(**training_filters)
        training_requests_received = training_records.count()
        training_completions = training_records.filter(status='completed', passed=True).count()
        training_failures = training_records.filter(status='completed', passed=False).count()
        training_sessions_conducted = training_records.filter(session_date__isnull=False).count()
        
        # Risk assessment statistics
        assessment_filters = queryset_filters.copy()
        if 'reviewed_by' in assessment_filters:
            assessment_filters['reviewed_by'] = assessment_filters.pop('reviewed_by')
        
        risk_assessments = UserRiskAssessment.objects.filter(**assessment_filters)
        assessments_reviewed = risk_assessments.filter(status__in=['approved', 'rejected']).count()
        assessments_approved = risk_assessments.filter(status='approved').count()
        assessments_rejected = risk_assessments.filter(status='rejected').count()
        
        # Created assessments (different filter)
        created_filters = queryset_filters.copy()
        if 'reviewed_by' in created_filters:
            created_filters['created_by'] = created_filters.pop('reviewed_by')
        assessments_created = RiskAssessment.objects.filter(**created_filters).count()
        
        # Response time calculations
        response_times = access_requests.filter(
            reviewed_at__isnull=False
        ).extra(
            select={
                'response_hours': '(JULIANDAY(reviewed_at) - JULIANDAY(created_at)) * 24'
            }
        ).values_list('response_hours', flat=True)
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
        
        # Overdue items
        overdue_items = access_requests.filter(
            status='pending',
            created_at__lt=timezone.now() - timedelta(days=3)
        ).count()
        
        return {
            'period_start': period_start,
            'period_end': period_end,
            'period_type': period_type,
            'access_requests_received': access_requests_received,
            'access_requests_approved': access_requests_approved,
            'access_requests_rejected': access_requests_rejected,
            'access_requests_pending': access_requests_pending,
            'training_requests_received': training_requests_received,
            'training_sessions_conducted': training_sessions_conducted,
            'training_completions': training_completions,
            'training_failures': training_failures,
            'assessments_created': assessments_created,
            'assessments_reviewed': assessments_reviewed,
            'assessments_approved': assessments_approved,
            'assessments_rejected': assessments_rejected,
            'avg_response_time_hours': avg_response_time,
            'min_response_time_hours': min_response_time,
            'max_response_time_hours': max_response_time,
            'overdue_items': overdue_items,
        }
    
    @classmethod
    def get_dashboard_data(cls, user=None, resource=None, days=30):
        """Get comprehensive dashboard data for approval workflows."""
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, Avg, Q
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Base filters
        base_filters = {
            'created_at__date__range': [start_date, end_date]
        }
        
        # Access request summary
        access_requests = AccessRequest.objects.filter(**base_filters)
        if user:
            access_requests = access_requests.filter(
                Q(user=user) | Q(reviewed_by=user)
            )
        if resource:
            access_requests = access_requests.filter(resource=resource)
        
        access_summary = {
            'total': access_requests.count(),
            'pending': access_requests.filter(status='pending').count(),
            'approved': access_requests.filter(status='approved').count(),
            'rejected': access_requests.filter(status='rejected').count(),
        }
        
        # Training summary
        training_records = UserTraining.objects.filter(**base_filters)
        if user:
            training_records = training_records.filter(
                Q(user=user) | Q(instructor=user)
            )
        
        training_summary = {
            'total': training_records.count(),
            'completed': training_records.filter(status='completed', passed=True).count(),
            'failed': training_records.filter(status='completed', passed=False).count(),
            'in_progress': training_records.filter(status='in_progress').count(),
        }
        
        # Risk assessment summary
        risk_assessments = UserRiskAssessment.objects.filter(**base_filters)
        if user:
            risk_assessments = risk_assessments.filter(
                Q(user=user) | Q(reviewed_by=user)
            )
        
        assessment_summary = {
            'total': risk_assessments.count(),
            'approved': risk_assessments.filter(status='approved').count(),
            'rejected': risk_assessments.filter(status='rejected').count(),
            'pending': risk_assessments.filter(status='submitted').count(),
        }
        
        # Recent activity
        recent_access_requests = access_requests.order_by('-created_at')[:10]
        recent_training = training_records.order_by('-updated_at')[:10]
        recent_assessments = risk_assessments.order_by('-updated_at')[:10]
        
        # Performance metrics
        if user:
            response_times = access_requests.filter(
                reviewed_by=user,
                reviewed_at__isnull=False
            ).extra(
                select={
                    'response_hours': '(JULIANDAY(reviewed_at) - JULIANDAY(created_at)) * 24'
                }
            ).values_list('response_hours', flat=True)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        else:
            avg_response_time = 0
        
        return {
            'summary': {
                'access_requests': access_summary,
                'training': training_summary,
                'assessments': assessment_summary,
            },
            'recent_activity': {
                'access_requests': recent_access_requests,
                'training': recent_training,
                'assessments': recent_assessments,
            },
            'performance': {
                'avg_response_time_hours': avg_response_time,
                'total_items_processed': (
                    access_summary['approved'] + access_summary['rejected'] +
                    training_summary['completed'] + training_summary['failed'] +
                    assessment_summary['approved'] + assessment_summary['rejected']
                ),
            },
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': days,
            }
        }


class RiskAssessment(models.Model):
    """Risk assessments for resource access."""
    ASSESSMENT_TYPES = [
        ('general', 'General Risk Assessment'),
        ('chemical', 'Chemical Hazard Assessment'),
        ('biological', 'Biological Safety Assessment'),
        ('radiation', 'Radiation Safety Assessment'),
        ('mechanical', 'Mechanical Safety Assessment'),
        ('electrical', 'Electrical Safety Assessment'),
        ('fire', 'Fire Safety Assessment'),
        ('environmental', 'Environmental Impact Assessment'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    title = models.CharField(max_length=200)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='risk_assessments')
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES, default='general')
    description = models.TextField(help_text="Detailed description of the assessment")
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='medium')
    
    # Assessment content
    hazards_identified = models.JSONField(default=list, help_text="List of identified hazards")
    control_measures = models.JSONField(default=list, help_text="Control measures and mitigation steps")
    emergency_procedures = models.TextField(blank=True, help_text="Emergency response procedures")
    ppe_requirements = models.JSONField(default=list, help_text="Personal protective equipment requirements")
    
    # Assessment lifecycle
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_assessments')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_assessments')
    approved_at = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateField(help_text="Assessment expiry date")
    review_frequency_months = models.PositiveIntegerField(default=12, help_text="Review frequency in months")
    
    # Status tracking
    is_active = models.BooleanField(default=True)
    is_mandatory = models.BooleanField(default=True, help_text="Must be completed before access")
    requires_renewal = models.BooleanField(default=True, help_text="Requires periodic renewal")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_riskassessment'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.resource.name}"
    
    @property
    def is_expired(self):
        """Check if the assessment has expired."""
        return timezone.now().date() > self.valid_until
    
    @property
    def is_due_for_review(self):
        """Check if assessment is due for review."""
        if not self.approved_at:
            return True
        review_due = self.approved_at + timedelta(days=self.review_frequency_months * 30)
        return timezone.now() > review_due


class UserRiskAssessment(models.Model):
    """Tracks user completion of risk assessments."""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted for Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='risk_assessments')
    risk_assessment = models.ForeignKey(RiskAssessment, on_delete=models.CASCADE, related_name='user_completions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    # Completion tracking
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Assessment responses
    responses = models.JSONField(default=dict, help_text="User responses to assessment questions")
    assessor_notes = models.TextField(blank=True, help_text="Notes from the person reviewing the assessment")
    user_declaration = models.TextField(blank=True, help_text="User declaration and acknowledgment")
    
    # Review information
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_assessments')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Score and outcome
    score_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pass_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=80.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_userriskassessment'
        unique_together = ['user', 'risk_assessment', 'status']  # Prevent duplicate active assessments
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.risk_assessment.title} ({self.get_status_display()})"
    
    @property
    def is_expired(self):
        """Check if the user's assessment completion has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if the assessment completion is currently valid."""
        return self.status == 'approved' and not self.is_expired
    
    def start_assessment(self):
        """Start the assessment process."""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])
    
    def submit_for_review(self, responses, declaration=""):
        """Submit assessment for review."""
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.responses = responses
        self.user_declaration = declaration
        self.save(update_fields=['status', 'submitted_at', 'responses', 'user_declaration', 'updated_at'])
    
    def approve(self, reviewed_by, score=None, notes=""):
        """Approve the assessment."""
        self.status = 'approved'
        self.completed_at = timezone.now()
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        
        if score is not None:
            self.score_percentage = score
        
        # Set expiry based on risk assessment renewal requirements
        if self.risk_assessment.requires_renewal:
            self.expires_at = timezone.now() + timedelta(days=self.risk_assessment.review_frequency_months * 30)
        
        self.save()
    
    def reject(self, reviewed_by, notes=""):
        """Reject the assessment."""
        self.status = 'rejected'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()


class TrainingCourse(models.Model):
    """Training courses required for resource access."""
    COURSE_TYPES = [
        ('induction', 'General Induction'),
        ('safety', 'Safety Training'),
        ('equipment', 'Equipment Specific Training'),
        ('software', 'Software Training'),
        ('advanced', 'Advanced Certification'),
        ('refresher', 'Refresher Course'),
    ]
    
    DELIVERY_METHODS = [
        ('in_person', 'In-Person Training'),
        ('online', 'Online Training'),
        ('hybrid', 'Hybrid Training'),
        ('self_study', 'Self-Study'),
        ('assessment_only', 'Assessment Only'),
    ]
    
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True, help_text="Unique course code")
    description = models.TextField()
    course_type = models.CharField(max_length=20, choices=COURSE_TYPES, default='equipment')
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS, default='in_person')
    
    # Course requirements
    prerequisite_courses = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='dependent_courses')
    duration_hours = models.DecimalField(max_digits=5, decimal_places=1, help_text="Course duration in hours")
    max_participants = models.PositiveIntegerField(default=10, help_text="Maximum participants per session")
    
    # Content and materials
    learning_objectives = models.JSONField(default=list, help_text="List of learning objectives")
    course_materials = models.JSONField(default=list, help_text="Required materials and resources")
    assessment_criteria = models.JSONField(default=list, help_text="Assessment criteria and methods")
    
    # Validity and renewal
    valid_for_months = models.PositiveIntegerField(default=24, help_text="Certificate validity in months")
    requires_practical_assessment = models.BooleanField(default=False)
    pass_mark_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=80.00)
    
    # Management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_courses')
    instructors = models.ManyToManyField(User, related_name='instructor_courses', blank=True)
    is_active = models.BooleanField(default=True)
    is_mandatory = models.BooleanField(default=False, help_text="Required for all users")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_trainingcourse'
        ordering = ['title']
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    def get_available_instructors(self):
        """Get list of users who can instruct this course."""
        return self.instructors.filter(is_active=True)


class ResourceTrainingRequirement(models.Model):
    """Defines training requirements for specific resources."""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='training_requirements')
    training_course = models.ForeignKey(TrainingCourse, on_delete=models.CASCADE, related_name='resource_requirements')
    is_mandatory = models.BooleanField(default=True, help_text="Must be completed before access")
    required_for_access_types = models.JSONField(default=list, help_text="Access types that require this training")
    order = models.PositiveIntegerField(default=1, help_text="Order in which training should be completed")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_resourcetrainingrequirement'
        unique_together = ['resource', 'training_course']
        ordering = ['order', 'training_course__title']
    
    def __str__(self):
        return f"{self.resource.name} requires {self.training_course.title}"


class UserTraining(models.Model):
    """Tracks user completion of training courses."""
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_records')
    training_course = models.ForeignKey(TrainingCourse, on_delete=models.CASCADE, related_name='user_completions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    
    # Enrollment and completion
    enrolled_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Training session details
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='taught_training')
    session_date = models.DateTimeField(null=True, blank=True)
    session_location = models.CharField(max_length=200, blank=True)
    
    # Assessment results
    theory_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    practical_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    passed = models.BooleanField(default=False)
    
    # Feedback and notes
    instructor_notes = models.TextField(blank=True)
    user_feedback = models.TextField(blank=True)
    
    # Certificate details
    certificate_number = models.CharField(max_length=100, blank=True, unique=True)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_usertraining'
        unique_together = ['user', 'training_course', 'status']  # Prevent duplicate active records
        ordering = ['-completed_at', '-enrolled_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.training_course.title} ({self.get_status_display()})"
    
    @property
    def is_expired(self):
        """Check if the training has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if the training completion is currently valid."""
        return self.status == 'completed' and self.passed and not self.is_expired
    
    def start_training(self):
        """Start the training."""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])
    
    def complete_training(self, theory_score=None, practical_score=None, instructor=None, notes=""):
        """Complete the training with scores."""
        self.theory_score = theory_score
        self.practical_score = practical_score
        self.instructor = instructor
        self.instructor_notes = notes
        
        # Calculate overall score
        if theory_score is not None and practical_score is not None:
            self.overall_score = (theory_score + practical_score) / 2
        elif theory_score is not None:
            self.overall_score = theory_score
        elif practical_score is not None:
            self.overall_score = practical_score
        
        # Check if passed
        if self.overall_score is not None:
            self.passed = self.overall_score >= self.training_course.pass_mark_percentage
        
        if self.passed:
            self.status = 'completed'
            self.completed_at = timezone.now()
            
            # Set expiry date
            if self.training_course.valid_for_months:
                self.expires_at = timezone.now() + timedelta(days=self.training_course.valid_for_months * 30)
            
            # Generate certificate number
            if not self.certificate_number:
                self.certificate_number = f"{self.training_course.code}-{self.user.id}-{timezone.now().strftime('%Y%m%d')}"
                self.certificate_issued_at = timezone.now()
        else:
            self.status = 'failed'
        
        self.save()


class MaintenanceVendor(models.Model):
    """Vendors and service providers for maintenance."""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    
    # Vendor capabilities
    specialties = models.JSONField(default=list, help_text="Areas of expertise (e.g., electrical, mechanical)")
    certifications = models.JSONField(default=list, help_text="Relevant certifications")
    service_areas = models.JSONField(default=list, help_text="Geographic service areas")
    
    # Performance metrics
    average_response_time = models.DurationField(null=True, blank=True, help_text="Average response time for service calls")
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="Vendor rating (1-5)")
    
    # Business details
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    emergency_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_maintenancevendor'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def contract_active(self):
        """Check if vendor contract is currently active."""
        if not self.contract_start_date or not self.contract_end_date:
            return True  # No contract dates = always active
        today = timezone.now().date()
        return self.contract_start_date <= today <= self.contract_end_date


class Maintenance(models.Model):
    """Enhanced maintenance schedules for resources with cost tracking and vendor management."""
    MAINTENANCE_TYPES = [
        ('preventive', 'Preventive Maintenance'),
        ('corrective', 'Corrective Maintenance'),
        ('emergency', 'Emergency Repair'),
        ('calibration', 'Calibration'),
        ('inspection', 'Inspection'),
        ('upgrade', 'Upgrade'),
        ('installation', 'Installation'),
        ('decommission', 'Decommission'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
        ('emergency', 'Emergency'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
        ('overdue', 'Overdue'),
    ]
    
    # Basic maintenance information
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='maintenances')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES, default='preventive')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Vendor and cost information
    vendor = models.ForeignKey(MaintenanceVendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenances')
    is_internal = models.BooleanField(default=True, help_text="Performed by internal staff")
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    labor_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Recurrence and scheduling
    is_recurring = models.BooleanField(default=False)
    recurring_pattern = models.JSONField(null=True, blank=True)
    next_maintenance_date = models.DateTimeField(null=True, blank=True, help_text="When next maintenance is due")
    
    # Impact and dependencies
    blocks_booking = models.BooleanField(default=True)
    affects_other_resources = models.ManyToManyField(Resource, blank=True, related_name='affected_by_maintenance')
    prerequisite_maintenances = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='dependent_maintenances')
    
    # Completion tracking
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    issues_found = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_maintenances')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_maintenances')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_maintenances')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_maintenance'
        ordering = ['start_time']
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('start_time')),
                name='maintenance_end_after_start'
            )
        ]

    def __str__(self):
        return f"{self.title} - {self.resource.name} ({self.start_time.strftime('%Y-%m-%d')})"

    def clean(self):
        """Validate maintenance schedule."""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("End time must be after start time.")
        
        # Validate cost relationships
        if self.actual_cost and self.labor_hours and self.parts_cost:
            if self.vendor and self.vendor.hourly_rate:
                calculated_labor = self.labor_hours * self.vendor.hourly_rate
                expected_total = calculated_labor + self.parts_cost
                if abs(float(self.actual_cost) - float(expected_total)) > 0.01:
                    raise ValidationError("Actual cost should equal labor cost plus parts cost.")

    def save(self, *args, **kwargs):
        # Auto-calculate total cost if not provided
        if not self.actual_cost and self.labor_hours and self.parts_cost:
            if self.vendor and self.vendor.hourly_rate:
                labor_cost = self.labor_hours * self.vendor.hourly_rate
                self.actual_cost = labor_cost + self.parts_cost
        
        # Update status based on dates
        if self.status == 'scheduled':
            now = timezone.now()
            if self.start_time <= now <= self.end_time:
                self.status = 'in_progress'
            elif self.end_time < now and self.status != 'completed':
                self.status = 'overdue'
        
        # Set completion timestamp
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)

    def overlaps_with_booking(self, booking):
        """Check if maintenance overlaps with a booking."""
        return (self.start_time < booking.end_time and 
                self.end_time > booking.start_time)
    
    @property
    def duration(self):
        """Return maintenance duration as timedelta."""
        return self.end_time - self.start_time
    
    @property
    def is_overdue(self):
        """Check if maintenance is overdue."""
        return (self.status in ['scheduled', 'in_progress'] and 
                self.end_time < timezone.now())
    
    @property
    def cost_variance(self):
        """Calculate variance between estimated and actual cost."""
        if self.estimated_cost and self.actual_cost:
            return self.actual_cost - self.estimated_cost
        return None
    
    @property
    def cost_variance_percentage(self):
        """Calculate cost variance as percentage."""
        if self.estimated_cost and self.actual_cost and self.estimated_cost > 0:
            return ((self.actual_cost - self.estimated_cost) / self.estimated_cost) * 100
        return None
    
    def get_affected_bookings(self):
        """Get bookings that are affected by this maintenance."""
        if not self.blocks_booking:
            return Booking.objects.none()
        
        affected_resources = [self.resource] + list(self.affects_other_resources.all())
        return Booking.objects.filter(
            resource__in=affected_resources,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            status__in=['pending', 'approved']
        )
    
    def calculate_impact_score(self):
        """Calculate impact score based on affected bookings and resource importance."""
        affected_bookings = self.get_affected_bookings().count()
        resource_usage = self.resource.bookings.filter(
            start_time__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Base impact on number of affected bookings and recent usage
        impact_score = (affected_bookings * 2) + (resource_usage * 0.1)
        
        # Adjust for priority
        priority_multipliers = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.5,
            'critical': 2.0,
            'emergency': 3.0
        }
        
        return impact_score * priority_multipliers.get(self.priority, 1.0)


class MaintenanceDocument(models.Model):
    """Documentation and files related to maintenance activities."""
    maintenance = models.ForeignKey(Maintenance, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    document_type = models.CharField(max_length=50, choices=[
        ('manual', 'Service Manual'),
        ('checklist', 'Maintenance Checklist'),
        ('invoice', 'Invoice/Receipt'),
        ('report', 'Maintenance Report'),
        ('photo', 'Photograph'),
        ('certificate', 'Certificate'),
        ('warranty', 'Warranty Document'),
        ('other', 'Other'),
    ], default='other')
    
    file = models.FileField(upload_to='maintenance_docs/%Y/%m/')
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Document metadata
    tags = models.JSONField(default=list, help_text="Tags for categorization")
    is_public = models.BooleanField(default=False, help_text="Viewable by all users")
    version = models.CharField(max_length=20, blank=True, help_text="Document version")
    
    class Meta:
        db_table = 'booking_maintenancedocument'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} ({self.maintenance.title})"
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class MaintenanceAlert(models.Model):
    """Predictive maintenance alerts and notifications."""
    ALERT_TYPES = [
        ('due', 'Maintenance Due'),
        ('overdue', 'Maintenance Overdue'),
        ('cost_overrun', 'Cost Overrun'),
        ('vendor_performance', 'Vendor Performance Issue'),
        ('pattern_anomaly', 'Usage Pattern Anomaly'),
        ('predictive', 'Predictive Alert'),
        ('compliance', 'Compliance Reminder'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('urgent', 'Urgent'),
    ]
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='maintenance_alerts')
    maintenance = models.ForeignKey(Maintenance, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='info')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    recommendation = models.TextField(blank=True, help_text="Recommended action")
    
    # Alert data
    alert_data = models.JSONField(default=dict, help_text="Additional alert context")
    threshold_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Status tracking
    is_active = models.BooleanField(default=True)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'booking_maintenancealert'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['resource', 'is_active']),
            models.Index(fields=['alert_type', 'severity']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.resource.name}"
    
    @property
    def is_expired(self):
        """Check if alert has expired."""
        return self.expires_at and timezone.now() > self.expires_at
    
    def acknowledge(self, user):
        """Acknowledge the alert."""
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self):
        """Mark alert as resolved."""
        self.resolved_at = timezone.now()
        self.is_active = False
        self.save()


class MaintenanceAnalytics(models.Model):
    """Analytics and metrics for maintenance activities."""
    resource = models.OneToOneField(Resource, on_delete=models.CASCADE, related_name='maintenance_analytics')
    
    # Cost metrics
    total_maintenance_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    average_maintenance_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preventive_cost_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Percentage of costs from preventive maintenance")
    
    # Time metrics
    total_downtime_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_repair_time = models.DurationField(null=True, blank=True)
    planned_vs_unplanned_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Frequency metrics
    total_maintenance_count = models.PositiveIntegerField(default=0)
    preventive_maintenance_count = models.PositiveIntegerField(default=0)
    corrective_maintenance_count = models.PositiveIntegerField(default=0)
    emergency_maintenance_count = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    first_time_fix_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Percentage of issues fixed on first attempt")
    mean_time_between_failures = models.DurationField(null=True, blank=True)
    mean_time_to_repair = models.DurationField(null=True, blank=True)
    
    # Vendor metrics
    vendor_performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    external_maintenance_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Prediction data
    next_failure_prediction = models.DateTimeField(null=True, blank=True)
    failure_probability = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    recommended_maintenance_interval = models.DurationField(null=True, blank=True)
    
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_maintenanceanalytics'
        verbose_name_plural = 'Maintenance Analytics'
    
    def __str__(self):
        return f"Analytics for {self.resource.name}"
    
    def calculate_metrics(self):
        """Recalculate all maintenance metrics for this resource."""
        maintenances = self.resource.maintenances.all()
        completed_maintenances = maintenances.filter(status='completed')
        
        if not completed_maintenances.exists():
            return
        
        # Cost metrics
        costs = completed_maintenances.exclude(actual_cost__isnull=True).values_list('actual_cost', flat=True)
        if costs:
            self.total_maintenance_cost = sum(costs)
            self.average_maintenance_cost = sum(costs) / len(costs)
        
        preventive_costs = completed_maintenances.filter(
            maintenance_type='preventive'
        ).exclude(actual_cost__isnull=True).aggregate(
            total=models.Sum('actual_cost')
        )['total'] or 0
        
        if self.total_maintenance_cost > 0:
            self.preventive_cost_ratio = (preventive_costs / self.total_maintenance_cost) * 100
        
        # Frequency metrics
        self.total_maintenance_count = maintenances.count()
        self.preventive_maintenance_count = maintenances.filter(maintenance_type='preventive').count()
        self.corrective_maintenance_count = maintenances.filter(maintenance_type='corrective').count()
        self.emergency_maintenance_count = maintenances.filter(maintenance_type='emergency').count()
        
        # Time metrics
        durations = []
        for maintenance in completed_maintenances:
            if maintenance.completed_at and maintenance.start_time:
                duration = maintenance.completed_at - maintenance.start_time
                durations.append(duration.total_seconds() / 3600)  # Convert to hours
        
        if durations:
            self.total_downtime_hours = sum(durations)
            avg_hours = sum(durations) / len(durations)
            self.average_repair_time = timedelta(hours=avg_hours)
        
        # Performance metrics
        # Simple first-time fix rate calculation
        if completed_maintenances.count() > 0:
            repeated_issues = 0
            for maintenance in completed_maintenances:
                # Check if there's another maintenance within 30 days for same type of issue
                related = completed_maintenances.filter(
                    maintenance_type=maintenance.maintenance_type,
                    start_time__gt=maintenance.completed_at,
                    start_time__lt=maintenance.completed_at + timedelta(days=30)
                ).exists()
                if related:
                    repeated_issues += 1
            
            self.first_time_fix_rate = ((completed_maintenances.count() - repeated_issues) / completed_maintenances.count()) * 100
        
        self.save()


class BookingHistory(models.Model):
    """Audit trail for booking changes."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'booking_bookinghistory'
        ordering = ['-timestamp']



class WaitingListNotification(models.Model):
    """Notifications for waiting list availability."""
    waiting_list_entry = models.ForeignKey(WaitingListEntry, on_delete=models.CASCADE, related_name='notifications')
    available_start_time = models.DateTimeField()
    available_end_time = models.DateTimeField()
    
    # Notification details
    sent_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # How long user has to respond
    
    # Response tracking
    response_deadline = models.DateTimeField()
    user_response = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Response'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Response Expired'),
    ], default='pending')
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Auto-booking result
    booking_created = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'booking_waitinglistnotification'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Notification for {self.waiting_list_entry.user.username} - {self.available_start_time}"
    
    def save(self, *args, **kwargs):
        if not self.response_deadline:
            # Give user 2 hours to respond by default
            self.response_deadline = self.sent_at + timedelta(hours=2)
        
        if not self.expires_at:
            # Notification expires when the time slot starts
            self.expires_at = self.available_start_time
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if notification has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def response_time_remaining(self):
        """Time remaining to respond."""
        if self.user_response != 'pending':
            return timedelta(0)
        
        remaining = self.response_deadline - timezone.now()
        return remaining if remaining > timedelta(0) else timedelta(0)
    
    def accept_offer(self):
        """User accepts the time slot offer."""
        if self.user_response != 'pending' or self.is_expired:
            return False
        
        self.user_response = 'accepted'
        self.responded_at = timezone.now()
        self.save(update_fields=['user_response', 'responded_at'])
        
        # Mark waiting list entry as fulfilled
        self.waiting_list_entry.mark_as_fulfilled()
        
        return True
    
    def decline_offer(self):
        """User declines the time slot offer."""
        if self.user_response != 'pending':
            return False
        
        self.user_response = 'declined'
        self.responded_at = timezone.now()
        self.save(update_fields=['user_response', 'responded_at'])
        
        return True


class SystemSetting(models.Model):
    """System-wide configuration settings."""
    
    SETTING_TYPES = [
        ('string', 'Text String'),
        ('integer', 'Integer'),
        ('boolean', 'True/False'),
        ('json', 'JSON Data'),
        ('float', 'Decimal Number'),
    ]
    
    key = models.CharField(max_length=100, unique=True, help_text="Setting identifier")
    value = models.TextField(help_text="Setting value (stored as text)")
    value_type = models.CharField(max_length=10, choices=SETTING_TYPES, default='string')
    description = models.TextField(help_text="What this setting controls")
    category = models.CharField(max_length=50, default='general', help_text="Setting category")
    is_editable = models.BooleanField(default=True, help_text="Can be modified through admin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_systemsetting'
        ordering = ['category', 'key']
    
    def __str__(self):
        return f"{self.key} = {self.value}"
    
    def clean(self):
        """Validate value based on type."""
        if self.value_type == 'integer':
            try:
                int(self.value)
            except ValueError:
                raise ValidationError({'value': 'Must be a valid integer'})
        elif self.value_type == 'float':
            try:
                float(self.value)
            except ValueError:
                raise ValidationError({'value': 'Must be a valid decimal number'})
        elif self.value_type == 'boolean':
            if self.value.lower() not in ['true', 'false', '1', '0']:
                raise ValidationError({'value': 'Must be true/false or 1/0'})
        elif self.value_type == 'json':
            try:
                json.loads(self.value)
            except json.JSONDecodeError:
                raise ValidationError({'value': 'Must be valid JSON'})
    
    def get_value(self):
        """Get typed value."""
        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() in ['true', '1']
        elif self.value_type == 'json':
            return json.loads(self.value)
        else:
            return self.value
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get a setting value by key."""
        try:
            setting = cls.objects.get(key=key)
            return setting.get_value()
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, key, value, value_type='string', description='', category='general'):
        """Set a setting value."""
        if value_type == 'json' and not isinstance(value, str):
            value = json.dumps(value)
        elif value_type == 'boolean':
            value = 'true' if value else 'false'
        else:
            value = str(value)
        
        setting, created = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'value_type': value_type,
                'description': description,
                'category': category
            }
        )
        return setting


class PDFExportSettings(models.Model):
    """PDF export configuration settings."""
    
    QUALITY_CHOICES = [
        ('high', 'High Quality (2x scale)'),
        ('medium', 'Medium Quality (1.5x scale)'),
        ('low', 'Low Quality (1x scale)'),
    ]
    
    ORIENTATION_CHOICES = [
        ('landscape', 'Landscape'),
        ('portrait', 'Portrait'),
    ]
    
    name = models.CharField(max_length=100, unique=True, help_text="Configuration name")
    is_default = models.BooleanField(default=False, help_text="Use as default configuration")
    
    # Export settings
    default_quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='high')
    default_orientation = models.CharField(max_length=10, choices=ORIENTATION_CHOICES, default='landscape')
    include_header = models.BooleanField(default=True, help_text="Include enhanced header")
    include_footer = models.BooleanField(default=True, help_text="Include enhanced footer")
    include_legend = models.BooleanField(default=True, help_text="Include status legend")
    include_details = models.BooleanField(default=True, help_text="Include booking details in footer")
    preserve_colors = models.BooleanField(default=True, help_text="Maintain booking status colors")
    multi_page_support = models.BooleanField(default=True, help_text="Split large calendars across pages")
    compress_pdf = models.BooleanField(default=False, help_text="Compress PDF (smaller file size)")
    
    # Custom styling
    header_logo_url = models.URLField(blank=True, help_text="URL to logo image for PDF header")
    custom_css = models.TextField(blank=True, help_text="Custom CSS for PDF export")
    watermark_text = models.CharField(max_length=100, blank=True, help_text="Watermark text")
    
    # Metadata
    author_name = models.CharField(max_length=100, blank=True, help_text="Default author name")
    organization_name = models.CharField(max_length=100, blank=True, help_text="Organization name")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_pdfexportsettings'
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        default_marker = " (Default)" if self.is_default else ""
        return f"{self.name}{default_marker}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default configuration
        if self.is_default:
            PDFExportSettings.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_default_config(cls):
        """Get the default PDF export configuration."""
        try:
            return cls.objects.get(is_default=True)
        except cls.DoesNotExist:
            # Create default configuration if none exists
            return cls.objects.create(
                name="Default Configuration",
                is_default=True,
                default_quality='high',
                default_orientation='landscape',
                include_header=True,
                include_footer=True,
                include_legend=True,
                include_details=True,
                preserve_colors=True,
                multi_page_support=True,
                compress_pdf=False,
                organization_name="Aperture Booking"
            )
    
    def to_json(self):
        """Convert settings to JSON for frontend use."""
        return {
            'name': self.name,
            'defaultQuality': self.default_quality,
            'defaultOrientation': self.default_orientation,
            'includeHeader': self.include_header,
            'includeFooter': self.include_footer,
            'includeLegend': self.include_legend,
            'includeDetails': self.include_details,
            'preserveColors': self.preserve_colors,
            'multiPageSupport': self.multi_page_support,
            'compressPdf': self.compress_pdf,
            'headerLogoUrl': self.header_logo_url,
            'customCss': self.custom_css,
            'watermarkText': self.watermark_text,
            'authorName': self.author_name,
            'organizationName': self.organization_name
        }


# Onboarding Tutorial System Models

class TutorialCategory(models.Model):
    """Categories for organizing tutorials."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-graduation-cap')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_tutorialcategory'
        ordering = ['order', 'name']
        verbose_name = 'Tutorial Category'
        verbose_name_plural = 'Tutorial Categories'
    
    def __str__(self):
        return self.name


class Tutorial(models.Model):
    """Individual tutorial configurations."""
    TRIGGER_TYPES = [
        ('manual', 'Manual Start'),
        ('first_login', 'First Login'),
        ('role_change', 'Role Change'),
        ('page_visit', 'Page Visit'),
        ('feature_access', 'Feature Access'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TutorialCategory, on_delete=models.CASCADE, related_name='tutorials')
    
    # Targeting
    target_roles = models.JSONField(default=list, help_text="User roles this tutorial applies to")
    target_pages = models.JSONField(default=list, help_text="Pages where this tutorial can be triggered")
    
    # Configuration
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES, default='manual')
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='beginner')
    estimated_duration = models.PositiveIntegerField(help_text="Estimated duration in minutes")
    
    # Content
    steps = models.JSONField(default=list, help_text="Tutorial steps configuration")
    
    # Settings
    is_mandatory = models.BooleanField(default=False, help_text="Whether users must complete this tutorial")
    is_active = models.BooleanField(default=True)
    auto_start = models.BooleanField(default=False, help_text="Auto-start when conditions are met")
    allow_skip = models.BooleanField(default=True, help_text="Allow users to skip this tutorial")
    show_progress = models.BooleanField(default=True, help_text="Show progress indicator")
    
    # Metadata
    version = models.CharField(max_length=10, default='1.0')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tutorials')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_tutorial'
        ordering = ['category__order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
    def is_applicable_for_user(self, user):
        """Check if tutorial applies to a specific user."""
        if not self.is_active:
            return False
        
        if not user.is_authenticated:
            return False
        
        try:
            user_role = user.userprofile.role
        except:
            user_role = 'student'  # Default role
        
        # Check role targeting
        if self.target_roles and user_role not in self.target_roles:
            return False
        
        return True
    
    def get_next_step(self, current_step):
        """Get the next step in the tutorial."""
        if current_step < len(self.steps) - 1:
            return current_step + 1
        return None
    
    def get_step_count(self):
        """Get total number of steps."""
        return len(self.steps)


class UserTutorialProgress(models.Model):
    """Track user progress through tutorials."""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('abandoned', 'Abandoned'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutorial_progress')
    tutorial = models.ForeignKey(Tutorial, on_delete=models.CASCADE, related_name='user_progress')
    
    # Progress tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    current_step = models.PositiveIntegerField(default=0)
    completed_steps = models.JSONField(default=list, help_text="List of completed step indices")
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed_at = models.DateTimeField(auto_now=True)
    
    # Metrics
    time_spent = models.PositiveIntegerField(default=0, help_text="Time spent in seconds")
    attempts = models.PositiveIntegerField(default=0, help_text="Number of times tutorial was started")
    
    # Feedback
    rating = models.PositiveIntegerField(null=True, blank=True, help_text="User rating 1-5")
    feedback = models.TextField(blank=True, help_text="User feedback")
    
    class Meta:
        db_table = 'booking_usertutorialprogress'
        unique_together = ['user', 'tutorial']
        ordering = ['-last_accessed_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.tutorial.name} ({self.status})"
    
    def start_tutorial(self):
        """Start the tutorial."""
        if self.status == 'not_started':
            self.attempts += 1
        
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.current_step = 0
        self.save(update_fields=['status', 'started_at', 'current_step', 'attempts', 'last_accessed_at'])
    
    def complete_step(self, step_index):
        """Mark a step as completed."""
        if step_index not in self.completed_steps:
            self.completed_steps.append(step_index)
            self.completed_steps.sort()
        
        self.current_step = step_index + 1
        self.save(update_fields=['completed_steps', 'current_step', 'last_accessed_at'])
        
        # Check if tutorial is complete
        if len(self.completed_steps) >= self.tutorial.get_step_count():
            self.complete_tutorial()
    
    def complete_tutorial(self):
        """Mark tutorial as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'last_accessed_at'])
    
    def skip_tutorial(self):
        """Mark tutorial as skipped."""
        self.status = 'skipped'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'last_accessed_at'])
    
    @property
    def progress_percentage(self):
        """Calculate completion percentage."""
        total_steps = self.tutorial.get_step_count()
        if total_steps == 0:
            return 100
        return (len(self.completed_steps) / total_steps) * 100
    
    @property
    def is_completed(self):
        """Check if tutorial is completed."""
        return self.status == 'completed'
    
    @property
    def is_in_progress(self):
        """Check if tutorial is in progress."""
        return self.status == 'in_progress'


class TutorialAnalytics(models.Model):
    """Analytics and metrics for tutorials."""
    tutorial = models.OneToOneField(Tutorial, on_delete=models.CASCADE, related_name='analytics')
    
    # Completion metrics
    total_starts = models.PositiveIntegerField(default=0)
    total_completions = models.PositiveIntegerField(default=0)
    total_skips = models.PositiveIntegerField(default=0)
    total_abandons = models.PositiveIntegerField(default=0)
    
    # Time metrics
    average_completion_time = models.PositiveIntegerField(default=0, help_text="Average completion time in seconds")
    average_rating = models.FloatField(default=0.0, help_text="Average user rating")
    
    # Step analytics
    step_completion_rates = models.JSONField(default=dict, help_text="Completion rate for each step")
    step_drop_off_points = models.JSONField(default=list, help_text="Steps where users commonly drop off")
    
    # Updated timestamp
    last_calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_tutorialanalytics'
    
    def __str__(self):
        return f"Analytics for {self.tutorial.name}"
    
    @property
    def completion_rate(self):
        """Calculate completion rate percentage."""
        if self.total_starts == 0:
            return 0
        return (self.total_completions / self.total_starts) * 100
    
    @property
    def skip_rate(self):
        """Calculate skip rate percentage."""
        if self.total_starts == 0:
            return 0
        return (self.total_skips / self.total_starts) * 100
    
    def update_metrics(self):
        """Recalculate all metrics from user progress data."""
        progress_qs = self.tutorial.user_progress.all()
        
        self.total_starts = progress_qs.exclude(status='not_started').count()
        self.total_completions = progress_qs.filter(status='completed').count()
        self.total_skips = progress_qs.filter(status='skipped').count()
        self.total_abandons = progress_qs.filter(status='abandoned').count()
        
        # Calculate average completion time
        completed_progress = progress_qs.filter(status='completed', time_spent__gt=0)
        if completed_progress.exists():
            self.average_completion_time = completed_progress.aggregate(
                models.Avg('time_spent')
            )['time_spent__avg'] or 0
        
        # Calculate average rating
        rated_progress = progress_qs.filter(rating__isnull=False)
        if rated_progress.exists():
            self.average_rating = rated_progress.aggregate(
                models.Avg('rating')
            )['rating__avg'] or 0.0
        
        self.save()


class EmailConfiguration(models.Model):
    """Store and manage email configuration settings."""
    
    # Email Backend Configuration
    BACKEND_CHOICES = [
        ('django.core.mail.backends.smtp.EmailBackend', 'SMTP Email Backend'),
        ('django.core.mail.backends.console.EmailBackend', 'Console Email Backend (Development)'),
        ('django.core.mail.backends.filebased.EmailBackend', 'File-based Email Backend (Testing)'),
        ('django.core.mail.backends.locmem.EmailBackend', 'In-memory Email Backend (Testing)'),
        ('django.core.mail.backends.dummy.EmailBackend', 'Dummy Email Backend (No emails sent)'),
    ]
    
    # Basic Configuration
    is_active = models.BooleanField(
        default=False,
        help_text="Enable this configuration as the active email settings"
    )
    name = models.CharField(
        max_length=100,
        help_text="Descriptive name for this email configuration"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of this configuration"
    )
    
    # Email Backend Settings
    email_backend = models.CharField(
        max_length=100,
        choices=BACKEND_CHOICES,
        default='django.core.mail.backends.smtp.EmailBackend',
        help_text="Django email backend to use"
    )
    
    # SMTP Server Settings
    email_host = models.CharField(
        max_length=255,
        help_text="SMTP server hostname (e.g., smtp.gmail.com)"
    )
    email_port = models.PositiveIntegerField(
        default=587,
        help_text="SMTP server port (587 for TLS, 465 for SSL, 25 for standard)"
    )
    email_use_tls = models.BooleanField(
        default=True,
        help_text="Use TLS (Transport Layer Security) encryption"
    )
    email_use_ssl = models.BooleanField(
        default=False,
        help_text="Use SSL (Secure Sockets Layer) encryption"
    )
    
    # Authentication Settings
    email_host_user = models.CharField(
        max_length=255,
        blank=True,
        help_text="SMTP server username/email address"
    )
    email_host_password = models.CharField(
        max_length=255,
        blank=True,
        help_text="SMTP server password (stored encrypted)"
    )
    
    # Email Addresses
    default_from_email = models.EmailField(
        help_text="Default 'from' email address for outgoing emails"
    )
    server_email = models.EmailField(
        blank=True,
        help_text="Email address used for error messages from Django"
    )
    
    # Advanced Settings
    email_timeout = models.PositiveIntegerField(
        default=10,
        help_text="Timeout in seconds for SMTP connections"
    )
    
    # File-based Backend Settings (for testing)
    email_file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Directory path for file-based email backend"
    )
    
    # Validation and Testing
    is_validated = models.BooleanField(
        default=False,
        help_text="Whether this configuration has been successfully tested"
    )
    last_test_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this configuration was tested"
    )
    last_test_result = models.TextField(
        blank=True,
        help_text="Result of the last configuration test"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_email_configs',
        help_text="User who created this configuration"
    )
    
    class Meta:
        verbose_name = "Email Configuration"
        verbose_name_plural = "Email Configurations"
        ordering = ['-is_active', '-updated_at']
    
    def __str__(self):
        active_indicator = " (Active)" if self.is_active else ""
        return f"{self.name}{active_indicator}"
    
    def clean(self):
        """Validate the configuration settings."""
        super().clean()
        
        # Validate that only one configuration can be active
        if self.is_active:
            existing_active = EmailConfiguration.objects.filter(is_active=True)
            if self.pk:
                existing_active = existing_active.exclude(pk=self.pk)
            
            if existing_active.exists():
                raise ValidationError(
                    "Only one email configuration can be active at a time. "
                    "Please deactivate the current active configuration first."
                )
        
        # Validate SMTP settings for SMTP backend
        if self.email_backend == 'django.core.mail.backends.smtp.EmailBackend':
            if not self.email_host:
                raise ValidationError("Email host is required for SMTP backend.")
            
            if self.email_use_tls and self.email_use_ssl:
                raise ValidationError("Cannot use both TLS and SSL simultaneously.")
        
        # Validate file path for file-based backend
        if self.email_backend == 'django.core.mail.backends.filebased.EmailBackend':
            if not self.email_file_path:
                raise ValidationError("File path is required for file-based email backend.")
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one active configuration."""
        self.full_clean()
        
        # If this configuration is being set as active, deactivate others
        if self.is_active:
            EmailConfiguration.objects.filter(is_active=True).update(is_active=False)
        
        super().save(*args, **kwargs)
    
    def activate(self):
        """Activate this configuration and deactivate others."""
        EmailConfiguration.objects.filter(is_active=True).update(is_active=False)
        self.is_active = True
        self.save()
    
    def deactivate(self):
        """Deactivate this configuration."""
        self.is_active = False
        self.save()
    
    def test_configuration(self, test_email=None):
        """Test this email configuration by sending a test email."""
        from django.core.mail import send_mail
        from django.conf import settings
        import tempfile
        import os
        
        # Temporarily apply this configuration
        original_settings = {}
        test_settings = {
            'EMAIL_BACKEND': self.email_backend,
            'EMAIL_HOST': self.email_host,
            'EMAIL_PORT': self.email_port,
            'EMAIL_USE_TLS': self.email_use_tls,
            'EMAIL_USE_SSL': self.email_use_ssl,
            'EMAIL_HOST_USER': self.email_host_user,
            'EMAIL_HOST_PASSWORD': self.email_host_password,
            'DEFAULT_FROM_EMAIL': self.default_from_email,
            'EMAIL_TIMEOUT': self.email_timeout,
        }
        
        # Handle file-based backend
        if self.email_backend == 'django.core.mail.backends.filebased.EmailBackend':
            if self.email_file_path:
                test_settings['EMAIL_FILE_PATH'] = self.email_file_path
            else:
                test_settings['EMAIL_FILE_PATH'] = tempfile.gettempdir()
        
        # Save original settings
        for key in test_settings:
            if hasattr(settings, key):
                original_settings[key] = getattr(settings, key)
        
        try:
            # Apply test settings
            for key, value in test_settings.items():
                setattr(settings, key, value)
            
            # Send test email
            test_recipient = test_email or self.default_from_email
            subject = f"Email Configuration Test - {self.name}"
            message = f"""
Email Configuration Test

This is a test email sent to verify the email configuration "{self.name}".

Configuration Details:
- Backend: {self.email_backend}
- Host: {self.email_host}
- Port: {self.email_port}
- Use TLS: {self.email_use_tls}
- Use SSL: {self.email_use_ssl}
- From: {self.default_from_email}

If you received this email, the configuration is working correctly!

--
Aperture Booking System
            """.strip()
            
            send_mail(
                subject=subject,
                message=message,
                from_email=self.default_from_email,
                recipient_list=[test_recipient],
                fail_silently=False
            )
            
            # Update test results
            self.is_validated = True
            self.last_test_date = timezone.now()
            self.last_test_result = f"Success: Test email sent to {test_recipient}"
            self.save()
            
            return True, f"Test email sent successfully to {test_recipient}"
            
        except Exception as e:
            # Update test results with error
            self.is_validated = False
            self.last_test_date = timezone.now()
            self.last_test_result = f"Error: {str(e)}"
            self.save()
            
            return False, f"Test failed: {str(e)}"
            
        finally:
            # Restore original settings
            for key, value in original_settings.items():
                setattr(settings, key, value)
            
            # Remove any test settings that weren't originally present
            for key in test_settings:
                if key not in original_settings and hasattr(settings, key):
                    delattr(settings, key)
    
    def apply_to_settings(self):
        """Apply this configuration to Django settings."""
        from django.conf import settings
        
        if not self.is_active:
            return False
        
        # Apply configuration to settings
        settings.EMAIL_BACKEND = self.email_backend
        settings.EMAIL_HOST = self.email_host
        settings.EMAIL_PORT = self.email_port
        settings.EMAIL_USE_TLS = self.email_use_tls
        settings.EMAIL_USE_SSL = self.email_use_ssl
        settings.EMAIL_HOST_USER = self.email_host_user
        settings.EMAIL_HOST_PASSWORD = self.email_host_password
        settings.DEFAULT_FROM_EMAIL = self.default_from_email
        settings.EMAIL_TIMEOUT = self.email_timeout
        
        if self.server_email:
            settings.SERVER_EMAIL = self.server_email
        
        if self.email_backend == 'django.core.mail.backends.filebased.EmailBackend' and self.email_file_path:
            settings.EMAIL_FILE_PATH = self.email_file_path
        
        return True
    
    def get_configuration_dict(self):
        """Return configuration as a dictionary."""
        config = {
            'EMAIL_BACKEND': self.email_backend,
            'EMAIL_HOST': self.email_host,
            'EMAIL_PORT': self.email_port,
            'EMAIL_USE_TLS': self.email_use_tls,
            'EMAIL_USE_SSL': self.email_use_ssl,
            'EMAIL_HOST_USER': self.email_host_user,
            'EMAIL_HOST_PASSWORD': '***' if self.email_host_password else '',
            'DEFAULT_FROM_EMAIL': self.default_from_email,
            'EMAIL_TIMEOUT': self.email_timeout,
        }
        
        if self.server_email:
            config['SERVER_EMAIL'] = self.server_email
        
        if self.email_backend == 'django.core.mail.backends.filebased.EmailBackend' and self.email_file_path:
            config['EMAIL_FILE_PATH'] = self.email_file_path
        
        return config
    
    @classmethod
    def get_active_configuration(cls):
        """Get the currently active email configuration."""
        return cls.objects.filter(is_active=True).first()
    
    @classmethod
    def get_common_configurations(cls):
        """Return a list of common email provider configurations."""
        return [
            {
                'name': 'Gmail SMTP',
                'email_host': 'smtp.gmail.com',
                'email_port': 587,
                'email_use_tls': True,
                'email_use_ssl': False,
                'description': 'Google Gmail SMTP configuration'
            },
            {
                'name': 'Outlook/Hotmail SMTP',
                'email_host': 'smtp-mail.outlook.com',
                'email_port': 587,
                'email_use_tls': True,
                'email_use_ssl': False,
                'description': 'Microsoft Outlook/Hotmail SMTP configuration'
            },
            {
                'name': 'Yahoo Mail SMTP',
                'email_host': 'smtp.mail.yahoo.com',
                'email_port': 587,
                'email_use_tls': True,
                'email_use_ssl': False,
                'description': 'Yahoo Mail SMTP configuration'
            },
            {
                'name': 'SendGrid SMTP',
                'email_host': 'smtp.sendgrid.net',
                'email_port': 587,
                'email_use_tls': True,
                'email_use_ssl': False,
                'description': 'SendGrid email service SMTP configuration'
            },
            {
                'name': 'Mailgun SMTP',
                'email_host': 'smtp.mailgun.org',
                'email_port': 587,
                'email_use_tls': True,
                'email_use_ssl': False,
                'description': 'Mailgun email service SMTP configuration'
            }
        ]


class ChecklistItem(models.Model):
    """Individual checklist item that can be assigned to resources."""
    
    ITEM_TYPES = [
        ('checkbox', 'Checkbox (Yes/No)'),
        ('text', 'Text Input'),
        ('number', 'Number Input'),
        ('select', 'Dropdown Selection'),
        ('textarea', 'Long Text'),
    ]
    
    CATEGORY_CHOICES = [
        ('safety', 'Safety Check'),
        ('equipment', 'Equipment Status'),
        ('cleanliness', 'Cleanliness'),
        ('documentation', 'Documentation'),
        ('maintenance', 'Maintenance Check'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200, help_text="Question or instruction text")
    description = models.TextField(blank=True, help_text="Additional description or guidance")
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='checkbox')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    is_required = models.BooleanField(default=True, help_text="Must be completed to proceed")
    
    # For select/dropdown items
    options = models.JSONField(
        blank=True,
        null=True,
        help_text="JSON array of options for select items, e.g. ['Good', 'Needs Attention', 'Damaged']"
    )
    
    # For validation
    min_value = models.FloatField(null=True, blank=True, help_text="Minimum value for number inputs")
    max_value = models.FloatField(null=True, blank=True, help_text="Maximum value for number inputs")
    max_length = models.IntegerField(null=True, blank=True, help_text="Maximum length for text inputs")
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_checklist_items'
    )
    
    class Meta:
        db_table = 'booking_checklistitem'
        ordering = ['category', 'title']
    
    def __str__(self):
        return f"{self.get_category_display()}: {self.title}"
    
    def clean(self):
        """Validate the checklist item configuration."""
        from django.core.exceptions import ValidationError
        
        if self.item_type == 'select' and not self.options:
            raise ValidationError("Select items must have options defined")
        
        if self.item_type == 'number':
            if self.min_value is not None and self.max_value is not None:
                if self.min_value >= self.max_value:
                    raise ValidationError("Min value must be less than max value")


class ResourceChecklistItem(models.Model):
    """Links checklist items to specific resources with ordering."""
    
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='checklist_items'
    )
    checklist_item = models.ForeignKey(
        ChecklistItem,
        on_delete=models.CASCADE,
        related_name='resource_assignments'
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers first)")
    is_active = models.BooleanField(default=True, help_text="Include this item in the checklist")
    
    # Override settings per resource
    override_required = models.BooleanField(
        default=False,
        help_text="Override the default required setting for this resource"
    )
    is_required_override = models.BooleanField(
        default=True,
        help_text="Required setting when override is enabled"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_resourcechecklistitem'
        ordering = ['order', 'checklist_item__category', 'checklist_item__title']
        unique_together = ['resource', 'checklist_item']
    
    def __str__(self):
        return f"{self.resource.name} - {self.checklist_item.title}"
    
    @property
    def is_required(self):
        """Get the effective required status for this item."""
        if self.override_required:
            return self.is_required_override
        return self.checklist_item.is_required


class ChecklistResponse(models.Model):
    """User responses to checklist items during checkout."""
    
    booking = models.ForeignKey(
        'Booking',
        on_delete=models.CASCADE,
        related_name='checklist_responses'
    )
    checklist_item = models.ForeignKey(
        ChecklistItem,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    
    # Response data
    text_response = models.TextField(blank=True, help_text="Text/textarea responses")
    number_response = models.FloatField(null=True, blank=True, help_text="Number responses")
    boolean_response = models.BooleanField(null=True, blank=True, help_text="Checkbox responses")
    select_response = models.CharField(max_length=200, blank=True, help_text="Selected option")
    
    # Metadata
    completed_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    
    # Validation status
    is_valid = models.BooleanField(default=True, help_text="Whether the response passes validation")
    validation_notes = models.TextField(blank=True, help_text="Notes about validation issues")
    
    class Meta:
        db_table = 'booking_checklistresponse'
        unique_together = ['booking', 'checklist_item']
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.booking} - {self.checklist_item.title}"
    
    def get_response_value(self):
        """Get the actual response value based on item type."""
        item_type = self.checklist_item.item_type
        
        if item_type == 'checkbox':
            return self.boolean_response
        elif item_type == 'number':
            return self.number_response
        elif item_type == 'select':
            return self.select_response
        else:  # text, textarea
            return self.text_response
    
    def validate_response(self):
        """Validate the response against the checklist item constraints."""
        item = self.checklist_item
        value = self.get_response_value()
        
        # Required field validation
        if item.is_required and value in [None, '', False]:
            self.is_valid = False
            self.validation_notes = "This field is required"
            return False
        
        # Type-specific validation
        if item.item_type == 'number' and self.number_response is not None:
            if item.min_value is not None and self.number_response < item.min_value:
                self.is_valid = False
                self.validation_notes = f"Value must be at least {item.min_value}"
                return False
            if item.max_value is not None and self.number_response > item.max_value:
                self.is_valid = False
                self.validation_notes = f"Value must be at most {item.max_value}"
                return False
        
        if item.item_type in ['text', 'textarea'] and self.text_response:
            if item.max_length and len(self.text_response) > item.max_length:
                self.is_valid = False
                self.validation_notes = f"Text must be {item.max_length} characters or less"
                return False
        
        if item.item_type == 'select' and self.select_response:
            if item.options and self.select_response not in item.options:
                self.is_valid = False
                self.validation_notes = "Invalid selection"
                return False
        
        self.is_valid = True
        self.validation_notes = ""
        return True


class BackupSchedule(models.Model):
    """Model for managing automated backup schedules."""
    
    FREQUENCY_CHOICES = [
        ('disabled', 'Disabled'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    DAY_OF_WEEK_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    # Basic scheduling
    name = models.CharField(max_length=200, default="Automated Backup")
    enabled = models.BooleanField(default=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='weekly')
    
    # Time settings
    backup_time = models.TimeField(default='02:00', help_text="Time of day to run backup (24-hour format)")
    day_of_week = models.IntegerField(
        choices=DAY_OF_WEEK_CHOICES, 
        default=6,  # Sunday
        help_text="Day of week for weekly backups"
    )
    day_of_month = models.IntegerField(
        default=1,
        help_text="Day of month for monthly backups (1-28)"
    )
    
    # Backup options
    include_media = models.BooleanField(default=True, help_text="Include media files in automated backups")
    include_database = models.BooleanField(default=True, help_text="Include database in automated backups")
    include_configuration = models.BooleanField(default=True, help_text="Include configuration analysis in automated backups")
    
    # Retention settings
    max_backups_to_keep = models.IntegerField(
        default=7,
        help_text="Maximum number of automated backups to keep (older ones will be deleted)"
    )
    retention_days = models.IntegerField(
        default=30,
        help_text="Days to keep automated backups before deletion"
    )
    
    # Status tracking
    last_run = models.DateTimeField(null=True, blank=True)
    last_success = models.DateTimeField(null=True, blank=True)
    last_backup_name = models.CharField(max_length=255, blank=True)
    consecutive_failures = models.IntegerField(default=0)
    total_runs = models.IntegerField(default=0)
    total_successes = models.IntegerField(default=0)
    
    # Error tracking
    last_error = models.TextField(blank=True)
    notification_email = models.EmailField(
        blank=True,
        help_text="Email to notify on backup failures (leave blank to disable)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Backup Schedule"
        verbose_name_plural = "Backup Schedules"
    
    def __str__(self):
        status = "Enabled" if self.enabled else "Disabled"
        return f"{self.name} ({self.frequency}, {status})"
    
    def clean(self):
        """Validate backup schedule settings."""
        if self.day_of_month < 1 or self.day_of_month > 28:
            raise ValidationError("Day of month must be between 1 and 28")
        
        if self.max_backups_to_keep < 1:
            raise ValidationError("Must keep at least 1 backup")
        
        if self.retention_days < 1:
            raise ValidationError("Retention period must be at least 1 day")
        
        if not any([self.include_database, self.include_media, self.include_configuration]):
            raise ValidationError("At least one backup component must be selected")
    
    def get_next_run_time(self):
        """Calculate the next scheduled run time."""
        from datetime import datetime, time, timedelta
        import calendar
        
        if not self.enabled or self.frequency == 'disabled':
            return None
        
        now = timezone.now()
        today = now.date()
        
        # Ensure backup_time is a time object
        backup_time = self.backup_time
        if isinstance(backup_time, str):
            from datetime import time as datetime_time
            try:
                # Parse string format like "14:30" or "02:00"
                hour, minute = backup_time.split(':')
                backup_time = datetime_time(int(hour), int(minute))
            except (ValueError, AttributeError):
                # Fallback to default time if parsing fails
                backup_time = datetime_time(2, 0)  # 2:00 AM
        
        current_time = now.time()
        
        if self.frequency == 'daily':
            # Next run is today if time hasn't passed, otherwise tomorrow
            next_date = today
            if current_time > backup_time:
                next_date = today + timedelta(days=1)
                
        elif self.frequency == 'weekly':
            # Find next occurrence of the specified day of week
            days_ahead = self.day_of_week - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_date = today + timedelta(days=days_ahead)
            
            # If it's the target day but time hasn't passed yet, use today
            if days_ahead == 7 and current_time <= backup_time:
                next_date = today
                
        elif self.frequency == 'monthly':
            # Find next occurrence of the specified day of month
            if today.day < self.day_of_month and current_time <= backup_time:
                # This month, day hasn't passed yet
                next_date = today.replace(day=self.day_of_month)
            else:
                # Next month
                if today.month == 12:
                    next_month = today.replace(year=today.year + 1, month=1, day=self.day_of_month)
                else:
                    next_month = today.replace(month=today.month + 1, day=self.day_of_month)
                next_date = next_month
        
        else:
            return None
        
        return timezone.make_aware(datetime.combine(next_date, backup_time))
    
    def should_run_now(self):
        """Check if backup should run now based on schedule."""
        if not self.enabled or self.frequency == 'disabled':
            return False
        
        next_run = self.get_next_run_time()
        if not next_run:
            return False
        
        now = timezone.now()
        # Allow a 5-minute window for execution
        return abs((now - next_run).total_seconds()) <= 300
    
    def record_run(self, success=True, backup_name='', error_message=''):
        """Record the results of a backup run."""
        now = timezone.now()
        self.last_run = now
        self.total_runs += 1
        
        if success:
            self.last_success = now
            self.last_backup_name = backup_name
            self.total_successes += 1
            self.consecutive_failures = 0
            self.last_error = ''
        else:
            self.consecutive_failures += 1
            self.last_error = error_message
        
        self.save(update_fields=['last_run', 'last_success', 'last_backup_name', 
                                'total_runs', 'total_successes', 'consecutive_failures', 'last_error'])
    
    @property
    def success_rate(self):
        """Calculate backup success rate as percentage."""
        if self.total_runs == 0:
            return 0
        return round((self.total_successes / self.total_runs) * 100, 1)
    
    @property
    def is_healthy(self):
        """Check if backup schedule is considered healthy."""
        if not self.enabled:
            return True
        
        # More than 3 consecutive failures is concerning
        if self.consecutive_failures > 3:
            return False
        
        # No successful backup in the last 7 days (for enabled schedules)
        if self.last_success:
            days_since_success = (timezone.now() - self.last_success).days
            if days_since_success > 7:
                return False
        elif self.total_runs > 0:
            # Has run but never succeeded
            return False
        
        return True


class UpdateInfo(models.Model):
    """Track application updates and version information."""
    
    STATUS_CHOICES = [
        ('checking', 'Checking for Updates'),
        ('available', 'Update Available'),
        ('downloading', 'Downloading Update'),
        ('ready', 'Ready to Install'),
        ('installing', 'Installing Update'),
        ('completed', 'Update Completed'),
        ('failed', 'Update Failed'),
        ('up_to_date', 'Up to Date'),
    ]
    
    current_version = models.CharField(max_length=50, help_text="Currently installed version")
    latest_version = models.CharField(max_length=50, blank=True, help_text="Latest available version")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='up_to_date')
    
    # Release information
    release_url = models.URLField(blank=True, help_text="GitHub release URL")
    release_notes = models.TextField(blank=True, help_text="Release notes/changelog")
    release_date = models.DateTimeField(null=True, blank=True)
    download_url = models.URLField(blank=True, help_text="Download URL for the release")
    
    # Update tracking
    last_check = models.DateTimeField(auto_now=True)
    download_progress = models.IntegerField(default=0, help_text="Download progress percentage")
    error_message = models.TextField(blank=True, help_text="Error message if update failed")
    
    # Settings
    auto_check_enabled = models.BooleanField(default=True, help_text="Automatically check for updates")
    github_repo = models.CharField(max_length=100, default="ohbotno/aperture-booking", 
                                 help_text="GitHub repository (username/repo-name)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_updateinfo'
        verbose_name = "Update Information"
        verbose_name_plural = "Update Information"
    
    def __str__(self):
        return f"Version {self.current_version} -> {self.latest_version or 'Unknown'}"
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton update info instance."""
        from aperture_booking import __version__
        instance, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'current_version': __version__,  # Use version from __init__.py
                'github_repo': 'your-username/aperture-booking'
            }
        )
        return instance
    
    def is_update_available(self):
        """Check if an update is available."""
        if not self.latest_version or not self.current_version:
            return False
        return self.latest_version != self.current_version
    
    def can_install_update(self):
        """Check if update can be installed."""
        return self.status == 'ready' and self.is_update_available()


class UpdateHistory(models.Model):
    """Track update installation history."""
    
    RESULT_CHOICES = [
        ('success', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    from_version = models.CharField(max_length=50)
    to_version = models.CharField(max_length=50)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Backup information
    backup_created = models.BooleanField(default=False)
    backup_path = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_updatehistory'
        verbose_name = "Update History"
        verbose_name_plural = "Update History"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Update {self.from_version} -> {self.to_version} ({self.result})"
    
    @property
    def duration(self):
        """Calculate update duration."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


# License Management Models for White Label Support
class LicenseConfiguration(models.Model):
    """
    License configuration for white-label deployments.
    Supports both open source (honor system) and commercial licensing.
    """
    LICENSE_TYPES = [
        ('open_source', 'Open Source (GPL-3.0)'),
        ('basic_commercial', 'Basic Commercial White Label'),
        ('premium_commercial', 'Premium Commercial White Label'),
        ('enterprise', 'Enterprise License'),
    ]
    
    # License identification
    license_key = models.CharField(
        max_length=255, 
        unique=True,
        help_text="Unique license key for this installation"
    )
    license_type = models.CharField(
        max_length=50, 
        choices=LICENSE_TYPES,
        default='open_source'
    )
    
    # Organization details
    organization_name = models.CharField(
        max_length=200,
        help_text="Name of the licensed organization"
    )
    organization_slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-safe identifier for custom theming"
    )
    contact_email = models.EmailField(
        help_text="Primary contact for license holder"
    )
    
    # License restrictions
    allowed_domains = models.JSONField(
        default=list,
        help_text="List of domains where this license is valid"
    )
    max_users = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of active users (null = unlimited)"
    )
    max_resources = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of resources (null = unlimited)"
    )
    
    # Feature enablement
    features_enabled = models.JSONField(
        default=dict,
        help_text="JSON object defining which features are enabled"
    )
    
    # License validity
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="License expiration date (null = no expiration)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this license is currently active"
    )
    
    # Validation tracking
    last_validation = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time license was validated"
    )
    validation_failures = models.PositiveIntegerField(
        default=0,
        help_text="Count of recent validation failures"
    )
    
    # Support and updates
    support_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Support and updates expiration date"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_licenseconfiguration'
        verbose_name = "License Configuration"
        verbose_name_plural = "License Configurations"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.organization_name} ({self.get_license_type_display()})"
    
    def is_valid(self):
        """Check if license is currently valid."""
        if not self.is_active:
            return False
        
        if self.expires_at and self.expires_at < timezone.now():
            return False
            
        return True
    
    def get_enabled_features(self):
        """Get list of enabled features based on license type."""
        base_features = {
            'basic_booking': True,
            'user_management': True,
            'resource_management': True,
            'email_notifications': True,
        }
        
        if self.license_type == 'open_source':
            base_features.update({
                'custom_branding': False,
                'white_label': False,
                'advanced_reports': False,
                'api_access': True,
                'premium_support': False,
            })
        elif self.license_type == 'basic_commercial':
            base_features.update({
                'custom_branding': True,
                'white_label': True,
                'advanced_reports': False,
                'api_access': True,
                'premium_support': True,
            })
        elif self.license_type == 'premium_commercial':
            base_features.update({
                'custom_branding': True,
                'white_label': True,
                'advanced_reports': True,
                'api_access': True,
                'premium_support': True,
                'custom_integrations': True,
            })
        elif self.license_type == 'enterprise':
            base_features.update({
                'custom_branding': True,
                'white_label': True,
                'advanced_reports': True,
                'api_access': True,
                'premium_support': True,
                'custom_integrations': True,
                'multi_tenant': True,
                'priority_support': True,
            })
        
        # Merge with custom features from JSON field
        base_features.update(self.features_enabled)
        return base_features
    
    def check_usage_limits(self):
        """Check if current usage exceeds license limits."""
        issues = []
        
        if self.max_users:
            active_users = User.objects.filter(is_active=True).count()
            if active_users > self.max_users:
                issues.append(f"User limit exceeded: {active_users}/{self.max_users}")
        
        if self.max_resources:
            active_resources = Resource.objects.filter(is_active=True).count()
            if active_resources > self.max_resources:
                issues.append(f"Resource limit exceeded: {active_resources}/{self.max_resources}")
        
        return issues


class BrandingConfiguration(models.Model):
    """
    Customization and branding settings for white-label deployments.
    """
    # Link to license
    license = models.OneToOneField(
        LicenseConfiguration,
        on_delete=models.CASCADE,
        related_name='branding'
    )
    
    # Basic branding
    app_title = models.CharField(
        max_length=100,
        default='Aperture Booking',
        help_text="Application name shown in browser title and headers"
    )
    company_name = models.CharField(
        max_length=200,
        help_text="Company/organization name"
    )
    
    # Visual branding
    logo_primary = models.ImageField(
        upload_to='branding/logos/',
        null=True,
        blank=True,
        help_text="Primary logo (displayed in header)"
    )
    logo_favicon = models.ImageField(
        upload_to='branding/favicons/',
        null=True,
        blank=True,
        help_text="Favicon (16x16 or 32x32 pixels)"
    )
    
    # Color scheme
    color_primary = models.CharField(
        max_length=7,
        default='#007bff',
        help_text="Primary brand color (hex format)"
    )
    color_secondary = models.CharField(
        max_length=7,
        default='#6c757d',
        help_text="Secondary brand color (hex format)"
    )
    color_accent = models.CharField(
        max_length=7,
        default='#28a745',
        help_text="Accent color for highlights and buttons"
    )
    
    # Content customization
    welcome_message = models.TextField(
        blank=True,
        help_text="Custom welcome message for the homepage"
    )
    footer_text = models.TextField(
        blank=True,
        help_text="Custom footer text"
    )
    custom_css = models.TextField(
        blank=True,
        help_text="Additional CSS for custom styling"
    )
    
    # Contact information
    support_email = models.EmailField(
        blank=True,
        help_text="Support contact email"
    )
    support_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Support contact phone"
    )
    website_url = models.URLField(
        blank=True,
        help_text="Organization website URL"
    )
    
    # Email customization
    email_from_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name shown in 'From' field of emails"
    )
    email_signature = models.TextField(
        blank=True,
        help_text="Signature added to notification emails"
    )
    
    # Feature toggles
    show_powered_by = models.BooleanField(
        default=True,
        help_text="Show 'Powered by Aperture Booking' in footer"
    )
    enable_public_registration = models.BooleanField(
        default=True,
        help_text="Allow public user registration"
    )
    enable_guest_booking = models.BooleanField(
        default=False,
        help_text="Allow guest bookings without registration"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_brandingconfiguration'
        verbose_name = "Branding Configuration"
        verbose_name_plural = "Branding Configurations"
    
    def __str__(self):
        return f"Branding for {self.company_name}"
    
    def get_css_variables(self):
        """Generate CSS custom properties for theming."""
        return {
            '--primary-color': self.color_primary,
            '--secondary-color': self.color_secondary,
            '--accent-color': self.color_accent,
        }


class LicenseValidationLog(models.Model):
    """
    Log of license validation attempts for monitoring and troubleshooting.
    """
    VALIDATION_TYPES = [
        ('startup', 'Application Startup'),
        ('periodic', 'Periodic Check'),
        ('feature_access', 'Feature Access'),
        ('admin_manual', 'Manual Admin Check'),
    ]
    
    RESULT_TYPES = [
        ('success', 'Validation Successful'),
        ('expired', 'License Expired'),
        ('invalid_key', 'Invalid License Key'),
        ('domain_mismatch', 'Domain Not Allowed'),
        ('usage_exceeded', 'Usage Limits Exceeded'),
        ('network_error', 'Network/Server Error'),
        ('not_found', 'License Not Found'),
    ]
    
    license = models.ForeignKey(
        LicenseConfiguration,
        on_delete=models.CASCADE,
        related_name='validation_logs'
    )
    
    validation_type = models.CharField(
        max_length=20,
        choices=VALIDATION_TYPES
    )
    result = models.CharField(
        max_length=20,
        choices=RESULT_TYPES
    )
    
    # Validation details
    domain_checked = models.CharField(
        max_length=255,
        blank=True,
        help_text="Domain that was validated"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Browser/client user agent"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of validation request"
    )
    
    # Error details
    error_message = models.TextField(
        blank=True,
        help_text="Error message if validation failed"
    )
    
    # Performance tracking
    response_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Validation response time in seconds"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_licensevalidationlog'
        verbose_name = "License Validation Log"
        verbose_name_plural = "License Validation Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['license', '-created_at']),
            models.Index(fields=['result', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.license.organization_name} - {self.get_result_display()} ({self.created_at})"


class ResourceIssue(models.Model):
    """Model for tracking issues reported by users for resources."""
    
    SEVERITY_CHOICES = [
        ('low', 'Low - Minor issue, resource still usable'),
        ('medium', 'Medium - Issue affects functionality'),
        ('high', 'High - Resource partially unusable'),
        ('critical', 'Critical - Resource completely unusable'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_parts', 'Waiting for Parts'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('duplicate', 'Duplicate'),
    ]
    
    CATEGORY_CHOICES = [
        ('mechanical', 'Mechanical Issue'),
        ('electrical', 'Electrical Issue'),
        ('software', 'Software Issue'),
        ('safety', 'Safety Concern'),
        ('calibration', 'Calibration Required'),
        ('maintenance', 'Maintenance Required'),
        ('damage', 'Physical Damage'),
        ('other', 'Other'),
    ]
    
    resource = models.ForeignKey(
        Resource, 
        on_delete=models.CASCADE, 
        related_name='issues'
    )
    reported_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reported_issues'
    )
    title = models.CharField(
        max_length=200, 
        help_text="Brief description of the issue"
    )
    description = models.TextField(
        help_text="Detailed description of the issue, including steps to reproduce if applicable"
    )
    severity = models.CharField(
        max_length=20, 
        choices=SEVERITY_CHOICES, 
        default='medium'
    )
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='other'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='open'
    )
    
    # Related booking if issue occurred during a specific booking
    related_booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_issues',
        help_text="Booking during which this issue was discovered"
    )
    
    # Image upload for visual evidence
    image = models.ImageField(
        upload_to='issue_reports/',
        blank=True,
        null=True,
        help_text="Photo of the issue (optional)"
    )
    
    # Location details
    specific_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Specific part or area of the resource affected"
    )
    
    # Admin fields
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_issues',
        limit_choices_to={'userprofile__role__in': ['technician', 'sysadmin']},
        help_text="Technician assigned to resolve this issue"
    )
    
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes for tracking resolution progress"
    )
    
    resolution_description = models.TextField(
        blank=True,
        help_text="Description of how the issue was resolved"
    )
    
    estimated_repair_cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated cost to repair (optional)"
    )
    
    actual_repair_cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual cost of repair (optional)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the issue was marked as resolved"
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the issue was closed"
    )
    
    # Priority and urgency flags
    is_urgent = models.BooleanField(
        default=False,
        help_text="Requires immediate attention"
    )
    
    blocks_resource_use = models.BooleanField(
        default=False,
        help_text="This issue prevents the resource from being used"
    )
    
    class Meta:
        db_table = 'booking_resourceissue'
        verbose_name = "Resource Issue"
        verbose_name_plural = "Resource Issues"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['resource', 'status']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def __str__(self):
        return f"{self.resource.name} - {self.title} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Set timestamps based on status changes
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status == 'closed' and not self.closed_at:
            self.closed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def age_in_days(self):
        """How many days since the issue was reported."""
        return (timezone.now() - self.created_at).days
    
    @property
    def is_overdue(self):
        """Check if issue is overdue based on severity."""
        age = self.age_in_days
        if self.severity == 'critical':
            return age > 1  # Critical issues should be resolved within 1 day
        elif self.severity == 'high':
            return age > 3  # High severity within 3 days
        elif self.severity == 'medium':
            return age > 7  # Medium severity within 1 week
        else:
            return age > 14  # Low severity within 2 weeks
    
    @property
    def time_to_resolution(self):
        """Time taken to resolve the issue."""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None
    
    def can_be_edited_by(self, user):
        """Check if user can edit this issue."""
        # Reporters can edit their own issues if they're still open
        if self.reported_by == user and self.status == 'open':
            return True
        
        # Technicians and sysadmins can always edit
        try:
            return user.userprofile.role in ['technician', 'sysadmin']
        except:
            return False
    
    def get_status_color(self):
        """Get Bootstrap color class for status."""
        status_colors = {
            'open': 'danger',
            'in_progress': 'warning',
            'waiting_parts': 'info',
            'resolved': 'success',
            'closed': 'secondary',
            'duplicate': 'secondary',
        }
        return status_colors.get(self.status, 'secondary')
    
    def get_severity_color(self):
        """Get Bootstrap color class for severity."""
        severity_colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'danger',
        }
        return severity_colors.get(self.severity, 'secondary')