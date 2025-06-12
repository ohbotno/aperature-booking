# booking/views.py
"""
API views for the Lab Booking System.

This file is part of the Lab Booking System.
Copyright (C) 2025 Lab Booking System Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from .models import UserProfile, Resource, Booking, ApprovalRule, Maintenance, EmailVerificationToken, PasswordResetToken, BookingTemplate
from .forms import UserRegistrationForm, UserProfileForm, CustomPasswordResetForm, CustomSetPasswordForm, BookingForm, RecurringBookingForm, BookingTemplateForm, CreateBookingFromTemplateForm, SaveAsTemplateForm
from .recurring import RecurringBookingGenerator, RecurringBookingManager
from .conflicts import ConflictDetector, ConflictResolver, ConflictManager
from .serializers import (
    UserProfileSerializer, ResourceSerializer, BookingSerializer,
    ApprovalRuleSerializer, MaintenanceSerializer
)


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
                   user_profile.role in ['lab_manager', 'sysadmin'])
        
        return obj.user == request.user


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
            if user_profile.role in ['lab_manager', 'sysadmin']:
                return UserProfile.objects.all()
            else:
                # Regular users can only see their own profile and group members
                return UserProfile.objects.filter(
                    Q(user=user) | Q(group=user_profile.group)
                )
        except UserProfile.DoesNotExist:
            return UserProfile.objects.filter(user=user)


class ResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for resources."""
    queryset = Resource.objects.filter(is_active=True)
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
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
            if user_profile.role in ['lab_manager', 'sysadmin']:
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
            queryset = queryset.filter(
                start_time__gte=start_date,
                end_time__lte=end_date
            )
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('start_time')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a booking."""
        booking = self.get_object()
        user_profile = request.user.userprofile
        
        if user_profile.role not in ['lab_manager', 'sysadmin']:
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
        
        if user_profile.role not in ['lab_manager', 'sysadmin']:
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
                    'resource': booking.resource.name,
                    'user': booking.user.get_full_name(),
                    'status': booking.status,
                    'description': booking.description,
                }
            })
        
        return Response(events)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get booking statistics."""
        user_profile = request.user.userprofile
        
        if user_profile.role not in ['lab_manager', 'sysadmin']:
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
            queryset = queryset.filter(
                start_time__gte=start_date,
                end_time__lte=end_date
            )
        
        return queryset.order_by('start_time')


# Template views
def register_view(request):
    """User registration view."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, 
                'Registration successful! Please check your email to verify your account before logging in.'
            )
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
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
    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.save()
            
            messages.success(request, f'Booking "{booking.title}" created successfully.')
            return redirect('booking:booking_detail', pk=booking.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookingForm(user=request.user)
    
    return render(request, 'booking/create_booking.html', {'form': form})


@login_required
def booking_detail_view(request, pk):
    """View booking details."""
    booking = get_object_or_404(Booking, pk=pk)
    
    # Check permissions
    try:
        user_profile = request.user.userprofile
        if (booking.user != request.user and 
            user_profile.role not in ['lab_manager', 'sysadmin'] and
            not booking.shared_with_group):
            messages.error(request, 'You do not have permission to view this booking.')
            return redirect('booking:dashboard')
    except UserProfile.DoesNotExist:
        if booking.user != request.user:
            messages.error(request, 'You do not have permission to view this booking.')
            return redirect('booking:dashboard')
    
    # Get recurring series if applicable
    recurring_series = None
    if booking.is_recurring:
        recurring_series = RecurringBookingManager.get_recurring_series(booking)
    
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
            user_profile.role not in ['lab_manager', 'sysadmin']):
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
        if user_profile.role not in ['lab_manager', 'sysadmin']:
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
        if user_profile.role not in ['lab_manager', 'sysadmin']:
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
        if user_profile.role not in ['lab_manager', 'sysadmin']:
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
def profile_view(request):
    """User profile management view."""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=profile)
    
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
    user_bookings = Booking.objects.filter(user=request.user).order_by('start_time')[:5]
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