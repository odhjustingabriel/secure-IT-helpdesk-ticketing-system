from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Ticket(models.Model):
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_CRITICAL = "critical"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_CRITICAL, "Critical"),
    ]

    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_PENDING = "pending"
    STATUS_RESOLVED = "resolved"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_PENDING, "Pending"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_CLOSED, "Closed"),
    ]

    title = models.CharField(max_length=160)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="tickets")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_tickets")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )
    attachment = models.FileField(upload_to="ticket_attachments/%Y/%m/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"#{self.pk} {self.title}"

    def save(self, *args, **kwargs):
        if self.status == self.STATUS_CLOSED and self.closed_at is None:
            self.closed_at = timezone.now()
        if self.status != self.STATUS_CLOSED:
            self.closed_at = None
        super().save(*args, **kwargs)


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ticket_comments")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.ticket}"


class AuditLog(models.Model):
    ACTION_CREATED = "created_ticket"
    ACTION_STATUS = "changed_status"
    ACTION_PRIORITY = "changed_priority"
    ACTION_ASSIGNMENT = "assigned_ticket"
    ACTION_COMMENT = "added_comment"

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=80)
    field_changed = models.CharField(max_length=80, blank=True, null=True)
    old_value = models.CharField(max_length=255, blank=True, null=True)
    new_value = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} on {self.ticket} at {self.timestamp:%Y-%m-%d %H:%M}"

    @property
    def readable_message(self):
        actor = self.actor.get_full_name() or self.actor.username if self.actor else "System"
        action_labels = {
            self.ACTION_CREATED: "created this ticket",
            self.ACTION_COMMENT: "added a comment",
            self.ACTION_STATUS: "changed status",
            self.ACTION_PRIORITY: "changed priority",
            self.ACTION_ASSIGNMENT: "changed assignment",
        }
        action = action_labels.get(self.action, self.action.replace("_", " "))
        if self.field_changed:
            return f"{actor} {action} from {self.old_value or 'blank'} to {self.new_value or 'blank'}."
        return f"{actor} {action}."
