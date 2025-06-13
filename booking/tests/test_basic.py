"""Basic test to validate Django setup."""
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from booking.models import UserProfile


@pytest.mark.django_db
class TestBasicSetup:
    """Test basic Django setup and model creation."""
    
    def test_user_creation(self):
        """Test creating a basic user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
    
    def test_user_profile_creation(self):
        """Test that user profile is automatically created via signal."""
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # UserProfile should be automatically created via signal
        assert hasattr(user, 'userprofile')
        profile = user.userprofile
        
        # Update the profile
        profile.role = 'student'
        profile.group = 'test_group'
        profile.college = 'test_college'
        profile.training_level = 1
        profile.is_inducted = True
        profile.email_verified = True
        profile.save()
        
        assert profile.role == 'student'
        assert profile.group == 'test_group'
        assert profile.training_level == 1
        assert str(profile) == f"{user.get_full_name()} (student)"