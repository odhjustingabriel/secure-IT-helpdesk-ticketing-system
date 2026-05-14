from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

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
