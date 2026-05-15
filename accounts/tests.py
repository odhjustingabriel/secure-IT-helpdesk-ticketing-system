from django.contrib.auth.models import User
from django.contrib import admin
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .admin import ProfileAdmin
from .models import Profile
from .permissions import is_admin_role, is_support_or_admin


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
        self.assertIn("Password hash metadata", profile_admin.password_hash_preview.short_description)
        self.assertIn("Django stores password hashes", rendered)
        self.assertIn("pbkdf2_sha256 hash stored", rendered)
        self.assertNotIn(user.password, rendered)
        self.assertNotIn("data-secret", rendered)
        self.assertNotIn("PlainPassword12345", rendered)

    def test_profile_admin_password_hash_preview_hidden_for_non_superusers(self):
        user = User.objects.create_user("hashhidden", email="hashhidden@example.com", password="PlainPassword12345")
        staff = User.objects.create_user("staff", email="staff@example.com", password="StaffPassword12345", is_staff=True)
        request = RequestFactory().get("/")
        request.user = staff
        profile_admin = ProfileAdmin(Profile, admin.site)

        self.assertNotIn("password_hash_preview", profile_admin.get_readonly_fields(request, user.profile))


class RoleSeparationTests(TestCase):
    def setUp(self):
        self.support = User.objects.create_user("support", email="support@example.com", password="StrongPass12345")
        self.support.profile.role = Profile.ROLE_SUPPORT
        self.support.profile.save()
        self.admin_user = User.objects.create_user("roleadmin", email="admin@example.com", password="StrongPass12345")
        self.admin_user.profile.role = Profile.ROLE_ADMIN
        self.admin_user.profile.save()

    def test_profile_role_helpers_separate_support_from_admin(self):
        self.assertTrue(self.support.profile.is_support_role)
        self.assertFalse(self.support.profile.is_admin_role)
        self.assertTrue(is_support_or_admin(self.support))
        self.assertFalse(is_admin_role(self.support))

        self.assertFalse(self.admin_user.profile.is_support_role)
        self.assertTrue(self.admin_user.profile.is_admin_role)
        self.assertTrue(is_support_or_admin(self.admin_user))
        self.assertTrue(is_admin_role(self.admin_user))

    def test_navigation_hides_admin_link_from_support_role(self):
        self.client.login(username="support", password="StrongPass12345")
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'href="/admin/"')
        self.assertContains(response, reverse("password_change"))

    def test_navigation_shows_admin_link_for_admin_role(self):
        self.client.login(username="roleadmin", password="StrongPass12345")
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/admin/"')


class PasswordChangeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("passworduser", email="password@example.com", password="OldPass12345")

    def test_authenticated_user_can_change_password(self):
        self.client.login(username="passworduser", password="OldPass12345")
        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "OldPass12345",
                "new_password1": "NewPass12345",
                "new_password2": "NewPass12345",
            },
        )

        self.assertRedirects(response, reverse("password_change_done"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass12345"))
        done_response = self.client.get(reverse("password_change_done"))
        self.assertContains(done_response, "Password changed")

    def test_change_password_form_rejects_wrong_current_password(self):
        self.client.login(username="passworduser", password="OldPass12345")
        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "WrongPass12345",
                "new_password1": "NewPass12345",
                "new_password2": "NewPass12345",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your old password was entered incorrectly")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass12345"))
