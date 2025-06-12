# booking/urls.py
"""
URL configuration for the booking app.

This file is part of the Lab Booking System.
Copyright (C) 2025 Lab Booking System Contributors

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

app_name = 'booking'

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    
    # Template views
    path('', views.calendar_view, name='calendar'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('verify-email/<uuid:token>/', views.verify_email_view, name='verify_email'),
    path('resend-verification/', views.resend_verification_view, name='resend_verification'),
]