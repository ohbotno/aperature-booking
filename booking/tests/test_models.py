"""Test cases for booking models."""
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from booking.models import UserProfile, Resource, Booking, BookingTemplate, ApprovalRule
from booking.tests.factories import (
    UserFactory, UserProfileFactory, ResourceFactory, 
    BookingFactory, BookingTemplateFactory, ApprovalRuleFactory
)


@pytest.mark.django_db
class TestUserProfile:
    """Test UserProfile model functionality."""
    
    def test_user_profile_creation(self):
        """Test creating a user profile."""
        profile = UserProfileFactory()
        assert profile.user.username
        assert profile.role == 'student'
        assert profile.email_verified is True
    
    def test_user_profile_str(self):
        """Test UserProfile string representation."""
        profile = UserProfileFactory(user__username="testuser", user__first_name="Test", user__last_name="User")
        expected = "Test User (student)"
        assert str(profile) == expected
    
    def test_role_permissions(self):
        """Test role-based permission methods."""
        student = UserProfileFactory(role='student')
        academic = UserProfileFactory(role='academic')
        technician = UserProfileFactory(role='technician')
        
        # Test priority booking permissions
        assert not student.can_book_priority
        assert academic.can_book_priority
        assert technician.can_book_priority
        
        # Test recurring booking permissions
        assert not student.can_create_recurring
        assert academic.can_create_recurring
        assert technician.can_create_recurring


@pytest.mark.django_db
class TestResource:
    """Test Resource model functionality."""
    
    def test_resource_creation(self):
        """Test creating a resource."""
        resource = ResourceFactory()
        assert resource.name
        assert resource.resource_type == 'instrument'
        assert resource.capacity == 1
        assert resource.is_active is True
    
    def test_resource_str(self):
        """Test Resource string representation."""
        resource = ResourceFactory(name="Test Robot", resource_type="robot")
        assert "Test Robot" in str(resource)
        assert "Robot" in str(resource)
    
    def test_user_can_access_resource(self):
        """Test user access to resources based on training."""
        basic_resource = ResourceFactory(required_training_level=1)
        advanced_resource = ResourceFactory(required_training_level=3)
        
        basic_user = UserProfileFactory(training_level=1)
        advanced_user = UserProfileFactory(training_level=3)
        
        # Basic user can access basic resource
        assert basic_resource.is_available_for_user(basic_user)
        # Basic user cannot access advanced resource
        assert not advanced_resource.is_available_for_user(basic_user)
        # Advanced user can access both
        assert basic_resource.is_available_for_user(advanced_user)
        assert advanced_resource.is_available_for_user(advanced_user)
    
    def test_induction_requirements(self):
        """Test induction requirement checking."""
        resource = ResourceFactory(requires_induction=True)
        
        inducted_user = UserProfileFactory(is_inducted=True)
        non_inducted_user = UserProfileFactory(is_inducted=False)
        
        assert resource.is_available_for_user(inducted_user)
        assert not resource.is_available_for_user(non_inducted_user)


@pytest.mark.django_db
class TestBooking:
    """Test Booking model functionality."""
    
    def test_booking_creation(self):
        """Test creating a booking."""
        booking = BookingFactory()
        assert booking.title
        assert booking.status == 'pending'
        assert booking.start_time < booking.end_time
    
    def test_booking_str(self):
        """Test Booking string representation."""
        start_time = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        booking = BookingFactory(title="Test Booking", start_time=start_time)
        expected_date = start_time.strftime('%Y-%m-%d %H:%M')
        expected = f"Test Booking - {booking.resource.name} ({expected_date})"
        assert str(booking) == expected
    
    def test_booking_duration(self):
        """Test booking duration calculation."""
        start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end = start + timedelta(hours=3)
        booking = BookingFactory(start_time=start, end_time=end)
        assert booking.duration == timedelta(hours=3)
    
    def test_booking_validation_time_order(self):
        """Test that booking end time must be after start time."""
        start = timezone.now()
        end = start - timedelta(hours=1)  # End before start
        
        with pytest.raises(ValidationError):
            booking = BookingFactory(start_time=start, end_time=end)
            booking.full_clean()
    
    def test_booking_validation_working_hours(self):
        """Test booking time validation within working hours."""
        # Create booking outside working hours (before 9 AM)
        start = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1)
        
        with pytest.raises(ValidationError):
            booking = BookingFactory(start_time=start, end_time=end)
            booking.full_clean()
    
    def test_booking_validation_max_duration(self):
        """Test booking duration validation against resource limits."""
        resource = ResourceFactory(max_booking_hours=4)
        start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=6)  # Exceeds 4-hour limit
        
        with pytest.raises(ValidationError):
            booking = BookingFactory(
                resource=resource,
                start_time=start,
                end_time=end
            )
            booking.full_clean()
    
    def test_booking_conflict_detection(self):
        """Test booking conflict detection."""
        resource = ResourceFactory()
        start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end = start + timedelta(hours=2)
        
        # Create first booking
        booking1 = BookingFactory(
            resource=resource,
            start_time=start,
            end_time=end,
            status='approved'
        )
        
        # Create overlapping booking (not saved yet)
        overlap_start = start + timedelta(hours=1)
        overlap_end = end + timedelta(hours=1)
        booking2 = BookingFactory.build(
            resource=resource,
            start_time=overlap_start,
            end_time=overlap_end
        )
        
        # Check for conflicts (method returns boolean)
        has_conflicts = booking2.has_conflicts()
        assert has_conflicts is True
    
    def test_can_be_cancelled_by_user(self):
        """Test booking cancellation permissions."""
        user = UserProfileFactory()
        future_time = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        booking = BookingFactory(
            user=user.user, 
            status='pending',
            start_time=future_time,
            end_time=future_time + timedelta(hours=2)
        )
        
        # Pending booking in future can be cancelled
        assert booking.can_be_cancelled
        
        # Approved booking in future can be cancelled
        booking.status = 'approved'
        assert booking.can_be_cancelled
        
        # Cancelled booking cannot be cancelled again
        booking.status = 'cancelled'
        assert not booking.can_be_cancelled
        
        # Past booking cannot be cancelled  
        past_time = timezone.now() - timedelta(hours=1)
        past_booking = BookingFactory.build(
            user=user.user,
            status='pending',
            start_time=past_time,
            end_time=past_time + timedelta(hours=1)
        )
        assert not past_booking.can_be_cancelled


@pytest.mark.django_db
class TestBookingTemplate:
    """Test BookingTemplate model functionality."""
    
    def test_template_creation(self):
        """Test creating a booking template."""
        template = BookingTemplateFactory()
        assert template.name
        assert template.duration_hours == 2
    
    def test_template_str(self):
        """Test BookingTemplate string representation."""
        resource = ResourceFactory(name="Test Lab")
        template = BookingTemplateFactory(name="Weekly Meeting", resource=resource)
        expected = "Weekly Meeting - Test Lab"
        assert str(template) == expected
    
    def test_template_usage_tracking(self):
        """Test template usage count tracking."""
        template = BookingTemplateFactory()
        initial_count = template.use_count
        
        # Use the template's method to create a booking
        start_time = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        template.create_booking_from_template(start_time)
        template.refresh_from_db()
        
        assert template.use_count == initial_count + 1


@pytest.mark.django_db
class TestApprovalRule:
    """Test ApprovalRule model functionality."""
    
    def test_approval_rule_creation(self):
        """Test creating an approval rule."""
        rule = ApprovalRuleFactory()
        assert rule.name
        assert rule.approval_type == 'auto'
        assert rule.is_active is True
    
    def test_approval_rule_str(self):
        """Test ApprovalRule string representation."""
        resource = ResourceFactory(name="Test Robot")
        rule = ApprovalRuleFactory(name="Auto Approve Students", resource=resource)
        expected = "Auto Approve Students - Test Robot"
        assert str(rule) == expected
    
    def test_applies_to_user(self):
        """Test if approval rule applies to a user."""
        resource = ResourceFactory()
        rule = ApprovalRuleFactory(
            resource=resource,
            approval_type='auto',
            user_roles=['student']
        )
        
        student_user = UserProfileFactory(role='student')
        academic_user = UserProfileFactory(role='academic')
        
        assert rule.applies_to_user(student_user)
        assert not rule.applies_to_user(academic_user)
    
    def test_applies_to_all_users(self):
        """Test approval rule that applies to all users."""
        resource = ResourceFactory()
        rule = ApprovalRuleFactory(
            resource=resource,
            approval_type='auto',
            user_roles=[]  # Empty list means all users
        )
        
        student_user = UserProfileFactory(role='student')
        academic_user = UserProfileFactory(role='academic')
        
        assert rule.applies_to_user(student_user)
        assert rule.applies_to_user(academic_user)
    
    def test_inactive_rule(self):
        """Test that inactive rules don't apply."""
        resource = ResourceFactory()
        rule = ApprovalRuleFactory(
            resource=resource,
            approval_type='auto',
            is_active=False
        )
        
        user = UserProfileFactory(role='student')
        assert not rule.applies_to_user(user)