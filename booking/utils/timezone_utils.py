# booking/utils/timezone_utils.py
"""
Timezone utilities for the Aperture Booking system.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from django.utils import timezone
from datetime import datetime
import warnings


def make_aware_datetime(dt):
    """Convert a naive datetime to timezone-aware datetime."""
    if dt is None:
        return None
    
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def safe_now():
    """Get current timezone-aware datetime."""
    return timezone.now()


def safe_datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0):
    """Create a timezone-aware datetime."""
    dt = datetime(year, month, day, hour, minute, second, microsecond)
    return make_aware_datetime(dt)


def fix_naive_datetime_warnings():
    """
    Suppress naive datetime warnings in development.
    Note: This should not be used in production - fix the actual naive datetime usage instead.
    """
    warnings.filterwarnings('ignore', message='.*received a naive datetime.*')


# Auto-fix for development (can be removed in production)
# Uncomment the line below to suppress warnings temporarily
# fix_naive_datetime_warnings()