# booking/templatetags/booking_extras.py
"""
Template tags and filters for booking-related functionality.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperture-booking.org/commercial
"""

from django import template
from datetime import timedelta

register = template.Library()


@register.filter
def duration_to(start_time, end_time):
    """
    Calculate and format the duration between two datetime objects.
    Usage: {{ start_time|duration_to:end_time }}
    """
    if not start_time or not end_time:
        return "Unknown"
    
    try:
        duration = end_time - start_time
        
        # Extract days, hours, and minutes
        days = duration.days
        seconds = duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        # Format the duration string
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 and days == 0:  # Only show minutes if less than a day
            parts.append(f"{minutes}m")
        
        if not parts:
            return "< 1m"
        
        return " ".join(parts)
    
    except (TypeError, AttributeError):
        return "Invalid"


@register.filter
def sub(value, arg):
    """
    Subtract arg from value. Useful for datetime calculations.
    Usage: {{ end_time|sub:start_time }}
    """
    try:
        return value - arg
    except (TypeError, ValueError):
        return ""


@register.filter
def div(value, arg):
    """
    Divide value by arg.
    Usage: {{ seconds|div:3600 }}
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0