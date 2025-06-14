# booking/admin.py
"""
Django admin configuration for the Aperture Booking.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    UserProfile, Resource, Booking, BookingAttendee, 
    ApprovalRule, Maintenance, BookingHistory,
    Notification, NotificationPreference, EmailTemplate,
    WaitingListEntry, WaitingListNotification,
    CheckInOutEvent, UsageAnalytics,
    Faculty, College, Department
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    readonly_fields = ('created_at',)


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'faculty', 'is_active', 'created_at')
    list_filter = ('faculty', 'is_active')
    search_fields = ('name', 'code', 'faculty__name')
    readonly_fields = ('created_at',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'college', 'is_active', 'created_at')
    list_filter = ('college__faculty', 'college', 'is_active')
    search_fields = ('name', 'code', 'college__name', 'college__faculty__name')
    readonly_fields = ('created_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'academic_path', 'student_level', 'training_level', 'is_inducted')
    list_filter = ('role', 'faculty', 'college', 'department', 'student_level', 'training_level', 'is_inducted')
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name', 
        'student_id', 'staff_number', 'faculty__name', 'college__name', 'department__name'
    )
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role')
        }),
        ('Academic Structure', {
            'fields': ('faculty', 'college', 'department', 'group')
        }),
        ('Role-Specific Information', {
            'fields': ('student_id', 'student_level', 'staff_number')
        }),
        ('System Information', {
            'fields': ('training_level', 'is_inducted', 'email_verified', 'phone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'resource_type', 'location', 'capacity', 'required_training_level', 'is_active')
    list_filter = ('resource_type', 'location', 'is_active', 'requires_induction')
    search_fields = ('name', 'description', 'location')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource', 'user', 'start_time', 'end_time', 'status', 'checkin_status', 'is_checked_in')
    list_filter = ('status', 'resource__resource_type', 'is_recurring', 'shared_with_group', 'no_show', 'auto_checked_out')
    search_fields = ('title', 'description', 'user__username', 'resource__name')
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'checked_in_at', 'checked_out_at', 'actual_start_time', 'actual_end_time')
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'resource', 'user', 'status')
        }),
        ('Scheduling', {
            'fields': ('start_time', 'end_time', 'is_recurring', 'recurring_pattern')
        }),
        ('Sharing & Attendees', {
            'fields': ('shared_with_group', 'notes')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Check-in/Check-out', {
            'fields': ('checked_in_at', 'checked_out_at', 'actual_start_time', 'actual_end_time', 'no_show', 'auto_checked_out'),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_no_show', 'auto_check_out_selected']
    
    def is_checked_in(self, obj):
        return obj.is_checked_in
    is_checked_in.boolean = True
    is_checked_in.short_description = 'Checked In'
    
    def checkin_status(self, obj):
        return obj.checkin_status
    checkin_status.short_description = 'Status'
    
    def mark_no_show(self, request, queryset):
        """Mark selected bookings as no-show."""
        from .checkin_service import checkin_service
        
        count = 0
        for booking in queryset:
            if not booking.checked_in_at and not booking.no_show:
                try:
                    success, message = checkin_service.mark_no_show(booking.id, request.user, "Marked by admin")
                    if success:
                        count += 1
                except Exception:
                    pass
        
        self.message_user(request, f'Marked {count} bookings as no-show.')
    mark_no_show.short_description = 'Mark selected bookings as no-show'
    
    def auto_check_out_selected(self, request, queryset):
        """Auto check-out selected bookings."""
        count = 0
        for booking in queryset:
            if booking.is_checked_in:
                try:
                    if booking.auto_check_out():
                        count += 1
                except Exception:
                    pass
        
        self.message_user(request, f'Auto checked-out {count} bookings.')
    auto_check_out_selected.short_description = 'Auto check-out selected bookings'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('resource', 'user', 'approved_by')


@admin.register(BookingAttendee)
class BookingAttendeeAdmin(admin.ModelAdmin):
    list_display = ('booking', 'user', 'is_primary', 'added_at')
    list_filter = ('is_primary',)
    search_fields = ('booking__title', 'user__username')


@admin.register(ApprovalRule)
class ApprovalRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'resource', 'approval_type', 'is_active', 'priority')
    list_filter = ('approval_type', 'is_active')
    search_fields = ('name', 'resource__name')
    filter_horizontal = ('approvers',)


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource', 'start_time', 'end_time', 'maintenance_type', 'blocks_booking')
    list_filter = ('maintenance_type', 'blocks_booking', 'is_recurring')
    search_fields = ('title', 'description', 'resource__name')
    date_hierarchy = 'start_time'


@admin.register(BookingHistory)
class BookingHistoryAdmin(admin.ModelAdmin):
    list_display = ('booking', 'user', 'action', 'timestamp')
    list_filter = ('action',)
    search_fields = ('booking__title', 'user__username', 'action')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'delivery_method', 'status', 'priority', 'created_at')
    list_filter = ('notification_type', 'delivery_method', 'status', 'priority', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'sent_at', 'read_at')
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'booking', 'resource', 'maintenance')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'delivery_method', 'is_enabled', 'frequency')
    list_filter = ('notification_type', 'delivery_method', 'is_enabled', 'frequency')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'notification_type', 'is_active', 'created_at')
    list_filter = ('notification_type', 'is_active')
    search_fields = ('name', 'subject_template')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'notification_type', 'is_active')
        }),
        ('Email Content', {
            'fields': ('subject_template', 'html_template', 'text_template')
        }),
        ('Template Variables', {
            'fields': ('available_variables',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(WaitingListEntry)
class WaitingListEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'resource', 'preferred_start_time', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'resource__resource_type', 'flexible_start_time', 'auto_book')
    search_fields = ('user__username', 'user__email', 'resource__name', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'notified_at', 'fulfilled_at')
    date_hierarchy = 'preferred_start_time'
    
    fieldsets = (
        ('User and Resource', {
            'fields': ('user', 'resource', 'status', 'priority')
        }),
        ('Time Preferences', {
            'fields': (
                'preferred_start_time', 'preferred_end_time',
                'min_duration_minutes', 'max_duration_minutes'
            )
        }),
        ('Flexibility Options', {
            'fields': (
                'flexible_start_time', 'flexible_duration', 
                'max_days_advance', 'auto_book'
            )
        }),
        ('Notifications', {
            'fields': (
                'notify_immediately', 'notification_advance_hours'
            )
        }),
        ('Metadata', {
            'fields': ('notes', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'notified_at', 'fulfilled_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'resource')
    
    actions = ['mark_as_expired', 'mark_as_cancelled', 'process_waiting_list']
    
    def mark_as_expired(self, request, queryset):
        """Mark selected entries as expired."""
        updated = queryset.filter(status='active').update(status='expired')
        self.message_user(request, f'Marked {updated} entries as expired.')
    mark_as_expired.short_description = 'Mark selected entries as expired'
    
    def mark_as_cancelled(self, request, queryset):
        """Cancel selected entries."""
        updated = queryset.filter(status__in=['active', 'notified']).update(status='cancelled')
        self.message_user(request, f'Cancelled {updated} entries.')
    mark_as_cancelled.short_description = 'Cancel selected entries'
    
    def process_waiting_list(self, request, queryset):
        """Process waiting list for selected entries' resources."""
        from .waiting_list import waiting_list_service
        
        resources = set(entry.resource for entry in queryset)
        total_notifications = 0
        
        for resource in resources:
            notifications_sent = waiting_list_service.process_waiting_list_for_resource(resource)
            total_notifications += notifications_sent
        
        self.message_user(request, f'Processed waiting lists for {len(resources)} resources. {total_notifications} notifications sent.')
    process_waiting_list.short_description = 'Process waiting list for selected resources'


@admin.register(WaitingListNotification)
class WaitingListNotificationAdmin(admin.ModelAdmin):
    list_display = ('waiting_list_entry', 'available_start_time', 'user_response', 'sent_at', 'response_deadline')
    list_filter = ('user_response', 'sent_at', 'waiting_list_entry__resource')
    search_fields = ('waiting_list_entry__user__username', 'waiting_list_entry__resource__name')
    readonly_fields = ('sent_at', 'responded_at')
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('waiting_list_entry', 'available_start_time', 'available_end_time')
        }),
        ('Response Tracking', {
            'fields': ('user_response', 'response_deadline', 'responded_at')
        }),
        ('Booking Result', {
            'fields': ('booking_created',)
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'expires_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'waiting_list_entry__user', 
            'waiting_list_entry__resource',
            'booking_created'
        )


@admin.register(CheckInOutEvent)
class CheckInOutEventAdmin(admin.ModelAdmin):
    list_display = ('booking', 'event_type', 'user', 'timestamp', 'actual_time')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('booking__title', 'user__username', 'notes')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Event Details', {
            'fields': ('booking', 'event_type', 'user', 'timestamp', 'actual_time')
        }),
        ('Additional Information', {
            'fields': ('notes', 'ip_address', 'user_agent', 'location_data'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('booking__resource', 'user')


@admin.register(UsageAnalytics)
class UsageAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('resource', 'date', 'total_bookings', 'utilization_rate', 'efficiency_rate', 'no_show_rate')
    list_filter = ('date', 'resource__resource_type')
    search_fields = ('resource__name',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('resource', 'date')
        }),
        ('Booking Statistics', {
            'fields': ('total_bookings', 'completed_bookings', 'no_show_bookings', 'cancelled_bookings')
        }),
        ('Time Statistics (Minutes)', {
            'fields': ('total_booked_minutes', 'total_actual_minutes', 'total_wasted_minutes')
        }),
        ('Efficiency Metrics', {
            'fields': ('utilization_rate', 'efficiency_rate', 'no_show_rate')
        }),
        ('Timing Analysis', {
            'fields': (
                'avg_early_checkin_minutes', 'avg_late_checkin_minutes',
                'avg_early_checkout_minutes', 'avg_late_checkout_minutes'
            ),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('resource')