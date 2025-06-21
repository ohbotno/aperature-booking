# booking/utilization_service.py
"""
Resource utilization trend analysis service.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This software is dual-licensed:
1. GNU General Public License v3.0 (GPL-3.0) - for open source use
2. Commercial License - for proprietary and commercial use

For GPL-3.0 license terms, see LICENSE file.
For commercial licensing, see COMMERCIAL-LICENSE.txt or visit:
https://aperture-booking.org/commercial
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any
from django.db import models
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, F, Case, When
from django.db.models.functions import Extract, TruncDay, TruncWeek, TruncMonth, TruncQuarter, TruncYear

logger = logging.getLogger(__name__)


class UtilizationTrendService:
    """
    Service for calculating and analyzing resource utilization trends.
    
    Provides comprehensive utilization analysis including:
    - Historical trend calculation
    - Peak usage analysis
    - Capacity planning insights
    - Predictive forecasting
    - User behavior patterns
    """
    
    def __init__(self):
        self.trend_thresholds = {
            'stable_range': 5.0,  # ±5% considered stable
            'moderate_threshold': 20.0,  # 20% change considered moderate
            'strong_threshold': 50.0,  # 50% change considered strong
            'volatile_threshold': 30.0,  # 30% variance considered volatile
        }
    
    def calculate_utilization_trends(self, resource=None, period_type='daily', 
                                   start_date=None, end_date=None, force_recalculate=False):
        """
        Calculate utilization trends for resources over specified periods.
        
        Args:
            resource: Specific resource to analyze (None for all)
            period_type: 'hourly', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
            start_date: Start date for analysis
            end_date: End date for analysis
            force_recalculate: Whether to recalculate existing trends
            
        Returns:
            Dict with calculation results and statistics
        """
        from .models import Resource, ResourceUtilizationTrend
        
        logger.info(f"Starting utilization trend calculation for period_type: {period_type}")
        
        # Set default date range if not provided
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - self._get_default_lookback_period(period_type)
        
        # Get resources to analyze
        resources = [resource] if resource else Resource.objects.filter(is_active=True)
        
        results = {
            'processed_resources': 0,
            'created_trends': 0,
            'updated_trends': 0,
            'period_type': period_type,
            'date_range': (start_date, end_date),
            'resources_analyzed': []
        }
        
        for res in resources:
            try:
                resource_result = self._calculate_resource_trends(
                    res, period_type, start_date, end_date, force_recalculate
                )
                results['processed_resources'] += 1
                results['created_trends'] += resource_result['created']
                results['updated_trends'] += resource_result['updated']
                results['resources_analyzed'].append({
                    'resource_id': res.id,
                    'resource_name': res.name,
                    'periods_processed': resource_result['periods_processed']
                })
                
            except Exception as e:
                logger.error(f"Error calculating trends for resource {res.id}: {str(e)}")
                continue
        
        logger.info(f"Utilization trend calculation complete. Processed {results['processed_resources']} resources")
        return results
    
    def _calculate_resource_trends(self, resource, period_type, start_date, end_date, force_recalculate):
        """Calculate utilization trends for a specific resource."""
        from .models import ResourceUtilizationTrend, Booking
        
        # Generate time periods
        periods = self._generate_time_periods(period_type, start_date, end_date)
        
        result = {'created': 0, 'updated': 0, 'periods_processed': len(periods)}
        
        for period_start, period_end in periods:
            # Check if trend already exists
            existing_trend = ResourceUtilizationTrend.objects.filter(
                resource=resource,
                period_type=period_type,
                period_start=period_start
            ).first()
            
            if existing_trend and not force_recalculate:
                continue
            
            # Calculate utilization metrics for this period
            trend_data = self._calculate_period_utilization(
                resource, period_start, period_end, period_type
            )
            
            if existing_trend:
                # Update existing trend
                for field, value in trend_data.items():
                    setattr(existing_trend, field, value)
                existing_trend.save()
                result['updated'] += 1
            else:
                # Create new trend
                trend_data.update({
                    'resource': resource,
                    'period_type': period_type,
                    'period_start': period_start,
                    'period_end': period_end
                })
                ResourceUtilizationTrend.objects.create(**trend_data)
                result['created'] += 1
        
        # Calculate trend directions and forecasts
        self._calculate_trend_indicators(resource, period_type)
        
        return result
    
    def _calculate_period_utilization(self, resource, period_start, period_end, period_type):
        """Calculate utilization metrics for a specific time period."""
        from .models import Booking, CheckInOut, WaitingListEntry
        
        # Calculate available hours
        total_available_hours = self._calculate_available_hours(
            resource, period_start, period_end
        )
        
        # Get bookings for this period
        bookings = Booking.objects.filter(
            resource=resource,
            start_time__gte=period_start,
            start_time__lt=period_end,
            status__in=['confirmed', 'completed']
        ).select_related('user')
        
        # Calculate booking metrics
        total_bookings = bookings.count()
        unique_users = bookings.values('user').distinct().count()
        
        # Calculate booked hours
        total_booked_hours = Decimal('0')
        total_used_hours = Decimal('0')
        no_show_count = 0
        booking_durations = []
        
        for booking in bookings:
            duration = (booking.end_time - booking.start_time).total_seconds() / 3600
            total_booked_hours += Decimal(str(duration))
            booking_durations.append(duration)
            
            # Check actual usage via check-in/check-out
            try:
                checkin = CheckInOut.objects.filter(
                    booking=booking,
                    check_in_time__isnull=False
                ).first()
                
                if checkin:
                    if checkin.check_out_time:
                        actual_duration = (checkin.check_out_time - checkin.check_in_time).total_seconds() / 3600
                        total_used_hours += Decimal(str(actual_duration))
                    else:
                        # Assume full booking duration if checked in but not out
                        total_used_hours += Decimal(str(duration))
                else:
                    # No check-in recorded - consider it a no-show
                    no_show_count += 1
            except:
                # If check-in system not available, assume booking was used
                total_used_hours += Decimal(str(duration))
        
        # Calculate rates
        utilization_rate = Decimal('0')
        actual_usage_rate = Decimal('0')
        no_show_rate = Decimal('0')
        
        if total_available_hours > 0:
            utilization_rate = (total_booked_hours / total_available_hours * 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        
        if total_booked_hours > 0:
            actual_usage_rate = (total_used_hours / total_booked_hours * 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            no_show_rate = (Decimal(str(no_show_count)) / Decimal(str(total_bookings)) * 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        
        # Calculate average booking duration
        average_booking_duration = Decimal('0')
        if booking_durations:
            average_booking_duration = Decimal(str(sum(booking_durations) / len(booking_durations))).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        
        # Calculate peak usage patterns
        peak_hour, peak_day, peak_utilization = self._calculate_peak_patterns(
            bookings, period_start, period_end
        )
        
        # Calculate capacity metrics
        capacity_utilization = self._calculate_capacity_utilization(
            resource, total_used_hours, total_available_hours
        )
        
        # Calculate waiting list demand
        waiting_list_demand = self._calculate_waiting_list_demand(
            resource, period_start, period_end
        )
        
        # Generate user and time patterns
        user_patterns = self._analyze_user_patterns(bookings)
        time_patterns = self._analyze_time_patterns(bookings, period_start, period_end)
        
        return {
            'total_available_hours': total_available_hours,
            'total_booked_hours': total_booked_hours,
            'total_used_hours': total_used_hours,
            'utilization_rate': utilization_rate,
            'actual_usage_rate': actual_usage_rate,
            'total_bookings': total_bookings,
            'unique_users': unique_users,
            'average_booking_duration': average_booking_duration,
            'no_show_count': no_show_count,
            'no_show_rate': no_show_rate,
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'peak_utilization': peak_utilization,
            'capacity_utilization': capacity_utilization,
            'waiting_list_demand': waiting_list_demand,
            'user_patterns': user_patterns,
            'time_patterns': time_patterns,
        }
    
    def _calculate_available_hours(self, resource, start_time, end_time):
        """Calculate total available hours for a resource in a time period."""
        # This is a simplified calculation
        # In a real implementation, you'd account for:
        # - Resource operating hours
        # - Holidays and closures
        # - Maintenance periods
        # - Resource capacity (if it supports multiple simultaneous users)
        
        total_hours = (end_time - start_time).total_seconds() / 3600
        
        # Assume 12 hours per day of availability (8 AM to 8 PM)
        # This should be made configurable per resource
        availability_ratio = 12.0 / 24.0  # 50% of the day
        
        return Decimal(str(total_hours * availability_ratio)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    def _calculate_peak_patterns(self, bookings, period_start, period_end):
        """Calculate peak usage patterns for bookings."""
        if not bookings.exists():
            return None, None, Decimal('0')
        
        # Analyze by hour of day
        hourly_usage = {}
        daily_usage = {}
        
        for booking in bookings:
            hour = booking.start_time.hour
            day = booking.start_time.weekday()  # 0=Monday, 6=Sunday
            duration = (booking.end_time - booking.start_time).total_seconds() / 3600
            
            hourly_usage[hour] = hourly_usage.get(hour, 0) + duration
            daily_usage[day] = daily_usage.get(day, 0) + duration
        
        # Find peak hour and day
        peak_hour = max(hourly_usage.items(), key=lambda x: x[1])[0] if hourly_usage else None
        peak_day = max(daily_usage.items(), key=lambda x: x[1])[0] if daily_usage else None
        
        # Calculate peak utilization (simplified)
        max_hourly_usage = max(hourly_usage.values()) if hourly_usage else 0
        peak_utilization = Decimal(str(min(100, max_hourly_usage * 100))).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        return peak_hour, peak_day, peak_utilization
    
    def _calculate_capacity_utilization(self, resource, total_used_hours, total_available_hours):
        """Calculate capacity utilization considering resource constraints."""
        if total_available_hours == 0:
            return Decimal('0')
        
        # Simple capacity calculation - could be enhanced with resource-specific logic
        capacity_ratio = total_used_hours / total_available_hours * 100
        
        return capacity_ratio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _calculate_waiting_list_demand(self, resource, period_start, period_end):
        """Calculate unfulfilled demand from waiting list entries."""
        from .models import WaitingListEntry
        
        try:
            waiting_entries = WaitingListEntry.objects.filter(
                booking_request__resource=resource,
                created_at__gte=period_start,
                created_at__lt=period_end,
                status__in=['waiting', 'expired']
            )
            
            total_demand = Decimal('0')
            for entry in waiting_entries:
                if hasattr(entry, 'preferred_duration') and entry.preferred_duration:
                    total_demand += Decimal(str(entry.preferred_duration))
                else:
                    # Assume 2-hour default if duration not specified
                    total_demand += Decimal('2.0')
            
            return total_demand.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except:
            # Return 0 if waiting list not implemented
            return Decimal('0')
    
    def _analyze_user_patterns(self, bookings):
        """Analyze user behavior patterns."""
        patterns = {
            'user_segments': {},
            'booking_frequency': {},
            'preferred_times': {},
            'booking_lengths': {}
        }
        
        user_bookings = {}
        for booking in bookings:
            user_id = booking.user.id
            if user_id not in user_bookings:
                user_bookings[user_id] = []
            user_bookings[user_id].append(booking)
        
        # Analyze user segments
        for user_id, user_booking_list in user_bookings.items():
            booking_count = len(user_booking_list)
            total_duration = sum([
                (b.end_time - b.start_time).total_seconds() / 3600 
                for b in user_booking_list
            ])
            
            if booking_count >= 10:
                segment = 'heavy_user'
            elif booking_count >= 5:
                segment = 'regular_user'
            elif booking_count >= 2:
                segment = 'occasional_user'
            else:
                segment = 'light_user'
            
            patterns['user_segments'][segment] = patterns['user_segments'].get(segment, 0) + 1
            patterns['booking_frequency'][user_id] = booking_count
            patterns['booking_lengths'][user_id] = total_duration
        
        return patterns
    
    def _analyze_time_patterns(self, bookings, period_start, period_end):
        """Analyze time-based usage patterns."""
        patterns = {
            'hourly_distribution': {},
            'daily_distribution': {},
            'monthly_distribution': {},
            'seasonal_patterns': {}
        }
        
        for booking in bookings:
            hour = booking.start_time.hour
            day = booking.start_time.weekday()
            month = booking.start_time.month
            duration = (booking.end_time - booking.start_time).total_seconds() / 3600
            
            patterns['hourly_distribution'][hour] = patterns['hourly_distribution'].get(hour, 0) + duration
            patterns['daily_distribution'][day] = patterns['daily_distribution'].get(day, 0) + duration
            patterns['monthly_distribution'][month] = patterns['monthly_distribution'].get(month, 0) + duration
        
        return patterns
    
    def _calculate_trend_indicators(self, resource, period_type):
        """Calculate trend direction and strength indicators."""
        from .models import ResourceUtilizationTrend
        
        # Get recent trends for comparison
        trends = ResourceUtilizationTrend.objects.filter(
            resource=resource,
            period_type=period_type
        ).order_by('-period_start')[:10]
        
        if len(trends) < 2:
            return
        
        # Calculate trend direction and strength
        for i, trend in enumerate(trends[:-1]):
            previous_trend = trends[i + 1]
            
            # Calculate change in utilization
            current_rate = float(trend.utilization_rate)
            previous_rate = float(previous_trend.utilization_rate)
            
            if previous_rate > 0:
                change_percent = ((current_rate - previous_rate) / previous_rate) * 100
            else:
                change_percent = 0
            
            # Determine trend direction
            if abs(change_percent) <= self.trend_thresholds['stable_range']:
                trend_direction = 'stable'
            elif change_percent > 0:
                trend_direction = 'increasing'
            else:
                trend_direction = 'decreasing'
            
            # Calculate volatility
            recent_rates = [float(t.utilization_rate) for t in trends[:5]]
            if len(recent_rates) >= 3:
                avg_rate = sum(recent_rates) / len(recent_rates)
                variance = sum([(rate - avg_rate) ** 2 for rate in recent_rates]) / len(recent_rates)
                std_dev = variance ** 0.5
                
                if std_dev > self.trend_thresholds['volatile_threshold']:
                    trend_direction = 'volatile'
            
            # Update trend with indicators
            trend.trend_direction = trend_direction
            trend.trend_strength = Decimal(str(change_percent)).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            # Simple forecast for next period
            if len(trends) >= 3:
                trend.forecast_next_period = self._calculate_simple_forecast(trends[:3])
                trend.forecast_confidence = self._calculate_forecast_confidence(trends[:5])
            
            trend.save()
    
    def _calculate_simple_forecast(self, recent_trends):
        """Calculate simple forecast based on recent trends."""
        rates = [float(t.utilization_rate) for t in recent_trends]
        
        if len(rates) >= 2:
            # Simple linear trend
            trend_slope = (rates[0] - rates[1])
            forecast = rates[0] + trend_slope
            
            # Constrain forecast to reasonable bounds
            forecast = max(0, min(100, forecast))
            
            return Decimal(str(forecast)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return None
    
    def _calculate_forecast_confidence(self, recent_trends):
        """Calculate confidence level for forecast."""
        if len(recent_trends) < 3:
            return Decimal('50')  # Low confidence with limited data
        
        rates = [float(t.utilization_rate) for t in recent_trends]
        
        # Calculate consistency (lower variance = higher confidence)
        avg_rate = sum(rates) / len(rates)
        variance = sum([(rate - avg_rate) ** 2 for rate in rates]) / len(rates)
        std_dev = variance ** 0.5
        
        # Convert to confidence percentage (inverse relationship)
        confidence = max(30, min(95, 100 - (std_dev * 2)))
        
        return Decimal(str(confidence)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _generate_time_periods(self, period_type, start_date, end_date):
        """Generate list of time periods for analysis."""
        periods = []
        current = start_date
        
        while current < end_date:
            if period_type == 'hourly':
                next_period = current + timedelta(hours=1)
            elif period_type == 'daily':
                next_period = current + timedelta(days=1)
            elif period_type == 'weekly':
                next_period = current + timedelta(weeks=1)
            elif period_type == 'monthly':
                # Handle month boundaries properly
                if current.month == 12:
                    next_period = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    next_period = current.replace(month=current.month + 1, day=1)
            elif period_type == 'quarterly':
                if current.month <= 3:
                    next_period = current.replace(month=4, day=1)
                elif current.month <= 6:
                    next_period = current.replace(month=7, day=1)
                elif current.month <= 9:
                    next_period = current.replace(month=10, day=1)
                else:
                    next_period = current.replace(year=current.year + 1, month=1, day=1)
            elif period_type == 'yearly':
                next_period = current.replace(year=current.year + 1, month=1, day=1)
            else:
                raise ValueError(f"Invalid period_type: {period_type}")
            
            if next_period > end_date:
                next_period = end_date
            
            periods.append((current, next_period))
            current = next_period
        
        return periods
    
    def _get_default_lookback_period(self, period_type):
        """Get default lookback period for analysis."""
        lookback_periods = {
            'hourly': timedelta(days=7),      # 1 week for hourly
            'daily': timedelta(days=90),      # 3 months for daily
            'weekly': timedelta(days=365),    # 1 year for weekly
            'monthly': timedelta(days=730),   # 2 years for monthly
            'quarterly': timedelta(days=1095), # 3 years for quarterly
            'yearly': timedelta(days=1825),   # 5 years for yearly
        }
        return lookback_periods.get(period_type, timedelta(days=90))
    
    def get_utilization_summary(self, resource=None, period_type='monthly', limit=12):
        """Get utilization trend summary for dashboard display."""
        from .models import ResourceUtilizationTrend
        
        query = ResourceUtilizationTrend.objects.filter(period_type=period_type)
        if resource:
            query = query.filter(resource=resource)
        
        trends = query.order_by('-period_start')[:limit]
        
        summary = {
            'current_utilization': None,
            'trend_direction': 'stable',
            'capacity_status': 'normal',
            'efficiency_score': 0,
            'peak_patterns': {},
            'recommendations': []
        }
        
        if trends:
            latest_trend = trends[0]
            summary['current_utilization'] = float(latest_trend.utilization_rate)
            summary['trend_direction'] = latest_trend.trend_direction
            summary['capacity_status'] = latest_trend.get_capacity_status()
            summary['efficiency_score'] = latest_trend.efficiency_score
            
            # Generate recommendations
            summary['recommendations'] = self._generate_recommendations(latest_trend, trends)
        
        return summary
    
    def _generate_recommendations(self, latest_trend, historical_trends):
        """Generate utilization optimization recommendations."""
        recommendations = []
        
        # High utilization recommendations
        if latest_trend.utilization_rate >= 90:
            recommendations.append({
                'type': 'capacity',
                'priority': 'high',
                'message': 'Resource is near capacity. Consider adding more booking slots or additional resources.'
            })
        
        # Low utilization recommendations
        elif latest_trend.utilization_rate <= 30:
            recommendations.append({
                'type': 'utilization',
                'priority': 'medium',
                'message': 'Resource utilization is low. Consider marketing to increase usage or adjusting availability.'
            })
        
        # High no-show rate recommendations
        if latest_trend.no_show_rate >= 20:
            recommendations.append({
                'type': 'efficiency',
                'priority': 'medium',
                'message': 'High no-show rate detected. Consider implementing stricter booking policies or reminders.'
            })
        
        # Trend-based recommendations
        if latest_trend.trend_direction == 'decreasing' and latest_trend.trend_strength <= -20:
            recommendations.append({
                'type': 'trend',
                'priority': 'medium',
                'message': 'Utilization is declining. Investigate potential causes and consider promotional activities.'
            })
        
        return recommendations


# Global service instance
utilization_service = UtilizationTrendService()