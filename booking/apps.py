# booking/apps.py
"""
App configuration for the booking app.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperture-booking.org/commercial
"""

from django.apps import AppConfig


class BookingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booking'
    
    def ready(self):
        import booking.signals