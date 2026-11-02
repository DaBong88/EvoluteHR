# Generated for EvoluteHR's manager request hub.

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ("employee", "0007_remove_policy_specific_employees_policy_department_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportingManagerChangeRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name="Created At")),
                ("is_active", models.BooleanField(default=True, verbose_name="Is Active")),
                ("reason", models.TextField(verbose_name="Reason")),
                ("status", models.CharField(choices=[("requested", "Requested"), ("approved", "Approved"), ("declined", "Declined")], default="requested", max_length=16)),
                ("decision_note", models.TextField(blank=True, verbose_name="Decision note")),
                ("created_by", models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to="horilla_auth.horillauser", verbose_name="Created By")),
                ("current_manager_id", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reporting_change_requests_made", to="employee.employee", verbose_name="Current manager")),
                ("employee_id", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reporting_change_requests", to="employee.employee", verbose_name="Team member")),
                ("requested_manager_id", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reporting_change_requests_received", to="employee.employee", verbose_name="Requested manager")),
                ("modified_by", models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_modified_by", to=settings.AUTH_USER_MODEL, verbose_name="Modified By")),
            ],
            options={
                "verbose_name": "Reporting manager change request",
                "verbose_name_plural": "Reporting manager change requests",
                "ordering": ["-id"],
            },
        ),
    ]
