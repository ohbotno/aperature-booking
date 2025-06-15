# booking/templatetags/notification_tags.py
"""
Template tags for notification preferences.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, {})
    return {}


@register.filter  
def get_attr(obj, attr):
    """Get an attribute from an object."""
    if hasattr(obj, attr):
        return getattr(obj, attr)
    return None