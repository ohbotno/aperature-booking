# aperture_booking/urls.py
"""
URL configuration for aperture_booking project.

This file is part of the Aperature Booking.
Copyright (C) 2025 Aperature Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperature-booking.org/commercial
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from booking.forms import CustomAuthenticationForm
from booking.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Custom login view with our form and first login logic
    path('accounts/login/', CustomLoginView.as_view(authentication_form=CustomAuthenticationForm), name='login'),
    # Include other auth URLs
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/', include('booking.api_urls')),
    path('', include('booking.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)