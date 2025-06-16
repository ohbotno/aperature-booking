# booking/serializers.py
"""
DRF serializers for the Aperture Booking.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Resource, Booking, BookingAttendee, ApprovalRule, Maintenance, WaitingListEntry


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'full_name', 'role', 'group', 'college', 
            'student_id', 'phone', 'training_level', 'is_inducted',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ResourceSerializer(serializers.ModelSerializer):
    available_for_user = serializers.SerializerMethodField()
    
    class Meta:
        model = Resource
        fields = [
            'id', 'name', 'resource_type', 'description', 'location',
            'capacity', 'required_training_level', 'requires_induction',
            'max_booking_hours', 'is_active', 'available_for_user',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'available_for_user']
    
    def get_available_for_user(self, obj):
        """Check if resource is available for the current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                user_profile = request.user.userprofile
                return obj.is_available_for_user(user_profile)
            except UserProfile.DoesNotExist:
                return False
        return False


class BookingAttendeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BookingAttendee
        fields = ['id', 'user', 'is_primary', 'added_at']
        read_only_fields = ['id', 'added_at']


class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    resource = ResourceSerializer(read_only=True)
    resource_id = serializers.IntegerField(write_only=True)
    attendees = BookingAttendeeSerializer(source='bookingattendee_set', many=True, read_only=True)
    duration_hours = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    has_conflicts = serializers.SerializerMethodField()
    can_start = serializers.SerializerMethodField()
    dependency_status = serializers.SerializerMethodField()
    prerequisite_bookings = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all(), many=True, required=False)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'resource', 'resource_id', 'user', 'title', 'description',
            'start_time', 'end_time', 'status', 'is_recurring', 'recurring_pattern',
            'shared_with_group', 'attendees', 'notes', 'duration_hours',
            'can_cancel', 'has_conflicts', 'can_start', 'dependency_status',
            'prerequisite_bookings', 'dependency_type', 'dependency_conditions',
            'created_at', 'updated_at', 'approved_by', 'approved_at'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at', 'duration_hours',
            'can_cancel', 'has_conflicts', 'can_start', 'dependency_status',
            'approved_by', 'approved_at'
        ]
    
    def get_duration_hours(self, obj):
        """Calculate booking duration in hours."""
        return obj.duration.total_seconds() / 3600
    
    def get_can_cancel(self, obj):
        """Check if booking can be cancelled."""
        return obj.can_be_cancelled
    
    def get_has_conflicts(self, obj):
        """Check if booking has conflicts."""
        return obj.has_conflicts()
    
    def get_can_start(self, obj):
        """Check if booking can start based on dependencies."""
        return obj.can_start
    
    def get_dependency_status(self, obj):
        """Get human-readable dependency status."""
        return obj.dependency_status
    
    def validate_resource_id(self, value):
        """Validate that resource exists and is active."""
        try:
            resource = Resource.objects.get(id=value)
            if not resource.is_active:
                raise serializers.ValidationError("Selected resource is not active.")
            return value
        except Resource.DoesNotExist:
            raise serializers.ValidationError("Selected resource does not exist.")
    
    def validate(self, data):
        """Validate booking data."""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        resource_id = data.get('resource_id')
        
        if start_time and end_time:
            # Check time order
            if start_time >= end_time:
                raise serializers.ValidationError("End time must be after start time.")
            
            # Check booking window (9 AM - 6 PM)
            if (start_time.hour < 9 or start_time.hour >= 18 or
                end_time.hour < 9 or end_time.hour > 18):
                raise serializers.ValidationError("Bookings must be between 09:00 and 18:00.")
            
            # Check resource availability and conflicts
            if resource_id:
                try:
                    resource = Resource.objects.get(id=resource_id)
                    
                    # Check user permissions
                    request = self.context.get('request')
                    if request and request.user.is_authenticated:
                        try:
                            user_profile = request.user.userprofile
                            if not resource.is_available_for_user(user_profile):
                                raise serializers.ValidationError(
                                    "You don't have permission to book this resource."
                                )
                        except UserProfile.DoesNotExist:
                            raise serializers.ValidationError(
                                "User profile not found. Please contact administrator."
                            )
                    
                    # Check for conflicts (excluding current booking if updating)
                    conflicts = Booking.objects.filter(
                        resource=resource,
                        status__in=['approved', 'pending'],
                        start_time__lt=end_time,
                        end_time__gt=start_time
                    )
                    
                    if self.instance:
                        conflicts = conflicts.exclude(pk=self.instance.pk)
                    
                    if conflicts.exists():
                        raise serializers.ValidationError("This time slot conflicts with existing bookings.")
                    
                    # Check max booking hours
                    if resource.max_booking_hours:
                        duration_hours = (end_time - start_time).total_seconds() / 3600
                        if duration_hours > resource.max_booking_hours:
                            raise serializers.ValidationError(
                                f"Booking exceeds maximum allowed hours ({resource.max_booking_hours}h)."
                            )
                
                except Resource.DoesNotExist:
                    raise serializers.ValidationError("Selected resource does not exist.")
        
        return data
    
    def create(self, validated_data):
        """Create a new booking."""
        validated_data['user'] = self.context['request'].user
        resource_id = validated_data.pop('resource_id')
        validated_data['resource'] = Resource.objects.get(id=resource_id)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Update an existing booking."""
        if 'resource_id' in validated_data:
            resource_id = validated_data.pop('resource_id')
            validated_data['resource'] = Resource.objects.get(id=resource_id)
        return super().update(instance, validated_data)


class ApprovalRuleSerializer(serializers.ModelSerializer):
    resource = ResourceSerializer(read_only=True)
    approvers = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = ApprovalRule
        fields = [
            'id', 'name', 'resource', 'approval_type', 'user_roles',
            'approvers', 'conditions', 'is_active', 'priority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MaintenanceSerializer(serializers.ModelSerializer):
    resource = ResourceSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Maintenance
        fields = [
            'id', 'resource', 'title', 'description', 'start_time', 'end_time',
            'maintenance_type', 'is_recurring', 'recurring_pattern',
            'blocks_booking', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class WaitingListEntrySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    resource = ResourceSerializer(read_only=True)
    resource_id = serializers.IntegerField(write_only=True)
    resulting_booking = BookingSerializer(read_only=True)
    time_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    can_auto_book = serializers.SerializerMethodField()
    
    class Meta:
        model = WaitingListEntry
        fields = [
            'id', 'user', 'resource', 'resource_id', 'desired_start_time', 'desired_end_time',
            'title', 'description', 'flexible_start', 'flexible_duration',
            'min_duration_minutes', 'max_wait_days', 'priority', 'auto_book',
            'notification_hours_ahead', 'status', 'position', 'times_notified',
            'last_notification_sent', 'resulting_booking', 'availability_window_start',
            'availability_window_end', 'response_deadline', 'time_remaining',
            'is_expired', 'can_auto_book', 'created_at', 'updated_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'position', 'times_notified',
            'last_notification_sent', 'resulting_booking', 'availability_window_start',
            'availability_window_end', 'response_deadline', 'time_remaining',
            'is_expired', 'can_auto_book', 'created_at', 'updated_at', 'expires_at'
        ]
    
    def get_time_remaining(self, obj):
        """Get time remaining until expiration."""
        remaining = obj.time_remaining
        if remaining:
            return remaining.total_seconds()
        return None
    
    def get_is_expired(self, obj):
        """Check if waiting list entry has expired."""
        return obj.is_expired
    
    def get_can_auto_book(self, obj):
        """Check if this entry can be auto-booked."""
        return obj.can_auto_book
    
    def validate_resource_id(self, value):
        """Validate that resource exists and is active."""
        try:
            resource = Resource.objects.get(id=value)
            if not resource.is_active:
                raise serializers.ValidationError("Selected resource is not active.")
            return value
        except Resource.DoesNotExist:
            raise serializers.ValidationError("Selected resource does not exist.")
    
    def validate(self, data):
        """Validate waiting list entry data."""
        desired_start_time = data.get('desired_start_time')
        desired_end_time = data.get('desired_end_time')
        min_duration_minutes = data.get('min_duration_minutes', 60)
        
        if desired_start_time and desired_end_time:
            # Check time order
            if desired_start_time >= desired_end_time:
                raise serializers.ValidationError("End time must be after start time.")
            
            # Check minimum duration
            duration_minutes = (desired_end_time - desired_start_time).total_seconds() / 60
            if min_duration_minutes > duration_minutes:
                raise serializers.ValidationError(
                    "Minimum duration cannot be longer than desired duration."
                )
        
        return data
    
    def create(self, validated_data):
        """Create a new waiting list entry."""
        validated_data['user'] = self.context['request'].user
        resource_id = validated_data.pop('resource_id')
        validated_data['resource'] = Resource.objects.get(id=resource_id)
        return super().create(validated_data)