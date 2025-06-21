# booking/management/commands/calculate_utilization_trends.py
"""
Management command to calculate resource utilization trends.

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
from django.utils import timezone
from datetime import datetime, timedelta
from booking.utilization_service import utilization_service
from booking.models import Resource


class Command(BaseCommand):
    help = 'Calculate resource utilization trends for analytics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--resource-id',
            type=int,
            help='Specific resource ID to analyze'
        )
        
        parser.add_argument(
            '--period-type',
            type=str,
            choices=['hourly', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'],
            default='daily',
            help='Period type for trend analysis'
        )
        
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date for analysis (YYYY-MM-DD format)'
        )
        
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for analysis (YYYY-MM-DD format)'
        )
        
        parser.add_argument(
            '--days-back',
            type=int,
            help='Number of days to go back from today (alternative to start-date)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recalculation of existing trends'
        )
        
        parser.add_argument(
            '--resource-type',
            type=str,
            help='Filter resources by type (equipment, room, facility, service)'
        )
        
        parser.add_argument(
            '--location',
            type=str,
            help='Filter resources by location'
        )
        
        parser.add_argument(
            '--active-only',
            action='store_true',
            default=True,
            help='Only analyze active resources (default: True)'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of resources to process in each batch'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        """Main command handler."""
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        
        self.stdout.write(
            self.style.SUCCESS('Starting utilization trend calculation...')
        )
        
        # Parse command line options
        resource_id = options.get('resource_id')
        period_type = options.get('period_type')
        start_date = self._parse_date(options.get('start_date'))
        end_date = self._parse_date(options.get('end_date'))
        days_back = options.get('days_back')
        force_recalculate = options.get('force', False)
        resource_type = options.get('resource_type')
        location = options.get('location')
        active_only = options.get('active_only', True)
        batch_size = options.get('batch_size', 10)
        
        # Set default date range if not provided
        if not end_date:
            end_date = timezone.now()
        
        if not start_date:
            if days_back:
                start_date = end_date - timedelta(days=days_back)
            else:
                # Default lookback based on period type
                default_days = {
                    'hourly': 7,
                    'daily': 90,
                    'weekly': 365,
                    'monthly': 730,
                    'quarterly': 1095,
                    'yearly': 1825
                }
                start_date = end_date - timedelta(days=default_days.get(period_type, 90))
        
        if self.verbose:
            self.stdout.write(f"Analysis period: {start_date} to {end_date}")
            self.stdout.write(f"Period type: {period_type}")
            self.stdout.write(f"Force recalculate: {force_recalculate}")
        
        # Get resources to analyze
        resources = self._get_resources(
            resource_id, resource_type, location, active_only
        )
        
        if not resources:
            self.stdout.write(
                self.style.WARNING('No resources found matching criteria.')
            )
            return
        
        self.stdout.write(f"Found {len(resources)} resources to analyze")
        
        # Process resources in batches
        total_processed = 0
        total_created = 0
        total_updated = 0
        errors = 0
        
        for i in range(0, len(resources), batch_size):
            batch = resources[i:i + batch_size]
            
            if self.verbose:
                self.stdout.write(f"Processing batch {i//batch_size + 1}...")
            
            for resource in batch:
                try:
                    if self.verbose:
                        self.stdout.write(f"  Analyzing resource: {resource.name}")
                    
                    # Calculate trends for this resource
                    results = utilization_service.calculate_utilization_trends(
                        resource=resource,
                        period_type=period_type,
                        start_date=start_date,
                        end_date=end_date,
                        force_recalculate=force_recalculate
                    )
                    
                    total_processed += 1
                    total_created += results['created_trends']
                    total_updated += results['updated_trends']
                    
                    if self.verbose:
                        self.stdout.write(
                            f"    Created: {results['created_trends']}, "
                            f"Updated: {results['updated_trends']}"
                        )
                    
                except Exception as e:
                    errors += 1
                    self.stderr.write(
                        self.style.ERROR(
                            f"Error processing resource {resource.name}: {str(e)}"
                        )
                    )
                    if self.verbose:
                        import traceback
                        self.stderr.write(traceback.format_exc())
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nUtilization trend calculation completed!'
            )
        )
        self.stdout.write(f'Resources processed: {total_processed}')
        self.stdout.write(f'Trends created: {total_created}')
        self.stdout.write(f'Trends updated: {total_updated}')
        
        if errors:
            self.stdout.write(
                self.style.WARNING(f'Errors encountered: {errors}')
            )
        
        # Show recommendations for high/low utilization
        self._show_utilization_insights(period_type)
    
    def _parse_date(self, date_string):
        """Parse date string in YYYY-MM-DD format."""
        if not date_string:
            return None
        
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').replace(
                tzinfo=timezone.get_current_timezone()
            )
        except ValueError:
            self.stderr.write(
                self.style.ERROR(f'Invalid date format: {date_string}. Use YYYY-MM-DD.')
            )
            return None
    
    def _get_resources(self, resource_id, resource_type, location, active_only):
        """Get resources based on filter criteria."""
        if resource_id:
            try:
                resource = Resource.objects.get(id=resource_id)
                return [resource]
            except Resource.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f'Resource with ID {resource_id} not found.')
                )
                return []
        
        # Build queryset with filters
        queryset = Resource.objects.all()
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        return list(queryset.order_by('name'))
    
    def _show_utilization_insights(self, period_type):
        """Show insights about utilization patterns."""
        from booking.models import ResourceUtilizationTrend
        
        # Get recent trends
        recent_trends = ResourceUtilizationTrend.objects.filter(
            period_type=period_type
        ).select_related('resource').order_by('-period_start')[:50]
        
        if not recent_trends:
            return
        
        # Analyze utilization patterns
        high_utilization = []
        low_utilization = []
        trending_up = []
        trending_down = []
        
        for trend in recent_trends:
            utilization = float(trend.utilization_rate)
            
            if utilization >= 90:
                high_utilization.append((trend.resource.name, utilization))
            elif utilization <= 20:
                low_utilization.append((trend.resource.name, utilization))
            
            if trend.trend_direction == 'increasing' and trend.trend_strength >= 20:
                trending_up.append((trend.resource.name, float(trend.trend_strength)))
            elif trend.trend_direction == 'decreasing' and trend.trend_strength <= -20:
                trending_down.append((trend.resource.name, abs(float(trend.trend_strength))))
        
        # Display insights
        self.stdout.write('\n' + self.style.SUCCESS('UTILIZATION INSIGHTS:'))
        
        if high_utilization:
            self.stdout.write('\n🔴 HIGH UTILIZATION (≥90%):')
            for name, rate in high_utilization[:5]:
                self.stdout.write(f'  • {name}: {rate:.1f}%')
        
        if low_utilization:
            self.stdout.write('\n🟡 LOW UTILIZATION (≤20%):')
            for name, rate in low_utilization[:5]:
                self.stdout.write(f'  • {name}: {rate:.1f}%')
        
        if trending_up:
            self.stdout.write('\n📈 TRENDING UP (≥20% increase):')
            for name, strength in trending_up[:3]:
                self.stdout.write(f'  • {name}: +{strength:.1f}%')
        
        if trending_down:
            self.stdout.write('\n📉 TRENDING DOWN (≥20% decrease):')
            for name, strength in trending_down[:3]:
                self.stdout.write(f'  • {name}: -{strength:.1f}%')
        
        # Recommendations
        self.stdout.write('\n' + self.style.SUCCESS('RECOMMENDATIONS:'))
        
        if high_utilization:
            self.stdout.write(
                '• Consider adding more booking slots or resources for high-utilization items'
            )
        
        if low_utilization:
            self.stdout.write(
                '• Review marketing and scheduling for low-utilization resources'
            )
        
        if trending_down:
            self.stdout.write(
                '• Investigate causes of declining utilization trends'
            )
        
        self.stdout.write('')