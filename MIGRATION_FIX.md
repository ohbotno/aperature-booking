# Migration Fix Instructions

## Problem
Your database has migration conflicts due to duplicate migrations that create the same tables and indexes. This is preventing a clean migration.

## Solution: Complete Database Reset

The cleanest and most reliable solution is to start with a fresh database:

### Step 1: Backup Current Database (Optional)
```bash
cp db.sqlite3 db.sqlite3.old
```

### Step 2: Remove Database and Migration History
```bash
# Remove the database file
rm db.sqlite3

# Remove migration tracking (optional - keeps migration files but clears tracking)
# rm -rf booking/migrations/__pycache__/
```

### Step 3: Create Fresh Database
```bash
# Activate virtual environment
source /home/adam/.virtualenvs/Aperture\ Booking/bin/activate

# Run migrations from scratch
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Set up essential system data
python manage.py create_email_templates
python manage.py create_lab_admin_group
```

### Step 4: Verify Setup
```bash
# Check migration status
python manage.py showmigrations

# Start development server
python manage.py runserver
```

## Alternative: Fix Migrations Manually

If you need to preserve some data, you can try to fix the migrations manually:

### Option A: Skip Problematic Migrations
```bash
# Mark all remaining booking migrations as fake
python manage.py migrate booking --fake
python manage.py migrate  # Apply other apps
```

### Option B: Remove Duplicate Migration
```bash
# Delete the duplicate migration file
rm booking/migrations/0019_create_waiting_list_model.py

# Continue with migrations
python manage.py migrate
```

## What This Fixes

- ✅ Resolves duplicate table creation conflicts
- ✅ Fixes index naming conflicts  
- ✅ Ensures clean migration state
- ✅ Removes all example data automatically
- ✅ Provides fresh start for production

## After Migration Fix

1. **Create Admin User**: Set up your administrative account
2. **Configure System**: 
   - Set up email templates for your organization
   - Configure notification preferences
   - Add your institution's branding
3. **Add Real Data**:
   - Create your actual resources
   - Set up user accounts for staff and students
   - Configure approval workflows

## Recommendation

**Use the complete database reset (Steps 1-4)** as it's the most reliable solution and automatically removes all example data, giving you a clean production-ready system.

The migration conflicts indicate the database has accumulated inconsistencies over development. A fresh start ensures everything works correctly.