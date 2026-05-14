# Generated for Secure IT Helpdesk MVP
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name_plural": "categories", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Ticket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160)),
                ("description", models.TextField()),
                ("priority", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")], default="medium", max_length=20)),
                ("status", models.CharField(choices=[("open", "Open"), ("in_progress", "In progress"), ("pending", "Pending"), ("resolved", "Resolved"), ("closed", "Closed")], default="open", max_length=20)),
                ("attachment", models.FileField(blank=True, null=True, upload_to="ticket_attachments/%Y/%m/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_tickets", to=settings.AUTH_USER_MODEL)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="tickets", to="tickets.category")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="created_tickets", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ticket_comments", to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="comments", to="tickets.ticket")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=80)),
                ("field_changed", models.CharField(blank=True, max_length=80, null=True)),
                ("old_value", models.CharField(blank=True, max_length=255, null=True)),
                ("new_value", models.CharField(blank=True, max_length=255, null=True)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_logs", to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="audit_logs", to="tickets.ticket")),
            ],
            options={"ordering": ["-timestamp"]},
        ),
    ]
