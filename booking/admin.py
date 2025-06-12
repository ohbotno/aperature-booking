# booking/admin.py
"""
Django admin configuration for the Lab Booking System.

This file is part of the Lab Booking System.
Copyright (C) 2025 Lab Booking System Contributors

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
    ApprovalRule, Maintenance, BookingHistory
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'group', 'college', 'training_level', 'is_inducted')
    list_filter = ('role', 'group', 'college', 'training_level', 'is_inducted')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'student_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'resource_type', 'location', 'capacity', 'required_training_level', 'is_active')
    list_filter = ('resource_type', 'location', 'is_active', 'requires_induction')
    search_fields = ('name', 'description', 'location')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource', 'user', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'resource__resource_type', 'is_recurring', 'shared_with_group')
    search_fields = ('title', 'description', 'user__username', 'resource__name')
    readonly_fields = ('created_at', 'updated_at', 'approved_at')
    date_hierarchy = 'start_time'
    
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