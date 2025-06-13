# booking/models.py
"""
Core models for the Lab Booking System.

This file is part of the Lab Booking System.
Copyright (C) 2025 Lab Booking System Contributors

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


class NotificationPreference(models.Model):
    """User notification preferences."""
    NOTIFICATION_TYPES = [
        ('booking_confirmed', 'Booking Confirmed'),
        ('booking_cancelled', 'Booking Cancelled'), 
        ('booking_reminder', 'Booking Reminder'),
        ('approval_request', 'Approval Request'),
        ('approval_decision', 'Approval Decision'),
        ('maintenance_alert', 'Maintenance Alert'),
        ('conflict_detected', 'Conflict Detected'),
        ('quota_warning', 'Quota Warning'),
        ('waitlist_joined', 'Joined Waiting List'),
        ('waitlist_availability', 'Waiting List Slot Available'),
        ('waitlist_cancelled', 'Left Waiting List'),
    ]
    
    DELIVERY_METHODS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'In-App'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_METHODS)
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
    delivery_method = models.CharField(max_length=10, choices=NotificationPreference.DELIVERY_METHODS)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Related objects
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, null=True, blank=True)
    resource = models.ForeignKey('Resource', on_delete=models.CASCADE, null=True, blank=True)
    maintenance = models.ForeignKey('Maintenance', on_delete=models.CASCADE, null=True, blank=True)
    
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
    
    def mark_as_failed(self):
        """Mark notification as failed and handle retry logic."""
        self.status = 'failed'
        self.retry_count += 1
        if self.retry_count < self.max_retries:
            # Exponential backoff: 5min, 15min, 45min
            delay_minutes = 5 * (3 ** (self.retry_count - 1))
            self.next_retry_at = timezone.now() + timedelta(minutes=delay_minutes)
            self.status = 'pending'  # Reset to pending for retry
        self.save(update_fields=['status', 'retry_count', 'next_retry_at', 'updated_at'])
    
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


class ApprovalRule(models.Model):
    """Rules for booking approval workflows."""
    APPROVAL_TYPES = [
        ('auto', 'Automatic Approval'),
        ('single', 'Single Level Approval'),
        ('tiered', 'Tiered Approval'),
        ('quota', 'Quota Based'),
    ]
    
    name = models.CharField(max_length=200)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='approval_rules')
    approval_type = models.CharField(max_length=20, choices=APPROVAL_TYPES)
    user_roles = models.JSONField(default=list)  # Roles that this rule applies to
    approvers = models.ManyToManyField(User, related_name='approval_rules', blank=True)
    conditions = models.JSONField(default=dict)  # Additional conditions
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=1)
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


class WaitingListEntry(models.Model):
    """Users waiting for resource availability."""
    PRIORITY_LEVELS = [
        ('normal', 'Normal'),
        ('high', 'High Priority'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('notified', 'Notified'),
        ('expired', 'Expired'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
    ]
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='waiting_list')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='waiting_list_entries')
    
    # Time preferences - user can specify flexible time windows
    preferred_start_time = models.DateTimeField()
    preferred_end_time = models.DateTimeField()
    min_duration_minutes = models.PositiveIntegerField(default=60)
    max_duration_minutes = models.PositiveIntegerField(default=240)
    
    # Flexibility options
    flexible_start_time = models.BooleanField(default=True, help_text="Can start earlier/later than preferred time")
    flexible_duration = models.BooleanField(default=True, help_text="Can accept shorter/longer slots")
    max_days_advance = models.PositiveIntegerField(default=14, help_text="Maximum days in advance to consider")
    
    # Notification preferences
    notify_immediately = models.BooleanField(default=True)
    notification_advance_hours = models.PositiveIntegerField(default=24, help_text="Hours notice before slot")
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    
    # Auto-booking option
    auto_book = models.BooleanField(default=False, help_text="Automatically book when slot becomes available")
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'booking_waitinglistentry'
        ordering = ['priority', 'created_at']  # High priority first, then FIFO
        indexes = [
            models.Index(fields=['resource', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['preferred_start_time']),
            models.Index(fields=['created_at']),
        ]
        unique_together = ['resource', 'user', 'preferred_start_time']  # Prevent duplicate entries
    
    def __str__(self):
        return f"{self.user.username} waiting for {self.resource.name} at {self.preferred_start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def clean(self):
        """Validate waiting list entry."""
        if self.preferred_start_time >= self.preferred_end_time:
            raise ValidationError("End time must be after start time.")
        
        if self.min_duration_minutes > self.max_duration_minutes:
            raise ValidationError("Minimum duration cannot exceed maximum duration.")
        
        # Check if preferred time is in the past
        if self.preferred_start_time < timezone.now():
            raise ValidationError("Cannot create waiting list entry for past time.")
        
        # Check if user has permission to book this resource
        try:
            user_profile = self.user.userprofile
            if not self.resource.is_available_for_user(user_profile):
                raise ValidationError("User does not meet resource requirements.")
        except:
            pass
    
    def save(self, *args, **kwargs):
        # Set expiration time if not set
        if not self.expires_at:
            self.expires_at = self.preferred_end_time + timedelta(days=self.max_days_advance)
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if waiting list entry has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def preferred_duration(self):
        """Return preferred duration as timedelta."""
        return self.preferred_end_time - self.preferred_start_time
    
    @property
    def min_duration(self):
        """Return minimum duration as timedelta."""
        return timedelta(minutes=self.min_duration_minutes)
    
    @property
    def max_duration(self):
        """Return maximum duration as timedelta."""
        return timedelta(minutes=self.max_duration_minutes)
    
    def check_availability_match(self, available_start, available_end):
        """Check if an available slot matches this waiting list entry's criteria."""
        if self.status != 'active':
            return False
        
        if self.is_expired:
            return False
        
        available_duration = available_end - available_start
        
        # Check duration requirements
        if available_duration < self.min_duration:
            return False
        
        if not self.flexible_duration and available_duration > self.max_duration:
            return False
        
        # Check time preferences
        if not self.flexible_start_time:
            # Strict time matching
            time_buffer = timedelta(minutes=15)  # Allow 15 minutes flexibility
            if abs(available_start - self.preferred_start_time) > time_buffer:
                return False
        else:
            # Flexible time matching - check if it's within the acceptable window
            latest_acceptable_start = self.preferred_start_time + timedelta(hours=2)
            earliest_acceptable_start = self.preferred_start_time - timedelta(hours=2)
            
            if available_start < earliest_acceptable_start or available_start > latest_acceptable_start:
                return False
        
        return True
    
    def mark_as_notified(self):
        """Mark entry as notified."""
        self.status = 'notified'
        self.notified_at = timezone.now()
        self.save(update_fields=['status', 'notified_at', 'updated_at'])
    
    def mark_as_fulfilled(self):
        """Mark entry as fulfilled."""
        self.status = 'fulfilled'
        self.fulfilled_at = timezone.now()
        self.save(update_fields=['status', 'fulfilled_at', 'updated_at'])
    
    def cancel(self):
        """Cancel waiting list entry."""
        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])


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