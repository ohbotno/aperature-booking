# Database Cleanup Instructions

## Overview
The current database contains example/test data that needs to be removed for production deployment. Due to database schema issues, automatic cleanup scripts encounter foreign key constraints and missing columns.

## What Has Been Cleaned

### 🗑️ Removed Files
- ✅ `booking/management/commands/populate_fake_data.py` - Script that creates fake user and booking data
- ✅ `booking/management/commands/create_sample_maintenance.py` - Sample maintenance data creation
- ✅ `booking/management/commands/create_sample_tutorials.py` - Sample tutorial creation
- ✅ `booking/management/commands/demo_calendar_features.py` - Demo calendar features
- ✅ `booking/management/commands/test_notifications.py` - Test notification script
- ✅ `booking/templates/booking/components/drag_drop_demo.html` - Demo template
- ✅ Coverage test files created during development
- ✅ Development documentation files (PLANNING.md, TASK.md)
- ✅ Coverage reports (htmlcov/)

### 📝 Updated Files
- ✅ `README.md` - Removed reference to sample data loading

## Current Database Contents

The database currently contains:
- **26 Users** (including test users with fake data)
- **9 Resources** (test equipment and rooms)
- **59 Bookings** (example bookings)
- **182 Notifications** (system notifications)
- **350 Notification Preferences** (user preferences)
- **Academic hierarchy data** (faculties, colleges, departments)

## Manual Cleanup Options

### Option 1: Fresh Database (Recommended)
The cleanest approach is to start with a fresh database:

```bash
# Backup current database (optional)
cp db.sqlite3 db.sqlite3.backup

# Remove current database
rm db.sqlite3

# Create fresh database
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Set up essential templates
python manage.py create_email_templates
python manage.py create_lab_admin_group
```

### Option 2: Manual Data Removal via Admin Panel
If you need to preserve some data, use the Django admin panel:

1. Access `/admin/` as superuser
2. Manually delete:
   - All Bookings
   - All Resources (except those you want to keep)
   - Test Users (keep only real admin users)
   - Notifications and Notification Preferences
   - Academic hierarchy data (unless needed)

### Option 3: Direct Database Cleanup
For SQLite database, you can use direct SQL commands:

```bash
# Open SQLite database
sqlite3 db.sqlite3

# Disable foreign key constraints temporarily
PRAGMA foreign_keys = OFF;

# Delete example data (adjust admin_user_id)
DELETE FROM booking_booking;
DELETE FROM booking_resource;
DELETE FROM booking_notification;
DELETE FROM booking_notificationpreference;
DELETE FROM booking_department;
DELETE FROM booking_college;
DELETE FROM booking_faculty;
DELETE FROM booking_userprofile WHERE user_id != 1;  -- Replace 1 with actual admin ID
DELETE FROM auth_user WHERE id != 1;  -- Replace 1 with actual admin ID

# Re-enable foreign key constraints
PRAGMA foreign_keys = ON;

# Exit SQLite
.exit
```

## Database Schema Issues

The current database has some schema inconsistencies:
- Missing column `resulting_booking_id` in some tables
- Duplicate migration artifacts
- Foreign key constraint conflicts

These issues prevent automatic cleanup scripts from working properly.

## Recommendations

For production deployment:

1. **Use Option 1 (Fresh Database)** - Most reliable approach
2. **Set up proper backup procedures** before adding real data
3. **Create only necessary admin users** initially
4. **Add real resources and users** as needed for your institution
5. **Configure email templates** for your organization

## Post-Cleanup Steps

After cleaning the database:

1. Create a superuser for system administration
2. Set up your organization's academic hierarchy (if using)
3. Configure email templates with your branding
4. Add real resources for your institution
5. Create user accounts for actual staff and students
6. Test the booking workflow with real scenarios

## Files to Review

Consider reviewing these files for any remaining example content:
- Email templates (may contain example text)
- Static files (logos, images)
- Configuration files (settings.py)

This cleanup ensures the system is ready for production use with your actual data.