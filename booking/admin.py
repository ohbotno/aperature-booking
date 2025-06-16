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
    Notification, NotificationPreference, EmailTemplate, PushSubscription,
    WaitingListEntry,
    CheckInOutEvent, UsageAnalytics,
    Faculty, College, Department,
    ResourceAccess, AccessRequest, TrainingRequest,
    SystemSetting, PDFExportSettings
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
    
    actions = ['export_users_csv', 'bulk_assign_group', 'bulk_change_role', 'bulk_set_training_level']
    
    def export_users_csv(self, request, queryset):
        """Export selected users to CSV format."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'username', 'email', 'first_name', 'last_name', 'role', 'group',
            'faculty_code', 'college_code', 'department_code', 'student_id',
            'staff_number', 'training_level', 'phone'
        ])
        
        for profile in queryset.select_related('user', 'faculty', 'college', 'department'):
            writer.writerow([
                profile.user.username,
                profile.user.email,
                profile.user.first_name,
                profile.user.last_name,
                profile.role,
                profile.group,
                profile.faculty.code if profile.faculty else '',
                profile.college.code if profile.college else '',
                profile.department.code if profile.department else '',
                profile.student_id or '',
                profile.staff_number or '',
                profile.training_level,
                profile.phone,
            ])
        
        return response
    export_users_csv.short_description = 'Export selected users as CSV'
    
    def bulk_assign_group(self, request, queryset):
        """Bulk assign group to selected users."""
        # This could be expanded to show a form, for now we'll use a simple approach
        from django.contrib import messages
        
        group_name = request.POST.get('group_name', '').strip()
        if group_name:
            updated = queryset.update(group=group_name)
            messages.success(request, f'Assigned {updated} users to group "{group_name}"')
        else:
            messages.error(request, 'Please provide a group name')
    bulk_assign_group.short_description = 'Assign group to selected users'
    
    def bulk_change_role(self, request, queryset):
        """Bulk change role for selected users."""
        # This would benefit from a proper form interface
        pass
    bulk_change_role.short_description = 'Change role for selected users'
    
    def bulk_set_training_level(self, request, queryset):
        """Bulk set training level for selected users."""
        training_level = request.POST.get('training_level')
        if training_level and training_level.isdigit():
            level = int(training_level)
            if 1 <= level <= 5:
                updated = queryset.update(training_level=level)
                self.message_user(request, f'Set training level to {level} for {updated} users.')
            else:
                self.message_user(request, 'Training level must be between 1 and 5.', level='error')
        else:
            self.message_user(request, 'Please provide a valid training level (1-5).', level='error')
    bulk_set_training_level.short_description = 'Set training level for selected users'
    
    def changelist_view(self, request, extra_context=None):
        """Add CSV import functionality to the changelist view."""
        extra_context = extra_context or {}
        
        if request.method == 'POST' and 'csv_file' in request.FILES:
            return self.handle_csv_import(request)
        
        # Add groups summary for group management
        try:
            from django.db.models import Count
            groups_summary = UserProfile.objects.exclude(group='').values('group').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            extra_context['groups_summary'] = groups_summary
        except:
            pass
            
        return super().changelist_view(request, extra_context)
    
    def handle_csv_import(self, request):
        """Handle CSV file upload and import."""
        from django.contrib import messages
        from django.shortcuts import redirect
        import tempfile
        import os
        
        csv_file = request.FILES['csv_file']
        update_existing = request.POST.get('update_existing') == 'on'
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
            return redirect('admin:booking_userprofile_changelist')
        
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp_file:
                for chunk in csv_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # Import using management command logic
            from booking.management.commands.import_users_csv import Command
            command = Command()
            
            # Capture output
            from io import StringIO
            output = StringIO()
            command.stdout = output
            
            # Run import
            command.handle(
                csv_file=tmp_file_path,
                dry_run=False,
                update_existing=update_existing,
                default_password='ChangeMe123!'
            )
            
            # Clean up
            os.unlink(tmp_file_path)
            
            # Show results
            output_text = output.getvalue()
            if 'Error' in output_text:
                messages.warning(request, f'Import completed with some issues:\n{output_text}')
            else:
                messages.success(request, f'Import successful:\n{output_text}')
                
        except Exception as e:
            messages.error(request, f'Import failed: {str(e)}')
        
        return redirect('admin:booking_userprofile_changelist')


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
    list_display = ('title', 'user', 'notification_type', 'delivery_method', 'status', 'priority', 'created_at', 'retry_count')
    list_filter = ('notification_type', 'delivery_method', 'status', 'priority', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'sent_at', 'read_at', 'next_retry_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'notification_type', 'title', 'message', 'priority', 'delivery_method', 'status')
        }),
        ('Related Objects', {
            'fields': ('booking', 'resource', 'maintenance', 'access_request', 'training_request'),
            'classes': ('collapse',)
        }),
        ('Delivery Information', {
            'fields': ('sent_at', 'read_at', 'retry_count', 'next_retry_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_sent', 'mark_as_read', 'retry_failed', 'send_pending', 'delete_old_notifications']
    
    def mark_as_sent(self, request, queryset):
        """Mark selected notifications as sent."""
        count = 0
        for notification in queryset.filter(status__in=['pending', 'failed']):
            notification.mark_as_sent()
            count += 1
        self.message_user(request, f'Marked {count} notifications as sent.')
    mark_as_sent.short_description = 'Mark as sent'
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        count = 0
        for notification in queryset.filter(status__in=['pending', 'sent']):
            notification.mark_as_read()
            count += 1
        self.message_user(request, f'Marked {count} notifications as read.')
    mark_as_read.short_description = 'Mark as read'
    
    def retry_failed(self, request, queryset):
        """Retry failed notifications."""
        from .notifications import notification_service
        
        failed_notifications = queryset.filter(status='failed')
        for notification in failed_notifications:
            notification.status = 'pending'
            notification.next_retry_at = None
            notification.save(update_fields=['status', 'next_retry_at'])
        
        sent_count = notification_service.send_pending_notifications()
        self.message_user(request, f'Reset {failed_notifications.count()} failed notifications. {sent_count} notifications processed.')
    retry_failed.short_description = 'Retry failed notifications'
    
    def send_pending(self, request, queryset):
        """Send pending notifications."""
        from .notifications import notification_service
        
        sent_count = notification_service.send_pending_notifications()
        self.message_user(request, f'Processed pending notifications. {sent_count} notifications sent.')
    send_pending.short_description = 'Send pending notifications'
    
    def delete_old_notifications(self, request, queryset):
        """Delete notifications older than 30 days."""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=30)
        old_notifications = queryset.filter(created_at__lt=cutoff_date)
        count = old_notifications.count()
        old_notifications.delete()
        
        self.message_user(request, f'Deleted {count} notifications older than 30 days.')
    delete_old_notifications.short_description = 'Delete notifications older than 30 days'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'booking', 'resource', 'maintenance')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'delivery_method', 'is_enabled', 'frequency')
    list_filter = ('notification_type', 'delivery_method', 'is_enabled', 'frequency')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['enable_notifications', 'disable_notifications', 'set_immediate_frequency', 'set_daily_digest']
    
    def enable_notifications(self, request, queryset):
        """Enable selected notification preferences."""
        updated = queryset.update(is_enabled=True)
        self.message_user(request, f'Enabled {updated} notification preferences.')
    enable_notifications.short_description = 'Enable selected preferences'
    
    def disable_notifications(self, request, queryset):
        """Disable selected notification preferences.""" 
        updated = queryset.update(is_enabled=False)
        self.message_user(request, f'Disabled {updated} notification preferences.')
    disable_notifications.short_description = 'Disable selected preferences'
    
    def set_immediate_frequency(self, request, queryset):
        """Set frequency to immediate for selected preferences."""
        updated = queryset.update(frequency='immediate')
        self.message_user(request, f'Set {updated} preferences to immediate frequency.')
    set_immediate_frequency.short_description = 'Set to immediate frequency'
    
    def set_daily_digest(self, request, queryset):
        """Set frequency to daily digest for selected preferences."""
        updated = queryset.update(frequency='daily_digest')
        self.message_user(request, f'Set {updated} preferences to daily digest.')
    set_daily_digest.short_description = 'Set to daily digest'


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


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint_preview', 'user_agent', 'is_active', 'created_at', 'last_used')
    list_filter = ('is_active', 'created_at', 'last_used')
    search_fields = ('user__username', 'user__email', 'user_agent', 'endpoint')
    readonly_fields = ('created_at', 'last_used', 'endpoint', 'p256dh_key', 'auth_key')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_active')
        }),
        ('Subscription Details', {
            'fields': ('endpoint', 'p256dh_key', 'auth_key', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_used'),
            'classes': ('collapse',)
        })
    )
    
    def endpoint_preview(self, obj):
        """Show preview of endpoint URL."""
        return f"{obj.endpoint[:60]}..." if len(obj.endpoint) > 60 else obj.endpoint
    endpoint_preview.short_description = 'Endpoint'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions', 'cleanup_inactive', 'test_push_notification']
    
    def activate_subscriptions(self, request, queryset):
        """Activate selected push subscriptions."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Activated {updated} push subscriptions.')
    activate_subscriptions.short_description = 'Activate selected subscriptions'
    
    def deactivate_subscriptions(self, request, queryset):
        """Deactivate selected push subscriptions."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {updated} push subscriptions.')
    deactivate_subscriptions.short_description = 'Deactivate selected subscriptions'
    
    def cleanup_inactive(self, request, queryset):
        """Remove inactive push subscriptions."""
        from .push_service import push_service
        removed = push_service.cleanup_inactive_subscriptions(days_old=30)
        self.message_user(request, f'Removed {removed} inactive push subscriptions.')
    cleanup_inactive.short_description = 'Clean up inactive subscriptions (30+ days)'
    
    def test_push_notification(self, request, queryset):
        """Send test push notifications to selected subscriptions."""
        from .push_service import push_service
        
        sent_count = 0
        for subscription in queryset.filter(is_active=True):
            success = push_service.send_push_notification(
                subscription=subscription,
                title="Test Notification",
                message="This is a test push notification from the admin interface.",
                data={'test': True, 'source': 'admin'}
            )
            if success:
                sent_count += 1
        
        self.message_user(request, f'Sent test notifications to {sent_count} devices.')
    test_push_notification.short_description = 'Send test push notification'


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


@admin.register(ResourceAccess)
class ResourceAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'resource', 'access_type', 'granted_by', 'granted_at', 'is_active', 'is_expired')
    list_filter = ('access_type', 'is_active', 'granted_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'resource__name', 'granted_by__username')
    readonly_fields = ('granted_at',)
    date_hierarchy = 'granted_at'
    
    fieldsets = (
        ('Access Information', {
            'fields': ('user', 'resource', 'access_type', 'is_active')
        }),
        ('Grant Details', {
            'fields': ('granted_by', 'granted_at', 'expires_at')
        }),
        ('Notes', {
            'fields': ('notes',)
        })
    )
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'resource', 'granted_by')
    
    actions = ['activate_access', 'deactivate_access', 'extend_access']
    
    def activate_access(self, request, queryset):
        """Activate selected access permissions."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Activated {updated} access permissions.')
    activate_access.short_description = 'Activate selected access permissions'
    
    def deactivate_access(self, request, queryset):
        """Deactivate selected access permissions."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {updated} access permissions.')
    deactivate_access.short_description = 'Deactivate selected access permissions'
    
    def extend_access(self, request, queryset):
        """Extend access by 30 days."""
        from django.utils import timezone
        from datetime import timedelta
        
        count = 0
        for access in queryset:
            if access.expires_at:
                access.expires_at = access.expires_at + timedelta(days=30)
                access.save()
                count += 1
        
        self.message_user(request, f'Extended {count} access permissions by 30 days.')
    extend_access.short_description = 'Extend selected access by 30 days'


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'resource', 'access_type', 'status', 'created_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'access_type', 'created_at', 'reviewed_at')
    search_fields = ('user__username', 'user__email', 'resource__name', 'justification', 'review_notes')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'resource', 'access_type', 'status')
        }),
        ('Request Details', {
            'fields': ('justification', 'requested_duration_days')
        }),
        ('Review Information', {
            'fields': ('reviewed_by', 'reviewed_at', 'review_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'resource', 'reviewed_by')
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        """Approve selected access requests."""
        count = 0
        for access_request in queryset.filter(status='pending'):
            try:
                access_request.approve(request.user, "Approved via admin action")
                count += 1
            except Exception as e:
                self.message_user(request, f'Error approving request {access_request.id}: {str(e)}', level='ERROR')
        
        self.message_user(request, f'Approved {count} access requests.')
    approve_requests.short_description = 'Approve selected requests'
    
    def reject_requests(self, request, queryset):
        """Reject selected access requests."""
        count = 0
        for access_request in queryset.filter(status='pending'):
            try:
                access_request.reject(request.user, "Rejected via admin action")
                count += 1
            except Exception as e:
                self.message_user(request, f'Error rejecting request {access_request.id}: {str(e)}', level='ERROR')
        
        self.message_user(request, f'Rejected {count} access requests.')
    reject_requests.short_description = 'Reject selected requests'


@admin.register(TrainingRequest)
class TrainingRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'resource', 'requested_level', 'current_level', 'status', 'created_at', 'training_date', 'reviewed_by')
    list_filter = ('status', 'requested_level', 'created_at', 'training_date')
    search_fields = ('user__username', 'user__email', 'resource__name', 'justification')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at', 'completed_date')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Training Request', {
            'fields': ('user', 'resource', 'requested_level', 'current_level', 'status')
        }),
        ('Request Details', {
            'fields': ('justification',)
        }),
        ('Training Schedule', {
            'fields': ('training_date', 'completed_date'),
            'classes': ('collapse',)
        }),
        ('Review Information', {
            'fields': ('reviewed_by', 'reviewed_at', 'review_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'resource', 'reviewed_by')
    
    actions = ['schedule_training', 'complete_training', 'cancel_training']
    
    def schedule_training(self, request, queryset):
        """Schedule training for selected requests."""
        from django.utils import timezone
        from datetime import timedelta
        
        count = 0
        training_date = timezone.now() + timedelta(days=7)  # Default to 1 week from now
        
        for training_request in queryset.filter(status='pending'):
            try:
                training_request.schedule_training(
                    training_date=training_date,
                    reviewed_by=request.user,
                    notes="Scheduled via admin action"
                )
                count += 1
            except Exception as e:
                self.message_user(request, f'Error scheduling training for request {training_request.id}: {str(e)}', level='ERROR')
        
        self.message_user(request, f'Scheduled training for {count} requests.')
    schedule_training.short_description = 'Schedule training for selected requests'
    
    def complete_training(self, request, queryset):
        """Mark training as completed for selected requests."""
        count = 0
        for training_request in queryset.filter(status__in=['pending', 'scheduled']):
            try:
                training_request.complete_training(request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f'Error completing training for request {training_request.id}: {str(e)}', level='ERROR')
        
        self.message_user(request, f'Completed training for {count} requests.')
    complete_training.short_description = 'Mark training as completed'
    
    def cancel_training(self, request, queryset):
        """Cancel selected training requests."""
        updated = queryset.filter(status__in=['pending', 'scheduled']).update(status='cancelled')
        self.message_user(request, f'Cancelled {updated} training requests.')
    cancel_training.short_description = 'Cancel selected training requests'


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value_preview', 'value_type', 'category', 'is_editable', 'updated_at')
    list_filter = ('value_type', 'category', 'is_editable')
    search_fields = ('key', 'description', 'value')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Setting Information', {
            'fields': ('key', 'description', 'category', 'is_editable')
        }),
        ('Value Configuration', {
            'fields': ('value_type', 'value')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def value_preview(self, obj):
        """Show abbreviated value for display."""
        value = obj.value
        if len(value) > 50:
            return f"{value[:47]}..."
        return value
    value_preview.short_description = 'Value'
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    actions = ['duplicate_settings', 'export_settings']
    
    def duplicate_settings(self, request, queryset):
        """Duplicate selected settings."""
        duplicated = 0
        for setting in queryset:
            new_key = f"{setting.key}_copy"
            if not SystemSetting.objects.filter(key=new_key).exists():
                SystemSetting.objects.create(
                    key=new_key,
                    value=setting.value,
                    value_type=setting.value_type,
                    description=f"Copy of {setting.description}",
                    category=setting.category,
                    is_editable=setting.is_editable
                )
                duplicated += 1
        
        self.message_user(request, f'Duplicated {duplicated} settings.')
    duplicate_settings.short_description = 'Duplicate selected settings'
    
    def export_settings(self, request, queryset):
        """Export settings as JSON."""
        import json
        from django.http import HttpResponse
        
        settings_data = []
        for setting in queryset:
            settings_data.append({
                'key': setting.key,
                'value': setting.value,
                'value_type': setting.value_type,
                'description': setting.description,
                'category': setting.category,
                'is_editable': setting.is_editable
            })
        
        response = HttpResponse(
            json.dumps(settings_data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="system_settings.json"'
        return response
    export_settings.short_description = 'Export settings as JSON'


@admin.register(PDFExportSettings)
class PDFExportSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_default', 'default_quality', 'default_orientation', 'organization_name', 'updated_at')
    list_filter = ('is_default', 'default_quality', 'default_orientation', 'include_header', 'include_legend')
    search_fields = ('name', 'description', 'organization_name', 'author_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Configuration Information', {
            'fields': ('name', 'is_default')
        }),
        ('Default Export Settings', {
            'fields': ('default_quality', 'default_orientation')
        }),
        ('Content Options', {
            'fields': (
                ('include_header', 'include_footer'),
                ('include_legend', 'include_details'),
                ('preserve_colors', 'multi_page_support'),
                'compress_pdf'
            )
        }),
        ('Customization', {
            'fields': ('header_logo_url', 'watermark_text', 'custom_css'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('author_name', 'organization_name')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['make_default', 'test_export_config', 'duplicate_config']
    
    def make_default(self, request, queryset):
        """Make selected configuration the default."""
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one configuration to make default.', level='ERROR')
            return
        
        config = queryset.first()
        PDFExportSettings.objects.filter(is_default=True).update(is_default=False)
        config.is_default = True
        config.save()
        
        self.message_user(request, f'"{config.name}" is now the default PDF export configuration.')
    make_default.short_description = 'Make selected configuration default'
    
    def test_export_config(self, request, queryset):
        """Test export configuration by generating sample JSON."""
        from django.http import HttpResponse
        import json
        
        configs = []
        for config in queryset:
            configs.append(config.to_json())
        
        response = HttpResponse(
            json.dumps(configs, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="pdf_export_configs.json"'
        return response
    test_export_config.short_description = 'Export configuration as JSON'
    
    def duplicate_config(self, request, queryset):
        """Duplicate selected configurations."""
        duplicated = 0
        for config in queryset:
            new_name = f"{config.name} (Copy)"
            if not PDFExportSettings.objects.filter(name=new_name).exists():
                PDFExportSettings.objects.create(
                    name=new_name,
                    is_default=False,  # Never duplicate as default
                    default_quality=config.default_quality,
                    default_orientation=config.default_orientation,
                    include_header=config.include_header,
                    include_footer=config.include_footer,
                    include_legend=config.include_legend,
                    include_details=config.include_details,
                    preserve_colors=config.preserve_colors,
                    multi_page_support=config.multi_page_support,
                    compress_pdf=config.compress_pdf,
                    header_logo_url=config.header_logo_url,
                    custom_css=config.custom_css,
                    watermark_text=config.watermark_text,
                    author_name=config.author_name,
                    organization_name=config.organization_name
                )
                duplicated += 1
        
        self.message_user(request, f'Duplicated {duplicated} configurations.')
    duplicate_config.short_description = 'Duplicate selected configurations'

