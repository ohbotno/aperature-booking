# Generated migration for BookingTemplate model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('booking', '0002_add_email_verification'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('title_template', models.CharField(max_length=200)),
                ('description_template', models.TextField(blank=True)),
                ('duration_hours', models.PositiveIntegerField(default=1)),
                ('duration_minutes', models.PositiveIntegerField(default=0)),
                ('preferred_start_time', models.TimeField(blank=True, null=True)),
                ('shared_with_group', models.BooleanField(default=False)),
                ('notes_template', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=False)),
                ('use_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='booking.resource')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_templates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'booking_bookingtemplate',
                'ordering': ['-use_count', 'name'],
            },
        ),
        migrations.AddConstraint(
            model_name='bookingtemplate',
            constraint=models.UniqueConstraint(fields=('user', 'name'), name='unique_user_template_name'),
        ),
        migrations.AddField(
            model_name='booking',
            name='template_used',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bookings_created', to='booking.bookingtemplate'),
        ),
    ]