from django.contrib import admin
from django.utils.html import format_html

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at", "updated_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")
    ordering = ("user__username",)
    readonly_fields = ("created_at", "updated_at")

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj and request.user.is_superuser:
            readonly_fields.append("password_hash_preview")
        return tuple(readonly_fields)

    @admin.display(description="Password hash metadata")
    def password_hash_preview(self, obj):
        if not obj or not obj.user_id:
            return "Save this profile before viewing password metadata."

        algorithm = obj.user.password.split("$", 1)[0] if obj.user.password else "unusable"
        return format_html(
            """
            <div class="readonly">
              <code>{algorithm} hash stored</code>
              <p class="help">Django stores password hashes, not readable plaintext passwords. The full hash is intentionally not exposed in this admin page; use the user's password change form to reset access.</p>
            </div>
            """,
            algorithm=algorithm,
        )
