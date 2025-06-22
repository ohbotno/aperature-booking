# Manual migration for final approval workflow features

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0022_auto_20250616_1453"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Create ApprovalDelegation model
        migrations.CreateModel(
            name="ApprovalDelegation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateField(help_text="When delegation becomes active")),
                ("end_date", models.DateField(help_text="When delegation expires")),
                ("delegated_permissions", models.JSONField(default=dict, help_text="Permissions delegated: {'access': bool, 'training': bool, 'assessment': bool}")),
                ("reason", models.CharField(help_text="Reason for delegation (e.g., vacation, sick leave)", max_length=200)),
                ("notes", models.TextField(blank=True, help_text="Additional notes about the delegation")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="created_delegations", to=settings.AUTH_USER_MODEL)),
                ("delegate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="delegations_received", to=settings.AUTH_USER_MODEL)),
                ("delegator", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="delegations_given", to="booking.resourceresponsible")),
            ],
            options={
                "db_table": "booking_approvaldelegation",
                "ordering": ["-start_date", "-created_at"],
                "unique_together": {("delegator", "delegate", "start_date")},
            },
        ),
        
        # Create ApprovalStatistics model
        migrations.CreateModel(
            name="ApprovalStatistics",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("period_type", models.CharField(choices=[("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly"), ("quarterly", "Quarterly"), ("yearly", "Yearly")], default="monthly", max_length=20)),
                ("access_requests_received", models.IntegerField(default=0)),
                ("access_requests_approved", models.IntegerField(default=0)),
                ("access_requests_rejected", models.IntegerField(default=0)),
                ("access_requests_pending", models.IntegerField(default=0)),
                ("training_requests_received", models.IntegerField(default=0)),
                ("training_sessions_conducted", models.IntegerField(default=0)),
                ("training_completions", models.IntegerField(default=0)),
                ("training_failures", models.IntegerField(default=0)),
                ("assessments_created", models.IntegerField(default=0)),
                ("assessments_reviewed", models.IntegerField(default=0)),
                ("assessments_approved", models.IntegerField(default=0)),
                ("assessments_rejected", models.IntegerField(default=0)),
                ("avg_response_time_hours", models.FloatField(default=0.0)),
                ("min_response_time_hours", models.FloatField(default=0.0)),
                ("max_response_time_hours", models.FloatField(default=0.0)),
                ("delegations_given", models.IntegerField(default=0)),
                ("delegations_received", models.IntegerField(default=0)),
                ("overdue_items", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("approver", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="approval_stats", to=settings.AUTH_USER_MODEL)),
                ("resource", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="approval_stats", to="booking.resource")),
            ],
            options={
                "db_table": "booking_approvalstatistics",
                "ordering": ["-period_start", "resource", "approver"],
                "unique_together": {("resource", "approver", "period_start", "period_type")},
            },
        ),
        
        # Add fields to ApprovalRule model
        migrations.AddField(
            model_name="approvalrule",
            name="condition_type",
            field=models.CharField(
                choices=[
                    ("time_based", "Time-Based Conditions"),
                    ("usage_based", "Usage-Based Conditions"),
                    ("training_based", "Training-Based Conditions"),
                    ("role_based", "Role-Based Conditions"),
                    ("resource_based", "Resource-Based Conditions"),
                    ("custom", "Custom Logic"),
                ],
                default="role_based",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="approvalrule",
            name="conditional_logic",
            field=models.JSONField(default=dict, help_text="Advanced conditional rules"),
        ),
        migrations.AddField(
            model_name="approvalrule",
            name="description",
            field=models.TextField(blank=True, help_text="Detailed description of when this rule applies"),
        ),
        migrations.AddField(
            model_name="approvalrule",
            name="fallback_rule",
            field=models.ForeignKey(
                blank=True,
                help_text="Rule to apply if conditions not met",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="booking.approvalrule",
            ),
        ),
        
        # Alter approval_type field to include conditional
        migrations.AlterField(
            model_name="approvalrule",
            name="approval_type",
            field=models.CharField(
                choices=[
                    ("auto", "Automatic Approval"),
                    ("single", "Single Level Approval"),
                    ("tiered", "Tiered Approval"),
                    ("quota", "Quota Based"),
                    ("conditional", "Conditional Approval"),
                ],
                max_length=20,
            ),
        ),
    ]