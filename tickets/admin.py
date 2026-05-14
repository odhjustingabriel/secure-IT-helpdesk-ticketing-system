from django.contrib import admin

from .models import AuditLog, Category, Comment, Ticket


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name", "description")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "priority", "status", "created_by", "assigned_to", "updated_at")
    list_filter = ("status", "priority", "category", "assigned_to")
    search_fields = ("title", "description", "created_by__username", "assigned_to__username")
    readonly_fields = ("created_at", "updated_at", "closed_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "created_at")
    search_fields = ("body", "author__username", "ticket__title")
    list_filter = ("created_at",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "ticket", "actor", "field_changed", "old_value", "new_value", "timestamp")
    list_filter = ("action", "field_changed", "timestamp")
    search_fields = ("action", "ticket__title", "actor__username", "old_value", "new_value")
    readonly_fields = ("timestamp",)
