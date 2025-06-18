# booking/management/commands/demo_calendar_features.py
"""
Management command to demonstrate calendar features.

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


class Command(BaseCommand):
    help = 'Demonstrate new calendar features'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎯 Calendar Enhancement Features Added!')
        )
        
        self.stdout.write('')
        self.stdout.write('📋 Keyboard Shortcuts:')
        
        shortcuts = [
            ('T', 'Go to today'),
            ('← →', 'Navigate previous/next'),
            ('M', 'Month view'),
            ('W', 'Week view'),
            ('D', 'Day view'),
            ('N', 'New booking'),
            ('F', 'Focus resource filter'),
            ('P', 'Export to PDF'),
            ('R', 'Refresh calendar'),
            ('H or ?', 'Show help'),
            ('Esc', 'Close modals'),
        ]
        
        for key, action in shortcuts:
            self.stdout.write(f'  {key:<8} {action}')
        
        self.stdout.write('')
        self.stdout.write('📄 PDF Export Features:')
        
        pdf_features = [
            'Export current calendar view to PDF',
            'Multiple view options (month/week/day)',
            'Landscape/portrait orientation',
            'Custom document titles',
            'Status legend inclusion',
            'Professional formatting',
            'High-quality rendering',
        ]
        
        for feature in pdf_features:
            self.stdout.write(f'  • {feature}')
        
        self.stdout.write('')
        self.stdout.write('🚀 How to Use:')
        self.stdout.write('  1. Navigate to the calendar page')
        self.stdout.write('  2. Use keyboard shortcuts for quick navigation')
        self.stdout.write('  3. Press H or ? to see the help modal')
        self.stdout.write('  4. Click the PDF button or press P to export')
        self.stdout.write('  5. Customize export options in the modal')
        
        self.stdout.write('')
        self.stdout.write('💡 Pro Tips:')
        self.stdout.write('  • Shortcuts work everywhere except form fields')
        self.stdout.write('  • PDF export captures current filter settings')
        self.stdout.write('  • Landscape orientation works best for calendars')
        self.stdout.write('  • Help modal shows all available shortcuts')
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('✅ Calendar features ready to use!')
        )