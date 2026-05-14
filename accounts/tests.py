from django.contrib.auth.models import User
from django.test import TestCase
from django.contrib import admin
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
