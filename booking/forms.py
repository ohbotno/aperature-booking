from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import UserProfile, EmailVerificationToken, PasswordResetToken


class UserRegistrationForm(UserCreationForm):
    """Extended user registration form with profile fields."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, initial='student')
    group = forms.CharField(max_length=100, required=False, help_text="Research group or class")
    college = forms.CharField(max_length=100, required=False)
    student_id = forms.CharField(max_length=50, required=False, help_text="Student ID (if applicable)")
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['role'].widget.attrs.update({'class': 'form-control'})
        self.fields['group'].widget.attrs.update({'class': 'form-control'})
        self.fields['college'].widget.attrs.update({'class': 'form-control'})
        self.fields['student_id'].widget.attrs.update({'class': 'form-control'})
        self.fields['phone'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = False  # Deactivate until email verification
        
        if commit:
            user.save()
            profile = UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                group=self.cleaned_data.get('group', ''),
                college=self.cleaned_data.get('college', ''),
                student_id=self.cleaned_data.get('student_id', ''),
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
        fields = ['role', 'group', 'college', 'student_id', 'phone']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'group': forms.TextInput(attrs={'class': 'form-control'}),
            'college': forms.TextInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.user.first_name = self.cleaned_data['first_name']
            profile.user.last_name = self.cleaned_data['last_name']
            profile.user.email = self.cleaned_data['email']
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