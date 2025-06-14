# booking/migrations/0001_initial.py
"""
Initial migration for Aperture Booking models.

This file is part of the Aperture Booking.
Copyright (C) 2025 Aperture Booking Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('resource_type', models.CharField(choices=[('robot', 'Robot'), ('instrument', 'Instrument'), ('room', 'Room'), ('safety_cabinet', 'Safety Cabinet'), ('equipment', 'Generic Equipment')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('location', models.CharField(max_length=200)),
                ('capacity', models.PositiveIntegerField(default=1)),
                ('required_training_level', models.PositiveIntegerField(default=1)),
                ('requires_induction', models.BooleanField(default=False)),
                ('max_booking_hours', models.PositiveIntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'booking_resource',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('student', 'Student'), ('researcher', 'Researcher'), ('lecturer', 'Lecturer'), ('lab_manager', 'Lab Manager'), ('sysadmin', 'System Administrator')], default='student', max_length=20)),
                ('group', models.CharField(blank=True, max_length=100)),
                ('college', models.CharField(blank=True, max_length=100)),
                ('student_id', models.CharField(blank=True, max_length=50, null=True)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('training_level', models.PositiveIntegerField(default=1)),
                ('is_inducted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'booking_userprofile',
            },
        ),
        migrations.CreateModel(
            name='Maintenance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('maintenance_type', models.CharField(max_length=100)),
                ('is_recurring', models.BooleanField(default=False)),
                ('recurring_pattern', models.JSONField(blank=True, null=True)),
                ('blocks_booking', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenances', to='booking.resource')),
            ],
            options={
                'db_table': 'booking_maintenance',
                'ordering': ['start_time'],
            },
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('status', models.CharField(choices=[('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled'), ('completed', 'Completed')], default='pending', max_length=20)),
                ('is_recurring', models.BooleanField(default=False)),
                ('recurring_pattern', models.JSONField(blank=True, null=True)),
                ('shared_with_group', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_bookings', to=settings.AUTH_USER_MODEL)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='booking.resource')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'booking_booking',
                'ordering': ['start_time'],
            },
        ),
        migrations.CreateModel(
            name='BookingHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=50)),
                ('old_values', models.JSONField(blank=True, null=True)),
                ('new_values', models.JSONField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='booking.booking')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'booking_bookinghistory',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='BookingAttendee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_primary', models.BooleanField(default=False)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='booking.booking')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'booking_bookingattendee',
            },
        ),
        migrations.AddField(
            model_name='booking',
            name='attendees',
            field=models.ManyToManyField(related_name='attending_bookings', through='booking.BookingAttendee', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='ApprovalRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('approval_type', models.CharField(choices=[('auto', 'Automatic Approval'), ('single', 'Single Level Approval'), ('tiered', 'Tiered Approval'), ('quota', 'Quota Based')], max_length=20)),
                ('user_roles', models.JSONField(default=list)),
                ('conditions', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('priority', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approvers', models.ManyToManyField(blank=True, related_name='approval_rules', to=settings.AUTH_USER_MODEL)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_rules', to='booking.resource')),
            ],
            options={
                'db_table': 'booking_approvalrule',
                'ordering': ['priority', 'name'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='bookingattendee',
            unique_together={('booking', 'user')},
        ),
        migrations.AddConstraint(
            model_name='booking',
            constraint=models.CheckConstraint(check=models.Q(('end_time__gt', models.F('start_time'))), name='booking_end_after_start'),
        ),
    ]