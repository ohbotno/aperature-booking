"""Test cases for booking API endpoints."""
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from booking.models import Booking, Resource, UserProfile
from booking.tests.factories import (
    UserFactory, UserProfileFactory, ResourceFactory, BookingFactory
)


@pytest.mark.django_db
class TestBookingAPI:
    """Test booking API endpoints."""
    
    def setup_method(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user_profile = UserProfileFactory()
        self.user = self.user_profile.user
        self.client.force_authenticate(user=self.user)
    
    def test_list_bookings(self):
        """Test listing bookings."""
        # Create some bookings for the user
        BookingFactory.create_batch(3, user=self.user_profile)
        BookingFactory.create_batch(2)  # Other users' bookings
        
        url = reverse('booking-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Should only see own bookings (unless manager)
        assert len(response.data['results']) >= 3
    
    def test_create_booking(self):
        """Test creating a new booking."""
        resource = ResourceFactory()
        start_time = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        data = {
            'resource': resource.id,
            'title': 'Test Booking',
            'description': 'Test description',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
        }
        
        url = reverse('booking-list')
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Booking.objects.filter(title='Test Booking').exists()
    
    def test_create_booking_with_conflicts(self):
        """Test creating a booking that conflicts with existing booking."""
        resource = ResourceFactory()
        start_time = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=2)
        
        # Create existing booking
        BookingFactory(
            resource=resource,
            start_time=start_time,
            end_time=end_time,
            status=Booking.CONFIRMED
        )
        
        # Try to create conflicting booking
        data = {
            'resource': resource.id,
            'title': 'Conflicting Booking',
            'description': 'Should conflict',
            'start_time': (start_time + timedelta(minutes=30)).isoformat(),
            'end_time': (end_time + timedelta(minutes=30)).isoformat(),
        }
        
        url = reverse('booking-list')
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'conflict' in str(response.data).lower()
    
    def test_update_booking(self):
        """Test updating an existing booking."""
        booking = BookingFactory(user=self.user_profile, status=Booking.PENDING)
        
        data = {
            'title': 'Updated Title',
            'description': 'Updated description',
        }
        
        url = reverse('booking-detail', kwargs={'pk': booking.pk})
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.title == 'Updated Title'
    
    def test_update_booking_time(self):
        """Test updating booking time without conflicts."""
        booking = BookingFactory(user=self.user_profile, status=Booking.PENDING)
        new_start = timezone.now().replace(hour=14, minute=0, second=0, microsecond=0)
        new_end = new_start + timedelta(hours=2)
        
        data = {
            'start_time': new_start.isoformat(),
            'end_time': new_end.isoformat(),
        }
        
        url = reverse('booking-detail', kwargs={'pk': booking.pk})
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.start_time.hour == 14
    
    def test_delete_booking(self):
        """Test deleting a booking."""
        booking = BookingFactory(user=self.user_profile, status=Booking.PENDING)
        
        url = reverse('booking-detail', kwargs={'pk': booking.pk})
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        booking.refresh_from_db()
        assert booking.status == Booking.CANCELLED
    
    def test_cannot_update_others_booking(self):
        """Test that users cannot update others' bookings."""
        other_user = UserProfileFactory()
        booking = BookingFactory(user=other_user)
        
        data = {'title': 'Hacked Title'}
        
        url = reverse('booking-detail', kwargs={'pk': booking.pk})
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_manager_can_update_any_booking(self):
        """Test that managers can update any booking."""
        # Make user a lab manager
        self.user_profile.role = UserProfile.LAB_MANAGER
        self.user_profile.save()
        
        other_user = UserProfileFactory()
        booking = BookingFactory(user=other_user)
        
        data = {'title': 'Manager Updated'}
        
        url = reverse('booking-detail', kwargs={'pk': booking.pk})
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.title == 'Manager Updated'


@pytest.mark.django_db
class TestResourceAPI:
    """Test resource API endpoints."""
    
    def setup_method(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user_profile = UserProfileFactory()
        self.user = self.user_profile.user
        self.client.force_authenticate(user=self.user)
    
    def test_list_resources(self):
        """Test listing resources."""
        ResourceFactory.create_batch(5)
        
        url = reverse('resource-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5
    
    def test_filter_resources_by_category(self):
        """Test filtering resources by category."""
        ResourceFactory.create_batch(3, category=Resource.ROBOT)
        ResourceFactory.create_batch(2, category=Resource.INSTRUMENT)
        
        url = reverse('resource-list')
        response = self.client.get(url, {'category': Resource.ROBOT})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_resource_availability(self):
        """Test checking resource availability."""
        resource = ResourceFactory()
        
        # Create booking that occupies the resource
        start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=2)
        BookingFactory(
            resource=resource,
            start_time=start,
            end_time=end,
            status=Booking.CONFIRMED
        )
        
        url = reverse('resource-availability', kwargs={'pk': resource.pk})
        response = self.client.get(url, {
            'start': start.isoformat(),
            'end': end.isoformat()
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['available'] is False
    
    def test_create_resource_as_manager(self):
        """Test that managers can create resources."""
        self.user_profile.role = UserProfile.LAB_MANAGER
        self.user_profile.save()
        
        data = {
            'name': 'New Robot',
            'category': Resource.ROBOT,
            'description': 'Test robot',
            'location': 'Lab A',
            'capacity': 1,
            'required_training_level': UserProfile.BASIC,
            'requires_induction': True,
        }
        
        url = reverse('resource-list')
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Resource.objects.filter(name='New Robot').exists()
    
    def test_cannot_create_resource_as_student(self):
        """Test that students cannot create resources."""
        data = {
            'name': 'Unauthorized Robot',
            'category': Resource.ROBOT,
            'description': 'Should not be created',
        }
        
        url = reverse('resource-list')
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCalendarAPI:
    """Test calendar-specific API endpoints."""
    
    def setup_method(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user_profile = UserProfileFactory()
        self.user = self.user_profile.user
        self.client.force_authenticate(user=self.user)
    
    def test_calendar_events(self):
        """Test getting calendar events in FullCalendar format."""
        # Create bookings for the user
        start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=2)
        
        booking = BookingFactory(
            user=self.user_profile,
            start_time=start,
            end_time=end,
            title='Test Event'
        )
        
        url = reverse('calendar-events')
        response = self.client.get(url, {
            'start': (start - timedelta(days=1)).isoformat(),
            'end': (end + timedelta(days=1)).isoformat()
        })
        
        assert response.status_code == status.HTTP_200_OK
        events = response.data
        assert len(events) >= 1
        
        # Check FullCalendar format
        event = next(e for e in events if e['title'] == 'Test Event')
        assert 'id' in event
        assert 'title' in event
        assert 'start' in event
        assert 'end' in event
    
    def test_bulk_booking_operations(self):
        """Test bulk approve/reject operations."""
        self.user_profile.role = UserProfile.LAB_MANAGER
        self.user_profile.save()
        
        # Create pending bookings
        bookings = BookingFactory.create_batch(
            3, status=Booking.PENDING
        )
        booking_ids = [b.id for b in bookings]
        
        url = reverse('booking-bulk-approve')
        response = self.client.post(url, {
            'booking_ids': booking_ids
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check that bookings were approved
        for booking in bookings:
            booking.refresh_from_db()
            assert booking.status == Booking.CONFIRMED
    
    def test_booking_statistics(self):
        """Test getting booking statistics."""
        self.user_profile.role = UserProfile.LAB_MANAGER
        self.user_profile.save()
        
        # Create various bookings
        BookingFactory.create_batch(5, status=Booking.CONFIRMED)
        BookingFactory.create_batch(3, status=Booking.PENDING)
        BookingFactory.create_batch(2, status=Booking.CANCELLED)
        
        url = reverse('booking-statistics')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        stats = response.data
        
        assert 'total_bookings' in stats
        assert 'confirmed_bookings' in stats
        assert 'pending_bookings' in stats
        assert 'cancelled_bookings' in stats
        
        assert stats['confirmed_bookings'] >= 5
        assert stats['pending_bookings'] >= 3
        assert stats['cancelled_bookings'] >= 2


@pytest.mark.django_db
class TestAuthenticationAPI:
    """Test authentication-related API endpoints."""
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated requests are rejected."""
        client = APIClient()  # No authentication
        
        url = reverse('booking-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_authentication(self):
        """Test token-based authentication."""
        from rest_framework.authtoken.models import Token
        
        user = UserFactory()
        token = Token.objects.create(user=user)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        url = reverse('booking-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_user_profile_endpoint(self):
        """Test getting user profile information."""
        client = APIClient()
        user_profile = UserProfileFactory()
        client.force_authenticate(user=user_profile.user)
        
        url = reverse('user-profile')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['role'] == user_profile.role
        assert response.data['training_level'] == user_profile.training_level