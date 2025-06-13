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
        profile = UserProfileFactory(user__username="testuser")
        assert str(profile) == "testuser"
    
    def test_role_permissions(self):
        """Test role-based permission methods."""
        student = UserProfileFactory(role=UserProfile.STUDENT)
        lecturer = UserProfileFactory(role=UserProfile.LECTURER)
        manager = UserProfileFactory(role=UserProfile.LAB_MANAGER)
        
        # Test basic permissions
        assert not student.can_approve_bookings()
        assert lecturer.can_approve_bookings()
        assert manager.can_approve_bookings()
        
        # Test admin permissions
        assert not student.can_manage_resources()
        assert not lecturer.can_manage_resources()
        assert manager.can_manage_resources()


@pytest.mark.django_db
class TestResource:
    """Test Resource model functionality."""
    
    def test_resource_creation(self):
        """Test creating a resource."""
        resource = ResourceFactory()
        assert resource.name
        assert resource.category == Resource.INSTRUMENT
        assert resource.capacity == 1
    
    def test_resource_str(self):
        """Test Resource string representation."""
        resource = ResourceFactory(name="Test Robot")
        assert str(resource) == "Test Robot"
    
    def test_user_can_access_resource(self):
        """Test user access to resources based on training."""
        basic_resource = ResourceFactory(required_training_level=UserProfile.BASIC)
        advanced_resource = ResourceFactory(required_training_level=UserProfile.ADVANCED)
        
        basic_user = UserProfileFactory(training_level=UserProfile.BASIC)
        advanced_user = UserProfileFactory(training_level=UserProfile.ADVANCED)
        
        # Basic user can access basic resource
        assert basic_resource.user_can_access(basic_user)
        # Basic user cannot access advanced resource
        assert not advanced_resource.user_can_access(basic_user)
        # Advanced user can access both
        assert basic_resource.user_can_access(advanced_user)
        assert advanced_resource.user_can_access(advanced_user)
    
    def test_induction_requirements(self):
        """Test induction requirement checking."""
        resource = ResourceFactory(requires_induction=True)
        
        inducted_user = UserProfileFactory(is_inducted=True)
        non_inducted_user = UserProfileFactory(is_inducted=False)
        
        assert resource.user_can_access(inducted_user)
        assert not resource.user_can_access(non_inducted_user)


@pytest.mark.django_db
class TestBooking:
    """Test Booking model functionality."""
    
    def test_booking_creation(self):
        """Test creating a booking."""
        booking = BookingFactory()
        assert booking.title
        assert booking.status == Booking.PENDING
        assert booking.start_time < booking.end_time
    
    def test_booking_str(self):
        """Test Booking string representation."""
        booking = BookingFactory(title="Test Booking")
        expected = f"Test Booking - {booking.resource.name}"
        assert str(booking) == expected
    
    def test_booking_duration(self):
        """Test booking duration calculation."""
        start = timezone.now()
        end = start + timedelta(hours=3)
        booking = BookingFactory(start_time=start, end_time=end)
        assert booking.duration() == timedelta(hours=3)
    
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
        start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=2)
        
        # Create first booking
        booking1 = BookingFactory(
            resource=resource,
            start_time=start,
            end_time=end,
            status=Booking.CONFIRMED
        )
        
        # Create overlapping booking
        overlap_start = start + timedelta(hours=1)
        overlap_end = end + timedelta(hours=1)
        booking2 = BookingFactory.build(
            resource=resource,
            start_time=overlap_start,
            end_time=overlap_end
        )
        
        # Check for conflicts
        conflicts = booking2.has_conflicts()
        assert len(conflicts) > 0
        assert booking1 in conflicts
    
    def test_can_be_cancelled_by_user(self):
        """Test booking cancellation permissions."""
        user = UserProfileFactory()
        booking = BookingFactory(user=user, status=Booking.PENDING)
        
        # User can cancel their own pending booking
        assert booking.can_be_cancelled_by(user)
        
        # User cannot cancel confirmed booking
        booking.status = Booking.CONFIRMED
        assert not booking.can_be_cancelled_by(user)
        
        # Manager can cancel any booking
        manager = UserProfileFactory(role=UserProfile.LAB_MANAGER)
        assert booking.can_be_cancelled_by(manager)


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
        template = BookingTemplateFactory(name="Weekly Meeting")
        assert str(template) == "Weekly Meeting"
    
    def test_template_usage_tracking(self):
        """Test template usage count tracking."""
        template = BookingTemplateFactory()
        initial_count = template.usage_count
        
        # Create booking from template
        BookingFactory(template=template)
        template.refresh_from_db()
        
        assert template.usage_count == initial_count + 1


@pytest.mark.django_db
class TestApprovalRule:
    """Test ApprovalRule model functionality."""
    
    def test_approval_rule_creation(self):
        """Test creating an approval rule."""
        rule = ApprovalRuleFactory()
        assert rule.name
        assert rule.approval_type == ApprovalRule.AUTOMATIC
    
    def test_approval_rule_str(self):
        """Test ApprovalRule string representation."""
        rule = ApprovalRuleFactory(name="Auto Approve Students")
        assert str(rule) == "Auto Approve Students"
    
    def test_applies_to_booking(self):
        """Test if approval rule applies to a booking."""
        resource = ResourceFactory()
        rule = ApprovalRuleFactory(
            resource=resource,
            approval_type=ApprovalRule.AUTOMATIC
        )
        
        booking = BookingFactory(resource=resource)
        assert rule.applies_to(booking)
        
        # Rule for different resource shouldn't apply
        other_resource = ResourceFactory()
        other_booking = BookingFactory(resource=other_resource)
        assert not rule.applies_to(other_booking)
    
    def test_automatic_approval(self):
        """Test automatic approval logic."""
        resource = ResourceFactory()
        rule = ApprovalRuleFactory(
            resource=resource,
            approval_type=ApprovalRule.AUTOMATIC
        )
        
        booking = BookingFactory(resource=resource)
        assert rule.should_auto_approve(booking)
    
    def test_quota_based_approval(self):
        """Test quota-based approval logic."""
        resource = ResourceFactory()
        user = UserProfileFactory()
        
        rule = ApprovalRuleFactory(
            resource=resource,
            approval_type=ApprovalRule.QUOTA_BASED,
            conditions={'max_hours_per_week': 10}
        )
        
        # First booking within quota
        booking1 = BookingFactory(
            resource=resource,
            user=user,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=5)
        )
        assert rule.should_auto_approve(booking1)
        
        # Second booking that would exceed quota
        booking2 = BookingFactory.build(
            resource=resource,
            user=user,
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=6)
        )
        assert not rule.should_auto_approve(booking2)