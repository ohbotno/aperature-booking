# booking/api_urls.py
"""
API URL configuration for the booking app.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'resources', views.ResourceViewSet)
router.register(r'bookings', views.BookingViewSet)
router.register(r'approval-rules', views.ApprovalRuleViewSet)
router.register(r'maintenance', views.MaintenanceViewSet)
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'notification-preferences', views.NotificationPreferenceViewSet, basename='notification-preference')
router.register(r'waiting-list', views.WaitingListEntryViewSet, basename='waiting-list-entry')
router.register(r'waiting-list-notifications', views.WaitingListNotificationViewSet, basename='waiting-list-notification')

app_name = 'api'

urlpatterns = [
    # API URLs
    path('', include(router.urls)),
    
    # Additional API endpoints
    path('booking/<int:booking_id>/checkin/', views.api_checkin_booking, name='checkin'),
    path('booking/<int:booking_id>/checkout/', views.api_checkout_booking, name='api_checkout'),
    
    # AJAX URLs for dynamic form loading
    path('ajax/load-colleges/', views.ajax_load_colleges, name='ajax_load_colleges'),
    path('ajax/load-departments/', views.ajax_load_departments, name='ajax_load_departments'),
]