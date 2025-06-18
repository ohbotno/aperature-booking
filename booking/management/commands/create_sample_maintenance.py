# booking/management/commands/create_sample_maintenance.py
"""
Management command to create sample maintenance data.

This command creates sample vendors, maintenance schedules, and related data
for demonstrating the maintenance management system.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import random
from booking.models import (
    Resource, MaintenanceVendor, Maintenance, MaintenanceDocument,
    MaintenanceAlert, MaintenanceAnalytics
)


class Command(BaseCommand):
    help = 'Create sample maintenance data for demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of maintenance data (delete existing)',
        )

    def handle(self, *args, **options):
        if options['force']:
            self.stdout.write('Deleting existing maintenance data...')
            MaintenanceAlert.objects.all().delete()
            MaintenanceDocument.objects.all().delete()
            Maintenance.objects.all().delete()
            MaintenanceVendor.objects.all().delete()
            MaintenanceAnalytics.objects.all().delete()

        # Create sample vendors
        vendors_data = [
            {
                'name': 'TechService Solutions Ltd',
                'contact_person': 'John Smith',
                'email': 'john@techservice.com',
                'phone': '+44 1234 567890',
                'address': '123 Tech Street, London, UK',
                'website': 'https://techservice.com',
                'specialties': ['electrical', 'calibration', 'software'],
                'certifications': ['ISO 9001', 'NIST Certified'],
                'service_areas': ['London', 'Southeast England'],
                'hourly_rate': Decimal('75.00'),
                'emergency_rate': Decimal('120.00'),
                'rating': Decimal('4.5'),
                'is_active': True
            },
            {
                'name': 'Precision Maintenance Co',
                'contact_person': 'Sarah Johnson',
                'email': 'sarah@precision-maintenance.co.uk',
                'phone': '+44 1234 567891',
                'address': '456 Service Ave, Birmingham, UK',
                'website': 'https://precision-maintenance.co.uk',
                'specialties': ['mechanical', 'hydraulic', 'pneumatic'],
                'certifications': ['City & Guilds', 'BTEC'],
                'service_areas': ['Midlands', 'North England'],
                'hourly_rate': Decimal('65.00'),
                'emergency_rate': Decimal('95.00'),
                'rating': Decimal('4.2'),
                'is_active': True
            },
            {
                'name': 'BioCal Services',
                'contact_person': 'Dr. Michael Chen',
                'email': 'michael@biocal.co.uk',
                'phone': '+44 1234 567892',
                'address': '789 Science Park, Cambridge, UK',
                'website': 'https://biocal.co.uk',
                'specialties': ['biological', 'chemical', 'safety'],
                'certifications': ['UKAS Accredited', 'SafeContractor'],
                'service_areas': ['Cambridge', 'East England'],
                'hourly_rate': Decimal('85.00'),
                'emergency_rate': Decimal('130.00'),
                'rating': Decimal('4.8'),
                'is_active': True
            }
        ]

        vendors = {}
        for vendor_data in vendors_data:
            vendor, created = MaintenanceVendor.objects.get_or_create(
                name=vendor_data['name'],
                defaults=vendor_data
            )
            vendors[vendor_data['name']] = vendor
            if created:
                self.stdout.write(f'Created vendor: {vendor.name}')

        # Get admin user for maintenance creation
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(is_staff=True).first()
        
        if not admin_user:
            self.stderr.write('No admin user found. Please create a superuser first.')
            return

        # Get some resources
        resources = list(Resource.objects.all()[:10])  # Limit to first 10 resources
        if not resources:
            self.stderr.write('No resources found. Please create some resources first.')
            return

        # Create sample maintenance schedules
        maintenance_data = []
        now = timezone.now()
        
        # Past maintenance (completed)
        for i in range(15):
            resource = random.choice(resources)
            vendor = random.choice(list(vendors.values())) if random.random() > 0.3 else None
            
            # Past maintenance dates
            start_date = now - timedelta(days=random.randint(30, 365))
            end_date = start_date + timedelta(hours=random.randint(1, 8))
            completed_date = end_date + timedelta(hours=random.randint(0, 2))
            
            maintenance_type = random.choice(['preventive', 'corrective', 'calibration', 'inspection'])
            priority = random.choice(['low', 'medium', 'high'])
            
            estimated_cost = Decimal(str(random.randint(100, 2000)))
            actual_cost = estimated_cost * Decimal(str(random.uniform(0.8, 1.3)))
            
            maintenance_data.append({
                'resource': resource,
                'title': f'{maintenance_type.title()} Maintenance - {resource.name}',
                'description': f'Scheduled {maintenance_type} maintenance for {resource.name}',
                'start_time': start_date,
                'end_time': end_date,
                'maintenance_type': maintenance_type,
                'priority': priority,
                'status': 'completed',
                'vendor': vendor,
                'is_internal': vendor is None,
                'estimated_cost': estimated_cost,
                'actual_cost': actual_cost,
                'labor_hours': Decimal(str(random.uniform(2, 8))),
                'parts_cost': Decimal(str(random.randint(50, 500))),
                'completed_at': completed_date,
                'completion_notes': f'{maintenance_type.title()} maintenance completed successfully.',
                'created_by': admin_user,
                'assigned_to': admin_user
            })

        # Future maintenance (scheduled)
        for i in range(10):
            resource = random.choice(resources)
            vendor = random.choice(list(vendors.values())) if random.random() > 0.4 else None
            
            # Future maintenance dates
            start_date = now + timedelta(days=random.randint(1, 180))
            end_date = start_date + timedelta(hours=random.randint(2, 6))
            
            maintenance_type = random.choice(['preventive', 'calibration', 'inspection', 'upgrade'])
            priority = random.choice(['low', 'medium', 'high'])
            
            estimated_cost = Decimal(str(random.randint(150, 1500)))
            
            maintenance_data.append({
                'resource': resource,
                'title': f'Scheduled {maintenance_type.title()} - {resource.name}',
                'description': f'Upcoming {maintenance_type} maintenance for {resource.name}',
                'start_time': start_date,
                'end_time': end_date,
                'maintenance_type': maintenance_type,
                'priority': priority,
                'status': 'scheduled',
                'vendor': vendor,
                'is_internal': vendor is None,
                'estimated_cost': estimated_cost,
                'labor_hours': Decimal(str(random.uniform(2, 6))),
                'parts_cost': Decimal(str(random.randint(50, 400))),
                'created_by': admin_user,
                'assigned_to': admin_user
            })

        # Create maintenance records
        maintenances = []
        for data in maintenance_data:
            maintenance = Maintenance.objects.create(**data)
            maintenances.append(maintenance)

        self.stdout.write(f'Created {len(maintenances)} maintenance records')

        # Create some maintenance alerts
        alert_count = 0
        for resource in resources[:5]:  # Create alerts for first 5 resources
            # Usage pattern alert
            if random.random() > 0.5:
                MaintenanceAlert.objects.create(
                    resource=resource,
                    alert_type='pattern_anomaly',
                    severity='warning',
                    title=f'High Usage Detected - {resource.name}',
                    message=f'Resource {resource.name} has shown increased usage patterns in recent weeks.',
                    recommendation='Consider scheduling additional preventive maintenance.',
                    threshold_value=Decimal('40'),
                    actual_value=Decimal(str(random.uniform(45, 60))),
                    expires_at=now + timedelta(days=7)
                )
                alert_count += 1

            # Cost overrun alert
            if random.random() > 0.7:
                MaintenanceAlert.objects.create(
                    resource=resource,
                    alert_type='cost_overrun',
                    severity='info',
                    title=f'Maintenance Costs Rising - {resource.name}',
                    message=f'Maintenance costs for {resource.name} have increased by 15% compared to last quarter.',
                    recommendation='Review maintenance procedures and consider vendor negotiations.',
                    threshold_value=Decimal('10'),
                    actual_value=Decimal('15'),
                    expires_at=now + timedelta(days=14)
                )
                alert_count += 1

        self.stdout.write(f'Created {alert_count} maintenance alerts')

        # Calculate analytics for all resources
        analytics_count = 0
        for resource in resources:
            analytics, created = MaintenanceAnalytics.objects.get_or_create(resource=resource)
            analytics.calculate_metrics()
            analytics_count += 1

        self.stdout.write(f'Calculated analytics for {analytics_count} resources')

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample maintenance data:\n'
                f'  - {len(vendors)} vendors\n'
                f'  - {len(maintenances)} maintenance records\n'
                f'  - {alert_count} alerts\n'
                f'  - {analytics_count} analytics records'
            )
        )

        # Show some statistics
        self._show_statistics()

    def _show_statistics(self):
        """Show maintenance statistics."""
        self.stdout.write('\n--- Maintenance Statistics ---')
        
        # Maintenance by type
        from django.db.models import Count
        
        maintenance_by_type = Maintenance.objects.values('maintenance_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        self.stdout.write('\nMaintenance by Type:')
        for item in maintenance_by_type:
            self.stdout.write(f'  {item["maintenance_type"].title()}: {item["count"]}')
        
        # Maintenance by status
        maintenance_by_status = Maintenance.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        self.stdout.write('\nMaintenance by Status:')
        for item in maintenance_by_status:
            self.stdout.write(f'  {item["status"].title()}: {item["count"]}')
        
        # Vendor utilization
        vendor_maintenance = Maintenance.objects.filter(
            vendor__isnull=False
        ).values('vendor__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        if vendor_maintenance:
            self.stdout.write('\nVendor Utilization:')
            for item in vendor_maintenance:
                self.stdout.write(f'  {item["vendor__name"]}: {item["count"]} maintenance items')
        
        # Upcoming maintenance
        from django.utils import timezone
        upcoming = Maintenance.objects.filter(
            start_time__gte=timezone.now(),
            status='scheduled'
        ).count()
        
        self.stdout.write(f'\nUpcoming Scheduled Maintenance: {upcoming} items')
        
        # Active alerts
        active_alerts = MaintenanceAlert.objects.filter(is_active=True).count()
        self.stdout.write(f'Active Alerts: {active_alerts}')