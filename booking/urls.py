# booking/urls.py
"""
URL configuration for the booking app.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from django.urls import path, include
from . import views

app_name = 'booking'

urlpatterns = [
    
    # Template views
    path('', views.calendar_view, name='calendar'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    
    # Resource management URLs
    path('resources/', views.resources_list_view, name='resources_list'),
    path('resources/<int:resource_id>/', views.resource_detail_view, name='resource_detail'),
    path('resources/<int:resource_id>/request-access/', views.request_resource_access_view, name='request_resource_access'),
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
    path('booking/<int:pk>/edit/', views.edit_booking_view, name='edit_booking'),
    path('booking/<int:pk>/cancel/', views.cancel_booking_view, name='cancel_booking'),
    path('booking/<int:pk>/duplicate/', views.duplicate_booking_view, name='duplicate_booking'),
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
    
    # Notification URLs
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/preferences/', views.notification_preferences_view, name='notification_preferences'),
    
    # Waiting List URLs
    path('waiting-list/', views.waiting_list_view, name='waiting_list'),
    path('waiting-list/join/<int:resource_id>/', views.join_waiting_list, name='join_waiting_list'),
    path('waiting-list/leave/<int:entry_id>/', views.leave_waiting_list, name='leave_waiting_list'),
    path('waiting-list/respond/<int:notification_id>/', views.respond_to_availability, name='respond_to_availability'),
    
    # Check-in/Check-out URLs
    path('booking/<int:booking_id>/checkin/', views.checkin_view, name='checkin'),
    path('booking/<int:booking_id>/checkout/', views.checkout_view, name='checkout'),
    path('checkin-status/', views.checkin_status_view, name='checkin_status'),
    path('resource/<int:resource_id>/checkin-status/', views.resource_checkin_status_view, name='resource_checkin_status'),
    path('usage-analytics/', views.usage_analytics_view, name='usage_analytics'),
    
]