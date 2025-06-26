# booking/urls.py
"""
URL configuration for the booking app.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperture-booking.org/commercial
"""

from django.urls import path, include
from . import views

app_name = 'booking'

urlpatterns = [
    
    # Template views
    path('', views.calendar_view, name='calendar'),
    path('about/', views.about_page_view, name='about'),
    path('about/edit/', views.about_page_edit_view, name='about_edit'),
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
    
    # Group Management URLs (Manager only)
    path('groups/', views.group_management_view, name='group_management'),
    path('groups/<str:group_name>/', views.group_detail_view, name='group_detail'),
    path('groups/<str:group_name>/add-user/', views.add_user_to_group, name='add_user_to_group'),
    
    # Approval Workflow URLs
    path('approval/', views.approval_dashboard_view, name='approval_dashboard'),
    path('approval/access-requests/', views.access_requests_view, name='access_requests'),
    path('approval/access-requests/<int:request_id>/', views.access_request_detail_view, name='access_request_detail'),
    path('approval/access-requests/<int:request_id>/approve/', views.approve_access_request_view, name='approve_access_request'),
    path('approval/access-requests/<int:request_id>/reject/', views.reject_access_request_view, name='reject_access_request'),
    
    # Risk Assessment URLs
    path('risk-assessments/', views.risk_assessments_view, name='risk_assessments'),
    path('risk-assessments/<int:assessment_id>/', views.risk_assessment_detail_view, name='risk_assessment_detail'),
    path('risk-assessments/<int:assessment_id>/start/', views.start_risk_assessment_view, name='start_risk_assessment'),
    path('risk-assessments/<int:assessment_id>/submit/', views.submit_risk_assessment_view, name='submit_risk_assessment'),
    path('risk-assessments/create/', views.create_risk_assessment_view, name='create_risk_assessment'),
    
    # Training URLs
    path('training/', views.training_dashboard_view, name='training_dashboard'),
    path('training/courses/', views.training_courses_view, name='training_courses'),
    path('training/courses/<int:course_id>/', views.training_course_detail_view, name='training_course_detail'),
    path('training/courses/<int:course_id>/enroll/', views.enroll_training_view, name='enroll_training'),
    path('training/my-training/', views.my_training_view, name='my_training'),
    path('training/manage/', views.manage_training_view, name='manage_training'),
    
    # Resource Management URLs
    path('resources/<int:resource_id>/manage/', views.manage_resource_view, name='manage_resource'),
    path('resources/<int:resource_id>/assign-responsible/', views.assign_resource_responsible_view, name='assign_resource_responsible'),
    path('resources/<int:resource_id>/training-requirements/', views.resource_training_requirements_view, name='resource_training_requirements'),
    
    # Approval Statistics URLs
    path('statistics/', views.approval_statistics_view, name='approval_statistics'),
    
    # Approval Rules URLs
    path('approval-rules/', views.approval_rules_view, name='approval_rules'),
    path('approval-rules/<int:rule_id>/toggle/', views.approval_rule_toggle_view, name='approval_rule_toggle'),
    
    # Lab Admin URLs
    path('lab-admin/', views.lab_admin_dashboard_view, name='lab_admin_dashboard'),
    path('lab-admin/access-requests/', views.lab_admin_access_requests_view, name='lab_admin_access_requests'),
    path('lab-admin/training/', views.lab_admin_training_view, name='lab_admin_training'),
    path('lab-admin/users/', views.lab_admin_users_view, name='lab_admin_users'),
    path('lab-admin/resources/', views.lab_admin_resources_view, name='lab_admin_resources'),
    path('lab-admin/resources/add/', views.lab_admin_add_resource_view, name='lab_admin_add_resource'),
    path('lab-admin/resources/<int:resource_id>/edit/', views.lab_admin_edit_resource_view, name='lab_admin_edit_resource'),
    path('lab-admin/resources/<int:resource_id>/checklist/', views.lab_admin_resource_checklist_view, name='lab_admin_resource_checklist'),
    path('lab-admin/resources/<int:resource_id>/delete/', views.lab_admin_delete_resource_view, name='lab_admin_delete_resource'),
    path('lab-admin/maintenance/', views.lab_admin_maintenance_view, name='lab_admin_maintenance'),
    path('lab-admin/maintenance/add/', views.lab_admin_add_maintenance_view, name='lab_admin_add_maintenance'),
    path('lab-admin/maintenance/<int:maintenance_id>/', views.lab_admin_edit_maintenance_view, name='lab_admin_view_maintenance'),
    path('lab-admin/maintenance/<int:maintenance_id>/edit/', views.lab_admin_edit_maintenance_view, name='lab_admin_edit_maintenance'),
    path('lab-admin/maintenance/<int:maintenance_id>/delete/', views.lab_admin_delete_maintenance_view, name='lab_admin_delete_maintenance'),
    path('lab-admin/inductions/', views.lab_admin_inductions_view, name='lab_admin_inductions'),
    
    # Calendar Sync URLs
    path('calendar/export/', views.export_my_calendar_view, name='export_my_calendar'),
    path('calendar/feed/<str:token>/', views.my_calendar_feed_view, name='my_calendar_feed'),
    path('calendar/public/<str:token>/', views.public_calendar_feed_view, name='public_calendar_feed'),
    path('calendar/resource/<int:resource_id>/export/', views.export_resource_calendar_view, name='export_resource_calendar'),
    path('calendar/sync-settings/', views.calendar_sync_settings_view, name='calendar_sync_settings'),
    
    # Calendar Invitation URLs
    path('booking/<int:booking_id>/invitation/', views.download_booking_invitation, name='download_booking_invitation'),
    path('maintenance/<int:maintenance_id>/invitation/', views.download_maintenance_invitation, name='download_maintenance_invitation'),
    
    
    # AJAX helper URLs
    path('ajax/load-colleges/', views.ajax_load_colleges, name='ajax_load_colleges'),
    path('ajax/load-departments/', views.ajax_load_departments, name='ajax_load_departments'),
    
    # Site Administration URLs (System Admin only)
    path('site-admin/', views.site_admin_dashboard_view, name='site_admin_dashboard'),
    path('site-admin/users/', views.site_admin_users_view, name='site_admin_users'),
    path('site-admin/config/', views.site_admin_system_config_view, name='site_admin_config'),
    path('site-admin/audit/', views.site_admin_audit_logs_view, name='site_admin_audit'),
    path('site-admin/health-check/', views.site_admin_health_check_view, name='site_admin_health_check'),
    path('site-admin/test-email/', views.site_admin_test_email_view, name='site_admin_test_email'),
    path('site-admin/email-config/', views.site_admin_email_config_view, name='site_admin_email_config'),
    path('site-admin/email-config/create/', views.site_admin_email_config_create_view, name='site_admin_email_config_create'),
    path('site-admin/email-config/edit/<int:config_id>/', views.site_admin_email_config_edit_view, name='site_admin_email_config_edit'),
    path('site-admin/backup/', views.site_admin_backup_management_view, name='site_admin_backup_management'),
    path('site-admin/backup/create/', views.site_admin_backup_create_ajax, name='site_admin_backup_create_ajax'),
    path('site-admin/backup/status/', views.site_admin_backup_status_ajax, name='site_admin_backup_status_ajax'),
    path('site-admin/backup/download/<str:backup_name>/', views.site_admin_backup_download_view, name='site_admin_backup_download'),
    path('site-admin/backup/restore/<str:backup_name>/', views.site_admin_backup_restore_view, name='site_admin_backup_restore'),
    path('site-admin/backup/restore-info/<str:backup_name>/', views.site_admin_backup_restore_info_ajax, name='site_admin_backup_restore_info_ajax'),
    path('site-admin/backup/restore-execute/', views.site_admin_backup_restore_ajax, name='site_admin_backup_restore_ajax'),
    path('site-admin/backup/automation/', views.site_admin_backup_automation_view, name='site_admin_backup_automation'),
    path('site-admin/backup/automation/ajax/', views.site_admin_backup_automation_ajax, name='site_admin_backup_automation_ajax'),
    path('site-admin/backup/schedule/<int:schedule_id>/', views.site_admin_backup_schedule_detail_ajax, name='site_admin_backup_schedule_detail_ajax'),
    path('site-admin/updates/', views.site_admin_updates_view, name='site_admin_updates'),
    path('site-admin/updates/ajax/', views.site_admin_updates_ajax_view, name='site_admin_updates_ajax'),
    
    # Site Admin License Management URLs
    path('site-admin/license/', views.site_admin_license_management_view, name='site_admin_license_management'),
    path('site-admin/license/activate/', views.site_admin_license_activate_view, name='site_admin_license_activate'),
    path('site-admin/license/branding/', views.site_admin_branding_config_view, name='site_admin_branding_config'),
    path('site-admin/license/logs/', views.site_admin_license_validation_logs_view, name='site_admin_license_logs'),
    path('site-admin/license/validate/ajax/', views.site_admin_license_validate_ajax, name='site_admin_license_validate_ajax'),
    path('site-admin/license/export/', views.site_admin_license_export_view, name='site_admin_license_export'),
    
    # License Management URLs
    path('license/', views.licensing.license_status, name='license_status'),
    path('license/activate/', views.licensing.license_activate, name='license_activate'),
    path('license/configure/', views.licensing.license_configure, name='license_configure'),
    path('license/logs/', views.licensing.license_validation_logs, name='license_validation_logs'),
    path('license/validate/', views.licensing.license_validate_now, name='license_validate_now'),
    path('license/api/status/', views.licensing.license_api_status, name='license_api_status'),
    path('license/generate-key/', views.licensing.generate_license_key_view, name='generate_license_key'),
    
]