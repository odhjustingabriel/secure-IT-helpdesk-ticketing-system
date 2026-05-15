from django.contrib.auth.models import User
from django.contrib import admin
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .admin import ProfileAdmin
from .models import Profile


class RegistrationTests(TestCase):
    def test_registration_creates_profile_with_user_role(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "password1": "StrongPass12345",
                "password2": "StrongPass12345",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="newuser")
        self.assertEqual(user.profile.role, Profile.ROLE_USER)


    def test_profile_admin_role_configuration_keeps_profile_creation_working(self):
        user = User.objects.create_user("rolecheck", email="rolecheck@example.com", password="StrongPass12345")
        profile_admin = ProfileAdmin(Profile, admin.site)
        self.assertEqual(user.profile.role, Profile.ROLE_USER)
        self.assertEqual(profile_admin.list_display, ("user", "role", "created_at", "updated_at"))
        self.assertEqual(profile_admin.list_filter, ("role",))
        self.assertEqual(profile_admin.search_fields, ("user__username", "user__email"))
        self.assertEqual(profile_admin.ordering, ("user__username",))


    def test_profile_admin_password_hash_preview_is_superuser_only_and_not_plaintext(self):
        user = User.objects.create_user("hashcheck", email="hashcheck@example.com", password="PlainPassword12345")
        superuser = User.objects.create_superuser("admin", email="admin@example.com", password="AdminPassword12345")
        request = RequestFactory().get("/")
        request.user = superuser
        profile_admin = ProfileAdmin(Profile, admin.site)

        self.assertIn("password_hash_preview", profile_admin.get_readonly_fields(request, user.profile))
        rendered = str(profile_admin.password_hash_preview(user.profile))
        self.assertIn("Show hash for 1 second", rendered)
        self.assertIn("Django stores password hashes", rendered)
        self.assertNotIn("PlainPassword12345", rendered)

    def test_profile_admin_password_hash_preview_hidden_for_non_superusers(self):
        user = User.objects.create_user("hashhidden", email="hashhidden@example.com", password="PlainPassword12345")
        staff = User.objects.create_user("staff", email="staff@example.com", password="StaffPassword12345", is_staff=True)
        request = RequestFactory().get("/")
        request.user = staff
        profile_admin = ProfileAdmin(Profile, admin.site)

        self.assertNotIn("password_hash_preview", profile_admin.get_readonly_fields(request, user.profile))
