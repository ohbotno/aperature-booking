#!/bin/bash
# Direct fix for Django 4.2 migration compatibility

echo "Applying Django 4.2 migration fixes..."

# Fix the CheckConstraint syntax
sed -i 's/condition=models\.Q/check=models.Q/g' booking/migrations/0001_initial.py

# Verify the fix
if grep -q "condition=models.Q" booking/migrations/0001_initial.py; then
    echo "ERROR: Failed to fix migrations"
    exit 1
else
    echo "✓ Migration fixes applied successfully"
fi