# booking/views/__init__.py
"""
Views package for the Aperature Booking.

This file is part of the Aperature Booking.
Copyright (C) 2025 Aperature Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperature-booking.org/commercial
"""

# Import all views from main module for backward compatibility
from .main import *

# Import licensing views module for URL routing
from . import licensing