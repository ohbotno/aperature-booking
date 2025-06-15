#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/mnt/d/OneDrive - Swansea University/Projects/Aperture Booking')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aperture_booking.settings')

# Setup Django
django.setup()

from django.urls import reverse
from django.conf import settings

print("Available URL patterns:")
from django.urls.resolvers import get_resolver
resolver = get_resolver(settings.ROOT_URLCONF)

def print_urls(patterns, prefix=''):
    for pattern in patterns:
        if hasattr(pattern, 'url_patterns'):
            print_urls(pattern.url_patterns, prefix + str(pattern.pattern))
        else:
            print(f"{prefix}{pattern.pattern} -> {pattern.name}")

print_urls(resolver.url_patterns)