"""
Context processors for the Aperture Booking.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperture-booking.org/commercial
"""

from django.db.models import Q
from .models import Notification, AccessRequest, TrainingRequest


def has_model(model_name):
    """Check if a model exists to avoid import errors."""
    try:
        from . import models
        return hasattr(models, model_name)
    except:
        return False


def notification_context(request):
    """Add notification counts to template context."""
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'pending_access_requests_count': 0,
            'pending_training_requests_count': 0,
            'total_notifications_count': 0,
        }
    
    try:
        # Count unread in-app notifications
        unread_notifications = Notification.objects.filter(
            user=request.user,
            delivery_method='in_app',
            status__in=['pending', 'sent']
        ).count()
        
        # Count pending access requests for lab admins/technicians
        pending_access_requests = 0
        if hasattr(request.user, 'userprofile') and \
           (request.user.userprofile.role in ['technician', 'sysadmin'] or \
            request.user.groups.filter(name='Lab Admin').exists()):
            pending_access_requests = AccessRequest.objects.filter(
                status='pending'
            ).count()
        
        # Count pending training requests for lab admins/technicians
        pending_training_requests = 0
        if hasattr(request.user, 'userprofile') and \
           (request.user.userprofile.role in ['technician', 'sysadmin'] or \
            request.user.groups.filter(name='Lab Admin').exists()):
            if has_model('TrainingRequest'):
                pending_training_requests = TrainingRequest.objects.filter(
                    status='pending'
                ).count()
        
        # Total actionable items
        total_notifications = (
            unread_notifications + 
            pending_access_requests + 
            pending_training_requests
        )
        
        return {
            'unread_notifications_count': unread_notifications,
            'pending_access_requests_count': pending_access_requests,
            'pending_training_requests_count': pending_training_requests,
            'total_notifications_count': total_notifications,
        }
        
    except Exception as e:
        # Fallback in case of any errors
        return {
            'unread_notifications_count': 0,
            'pending_access_requests_count': 0,
            'pending_training_requests_count': 0,
            'total_notifications_count': 0,
        }