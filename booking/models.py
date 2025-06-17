# booking/models.py
"""
Core models for the Aperture Booking.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_resource'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_resource_type_display()})"

    def is_available_for_user(self, user_profile):
        """Check if resource is available for a specific user."""
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


class Maintenance(models.Model):
    """Maintenance schedules for resources."""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='maintenances')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    maintenance_type = models.CharField(max_length=100)
    is_recurring = models.BooleanField(default=False)
    recurring_pattern = models.JSONField(null=True, blank=True)
    blocks_booking = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_maintenance'
        ordering = ['start_time']

    def __str__(self):
        return f"{self.title} - {self.resource.name} ({self.start_time.strftime('%Y-%m-%d')})"

    def clean(self):
        """Validate maintenance schedule."""
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")

    def overlaps_with_booking(self, booking):
        """Check if maintenance overlaps with a booking."""
        return (self.start_time < booking.end_time and 
                self.end_time > booking.start_time)


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