# booking/apps.py
"""
App configuration for the booking app.

This file is part of the Lab Booking System.
Copyright (C) 2025 Lab Booking System Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from django.apps import AppConfig


class BookingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booking'
    
    def ready(self):
        import booking.signals