# booking/management/commands/test_notifications.py
"""
Test notification system functionality.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperture-booking.org/commercial
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from booking.models import Resource, Booking, NotificationPreference, PushSubscription
from booking.notifications import notification_service
from booking.sms_service import sms_service
from booking.push_service import push_service
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Test the complete notification system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-email',
            action='store_true',
            help='Test email notifications'
        )
        parser.add_argument(
            '--test-sms',
            action='store_true',
            help='Test SMS notifications'
        )
        parser.add_argument(
            '--test-push',
            action='store_true',
            help='Test push notifications'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username to test with (will create if not exists)'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔔 Testing Aperture Booking Notification System")
        self.stdout.write("=" * 50)
        
        # Create test user if needed
        username = options.get('user', 'testuser')
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            self.stdout.write(f"✓ Created test user: {username}")
        else:
            self.stdout.write(f"✓ Using existing user: {username}")
        
        # Test notification service availability
        self._test_service_availability()
        
        # Test notification creation
        self._test_notification_creation(user)
        
        # Test specific delivery methods
        if options['test_email']:
            self._test_email_notifications(user)
        
        if options['test_sms']:
            self._test_sms_notifications(user)
        
        if options['test_push']:
            self._test_push_notifications(user)
        
        # Test preferences
        self._test_notification_preferences(user)
        
        self.stdout.write("\n🎉 Notification system test completed!")

    def _test_service_availability(self):
        """Test if notification services are available."""
        self.stdout.write("\n📋 Testing Service Availability:")
        
        # Email service
        from django.core.mail import get_connection
        try:
            connection = get_connection()
            self.stdout.write("  ✓ Email service: Available")
        except Exception as e:
            self.stdout.write(f"  ⚠ Email service: {e}")
        
        # SMS service
        if sms_service.is_available():
            self.stdout.write("  ✓ SMS service: Available (Twilio configured)")
        else:
            self.stdout.write("  ⚠ SMS service: Not configured (Twilio credentials missing)")
        
        # Push service
        if push_service.is_available():
            self.stdout.write("  ✓ Push service: Available (VAPID keys configured)")
        else:
            self.stdout.write("  ⚠ Push service: Not configured (VAPID keys missing)")

    def _test_notification_creation(self, user):
        """Test basic notification creation."""
        self.stdout.write("\n📝 Testing Notification Creation:")
        
        # Create test notifications
        notifications = notification_service.create_notification(
            user=user,
            notification_type='booking_confirmed',
            title='Test Booking Confirmation',
            message='This is a test booking confirmation notification.',
            priority='medium'
        )
        
        self.stdout.write(f"  ✓ Created {len(notifications)} notifications")
        
        for notification in notifications:
            self.stdout.write(f"    - {notification.delivery_method}: {notification.title}")

    def _test_email_notifications(self, user):
        """Test email notification sending."""
        self.stdout.write("\n📧 Testing Email Notifications:")
        
        # Create email notification
        notifications = notification_service.create_notification(
            user=user,
            notification_type='booking_reminder',
            title='Test Email Notification',
            message='This is a test email notification.',
            priority='low'
        )
        
        # Try to send pending notifications
        try:
            sent_count = notification_service.send_pending_notifications()
            self.stdout.write(f"  ✓ Processed {sent_count} notifications")
        except Exception as e:
            self.stdout.write(f"  ✗ Email sending failed: {e}")

    def _test_sms_notifications(self, user):
        """Test SMS notification functionality."""
        self.stdout.write("\n📱 Testing SMS Notifications:")
        
        # Check if user has phone number
        if hasattr(user, 'userprofile') and user.userprofile.phone:
            phone = user.userprofile.phone
            self.stdout.write(f"  📞 User phone: {phone}")
            
            # Validate phone number
            is_valid = sms_service.validate_phone_number(phone)
            self.stdout.write(f"  📋 Phone validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
            
            if sms_service.is_available():
                # Create SMS notification preference
                NotificationPreference.objects.update_or_create(
                    user=user,
                    notification_type='booking_confirmed',
                    delivery_method='sms',
                    defaults={'is_enabled': True}
                )
                
                # Create and send SMS notification
                notifications = notification_service.create_notification(
                    user=user,
                    notification_type='booking_confirmed',
                    title='Test SMS Notification',
                    message='This is a test SMS notification from Aperture Booking.',
                    priority='medium'
                )
                
                sms_notifications = [n for n in notifications if n.delivery_method == 'sms']
                self.stdout.write(f"  ✓ Created {len(sms_notifications)} SMS notification(s)")
            else:
                self.stdout.write("  ⚠ SMS service not configured - skipping SMS test")
        else:
            self.stdout.write("  ⚠ User has no phone number - skipping SMS test")

    def _test_push_notifications(self, user):
        """Test push notification functionality."""
        self.stdout.write("\n🔔 Testing Push Notifications:")
        
        if push_service.is_available():
            # Create mock push subscription
            subscription = PushSubscription.objects.create(
                user=user,
                endpoint='https://fcm.googleapis.com/fcm/send/test-endpoint',
                p256dh_key='test-p256dh-key-for-testing-purposes-only',
                auth_key='test-auth-key',
                user_agent='Test Browser'
            )
            
            self.stdout.write(f"  ✓ Created test push subscription for {user.username}")
            
            # Create push notification preference
            NotificationPreference.objects.update_or_create(
                user=user,
                notification_type='booking_confirmed',
                delivery_method='push',
                defaults={'is_enabled': True}
            )
            
            # Get VAPID public key
            public_key = push_service.get_vapid_public_key()
            if public_key:
                self.stdout.write(f"  🔑 VAPID public key: {public_key[:20]}...")
            
            self.stdout.write("  ✓ Push notification system configured")
            
            # Clean up test subscription
            subscription.delete()
        else:
            self.stdout.write("  ⚠ Push service not configured - skipping push test")

    def _test_notification_preferences(self, user):
        """Test notification preferences system."""
        self.stdout.write("\n⚙️ Testing Notification Preferences:")
        
        # Get default preferences
        defaults = notification_service.default_preferences
        self.stdout.write(f"  📋 Default notification types: {len(defaults)}")
        
        # Create some test preferences
        test_prefs = [
            ('booking_confirmed', 'email', True),
            ('booking_confirmed', 'sms', False),
            ('booking_reminder', 'push', True),
            ('maintenance_alert', 'in_app', True),
        ]
        
        for notif_type, delivery, enabled in test_prefs:
            pref, created = NotificationPreference.objects.update_or_create(
                user=user,
                notification_type=notif_type,
                delivery_method=delivery,
                defaults={'is_enabled': enabled}
            )
            
            action = "Created" if created else "Updated"
            status = "enabled" if enabled else "disabled"
            self.stdout.write(f"  {action} preference: {notif_type} via {delivery} ({status})")
        
        # Test preference retrieval
        prefs = notification_service._get_user_preferences(user, 'booking_confirmed')
        self.stdout.write(f"  ✓ Retrieved preferences for booking_confirmed: {prefs}")

    def _cleanup_test_data(self, user):
        """Clean up test data."""
        # Remove test notifications
        from booking.models import Notification
        Notification.objects.filter(user=user, title__startswith='Test').delete()
        
        # Remove test preferences
        NotificationPreference.objects.filter(user=user).delete()
        
        # Remove test push subscriptions
        PushSubscription.objects.filter(user=user).delete()
        
        self.stdout.write("  🧹 Cleaned up test data")