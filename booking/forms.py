from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from .models import UserProfile, EmailVerificationToken, PasswordResetToken, Booking, Resource, BookingTemplate, Faculty, College, Department
from .recurring import RecurringBookingPattern


class UserRegistrationForm(UserCreationForm):
    """Extended user registration form with profile fields."""
    # Use email as username
    email = forms.EmailField(
        required=True,
        label="Email Address",
        help_text="This will be your username for logging in"
    )
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    # Exclude sysadmin role from registration - only admins can create sysadmins
    role = forms.ChoiceField(
        choices=[choice for choice in UserProfile.ROLE_CHOICES if choice[0] != 'sysadmin'],
        initial='student'
    )
    
    # Academic structure
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.filter(is_active=True),
        required=False,
        empty_label="Select Faculty"
    )
    college = forms.ModelChoiceField(
        queryset=College.objects.none(),  # Will be populated dynamically
        required=False,
        empty_label="Select College"
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),  # Will be populated dynamically
        required=False,
        empty_label="Select Department"
    )
    
    # Research/academic group
    group = forms.CharField(max_length=100, required=False, help_text="Research group or class")
    
    # Role-specific fields
    student_id = forms.CharField(
        max_length=50, 
        required=False, 
        label="Student ID",
        help_text="Required for students"
    )
    student_level = forms.ChoiceField(
        choices=[('', 'Select Level')] + UserProfile.STUDENT_LEVEL_CHOICES,
        required=False,
        label="Student Level",
        help_text="Required for students"
    )
    staff_number = forms.CharField(
        max_length=50, 
        required=False, 
        label="Staff Number",
        help_text="Required for staff members"
    )
    
    # Contact info
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remove username field since we're using email
        if 'username' in self.fields:
            del self.fields['username']
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Set up dynamic choices for college and department
        if 'faculty' in self.data:
            try:
                faculty_id = int(self.data.get('faculty'))
                self.fields['college'].queryset = College.objects.filter(
                    faculty_id=faculty_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        
        if 'college' in self.data:
            try:
                college_id = int(self.data.get('college'))
                self.fields['department'].queryset = Department.objects.filter(
                    college_id=college_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        student_id = cleaned_data.get('student_id')
        student_level = cleaned_data.get('student_level')
        staff_number = cleaned_data.get('staff_number')
        
        # Role-specific validation
        if role == 'student':
            if not student_id:
                raise forms.ValidationError("Student ID is required for student role.")
            if not student_level:
                raise forms.ValidationError("Student level is required for student role.")
        else:
            # Staff roles need staff number
            if role in ['researcher', 'lecturer', 'lab_manager']:
                if not staff_number:
                    raise forms.ValidationError(f"Staff number is required for {dict(UserProfile.ROLE_CHOICES)[role]} role.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        
        # Use email as username
        user.username = email
        user.email = email
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = False  # Deactivate until email verification
        
        if commit:
            user.save()
            profile = UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                faculty=self.cleaned_data.get('faculty'),
                college=self.cleaned_data.get('college'),
                department=self.cleaned_data.get('department'),
                group=self.cleaned_data.get('group', ''),
                student_id=self.cleaned_data.get('student_id', '') if self.cleaned_data['role'] == 'student' else '',
                student_level=self.cleaned_data.get('student_level', '') if self.cleaned_data['role'] == 'student' else '',
                staff_number=self.cleaned_data.get('staff_number', '') if self.cleaned_data['role'] != 'student' else '',
                phone=self.cleaned_data.get('phone', ''),
                email_verified=False
            )
            
            # Create email verification token
            token = EmailVerificationToken.objects.create(user=user)
            
            # Send verification email
            self.send_verification_email(user, token)
            
        return user
    
    def send_verification_email(self, user, token):
        """Send email verification to the user."""
        subject = 'Verify your Lab Booking System account'
        
        # Render email template
        html_message = render_to_string('registration/verification_email.html', {
            'user': user,
            'token': token.token,
            'domain': getattr(settings, 'SITE_DOMAIN', 'localhost:8000'),
        })
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't prevent registration
            import logging
            logger = logging.getLogger('booking')
            logger.error(f"Failed to send verification email to {user.email}: {e}")


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information."""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = [
            'role', 'faculty', 'college', 'department', 'group', 
            'student_id', 'student_level', 'staff_number', 'phone'
        ]
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'faculty': forms.Select(attrs={'class': 'form-control'}),
            'college': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'group': forms.TextInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'student_level': forms.Select(attrs={'class': 'form-control'}),
            'staff_number': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # Extract current user to check permissions
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        
        # Restrict role choices based on current user permissions
        if self.current_user:
            # Only superusers or sysadmins can assign sysadmin role
            if not (self.current_user.is_superuser or 
                    (hasattr(self.current_user, 'userprofile') and 
                     self.current_user.userprofile.role == 'sysadmin')):
                # Filter out sysadmin role for non-admin users
                role_choices = [choice for choice in UserProfile.ROLE_CHOICES if choice[0] != 'sysadmin']
                self.fields['role'].choices = role_choices
        
        # Set up dynamic choices for college and department based on existing data
        if self.instance.pk:
            if self.instance.faculty:
                self.fields['college'].queryset = College.objects.filter(
                    faculty=self.instance.faculty, is_active=True
                ).order_by('name')
            if self.instance.college:
                self.fields['department'].queryset = Department.objects.filter(
                    college=self.instance.college, is_active=True
                ).order_by('name')
        
        # Set up dynamic choices based on form data (for validation)
        if 'faculty' in self.data:
            try:
                faculty_id = int(self.data.get('faculty'))
                self.fields['college'].queryset = College.objects.filter(
                    faculty_id=faculty_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        
        if 'college' in self.data:
            try:
                college_id = int(self.data.get('college'))
                self.fields['department'].queryset = Department.objects.filter(
                    college_id=college_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        student_id = cleaned_data.get('student_id')
        student_level = cleaned_data.get('student_level')
        staff_number = cleaned_data.get('staff_number')
        
        # Role-specific validation
        if role == 'student':
            if not student_id:
                raise forms.ValidationError("Student ID is required for student role.")
            if not student_level:
                raise forms.ValidationError("Student level is required for student role.")
        else:
            # Staff roles need staff number
            if role in ['researcher', 'lecturer', 'lab_manager', 'sysadmin']:
                if not staff_number:
                    raise forms.ValidationError(f"Staff number is required for {dict(UserProfile.ROLE_CHOICES)[role]} role.")
        
        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Update username to match email if email changed
            old_email = profile.user.email
            new_email = self.cleaned_data['email']
            
            profile.user.first_name = self.cleaned_data['first_name']
            profile.user.last_name = self.cleaned_data['last_name']
            profile.user.email = new_email
            
            # Update username if email changed
            if old_email != new_email:
                profile.user.username = new_email
            
            profile.user.save()
            profile.save()
        return profile


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form using our token system."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError("No active account found with this email address.")
        return email
    
    def save(self, request=None, **kwargs):
        """Generate our custom reset token and send email."""
        email = self.cleaned_data['email']
        user = User.objects.get(email=email, is_active=True)
        
        # Clear any existing unused tokens
        PasswordResetToken.objects.filter(user=user, is_used=False).delete()
        
        # Create new token
        token = PasswordResetToken.objects.create(user=user)
        
        # Send reset email
        self.send_reset_email(user, token, request)
        
        return email
    
    def send_reset_email(self, user, token, request=None):
        """Send password reset email."""
        subject = 'Reset your Lab Booking System password'
        
        # Get domain from request or settings
        if request:
            domain = request.get_host()
        else:
            domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
        
        # Render email template
        html_message = render_to_string('registration/password_reset_email.html', {
            'user': user,
            'token': token.token,
            'domain': domain,
            'protocol': 'https' if getattr(settings, 'USE_HTTPS', False) else 'http',
        })
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            import logging
            logger = logging.getLogger('booking')
            logger.error(f"Failed to send password reset email to {user.email}: {e}")


class CustomSetPasswordForm(SetPasswordForm):
    """Custom set password form with styling."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})


class BookingForm(forms.ModelForm):
    """Form for creating and editing bookings."""
    
    class Meta:
        model = Booking
        fields = ['resource', 'title', 'description', 'start_time', 'end_time', 'shared_with_group', 'notes']
        widgets = {
            'resource': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'shared_with_group': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Filter resources based on user permissions
            try:
                user_profile = self.user.userprofile
                available_resources = []
                for resource in Resource.objects.filter(is_active=True):
                    if resource.is_available_for_user(user_profile):
                        available_resources.append(resource.pk)
                self.fields['resource'].queryset = Resource.objects.filter(pk__in=available_resources)
            except:
                self.fields['resource'].queryset = Resource.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        resource = cleaned_data.get('resource')
        
        if start_time and end_time:
            # Make timezone-aware if needed
            if timezone.is_naive(start_time):
                start_time = timezone.make_aware(start_time)
                cleaned_data['start_time'] = start_time
            
            if timezone.is_naive(end_time):
                end_time = timezone.make_aware(end_time)
                cleaned_data['end_time'] = end_time
            
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")
            
            # Allow booking up to 5 minutes in the past to account for form submission time
            if start_time < timezone.now() - timedelta(minutes=5):
                raise forms.ValidationError("Cannot book in the past.")
            
            # Check booking window (9 AM - 6 PM) - more lenient check
            if (start_time.hour < 9 or start_time.hour >= 18):
                raise forms.ValidationError("Booking start time must be between 09:00 and 18:00.")
                
            if end_time.hour > 18 or (end_time.hour == 18 and end_time.minute > 0):
                raise forms.ValidationError("Booking must end by 18:00.")
            
            # Check max booking hours if set
            if resource and resource.max_booking_hours:
                duration_hours = (end_time - start_time).total_seconds() / 3600
                if duration_hours > resource.max_booking_hours:
                    raise forms.ValidationError(
                        f"Booking exceeds maximum allowed hours ({resource.max_booking_hours}h)."
                    )
        
        return cleaned_data


class RecurringBookingForm(forms.Form):
    """Form for creating recurring bookings."""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    frequency = forms.ChoiceField(
        choices=FREQUENCY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="How often to repeat the booking"
    )
    
    interval = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Repeat every X periods (e.g., every 2 weeks)"
    )
    
    count = forms.IntegerField(
        min_value=1,
        max_value=52,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Number of occurrences (leave blank to use end date)"
    )
    
    until = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text="End date for recurrence (leave blank to use count)"
    )
    
    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Days of the week (for weekly recurrence)"
    )
    
    skip_conflicts = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Skip dates that have conflicts with existing bookings"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        frequency = cleaned_data.get('frequency')
        count = cleaned_data.get('count')
        until = cleaned_data.get('until')
        weekdays = cleaned_data.get('weekdays')
        
        if not count and not until:
            raise forms.ValidationError("Either specify a count or an end date.")
        
        if count and until:
            raise forms.ValidationError("Cannot specify both count and end date.")
        
        if frequency == 'weekly' and not weekdays:
            raise forms.ValidationError("Weekly recurrence requires selecting weekdays.")
        
        if until and until <= timezone.now().date():
            raise forms.ValidationError("End date must be in the future.")
        
        return cleaned_data
    
    def create_pattern(self):
        """Create RecurringBookingPattern from form data."""
        cleaned_data = self.cleaned_data
        
        until_datetime = None
        if cleaned_data.get('until'):
            until_datetime = timezone.make_aware(
                datetime.combine(cleaned_data['until'], datetime.min.time())
            )
        
        weekdays = None
        if cleaned_data.get('weekdays'):
            weekdays = [int(day) for day in cleaned_data['weekdays']]
        
        return RecurringBookingPattern(
            frequency=cleaned_data['frequency'],
            interval=cleaned_data['interval'],
            count=cleaned_data.get('count'),
            until=until_datetime,
            by_weekday=weekdays
        )


class BookingTemplateForm(forms.ModelForm):
    """Form for creating and editing booking templates."""
    
    class Meta:
        model = BookingTemplate
        fields = ['name', 'description', 'resource', 'title_template', 'description_template', 
                 'duration_hours', 'duration_minutes', 'preferred_start_time', 
                 'shared_with_group', 'notes_template', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'resource': forms.Select(attrs={'class': 'form-control'}),
            'title_template': forms.TextInput(attrs={'class': 'form-control'}),
            'description_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 8}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 59, 'step': 15}),
            'preferred_start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'shared_with_group': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Filter resources based on user permissions
            try:
                user_profile = self.user.userprofile
                available_resources = []
                for resource in Resource.objects.filter(is_active=True):
                    if resource.is_available_for_user(user_profile):
                        available_resources.append(resource.pk)
                self.fields['resource'].queryset = Resource.objects.filter(pk__in=available_resources)
            except:
                self.fields['resource'].queryset = Resource.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        duration_hours = cleaned_data.get('duration_hours', 0)
        duration_minutes = cleaned_data.get('duration_minutes', 0)
        
        if duration_hours == 0 and duration_minutes == 0:
            raise forms.ValidationError("Duration must be at least 1 minute.")
        
        # Check max duration
        total_minutes = (duration_hours * 60) + duration_minutes
        if total_minutes > 480:  # 8 hours
            raise forms.ValidationError("Duration cannot exceed 8 hours.")
        
        return cleaned_data


class CreateBookingFromTemplateForm(forms.Form):
    """Form for creating a booking from a template."""
    template = forms.ModelChoiceField(
        queryset=BookingTemplate.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select a template to use for this booking"
    )
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text="Date for the booking"
    )
    
    start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        help_text="Start time (leave blank to use template's preferred time)"
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Show templates accessible to the user
            accessible_templates = []
            for template in BookingTemplate.objects.all():
                if template.is_accessible_by_user(self.user):
                    accessible_templates.append(template.pk)
            
            self.fields['template'].queryset = BookingTemplate.objects.filter(
                pk__in=accessible_templates
            ).order_by('-use_count', 'name')
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        start_time = cleaned_data.get('start_time')
        template = cleaned_data.get('template')
        
        if start_date and start_date <= timezone.now().date():
            raise forms.ValidationError("Booking date must be in the future.")
        
        # Use template's preferred time if none provided
        if not start_time and template and template.preferred_start_time:
            cleaned_data['start_time'] = template.preferred_start_time
        elif not start_time:
            raise forms.ValidationError("Start time is required when template has no preferred time.")
        
        return cleaned_data
    
    def create_booking(self):
        """Create booking from template and form data."""
        template = self.cleaned_data['template']
        start_date = self.cleaned_data['start_date']
        start_time = self.cleaned_data['start_time']
        
        start_datetime = timezone.make_aware(
            datetime.combine(start_date, start_time)
        )
        
        return template.create_booking_from_template(start_datetime, self.user)


class SaveAsTemplateForm(forms.Form):
    """Form for saving a booking as a template."""
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Name for this template"
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Optional description for this template"
    )
    
    is_public = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Make this template available to other users"
    )