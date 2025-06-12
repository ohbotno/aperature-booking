# booking/signals.py
"""
Django signals for the Lab Booking System.

This file is part of the Lab Booking System.
Copyright (C) 2025 Lab Booking System Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Booking, BookingHistory


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()


@receiver(post_save, sender=Booking)
def log_booking_changes(sender, instance, created, **kwargs):
    """Log booking creation and updates."""
    if created:
        BookingHistory.objects.create(
            booking=instance,
            user=instance.user,
            action='created',
            new_values={
                'title': instance.title,
                'start_time': instance.start_time.isoformat(),
                'end_time': instance.end_time.isoformat(),
                'status': instance.status,
            }
        )


@receiver(post_delete, sender=Booking)
def log_booking_deletion(sender, instance, **kwargs):
    """Log booking deletion."""
    BookingHistory.objects.create(
        booking_id=instance.id,
        user=instance.user,
        action='deleted',
        old_values={
            'title': instance.title,
            'start_time': instance.start_time.isoformat(),
            'end_time': instance.end_time.isoformat(),
            'status': instance.status,
        }
    )