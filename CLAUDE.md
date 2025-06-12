# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based Lab Booking System for managing laboratory resource bookings in academic institutions. The system prevents double-booking conflicts, enables group collaboration, and provides comprehensive usage analytics.

**Core Architecture:**
- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: SQLite (dev), MySQL/PostgreSQL (production) with environment-based switching
- **Frontend**: Bootstrap 5 + FullCalendar for interactive booking interface
- **API**: RESTful API with token/session authentication

## Essential Commands

### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Testing
```bash
# Run all tests
python manage.py test

# Run with coverage (if installed)
coverage run --source='.' manage.py test
coverage report
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8
```

### Production Commands
```bash
# Collect static files
python manage.py collectstatic

# Run with Gunicorn
gunicorn lab_booking.wsgi:application
```

## Core Models & Architecture

### Key Models (booking/models.py)
- **UserProfile**: Extended user with roles (student, researcher, lecturer, lab_manager, sysadmin)
- **Resource**: Bookable equipment/rooms with capacity and training requirements
- **Booking**: Time-slot reservations with conflict detection and approval workflows
- **ApprovalRule**: Configurable approval workflows (auto, single, tiered, quota-based)
- **Maintenance**: Scheduled maintenance windows that block bookings
- **BookingHistory**: Audit trail for all booking changes

### Database Constraints
- Bookings must end after they start (CHECK constraint)
- No time conflicts for same resource
- Booking hours restricted to 9 AM - 6 PM
- Maximum booking duration per resource

### API Structure
- REST API at `/api/` with viewsets for all major models
- Token and session authentication
- Role-based permissions (IsOwnerOrManagerPermission)
- Pagination enabled (20 items per page)

## Environment Configuration

The application uses environment variables for configuration:

### Database Switching
- `DB_ENGINE`: sqlite (default), mysql, postgresql
- Database credentials via DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

### Key Settings
- `SECRET_KEY`: Django secret key
- `DEBUG`: Enable/disable debug mode
- `LAB_BOOKING_ADVANCE_DAYS`: How far ahead bookings can be made (default: 30)
- `TIME_ZONE`: Application timezone (default: UTC)

## Role-Based Permissions

User roles determine booking capabilities:
- **student**: Basic booking requests
- **researcher**: Can create recurring bookings
- **lecturer**: Priority booking, group management
- **lab_manager**: Approve bookings, manage resources
- **sysadmin**: Full system access

## Conflict Detection

The system prevents double-booking through:
- Database-level constraints
- Model validation in `Booking.has_conflicts()`
- Real-time validation in calendar interface
- Maintenance window blocking

## Key Business Logic

### Booking Validation (booking/models.py:139-161)
- Time constraints (9 AM - 6 PM)
- Duration limits per resource
- Training level requirements
- Induction requirements

### Approval Workflows (booking/models.py:199-233)
- Auto-approval for trusted users/resources
- Single-level approval with designated approvers
- Tiered approval for high-value equipment
- Quota-based approval with usage limits

## File Structure

```
lab_booking/
├── booking/           # Main Django app
│   ├── models.py      # Core data models
│   ├── views.py       # API views and web views
│   ├── serializers.py # DRF serializers
│   ├── urls.py        # URL routing
│   ├── admin.py       # Django admin configuration
│   └── templates/     # HTML templates
├── lab_booking/       # Django project settings
│   ├── settings.py    # Main configuration
│   ├── urls.py        # Root URL configuration
│   └── wsgi.py        # WSGI application
├── static/            # Static assets (CSS, JS)
├── templates/         # Global templates
└── manage.py          # Django management script
```

## Development Notes

- All models include created_at/updated_at timestamps
- Comprehensive logging to lab_booking.log
- CORS configured for frontend development
- JSON fields used for flexible data (recurring patterns, approval conditions)
- Database table names prefixed with 'booking_'
- Model validation enforced at save() level