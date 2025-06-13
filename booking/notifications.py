# booking/notifications.py
"""
Notification service for the Lab Booking System.

This file is part of the Lab Booking System.
Copyright (C) 2025 Lab Booking System Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q
from .models import (
    Notification, NotificationPreference, EmailTemplate, 
    Booking, Resource, Maintenance, UserProfile
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating and sending notifications."""
    
    def __init__(self):
        self.default_preferences = {
            'booking_confirmed': {'email': True, 'in_app': True},
            'booking_cancelled': {'email': True, 'in_app': True},
            'booking_reminder': {'email': True, 'in_app': False},
            'approval_request': {'email': True, 'in_app': True},
            'approval_decision': {'email': True, 'in_app': True},
            'maintenance_alert': {'email': True, 'in_app': True},
            'conflict_detected': {'email': True, 'in_app': True},
            'quota_warning': {'email': True, 'in_app': False},
        }
    
    def create_notification(
        self,
        user,
        notification_type: str,
        title: str,
        message: str,
        priority: str = 'medium',
        booking: Optional[Booking] = None,
        resource: Optional[Resource] = None,
        maintenance: Optional[Maintenance] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Notification]:
        """Create notifications based on user preferences."""
        notifications = []
        
        # Get user preferences or use defaults
        preferences = self._get_user_preferences(user, notification_type)
        
        for delivery_method, is_enabled in preferences.items():
            if is_enabled:
                notification = Notification.objects.create(
                    user=user,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    priority=priority,
                    delivery_method=delivery_method,
                    booking=booking,
                    resource=resource,
                    maintenance=maintenance,
                    metadata=metadata or {}
                )
                notifications.append(notification)
        
        return notifications
    
    def _get_user_preferences(self, user, notification_type: str) -> Dict[str, bool]:
        """Get user notification preferences for a specific type."""
        preferences = {}
        
        # Query user's explicit preferences
        user_prefs = NotificationPreference.objects.filter(
            user=user,
            notification_type=notification_type,
            is_enabled=True
        )
        
        for pref in user_prefs:
            preferences[pref.delivery_method] = True
        
        # Fill in defaults for missing preferences
        defaults = self.default_preferences.get(notification_type, {})
        for method, enabled in defaults.items():
            if method not in preferences:
                preferences[method] = enabled
        
        return preferences
    
    def send_pending_notifications(self) -> int:
        """Send all pending notifications."""
        pending_notifications = Notification.objects.filter(
            Q(status='pending') &
            (Q(next_retry_at__isnull=True) | Q(next_retry_at__lte=timezone.now()))
        ).select_related('user', 'booking', 'resource', 'maintenance')
        
        sent_count = 0
        
        for notification in pending_notifications:
            try:
                if notification.delivery_method == 'email':
                    self._send_email_notification(notification)
                elif notification.delivery_method == 'sms':
                    self._send_sms_notification(notification)
                elif notification.delivery_method == 'in_app':
                    # In-app notifications are already "sent" when created
                    notification.mark_as_sent()
                
                sent_count += 1
                logger.info(f"Sent {notification.delivery_method} notification to {notification.user.username}")
                
            except Exception as e:
                logger.error(f"Failed to send notification {notification.id}: {str(e)}")
                notification.mark_as_failed()
        
        return sent_count
    
    def _send_email_notification(self, notification: Notification):
        """Send email notification."""
        # Get email template
        template = self._get_email_template(notification.notification_type)
        
        if not template:
            # Fallback to basic email
            self._send_basic_email(notification)
            return
        
        # Build context for template
        context = self._build_email_context(notification)
        
        # Render email content
        subject = template.render_subject(context)
        html_content = template.render_html(context)
        text_content = template.render_text(context)
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[notification.user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        notification.mark_as_sent()
    
    def _send_basic_email(self, notification: Notification):
        """Send basic email without template."""
        from django.core.mail import send_mail
        
        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.user.email],
            fail_silently=False
        )
        
        notification.mark_as_sent()
    
    def _send_sms_notification(self, notification: Notification):
        """Send SMS notification (placeholder for future implementation)."""
        # TODO: Implement SMS service (Twilio, AWS SNS, etc.)
        logger.info(f"SMS notification queued for {notification.user.username}: {notification.title}")
        notification.mark_as_sent()
    
    def _get_email_template(self, notification_type: str) -> Optional[EmailTemplate]:
        """Get active email template for notification type."""
        try:
            return EmailTemplate.objects.get(
                notification_type=notification_type,
                is_active=True
            )
        except EmailTemplate.DoesNotExist:
            return None
    
    def _build_email_context(self, notification: Notification) -> Dict[str, Any]:
        """Build context variables for email template rendering."""
        context = {
            'user': notification.user,
            'user_profile': getattr(notification.user, 'userprofile', None),
            'notification': notification,
            'site_name': getattr(settings, 'SITE_NAME', 'Lab Booking System'),
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        # Add related objects
        if notification.booking:
            context['booking'] = notification.booking
            context['resource'] = notification.booking.resource
        
        if notification.resource:
            context['resource'] = notification.resource
        
        if notification.maintenance:
            context['maintenance'] = notification.maintenance
            context['resource'] = notification.maintenance.resource
        
        # Add metadata
        context.update(notification.metadata)
        
        return context
    
    def get_user_notifications(self, user, limit: int = 20, unread_only: bool = False) -> List[Notification]:
        """Get notifications for a user."""
        queryset = Notification.objects.filter(
            user=user,
            delivery_method='in_app'
        ).select_related('booking', 'resource', 'maintenance')
        
        if unread_only:
            queryset = queryset.filter(status__in=['pending', 'sent'])
        
        return list(queryset[:limit])
    
    def mark_notifications_as_read(self, user, notification_ids: List[int]) -> int:
        """Mark multiple notifications as read."""
        updated = Notification.objects.filter(
            user=user,
            id__in=notification_ids,
            delivery_method='in_app',
            status__in=['pending', 'sent']
        ).update(
            status='read',
            read_at=timezone.now(),
            updated_at=timezone.now()
        )
        
        return updated


class BookingNotifications:
    """Helper class for booking-specific notifications."""
    
    def __init__(self):
        self.service = NotificationService()
    
    def booking_created(self, booking: Booking):
        """Send notification when booking is created."""
        if booking.status == 'confirmed':
            self.booking_confirmed(booking)
        else:
            # Notify managers about approval request
            self._notify_approvers(booking)
    
    def booking_confirmed(self, booking: Booking):
        """Send notification when booking is confirmed."""
        self.service.create_notification(
            user=booking.user,
            notification_type='booking_confirmed',
            title=f'Booking Confirmed: {booking.resource.name}',
            message=f'Your booking "{booking.title}" has been confirmed for {booking.start_time.strftime("%B %d, %Y at %I:%M %p")}.',
            priority='medium',
            booking=booking,
            metadata={
                'booking_id': booking.id,
                'resource_name': booking.resource.name,
                'start_time': booking.start_time.isoformat(),
            }
        )
    
    def booking_cancelled(self, booking: Booking, cancelled_by):
        """Send notification when booking is cancelled."""
        if cancelled_by != booking.user:
            # Notify user if someone else cancelled their booking
            self.service.create_notification(
                user=booking.user,
                notification_type='booking_cancelled',
                title=f'Booking Cancelled: {booking.resource.name}',
                message=f'Your booking "{booking.title}" has been cancelled by {cancelled_by.get_full_name()}.',
                priority='high',
                booking=booking,
                metadata={
                    'booking_id': booking.id,
                    'cancelled_by': cancelled_by.get_full_name(),
                }
            )
    
    def booking_reminder(self, booking: Booking, hours_ahead: int = 24):
        """Send booking reminder notification."""
        self.service.create_notification(
            user=booking.user,
            notification_type='booking_reminder',
            title=f'Upcoming Booking: {booking.resource.name}',
            message=f'Reminder: You have a booking "{booking.title}" in {hours_ahead} hours.',
            priority='low',
            booking=booking,
            metadata={
                'booking_id': booking.id,
                'hours_ahead': hours_ahead,
            }
        )
    
    def conflict_detected(self, booking: Booking, conflicting_bookings: List[Booking]):
        """Send notification when booking conflicts are detected."""
        conflict_details = [
            f"{b.title} ({b.start_time.strftime('%m/%d %I:%M %p')} - {b.end_time.strftime('%I:%M %p')})"
            for b in conflicting_bookings
        ]
        
        self.service.create_notification(
            user=booking.user,
            notification_type='conflict_detected',
            title=f'Booking Conflict Detected: {booking.resource.name}',
            message=f'Your booking "{booking.title}" conflicts with: {", ".join(conflict_details)}',
            priority='high',
            booking=booking,
            metadata={
                'booking_id': booking.id,
                'conflicting_booking_ids': [b.id for b in conflicting_bookings],
            }
        )
    
    def _notify_approvers(self, booking: Booking):
        """Notify managers about approval requests."""
        # Get lab managers and system admins
        approvers = UserProfile.objects.filter(
            role__in=['lab_manager', 'sysadmin']
        ).select_related('user')
        
        for approver_profile in approvers:
            self.service.create_notification(
                user=approver_profile.user,
                notification_type='approval_request',
                title=f'Approval Required: {booking.resource.name}',
                message=f'New booking "{booking.title}" by {booking.user.get_full_name()} requires approval.',
                priority='medium',
                booking=booking,
                metadata={
                    'booking_id': booking.id,
                    'requester': booking.user.get_full_name(),
                }
            )


class MaintenanceNotifications:
    """Helper class for maintenance-specific notifications."""
    
    def __init__(self):
        self.service = NotificationService()
    
    def maintenance_scheduled(self, maintenance: Maintenance):
        """Send notification when maintenance is scheduled."""
        # Notify users with upcoming bookings for this resource
        affected_bookings = Booking.objects.filter(
            resource=maintenance.resource,
            start_time__gte=maintenance.start_time - timezone.timedelta(days=1),
            start_time__lte=maintenance.end_time + timezone.timedelta(days=1),
            status__in=['confirmed', 'pending']
        ).select_related('user')
        
        affected_users = set(booking.user for booking in affected_bookings)
        
        for user in affected_users:
            self.service.create_notification(
                user=user,
                notification_type='maintenance_alert',
                title=f'Maintenance Scheduled: {maintenance.resource.name}',
                message=f'Maintenance is scheduled for {maintenance.resource.name} from {maintenance.start_time.strftime("%B %d")} to {maintenance.end_time.strftime("%B %d")}. Your bookings may be affected.',
                priority='high',
                maintenance=maintenance,
                metadata={
                    'maintenance_id': maintenance.id,
                    'resource_name': maintenance.resource.name,
                }
            )


# Global service instances
notification_service = NotificationService()
booking_notifications = BookingNotifications()
maintenance_notifications = MaintenanceNotifications()