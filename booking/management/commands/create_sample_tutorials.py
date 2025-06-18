# booking/management/commands/create_sample_tutorials.py
"""
Management command to create sample tutorial data.

This command creates tutorial categories and sample tutorials for the onboarding system.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from booking.models import TutorialCategory, Tutorial, TutorialAnalytics


class Command(BaseCommand):
    help = 'Create sample tutorial data for the onboarding system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of tutorials (delete existing)',
        )

    def handle(self, *args, **options):
        if options['force']:
            self.stdout.write('Deleting existing tutorials...')
            Tutorial.objects.all().delete()
            TutorialCategory.objects.all().delete()

        # Create tutorial categories
        categories_data = [
            {
                'name': 'Getting Started',
                'description': 'Essential tutorials for new users to get started with the system',
                'icon': 'fas fa-play-circle',
                'order': 1
            },
            {
                'name': 'Basic Operations',
                'description': 'Learn how to perform common tasks like creating bookings and managing resources',
                'icon': 'fas fa-cogs',
                'order': 2
            },
            {
                'name': 'Advanced Features',
                'description': 'Advanced features for power users and administrators',
                'icon': 'fas fa-rocket',
                'order': 3
            },
            {
                'name': 'Lab Administration',
                'description': 'Tutorials specifically for lab administrators and technicians',
                'icon': 'fas fa-user-cog',
                'order': 4
            }
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = TutorialCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Get or create a default admin user for tutorial creation
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(is_staff=True).first()

        # Sample tutorials data
        tutorials_data = [
            {
                'name': 'Welcome to Aperture Booking',
                'description': 'A comprehensive introduction to the lab booking system. Learn about the main features and how to navigate the interface.',
                'category': 'Getting Started',
                'target_roles': ['student', 'researcher', 'academic'],
                'target_pages': ['dashboard'],
                'trigger_type': 'first_login',
                'difficulty_level': 'beginner',
                'estimated_duration': 5,
                'is_mandatory': True,
                'auto_start': True,
                'steps': [
                    {
                        'title': 'Welcome to Aperture Booking!',
                        'subtitle': 'Your laboratory resource booking system',
                        'description': 'Welcome! This quick tutorial will help you get familiar with the main features of our lab booking system. Let\'s start by exploring the dashboard.',
                        'target': None,
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Navigation Menu',
                        'subtitle': 'Find your way around',
                        'description': 'The sidebar on the left contains all the main navigation options. You can access your bookings, view the calendar, browse resources, and more from here.',
                        'target': '#sidebar',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Dashboard Overview',
                        'subtitle': 'Your personal hub',
                        'description': 'The dashboard shows you important information at a glance: your upcoming bookings, pending approvals, and quick actions. This is your starting point each time you log in.',
                        'target': '.main-content',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'User Menu',
                        'subtitle': 'Account settings and more',
                        'description': 'Click on your name in the top-right corner to access your profile settings, view notifications, and logout when you\'re done.',
                        'target': '.navbar .dropdown',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Ready to Start!',
                        'subtitle': 'You\'re all set',
                        'description': 'Great! You now know the basics of navigating Aperture Booking. Feel free to explore the system, and remember you can always access help tutorials from the floating help button.',
                        'target': None,
                        'image': None,
                        'code': None
                    }
                ]
            },
            {
                'name': 'Creating Your First Booking',
                'description': 'Step-by-step guide to creating your first resource booking. Learn how to select resources, choose time slots, and submit your booking request.',
                'category': 'Basic Operations',
                'target_roles': ['student', 'researcher', 'academic'],
                'target_pages': ['create_booking', 'calendar'],
                'trigger_type': 'page_visit',
                'difficulty_level': 'beginner',
                'estimated_duration': 7,
                'is_mandatory': False,
                'auto_start': False,
                'steps': [
                    {
                        'title': 'Let\'s Create a Booking',
                        'subtitle': 'Reserve lab resources easily',
                        'description': 'This tutorial will guide you through creating your first booking. You\'ll learn how to select resources, pick time slots, and submit your request.',
                        'target': None,
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Access the Booking Form',
                        'subtitle': 'Start here',
                        'description': 'Click on "New Booking" to open the booking creation form. You can find this button on the dashboard or navigate to Calendar and click the "Create Booking" button.',
                        'target': '[href*="create_booking"]',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Choose Your Resource',
                        'subtitle': 'Select what you need',
                        'description': 'Select the resource you want to book from the dropdown list. Each resource shows its location and availability status.',
                        'target': '#id_resource',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Set Date and Time',
                        'subtitle': 'When do you need it?',
                        'description': 'Choose your preferred date and time for the booking. The system will show you available slots and highlight any conflicts.',
                        'target': '#id_start_date',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Add Details',
                        'subtitle': 'Tell us more',
                        'description': 'Provide a title and description for your booking. This helps administrators understand the purpose of your reservation.',
                        'target': '#id_title',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Submit Your Booking',
                        'subtitle': 'You\'re almost done!',
                        'description': 'Review your booking details and click "Create Booking" to submit your request. You\'ll receive a confirmation and can track the status in "My Bookings".',
                        'target': 'button[type="submit"]',
                        'image': None,
                        'code': None
                    }
                ]
            },
            {
                'name': 'Managing Lab Resources',
                'description': 'Learn how to add, edit, and manage laboratory resources as an administrator. Covers resource configuration, maintenance periods, and access controls.',
                'category': 'Lab Administration',
                'target_roles': ['technician', 'sysadmin'],
                'target_pages': ['lab_admin_resources'],
                'trigger_type': 'manual',
                'difficulty_level': 'intermediate',
                'estimated_duration': 10,
                'is_mandatory': False,
                'auto_start': False,
                'steps': [
                    {
                        'title': 'Resource Management Overview',
                        'subtitle': 'Admin tools for resources',
                        'description': 'As a lab administrator, you can manage all laboratory resources from this interface. Let\'s explore the key features for resource management.',
                        'target': None,
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Resource List',
                        'subtitle': 'See all your resources',
                        'description': 'The main table shows all laboratory resources with their status, location, and key information. You can sort and filter to find specific resources quickly.',
                        'target': '.table-responsive',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Adding New Resources',
                        'subtitle': 'Expand your lab',
                        'description': 'Click "Add Resource" to create a new laboratory resource. You\'ll configure details like name, type, location, capacity, and access requirements.',
                        'target': '[href*="add_resource"]',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Resource Configuration',
                        'subtitle': 'Set up resource details',
                        'description': 'Configure important settings like training requirements, booking limits, and whether the resource requires induction before use.',
                        'target': '.form-control',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Maintenance Scheduling',
                        'subtitle': 'Plan downtime',
                        'description': 'Use the maintenance feature to schedule planned downtime for your resources. This prevents conflicts and informs users of unavailability.',
                        'target': '[href*="maintenance"]',
                        'image': None,
                        'code': None
                    }
                ]
            },
            {
                'name': 'Using the Calendar Interface',
                'description': 'Master the calendar view to see bookings, check availability, and manage your schedule efficiently.',
                'category': 'Basic Operations',
                'target_roles': [],  # Available to all roles
                'target_pages': ['calendar'],
                'trigger_type': 'page_visit',
                'difficulty_level': 'beginner',
                'estimated_duration': 5,
                'is_mandatory': False,
                'auto_start': False,
                'steps': [
                    {
                        'title': 'Calendar Navigation',
                        'subtitle': 'View your schedule',
                        'description': 'The calendar interface shows all bookings and resource availability. Learn how to navigate between different views and time periods.',
                        'target': '.fc',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Viewing Options',
                        'subtitle': 'Choose your perspective',
                        'description': 'Switch between month, week, and day views using the buttons at the top. Each view provides different levels of detail for your bookings.',
                        'target': '.fc-toolbar',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Resource Filtering',
                        'subtitle': 'Focus on what matters',
                        'description': 'Use the resource filter to show only specific resources or categories. This helps you focus on the equipment you need.',
                        'target': '.resource-filter',
                        'image': None,
                        'code': None
                    },
                    {
                        'title': 'Booking Details',
                        'subtitle': 'Click for more info',
                        'description': 'Click on any booking event to see detailed information, including description, attendees, and status. You can also edit or cancel bookings from here.',
                        'target': '.fc-event',
                        'image': None,
                        'code': None
                    }
                ]
            }
        ]

        # Create tutorials
        for tutorial_data in tutorials_data:
            category_name = tutorial_data.pop('category')
            category = categories[category_name]
            
            tutorial, created = Tutorial.objects.get_or_create(
                name=tutorial_data['name'],
                category=category,
                defaults={
                    **tutorial_data,
                    'created_by': admin_user
                }
            )
            
            if created:
                self.stdout.write(f'Created tutorial: {tutorial.name}')
                
                # Create analytics record
                TutorialAnalytics.objects.get_or_create(tutorial=tutorial)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(categories_data)} categories and {len(tutorials_data)} tutorials'
            )
        )
        
        # Display summary
        self.stdout.write('\n--- Tutorial System Summary ---')
        for category in TutorialCategory.objects.all():
            tutorial_count = category.tutorials.count()
            self.stdout.write(f'{category.name}: {tutorial_count} tutorials')