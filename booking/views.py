# booking/views.py
"""
API views for the Aperture Booking.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperture-booking.org/commercial
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, LoginView
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import (
    AboutPage, UserProfile, Resource, Booking, ApprovalRule, Maintenance, EmailVerificationToken, 
    PasswordResetToken, BookingTemplate, Notification, NotificationPreference, WaitingListEntry, 
    Faculty, College, Department, ResourceAccess, AccessRequest, TrainingRequest,
    ResourceResponsible, RiskAssessment, UserRiskAssessment, TrainingCourse, 
    ResourceTrainingRequirement, UserTraining
)
from .forms import (
    UserRegistrationForm, UserProfileForm, CustomPasswordResetForm, CustomSetPasswordForm, 
    BookingForm, RecurringBookingForm, BookingTemplateForm, CreateBookingFromTemplateForm, 
    SaveAsTemplateForm, AccessRequestForm, AccessRequestReviewForm, RiskAssessmentForm, 
    UserRiskAssessmentForm, TrainingCourseForm, UserTrainingEnrollForm, ResourceResponsibleForm,
    ResourceForm, AboutPageEditForm
)
from .recurring import RecurringBookingGenerator, RecurringBookingManager
from .conflicts import ConflictDetector, ConflictResolver, ConflictManager
from .serializers import (
    UserProfileSerializer, ResourceSerializer, BookingSerializer,
    ApprovalRuleSerializer, MaintenanceSerializer, WaitingListEntrySerializer,
    ResourceResponsibleSerializer, RiskAssessmentSerializer, UserRiskAssessmentSerializer,
    TrainingCourseSerializer, ResourceTrainingRequirementSerializer, UserTrainingSerializer,
    AccessRequestDetailSerializer
)
# from .notifications import notification_service  # TODO: Implement notification service
# from .waiting_list import waiting_list_service  # TODO: Implement waiting list service  
# from .checkin_service import checkin_service  # TODO: Implement checkin service


class IsOwnerOrManagerPermission(permissions.BasePermission):
    """Custom permission to only allow owners or managers to edit bookings."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to owner or lab managers
        if hasattr(request.user, 'userprofile'):
            user_profile = request.user.userprofile
            return (obj.user == request.user or 
                   user_profile.role in ['technician', 'sysadmin'])
        
        return obj.user == request.user


class IsManagerPermission(permissions.BasePermission):
    """Custom permission for managers only."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if hasattr(request.user, 'userprofile'):
            user_profile = request.user.userprofile
            return user_profile.role in ['technician', 'sysadmin']
        
        return False


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user profiles."""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        try:
            user_profile = user.userprofile
            if user_profile.role in ['technician', 'sysadmin']:
                return UserProfile.objects.all()
            else:
                # Regular users can only see their own profile and group members
                return UserProfile.objects.filter(
                    Q(user=user) | Q(group=user_profile.group)
                )
        except UserProfile.DoesNotExist:
            return UserProfile.objects.filter(user=user)


class ResourceViewSet(viewsets.ModelViewSet):
    """ViewSet for resources."""
    queryset = Resource.objects.filter(is_active=True)
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['resource_type', 'requires_induction', 'required_training_level']
    
    def get_permissions(self):
        """Different permissions for different actions."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only technicians and sysadmins can modify resources
            self.permission_classes = [permissions.IsAuthenticated, IsManagerPermission]
        return super().get_permissions()
    
    def get_queryset(self):
        """Filter resources based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by resource_type if provided
        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get resources available for the current user."""
        try:
            user_profile = request.user.userprofile
            available_resources = []
            
            for resource in self.get_queryset():
                if resource.is_available_for_user(user_profile):
                    available_resources.append(resource)
            
            serializer = self.get_serializer(available_resources, many=True)
            return Response(serializer.data)
        
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User profile not found"}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for bookings with full CRUD operations."""
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrManagerPermission]
    
    def get_queryset(self):
        """Filter bookings based on user role and query parameters."""
        user = self.request.user
        queryset = Booking.objects.select_related('resource', 'user', 'approved_by')
        
        try:
            user_profile = user.userprofile
            
            # Filter by user role
            if user_profile.role in ['technician', 'sysadmin']:
                # Managers can see all bookings
                pass
            elif user_profile.role == 'lecturer':
                # Lecturers can see their bookings and their group's bookings
                queryset = queryset.filter(
                    Q(user=user) | 
                    Q(user__userprofile__group=user_profile.group, shared_with_group=True)
                )
            else:
                # Students/researchers see their own bookings and shared group bookings
                queryset = queryset.filter(
                    Q(user=user) |
                    Q(user__userprofile__group=user_profile.group, shared_with_group=True) |
                    Q(attendees=user)
                ).distinct()
        
        except UserProfile.DoesNotExist:
            queryset = queryset.filter(user=user)
        
        # Filter by query parameters
        resource_id = self.request.query_params.get('resource')
        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)
        
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            try:
                # Parse date strings and make them timezone-aware
                start_datetime = timezone.make_aware(
                    datetime.strptime(start_date, '%Y-%m-%d')
                )
                end_datetime = timezone.make_aware(
                    datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                )
                queryset = queryset.filter(
                    start_time__gte=start_datetime,
                    end_time__lte=end_datetime
                )
            except ValueError:
                # If date parsing fails, skip filtering
                pass
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('start_time')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a booking."""
        booking = self.get_object()
        user_profile = request.user.userprofile
        
        if user_profile.role not in ['technician', 'sysadmin']:
            return Response(
                {"error": "Permission denied"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'pending':
            return Response(
                {"error": "Only pending bookings can be approved"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'approved'
        booking.approved_by = request.user
        booking.approved_at = timezone.now()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a booking."""
        booking = self.get_object()
        user_profile = request.user.userprofile
        
        if user_profile.role not in ['technician', 'sysadmin']:
            return Response(
                {"error": "Permission denied"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status != 'pending':
            return Response(
                {"error": "Only pending bookings can be rejected"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'rejected'
        booking.approved_by = request.user
        booking.approved_at = timezone.now()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking."""
        booking = self.get_object()
        
        if not booking.can_be_cancelled:
            return Response(
                {"error": "This booking cannot be cancelled"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Get bookings in calendar event format."""
        queryset = self.get_queryset()
        
        # Handle FullCalendar date range parameters
        start_param = request.query_params.get('start')
        end_param = request.query_params.get('end')
        
        if start_param and end_param:
            try:
                # Parse ISO format dates from FullCalendar
                start_date = timezone.datetime.fromisoformat(start_param.replace('Z', '+00:00'))
                end_date = timezone.datetime.fromisoformat(end_param.replace('Z', '+00:00'))
                
                # Make timezone-aware if needed
                if timezone.is_naive(start_date):
                    start_date = timezone.make_aware(start_date)
                if timezone.is_naive(end_date):
                    end_date = timezone.make_aware(end_date)
                
                # Filter bookings by date range
                queryset = queryset.filter(
                    start_time__lt=end_date,
                    end_time__gt=start_date
                )
            except (ValueError, TypeError) as e:
                # If date parsing fails, just log and continue without filtering
                print(f"Calendar date parsing error: {e}")
        
        # Convert to FullCalendar event format
        events = []
        for booking in queryset:
            color = {
                'pending': '#ffc107',
                'approved': '#28a745',
                'rejected': '#dc3545',
                'cancelled': '#6c757d',
                'completed': '#17a2b8'
            }.get(booking.status, '#007bff')
            
            events.append({
                'id': booking.id,
                'title': booking.title,
                'start': booking.start_time.isoformat(),
                'end': booking.end_time.isoformat(),
                'backgroundColor': color,
                'borderColor': color,
                'extendedProps': {
                    'booking_id': booking.id,
                    'resource': booking.resource.name,
                    'resource_id': booking.resource.id,
                    'user': booking.user.get_full_name(),
                    'status': booking.status,
                    'description': booking.description,
                    'shared_with_group': booking.shared_with_group,
                    'is_recurring': booking.is_recurring,
                }
            })
        
        return Response(events)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get booking statistics."""
        user_profile = request.user.userprofile
        
        if user_profile.role not in ['technician', 'sysadmin']:
            return Response(
                {"error": "Permission denied"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Date range for statistics
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        bookings = Booking.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        stats = {
            'total_bookings': bookings.count(),
            'approved_bookings': bookings.filter(status='approved').count(),
            'pending_bookings': bookings.filter(status='pending').count(),
            'rejected_bookings': bookings.filter(status='rejected').count(),
            'cancelled_bookings': bookings.filter(status='cancelled').count(),
            'bookings_by_resource': list(
                bookings.values('resource__name')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
            'bookings_by_user': list(
                bookings.values('user__username', 'user__first_name', 'user__last_name')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
            'bookings_by_group': list(
                bookings.values('user__userprofile__group')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
        }
        
        return Response(stats)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to cancel booking instead of deleting it."""
        booking = self.get_object()
        
        # Check if booking can be cancelled
        if not booking.can_be_cancelled:
            return Response(
                {"error": "This booking cannot be cancelled"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as cancelled instead of deleting
        booking.status = 'cancelled'
        booking.save()
        
        # Create booking history entry
        from .models import BookingHistory
        BookingHistory.objects.create(
            booking=booking,
            user=request.user,
            action='cancelled',
            notes='Cancelled via API'
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def add_prerequisite(self, request, pk=None):
        """Add a prerequisite booking dependency."""
        booking = self.get_object()
        user_profile = request.user.userprofile
        
        # Check permissions - only owner or managers can add dependencies
        if booking.user != request.user and user_profile.role not in ['technician', 'sysadmin']:
            return Response(
                {"error": "Permission denied"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        prerequisite_id = request.data.get('prerequisite_id')
        dependency_type = request.data.get('dependency_type', 'sequential')
        conditions = request.data.get('conditions', {})
        
        if not prerequisite_id:
            return Response(
                {"error": "prerequisite_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            prerequisite_booking = Booking.objects.get(id=prerequisite_id)
            
            # Validate that user has access to prerequisite booking
            if (prerequisite_booking.user != request.user and 
                user_profile.role not in ['technician', 'sysadmin']):
                return Response(
                    {"error": "You don't have access to the specified prerequisite booking"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            booking.add_prerequisite(prerequisite_booking, dependency_type, conditions)
            
            serializer = self.get_serializer(booking)
            return Response(serializer.data)
            
        except Booking.DoesNotExist:
            return Response(
                {"error": "Prerequisite booking not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def remove_prerequisite(self, request, pk=None):
        """Remove a prerequisite booking dependency."""
        booking = self.get_object()
        user_profile = request.user.userprofile
        
        # Check permissions
        if booking.user != request.user and user_profile.role not in ['technician', 'sysadmin']:
            return Response(
                {"error": "Permission denied"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        prerequisite_id = request.data.get('prerequisite_id')
        
        if not prerequisite_id:
            return Response(
                {"error": "prerequisite_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            prerequisite_booking = Booking.objects.get(id=prerequisite_id)
            booking.prerequisite_bookings.remove(prerequisite_booking)
            
            serializer = self.get_serializer(booking)
            return Response(serializer.data)
            
        except Booking.DoesNotExist:
            return Response(
                {"error": "Prerequisite booking not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def dependencies(self, request, pk=None):
        """Get booking dependency information."""
        booking = self.get_object()
        
        prerequisites = []
        for prereq in booking.prerequisite_bookings.all():
            prerequisites.append({
                'id': prereq.id,
                'title': prereq.title,
                'resource': prereq.resource.name,
                'start_time': prereq.start_time,
                'end_time': prereq.end_time,
                'status': prereq.status,
                'user': prereq.user.get_full_name()
            })
        
        dependents = []
        for dependent in booking.dependent_bookings.all():
            dependents.append({
                'id': dependent.id,
                'title': dependent.title,
                'resource': dependent.resource.name,
                'start_time': dependent.start_time,
                'end_time': dependent.end_time,
                'status': dependent.status,
                'user': dependent.user.get_full_name(),
                'dependency_type': dependent.dependency_type
            })
        
        return Response({
            'can_start': booking.can_start,
            'dependency_status': booking.dependency_status,
            'dependency_type': booking.dependency_type,
            'dependency_conditions': booking.dependency_conditions,
            'prerequisites': prerequisites,
            'dependents': dependents,
            'blocking_dependencies': [
                {
                    'id': dep.id,
                    'title': dep.title,
                    'status': dep.status,
                    'resource': dep.resource.name
                }
                for dep in booking.get_blocking_dependencies()
            ]
        })
    
    @action(detail=False, methods=['post'])
    def join_waiting_list(self, request):
        """Join waiting list when booking conflicts exist."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            # Check if validation failed due to conflicts
            errors = serializer.errors
            if any('conflict' in str(error).lower() for error in errors.values()):
                # Offer to join waiting list
                resource_id = request.data.get('resource_id')
                start_time = request.data.get('start_time')
                end_time = request.data.get('end_time')
                title = request.data.get('title', 'Booking Request')
                description = request.data.get('description', '')
                
                if resource_id and start_time and end_time:
                    waiting_entry = WaitingListEntry.objects.create(
                        user=request.user,
                        resource_id=resource_id,
                        desired_start_time=start_time,
                        desired_end_time=end_time,
                        title=title,
                        description=description,
                        flexible_start=request.data.get('flexible_start', False),
                        flexible_duration=request.data.get('flexible_duration', False),
                        auto_book=request.data.get('auto_book', False)
                    )
                    
                    return Response({
                        'booking_failed': True,
                        'reason': 'time_conflict',
                        'waiting_list_entry': WaitingListEntrySerializer(waiting_entry).data,
                        'message': 'Booking conflicts detected. You have been added to the waiting list.'
                    }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # If no conflicts, create booking normally
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ApprovalRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for approval rules (read-only for now)."""
    queryset = ApprovalRule.objects.filter(is_active=True)
    serializer_class = ApprovalRuleSerializer
    permission_classes = [permissions.IsAuthenticated]


class MaintenanceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for maintenance schedules."""
    queryset = Maintenance.objects.all()
    serializer_class = MaintenanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter maintenance by date range if provided."""
        queryset = super().get_queryset()
        
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date and end_date:
            try:
                # Parse date strings and make them timezone-aware
                start_datetime = timezone.make_aware(
                    datetime.strptime(start_date, '%Y-%m-%d')
                )
                end_datetime = timezone.make_aware(
                    datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                )
                queryset = queryset.filter(
                    start_time__gte=start_datetime,
                    end_time__lte=end_datetime
                )
            except ValueError:
                # If date parsing fails, skip filtering
                pass
        
        return queryset.order_by('start_time')
    
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Get maintenance periods formatted for FullCalendar."""
        # Get date range from query params
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        resource_id = request.query_params.get('resource')
        
        # Base queryset
        maintenance_periods = self.get_queryset()
        
        # Filter by date range if provided
        if start and end:
            try:
                start_date = timezone.make_aware(datetime.fromisoformat(start.replace('Z', '+00:00')))
                end_date = timezone.make_aware(datetime.fromisoformat(end.replace('Z', '+00:00')))
                maintenance_periods = maintenance_periods.filter(
                    end_time__gte=start_date,
                    start_time__lte=end_date
                )
            except ValueError:
                pass
        
        # Filter by resource if specified
        if resource_id:
            try:
                maintenance_periods = maintenance_periods.filter(resource_id=resource_id)
            except ValueError:
                pass
        
        # Format for FullCalendar
        events = []
        for maintenance in maintenance_periods:
            # Color coding based on maintenance type and status
            now = timezone.now()
            if maintenance.start_time > now:
                # Scheduled maintenance - blue
                color = '#007bff'
            elif maintenance.end_time < now:
                # Completed maintenance - gray
                color = '#6c757d'
            else:
                # Active maintenance - orange
                color = '#fd7e14'
            
            # Override color based on maintenance type
            type_colors = {
                'preventive': '#28a745',  # green
                'corrective': '#dc3545',  # red
                'inspection': '#17a2b8',  # cyan
                'calibration': '#6f42c1',  # purple
                'repair': '#ffc107',      # yellow
                'upgrade': '#6c757d'      # gray
            }
            color = type_colors.get(maintenance.maintenance_type, color)
            
            events.append({
                'id': f'maintenance-{maintenance.id}',
                'title': f'🔧 {maintenance.title}',
                'start': maintenance.start_time.isoformat(),
                'end': maintenance.end_time.isoformat(),
                'backgroundColor': color,
                'borderColor': color,
                'display': 'block',
                'classNames': ['maintenance-event'],
                'extendedProps': {
                    'type': 'maintenance',
                    'resource': maintenance.resource.name,
                    'maintenance_type': maintenance.maintenance_type,
                    'description': maintenance.description,
                    'blocks_booking': maintenance.blocks_booking,
                    'is_recurring': maintenance.is_recurring,
                    'created_by': maintenance.created_by.get_full_name() or maintenance.created_by.username,
                }
            })
        
        return Response(events)


# Template views
def register_view(request):
    """User registration view."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Get the verification token for development mode
            from .models import EmailVerificationToken
            from django.conf import settings
            token = EmailVerificationToken.objects.filter(user=user, is_used=False).first()
            
            if settings.DEBUG and token:
                # In development mode, show the verification URL
                verification_url = request.build_absolute_uri(f'/verify-email/{token.token}/')
                messages.success(
                    request, 
                    f'<strong>Registration Successful!</strong><br><br>'
                    f'<i class="bi bi-info-circle"></i> <strong>Important:</strong> Your account has been created but is currently <strong>inactive</strong>.<br><br>'
                    f'<i class="bi bi-envelope"></i> <strong>Next Steps:</strong><br>'
                    f'1. Check your email ({user.email}) for a verification link<br>'
                    f'2. Click the verification link to activate your account<br>'
                    f'3. Return here to log in<br><br>'
                    f'<i class="bi bi-gear"></i> <strong>Development Mode:</strong> You can verify directly using this link: <a href="{verification_url}" target="_blank" class="btn btn-sm btn-outline-primary">Verify Account Now</a><br><br>'
                    f'<small class="text-muted"><i class="bi bi-clock"></i> You cannot log in until your email is verified.</small>'
                )
            else:
                messages.success(
                    request, 
                    f'<strong>Registration Successful!</strong><br><br>'
                    f'<i class="bi bi-info-circle"></i> <strong>Important:</strong> Your account has been created but is currently <strong>inactive</strong>.<br><br>'
                    f'<i class="bi bi-envelope"></i> <strong>Next Steps:</strong><br>'
                    f'1. Check your email ({user.email}) for a verification link<br>'
                    f'2. Click the verification link to activate your account<br>'
                    f'3. Return here to log in<br><br>'
                    f'<small class="text-muted"><i class="bi bi-clock"></i> You cannot log in until your email is verified. If you don\'t see the email, check your spam folder or <a href="/resend-verification/">request a new verification email</a>.</small>'
                )
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
        # Clear any existing messages when showing the registration form
        list(messages.get_messages(request))
    
    return render(request, 'registration/register.html', {'form': form})


def verify_email_view(request, token):
    """Email verification view."""
    verification_token = get_object_or_404(EmailVerificationToken, token=token)
    
    if verification_token.is_used:
        messages.warning(request, 'This verification link has already been used.')
        return redirect('login')
    
    if verification_token.is_expired():
        messages.error(request, 'This verification link has expired. Please contact support.')
        return redirect('login')
    
    # Activate user and mark email as verified
    user = verification_token.user
    user.is_active = True
    user.save()
    
    profile = user.userprofile
    profile.email_verified = True
    profile.save()
    
    verification_token.is_used = True
    verification_token.save()
    
    messages.success(request, 'Email verified successfully! You can now log in.')
    return redirect('login')


def resend_verification_view(request):
    """Resend verification email view."""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(email=email, is_active=False)
            
            # Check if there's an existing unused token
            try:
                token = EmailVerificationToken.objects.get(user=user, is_used=False)
                if token.is_expired():
                    token.delete()
                    token = EmailVerificationToken.objects.create(user=user)
            except EmailVerificationToken.DoesNotExist:
                token = EmailVerificationToken.objects.create(user=user)
            
            # Send verification email
            form = UserRegistrationForm()
            form.send_verification_email(user, token)
            
            messages.success(request, 'Verification email has been resent. Please check your inbox.')
            
        except User.DoesNotExist:
            messages.error(request, 'No unverified account found with this email address.')
    
    return render(request, 'registration/resend_verification.html')


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view using our token system."""
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    success_url = '/password-reset-done/'
    
    def form_valid(self, form):
        form.save(request=self.request)
        return redirect(self.success_url)


def password_reset_confirm_view(request, token):
    """Custom password reset confirmation view."""
    reset_token = get_object_or_404(PasswordResetToken, token=token)
    
    if reset_token.is_used:
        messages.error(request, 'This password reset link has already been used.')
        return render(request, 'registration/password_reset_confirm.html', {'validlink': False})
    
    if reset_token.is_expired():
        messages.error(request, 'This password reset link has expired.')
        return render(request, 'registration/password_reset_confirm.html', {'validlink': False})
    
    if request.method == 'POST':
        form = CustomSetPasswordForm(reset_token.user, request.POST)
        if form.is_valid():
            form.save()
            reset_token.is_used = True
            reset_token.save()
            messages.success(request, 'Your password has been set successfully.')
            return redirect('password_reset_complete')
    else:
        form = CustomSetPasswordForm(reset_token.user)
    
    return render(request, 'registration/password_reset_confirm.html', {
        'form': form,
        'validlink': True,
    })


def password_reset_done_view(request):
    """Password reset done view."""
    return render(request, 'registration/password_reset_done.html')


def password_reset_complete_view(request):
    """Password reset complete view."""
    return render(request, 'registration/password_reset_complete.html')


@login_required
def create_booking_view(request):
    """Create a new booking."""
    conflicts_detected = False
    conflicting_bookings = []
    
    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user)
        
        # Check if this is a conflict override attempt
        override_conflicts = request.POST.get('override_conflicts') == 'true'
        
        # Debug logging
        import logging
        logger = logging.getLogger('booking')
        logger.debug(f"Create booking POST data: {request.POST}")
        logger.debug(f"User: {request.user}, is_superuser: {request.user.is_superuser}, is_staff: {request.user.is_staff}")
        logger.debug(f"Override conflicts: {override_conflicts}")
        
        if form.is_valid():
            try:
                booking = form.save(commit=False)
                booking.user = request.user
                
                # Handle conflict override if requested
                if override_conflicts and form.cleaned_data.get('override_conflicts'):
                    override_message = form.cleaned_data.get('override_message', '')
                    conflicts = form.get_conflicts()
                    
                    # Process each conflicting booking
                    from .notifications import BookingNotifications
                    notification_service = BookingNotifications()
                    
                    for conflicting_booking in conflicts:
                        notification_service.booking_overridden(
                            conflicting_booking, 
                            booking, 
                            override_message
                        )
                
                booking.save()
                messages.success(request, f'Booking "{booking.title}" created successfully.')
                return redirect('booking:booking_detail', pk=booking.pk)
                
            except Exception as e:
                messages.error(request, f'Error creating booking: {str(e)}')
        else:
            # Check if form validation failed due to conflicts
            if hasattr(form, '_conflicts'):
                conflicts_detected = True
                conflicting_bookings = form._conflicts
            
            # Add error messages (excluding conflict messages for privileged users)
            for field, errors in form.errors.items():
                for error in errors:
                    # Skip conflict error messages for privileged users as we handle them specially
                    if not (conflicts_detected and form._can_override_conflicts() and 'conflict detected' in error.lower()):
                        messages.error(request, f'{field.replace("_", " ").title()}: {error}')
    else:
        form = BookingForm(user=request.user)
    
    context = {
        'form': form,
        'conflicts_detected': conflicts_detected,
        'conflicting_bookings': conflicting_bookings,
        'can_override': hasattr(form, '_can_override_conflicts') and form._can_override_conflicts(),
    }
    
    return render(request, 'booking/create_booking.html', context)


@login_required
def booking_detail_view(request, pk):
    """View booking details."""
    booking = get_object_or_404(Booking, pk=pk)
    
    # Check permissions
    try:
        user_profile = request.user.userprofile
        if (booking.user != request.user and 
            user_profile.role not in ['technician', 'sysadmin'] and
            not booking.shared_with_group):
            messages.error(request, 'You do not have permission to view this booking.')
            return redirect('booking:dashboard')
    except UserProfile.DoesNotExist:
        if booking.user != request.user:
            messages.error(request, 'You do not have permission to view this booking.')
            return redirect('booking:dashboard')
    
    # Handle POST requests (e.g., cancellation)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'cancel':
            # Check if user can cancel this booking
            if (booking.user == request.user or 
                (hasattr(request.user, 'userprofile') and 
                 request.user.userprofile.role in ['technician', 'sysadmin'])):
                
                if booking.can_be_cancelled:
                    booking.status = 'cancelled'
                    booking.save()
                    messages.success(request, f'Booking "{booking.title}" has been cancelled.')
                    return redirect('booking:dashboard')
                else:
                    messages.error(request, 'This booking cannot be cancelled.')
            else:
                messages.error(request, 'You do not have permission to cancel this booking.')
    
    # Get recurring series if applicable
    recurring_series = None
    if booking.is_recurring:
        try:
            recurring_series = RecurringBookingManager.get_recurring_series(booking)
        except:
            recurring_series = None
    
    return render(request, 'booking/booking_detail.html', {
        'booking': booking,
        'recurring_series': recurring_series,
    })


@login_required
def create_recurring_booking_view(request, booking_pk):
    """Create recurring bookings based on an existing booking."""
    base_booking = get_object_or_404(Booking, pk=booking_pk, user=request.user)
    
    # Check if user can create recurring bookings
    try:
        user_profile = request.user.userprofile
        if not user_profile.can_create_recurring:
            messages.error(request, 'You do not have permission to create recurring bookings.')
            return redirect('booking:booking_detail', pk=booking_pk)
    except UserProfile.DoesNotExist:
        messages.error(request, 'You do not have permission to create recurring bookings.')
        return redirect('booking:booking_detail', pk=booking_pk)
    
    if request.method == 'POST':
        form = RecurringBookingForm(request.POST)
        if form.is_valid():
            try:
                pattern = form.create_pattern()
                generator = RecurringBookingGenerator(base_booking, pattern)
                
                skip_conflicts = form.cleaned_data.get('skip_conflicts', True)
                result = generator.create_recurring_bookings(skip_conflicts=skip_conflicts)
                
                # Update the base booking to mark it as recurring
                base_booking.is_recurring = True
                base_booking.recurring_pattern = pattern.to_dict()
                base_booking.save()
                
                success_msg = f"Created {result['total_created']} recurring bookings."
                if result['skipped_dates']:
                    success_msg += f" Skipped {len(result['skipped_dates'])} dates due to conflicts."
                
                messages.success(request, success_msg)
                return redirect('booking:booking_detail', pk=booking_pk)
                
            except Exception as e:
                messages.error(request, f'Error creating recurring bookings: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RecurringBookingForm()
    
    return render(request, 'booking/create_recurring.html', {
        'form': form,
        'base_booking': base_booking,
    })


@login_required
def cancel_recurring_series_view(request, booking_pk):
    """Cancel an entire recurring series."""
    booking = get_object_or_404(Booking, pk=booking_pk)
    
    # Check permissions
    try:
        user_profile = request.user.userprofile
        if (booking.user != request.user and 
            user_profile.role not in ['technician', 'sysadmin']):
            messages.error(request, 'You do not have permission to cancel this booking series.')
            return redirect('booking:booking_detail', pk=booking_pk)
    except UserProfile.DoesNotExist:
        if booking.user != request.user:
            messages.error(request, 'You do not have permission to cancel this booking series.')
            return redirect('booking:booking_detail', pk=booking_pk)
    
    if not booking.is_recurring:
        messages.error(request, 'This is not a recurring booking.')
        return redirect('booking:booking_detail', pk=booking_pk)
    
    if request.method == 'POST':
        cancel_future_only = request.POST.get('cancel_future_only') == 'on'
        
        try:
            cancelled_count = RecurringBookingManager.cancel_recurring_series(
                booking, cancel_future_only=cancel_future_only
            )
            
            if cancel_future_only:
                messages.success(request, f'Cancelled {cancelled_count} future bookings in the series.')
            else:
                messages.success(request, f'Cancelled {cancelled_count} bookings in the entire series.')
                
            return redirect('booking:dashboard')
            
        except Exception as e:
            messages.error(request, f'Error cancelling recurring series: {str(e)}')
    
    # Get series info for confirmation
    series = RecurringBookingManager.get_recurring_series(booking)
    future_count = sum(1 for b in series if b.start_time > timezone.now() and b.can_be_cancelled)
    total_count = sum(1 for b in series if b.can_be_cancelled)
    
    return render(request, 'booking/cancel_recurring.html', {
        'booking': booking,
        'series': series,
        'future_count': future_count,
        'total_count': total_count,
    })


@login_required
def conflict_detection_view(request):
    """Conflict detection and resolution interface."""
    # Check if user has permission to view conflicts
    try:
        user_profile = request.user.userprofile
        if user_profile.role not in ['technician', 'sysadmin']:
            messages.error(request, 'You do not have permission to access conflict management.')
            return redirect('booking:dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'You do not have permission to access conflict management.')
        return redirect('booking:dashboard')
    
    # Get filter parameters
    resource_id = request.GET.get('resource')
    days_ahead = int(request.GET.get('days', 30))
    
    conflicts_data = {}
    selected_resource = None
    
    if resource_id:
        try:
            selected_resource = Resource.objects.get(pk=resource_id)
            conflicts_data = ConflictManager.get_resource_conflicts_report(
                selected_resource, days_ahead
            )
        except Resource.DoesNotExist:
            messages.error(request, 'Selected resource not found.')
    
    # Get all resources for filter dropdown
    resources = Resource.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'booking/conflicts.html', {
        'conflicts_data': conflicts_data,
        'selected_resource': selected_resource,
        'resources': resources,
        'days_ahead': days_ahead,
    })


@login_required
def resolve_conflict_view(request, conflict_type, id1, id2):
    """Resolve a specific conflict between two bookings."""
    try:
        user_profile = request.user.userprofile
        if user_profile.role not in ['technician', 'sysadmin']:
            messages.error(request, 'You do not have permission to resolve conflicts.')
            return redirect('booking:dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'You do not have permission to resolve conflicts.')
        return redirect('booking:dashboard')
    
    try:
        booking1 = Booking.objects.get(pk=id1)
        booking2 = Booking.objects.get(pk=id2)
    except Booking.DoesNotExist:
        messages.error(request, 'One or more bookings not found.')
        return redirect('booking:conflicts')
    
    # Verify there's actually a conflict
    conflicts = ConflictDetector.check_booking_conflicts(booking1, exclude_booking_ids=[])
    conflict = None
    for c in conflicts:
        if c.booking2.pk == booking2.pk:
            conflict = c
            break
    
    if not conflict:
        messages.warning(request, 'No conflict detected between these bookings.')
        return redirect('booking:conflicts')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'cancel_booking1':
            if booking1.can_be_cancelled:
                booking1.status = 'cancelled'
                booking1.save()
                messages.success(request, f'Cancelled booking: {booking1.title}')
            else:
                messages.error(request, f'Cannot cancel booking: {booking1.title}')
                
        elif action == 'cancel_booking2':
            if booking2.can_be_cancelled:
                booking2.status = 'cancelled'
                booking2.save()
                messages.success(request, f'Cancelled booking: {booking2.title}')
            else:
                messages.error(request, f'Cannot cancel booking: {booking2.title}')
                
        elif action == 'reschedule_booking1':
            new_start = request.POST.get('new_start_time')
            new_end = request.POST.get('new_end_time')
            if new_start and new_end:
                try:
                    booking1.start_time = timezone.datetime.fromisoformat(new_start.replace('T', ' '))
                    booking1.end_time = timezone.datetime.fromisoformat(new_end.replace('T', ' '))
                    booking1.save()
                    messages.success(request, f'Rescheduled booking: {booking1.title}')
                except Exception as e:
                    messages.error(request, f'Error rescheduling booking: {str(e)}')
            else:
                messages.error(request, 'Invalid time values provided.')
                
        elif action == 'reschedule_booking2':
            new_start = request.POST.get('new_start_time')
            new_end = request.POST.get('new_end_time')
            if new_start and new_end:
                try:
                    booking2.start_time = timezone.datetime.fromisoformat(new_start.replace('T', ' '))
                    booking2.end_time = timezone.datetime.fromisoformat(new_end.replace('T', ' '))
                    booking2.save()
                    messages.success(request, f'Rescheduled booking: {booking2.title}')
                except Exception as e:
                    messages.error(request, f'Error rescheduling booking: {str(e)}')
            else:
                messages.error(request, 'Invalid time values provided.')
        
        return redirect('booking:conflicts')
    
    # Generate suggestions for resolution
    try:
        user1_profile = booking1.user.userprofile
        user2_profile = booking2.user.userprofile
        
        suggestions1 = ConflictResolver.suggest_alternative_times(booking1, [conflict])
        suggestions2 = ConflictResolver.suggest_alternative_times(booking2, [conflict])
        
        alt_resources1 = ConflictResolver.suggest_alternative_resources(booking1, user1_profile)
        alt_resources2 = ConflictResolver.suggest_alternative_resources(booking2, user2_profile)
    except:
        suggestions1 = suggestions2 = []
        alt_resources1 = alt_resources2 = []
    
    return render(request, 'booking/resolve_conflict.html', {
        'conflict': conflict,
        'booking1': booking1,
        'booking2': booking2,
        'suggestions1': suggestions1,
        'suggestions2': suggestions2,
        'alt_resources1': alt_resources1,
        'alt_resources2': alt_resources2,
    })


@login_required 
def bulk_resolve_conflicts_view(request):
    """Bulk resolve multiple conflicts."""
    try:
        user_profile = request.user.userprofile
        if user_profile.role not in ['technician', 'sysadmin']:
            messages.error(request, 'You do not have permission to resolve conflicts.')
            return redirect('booking:dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'You do not have permission to resolve conflicts.')
        return redirect('booking:dashboard')
    
    if request.method == 'POST':
        resource_id = request.POST.get('resource_id')
        strategy = request.POST.get('strategy', 'suggest_alternatives')
        conflict_ids = request.POST.getlist('conflict_ids')
        
        try:
            resource = Resource.objects.get(pk=resource_id)
            
            # Get conflicts for the resource
            conflicts_data = ConflictManager.get_resource_conflicts_report(resource, 30)
            all_conflicts = []
            
            # Convert conflict data back to conflict objects for processing
            for conflict_dict in conflicts_data['all_conflicts']:
                try:
                    booking1 = Booking.objects.get(pk=conflict_dict['booking1']['id'])
                    booking2 = Booking.objects.get(pk=conflict_dict['booking2']['id'])
                    from .conflicts import BookingConflict
                    conflict_obj = BookingConflict(booking1, booking2)
                    all_conflicts.append(conflict_obj)
                except Booking.DoesNotExist:
                    continue
            
            # Filter to selected conflicts if specified
            if conflict_ids:
                selected_conflicts = []
                for conflict in all_conflicts:
                    conflict_id = f"{conflict.booking1.pk}_{conflict.booking2.pk}"
                    if conflict_id in conflict_ids:
                        selected_conflicts.append(conflict)
                all_conflicts = selected_conflicts
            
            # Bulk resolve
            if all_conflicts:
                resolution_results = ConflictManager.bulk_resolve_conflicts(
                    all_conflicts, strategy
                )
                
                messages.success(
                    request, 
                    f"Processed {len(all_conflicts)} conflicts. "
                    f"{resolution_results['summary']['auto_resolvable']} can be auto-resolved, "
                    f"{resolution_results['summary']['manual_review']} need manual review."
                )
            else:
                messages.warning(request, 'No conflicts selected for resolution.')
                
        except Resource.DoesNotExist:
            messages.error(request, 'Resource not found.')
        except Exception as e:
            messages.error(request, f'Error processing conflicts: {str(e)}')
    
    return redirect('booking:conflicts')


@login_required
def notifications_list(request):
    """Display user's notifications."""
    notifications = notification_service.get_user_notifications(
        request.user, 
        limit=50, 
        unread_only=False
    )
    
    unread_count = len([n for n in notifications if n.status in ['pending', 'sent']])
    
    return render(request, 'booking/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
def notification_preferences(request):
    """Display and update user's notification preferences."""
    if request.method == 'POST':
        # Update preferences
        for key, value in request.POST.items():
            if key.startswith('pref_'):
                # Parse preference key: pref_{notification_type}_{delivery_method}
                parts = key.replace('pref_', '').split('_')
                if len(parts) >= 2:
                    notification_type = '_'.join(parts[:-1])
                    delivery_method = parts[-1]
                    
                    preference, created = NotificationPreference.objects.get_or_create(
                        user=request.user,
                        notification_type=notification_type,
                        delivery_method=delivery_method,
                        defaults={'is_enabled': value == 'on'}
                    )
                    
                    if not created:
                        preference.is_enabled = value == 'on'
                        preference.save()
        
        messages.success(request, 'Notification preferences updated successfully.')
        return redirect('booking:notification_preferences')
    
    # Get current preferences
    preferences = {}
    user_prefs = NotificationPreference.objects.filter(user=request.user)
    
    for pref in user_prefs:
        key = f"{pref.notification_type}_{pref.delivery_method}"
        preferences[key] = pref.is_enabled
    
    # Available notification types and delivery methods
    notification_types = NotificationPreference.NOTIFICATION_TYPES
    delivery_methods = NotificationPreference.DELIVERY_METHODS
    
    return render(request, 'booking/notification_preferences.html', {
        'preferences': preferences,
        'notification_types': notification_types,
        'delivery_methods': delivery_methods,
    })


# API Views for notifications
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for user notifications."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
            delivery_method='in_app'
        ).select_related('booking', 'resource', 'maintenance').order_by('-created_at')
    
    def get_serializer_class(self):
        # Simple serializer for notifications
        from rest_framework import serializers
        
        class NotificationSerializer(serializers.ModelSerializer):
            class Meta:
                model = Notification
                fields = [
                    'id', 'notification_type', 'title', 'message', 'priority',
                    'status', 'created_at', 'sent_at', 'read_at', 'metadata'
                ]
                read_only_fields = fields
        
        return NotificationSerializer
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = self.get_queryset().filter(status__in=['pending', 'sent']).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        notification_ids = list(
            self.get_queryset().filter(status__in=['pending', 'sent']).values_list('id', flat=True)
        )
        
        updated_count = notification_service.mark_notifications_as_read(
            request.user, notification_ids
        )
        
        return Response({
            'marked_read': updated_count,
            'message': f'Marked {updated_count} notifications as read'
        })
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a specific notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        
        return Response({
            'status': 'read',
            'message': 'Notification marked as read'
        })


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """API viewset for notification preferences."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class NotificationPreferenceSerializer(serializers.ModelSerializer):
            class Meta:
                model = NotificationPreference
                fields = [
                    'id', 'notification_type', 'delivery_method', 
                    'is_enabled', 'frequency', 'created_at', 'updated_at'
                ]
                read_only_fields = ['id', 'created_at', 'updated_at']
        
        return NotificationPreferenceSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Waiting List Views
@login_required
def waiting_list_view(request):
    """Display user's waiting list entries."""
    entries = waiting_list_service.get_user_waiting_list_entries(request.user)
    
    # Get pending notifications
    notifications = WaitingListNotification.objects.filter(
        waiting_list_entry__user=request.user,
        user_response='pending'
    ).select_related('waiting_list_entry__resource').order_by('-sent_at')
    
    return render(request, 'booking/waiting_list.html', {
        'waiting_list_entries': entries,
        'pending_notifications': notifications,
    })


@login_required
def join_waiting_list(request, resource_id):
    """Join waiting list for a resource."""
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user can access this resource
    try:
        user_profile = request.user.userprofile
        if not resource.is_available_for_user(user_profile):
            messages.error(request, f'You do not meet the requirements to book {resource.name}.')
            return redirect('booking:calendar')
    except:
        messages.error(request, 'User profile not found.')
        return redirect('booking:calendar')
    
    if request.method == 'POST':
        try:
            # Get form data
            preferred_start = timezone.datetime.fromisoformat(request.POST['preferred_start_time'])
            preferred_end = timezone.datetime.fromisoformat(request.POST['preferred_end_time'])
            
            # Optional parameters
            options = {
                'min_duration_minutes': int(request.POST.get('min_duration_minutes', 60)),
                'max_duration_minutes': int(request.POST.get('max_duration_minutes', 240)),
                'flexible_start_time': request.POST.get('flexible_start_time') == 'on',
                'flexible_duration': request.POST.get('flexible_duration') == 'on',
                'auto_book': request.POST.get('auto_book') == 'on',
                'priority': request.POST.get('priority', 'normal'),
                'notes': request.POST.get('notes', ''),
            }
            
            # Add to waiting list
            entry = waiting_list_service.add_to_waiting_list(
                user=request.user,
                resource=resource,
                preferred_start=preferred_start,
                preferred_end=preferred_end,
                **options
            )
            
            messages.success(request, f'Successfully added to waiting list for {resource.name}!')
            return redirect('booking:waiting_list')
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Failed to join waiting list: {str(e)}')
    
    # Pre-fill with requested time if available
    requested_start = request.GET.get('start_time')
    requested_end = request.GET.get('end_time')
    
    return render(request, 'booking/join_waiting_list.html', {
        'resource': resource,
        'requested_start_time': requested_start,
        'requested_end_time': requested_end,
    })


@login_required
def leave_waiting_list(request, entry_id):
    """Leave waiting list."""
    success, message = waiting_list_service.cancel_waiting_list_entry(entry_id, request.user)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('booking:waiting_list')


@login_required
def respond_to_availability(request, notification_id):
    """Respond to availability notification."""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accept':
            success, message = waiting_list_service.accept_availability_offer(notification_id, request.user)
        elif action == 'decline':
            success, message = waiting_list_service.decline_availability_offer(notification_id, request.user)
        else:
            success, message = False, 'Invalid action.'
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
    
    return redirect('booking:waiting_list')


# API Views for Waiting List
class WaitingListEntryViewSet(viewsets.ModelViewSet):
    """API viewset for waiting list entries."""
    serializer_class = WaitingListEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get waiting list entries based on user permissions."""
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.role in ['technician', 'sysadmin']:
            return WaitingListEntry.objects.all().select_related('user', 'resource', 'resulting_booking')
        else:
            return WaitingListEntry.objects.filter(user=self.request.user).select_related('resource', 'resulting_booking')
    
    def perform_create(self, serializer):
        """Create waiting list entry for current user."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel waiting list entry."""
        entry = self.get_object()
        
        if entry.user != request.user and request.user.userprofile.role not in ['technician', 'sysadmin']:
            return Response({'error': 'Permission denied'}, status=403)
        
        if entry.status not in ['waiting', 'notified']:
            return Response({'error': 'Cannot cancel entry in current status'}, status=400)
        
        entry.cancel_waiting()
        return Response({'status': 'success', 'message': 'Waiting list entry cancelled'})
    
    @action(detail=True, methods=['post'])
    def book_slot(self, request, pk=None):
        """Book an available slot from waiting list entry."""
        entry = self.get_object()
        
        if entry.user != request.user:
            return Response({'error': 'Permission denied'}, status=403)
        
        if entry.status != 'notified':
            return Response({'error': 'No available slot to book'}, status=400)
        
        # Get slot details from request
        slot_data = request.data.get('slot')
        if not slot_data:
            return Response({'error': 'Slot data required'}, status=400)
        
        try:
            booking = entry.create_booking_from_slot(slot_data)
            return Response({
                'status': 'success',
                'message': 'Booking created successfully',
                'booking_id': booking.id
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['get'])
    def find_opportunities(self, request):
        """Find available booking opportunities for waiting list entries."""
        if request.user.userprofile.role not in ['technician', 'sysadmin']:
            return Response({'error': 'Permission denied'}, status=403)
        
        resource_id = request.query_params.get('resource')
        resource = None
        
        if resource_id:
            try:
                resource = Resource.objects.get(id=resource_id)
            except Resource.DoesNotExist:
                return Response({'error': 'Resource not found'}, status=404)
        
        opportunities = WaitingListEntry.find_opportunities(resource)
        
        # Format the response
        formatted_opportunities = []
        for opportunity in opportunities:
            entry_data = WaitingListEntrySerializer(opportunity['entry']).data
            formatted_opportunities.append({
                'entry': entry_data,
                'available_slots': opportunity['slots']
            })
        
        return Response(formatted_opportunities)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get waiting list statistics."""
        if request.user.userprofile.role not in ['technician', 'sysadmin']:
            return Response({'error': 'Permission denied'}, status=403)
        
        resource_id = request.query_params.get('resource')
        queryset = self.get_queryset()
        
        if resource_id:
            try:
                resource = Resource.objects.get(id=resource_id)
                queryset = queryset.filter(resource=resource)
            except Resource.DoesNotExist:
                return Response({'error': 'Resource not found'}, status=404)
        
        # Calculate statistics
        stats = {
            'total_entries': queryset.count(),
            'waiting': queryset.filter(status='waiting').count(),
            'notified': queryset.filter(status='notified').count(),
            'booked': queryset.filter(status='booked').count(),
            'expired': queryset.filter(status='expired').count(),
            'cancelled': queryset.filter(status='cancelled').count(),
            'by_priority': {
                'urgent': queryset.filter(priority='urgent').count(),
                'high': queryset.filter(priority='high').count(),
                'normal': queryset.filter(priority='normal').count(),
                'low': queryset.filter(priority='low').count(),
            },
            'auto_book_enabled': queryset.filter(auto_book=True).count()
        }
        
        return Response(stats)


# WaitingListNotificationViewSet removed - using Notification model instead


@login_required
def resources_list_view(request):
    """View to display all available resources with access control, grouped by resource type."""
    resources = Resource.objects.filter(is_active=True).order_by('resource_type', 'name')
    
    # Add access information for each resource
    for resource in resources:
        resource.user_has_access_result = resource.user_has_access(request.user)
        resource.can_view_calendar_result = resource.can_user_view_calendar(request.user)
        
        # Check if user has pending access request
        resource.has_pending_request = AccessRequest.objects.filter(
            resource=resource,
            user=request.user,
            status='pending'
        ).exists()
        
        # Check if user has pending training request
        resource.has_pending_training = TrainingRequest.objects.filter(
            resource=resource,
            user=request.user,
            status__in=['pending', 'scheduled']
        ).exists()
    
    # Group resources by type - only include types that have at least one resource
    from itertools import groupby
    resources_by_type = {}
    for resource_type, group in groupby(resources, key=lambda x: x.resource_type):
        resource_list = list(group)
        if resource_list:  # Only include resource types that have available resources
            # Get the human-readable name for the resource type
            type_display = dict(Resource.RESOURCE_TYPES).get(resource_type, resource_type.title())
            resources_by_type[resource_type] = {
                'type_display': type_display,
                'resources': resource_list,
                'count': len(resource_list)
            }
    
    return render(request, 'booking/resources_list.html', {
        'resources': resources,  # Keep for backward compatibility
        'resources_by_type': resources_by_type,
        'user': request.user,
    })


@login_required
def resource_detail_view(request, resource_id):
    """View to show resource details and calendar or access request form."""
    resource = get_object_or_404(Resource, id=resource_id, is_active=True)
    
    # Check user's access
    user_has_access = resource.user_has_access(request.user)
    can_view_calendar = resource.can_user_view_calendar(request.user)
    
    # Check if user has pending access request
    has_pending_request = AccessRequest.objects.filter(
        resource=resource,
        user=request.user,
        status='pending'
    ).exists()
    
    # Check if user has pending training request
    has_pending_training = TrainingRequest.objects.filter(
        resource=resource,
        user=request.user,
        status__in=['pending', 'scheduled']
    ).exists()
    
    # If user can view calendar, show calendar view
    if can_view_calendar:
        return render(request, 'booking/resource_detail.html', {
            'resource': resource,
            'user_has_access': user_has_access,
            'can_view_calendar': can_view_calendar,
            'has_pending_training': has_pending_training,
            'show_calendar': True,
        })
    
    # Otherwise show access request form
    return render(request, 'booking/resource_detail.html', {
        'resource': resource,
        'user_has_access': user_has_access,
        'can_view_calendar': can_view_calendar,
        'has_pending_request': has_pending_request,
        'has_pending_training': has_pending_training,
        'show_calendar': False,
    })


@login_required
def request_resource_access_view(request, resource_id):
    """Handle resource access requests."""
    resource = get_object_or_404(Resource, id=resource_id, is_active=True)
    
    # Check if user already has access or pending request
    if resource.user_has_access(request.user):
        messages.info(request, 'You already have access to this resource.')
        return redirect('booking:resource_detail', resource_id=resource.id)
    
    if AccessRequest.objects.filter(resource=resource, user=request.user, status='pending').exists():
        messages.info(request, 'You already have a pending access request for this resource.')
        return redirect('booking:resource_detail', resource_id=resource.id)
    
    # Check if user has pending training request
    if TrainingRequest.objects.filter(resource=resource, user=request.user, status__in=['pending', 'scheduled']).exists():
        messages.info(request, 'You already have a pending training request for this resource.')
        return redirect('booking:resource_detail', resource_id=resource.id)
    
    if request.method == 'POST':
        access_type = request.POST.get('access_type', 'book')
        justification = request.POST.get('justification', '').strip()
        requested_duration_days = request.POST.get('requested_duration_days')
        has_training = request.POST.get('has_training', '')
        
        if not justification:
            messages.error(request, 'Please provide a justification for your access request.')
            return redirect('booking:request_resource_access', resource_id=resource.id)
        
        # Check if user meets training requirements
        user_profile = request.user.userprofile
        needs_training = resource.required_training_level > user_profile.training_level
        
        if needs_training:
            if has_training == 'yes':
                # User claims to have training but system shows they don't
                messages.warning(request, 
                    f'Our records show you have training level {user_profile.training_level}, but {resource.name} requires level {resource.required_training_level}. '
                    'Training information will be sent to you to update your qualifications.')
                
                # Create training request for verification
                training_request, created = TrainingRequest.objects.get_or_create(
                    user=request.user,
                    resource=resource,
                    status__in=['pending', 'scheduled'],
                    defaults={
                        'requested_level': resource.required_training_level,
                        'current_level': user_profile.training_level,
                        'justification': f"Training verification needed for access to {resource.name}. User claims training completion. Original request: {justification}",
                        'status': 'pending'
                    }
                )
                
            elif has_training == 'no':
                # User acknowledges they need training
                messages.info(request, 'Training information will be sent to you as this resource requires additional training.')
                
                # Create training request
                training_request, created = TrainingRequest.objects.get_or_create(
                    user=request.user,
                    resource=resource,
                    status__in=['pending', 'scheduled'],
                    defaults={
                        'requested_level': resource.required_training_level,
                        'current_level': user_profile.training_level,
                        'justification': f"Training needed for access to {resource.name}. Original request: {justification}",
                        'status': 'pending'
                    }
                )
            
            if 'training_request' in locals():
                if created:
                    messages.success(request, f'Training request for {resource.name} has been submitted. You will be contacted with training details.')
                    
                    # Send notifications
                    try:
                        from .notifications import training_request_notifications
                        training_request_notifications.training_request_submitted(training_request)
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Failed to send training request submission notification: {e}")
                else:
                    messages.info(request, f'You already have a pending training request for {resource.name}.')
            
            return redirect('booking:resource_detail', resource_id=resource.id)
        
        # User has sufficient training, proceed with access request
        access_request = AccessRequest.objects.create(
            resource=resource,
            user=request.user,
            access_type=access_type,
            justification=justification,
            requested_duration_days=int(requested_duration_days) if requested_duration_days else None
        )
        
        messages.success(request, f'Access request for {resource.name} has been submitted successfully.')
        
        # Send notifications
        try:
            from .notifications import access_request_notifications
            access_request_notifications.access_request_submitted(access_request)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send access request submission notification: {e}")
        
        return redirect('booking:resource_detail', resource_id=resource.id)
    
    return render(request, 'booking/request_access.html', {
        'resource': resource,
    })


@login_required
def notification_preferences_view(request):
    """Notification preferences management view."""
    from .models import NotificationPreference
    
    # Get all notification types
    notification_types = NotificationPreference.NOTIFICATION_TYPES
    delivery_methods = NotificationPreference.DELIVERY_METHODS
    frequency_choices = [
        ('immediate', 'Immediate'),
        ('daily_digest', 'Daily Digest'),
        ('weekly_digest', 'Weekly Digest'),
    ]
    
    if request.method == 'POST':
        # Process preference updates
        updated_count = 0
        
        for notification_type, _ in notification_types:
            for delivery_method, _ in delivery_methods:
                # Get form field names
                enabled_field = f"{notification_type}_{delivery_method}_enabled"
                frequency_field = f"{notification_type}_{delivery_method}_frequency"
                
                is_enabled = request.POST.get(enabled_field) == 'on'
                frequency = request.POST.get(frequency_field, 'immediate')
                
                # Update or create preference
                preference, created = NotificationPreference.objects.update_or_create(
                    user=request.user,
                    notification_type=notification_type,
                    delivery_method=delivery_method,
                    defaults={
                        'is_enabled': is_enabled,
                        'frequency': frequency
                    }
                )
                
                if created or preference.is_enabled != is_enabled:
                    updated_count += 1
        
        messages.success(request, f'Updated {updated_count} notification preferences.')
        return redirect('booking:notification_preferences')
    
    # Get current preferences
    current_preferences = {}
    user_prefs = NotificationPreference.objects.filter(user=request.user)
    
    for pref in user_prefs:
        key = f"{pref.notification_type}_{pref.delivery_method}"
        current_preferences[key] = {
            'enabled': pref.is_enabled,
            'frequency': pref.frequency
        }
    
    # Add default values for missing preferences
    from .notifications import notification_service
    for notification_type, _ in notification_types:
        for delivery_method, _ in delivery_methods:
            key = f"{notification_type}_{delivery_method}"
            if key not in current_preferences:
                defaults = notification_service.default_preferences.get(notification_type, {})
                current_preferences[key] = {
                    'enabled': defaults.get(delivery_method, False),
                    'frequency': defaults.get('frequency', 'immediate')
                }
    
    return render(request, 'booking/notification_preferences.html', {
        'notification_types': notification_types,
        'delivery_methods': delivery_methods,
        'frequency_choices': frequency_choices,
        'current_preferences': current_preferences,
    })


@login_required
def profile_view(request):
    """User profile management view."""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile, current_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=profile, current_user=request.user)
    
    return render(request, 'registration/profile.html', {'form': form, 'profile': profile})


@login_required
def calendar_view(request):
    """Main calendar view."""
    return render(request, 'booking/calendar.html', {
        'user': request.user,
        'resources': Resource.objects.filter(is_active=True),
    })


@login_required
def dashboard_view(request):
    """User dashboard view."""
    user_bookings = Booking.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'booking/dashboard.html', {
        'user': request.user,
        'recent_bookings': user_bookings,
    })


@login_required
def template_list_view(request):
    """List user's booking templates."""
    # Get templates accessible to the user
    accessible_templates = []
    for template in BookingTemplate.objects.all():
        if template.is_accessible_by_user(request.user):
            accessible_templates.append(template.pk)
    
    templates = BookingTemplate.objects.filter(
        pk__in=accessible_templates
    ).order_by('-use_count', 'name')
    
    user_templates = templates.filter(user=request.user)
    public_templates = templates.filter(is_public=True).exclude(user=request.user)
    group_templates = templates.exclude(user=request.user, is_public=True)
    
    return render(request, 'booking/templates.html', {
        'user_templates': user_templates,
        'public_templates': public_templates,
        'group_templates': group_templates,
    })


@login_required
def template_create_view(request):
    """Create a new booking template."""
    if request.method == 'POST':
        form = BookingTemplateForm(request.POST, user=request.user)
        if form.is_valid():
            template = form.save(commit=False)
            template.user = request.user
            template.save()
            messages.success(request, f'Template "{template.name}" created successfully.')
            return redirect('booking:templates')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookingTemplateForm(user=request.user)
    
    return render(request, 'booking/template_form.html', {
        'form': form,
        'title': 'Create Template',
    })


@login_required
def template_edit_view(request, pk):
    """Edit a booking template."""
    template = get_object_or_404(BookingTemplate, pk=pk)
    
    # Check if user can edit this template
    if template.user != request.user:
        messages.error(request, 'You can only edit your own templates.')
        return redirect('booking:templates')
    
    if request.method == 'POST':
        form = BookingTemplateForm(request.POST, instance=template, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Template "{template.name}" updated successfully.')
            return redirect('booking:templates')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookingTemplateForm(instance=template, user=request.user)
    
    return render(request, 'booking/template_form.html', {
        'form': form,
        'template': template,
        'title': 'Edit Template',
    })


@login_required
def template_delete_view(request, pk):
    """Delete a booking template."""
    template = get_object_or_404(BookingTemplate, pk=pk)
    
    # Check if user can delete this template
    if template.user != request.user:
        messages.error(request, 'You can only delete your own templates.')
        return redirect('booking:templates')
    
    if request.method == 'POST':
        template_name = template.name
        template.delete()
        messages.success(request, f'Template "{template_name}" deleted successfully.')
        return redirect('booking:templates')
    
    return render(request, 'booking/template_confirm_delete.html', {
        'template': template,
    })


@login_required
def create_booking_from_template_view(request):
    """Create a booking from a template."""
    if request.method == 'POST':
        form = CreateBookingFromTemplateForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                booking = form.create_booking()
                booking.save()
                messages.success(request, f'Booking "{booking.title}" created from template.')
                return redirect('booking:booking_detail', pk=booking.pk)
            except Exception as e:
                messages.error(request, f'Error creating booking: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CreateBookingFromTemplateForm(user=request.user)
    
    return render(request, 'booking/create_from_template.html', {
        'form': form,
    })


@login_required
def save_booking_as_template_view(request, booking_pk):
    """Save an existing booking as a template."""
    booking = get_object_or_404(Booking, pk=booking_pk)
    
    # Check if user owns the booking
    if booking.user != request.user:
        messages.error(request, 'You can only save your own bookings as templates.')
        return redirect('booking:booking_detail', pk=booking_pk)
    
    if request.method == 'POST':
        form = SaveAsTemplateForm(request.POST)
        if form.is_valid():
            try:
                template = booking.save_as_template(
                    template_name=form.cleaned_data['name'],
                    template_description=form.cleaned_data['description'],
                    is_public=form.cleaned_data['is_public']
                )
                messages.success(request, f'Booking saved as template "{template.name}".')
                return redirect('booking:templates')
            except Exception as e:
                messages.error(request, f'Error saving template: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-fill form with booking data
        initial_data = {
            'name': f"{booking.title} Template",
            'description': f"Template based on booking: {booking.title}",
        }
        form = SaveAsTemplateForm(initial=initial_data)
    
    return render(request, 'booking/save_as_template.html', {
        'form': form,
        'booking': booking,
    })


@login_required
def bulk_booking_operations_view(request):
    """Bulk operations on multiple bookings."""
    if request.method == 'POST':
        action = request.POST.get('action')
        booking_ids = request.POST.getlist('booking_ids')
        
        if not booking_ids:
            messages.error(request, 'No bookings selected.')
            return redirect('booking:dashboard')
        
        try:
            user_profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            messages.error(request, 'User profile not found.')
            return redirect('booking:dashboard')
        
        # Get bookings that user has permission to modify
        if user_profile.role in ['technician', 'sysadmin']:
            bookings = Booking.objects.filter(pk__in=booking_ids)
        else:
            bookings = Booking.objects.filter(pk__in=booking_ids, user=request.user)
        
        if not bookings.exists():
            messages.error(request, 'No bookings found or you do not have permission to modify them.')
            return redirect('booking:dashboard')
        
        success_count = 0
        error_count = 0
        errors = []
        
        if action == 'cancel':
            for booking in bookings:
                if booking.can_be_cancelled:
                    booking.status = 'cancelled'
                    booking.save()
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f'{booking.title} - Cannot be cancelled')
            
            if success_count > 0:
                messages.success(request, f'Successfully cancelled {success_count} booking(s).')
            if error_count > 0:
                messages.warning(request, f'{error_count} booking(s) could not be cancelled: {", ".join(errors[:3])}')
        
        elif action == 'approve' and user_profile.role in ['technician', 'sysadmin']:
            for booking in bookings:
                if booking.status == 'pending':
                    booking.status = 'approved'
                    booking.approved_by = request.user
                    booking.approved_at = timezone.now()
                    booking.save()
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f'{booking.title} - Not pending')
            
            if success_count > 0:
                messages.success(request, f'Successfully approved {success_count} booking(s).')
            if error_count > 0:
                messages.warning(request, f'{error_count} booking(s) could not be approved: {", ".join(errors[:3])}')
        
        elif action == 'reject' and user_profile.role in ['technician', 'sysadmin']:
            for booking in bookings:
                if booking.status == 'pending':
                    booking.status = 'rejected'
                    booking.save()
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f'{booking.title} - Not pending')
            
            if success_count > 0:
                messages.success(request, f'Successfully rejected {success_count} booking(s).')
            if error_count > 0:
                messages.warning(request, f'{error_count} booking(s) could not be rejected: {", ".join(errors[:3])}')
        
        else:
            messages.error(request, 'Invalid action or insufficient permissions.')
    
    return redirect('booking:dashboard')


@login_required
def booking_management_view(request):
    """Management interface for bookings with bulk operations."""
    try:
        user_profile = request.user.userprofile
        if user_profile.role not in ['technician', 'sysadmin']:
            messages.error(request, 'You do not have permission to access booking management.')
            return redirect('booking:dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'You do not have permission to access booking management.')
        return redirect('booking:dashboard')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    resource_filter = request.GET.get('resource', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    bookings = Booking.objects.select_related('resource', 'user', 'approved_by').order_by('-created_at')
    
    # Apply filters
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    if resource_filter:
        bookings = bookings.filter(resource_id=resource_filter)
    
    if user_filter:
        bookings = bookings.filter(
            Q(user__username__icontains=user_filter) |
            Q(user__first_name__icontains=user_filter) |
            Q(user__last_name__icontains=user_filter)
        )
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            bookings = bookings.filter(start_time__date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            bookings = bookings.filter(start_time__date__lte=to_date)
        except ValueError:
            pass
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(bookings, 25)  # Show 25 bookings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get resources for filter dropdown
    resources = Resource.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'resources': resources,
        'status_filter': status_filter,
        'resource_filter': resource_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': Booking.STATUS_CHOICES,
    }
    
    return render(request, 'booking/booking_management.html', context)


@login_required
def my_bookings_view(request):
    """User's own bookings with bulk operations."""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    resource_filter = request.GET.get('resource', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset - user's own bookings
    bookings = Booking.objects.filter(user=request.user).select_related('resource', 'approved_by').order_by('-created_at')
    
    # Apply filters
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    if resource_filter:
        bookings = bookings.filter(resource_id=resource_filter)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            bookings = bookings.filter(start_time__date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            bookings = bookings.filter(start_time__date__lte=to_date)
        except ValueError:
            pass
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(bookings, 20)  # Show 20 bookings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get resources for filter dropdown (only ones user has access to)
    try:
        user_profile = request.user.userprofile
        available_resources = []
        for resource in Resource.objects.filter(is_active=True):
            if resource.is_available_for_user(user_profile):
                available_resources.append(resource.pk)
        resources = Resource.objects.filter(pk__in=available_resources).order_by('name')
    except:
        resources = Resource.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'resources': resources,
        'status_filter': status_filter,
        'resource_filter': resource_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': Booking.STATUS_CHOICES,
    }
    
    return render(request, 'booking/my_bookings.html', context)


@login_required
def edit_booking_view(request, pk):
    """Edit an existing booking."""
    booking = get_object_or_404(Booking, pk=pk)
    
    # Check permissions
    try:
        user_profile = request.user.userprofile
        can_edit = (booking.user == request.user or 
                   user_profile.role in ['technician', 'sysadmin'])
    except UserProfile.DoesNotExist:
        can_edit = booking.user == request.user
    
    if not can_edit:
        messages.error(request, 'You do not have permission to edit this booking.')
        return redirect('booking:booking_detail', pk=pk)
    
    # Check if booking can be edited
    if booking.status not in ['pending', 'approved']:
        messages.error(request, 'Only pending or approved bookings can be edited.')
        return redirect('booking:booking_detail', pk=pk)
    
    # Don't allow editing past bookings
    if booking.start_time < timezone.now():
        messages.error(request, 'Cannot edit bookings that have already started.')
        return redirect('booking:booking_detail', pk=pk)
    
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking, user=request.user)
        if form.is_valid():
            try:
                updated_booking = form.save(commit=False)
                
                # If the booking was approved and user made changes, set it back to pending
                if (booking.status == 'approved' and 
                    booking.user == request.user and 
                    user_profile.role not in ['technician', 'sysadmin']):
                    
                    # Check if any important fields changed
                    important_changes = (
                        updated_booking.resource != booking.resource or
                        updated_booking.start_time != booking.start_time or
                        updated_booking.end_time != booking.end_time
                    )
                    
                    if important_changes:
                        updated_booking.status = 'pending'
                        updated_booking.approved_by = None
                        updated_booking.approved_at = None
                        messages.info(request, 'Booking updated and set to pending approval due to time/resource changes.')
                    else:
                        messages.success(request, 'Booking updated successfully.')
                else:
                    messages.success(request, 'Booking updated successfully.')
                
                updated_booking.save()
                return redirect('booking:booking_detail', pk=updated_booking.pk)
                
            except Exception as e:
                messages.error(request, f'Error updating booking: {str(e)}')
        else:
            # Add detailed error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = BookingForm(instance=booking, user=request.user)
    
    return render(request, 'booking/edit_booking.html', {
        'form': form,
        'booking': booking,
    })


@login_required
def cancel_booking_view(request, pk):
    """Cancel a booking with confirmation."""
    booking = get_object_or_404(Booking, pk=pk)
    
    # Check permissions
    try:
        user_profile = request.user.userprofile
        can_cancel = (booking.user == request.user or 
                     user_profile.role in ['technician', 'sysadmin'])
    except UserProfile.DoesNotExist:
        can_cancel = booking.user == request.user
    
    if not can_cancel:
        messages.error(request, 'You do not have permission to cancel this booking.')
        return redirect('booking:booking_detail', pk=pk)
    
    if not booking.can_be_cancelled:
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('booking:booking_detail', pk=pk)
    
    if request.method == 'POST':
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, f'Booking "{booking.title}" has been cancelled.')
            
            # Redirect based on user role
            if hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['technician', 'sysadmin']:
                return redirect('booking:manage_bookings')
            else:
                return redirect('booking:my_bookings')
        else:
            return redirect('booking:booking_detail', pk=pk)
    
    return render(request, 'booking/cancel_booking.html', {
        'booking': booking,
    })


@login_required
def duplicate_booking_view(request, pk):
    """Create a new booking based on an existing one."""
    original_booking = get_object_or_404(Booking, pk=pk)
    
    # Check if user has access to view the original booking
    try:
        user_profile = request.user.userprofile
        can_access = (
            original_booking.user == request.user or 
            user_profile.role in ['technician', 'sysadmin'] or
            (original_booking.shared_with_group and 
             user_profile.group == original_booking.user.userprofile.group)
        )
    except UserProfile.DoesNotExist:
        can_access = original_booking.user == request.user
    
    if not can_access:
        messages.error(request, 'You do not have permission to duplicate this booking.')
        return redirect('booking:dashboard')
    
    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                new_booking = form.save(commit=False)
                new_booking.user = request.user
                new_booking.status = 'pending'
                new_booking.save()
                
                messages.success(request, f'Booking "{new_booking.title}" created successfully.')
                return redirect('booking:booking_detail', pk=new_booking.pk)
            except Exception as e:
                messages.error(request, f'Error creating booking: {str(e)}')
        else:
            # Add detailed error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Pre-populate form with original booking data, but adjust times
        initial_data = {
            'resource': original_booking.resource,
            'title': f"Copy of {original_booking.title}",
            'description': original_booking.description,
            'shared_with_group': original_booking.shared_with_group,
            'notes': original_booking.notes,
        }
        
        # Set start time to tomorrow at the same time
        tomorrow = timezone.now() + timedelta(days=1)
        duration = original_booking.end_time - original_booking.start_time
        
        start_time = tomorrow.replace(
            hour=original_booking.start_time.hour,
            minute=original_booking.start_time.minute,
            second=0,
            microsecond=0
        )
        end_time = start_time + duration
        
        initial_data['start_time'] = start_time
        initial_data['end_time'] = end_time
        
        form = BookingForm(initial=initial_data, user=request.user)
    
    return render(request, 'booking/duplicate_booking.html', {
        'form': form,
        'original_booking': original_booking,
    })


# Check-in/Check-out Views
@login_required
def checkin_view(request, booking_id):
    """Check in to a booking."""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user can check in
    try:
        user_profile = request.user.userprofile
        can_checkin = (
            booking.user == request.user or
            booking.attendees.filter(id=request.user.id).exists() or
            user_profile.role in ['technician', 'sysadmin']
        )
    except UserProfile.DoesNotExist:
        can_checkin = booking.user == request.user
    
    if not can_checkin:
        messages.error(request, 'You do not have permission to check in to this booking.')
        return redirect('booking:booking_detail', pk=booking_id)
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        
        # Get client info for tracking
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        success, message = checkin_service.check_in_booking(
            booking_id=booking_id,
            user=request.user,
            notes=notes,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect('booking:booking_detail', pk=booking_id)
    
    return render(request, 'booking/checkin.html', {
        'booking': booking,
    })


@login_required
def checkout_view(request, booking_id):
    """Check out of a booking."""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user can check out
    try:
        user_profile = request.user.userprofile
        can_checkout = (
            booking.user == request.user or
            booking.attendees.filter(id=request.user.id).exists() or
            user_profile.role in ['technician', 'sysadmin']
        )
    except UserProfile.DoesNotExist:
        can_checkout = booking.user == request.user
    
    if not can_checkout:
        messages.error(request, 'You do not have permission to check out of this booking.')
        return redirect('booking:booking_detail', pk=booking_id)
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        
        # Get client info for tracking
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        success, message = checkin_service.check_out_booking(
            booking_id=booking_id,
            user=request.user,
            notes=notes,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect('booking:booking_detail', pk=booking_id)
    
    return render(request, 'booking/checkout.html', {
        'booking': booking,
    })


@login_required
def checkin_status_view(request):
    """View current check-in status for user's bookings."""
    # Get user's bookings for today
    today = timezone.now().date()
    user_bookings = Booking.objects.filter(
        Q(user=request.user) | Q(attendees=request.user),
        start_time__date=today,
        status__in=['approved', 'confirmed']
    ).select_related('resource').distinct().order_by('start_time')
    
    # Get currently checked in bookings
    checked_in_bookings = Booking.objects.filter(
        Q(user=request.user) | Q(attendees=request.user),
        checked_in_at__isnull=False,
        checked_out_at__isnull=True
    ).select_related('resource').distinct()
    
    return render(request, 'booking/checkin_status.html', {
        'user_bookings': user_bookings,
        'checked_in_bookings': checked_in_bookings,
        'today': today,
    })


@login_required
def resource_checkin_status_view(request, resource_id):
    """View current check-in status for a specific resource (managers only)."""
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user has permission
    try:
        user_profile = request.user.userprofile
        if user_profile.role not in ['technician', 'sysadmin']:
            messages.error(request, 'You do not have permission to view resource check-in status.')
            return redirect('booking:calendar')
    except UserProfile.DoesNotExist:
        messages.error(request, 'You do not have permission to view resource check-in status.')
        return redirect('booking:calendar')
    
    # Get current check-ins for this resource
    current_checkins = checkin_service.get_current_checkins(resource)
    
    # Get today's bookings for this resource
    today = timezone.now().date()
    today_bookings = Booking.objects.filter(
        resource=resource,
        start_time__date=today,
        status__in=['approved', 'confirmed']
    ).select_related('user').order_by('start_time')
    
    # Get overdue check-ins and check-outs for this resource
    overdue_checkins = [b for b in checkin_service.get_overdue_checkins() if b.resource == resource]
    overdue_checkouts = [b for b in checkin_service.get_overdue_checkouts() if b.resource == resource]
    
    return render(request, 'booking/resource_checkin_status.html', {
        'resource': resource,
        'current_checkins': current_checkins,
        'today_bookings': today_bookings,
        'overdue_checkins': overdue_checkins,
        'overdue_checkouts': overdue_checkouts,
        'today': today,
    })


@login_required
def usage_analytics_view(request):
    """View usage analytics (managers only)."""
    try:
        user_profile = request.user.userprofile
        if user_profile.role not in ['technician', 'sysadmin']:
            messages.error(request, 'You do not have permission to view usage analytics.')
            return redirect('booking:dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'You do not have permission to view usage analytics.')
        return redirect('booking:dashboard')
    
    # Get filter parameters
    resource_id = request.GET.get('resource')
    days = int(request.GET.get('days', 30))
    
    # Calculate date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get analytics
    resource = None
    if resource_id:
        try:
            resource = Resource.objects.get(id=resource_id)
        except Resource.DoesNotExist:
            pass
    
    analytics = checkin_service.get_usage_analytics(
        resource=resource,
        start_date=start_date,
        end_date=end_date
    )
    
    # Get all resources for filter
    resources = Resource.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'booking/usage_analytics.html', {
        'analytics': analytics,
        'resource': resource,
        'resources': resources,
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    })


# API Views for Check-in/Check-out
@login_required
def api_checkin_booking(request, booking_id):
    """API endpoint for checking in to a booking."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    success, message = checkin_service.check_in_booking(
        booking_id=booking_id,
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    if success:
        return JsonResponse({'success': True, 'message': message})
    else:
        return JsonResponse({'success': False, 'message': message}, status=400)


@login_required  
def api_checkout_booking(request, booking_id):
    """API endpoint for checking out of a booking."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    success, message = checkin_service.check_out_booking(
        booking_id=booking_id,
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    if success:
        return JsonResponse({'success': True, 'message': message})
    else:
        return JsonResponse({'success': False, 'message': message}, status=400)


def ajax_load_colleges(request):
    """AJAX view to load colleges based on faculty selection."""
    faculty_id = request.GET.get('faculty_id')
    colleges = College.objects.filter(faculty_id=faculty_id, is_active=True).order_by('name')
    data = [{'id': college.id, 'name': college.name} for college in colleges]
    return JsonResponse({'colleges': data})


def ajax_load_departments(request):
    """AJAX view to load departments based on college selection."""
    college_id = request.GET.get('college_id')
    departments = Department.objects.filter(college_id=college_id, is_active=True).order_by('name')
    data = [{'id': department.id, 'name': department.name} for department in departments]
    return JsonResponse({'departments': data})


@login_required
def group_management_view(request):
    """Group management interface for managers."""
    try:
        user_profile = request.user.userprofile
        if user_profile.role not in ['technician', 'sysadmin']:
            messages.error(request, 'You do not have permission to manage groups.')
            return redirect('booking:dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'You do not have permission to manage groups.')
        return redirect('booking:dashboard')

    # Handle POST requests for group operations
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_group':
            return handle_create_group(request)
        elif action == 'rename_group':
            return handle_rename_group(request)
        elif action == 'merge_groups':
            return handle_merge_groups(request)
        elif action == 'delete_group':
            return handle_delete_group(request)
        elif action == 'bulk_assign':
            return handle_bulk_assign_users(request)

    # Get groups with member counts
    groups_data = UserProfile.objects.exclude(group='').values('group').annotate(
        member_count=Count('id'),
        students=Count('id', filter=Q(role='student')),
        researchers=Count('id', filter=Q(role='researcher')),
        academics=Count('id', filter=Q(role='academic')),
        technicians=Count('id', filter=Q(role='technician')),
        recent_activity=Count('user__booking', filter=Q(user__booking__created_at__gte=timezone.now() - timedelta(days=30)))
    ).order_by('-member_count')

    # Get users without groups
    ungrouped_users = UserProfile.objects.filter(group='').select_related('user')
    
    # Get recent group activities (bookings by group members)
    recent_bookings = Booking.objects.filter(
        user__userprofile__group__isnull=False,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('user__userprofile', 'resource').order_by('-created_at')[:20]

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        groups_data = groups_data.filter(group__icontains=search_query)

    # Pagination
    paginator = Paginator(groups_data, 20)
    page_number = request.GET.get('page')
    groups_page = paginator.get_page(page_number)

    context = {
        'groups_data': groups_page,
        'ungrouped_users': ungrouped_users,
        'recent_bookings': recent_bookings,
        'search_query': search_query,
        'total_groups': groups_data.count(),
        'total_ungrouped': ungrouped_users.count(),
    }

    return render(request, 'booking/group_management.html', context)


@login_required  
def group_detail_view(request, group_name):
    """Detailed view of a specific group."""
    try:
        user_profile = request.user.userprofile
        if user_profile.role not in ['technician', 'sysadmin']:
            messages.error(request, 'You do not have permission to view group details.')
            return redirect('booking:dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'You do not have permission to view group details.')
        return redirect('booking:dashboard')

    # Get group members
    group_members = UserProfile.objects.filter(group=group_name).select_related(
        'user', 'faculty', 'college', 'department'
    ).order_by('user__last_name', 'user__first_name')

    if not group_members.exists():
        messages.error(request, f'Group "{group_name}" not found.')
        return redirect('booking:group_management')

    # Handle POST requests for member management
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'remove_member':
            user_id = request.POST.get('user_id')
            try:
                member = UserProfile.objects.get(id=user_id, group=group_name)
                member.group = ''
                member.save()
                messages.success(request, f'Removed {member.user.get_full_name()} from group {group_name}.')
            except UserProfile.DoesNotExist:
                messages.error(request, 'User not found in this group.')
        
        elif action == 'change_role':
            user_id = request.POST.get('user_id')
            new_role = request.POST.get('new_role')
            try:
                member = UserProfile.objects.get(id=user_id, group=group_name)
                member.role = new_role
                member.save()
                messages.success(request, f'Changed {member.user.get_full_name()}\'s role to {new_role}.')
            except UserProfile.DoesNotExist:
                messages.error(request, 'User not found in this group.')
        
        return redirect('booking:group_detail', group_name=group_name)

    # Get group statistics
    group_stats = {
        'total_members': group_members.count(),
        'roles': group_members.values('role').annotate(count=Count('id')),
        'recent_bookings': Booking.objects.filter(
            user__userprofile__group=group_name,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count(),
        'active_bookings': Booking.objects.filter(
            user__userprofile__group=group_name,
            status__in=['pending', 'approved'],
            start_time__gte=timezone.now()
        ).count(),
    }

    # Get group's recent bookings
    recent_bookings = Booking.objects.filter(
        user__userprofile__group=group_name
    ).select_related('user', 'resource').order_by('-created_at')[:10]

    # Available users to add to group
    available_users = UserProfile.objects.filter(group='').select_related('user')

    context = {
        'group_name': group_name,
        'group_members': group_members,
        'group_stats': group_stats,
        'recent_bookings': recent_bookings,
        'available_users': available_users,
        'role_choices': UserProfile.ROLE_CHOICES,
    }

    return render(request, 'booking/group_detail.html', context)


def handle_create_group(request):
    """Handle group creation."""
    group_name = request.POST.get('group_name', '').strip()
    description = request.POST.get('description', '').strip()
    
    if not group_name:
        messages.error(request, 'Group name is required.')
        return redirect('booking:group_management')
    
    # Check if group already exists
    if UserProfile.objects.filter(group=group_name).exists():
        messages.error(request, f'Group "{group_name}" already exists.')
        return redirect('booking:group_management')
    
    # For now, we'll just create the group when first user is assigned
    # In a more advanced implementation, we might have a separate Group model
    messages.success(request, f'Group "{group_name}" will be created when first user is assigned.')
    return redirect('booking:group_management')


def handle_rename_group(request):
    """Handle group renaming."""
    old_name = request.POST.get('old_group_name', '').strip()
    new_name = request.POST.get('new_group_name', '').strip()
    
    if not old_name or not new_name:
        messages.error(request, 'Both old and new group names are required.')
        return redirect('booking:group_management')
    
    if old_name == new_name:
        messages.error(request, 'New group name must be different from old name.')
        return redirect('booking:group_management')
    
    # Check if new name already exists
    if UserProfile.objects.filter(group=new_name).exists():
        messages.error(request, f'Group "{new_name}" already exists.')
        return redirect('booking:group_management')
    
    # Rename the group
    updated = UserProfile.objects.filter(group=old_name).update(group=new_name)
    
    if updated > 0:
        messages.success(request, f'Renamed group "{old_name}" to "{new_name}" for {updated} users.')
    else:
        messages.error(request, f'Group "{old_name}" not found.')
    
    return redirect('booking:group_management')


def handle_merge_groups(request):
    """Handle merging groups."""
    source_group = request.POST.get('source_group', '').strip()
    target_group = request.POST.get('target_group', '').strip()
    
    if not source_group or not target_group:
        messages.error(request, 'Both source and target group names are required.')
        return redirect('booking:group_management')
    
    if source_group == target_group:
        messages.error(request, 'Source and target groups must be different.')
        return redirect('booking:group_management')
    
    # Check if both groups exist
    source_count = UserProfile.objects.filter(group=source_group).count()
    target_count = UserProfile.objects.filter(group=target_group).count()
    
    if source_count == 0:
        messages.error(request, f'Source group "{source_group}" not found.')
        return redirect('booking:group_management')
    
    if target_count == 0:
        messages.error(request, f'Target group "{target_group}" not found.')
        return redirect('booking:group_management')
    
    # Merge the groups
    updated = UserProfile.objects.filter(group=source_group).update(group=target_group)
    
    messages.success(request, f'Merged {updated} users from "{source_group}" into "{target_group}".')
    return redirect('booking:group_management')


def handle_delete_group(request):
    """Handle group deletion (removes group assignment from users)."""
    group_name = request.POST.get('group_name', '').strip()
    
    if not group_name:
        messages.error(request, 'Group name is required.')
        return redirect('booking:group_management')
    
    # Remove group assignment from all users
    updated = UserProfile.objects.filter(group=group_name).update(group='')
    
    if updated > 0:
        messages.success(request, f'Removed group assignment from {updated} users in "{group_name}".')
    else:
        messages.error(request, f'Group "{group_name}" not found.')
    
    return redirect('booking:group_management')


def handle_bulk_assign_users(request):
    """Handle bulk assignment of users to a group."""
    group_name = request.POST.get('target_group', '').strip()
    user_ids = request.POST.getlist('user_ids')
    
    if not group_name:
        messages.error(request, 'Target group name is required.')
        return redirect('booking:group_management')
    
    if not user_ids:
        messages.error(request, 'No users selected.')
        return redirect('booking:group_management')
    
    # Update selected users
    updated = UserProfile.objects.filter(id__in=user_ids).update(group=group_name)
    
    messages.success(request, f'Assigned {updated} users to group "{group_name}".')
    return redirect('booking:group_management')


@login_required
def add_user_to_group(request, group_name):
    """Add a user to a specific group via AJAX."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        user_profile = request.user.userprofile
        if user_profile.role not in ['technician', 'sysadmin']:
            return JsonResponse({'error': 'Permission denied'}, status=403)
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    user_id = request.POST.get('user_id')
    
    try:
        user_profile = UserProfile.objects.get(id=user_id)
        user_profile.group = group_name
        user_profile.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Added {user_profile.user.get_full_name()} to group {group_name}.'
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Approval Workflow API Views

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .serializers import (
    ResourceResponsibleSerializer, RiskAssessmentSerializer, UserRiskAssessmentSerializer,
    TrainingCourseSerializer, ResourceTrainingRequirementSerializer, UserTrainingSerializer,
    AccessRequestDetailSerializer
)
from .models import (
    ResourceResponsible, RiskAssessment, UserRiskAssessment, TrainingCourse,
    ResourceTrainingRequirement, UserTraining, AccessRequest
)


class IsManagerOrReadOnly(permissions.BasePermission):
    """Permission that allows managers to edit, others to read only."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions for managers only
        try:
            user_profile = request.user.userprofile
            return user_profile.role in ['technician', 'sysadmin']
        except:
            return False


class ResourceResponsibleViewSet(viewsets.ModelViewSet):
    queryset = ResourceResponsible.objects.all()
    serializer_class = ResourceResponsibleSerializer
    permission_classes = [IsManagerOrReadOnly]
    
    def get_queryset(self):
        queryset = ResourceResponsible.objects.select_related('user', 'resource', 'assigned_by')
        
        # Filter by resource
        resource_id = self.request.query_params.get('resource', None)
        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)
        
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by role type
        role_type = self.request.query_params.get('role_type', None)
        if role_type:
            queryset = queryset.filter(role_type=role_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_resource(self, request):
        """Get responsible persons for a specific resource."""
        resource_id = request.query_params.get('resource_id')
        if not resource_id:
            return Response({'error': 'resource_id parameter required'}, status=400)
        
        responsible_persons = self.get_queryset().filter(resource_id=resource_id, is_active=True)
        serializer = self.get_serializer(responsible_persons, many=True)
        return Response(serializer.data)


class RiskAssessmentViewSet(viewsets.ModelViewSet):
    queryset = RiskAssessment.objects.all()
    serializer_class = RiskAssessmentSerializer
    permission_classes = [IsManagerOrReadOnly]
    
    def get_queryset(self):
        queryset = RiskAssessment.objects.select_related('resource', 'created_by', 'approved_by')
        
        # Filter by resource
        resource_id = self.request.query_params.get('resource', None)
        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)
        
        # Filter by assessment type
        assessment_type = self.request.query_params.get('assessment_type', None)
        if assessment_type:
            queryset = queryset.filter(assessment_type=assessment_type)
        
        # Filter by risk level
        risk_level = self.request.query_params.get('risk_level', None)
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by mandatory status
        is_mandatory = self.request.query_params.get('is_mandatory', None)
        if is_mandatory is not None:
            queryset = queryset.filter(is_mandatory=is_mandatory.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrReadOnly])
    def approve(self, request, pk=None):
        """Approve a risk assessment."""
        assessment = self.get_object()
        assessment.approved_by = request.user
        assessment.approved_at = timezone.now()
        assessment.save()
        
        serializer = self.get_serializer(assessment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_resource(self, request):
        """Get risk assessments for a specific resource."""
        resource_id = request.query_params.get('resource_id')
        if not resource_id:
            return Response({'error': 'resource_id parameter required'}, status=400)
        
        assessments = self.get_queryset().filter(resource_id=resource_id, is_active=True)
        serializer = self.get_serializer(assessments, many=True)
        return Response(serializer.data)


class UserRiskAssessmentViewSet(viewsets.ModelViewSet):
    queryset = UserRiskAssessment.objects.all()
    serializer_class = UserRiskAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = UserRiskAssessment.objects.select_related('user', 'risk_assessment', 'reviewed_by')
        
        # Users can only see their own assessments unless they're managers
        try:
            user_profile = self.request.user.userprofile
            if user_profile.role not in ['technician', 'sysadmin']:
                queryset = queryset.filter(user=self.request.user)
        except:
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by risk assessment
        assessment_id = self.request.query_params.get('risk_assessment', None)
        if assessment_id:
            queryset = queryset.filter(risk_assessment_id=assessment_id)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a risk assessment."""
        assessment = self.get_object()
        if assessment.user != request.user:
            return Response({'error': 'Permission denied'}, status=403)
        
        assessment.start_assessment()
        serializer = self.get_serializer(assessment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit assessment for review."""
        assessment = self.get_object()
        if assessment.user != request.user:
            return Response({'error': 'Permission denied'}, status=403)
        
        responses = request.data.get('responses', {})
        declaration = request.data.get('declaration', '')
        
        assessment.submit_for_review(responses, declaration)
        serializer = self.get_serializer(assessment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrReadOnly])
    def approve(self, request, pk=None):
        """Approve an assessment."""
        assessment = self.get_object()
        score = request.data.get('score')
        notes = request.data.get('notes', '')
        
        assessment.approve(request.user, score, notes)
        serializer = self.get_serializer(assessment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrReadOnly])
    def reject(self, request, pk=None):
        """Reject an assessment."""
        assessment = self.get_object()
        notes = request.data.get('notes', '')
        
        assessment.reject(request.user, notes)
        serializer = self.get_serializer(assessment)
        return Response(serializer.data)


class TrainingCourseViewSet(viewsets.ModelViewSet):
    queryset = TrainingCourse.objects.all()
    serializer_class = TrainingCourseSerializer
    permission_classes = [IsManagerOrReadOnly]
    
    def get_queryset(self):
        queryset = TrainingCourse.objects.select_related('created_by').prefetch_related('instructors', 'prerequisite_courses')
        
        # Filter by course type
        course_type = self.request.query_params.get('course_type', None)
        if course_type:
            queryset = queryset.filter(course_type=course_type)
        
        # Filter by delivery method
        delivery_method = self.request.query_params.get('delivery_method', None)
        if delivery_method:
            queryset = queryset.filter(delivery_method=delivery_method)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by mandatory status
        is_mandatory = self.request.query_params.get('is_mandatory', None)
        if is_mandatory is not None:
            queryset = queryset.filter(is_mandatory=is_mandatory.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def available_for_resource(self, request):
        """Get training courses required for a specific resource."""
        resource_id = request.query_params.get('resource_id')
        if not resource_id:
            return Response({'error': 'resource_id parameter required'}, status=400)
        
        # Get training requirements for the resource
        requirements = ResourceTrainingRequirement.objects.filter(
            resource_id=resource_id
        ).select_related('training_course')
        
        courses = [req.training_course for req in requirements]
        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data)


class ResourceTrainingRequirementViewSet(viewsets.ModelViewSet):
    queryset = ResourceTrainingRequirement.objects.all()
    serializer_class = ResourceTrainingRequirementSerializer
    permission_classes = [IsManagerOrReadOnly]
    
    def get_queryset(self):
        queryset = ResourceTrainingRequirement.objects.select_related('resource', 'training_course')
        
        # Filter by resource
        resource_id = self.request.query_params.get('resource', None)
        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)
        
        # Filter by training course
        course_id = self.request.query_params.get('training_course', None)
        if course_id:
            queryset = queryset.filter(training_course_id=course_id)
        
        # Filter by mandatory status
        is_mandatory = self.request.query_params.get('is_mandatory', None)
        if is_mandatory is not None:
            queryset = queryset.filter(is_mandatory=is_mandatory.lower() == 'true')
        
        return queryset


class UserTrainingViewSet(viewsets.ModelViewSet):
    queryset = UserTraining.objects.all()
    serializer_class = UserTrainingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = UserTraining.objects.select_related('user', 'training_course', 'instructor')
        
        # Users can only see their own training unless they're managers
        try:
            user_profile = self.request.user.userprofile
            if user_profile.role not in ['technician', 'sysadmin']:
                queryset = queryset.filter(user=self.request.user)
        except:
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by training course
        course_id = self.request.query_params.get('training_course', None)
        if course_id:
            queryset = queryset.filter(training_course_id=course_id)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start training."""
        training = self.get_object()
        if training.user != request.user:
            return Response({'error': 'Permission denied'}, status=403)
        
        training.start_training()
        serializer = self.get_serializer(training)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrReadOnly])
    def complete(self, request, pk=None):
        """Complete training with scores."""
        training = self.get_object()
        
        theory_score = request.data.get('theory_score')
        practical_score = request.data.get('practical_score')
        instructor_notes = request.data.get('instructor_notes', '')
        
        training.complete_training(
            theory_score=theory_score,
            practical_score=practical_score,
            instructor=request.user,
            notes=instructor_notes
        )
        
        serializer = self.get_serializer(training)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def enroll(self, request):
        """Enroll user in a training course."""
        course_id = request.data.get('training_course_id')
        if not course_id:
            return Response({'error': 'training_course_id required'}, status=400)
        
        try:
            course = TrainingCourse.objects.get(id=course_id)
            training, created = UserTraining.objects.get_or_create(
                user=request.user,
                training_course=course,
                status='enrolled',
                defaults={'status': 'enrolled'}
            )
            
            if not created:
                return Response({'error': 'Already enrolled in this course'}, status=400)
            
            serializer = self.get_serializer(training)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except TrainingCourse.DoesNotExist:
            return Response({'error': 'Training course not found'}, status=404)


class AccessRequestViewSet(viewsets.ModelViewSet):
    """Enhanced AccessRequest viewset with approval workflow."""
    queryset = AccessRequest.objects.all()
    serializer_class = AccessRequestDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = AccessRequest.objects.select_related('user', 'resource', 'reviewed_by')
        
        # Users can see their own requests, managers can see all
        try:
            user_profile = self.request.user.userprofile
            if user_profile.role not in ['technician', 'sysadmin']:
                # Check if user can approve requests for any resources
                can_approve = ResourceResponsible.objects.filter(
                    user=self.request.user,
                    is_active=True,
                    can_approve_access=True
                ).exists()
                
                if not can_approve:
                    queryset = queryset.filter(user=self.request.user)
        except:
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by resource
        resource_id = self.request.query_params.get('resource', None)
        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)
        
        # Filter requests that need approval by current user
        needs_approval = self.request.query_params.get('needs_approval', None)
        if needs_approval == 'true':
            # Get resources where current user can approve
            approvable_resources = ResourceResponsible.objects.filter(
                user=self.request.user,
                is_active=True,
                can_approve_access=True
            ).values_list('resource_id', flat=True)
            
            queryset = queryset.filter(
                resource_id__in=approvable_resources,
                status='pending'
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an access request."""
        access_request = self.get_object()
        
        # Check if user can approve this request
        if not access_request.can_be_approved_by(request.user):
            return Response({'error': 'Permission denied'}, status=403)
        
        # Check if user meets all requirements
        compliance = access_request.check_user_compliance()
        if not (compliance['training_complete'] and compliance['risk_assessments_complete']):
            return Response({
                'error': 'User has not completed all required training and risk assessments',
                'missing_requirements': {
                    'training': [str(t) for t in compliance['missing_training']],
                    'assessments': [str(a) for a in compliance['missing_assessments']]
                }
            }, status=400)
        
        review_notes = request.data.get('review_notes', '')
        expires_in_days = request.data.get('expires_in_days')
        
        access_request.approve(request.user, review_notes, expires_in_days)
        
        serializer = self.get_serializer(access_request)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an access request."""
        access_request = self.get_object()
        
        # Check if user can approve this request
        if not access_request.can_be_approved_by(request.user):
            return Response({'error': 'Permission denied'}, status=403)
        
        review_notes = request.data.get('review_notes', '')
        access_request.reject(request.user, review_notes)
        
        serializer = self.get_serializer(access_request)
        return Response(serializer.data)


class ResourceUtilizationTrendViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for resource utilization trend analysis."""
    serializer_class = None  # Will define serializer separately
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        from .models import ResourceUtilizationTrend
        queryset = ResourceUtilizationTrend.objects.select_related('resource')
        
        # Filter by resource if specified
        resource_id = self.request.query_params.get('resource', None)
        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)
        
        # Filter by period type
        period_type = self.request.query_params.get('period_type', 'daily')
        queryset = queryset.filter(period_type=period_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date)
                queryset = queryset.filter(period_start__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date)
                queryset = queryset.filter(period_end__lte=end_date)
            except ValueError:
                pass
        
        return queryset.order_by('-period_start')
    
    def list(self, request, *args, **kwargs):
        """List utilization trends with summary statistics."""
        queryset = self.get_queryset()
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = self._serialize_trends(page)
            return self.get_paginated_response(data)
        
        data = self._serialize_trends(queryset)
        return Response(data)
    
    def _serialize_trends(self, trends):
        """Serialize trend data with calculations."""
        data = []
        for trend in trends:
            data.append({
                'id': trend.id,
                'resource': {
                    'id': trend.resource.id,
                    'name': trend.resource.name,
                    'type': trend.resource.resource_type,
                    'location': trend.resource.location,
                },
                'period_type': trend.period_type,
                'period_start': trend.period_start.isoformat(),
                'period_end': trend.period_end.isoformat(),
                'utilization_rate': float(trend.utilization_rate),
                'actual_usage_rate': float(trend.actual_usage_rate),
                'total_bookings': trend.total_bookings,
                'unique_users': trend.unique_users,
                'no_show_rate': float(trend.no_show_rate),
                'trend_direction': trend.trend_direction,
                'trend_strength': float(trend.trend_strength),
                'capacity_status': trend.get_capacity_status(),
                'efficiency_score': trend.efficiency_score,
                'demand_score': trend.demand_score,
                'waste_score': trend.waste_score,
                'peak_hour': trend.peak_hour,
                'peak_day': trend.peak_day,
                'forecast_next_period': float(trend.forecast_next_period) if trend.forecast_next_period else None,
                'forecast_confidence': float(trend.forecast_confidence),
                'calculated_at': trend.calculated_at.isoformat(),
            })
        return data
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get utilization summary for dashboard."""
        from .utilization_service import utilization_service
        
        resource_id = request.query_params.get('resource')
        period_type = request.query_params.get('period_type', 'monthly')
        limit = int(request.query_params.get('limit', 12))
        
        resource = None
        if resource_id:
            try:
                from .models import Resource
                resource = Resource.objects.get(id=resource_id)
            except Resource.DoesNotExist:
                return Response({'error': 'Resource not found'}, status=404)
        
        summary = utilization_service.get_utilization_summary(
            resource=resource,
            period_type=period_type,
            limit=limit
        )
        
        return Response(summary)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Trigger utilization trend calculation."""
        from .utilization_service import utilization_service
        
        # Check if user has permission to trigger calculations
        try:
            user_profile = request.user.userprofile
            if user_profile.role not in ['technician', 'sysadmin']:
                return Response({'error': 'Permission denied'}, status=403)
        except:
            return Response({'error': 'Permission denied'}, status=403)
        
        # Get calculation parameters
        resource_id = request.data.get('resource_id')
        period_type = request.data.get('period_type', 'daily')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        force_recalculate = request.data.get('force_recalculate', False)
        
        # Parse dates
        try:
            if start_date:
                start_date = datetime.fromisoformat(start_date)
            if end_date:
                end_date = datetime.fromisoformat(end_date)
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=400)
        
        # Get resource if specified
        resource = None
        if resource_id:
            try:
                from .models import Resource
                resource = Resource.objects.get(id=resource_id)
            except Resource.DoesNotExist:
                return Response({'error': 'Resource not found'}, status=404)
        
        # Trigger calculation
        try:
            results = utilization_service.calculate_utilization_trends(
                resource=resource,
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                force_recalculate=force_recalculate
            )
            
            return Response({
                'message': 'Calculation completed successfully',
                'results': results
            })
        
        except Exception as e:
            logger.error(f"Utilization calculation error: {str(e)}")
            return Response({'error': 'Calculation failed'}, status=500)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export utilization trends as CSV."""
        import csv
        from django.http import HttpResponse
        
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="utilization_trends.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Resource', 'Period Type', 'Period Start', 'Period End',
            'Utilization Rate', 'Actual Usage Rate', 'Total Bookings',
            'Unique Users', 'No Show Rate', 'Trend Direction',
            'Trend Strength', 'Capacity Status', 'Efficiency Score'
        ])
        
        for trend in queryset:
            writer.writerow([
                trend.resource.name,
                trend.period_type,
                trend.period_start.strftime('%Y-%m-%d %H:%M'),
                trend.period_end.strftime('%Y-%m-%d %H:%M'),
                float(trend.utilization_rate),
                float(trend.actual_usage_rate),
                trend.total_bookings,
                trend.unique_users,
                float(trend.no_show_rate),
                trend.trend_direction,
                float(trend.trend_strength),
                trend.get_capacity_status(),
                trend.efficiency_score,
            ])
        
        return response


# Approval Workflow Template Views

@login_required
def approval_dashboard_view(request):
    """Dashboard for approval workflow management."""
    # Summary statistics
    pending_access_requests = AccessRequest.objects.filter(status='pending').count()
    incomplete_assessments = UserRiskAssessment.objects.filter(status='submitted').count()
    pending_training = UserTraining.objects.filter(status='completed').count()
    overdue_items = 0  # Placeholder for overdue calculations
    
    # Recent access requests
    recent_access_requests = AccessRequest.objects.filter(
        status='pending'
    ).select_related('user', 'resource').order_by('-created_at')[:5]
    
    # Quick stats
    approved_today = AccessRequest.objects.filter(
        status='approved',
        reviewed_at__date=timezone.now().date()
    ).count()
    total_this_week = AccessRequest.objects.filter(
        created_at__week=timezone.now().isocalendar().week
    ).count()
    
    context = {
        'pending_access_requests': pending_access_requests,
        'incomplete_assessments': incomplete_assessments,
        'pending_training': pending_training,
        'overdue_items': overdue_items,
        'recent_access_requests': recent_access_requests,
        'approved_today': approved_today,
        'total_this_week': total_this_week,
    }
    
    return render(request, 'booking/approval_dashboard.html', context)


@login_required
def access_requests_view(request):
    """List view for access requests."""
    from django.core.paginator import Paginator
    
    # Start with all access requests
    access_requests = AccessRequest.objects.select_related('user', 'resource', 'reviewed_by')
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        access_requests = access_requests.filter(status=status_filter)
    
    resource_type_filter = request.GET.get('resource_type')
    if resource_type_filter:
        access_requests = access_requests.filter(resource__resource_type=resource_type_filter)
    
    access_type_filter = request.GET.get('access_type')
    if access_type_filter:
        access_requests = access_requests.filter(access_type=access_type_filter)
    
    # Order by priority and creation date
    access_requests = access_requests.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(access_requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options for the template
    resource_types = Resource.RESOURCE_TYPE_CHOICES
    
    context = {
        'access_requests': page_obj,
        'resource_types': resource_types,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, 'booking/access_requests.html', context)


@login_required
def access_request_detail_view(request, request_id):
    """Detail view for a single access request."""
    access_request = get_object_or_404(AccessRequest, id=request_id)
    
    # Check if current user can approve
    can_approve = access_request.can_be_approved_by(request.user)
    
    context = {
        'access_request': access_request,
        'can_approve': can_approve,
    }
    
    return render(request, 'booking/access_request_detail.html', context)


@login_required
def approve_access_request_view(request, request_id):
    """Approve an access request."""
    access_request = get_object_or_404(AccessRequest, id=request_id)
    
    # Check permissions
    if not access_request.can_be_approved_by(request.user):
        messages.error(request, "You don't have permission to approve this request.")
        return redirect('booking:access_request_detail', request_id=request_id)
    
    if request.method == 'POST':
        form = AccessRequestReviewForm(request.POST)
        if form.is_valid():
            review_notes = form.cleaned_data.get('review_notes', '')
            granted_duration = form.cleaned_data.get('granted_duration_days')
            
            # Approve the request
            access_request.approve(request.user, review_notes, granted_duration)
            
            messages.success(request, f"Access request for {access_request.resource.name} has been approved.")
            return redirect('booking:access_request_detail', request_id=request_id)
    else:
        form = AccessRequestReviewForm(initial={'decision': 'approve'})
    
    context = {
        'access_request': access_request,
        'form': form,
        'action': 'approve',
    }
    
    return render(request, 'booking/access_request_review.html', context)


@login_required
def reject_access_request_view(request, request_id):
    """Reject an access request."""
    access_request = get_object_or_404(AccessRequest, id=request_id)
    
    # Check permissions
    if not access_request.can_be_approved_by(request.user):
        messages.error(request, "You don't have permission to reject this request.")
        return redirect('booking:access_request_detail', request_id=request_id)
    
    if request.method == 'POST':
        form = AccessRequestReviewForm(request.POST)
        if form.is_valid():
            review_notes = form.cleaned_data.get('review_notes', '')
            
            # Reject the request
            access_request.reject(request.user, review_notes)
            
            messages.success(request, f"Access request for {access_request.resource.name} has been rejected.")
            return redirect('booking:access_request_detail', request_id=request_id)
    else:
        form = AccessRequestReviewForm(initial={'decision': 'reject'})
    
    context = {
        'access_request': access_request,
        'form': form,
        'action': 'reject',
    }
    
    return render(request, 'booking/access_request_review.html', context)


@login_required
def risk_assessments_view(request):
    """List view for risk assessments."""
    from django.core.paginator import Paginator
    
    # Get all risk assessments
    risk_assessments = RiskAssessment.objects.select_related('resource', 'created_by')
    
    # Apply filters
    assessment_type_filter = request.GET.get('assessment_type')
    if assessment_type_filter:
        risk_assessments = risk_assessments.filter(assessment_type=assessment_type_filter)
    
    risk_level_filter = request.GET.get('risk_level')
    if risk_level_filter:
        risk_assessments = risk_assessments.filter(risk_level=risk_level_filter)
    
    resource_filter = request.GET.get('resource')
    if resource_filter:
        risk_assessments = risk_assessments.filter(resource_id=resource_filter)
    
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        risk_assessments = risk_assessments.filter(is_active=True, valid_until__gte=timezone.now().date())
    elif status_filter == 'expired':
        risk_assessments = risk_assessments.filter(valid_until__lt=timezone.now().date())
    
    # Order by creation date
    risk_assessments = risk_assessments.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(risk_assessments, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user's assessment status
    user_assessments = {}
    if request.user.is_authenticated:
        user_assessment_qs = UserRiskAssessment.objects.filter(
            user=request.user,
            risk_assessment__in=risk_assessments
        ).select_related('risk_assessment')
        
        user_assessments = {
            ua.risk_assessment.id: ua for ua in user_assessment_qs
        }
    
    # Filter options
    assessment_types = RiskAssessment.ASSESSMENT_TYPE_CHOICES
    resources = Resource.objects.filter(is_active=True).order_by('name')
    
    context = {
        'risk_assessments': page_obj,
        'assessment_types': assessment_types,
        'resources': resources,
        'user_assessments': user_assessments,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, 'booking/risk_assessments.html', context)


@login_required
def risk_assessment_detail_view(request, assessment_id):
    """Detail view for a risk assessment."""
    assessment = get_object_or_404(RiskAssessment, id=assessment_id)
    
    # Get user's assessment if exists
    user_assessment = None
    if request.user.is_authenticated:
        try:
            user_assessment = UserRiskAssessment.objects.get(
                user=request.user,
                risk_assessment=assessment
            )
        except UserRiskAssessment.DoesNotExist:
            pass
    
    context = {
        'assessment': assessment,
        'user_assessment': user_assessment,
    }
    
    return render(request, 'booking/risk_assessment_detail.html', context)


@login_required
def start_risk_assessment_view(request, assessment_id):
    """Start a risk assessment."""
    assessment = get_object_or_404(RiskAssessment, id=assessment_id)
    
    # Check if user already has an assessment
    user_assessment, created = UserRiskAssessment.objects.get_or_create(
        user=request.user,
        risk_assessment=assessment,
        defaults={'status': 'not_started'}
    )
    
    if request.method == 'POST':
        form = UserRiskAssessmentForm(request.POST, instance=user_assessment, risk_assessment=assessment)
        if form.is_valid():
            user_assessment = form.save(commit=False)
            user_assessment.status = 'submitted'
            user_assessment.submitted_at = timezone.now()
            user_assessment.save()
            
            messages.success(request, "Risk assessment submitted for review.")
            return redirect('booking:risk_assessment_detail', assessment_id=assessment_id)
    else:
        # Mark as started
        if user_assessment.status == 'not_started':
            user_assessment.status = 'in_progress'
            user_assessment.started_at = timezone.now()
            user_assessment.save()
        
        form = UserRiskAssessmentForm(instance=user_assessment, risk_assessment=assessment)
    
    context = {
        'assessment': assessment,
        'user_assessment': user_assessment,
        'form': form,
    }
    
    return render(request, 'booking/start_risk_assessment.html', context)


@login_required
def submit_risk_assessment_view(request, assessment_id):
    """Submit a completed risk assessment."""
    assessment = get_object_or_404(RiskAssessment, id=assessment_id)
    user_assessment = get_object_or_404(
        UserRiskAssessment,
        user=request.user,
        risk_assessment=assessment
    )
    
    if user_assessment.status != 'in_progress':
        messages.error(request, "This assessment cannot be submitted.")
        return redirect('booking:risk_assessment_detail', assessment_id=assessment_id)
    
    user_assessment.status = 'submitted'
    user_assessment.submitted_at = timezone.now()
    user_assessment.save()
    
    messages.success(request, "Risk assessment submitted for review.")
    return redirect('booking:risk_assessment_detail', assessment_id=assessment_id)


@login_required
def create_risk_assessment_view(request):
    """Create a new risk assessment."""
    if not request.user.userprofile.role in ['technician', 'academic', 'sysadmin']:
        messages.error(request, "You don't have permission to create risk assessments.")
        return redirect('booking:risk_assessments')
    
    if request.method == 'POST':
        form = RiskAssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.created_by = request.user
            assessment.save()
            
            messages.success(request, f"Risk assessment '{assessment.title}' created successfully.")
            return redirect('booking:risk_assessment_detail', assessment_id=assessment.id)
    else:
        form = RiskAssessmentForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'booking/create_risk_assessment.html', context)


@login_required
def training_dashboard_view(request):
    """Dashboard for training management."""
    # User's training statistics
    my_completed_training = UserTraining.objects.filter(
        user=request.user, status='completed'
    ).count()
    
    my_in_progress_training = UserTraining.objects.filter(
        user=request.user, status='in_progress'
    ).count()
    
    available_courses = TrainingCourse.objects.filter(is_active=True).count()
    
    expiring_soon = UserTraining.objects.filter(
        user=request.user,
        status='completed',
        expires_at__lte=timezone.now() + timedelta(days=30)
    ).count()
    
    # User's training progress
    my_training = UserTraining.objects.filter(
        user=request.user
    ).select_related('training_course').order_by('-enrolled_at')[:6]
    
    # Recommended courses (placeholder logic)
    recommended_courses = TrainingCourse.objects.filter(
        is_active=True
    ).exclude(
        id__in=UserTraining.objects.filter(user=request.user).values_list('training_course_id', flat=True)
    )[:5]
    
    # Upcoming sessions
    upcoming_sessions = UserTraining.objects.filter(
        user=request.user,
        session_date__gte=timezone.now(),
        status__in=['enrolled', 'in_progress']
    ).order_by('session_date')[:5]
    
    context = {
        'my_completed_training': my_completed_training,
        'my_in_progress_training': my_in_progress_training,
        'available_courses': available_courses,
        'expiring_soon': expiring_soon,
        'my_training': my_training,
        'recommended_courses': recommended_courses,
        'upcoming_sessions': upcoming_sessions,
    }
    
    return render(request, 'booking/training_dashboard.html', context)


@login_required
def training_courses_view(request):
    """List view for training courses."""
    courses = TrainingCourse.objects.filter(is_active=True).order_by('title')
    
    context = {
        'courses': courses,
    }
    
    return render(request, 'booking/training_courses.html', context)


@login_required
def training_course_detail_view(request, course_id):
    """Detail view for a training course."""
    course = get_object_or_404(TrainingCourse, id=course_id)
    
    # Get user's training record if exists
    user_training = None
    if request.user.is_authenticated:
        try:
            user_training = UserTraining.objects.get(
                user=request.user,
                training_course=course
            )
        except UserTraining.DoesNotExist:
            pass
    
    context = {
        'course': course,
        'user_training': user_training,
    }
    
    return render(request, 'booking/training_course_detail.html', context)


@login_required
def enroll_training_view(request, course_id):
    """Enroll in a training course."""
    course = get_object_or_404(TrainingCourse, id=course_id)
    
    # Check if already enrolled
    existing_training = UserTraining.objects.filter(
        user=request.user,
        training_course=course
    ).first()
    
    if existing_training:
        messages.warning(request, f"You are already enrolled in {course.title}.")
        return redirect('booking:training_course_detail', course_id=course_id)
    
    if request.method == 'POST':
        form = UserTrainingEnrollForm(request.POST, training_course=course)
        if form.is_valid():
            # Create training record
            user_training = UserTraining.objects.create(
                user=request.user,
                training_course=course,
                status='enrolled'
            )
            
            messages.success(request, f"Successfully enrolled in {course.title}.")
            return redirect('booking:training_course_detail', course_id=course_id)
    else:
        form = UserTrainingEnrollForm(training_course=course)
    
    context = {
        'course': course,
        'form': form,
    }
    
    return render(request, 'booking/enroll_training.html', context)


@login_required
def my_training_view(request):
    """View user's training records."""
    training_records = UserTraining.objects.filter(
        user=request.user
    ).select_related('training_course').order_by('-enrolled_at')
    
    context = {
        'training_records': training_records,
    }
    
    return render(request, 'booking/my_training.html', context)


@login_required
def manage_training_view(request):
    """Manage training (for instructors/managers)."""
    if not request.user.userprofile.role in ['technician', 'academic', 'sysadmin']:
        messages.error(request, "You don't have permission to manage training.")
        return redirect('booking:training_dashboard')
    
    # Get training records to review
    pending_training = UserTraining.objects.filter(
        status='completed'
    ).select_related('user', 'training_course').order_by('-completed_at')
    
    context = {
        'pending_training': pending_training,
    }
    
    return render(request, 'booking/manage_training.html', context)


@login_required
def manage_resource_view(request, resource_id):
    """Manage a specific resource."""
    resource = get_object_or_404(Resource, id=resource_id)
    
    if not request.user.userprofile.role in ['technician', 'sysadmin']:
        messages.error(request, "You don't have permission to manage resources.")
        return redirect('booking:resource_detail', resource_id=resource_id)
    
    context = {
        'resource': resource,
    }
    
    return render(request, 'booking/manage_resource.html', context)


@login_required
def assign_resource_responsible_view(request, resource_id):
    """Assign responsibility for a resource."""
    resource = get_object_or_404(Resource, id=resource_id)
    
    if not request.user.userprofile.role in ['technician', 'sysadmin']:
        messages.error(request, "You don't have permission to assign resource responsibility.")
        return redirect('booking:resource_detail', resource_id=resource_id)
    
    if request.method == 'POST':
        form = ResourceResponsibleForm(request.POST, resource=resource)
        if form.is_valid():
            responsible = form.save(commit=False)
            responsible.resource = resource
            responsible.assigned_by = request.user
            responsible.save()
            
            messages.success(request, f"Resource responsibility assigned to {responsible.user.get_full_name()}.")
            return redirect('booking:manage_resource', resource_id=resource_id)
    else:
        form = ResourceResponsibleForm(resource=resource)
    
    context = {
        'resource': resource,
        'form': form,
    }
    
    return render(request, 'booking/assign_resource_responsible.html', context)


@login_required
def resource_training_requirements_view(request, resource_id):
    """Manage training requirements for a resource."""
    resource = get_object_or_404(Resource, id=resource_id)
    
    if not request.user.userprofile.role in ['technician', 'sysadmin']:
        messages.error(request, "You don't have permission to manage training requirements.")
        return redirect('booking:resource_detail', resource_id=resource_id)
    
    training_requirements = ResourceTrainingRequirement.objects.filter(
        resource=resource
    ).select_related('training_course').order_by('order')
    
    context = {
        'resource': resource,
        'training_requirements': training_requirements,
    }
    
    return render(request, 'booking/resource_training_requirements.html', context)



def is_lab_admin(user):
    """Check if user is in Lab Admin group."""
    return user.groups.filter(name='Lab Admin').exists() or user.is_staff or user.userprofile.role in ['technician', 'sysadmin']

@login_required
@user_passes_test(is_lab_admin)
def approval_statistics_view(request):
    """User-friendly approval statistics dashboard."""
    from .models import ApprovalStatistics, AccessRequest, TrainingRequest
    from django.db.models import Avg, Sum, Count
    from datetime import datetime, timedelta
    import json
    
    # Get filter parameters
    period_type = request.GET.get('period', 'monthly')
    resource_filter = request.GET.get('resource')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Set default date range (last 30 days)
    today = timezone.now().date()
    if not start_date:
        start_date = today - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = today
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Base queryset for statistics
    stats_qs = ApprovalStatistics.objects.filter(
        period_start__gte=start_date,
        period_end__lte=end_date,
        period_type=period_type
    )
    
    # Filter by resource if specified
    if resource_filter:
        stats_qs = stats_qs.filter(resource_id=resource_filter)
    
    # Only show statistics for resources the user has responsibility for (unless admin)
    if not request.user.userprofile.role in ['technician', 'sysadmin']:
        stats_qs = stats_qs.filter(resource__responsible_persons__user=request.user)
    
    # Calculate summary statistics
    summary_data = stats_qs.aggregate(
        total_requests=Sum('access_requests_received'),
        total_approved=Sum('access_requests_approved'),
        total_rejected=Sum('access_requests_rejected'),
        total_pending=Sum('access_requests_pending'),
        avg_response_time=Avg('avg_response_time_hours'),
        total_overdue=Sum('overdue_items'),
        total_training_requests=Sum('training_requests_received'),
        total_training_completions=Sum('training_completions'),
        total_assessments=Sum('assessments_created'),
    )
    
    # Calculate approval rate
    total_processed = (summary_data['total_approved'] or 0) + (summary_data['total_rejected'] or 0)
    approval_rate = (summary_data['total_approved'] or 0) / total_processed * 100 if total_processed > 0 else 0
    
    # Calculate trends (comparing to previous period)
    previous_start = start_date - (end_date - start_date)
    previous_end = start_date - timedelta(days=1)
    
    previous_stats = ApprovalStatistics.objects.filter(
        period_start__gte=previous_start,
        period_end__lte=previous_end,
        period_type=period_type
    )
    
    if resource_filter:
        previous_stats = previous_stats.filter(resource_id=resource_filter)
    
    if not request.user.userprofile.role in ['technician', 'sysadmin']:
        previous_stats = previous_stats.filter(resource__responsible_persons__user=request.user)
    
    previous_data = previous_stats.aggregate(
        prev_total_requests=Sum('access_requests_received'),
        prev_total_approved=Sum('access_requests_approved'),
        prev_total_rejected=Sum('access_requests_rejected'),
        prev_avg_response_time=Avg('avg_response_time_hours'),
        prev_total_overdue=Sum('overdue_items'),
    )
    
    # Calculate trend indicators
    prev_processed = (previous_data['prev_total_approved'] or 0) + (previous_data['prev_total_rejected'] or 0)
    prev_approval_rate = (previous_data['prev_total_approved'] or 0) / prev_processed * 100 if prev_processed > 0 else 0
    
    summary = {
        'total_requests': summary_data['total_requests'] or 0,
        'approval_rate': approval_rate,
        'avg_response_time': summary_data['avg_response_time'] or 0,
        'overdue_items': summary_data['total_overdue'] or 0,
        
        # Trends
        'approval_change': approval_rate - prev_approval_rate,
        'approval_trend': 'up' if approval_rate > prev_approval_rate else 'down' if approval_rate < prev_approval_rate else 'stable',
        'response_change': (summary_data['avg_response_time'] or 0) - (previous_data['prev_avg_response_time'] or 0),
        'response_trend': 'down' if (summary_data['avg_response_time'] or 0) < (previous_data['prev_avg_response_time'] or 0) else 'up' if (summary_data['avg_response_time'] or 0) > (previous_data['prev_avg_response_time'] or 0) else 'stable',
        'overdue_change': (summary_data['total_overdue'] or 0) - (previous_data['prev_total_overdue'] or 0),
        'overdue_trend': 'up' if (summary_data['total_overdue'] or 0) > (previous_data['prev_total_overdue'] or 0) else 'down' if (summary_data['total_overdue'] or 0) < (previous_data['prev_total_overdue'] or 0) else 'stable',
        'volume_change': (summary_data['total_requests'] or 0) - (previous_data['prev_total_requests'] or 0),
        'volume_trend': 'up' if (summary_data['total_requests'] or 0) > (previous_data['prev_total_requests'] or 0) else 'down' if (summary_data['total_requests'] or 0) < (previous_data['prev_total_requests'] or 0) else 'stable',
    }
    
    # Resource-level statistics
    resource_stats = []
    for stat in stats_qs.select_related('resource', 'approver'):
        total_requests = stat.access_requests_received
        approved = stat.access_requests_approved
        rejected = stat.access_requests_rejected
        processed = approved + rejected
        
        resource_stats.append({
            'resource_name': stat.resource.name,
            'approver_name': stat.approver.get_full_name() or stat.approver.username,
            'total_requests': total_requests,
            'approved': approved,
            'rejected': rejected,
            'approval_rate': (approved / processed * 100) if processed > 0 else 0,
            'avg_response_time': stat.avg_response_time_hours,
            'overdue': stat.overdue_items,
        })
    
    # Sort by total requests descending
    resource_stats.sort(key=lambda x: x['total_requests'], reverse=True)
    
    # Top performers (by approval rate and response time)
    top_performers = sorted(resource_stats, key=lambda x: (x['approval_rate'], -x['avg_response_time']), reverse=True)[:5]
    
    # Chart data for distribution
    distribution_labels = ['Approved', 'Rejected', 'Pending']
    distribution_data = [
        summary_data['total_approved'] or 0,
        summary_data['total_rejected'] or 0,
        summary_data['total_pending'] or 0
    ]
    
    # Timeline data for response time trend
    timeline_stats = stats_qs.order_by('period_start').values('period_start', 'avg_response_time_hours')
    timeline_labels = [stat['period_start'].strftime('%m/%d') for stat in timeline_stats]
    timeline_data = [stat['avg_response_time_hours'] for stat in timeline_stats]
    
    # Recent activity (mock data - in real implementation, this would come from audit logs)
    recent_activity = [
        {
            'description': 'New access request approved for Lab Equipment A',
            'timestamp': timezone.now() - timedelta(hours=2),
            'icon': 'check',
            'color': 'success'
        },
        {
            'description': 'Training session completed for Safety Protocol',
            'timestamp': timezone.now() - timedelta(hours=5),
            'icon': 'graduation-cap',
            'color': 'info'
        },
        {
            'description': 'Risk assessment reviewed for Chemical Lab',
            'timestamp': timezone.now() - timedelta(hours=8),
            'icon': 'shield-alt',
            'color': 'warning'
        },
    ]
    
    # Get all resources for filter dropdown
    resources = Resource.objects.all().order_by('name')
    
    # Handle CSV export
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="approval_statistics_{start_date}_to_{end_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Resource', 'Approver', 'Total Requests', 'Approved', 'Rejected', 
            'Approval Rate (%)', 'Avg Response Time (hours)', 'Overdue Items'
        ])
        
        for stat in resource_stats:
            writer.writerow([
                stat['resource_name'],
                stat['approver_name'],
                stat['total_requests'],
                stat['approved'],
                stat['rejected'],
                f"{stat['approval_rate']:.1f}",
                f"{stat['avg_response_time']:.1f}",
                stat['overdue']
            ])
        
        return response
    
    context = {
        'summary': summary,
        'resource_stats': resource_stats[:10],  # Limit to top 10 for display
        'top_performers': top_performers,
        'recent_activity': recent_activity,
        'resources': resources,
        
        # Chart data (convert to JSON for template)
        'distribution_labels': json.dumps(distribution_labels),
        'distribution_data': json.dumps(distribution_data),
        'timeline_labels': json.dumps(timeline_labels),
        'timeline_data': json.dumps(timeline_data),
    }
    
    return render(request, 'booking/approval_statistics.html', context)


@login_required
def approval_rules_view(request):
    """User-friendly approval rules management interface."""
    from .models import ApprovalRule
    import json
    
    # Only allow technicians and sysadmins to manage rules
    if not request.user.userprofile.role in ['technician', 'sysadmin']:
        messages.error(request, "You don't have permission to manage approval rules.")
        return redirect('booking:dashboard')
    
    # Get all rules with filters
    rules_qs = ApprovalRule.objects.all().select_related('resource', 'fallback_rule')
    
    # Apply filters
    type_filter = request.GET.get('type')
    resource_filter = request.GET.get('resource')
    search_filter = request.GET.get('search')
    
    if type_filter:
        rules_qs = rules_qs.filter(approval_type=type_filter)
    
    if resource_filter:
        rules_qs = rules_qs.filter(resource_id=resource_filter)
    
    if search_filter:
        rules_qs = rules_qs.filter(
            Q(name__icontains=search_filter) |
            Q(description__icontains=search_filter)
        )
    
    # Order by priority, then by created date
    rules_qs = rules_qs.order_by('priority', '-created_at')
    
    # Pagination
    paginator = Paginator(rules_qs, 10)
    page_number = request.GET.get('page')
    rules = paginator.get_page(page_number)
    
    # Calculate statistics
    stats = {
        'auto_rules': ApprovalRule.objects.filter(approval_type='auto').count(),
        'manual_rules': ApprovalRule.objects.filter(approval_type__in=['single', 'tiered']).count(),
        'conditional_rules': ApprovalRule.objects.filter(approval_type='conditional').count(),
        'active_rules': ApprovalRule.objects.filter(is_active=True).count(),
    }
    
    # Get resources for filters and creation
    resources = Resource.objects.all().order_by('name')
    
    # Get all rules for fallback options
    all_rules = ApprovalRule.objects.all().order_by('name')
    
    # Handle POST request for creating rule
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            approval_type = request.POST.get('approval_type')
            description = request.POST.get('description', '')
            resource_id = request.POST.get('resource')
            user_role = request.POST.get('user_role')
            priority = int(request.POST.get('priority', 100))
            fallback_rule_id = request.POST.get('fallback_rule')
            condition_type = request.POST.get('condition_type')
            conditional_logic_json = request.POST.get('conditional_logic')
            
            # Validate required fields
            if not all([name, approval_type]):
                messages.error(request, "Please fill in all required fields.")
                return redirect('booking:approval_rules')
            
            # Get related objects
            resource = None
            if resource_id:
                resource = get_object_or_404(Resource, id=resource_id)
            
            fallback_rule = None
            if fallback_rule_id:
                fallback_rule = get_object_or_404(ApprovalRule, id=fallback_rule_id)
            
            # Parse conditional logic
            conditional_logic = {}
            if approval_type == 'conditional' and conditional_logic_json:
                try:
                    conditional_logic = json.loads(conditional_logic_json)
                except json.JSONDecodeError:
                    conditional_logic = {}
            
            # Create approval rule
            rule = ApprovalRule.objects.create(
                name=name,
                approval_type=approval_type,
                description=description,
                resource=resource,
                user_role=user_role if user_role else None,
                priority=priority,
                fallback_rule=fallback_rule,
                condition_type=condition_type if approval_type == 'conditional' else 'role_based',
                conditional_logic=conditional_logic,
                is_active=True,
                created_by=request.user
            )
            
            messages.success(request, f"Approval rule '{name}' created successfully.")
            return redirect('booking:approval_rules')
            
        except Exception as e:
            messages.error(request, f"Error creating approval rule: {str(e)}")
            return redirect('booking:approval_rules')
    
    context = {
        'rules': rules,
        'stats': stats,
        'resources': resources,
        'all_rules': all_rules,
    }
    
    return render(request, 'booking/approval_rules.html', context)


@login_required
def approval_rule_toggle_view(request, rule_id):
    """Toggle approval rule active/inactive status."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    # Only allow technicians and sysadmins
    if not request.user.userprofile.role in ['technician', 'sysadmin']:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        import json
        
        rule = get_object_or_404(ApprovalRule, id=rule_id)
        
        data = json.loads(request.body)
        new_status = data.get('active', False)
        
        rule.is_active = new_status
        rule.save()
        
        return JsonResponse({
            'success': True, 
            'message': f"Rule {'enabled' if new_status else 'disabled'} successfully"
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# Lab Admin Views

@login_required
@user_passes_test(is_lab_admin)
def lab_admin_dashboard_view(request):
    """Lab Admin dashboard with overview of pending tasks."""
    from .models import AccessRequest, TrainingRequest, UserTraining, UserProfile
    from django.utils import timezone
    from datetime import timedelta
    
    # Get pending items
    pending_access_requests = AccessRequest.objects.filter(status='pending').count()
    pending_training_requests = TrainingRequest.objects.filter(status='pending').count()
    
    # Get upcoming training sessions
    upcoming_training = UserTraining.objects.filter(
        session_date__gte=timezone.now().date(),
        status='scheduled'
    ).count()
    
    # Get recent registrations (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_registrations = UserProfile.objects.filter(
        user__date_joined__gte=week_ago
    ).count()
    
    # Get overdue items
    overdue_access_requests = AccessRequest.objects.filter(
        status='pending',
        created_at__lt=timezone.now() - timedelta(days=3)
    ).count()
    
    context = {
        'pending_access_requests': pending_access_requests,
        'pending_training_requests': pending_training_requests,
        'upcoming_training': upcoming_training,
        'recent_registrations': recent_registrations,
        'overdue_access_requests': overdue_access_requests,
    }
    
    return render(request, 'booking/lab_admin_dashboard.html', context)


@login_required
@user_passes_test(is_lab_admin)
def lab_admin_access_requests_view(request):
    """Manage access requests."""
    from .models import AccessRequest
    
    # Handle status updates
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        
        if request_id and action:
            access_request = get_object_or_404(AccessRequest, id=request_id)
            
            if action == 'approve':
                try:
                    access_request.approve(request.user, "Approved via Lab Admin dashboard")
                    messages.success(request, f'Access request approved for {access_request.user.get_full_name()}')
                except ValueError as e:
                    messages.error(request, f'Error approving request: {str(e)}')
                except Exception as e:
                    messages.error(request, f'Unexpected error: {str(e)}')
                
            elif action == 'reject':
                try:
                    access_request.reject(request.user, "Rejected via Lab Admin dashboard")
                    messages.success(request, f'Access request rejected for {access_request.user.get_full_name()}')
                except ValueError as e:
                    messages.error(request, f'Error rejecting request: {str(e)}')
                except Exception as e:
                    messages.error(request, f'Unexpected error: {str(e)}')
        
        return redirect('booking:lab_admin_access_requests')
    
    # Get access requests
    access_requests = AccessRequest.objects.select_related(
        'user', 'resource', 'reviewed_by'
    ).order_by('-created_at')
    
    # Apply filters
    status_filter = request.GET.get('status', 'pending')
    if status_filter and status_filter != 'all':
        access_requests = access_requests.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(access_requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'access_requests': page_obj,
        'status_filter': status_filter,
    }
    
    return render(request, 'booking/lab_admin_access_requests.html', context)


@login_required
@user_passes_test(is_lab_admin)
def lab_admin_training_view(request):
    """Manage training requests and sessions."""
    from .models import TrainingRequest, UserTraining, TrainingCourse
    
    # Handle training request approval
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve_request':
            request_id = request.POST.get('request_id')
            training_request = get_object_or_404(TrainingRequest, id=request_id)
            
            training_request.status = 'approved'
            training_request.reviewed_by = request.user
            training_request.reviewed_at = timezone.now()
            training_request.save()
            
            messages.success(request, f'Training request approved for {training_request.user.get_full_name()}')
            
        elif action == 'schedule_training':
            user_training_id = request.POST.get('user_training_id')
            session_date = request.POST.get('session_date')
            
            if user_training_id and session_date:
                user_training = get_object_or_404(UserTraining, id=user_training_id)
                user_training.session_date = session_date
                user_training.instructor = request.user
                user_training.status = 'scheduled'
                user_training.save()
                
                messages.success(request, f'Training session scheduled for {user_training.user.get_full_name()}')
        
        return redirect('booking:lab_admin_training')
    
    # Get training data
    pending_requests = TrainingRequest.objects.filter(status='pending').select_related('user', 'resource', 'reviewed_by')
    upcoming_sessions = UserTraining.objects.filter(
        session_date__gte=timezone.now().date(),
        status='scheduled'
    ).select_related('user', 'training_course', 'instructor')
    
    context = {
        'pending_requests': pending_requests,
        'upcoming_sessions': upcoming_sessions,
    }
    
    return render(request, 'booking/lab_admin_training.html', context)


@login_required
@user_passes_test(is_lab_admin)
def lab_admin_users_view(request):
    """Manage user profiles and access."""
    from .models import UserProfile, ResourceAccess
    
    # Get users
    users = User.objects.select_related('userprofile').order_by('username')
    
    # Apply filters
    role_filter = request.GET.get('role')
    search_query = request.GET.get('search')
    
    if role_filter:
        users = users.filter(userprofile__role=role_filter)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get role choices for filter
    role_choices = UserProfile.ROLE_CHOICES
    
    context = {
        'users': page_obj,
        'role_filter': role_filter,
        'search_query': search_query,
        'role_choices': role_choices,
    }
    
    return render(request, 'booking/lab_admin_users.html', context)


@login_required
@user_passes_test(is_lab_admin)
def lab_admin_resources_view(request):
    """Manage resources - list, add, edit, delete."""
    from .models import Resource
    
    # Get resources
    resources = Resource.objects.all().order_by('name')
    
    # Apply filters
    resource_type_filter = request.GET.get('type')
    search_query = request.GET.get('search')
    status_filter = request.GET.get('status', 'all')
    
    if resource_type_filter:
        resources = resources.filter(resource_type=resource_type_filter)
    
    if search_query:
        resources = resources.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    if status_filter == 'active':
        resources = resources.filter(is_active=True)
    elif status_filter == 'inactive':
        resources = resources.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(resources, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get resource type choices for filter
    resource_types = Resource.RESOURCE_TYPES
    
    context = {
        'resources': page_obj,
        'resource_type_filter': resource_type_filter,
        'search_query': search_query,
        'status_filter': status_filter,
        'resource_types': resource_types,
    }
    
    return render(request, 'booking/lab_admin_resources.html', context)


@login_required
@user_passes_test(is_lab_admin)
def lab_admin_add_resource_view(request):
    """Add a new resource."""
    from .models import Resource
    from .forms import ResourceForm
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save()
            messages.success(request, f'Resource "{resource.name}" has been created successfully.')
            return redirect('booking:lab_admin_resources')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResourceForm()
    
    context = {
        'form': form,
        'title': 'Add New Resource',
        'action': 'Add',
    }
    
    return render(request, 'booking/lab_admin_resource_form.html', context)


@login_required
@user_passes_test(is_lab_admin)
def lab_admin_edit_resource_view(request, resource_id):
    """Edit an existing resource."""
    from .models import Resource
    from .forms import ResourceForm
    
    resource = get_object_or_404(Resource, id=resource_id)
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            resource = form.save()
            messages.success(request, f'Resource "{resource.name}" has been updated successfully.')
            return redirect('booking:lab_admin_resources')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResourceForm(instance=resource)
    
    context = {
        'form': form,
        'resource': resource,
        'title': f'Edit Resource: {resource.name}',
        'action': 'Update',
    }
    
    return render(request, 'booking/lab_admin_resource_form.html', context)


@login_required
@user_passes_test(is_lab_admin)
def lab_admin_delete_resource_view(request, resource_id):
    """Delete a resource with confirmation."""
    from .models import Resource
    
    resource = get_object_or_404(Resource, id=resource_id)
    
    if request.method == 'POST':
        # Check if resource has any bookings
        if resource.bookings.exists():
            messages.error(request, f'Cannot delete "{resource.name}" because it has existing bookings. Please deactivate it instead.')
            return redirect('booking:lab_admin_resources')
        
        resource_name = resource.name
        resource.delete()
        messages.success(request, f'Resource "{resource_name}" has been deleted successfully.')
        return redirect('booking:lab_admin_resources')
    
    # Check dependencies
    booking_count = resource.bookings.count()
    access_count = resource.access_permissions.count()
    
    context = {
        'resource': resource,
        'booking_count': booking_count,
        'access_count': access_count,
        'can_delete': booking_count == 0,
    }
    
    return render(request, 'booking/lab_admin_resource_delete.html', context)


@login_required
@user_passes_test(is_lab_admin)
def lab_admin_maintenance_view(request):
    """Display and manage maintenance periods for lab administrators."""
    from django.core.paginator import Paginator
    from django.utils import timezone
    
    # Get filter parameters
    resource_filter = request.GET.get('resource', '')
    type_filter = request.GET.get('type', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    maintenance_list = Maintenance.objects.select_related('resource', 'created_by').order_by('-start_time')
    
    # Apply filters
    if resource_filter:
        maintenance_list = maintenance_list.filter(resource_id=resource_filter)
    
    if type_filter:
        maintenance_list = maintenance_list.filter(maintenance_type=type_filter)
    
    if search_query:
        maintenance_list = maintenance_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(resource__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(maintenance_list, 25)
    page_number = request.GET.get('page')
    maintenance_periods = paginator.get_page(page_number)
    
    # Statistics
    now = timezone.now()
    stats = {
        'scheduled_count': Maintenance.objects.filter(start_time__gt=now).count(),
        'active_count': Maintenance.objects.filter(start_time__lte=now, end_time__gte=now).count(),
        'completed_count': Maintenance.objects.filter(
            end_time__lt=now,
            start_time__month=now.month,
            start_time__year=now.year
        ).count(),
        'recurring_count': Maintenance.objects.filter(is_recurring=True).count(),
    }
    
    # Get all resources for filtering
    resources = Resource.objects.filter(is_active=True).order_by('name')
    
    context = {
        'maintenance_periods': maintenance_periods,
        'resources': resources,
        'stats': stats,
        'resource_filter': resource_filter,
        'type_filter': type_filter,
        'search_query': search_query,
    }
    
    return render(request, 'booking/lab_admin_maintenance.html', context)


@login_required
@user_passes_test(is_lab_admin)
def lab_admin_add_maintenance_view(request):
    """Add a new maintenance period."""
    import json
    from django.utils.dateparse import parse_datetime
    
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title')
            resource_id = request.POST.get('resource')
            description = request.POST.get('description', '')
            start_time = parse_datetime(request.POST.get('start_time'))
            end_time = parse_datetime(request.POST.get('end_time'))
            maintenance_type = request.POST.get('maintenance_type')
            blocks_booking = request.POST.get('blocks_booking') == 'on'
            is_recurring = request.POST.get('is_recurring') == 'on'
            
            # Validation
            if not all([title, resource_id, start_time, end_time, maintenance_type]):
                return JsonResponse({'success': False, 'error': 'All required fields must be filled'})
            
            if end_time <= start_time:
                return JsonResponse({'success': False, 'error': 'End time must be after start time'})
            
            resource = get_object_or_404(Resource, id=resource_id)
            
            # Handle recurring pattern
            recurring_pattern = None
            if is_recurring and request.POST.get('recurring_pattern'):
                recurring_pattern = json.loads(request.POST.get('recurring_pattern'))
            
            # Create maintenance
            maintenance = Maintenance.objects.create(
                resource=resource,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                maintenance_type=maintenance_type,
                blocks_booking=blocks_booking,
                is_recurring=is_recurring,
                recurring_pattern=recurring_pattern,
                created_by=request.user
            )
            
            return JsonResponse({'success': True, 'message': 'Maintenance period scheduled successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@user_passes_test(is_lab_admin)
def lab_admin_edit_maintenance_view(request, maintenance_id):
    """Edit or view an existing maintenance period."""
    maintenance = get_object_or_404(Maintenance, id=maintenance_id)
    
    if request.method == 'GET':
        # Return maintenance data for viewing/editing
        maintenance_data = {
            'id': maintenance.id,
            'title': maintenance.title,
            'description': maintenance.description,
            'resource_id': maintenance.resource.id,
            'resource_name': maintenance.resource.name,
            'start_time': maintenance.start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': maintenance.end_time.strftime('%Y-%m-%dT%H:%M'),
            'maintenance_type': maintenance.maintenance_type,
            'blocks_booking': maintenance.blocks_booking,
            'is_recurring': maintenance.is_recurring,
            'recurring_pattern': maintenance.recurring_pattern,
            'created_by': maintenance.created_by.get_full_name() or maintenance.created_by.username,
            'created_at': maintenance.created_at.strftime('%Y-%m-%d %H:%M'),
        }
        
        # Generate HTML for view modal
        from django.template.loader import render_to_string
        html = render_to_string('booking/maintenance_detail.html', {'maintenance': maintenance}, request=request)
        
        return JsonResponse({
            'success': True,
            'maintenance': maintenance_data,
            'html': html
        })
    
    elif request.method == 'POST':
        # Update maintenance
        try:
            from django.utils.dateparse import parse_datetime
            
            maintenance.title = request.POST.get('title')
            maintenance.description = request.POST.get('description', '')
            maintenance.start_time = parse_datetime(request.POST.get('start_time'))
            maintenance.end_time = parse_datetime(request.POST.get('end_time'))
            maintenance.maintenance_type = request.POST.get('maintenance_type')
            maintenance.blocks_booking = request.POST.get('blocks_booking') == 'on'
            
            # Validation
            if maintenance.end_time <= maintenance.start_time:
                return JsonResponse({'success': False, 'error': 'End time must be after start time'})
            
            # Update resource if changed
            resource_id = request.POST.get('resource')
            if resource_id and str(maintenance.resource.id) != resource_id:
                maintenance.resource = get_object_or_404(Resource, id=resource_id)
            
            maintenance.save()
            
            return JsonResponse({'success': True, 'message': 'Maintenance period updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@user_passes_test(is_lab_admin)
def lab_admin_delete_maintenance_view(request, maintenance_id):
    """Delete a maintenance period."""
    maintenance = get_object_or_404(Maintenance, id=maintenance_id)
    
    if request.method == 'POST':
        try:
            maintenance_title = maintenance.title
            maintenance.delete()
            return JsonResponse({'success': True, 'message': f'Maintenance period "{maintenance_title}" deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def download_booking_invitation(request, booking_id):
    """Download a calendar invitation for a specific booking."""
    from .calendar_sync import ICSCalendarGenerator, create_ics_response
    from .models import Booking
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check permissions - user must be the booking owner or have admin access
    if not (booking.user == request.user or 
            request.user.userprofile.role in ['technician', 'sysadmin'] or
            request.user.groups.filter(name='Lab Admin').exists()):
        messages.error(request, "You don't have permission to download this booking invitation.")
        return redirect('booking:my_bookings')
    
    # Generate ICS invitation
    generator = ICSCalendarGenerator(request)
    ics_content = generator.generate_booking_invitation(booking)
    
    # Create filename
    safe_title = booking.title.replace(' ', '-').replace('/', '-')
    filename = f"booking-{safe_title}-{booking.start_time.strftime('%Y%m%d')}.ics"
    
    return create_ics_response(ics_content, filename)


@login_required
@user_passes_test(is_lab_admin)
def download_maintenance_invitation(request, maintenance_id):
    """Download a calendar invitation for a specific maintenance period."""
    from .calendar_sync import ICSCalendarGenerator, create_ics_response
    from .models import Maintenance
    
    maintenance = get_object_or_404(Maintenance, id=maintenance_id)
    
    # Generate ICS invitation
    generator = ICSCalendarGenerator(request)
    ics_content = generator.generate_maintenance_invitation(maintenance)
    
    # Create filename
    safe_title = maintenance.title.replace(' ', '-').replace('/', '-')
    filename = f"maintenance-{safe_title}-{maintenance.start_time.strftime('%Y%m%d')}.ics"
    
    return create_ics_response(ics_content, filename)


@login_required
def export_my_calendar_view(request):
    """Export user's bookings as ICS file for download."""
    from .calendar_sync import ICSCalendarGenerator, create_ics_response
    
    # Get parameters
    include_past = request.GET.get('include_past', 'false').lower() == 'true'
    days_ahead = int(request.GET.get('days_ahead', '90'))
    
    # Generate ICS
    generator = ICSCalendarGenerator(request)
    ics_content = generator.generate_user_calendar(
        user=request.user,
        include_past=include_past,
        days_ahead=days_ahead
    )
    
    # Create filename
    user_name = request.user.get_full_name() or request.user.username
    filename = f"my-bookings-{user_name.replace(' ', '-').lower()}.ics"
    
    return create_ics_response(ics_content, filename)


@login_required
def my_calendar_feed_view(request, token):
    """Provide ICS calendar feed for subscription (with token authentication)."""
    from .calendar_sync import ICSCalendarGenerator, CalendarTokenGenerator, create_ics_feed_response
    
    # Verify token
    if not CalendarTokenGenerator.verify_user_token(request.user, token):
        return HttpResponse("Invalid token", status=403)
    
    # Get parameters
    include_past = request.GET.get('include_past', 'false').lower() == 'true'
    days_ahead = int(request.GET.get('days_ahead', '90'))
    
    # Generate ICS
    generator = ICSCalendarGenerator(request)
    ics_content = generator.generate_user_calendar(
        user=request.user,
        include_past=include_past,
        days_ahead=days_ahead
    )
    
    return create_ics_feed_response(ics_content)


def public_calendar_feed_view(request, token):
    """Provide public ICS calendar feed for subscription (token-based, no login required)."""
    from .calendar_sync import ICSCalendarGenerator, CalendarTokenGenerator, create_ics_feed_response
    from django.contrib.auth.models import User
    
    # Find user by token
    user = None
    for u in User.objects.filter(is_active=True):
        if CalendarTokenGenerator.verify_user_token(u, token):
            user = u
            break
    
    if not user:
        return HttpResponse("Invalid token", status=403)
    
    # Get parameters
    include_past = request.GET.get('include_past', 'false').lower() == 'true'
    days_ahead = int(request.GET.get('days_ahead', '90'))
    
    # Generate ICS
    generator = ICSCalendarGenerator(request)
    ics_content = generator.generate_user_calendar(
        user=user,
        include_past=include_past,
        days_ahead=days_ahead
    )
    
    return create_ics_feed_response(ics_content)


@login_required
def export_resource_calendar_view(request, resource_id):
    """Export resource bookings as ICS file for download."""
    from .calendar_sync import ICSCalendarGenerator, create_ics_response
    
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check permissions - only allow if user has access to the resource or is admin
    if not (request.user.userprofile.role in ['technician', 'sysadmin'] or 
            resource.resourceaccess_set.filter(user=request.user, is_active=True).exists()):
        messages.error(request, "You don't have permission to export this resource's calendar.")
        return redirect('booking:resource_detail', resource_id=resource_id)
    
    # Get parameters
    days_ahead = int(request.GET.get('days_ahead', '90'))
    
    # Generate ICS
    generator = ICSCalendarGenerator(request)
    ics_content = generator.generate_resource_calendar(
        resource=resource,
        days_ahead=days_ahead
    )
    
    # Create filename
    filename = f"{resource.name.replace(' ', '-').lower()}-calendar.ics"
    
    return create_ics_response(ics_content, filename)


@login_required
def calendar_sync_settings_view(request):
    """Display calendar synchronization settings and subscription URLs."""
    from .calendar_sync import CalendarTokenGenerator
    
    # Generate user's calendar token
    user_token = CalendarTokenGenerator.generate_user_token(request.user)
    
    # Build subscription URLs
    feed_url = request.build_absolute_uri(
        reverse('booking:public_calendar_feed', kwargs={'token': user_token})
    )
    
    export_url = request.build_absolute_uri(
        reverse('booking:export_my_calendar')
    )
    
    # Get user's resources for resource calendar export
    user_resources = Resource.objects.filter(
        Q(responsible_persons__user=request.user) |
        Q(resourceaccess__user=request.user, resourceaccess__is_active=True)
    ).distinct().order_by('name')
    
    context = {
        'user_token': user_token,
        'feed_url': feed_url,
        'export_url': export_url,
        'user_resources': user_resources,
    }
    
    return render(request, 'booking/calendar_sync_settings.html', context)


def about_page_view(request):
    """Display the about page with configurable content."""
    about_page = AboutPage.get_active()
    
    context = {
        'about_page': about_page,
    }
    
    return render(request, 'booking/about.html', context)


@user_passes_test(lambda u: u.is_staff or (hasattr(u, 'userprofile') and u.userprofile.role in ['technician', 'sysadmin']))
def about_page_edit_view(request):
    """Edit the about page with WYSIWYG editor."""
    about_page = AboutPage.get_active()
    
    if request.method == 'POST':
        form = AboutPageEditForm(request.POST, request.FILES, instance=about_page)
        if form.is_valid():
            about_page = form.save()
            messages.success(request, 'About page has been updated successfully.')
            return redirect('booking:about')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AboutPageEditForm(instance=about_page)
    
    context = {
        'form': form,
        'about_page': about_page,
        'is_new': about_page is None,
    }
    
    return render(request, 'booking/about_edit.html', context)


class CustomLoginView(LoginView):
    """Custom login view that handles first login redirect logic."""
    
    def get_success_url(self):
        """Redirect to about page on first login, dashboard on subsequent logins."""
        user = self.request.user
        
        try:
            profile = user.userprofile
            
            # Check if this is the user's first login
            if profile.first_login is None:
                # Mark the first login time
                profile.first_login = timezone.now()
                profile.save()
                
                # Redirect to about page for first-time users
                return '/about/'
            else:
                # Redirect to dashboard for returning users
                return '/dashboard/'
                
        except UserProfile.DoesNotExist:
            # If no profile exists, redirect to about page
            return '/about/'


