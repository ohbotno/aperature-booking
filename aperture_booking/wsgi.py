# aperture_booking/wsgi.py
"""
WSGI config for aperture_booking project.

This file is part of the Aperature Booking.
Copyright (C) 2025 Aperature Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperature-booking.org/commercial
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aperture_booking.settings')

application = get_wsgi_application()