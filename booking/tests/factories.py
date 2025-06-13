"""Test factories for creating test data."""
import factory
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from booking.models import (
    UserProfile, Resource, Booking, BookingTemplate, 
    ApprovalRule, Maintenance, BookingHistory
)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@test.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True


class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile
    
    user = factory.SubFactory(UserFactory)
    role = 'student'
    group = factory.Faker('word')
    college = factory.Faker('company')
    training_level = 1
    is_inducted = True
    email_verified = True


class ResourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Resource
    
    name = factory.Faker('word')
    resource_type = 'instrument'
    description = factory.Faker('text', max_nb_chars=200)
    location = factory.Faker('address')
    capacity = 1
    required_training_level = 1
    requires_induction = False
    max_booking_hours = 8


class BookingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Booking
    
    user = factory.SubFactory(UserFactory)
    resource = factory.SubFactory(ResourceFactory)
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text', max_nb_chars=100)
    start_time = factory.LazyFunction(lambda: timezone.now() + timedelta(days=1))
    end_time = factory.LazyAttribute(lambda obj: obj.start_time + timedelta(hours=2))
    status = 'pending'


class BookingTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BookingTemplate
    
    user = factory.SubFactory(UserFactory)
    name = factory.Faker('sentence', nb_words=3)
    description_template = factory.Faker('text', max_nb_chars=100)
    resource = factory.SubFactory(ResourceFactory)
    duration_hours = 2
    duration_minutes = 0


class ApprovalRuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ApprovalRule
    
    name = factory.Faker('sentence', nb_words=3)
    resource = factory.SubFactory(ResourceFactory)
    approval_type = 'auto'
    conditions = {}
    user_roles = []


class MaintenanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Maintenance
    
    resource = factory.SubFactory(ResourceFactory)
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text', max_nb_chars=100)
    start_time = factory.LazyFunction(lambda: timezone.now() + timedelta(days=2))
    end_time = factory.LazyAttribute(lambda obj: obj.start_time + timedelta(hours=4))


class BookingHistoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BookingHistory
    
    booking = factory.SubFactory(BookingFactory)
    user = factory.SubFactory(UserFactory)
    action = 'created'
    details = {}