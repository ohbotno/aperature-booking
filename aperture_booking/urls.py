# aperture_booking/urls.py
"""
URL configuration for aperture_booking project.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from booking.forms import CustomAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),
    # Custom login view with our form
    path('accounts/login/', auth_views.LoginView.as_view(authentication_form=CustomAuthenticationForm), name='login'),
    # Include other auth URLs
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/', include('booking.api_urls')),
    path('', include('booking.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)