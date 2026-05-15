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

    @admin.display(description="Password hash (not plaintext)")
    def password_hash_preview(self, obj):
        if not obj or not obj.user_id:
            return "Save this profile before viewing password metadata."

        element_id = f"password-hash-{obj.pk}"
        masked_value = "*" * 24
        return format_html(
            """
            <div class="readonly">
              <code id="{element_id}" data-secret="{password_hash}">{masked_value}</code>
              <button type="button" class="button" onclick="
                const code = document.getElementById('{element_id}');
                const button = this;
                code.textContent = code.dataset.secret;
                button.disabled = true;
                setTimeout(function() {{
                  code.textContent = '{masked_value}';
                  button.disabled = false;
                }}, 1000);
              ">Show hash for 1 second</button>
              <p class="help">Django stores password hashes, not readable plaintext passwords. Use the user's password change form to reset a password.</p>
            </div>
            """,
            element_id=element_id,
            password_hash=obj.user.password,
            masked_value=masked_value,
        )
