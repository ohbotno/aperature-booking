# booking/management/commands/generate_sample_utilization.py
"""
Management command to generate sample utilization trend data for testing and demonstration.

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
from decimal import Decimal
import random
from booking.models import Resource, ResourceUtilizationTrend


class Command(BaseCommand):
    help = 'Generate sample utilization trend data for testing and demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--resource-id',
            type=int,
            help='Specific resource ID to generate data for'
        )
        
        parser.add_argument(
            '--period-type',
            type=str,
            choices=['daily', 'weekly', 'monthly'],
            default='daily',
            help='Period type for trend data'
        )
        
        parser.add_argument(
            '--days-back',
            type=int,
            default=90,
            help='Number of days back to generate data for'
        )
        
        parser.add_argument(
            '--resources-count',
            type=int,
            default=5,
            help='Number of resources to generate data for (if no specific resource)'
        )
        
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing trend data before generating new data'
        )

    def handle(self, *args, **options):
        """Main command handler."""
        self.stdout.write(
            self.style.SUCCESS('Generating sample utilization trend data...')
        )
        
        resource_id = options.get('resource_id')
        period_type = options.get('period_type')
        days_back = options.get('days_back')
        resources_count = options.get('resources_count')
        clear_existing = options.get('clear_existing')
        
        # Get resources
        if resource_id:
            try:
                resources = [Resource.objects.get(id=resource_id)]
            except Resource.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f'Resource with ID {resource_id} not found.')
                )
                return
        else:
            resources = list(Resource.objects.filter(is_active=True)[:resources_count])
        
        if not resources:
            self.stdout.write(
                self.style.WARNING('No resources found to generate data for.')
            )
            return
        
        # Clear existing data if requested
        if clear_existing:
            count = ResourceUtilizationTrend.objects.filter(
                resource__in=resources,
                period_type=period_type
            ).count()
            ResourceUtilizationTrend.objects.filter(
                resource__in=resources,
                period_type=period_type
            ).delete()
            self.stdout.write(f'Cleared {count} existing trend records')
        
        # Generate periods
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)
        periods = self._generate_periods(period_type, start_date, end_date)
        
        total_created = 0
        
        for resource in resources:
            self.stdout.write(f'Generating data for resource: {resource.name}')
            
            # Create trend patterns for this resource
            base_utilization = random.uniform(30, 80)  # Base utilization rate
            trend_direction = random.choice(['increasing', 'decreasing', 'stable', 'volatile'])
            
            for i, (period_start, period_end) in enumerate(periods):
                trend_data = self._generate_trend_data(
                    resource, period_start, period_end, period_type,
                    base_utilization, trend_direction, i, len(periods)
                )
                
                ResourceUtilizationTrend.objects.create(**trend_data)
                total_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Generated {total_created} sample utilization trend records'
            )
        )
    
    def _generate_periods(self, period_type, start_date, end_date):
        """Generate time periods for data creation."""
        periods = []
        current = start_date
        
        while current < end_date:
            if period_type == 'daily':
                next_period = current + timedelta(days=1)
            elif period_type == 'weekly':
                next_period = current + timedelta(weeks=1)
            elif period_type == 'monthly':
                if current.month == 12:
                    next_period = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    next_period = current.replace(month=current.month + 1, day=1)
            
            if next_period > end_date:
                next_period = end_date
            
            periods.append((current, next_period))
            current = next_period
        
        return periods
    
    def _generate_trend_data(self, resource, period_start, period_end, period_type,
                           base_utilization, trend_direction, period_index, total_periods):
        """Generate realistic trend data for a specific period."""
        
        # Calculate utilization based on trend direction
        if trend_direction == 'increasing':
            trend_factor = period_index / total_periods * 30  # Up to 30% increase
            utilization_rate = min(95, base_utilization + trend_factor)
        elif trend_direction == 'decreasing':
            trend_factor = period_index / total_periods * 25  # Up to 25% decrease
            utilization_rate = max(5, base_utilization - trend_factor)
        elif trend_direction == 'volatile':
            volatility = random.uniform(-20, 20)
            utilization_rate = max(5, min(95, base_utilization + volatility))
        else:  # stable
            variation = random.uniform(-5, 5)
            utilization_rate = max(5, min(95, base_utilization + variation))
        
        # Add some randomness
        utilization_rate += random.uniform(-3, 3)
        utilization_rate = max(0, min(100, utilization_rate))
        
        # Calculate available hours based on period type
        if period_type == 'daily':
            available_hours = 12  # 12 hours per day
        elif period_type == 'weekly':
            available_hours = 60  # 12 hours * 5 days
        elif period_type == 'monthly':
            days_in_period = (period_end - period_start).days
            available_hours = days_in_period * 12 * (5/7)  # Weekdays only
        
        # Calculate other metrics
        total_booked_hours = Decimal(str(available_hours * utilization_rate / 100))
        actual_usage_rate = random.uniform(75, 95)  # Most bookings are used
        total_used_hours = total_booked_hours * Decimal(str(actual_usage_rate / 100))
        
        # Generate booking statistics
        avg_booking_duration = random.uniform(1.5, 4.0)
        total_bookings = max(1, int(float(total_booked_hours) / avg_booking_duration))
        unique_users = max(1, int(total_bookings * random.uniform(0.6, 0.9)))
        
        # No-show rate
        no_show_rate = random.uniform(2, 15)
        no_show_count = int(total_bookings * no_show_rate / 100)
        
        # Peak patterns
        peak_hour = random.randint(9, 16)  # Peak between 9 AM and 4 PM
        peak_day = random.randint(0, 4)    # Monday to Friday
        peak_utilization = min(100, utilization_rate + random.uniform(10, 25))
        
        # Trend calculations
        if trend_direction == 'increasing':
            trend_strength = random.uniform(15, 40)
        elif trend_direction == 'decreasing':
            trend_strength = random.uniform(-40, -15)
        elif trend_direction == 'volatile':
            trend_strength = random.uniform(-10, 10)
        else:  # stable
            trend_strength = random.uniform(-5, 5)
        
        # Capacity metrics
        capacity_utilization = utilization_rate + random.uniform(-5, 5)
        over_capacity_hours = max(0, (capacity_utilization - 100) / 100 * available_hours) if capacity_utilization > 100 else 0
        waiting_list_demand = Decimal(str(max(0, over_capacity_hours + random.uniform(0, 5))))
        
        # Generate user and time patterns
        user_patterns = {
            'user_segments': {
                'heavy_user': random.randint(1, 3),
                'regular_user': random.randint(2, 8),
                'occasional_user': random.randint(3, 12),
                'light_user': random.randint(5, 15)
            },
            'repeat_usage_rate': random.uniform(60, 85)
        }
        
        time_patterns = {
            'hourly_distribution': {
                str(h): random.uniform(0, 10) for h in range(8, 18)
            },
            'daily_distribution': {
                str(d): random.uniform(5, 25) for d in range(5)
            },
            'peak_hours': [9, 10, 13, 14, 15]
        }
        
        # Forecasting
        forecast_variation = random.uniform(-10, 10)
        forecast_next_period = max(0, min(100, utilization_rate + forecast_variation))
        forecast_confidence = random.uniform(65, 88)
        
        return {
            'resource': resource,
            'period_type': period_type,
            'period_start': period_start,
            'period_end': period_end,
            'total_available_hours': Decimal(str(available_hours)),
            'total_booked_hours': total_booked_hours.quantize(Decimal('0.01')),
            'total_used_hours': total_used_hours.quantize(Decimal('0.01')),
            'utilization_rate': Decimal(str(utilization_rate)).quantize(Decimal('0.01')),
            'actual_usage_rate': Decimal(str(actual_usage_rate)).quantize(Decimal('0.01')),
            'total_bookings': total_bookings,
            'unique_users': unique_users,
            'average_booking_duration': Decimal(str(avg_booking_duration)).quantize(Decimal('0.01')),
            'no_show_count': no_show_count,
            'no_show_rate': Decimal(str(no_show_rate)).quantize(Decimal('0.01')),
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'peak_utilization': Decimal(str(peak_utilization)).quantize(Decimal('0.01')),
            'trend_direction': trend_direction,
            'trend_strength': Decimal(str(trend_strength)).quantize(Decimal('0.01')),
            'capacity_utilization': Decimal(str(capacity_utilization)).quantize(Decimal('0.01')),
            'over_capacity_hours': Decimal(str(over_capacity_hours)).quantize(Decimal('0.01')),
            'waiting_list_demand': waiting_list_demand.quantize(Decimal('0.01')),
            'user_patterns': user_patterns,
            'time_patterns': time_patterns,
            'forecast_next_period': Decimal(str(forecast_next_period)).quantize(Decimal('0.01')),
            'forecast_confidence': Decimal(str(forecast_confidence)).quantize(Decimal('0.01')),
        }