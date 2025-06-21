# booking/checklist_service.py
"""
Checklist service for equipment checkout/checkin validation and completion logic.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperture-booking.org/commercial
"""

from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
import json
from typing import Dict, List, Optional, Tuple, Any
from .models import (
    ChecklistTemplate, ChecklistItem, ChecklistCompletion, 
    ChecklistItemCompletion, Booking, Resource
)


class ChecklistValidationError(Exception):
    """Custom exception for checklist validation errors."""
    pass


class ChecklistService:
    """Service class for handling checklist operations."""
    
    def get_applicable_templates(self, resource: Resource, template_type: str = 'both') -> List[ChecklistTemplate]:
        """
        Get all applicable checklist templates for a resource.
        
        Args:
            resource: The resource to get templates for
            template_type: Filter by template type ('checkout', 'checkin', 'both')
        
        Returns:
            List of applicable checklist templates
        """
        queryset = ChecklistTemplate.objects.filter(
            resource=resource,
            is_active=True
        )
        
        # Filter by template type if not 'both'
        if template_type != 'both':
            queryset = queryset.filter(
                template_type__in=[template_type, 'both']
            )
        
        # Check date validity
        now = timezone.now()
        valid_templates = []
        
        for template in queryset:
            if template.is_valid_for_date(now):
                valid_templates.append(template)
        
        return sorted(valid_templates, key=lambda t: (t.is_mandatory, t.name))
    
    def create_checklist_completion(
        self, 
        template: ChecklistTemplate, 
        user: User, 
        booking: Optional[Booking] = None,
        completion_type: str = 'checkout',
        due_date: Optional[timezone.datetime] = None
    ) -> ChecklistCompletion:
        """
        Create a new checklist completion instance.
        
        Args:
            template: The checklist template to use
            user: User completing the checklist
            booking: Associated booking (optional)
            completion_type: Type of completion
            due_date: When completion is due (optional)
        
        Returns:
            Created ChecklistCompletion instance
        """
        # Calculate due date if not provided
        if not due_date and template.time_limit_minutes:
            due_date = timezone.now() + timezone.timedelta(
                minutes=template.time_limit_minutes
            )
        
        completion = ChecklistCompletion.objects.create(
            template=template,
            booking=booking,
            user=user,
            completion_type=completion_type,
            due_date=due_date,
            status='not_started'
        )
        
        return completion
    
    def start_checklist(self, completion: ChecklistCompletion) -> ChecklistCompletion:
        """
        Start a checklist completion.
        
        Args:
            completion: The checklist completion to start
        
        Returns:
            Updated ChecklistCompletion instance
        """
        completion.start_completion()
        return completion
    
    def get_checklist_items(
        self, 
        completion: ChecklistCompletion, 
        previous_responses: Optional[Dict[str, Any]] = None
    ) -> List[ChecklistItem]:
        """
        Get checklist items that should be displayed based on conditional logic.
        
        Args:
            completion: The checklist completion
            previous_responses: Dict of previous responses for conditional logic
        
        Returns:
            List of checklist items to display
        """
        all_items = completion.template.get_active_items()
        
        if not previous_responses:
            previous_responses = {}
        
        displayed_items = []
        
        for item in all_items:
            if item.should_display(previous_responses):
                displayed_items.append(item)
        
        return displayed_items
    
    def validate_response(
        self, 
        item: ChecklistItem, 
        response: Any, 
        file_upload=None
    ) -> Tuple[bool, List[str]]:
        """
        Validate a single checklist item response.
        
        Args:
            item: The checklist item
            response: The response value
            file_upload: File upload (if applicable)
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = item.get_validation_errors(response)
        
        # Additional file validation for certain types
        if item.item_type == 'photo' and item.is_required and not file_upload:
            errors.append("Photo upload is required for this item.")
        
        if item.item_type == 'signature' and item.is_required and not response:
            errors.append("Digital signature is required for this item.")
        
        return len(errors) == 0, errors
    
    def save_item_response(
        self, 
        completion: ChecklistCompletion,
        item: ChecklistItem,
        response: Any,
        file_upload=None,
        issue_description: str = "",
        issue_severity: str = "low"
    ) -> ChecklistItemCompletion:
        """
        Save a response for a checklist item.
        
        Args:
            completion: The checklist completion
            item: The checklist item
            response: The response value
            file_upload: File upload (if applicable)
            issue_description: Description of any issue identified
            issue_severity: Severity of the issue
        
        Returns:
            Created or updated ChecklistItemCompletion instance
        """
        # Get or create item completion
        item_completion, created = ChecklistItemCompletion.objects.get_or_create(
            checklist_completion=completion,
            checklist_item=item,
            defaults={
                'response': str(response) if response is not None else '',
                'file_upload': file_upload
            }
        )
        
        if not created:
            # Update existing
            item_completion.response = str(response) if response is not None else ''
            if file_upload:
                item_completion.file_upload = file_upload
        
        # Validate response
        is_valid, errors = self.validate_response(item, response, file_upload)
        item_completion.validation_errors = errors
        item_completion.is_valid = is_valid
        
        # Handle issues
        if issue_description:
            item_completion.mark_issue(issue_description, issue_severity)
        
        item_completion.save()
        
        return item_completion
    
    def get_completion_status(self, completion: ChecklistCompletion) -> Dict[str, Any]:
        """
        Get detailed status information for a checklist completion.
        
        Args:
            completion: The checklist completion
        
        Returns:
            Dictionary with status information
        """
        total_items = completion.template.get_active_items().count()
        completed_items = completion.item_completions.exclude(response__exact='').count()
        
        return {
            'total_items': total_items,
            'completed_items': completed_items,
            'completion_percentage': completion.get_completion_percentage(),
            'has_issues': completion.has_issues,
            'issues_count': completion.get_issues_count(),
            'is_overdue': completion.is_overdue(),
            'status': completion.status,
            'can_complete': completed_items == total_items and completion.status == 'in_progress'
        }
    
    def complete_checklist(
        self, 
        completion: ChecklistCompletion,
        user_signature: str = "",
        ip_address: str = "",
        user_agent: str = ""
    ) -> ChecklistCompletion:
        """
        Complete a checklist if all required items are filled.
        
        Args:
            completion: The checklist completion
            user_signature: Digital signature data
            ip_address: IP address of the user
            user_agent: User agent string
        
        Returns:
            Updated ChecklistCompletion instance
        
        Raises:
            ChecklistValidationError: If checklist cannot be completed
        """
        status = self.get_completion_status(completion)
        
        if not status['can_complete']:
            raise ChecklistValidationError(
                "Cannot complete checklist: not all required items are filled or checklist is not in progress."
            )
        
        # Check for unresolved critical issues
        critical_issues = completion.item_completions.filter(
            has_issue=True,
            issue_severity='critical',
            issue_resolved=False
        ).count()
        
        if critical_issues > 0:
            raise ChecklistValidationError(
                f"Cannot complete checklist: {critical_issues} critical issues must be resolved first."
            )
        
        # Save metadata
        completion.user_signature = user_signature
        completion.ip_address = ip_address
        completion.user_agent = user_agent
        
        # Complete the checklist
        completion.complete_checklist()
        
        return completion
    
    def approve_checklist(
        self, 
        completion: ChecklistCompletion,
        approver: User,
        notes: str = ""
    ) -> ChecklistCompletion:
        """
        Approve a completed checklist.
        
        Args:
            completion: The checklist completion
            approver: User approving the checklist
            notes: Approval notes
        
        Returns:
            Updated ChecklistCompletion instance
        """
        if completion.status != 'completed':
            raise ChecklistValidationError("Only completed checklists can be approved.")
        
        completion.approve_checklist(approver, notes)
        return completion
    
    def reject_checklist(
        self, 
        completion: ChecklistCompletion,
        approver: User,
        reason: str
    ) -> ChecklistCompletion:
        """
        Reject a completed checklist.
        
        Args:
            completion: The checklist completion
            approver: User rejecting the checklist
            reason: Rejection reason
        
        Returns:
            Updated ChecklistCompletion instance
        """
        if completion.status != 'completed':
            raise ChecklistValidationError("Only completed checklists can be rejected.")
        
        completion.reject_checklist(approver, reason)
        return completion
    
    def escalate_checklist(
        self, 
        completion: ChecklistCompletion,
        escalated_to: User,
        reason: str
    ) -> ChecklistCompletion:
        """
        Escalate a checklist due to issues.
        
        Args:
            completion: The checklist completion
            escalated_to: User to escalate to
            reason: Escalation reason
        
        Returns:
            Updated ChecklistCompletion instance
        """
        completion.escalate_checklist(escalated_to, reason)
        return completion
    
    def get_pending_approvals(self, user: User) -> List[ChecklistCompletion]:
        """
        Get checklists pending approval for a user.
        
        Args:
            user: User to get pending approvals for
        
        Returns:
            List of ChecklistCompletion instances pending approval
        """
        # Get resources the user is responsible for
        from .models import ResourceResponsible
        
        responsible_resources = ResourceResponsible.objects.filter(
            user=user,
            is_active=True
        ).values_list('resource', flat=True)
        
        return ChecklistCompletion.objects.filter(
            template__resource__in=responsible_resources,
            status='completed'
        ).order_by('completed_at')
    
    def get_overdue_checklists(self) -> List[ChecklistCompletion]:
        """
        Get all overdue checklist completions.
        
        Returns:
            List of overdue ChecklistCompletion instances
        """
        now = timezone.now()
        return ChecklistCompletion.objects.filter(
            due_date__lt=now,
            status__in=['not_started', 'in_progress']
        ).select_related('template', 'user', 'booking')
    
    def get_checklist_analytics(
        self, 
        resource: Optional[Resource] = None,
        start_date: Optional[timezone.datetime] = None,
        end_date: Optional[timezone.datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics data for checklists.
        
        Args:
            resource: Filter by resource (optional)
            start_date: Start date for analytics (optional)
            end_date: End date for analytics (optional)
        
        Returns:
            Dictionary with analytics data
        """
        queryset = ChecklistCompletion.objects.all()
        
        if resource:
            queryset = queryset.filter(template__resource=resource)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        total_completions = queryset.count()
        
        if total_completions == 0:
            return {
                'total_completions': 0,
                'completion_rate': 0,
                'average_completion_time': 0,
                'issue_rate': 0,
                'approval_rate': 0,
                'overdue_rate': 0
            }
        
        # Calculate metrics
        completed = queryset.filter(status__in=['completed', 'approved']).count()
        with_issues = queryset.filter(has_issues=True).count()
        approved = queryset.filter(status='approved').count()
        overdue = queryset.filter(
            due_date__lt=timezone.now(),
            status__in=['not_started', 'in_progress']
        ).count()
        
        # Average completion time (for completed checklists)
        completed_with_time = queryset.filter(
            completion_time_seconds__isnull=False
        )
        
        if completed_with_time.exists():
            avg_time = completed_with_time.aggregate(
                avg_time=models.Avg('completion_time_seconds')
            )['avg_time']
            avg_time_minutes = avg_time / 60 if avg_time else 0
        else:
            avg_time_minutes = 0
        
        return {
            'total_completions': total_completions,
            'completion_rate': (completed / total_completions) * 100,
            'average_completion_time_minutes': round(avg_time_minutes, 2),
            'issue_rate': (with_issues / total_completions) * 100,
            'approval_rate': (approved / completed) * 100 if completed > 0 else 0,
            'overdue_rate': (overdue / total_completions) * 100
        }
    
    def create_checklist_from_booking(
        self, 
        booking: Booking, 
        completion_type: str = 'checkout'
    ) -> List[ChecklistCompletion]:
        """
        Create checklist completions for a booking based on resource templates.
        
        Args:
            booking: The booking to create checklists for
            completion_type: Type of completion ('checkout' or 'checkin')
        
        Returns:
            List of created ChecklistCompletion instances
        """
        templates = self.get_applicable_templates(booking.resource, completion_type)
        completions = []
        
        for template in templates:
            if template.is_mandatory:
                completion = self.create_checklist_completion(
                    template=template,
                    user=booking.user,
                    booking=booking,
                    completion_type=completion_type,
                    due_date=booking.end_time if completion_type == 'checkout' else None
                )
                completions.append(completion)
        
        return completions
    
    def bulk_approve_checklists(
        self, 
        completion_ids: List[int], 
        approver: User, 
        notes: str = ""
    ) -> Tuple[int, List[str]]:
        """
        Bulk approve multiple checklists.
        
        Args:
            completion_ids: List of checklist completion IDs
            approver: User approving the checklists
            notes: Approval notes
        
        Returns:
            Tuple of (approved_count, error_messages)
        """
        approved_count = 0
        errors = []
        
        for completion_id in completion_ids:
            try:
                completion = ChecklistCompletion.objects.get(id=completion_id)
                self.approve_checklist(completion, approver, notes)
                approved_count += 1
            except ChecklistCompletion.DoesNotExist:
                errors.append(f"Checklist completion {completion_id} not found")
            except ChecklistValidationError as e:
                errors.append(f"Checklist {completion_id}: {str(e)}")
            except Exception as e:
                errors.append(f"Checklist {completion_id}: Unexpected error - {str(e)}")
        
        return approved_count, errors


# Global service instance
checklist_service = ChecklistService()