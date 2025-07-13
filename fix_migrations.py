#!/usr/bin/env python3
"""
Fix Django 4.2 compatibility issues in migrations.
Converts CheckConstraint 'condition' parameter to 'check'.
"""

import os
import re
import sys

def fix_migration_file(filepath):
    """Fix CheckConstraint syntax in a migration file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace condition= with check= in CheckConstraint
    original_content = content
    # Handle both formats
    content = re.sub(
        r'(CheckConstraint\s*\(\s*)condition(\s*=)',
        r'\1check\2',
        content
    )
    # Also handle inline format
    content = re.sub(
        r'(constraint\s*=\s*models\.CheckConstraint\s*\(\s*)condition(\s*=)',
        r'\1check\2',
        content
    )
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    return False

def main():
    """Main function to fix all migration files."""
    migrations_dir = os.path.join(os.path.dirname(__file__), 'booking', 'migrations')
    
    if not os.path.exists(migrations_dir):
        print(f"Error: Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    fixed_count = 0
    for filename in os.listdir(migrations_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(migrations_dir, filename)
            if fix_migration_file(filepath):
                fixed_count += 1
    
    if fixed_count > 0:
        print(f"\n✓ Fixed {fixed_count} migration file(s)")
    else:
        print("\n✓ No migration files needed fixing")

if __name__ == '__main__':
    main()