from django.contrib import admin
from django.utils.html import format_html

from .models import AuditLog, CannedResponse, Category, Comment, Tag, Ticket
from .utils import staff_users_queryset


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "priority",
        "status",
        "created_by",
        "assigned_to",
        "has_attachment",
        "updated_at",
    )
    list_filter = ("status", "priority", "category", "assigned_to", "tags")
    filter_horizontal = ("tags",)
    search_fields = ("title", "description", "created_by__username", "assigned_to__username", "tags__name")
    readonly_fields = ("created_at", "updated_at", "closed_at", "attachment_link")
    fieldsets = (
        ("Ticket details", {"fields": ("title", "description", "category", "priority", "status", "channel", "tags", "due_at", "first_response_at", "resolution_note")}),
        ("People", {"fields": ("created_by", "assigned_to")}),
        ("Attachment", {"fields": ("attachment", "attachment_link")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "closed_at")}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assigned_to":
            kwargs["queryset"] = staff_users_queryset()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(boolean=True, description="Attachment")
    def has_attachment(self, obj):
        return bool(obj.attachment)

    @admin.display(description="Current attachment")
    def attachment_link(self, obj):
        if not obj or not obj.attachment:
            return "No attachment uploaded."
        url = obj.attachment.url
        name = obj.attachment.name.rsplit("/", 1)[-1]
        lower_name = name.lower()
        if lower_name.endswith((".png", ".jpg", ".jpeg")):
            return format_html(
                '<a href="{}" target="_blank" rel="noopener">{}</a><br>'
                '<img src="{}" alt="{}" style="max-width: 320px; max-height: 220px; margin-top: 8px; border-radius: 8px; border: 1px solid #ddd;" />',
                url,
                name,
                url,
                name,
            )
        return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>', url, name)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(CannedResponse)
class CannedResponseAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "body")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "is_internal", "created_at")
    search_fields = ("body", "author__username", "ticket__title")
    list_filter = ("is_internal", "created_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "ticket", "actor", "field_changed", "old_value", "new_value", "timestamp")
    list_filter = ("action", "field_changed", "timestamp")
    search_fields = ("action", "ticket__title", "actor__username", "old_value", "new_value")
    readonly_fields = ("timestamp",)
