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
    
    # Password reset URLs
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset-done/', views.password_reset_done_view, name='password_reset_done'),
    path('reset-password/<uuid:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('password-reset-complete/', views.password_reset_complete_view, name='password_reset_complete'),
    
    # Booking URLs
    path('booking/create/', views.create_booking_view, name='create_booking'),
    path('booking/<int:pk>/', views.booking_detail_view, name='booking_detail'),
    path('booking/<int:booking_pk>/recurring/', views.create_recurring_booking_view, name='create_recurring'),
    path('booking/<int:booking_pk>/cancel-series/', views.cancel_recurring_series_view, name='cancel_recurring'),
    
    # Conflict management URLs
    path('conflicts/', views.conflict_detection_view, name='conflicts'),
    path('conflicts/resolve/<str:conflict_type>/<int:id1>/<int:id2>/', views.resolve_conflict_view, name='resolve_conflict'),
    path('conflicts/bulk-resolve/', views.bulk_resolve_conflicts_view, name='bulk_resolve_conflicts'),
    
    # Template management URLs
    path('templates/', views.template_list_view, name='templates'),
    path('templates/create/', views.template_create_view, name='template_create'),
    path('templates/<int:pk>/edit/', views.template_edit_view, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete_view, name='template_delete'),
    path('templates/create-booking/', views.create_booking_from_template_view, name='create_from_template'),
    path('booking/<int:booking_pk>/save-template/', views.save_booking_as_template_view, name='save_as_template'),
    
    # Bulk operations URLs
    path('bookings/bulk/', views.bulk_booking_operations_view, name='bulk_operations'),
    path('manage/', views.booking_management_view, name='manage_bookings'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
]